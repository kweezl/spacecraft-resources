#!/usr/bin/env python3
"""Generate colored item/resource icons from SpaceCraft data.cdb.

Pure logic plus a thin argparse ``main`` driven by src/commands/generate_icons.py.
Re-run after the game updates its data.cdb to regenerate the icon set.
"""
import argparse
import binascii
import json
import struct
import sys
import zlib
from dataclasses import dataclass
from pathlib import Path

from src.lib import deduplicate_icons

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
DEFAULT_ICON_FILES = (
    "ui/icons/sprite_sheet_icon_64.png",
    "ui/icons/sprite_sheet_icon_64_flat_white.png",
)
WINDOWS_INVALID_FILENAME_CHARS = set('<>:"/\\|?*')


@dataclass(frozen=True)
class Gradient:
    colors: list[tuple[int, int, int]]
    positions: list[float]

    def sample(self, value: float) -> tuple[int, int, int]:
        if value <= self.positions[0]:
            return self.colors[0]
        if value >= self.positions[-1]:
            return self.colors[-1]

        for index in range(1, len(self.positions)):
            right_pos = self.positions[index]
            if value <= right_pos:
                left_pos = self.positions[index - 1]
                left = self.colors[index - 1]
                right = self.colors[index]
                if right_pos == left_pos:
                    return right

                factor = (value - left_pos) / (right_pos - left_pos)
                return tuple(
                    clamp_byte(round(left[channel] + (right[channel] - left[channel]) * factor))
                    for channel in range(3)
                )

        return self.colors[-1]


@dataclass(frozen=True)
class RgbaImage:
    width: int
    height: int
    pixels: bytes

    def __post_init__(self):
        expected = self.width * self.height * 4
        if len(self.pixels) != expected:
            raise ValueError(f"RGBA data has {len(self.pixels)} bytes, expected {expected}")

    def crop(self, box: tuple[int, int, int, int]) -> "RgbaImage":
        left, top, right, bottom = box
        if left < 0 or top < 0 or right > self.width or bottom > self.height or right <= left or bottom <= top:
            raise ValueError(f"Crop box {box} is outside {self.width}x{self.height} image")

        out_width = right - left
        out_height = bottom - top
        rows = []
        row_bytes = self.width * 4
        crop_bytes = out_width * 4
        for y in range(top, bottom):
            start = y * row_bytes + left * 4
            rows.append(self.pixels[start:start + crop_bytes])

        return RgbaImage(out_width, out_height, b"".join(rows))


@dataclass(frozen=True)
class IconJob:
    sheet: str
    item_id: str
    name: str | None
    source_file: str
    size: int
    x: int
    y: int
    width: int
    height: int
    gradient: Gradient | None

    @property
    def output_name(self) -> str:
        validate_filename_id(self.item_id)
        return f"{self.item_id}.png"

    @property
    def crop_box(self) -> tuple[int, int, int, int]:
        left = self.x * self.size
        top = self.y * self.size
        right = left + self.width * self.size
        bottom = top + self.height * self.size
        return left, top, right, bottom


def clamp_byte(value: int) -> int:
    return max(0, min(255, value))


def signed_int_to_rgb(value: int) -> tuple[int, int, int]:
    rgb = value & 0xFFFFFF
    return (rgb >> 16) & 0xFF, (rgb >> 8) & 0xFF, rgb & 0xFF


def parse_gradient(value) -> Gradient | None:
    if not isinstance(value, dict):
        return None

    colors = value.get("colors")
    positions = value.get("positions")
    if not isinstance(colors, list) or not isinstance(positions, list):
        return None
    if len(colors) != len(positions) or not colors:
        return None

    pairs = sorted(
        (float(position), signed_int_to_rgb(int(color)))
        for color, position in zip(colors, positions, strict=True)
    )
    return Gradient(colors=[color for _, color in pairs], positions=[position for position, _ in pairs])


def validate_filename_id(item_id: str):
    if not item_id:
        raise ValueError("CDB id is empty")
    if item_id in {".", ".."}:
        raise ValueError(f"CDB id {item_id!r} is not a safe filename")
    bad = sorted(set(item_id) & WINDOWS_INVALID_FILENAME_CHARS)
    if bad:
        raise ValueError(f"CDB id {item_id!r} contains filename-invalid character(s): {''.join(bad)}")


def load_cdb(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def dig(row: dict, path: str):
    """Follow a dotted path (e.g. 'props.logo') into a nested CDB row."""
    node = row
    for part in path.split("."):
        if not isinstance(node, dict):
            return None
        node = node.get(part)
    return node


def iter_icon_jobs(cdb: dict, allowed_icon_files: set[str] | None = None, sheet: str | None = None, icon_path: str = "icon"):
    seen: set[str] = set()
    for sheet_obj in cdb.get("sheets", []):
        sheet_name = sheet_obj.get("name", "")
        if sheet is not None and sheet_name != sheet:
            continue
        for row in sheet_obj.get("lines", []):
            if not isinstance(row, dict):
                continue

            item_id = row.get("id")
            icon = dig(row, icon_path)
            if not isinstance(item_id, str) or not isinstance(icon, dict):
                continue

            source_file = icon.get("file")
            if not isinstance(source_file, str):
                continue
            if allowed_icon_files is not None and source_file not in allowed_icon_files:
                continue

            if not all(key in icon for key in ("size", "x", "y")):
                continue

            if item_id in seen:
                raise ValueError(f"Duplicate icon id {item_id!r}")
            seen.add(item_id)

            yield IconJob(
                sheet=sheet_name,
                item_id=item_id,
                name=row.get("name") if isinstance(row.get("name"), str) else None,
                source_file=source_file,
                size=int(icon["size"]),
                x=int(icon["x"]),
                y=int(icon["y"]),
                width=int(icon.get("width", 1)),
                height=int(icon.get("height", 1)),
                gradient=parse_gradient(row.get("color")),
            )


def read_png_rgba(path: Path) -> RgbaImage:
    return decode_png_rgba(path.read_bytes(), label=str(path))


def decode_png_rgba(data: bytes, label: str = "<png bytes>") -> RgbaImage:
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError(f"{label} is not a PNG file")

    offset = len(PNG_SIGNATURE)
    width = height = None
    idat_parts = []

    while offset < len(data):
        if offset + 8 > len(data):
            raise ValueError(f"{label} has a truncated PNG chunk header")

        length = struct.unpack(">I", data[offset:offset + 4])[0]
        chunk_type = data[offset + 4:offset + 8]
        offset += 8
        chunk_data = data[offset:offset + length]
        offset += length
        crc = data[offset:offset + 4]
        offset += 4

        expected_crc = struct.pack(">I", binascii.crc32(chunk_type + chunk_data) & 0xFFFFFFFF)
        if crc != expected_crc:
            raise ValueError(f"{label} has a bad CRC in {chunk_type.decode('ascii', 'replace')} chunk")

        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type, compression, filter_method, interlace = struct.unpack(
                ">IIBBBBB", chunk_data
            )
            if bit_depth != 8 or color_type != 6:
                raise ValueError(f"{label} must be an 8-bit RGBA PNG, got bit_depth={bit_depth}, color_type={color_type}")
            if compression != 0 or filter_method != 0 or interlace != 0:
                raise ValueError(f"{label} uses unsupported PNG options")
        elif chunk_type == b"IDAT":
            idat_parts.append(chunk_data)
        elif chunk_type == b"IEND":
            break

    if width is None or height is None:
        raise ValueError(f"{label} is missing IHDR")

    raw = zlib.decompress(b"".join(idat_parts))
    pixels = unfilter_png_rows(raw, width, height, 4)
    return RgbaImage(width, height, pixels)


def unfilter_png_rows(raw: bytes, width: int, height: int, bytes_per_pixel: int) -> bytes:
    stride = width * bytes_per_pixel
    expected = height * (stride + 1)
    if len(raw) != expected:
        raise ValueError(f"PNG data has {len(raw)} bytes after decompression, expected {expected}")

    output = bytearray()
    previous = bytearray(stride)
    offset = 0
    for _ in range(height):
        filter_type = raw[offset]
        offset += 1
        row = bytearray(raw[offset:offset + stride])
        offset += stride

        if filter_type == 0:
            pass
        elif filter_type == 1:
            for i in range(stride):
                left = row[i - bytes_per_pixel] if i >= bytes_per_pixel else 0
                row[i] = (row[i] + left) & 0xFF
        elif filter_type == 2:
            for i in range(stride):
                row[i] = (row[i] + previous[i]) & 0xFF
        elif filter_type == 3:
            for i in range(stride):
                left = row[i - bytes_per_pixel] if i >= bytes_per_pixel else 0
                up = previous[i]
                row[i] = (row[i] + ((left + up) // 2)) & 0xFF
        elif filter_type == 4:
            for i in range(stride):
                left = row[i - bytes_per_pixel] if i >= bytes_per_pixel else 0
                up = previous[i]
                up_left = previous[i - bytes_per_pixel] if i >= bytes_per_pixel else 0
                row[i] = (row[i] + paeth_predictor(left, up, up_left)) & 0xFF
        else:
            raise ValueError(f"Unsupported PNG filter type {filter_type}")

        output.extend(row)
        previous = row

    return bytes(output)


def paeth_predictor(left: int, up: int, up_left: int) -> int:
    estimate = left + up - up_left
    left_distance = abs(estimate - left)
    up_distance = abs(estimate - up)
    up_left_distance = abs(estimate - up_left)
    if left_distance <= up_distance and left_distance <= up_left_distance:
        return left
    if up_distance <= up_left_distance:
        return up
    return up_left


def write_png_rgba(path: Path, image: RgbaImage):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encode_png_rgba(image))


def write_webp_rgba(path: Path, image: RgbaImage):
    # WebP has no stdlib encoder; Pillow (libwebp) handles it. Lossless keeps the
    # recoloured pixel-art icons exact while being smaller than PNG.
    try:
        from PIL import Image
    except ImportError as error:  # pragma: no cover - depends on environment
        raise RuntimeError("WebP output requires Pillow (pip install Pillow)") from error

    path.parent.mkdir(parents=True, exist_ok=True)
    picture = Image.frombytes("RGBA", (image.width, image.height), image.pixels)
    picture.save(path, format="WEBP", lossless=True)


def write_icon(path: Path, image: RgbaImage, fmt: str):
    if fmt == "webp":
        write_webp_rgba(path, image)
    else:
        write_png_rgba(path, image)


def icon_filename(item_id: str, fmt: str) -> str:
    validate_filename_id(item_id)
    return f"{item_id}.{fmt}"


def encode_png_rgba(image: RgbaImage) -> bytes:
    rows = []
    stride = image.width * 4
    for y in range(image.height):
        start = y * stride
        rows.append(b"\x00" + image.pixels[start:start + stride])

    data = bytearray(PNG_SIGNATURE)
    data.extend(png_chunk(b"IHDR", struct.pack(">IIBBBBB", image.width, image.height, 8, 6, 0, 0, 0)))
    data.extend(png_chunk(b"IDAT", zlib.compress(b"".join(rows), level=9)))
    data.extend(png_chunk(b"IEND", b""))
    return bytes(data)


def png_chunk(chunk_type: bytes, chunk_data: bytes) -> bytes:
    return (
        struct.pack(">I", len(chunk_data))
        + chunk_type
        + chunk_data
        + struct.pack(">I", binascii.crc32(chunk_type + chunk_data) & 0xFFFFFFFF)
    )


def recolor_rgba(pixels: bytes, gradient: Gradient) -> bytes:
    output = bytearray(len(pixels))
    for index in range(0, len(pixels), 4):
        red, green, blue, alpha = pixels[index:index + 4]
        brightness = (red + green + blue) / (255 * 3)
        new_red, new_green, new_blue = gradient.sample(brightness)
        output[index:index + 4] = bytes([new_red, new_green, new_blue, alpha])
    return bytes(output)


def manifest_record(job: IconJob, output_path: Path) -> dict:
    record = {
        "id": job.item_id,
        "name": job.name,
        "sheet": job.sheet,
        "output": path_to_json(output_path),
        "source": {
            "file": job.source_file,
            "size": job.size,
            "x": job.x,
            "y": job.y,
            "width": job.width,
            "height": job.height,
        },
    }
    if job.gradient is not None:
        record["color"] = {
            "colors": [rgb_to_hex(color) for color in job.gradient.colors],
            "positions": job.gradient.positions,
        }
    return record


def path_to_json(path: Path) -> str:
    return path.as_posix()


def rgb_to_hex(color: tuple[int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}".format(*color)


def generate_icons(
    cdb_path: Path,
    assets_root: Path,
    out_dir: Path,
    manifest_path: Path,
    allowed_icon_files: set[str] | None,
    recolor: bool,
    clean: bool,
    dry_run: bool,
    dedup: bool = True,
    aliases_path: Path | None = None,
    sheet: str | None = None,
    icon_path: str = "icon",
    fmt: str = "webp",
) -> tuple[int, list[dict]]:
    cdb = load_cdb(cdb_path)
    jobs = list(iter_icon_jobs(cdb, allowed_icon_files, sheet, icon_path))
    source_cache: dict[Path, RgbaImage] = {}

    # Pass 1: build a manifest record for every item (no files written yet).
    records = [manifest_record(job, out_dir / icon_filename(job.item_id, fmt)) for job in jobs]
    records_by_id = {record["id"]: record for record in records}

    # Decide which jobs get a PNG on disk. In dedup mode only one canonical icon
    # per unique (crop + colour) is written; every other item is pointed at that
    # canonical file via the manifest and an alias map.
    alias_map = None
    if dedup:
        manifest_icons = {record["id"]: record for record in records}
        report = deduplicate_icons.analyze({"icons": manifest_icons})
        alias_map = deduplicate_icons.build_alias_map({"icons": manifest_icons}, report)
        canonical_ids = set(report.groups)
        for canonical, ids in report.groups.items():
            canonical_output = records_by_id[canonical]["output"]
            for item_id in ids:
                records_by_id[item_id]["output"] = canonical_output
        write_jobs = [job for job in jobs if job.item_id in canonical_ids]
    else:
        write_jobs = jobs

    expected_names = {Path(records_by_id[job.item_id]["output"]).name for job in write_jobs}

    if clean and not dry_run and out_dir.exists():
        # Remove any stale icons, including ones left from a different format.
        for stale_icon in list(out_dir.glob("*.png")) + list(out_dir.glob("*.webp")):
            if stale_icon.name not in expected_names:
                stale_icon.unlink()

    if not dry_run:
        for job in write_jobs:
            source_path = assets_root / Path(job.source_file)
            if source_path not in source_cache:
                source_cache[source_path] = read_png_rgba(source_path)

            image = source_cache[source_path].crop(job.crop_box)
            if recolor and job.gradient is not None:
                image = RgbaImage(image.width, image.height, recolor_rgba(image.pixels, job.gradient))

            write_icon(out_dir / icon_filename(job.item_id, fmt), image, fmt)

        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest = {
            "data": path_to_json(cdb_path),
            "assets": path_to_json(assets_root),
            "out": path_to_json(out_dir),
            "count": len(records),
            "icons": {record["id"]: record for record in records},
        }
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        if dedup and alias_map is not None and aliases_path is not None:
            aliases_path.parent.mkdir(parents=True, exist_ok=True)
            aliases_path.write_text(json.dumps(alias_map, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return len(jobs), records


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Generate colored item/resource icons from SpaceCraft data.cdb.")
    parser.add_argument("--data", type=Path, default=Path("unpacked/data.cdb"), help="Path to data.cdb JSON.")
    parser.add_argument("--assets", type=Path, default=Path("unpacked"), help="Root folder containing unpacked assets.")
    parser.add_argument("--out", type=Path, default=Path("generated/icons"), help="Output directory for PNG icons.")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("generated/icons_manifest.json"),
        help="Output JSON manifest path.",
    )
    parser.add_argument(
        "--icon-file",
        action="append",
        dest="icon_files",
        help="Restrict to this CDB icon file path. Can be passed multiple times.",
    )
    parser.add_argument(
        "--all-icon-files",
        action="store_true",
        help="Generate every CDB icon entry with a tile source instead of only sprite_sheet_icon_64 variants.",
    )
    parser.add_argument(
        "--sheet",
        default="item",
        help=(
            "Restrict generation to this CDB sheet, using each row's own icon "
            "(default: item). Pass an empty string to scan all sheets with the "
            "source-file filter instead."
        ),
    )
    parser.add_argument(
        "--icon-path",
        default="icon",
        help="Dotted row path to the icon object (default: icon). Use props.logo for factions.",
    )
    parser.add_argument(
        "--format",
        choices=["webp", "png"],
        default="webp",
        help="Icon output image format (default: webp).",
    )
    parser.add_argument("--no-recolor", action="store_true", help="Crop icons without applying CDB color gradients.")
    parser.add_argument("--clean", action="store_true", help="Delete stale PNGs in the output directory.")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be generated without writing files.")
    parser.add_argument(
        "--dedup",
        dest="dedup",
        action="store_true",
        default=True,
        help="Write only unique icons + aliases.json (default).",
    )
    parser.add_argument(
        "--no-dedup",
        dest="dedup",
        action="store_false",
        help="Write one PNG per item and no aliases.json.",
    )
    parser.add_argument(
        "--aliases",
        type=Path,
        default=Path("generated/aliases.json"),
        help="Alias map output path (written in dedup mode).",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    sheet = args.sheet or None
    if args.icon_files:
        allowed_icon_files = set(args.icon_files)
    elif args.all_icon_files or sheet:
        # A single-sheet scope keys icons by row id (unique within a sheet), so
        # all source files can be used without cross-sheet id collisions.
        allowed_icon_files = None
    else:
        allowed_icon_files = set(DEFAULT_ICON_FILES)

    try:
        count, records = generate_icons(
            cdb_path=args.data,
            assets_root=args.assets,
            out_dir=args.out,
            manifest_path=args.manifest,
            allowed_icon_files=allowed_icon_files,
            recolor=not args.no_recolor,
            clean=args.clean,
            dry_run=args.dry_run,
            dedup=args.dedup,
            aliases_path=args.aliases,
            sheet=sheet,
            icon_path=args.icon_path,
            fmt=args.format,
        )
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    written = len({record["output"] for record in records})
    action = "Would generate" if args.dry_run else "Generated"
    if args.dedup:
        print(f"{action} {written} unique icons for {count} items")
    else:
        print(f"{action} {count} icons")
    if records:
        print(f"First: {records[0]['output']}")
        print(f"Last:  {records[-1]['output']}")
    if not args.dry_run:
        print(f"Manifest: {args.manifest}")
        if args.dedup:
            print(f"Aliases:  {args.aliases}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
