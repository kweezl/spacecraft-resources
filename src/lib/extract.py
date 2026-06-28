#!/usr/bin/env python3
"""Extract files from a SpaceCraft .pak archive.

Pure logic plus a thin argparse ``main`` driven by src/commands/extract.py.
"""
import argparse
import struct
from pathlib import Path, PurePosixPath


class PakParseError(ValueError):
    pass


class Reader:
    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0

    def read(self, n: int) -> bytes:
        if self.pos + n > len(self.data):
            raise EOFError(f"Unexpected end of index at 0x{self.pos:X}")
        out = self.data[self.pos:self.pos + n]
        self.pos += n
        return out

    def u8(self) -> int:
        return self.read(1)[0]

    def u32(self) -> int:
        return struct.unpack("<I", self.read(4))[0]


def dump_bytes(data: bytes, pos: int, radius: int = 96):
    start = max(0, pos - radius)
    end = min(len(data), pos + radius)

    print(f"Index dump around 0x{pos:X}")
    print(f"Range: 0x{start:X}..0x{end:X}")
    print()

    chunk = data[start:end]
    for i in range(0, len(chunk), 16):
        absolute = start + i
        row = chunk[i:i + 16]
        hex_part = " ".join(f"{b:02X}" for b in row)
        ascii_part = "".join(chr(b) if 32 <= b <= 126 else "." for b in row)
        print(f"{absolute:08X}  {hex_part:<48}  {ascii_part}")


def format_index_dump(data: bytes, pos: int, radius: int = 32) -> str:
    start = max(0, pos - radius)
    end = min(len(data), pos + radius)
    lines = [
        f"Index bytes around failure 0x{pos:X}",
        f"Range: 0x{start:X}..0x{end:X}",
    ]

    chunk = data[start:end]
    for i in range(0, len(chunk), 16):
        absolute = start + i
        row = chunk[i:i + 16]
        hex_part = " ".join(f"{b:02X}" for b in row)
        ascii_part = "".join(chr(b) if 32 <= b <= 126 else "." for b in row)
        lines.append(f"{absolute:08X}  {hex_part:<48}  {ascii_part}")

    return "\n".join(lines)


def parse_error(data: bytes, message: str, *, entry_start=None, reader_pos=None, path=None, entry_type=None):
    parts = [message]

    if entry_start is not None:
        parts.append(f"entry_start=0x{entry_start:X}")
    if reader_pos is not None:
        parts.append(f"reader_pos=0x{reader_pos:X}")
    if path is not None:
        parts.append(f"path={path}")
    if entry_type is not None:
        parts.append(f"entry_type={entry_type}")

    dump_pos = reader_pos if reader_pos is not None else entry_start or 0
    parts.append(format_index_dump(data, dump_pos))
    return PakParseError("\n".join(parts))


def next_16_byte_boundary(pos: int) -> int:
    return ((pos // 16) + 1) * 16


def read_entry(r: Reader, parent: PurePosixPath, pak_data_size: int):
    entry_start = r.pos

    try:
        name_len = r.u8()
        name = r.read(name_len).decode("utf-8", errors="replace")
        entry_type = r.u8()
    except EOFError as e:
        raise parse_error(
            r.data,
            str(e),
            entry_start=entry_start,
            reader_pos=r.pos,
            path=str(parent),
        ) from e

    path = parent / name if name else parent

    if entry_type == 1:
        try:
            child_count = r.u32()
        except EOFError as e:
            raise parse_error(
                r.data,
                str(e),
                entry_start=entry_start,
                reader_pos=r.pos,
                path=str(path),
                entry_type=entry_type,
            ) from e

        for _ in range(child_count):
            yield from read_entry(r, path, pak_data_size)

    elif entry_type == 0:
        try:
            offset = r.u32()
            size = r.u32()
            file_hash = r.u32()
        except EOFError as e:
            raise parse_error(
                r.data,
                str(e),
                entry_start=entry_start,
                reader_pos=r.pos,
                path=str(path),
                entry_type=entry_type,
            ) from e

        if offset + size > pak_data_size:
            raise parse_error(
                r.data,
                f"Invalid file range at index 0x{entry_start:X}: "
                f"{path}, offset={offset}, size={size}, pak_data_size={pak_data_size}",
                entry_start=entry_start,
                reader_pos=r.pos,
                path=str(path),
                entry_type=entry_type,
            )

        yield {
            "path": str(path),
            "type": "file",
            "offset": offset,
            "size": size,
            "packed_size": size,
            "unpacked_size": size,
            "hash": file_hash,
        }

    elif entry_type == 2:
        # Type-2 index entries do not carry the data offset directly. The first
        # two words are retained for diagnostics; real offsets are assigned after
        # the full index is parsed from the aligned type-2 data stream.
        try:
            stored_word_0 = r.u32()
            stored_word_1 = r.u32()
            size = r.u32()
            file_hash = r.u32()
        except EOFError as e:
            raise parse_error(
                r.data,
                str(e),
                entry_start=entry_start,
                reader_pos=r.pos,
                path=str(path),
                entry_type=entry_type,
            ) from e

        yield {
            "path": str(path),
            "type": "type2",
            "offset": None,
            "size": size,
            "packed_size": size,
            "unpacked_size": size,
            "hash": file_hash,
            "stored_word_0": stored_word_0,
            "stored_word_1": stored_word_1,
        }

    else:
        raise parse_error(
            r.data,
            f"Unknown entry type {entry_type} at index offset 0x{r.pos:X}; "
            f"entry started at 0x{entry_start:X}; path so far: {path}",
            entry_start=entry_start,
            reader_pos=r.pos,
            path=str(path),
            entry_type=entry_type,
        )


def assign_type2_offsets(files, pak_data_size: int):
    cursor = max(
        (
            item["offset"] + item["packed_size"]
            for item in files
            if item["type"] == "file"
        ),
        default=0,
    )

    for item in files:
        if item["type"] == "type2":
            cursor = next_16_byte_boundary(cursor)
            item["offset"] = cursor
            cursor += item["packed_size"]

    for item in files:
        if item["offset"] + item["packed_size"] > pak_data_size:
            raise ValueError(
                f"Invalid file range after offset assignment: "
                f"{item['path']}, offset={item['offset']}, "
                f"packed_size={item['packed_size']}, pak_data_size={pak_data_size}"
            )


def is_known_index_footer(trailing: bytes) -> bool:
    if not trailing:
        return True
    if all(b == 0 for b in trailing):
        return True
    if trailing.endswith(b"DATA") and all(b == 0 for b in trailing[:-4]):
        return True
    return False


def validate_index_consumed(index_data: bytes, pos: int):
    trailing = index_data[pos:]

    if is_known_index_footer(trailing):
        return

    raise parse_error(
        index_data,
        f"Unexpected trailing index bytes: parser stopped at 0x{pos:X}, "
        f"index size is 0x{len(index_data):X}, trailing={len(trailing)} bytes",
        entry_start=pos,
        reader_pos=pos,
    )


def scan_index(index_data: bytes, pak_data_size: int):
    r = Reader(index_data)
    file_count = 0
    type2_base = 0

    for item in read_entry(r, PurePosixPath(""), pak_data_size):
        file_count += 1

        if item["type"] == "file":
            type2_base = max(type2_base, item["offset"] + item["packed_size"])

    validate_index_consumed(index_data, r.pos)

    return {
        "file_count": file_count,
        "type2_base": type2_base,
        "parse_pos": r.pos,
        "index_size": len(index_data),
    }


def print_index_warning(summary):
    return


def iter_files(index_data: bytes, pak_data_size: int, summary=None):
    if summary is None:
        summary = scan_index(index_data, pak_data_size)

    r = Reader(index_data)
    type2_cursor = summary["type2_base"]

    for item in read_entry(r, PurePosixPath(""), pak_data_size):
        if item["type"] == "type2":
            type2_cursor = next_16_byte_boundary(type2_cursor)
            item["offset"] = type2_cursor
            type2_cursor += item["packed_size"]

        if item["offset"] + item["packed_size"] > pak_data_size:
            raise ValueError(
                f"Invalid file range after offset assignment: "
                f"{item['path']}, offset={item['offset']}, "
                f"packed_size={item['packed_size']}, pak_data_size={pak_data_size}"
            )

        yield item


def parse_files(index_data: bytes, pak_data_size: int, kind2_words: int = 4):
    summary = scan_index(index_data, pak_data_size)
    files = list(iter_files(index_data, pak_data_size, summary))
    print_index_warning(summary)

    return files


def safe_output_path(out_dir: Path, rel_path: str) -> Path:
    rel = PurePosixPath(rel_path)

    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError(f"Unsafe path in archive: {rel_path}")

    return out_dir.joinpath(*rel.parts)


def validate_total_extracted_size(files, pak_data_size: int):
    total_size = sum(item["packed_size"] for item in files)

    if total_size > pak_data_size:
        raise SystemExit(
            "Refusing to extract: selected entries total "
            f"{total_size} bytes, but the PAK data section is only "
            f"{pak_data_size} bytes. The index was probably parsed incorrectly."
        )


def copy_range(src, target: Path, absolute_offset: int, size: int):
    src.seek(absolute_offset)
    remaining = size

    with target.open("wb") as out:
        while remaining:
            chunk = src.read(min(1024 * 1024, remaining))
            if not chunk:
                raise EOFError(f"Unexpected end of PAK while extracting {target}")
            out.write(chunk)
            remaining -= len(chunk)


def build_filters(args):
    wanted_ext = None
    words = None

    if args.ext:
        wanted_ext = {
            e.lower() if e.startswith(".") else "." + e.lower()
            for e in args.ext
        }

    if args.contains:
        words = [w.lower() for w in args.contains]

    return wanted_ext, words


def file_matches(item, wanted_ext, words) -> bool:
    path_lower = item["path"].lower()

    if wanted_ext and Path(path_lower).suffix not in wanted_ext:
        return False

    if words and not any(w in path_lower for w in words):
        return False

    return True


def print_pak_header(pak_path: Path, data_start: int, unknown: int, file_count: int):
    print(f"PAK: {pak_path}")
    print(f"Data starts at: 0x{data_start:08X}")
    print(f"Unknown/header value: 0x{unknown:08X}")
    print(f"Files: {file_count}")
    print()


def print_list_item(item, data_start: int):
    print(
        f'{item["path"]}\t'
        f'{item["type"]}\t'
        f'{item["packed_size"]} bytes\t'
        f'unpacked={item["unpacked_size"]}\t'
        f'@ 0x{data_start + item["offset"]:08X}',
        flush=True,
    )


def format_extract_progress(index: int, total: int, item) -> str:
    return (
        f'Extracting {index}/{total}: {item["path"]} '
        f'({item["packed_size"]} bytes)'
    )


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("pak")
    parser.add_argument("--out", default="unpacked")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--ext", nargs="*")
    parser.add_argument("--contains", nargs="*")
    parser.add_argument("--kind2", type=int, choices=[3, 4], default=4, help=argparse.SUPPRESS)
    parser.add_argument("--debug-at", type=lambda x: int(x, 0))
    args = parser.parse_args(argv)

    pak_path = Path(args.pak)

    with pak_path.open("rb") as f:
        header = f.read(12)

        if header[:4] != b"PAK\x00":
            raise SystemExit("Not supported: missing PAK\\0 header")

        data_start = struct.unpack("<I", header[4:8])[0]
        unknown = struct.unpack("<I", header[8:12])[0]

        f.seek(12)
        index_data = f.read(data_start - 12)

    pak_data_size = pak_path.stat().st_size - data_start

    if args.debug_at is not None:
        dump_bytes(index_data, args.debug_at)
        return

    wanted_ext, words = build_filters(args)

    try:
        if args.list:
            summary = scan_index(index_data, pak_data_size)
            print_index_warning(summary)
            print_pak_header(pak_path, data_start, unknown, summary["file_count"])

            for item in iter_files(index_data, pak_data_size, summary):
                if file_matches(item, wanted_ext, words):
                    print_list_item(item, data_start)

            return

        files = parse_files(index_data, pak_data_size, args.kind2)
    except PakParseError as e:
        print()
        print("Parser failed.")
        print(e)
        raise SystemExit(1) from None
    except Exception as e:
        print()
        print("Parser failed.")
        print(e)
        print()
        print("Debug the failing area:")
        print(f'  py {Path(__file__).name} "{pak_path}" --debug-at 0x9417')
        print()
        raise

    print_pak_header(pak_path, data_start, unknown, len(files))

    selected = [
        item for item in files
        if file_matches(item, wanted_ext, words)
    ]

    validate_total_extracted_size(selected, pak_data_size)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    extracted = 0
    total_selected = len(selected)

    with pak_path.open("rb") as f:
        for index, item in enumerate(selected, 1):
            print(format_extract_progress(index, total_selected, item), flush=True)
            target = safe_output_path(out_dir, item["path"])
            target.parent.mkdir(parents=True, exist_ok=True)
            copy_range(f, target, data_start + item["offset"], item["packed_size"])
            extracted += 1

    print(f"Extracted {extracted} files to: {out_dir}")


if __name__ == "__main__":
    main()
