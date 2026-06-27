#!/usr/bin/env python3
"""DEPRECATED: this root-level script is kept only for the src/commands wrappers
that still call it. New parsing logic lives under src/ (see src/lib/craft.py and
src/commands/parse_craft.py). Do not add features here; it will be migrated and
removed in a follow-up task.

Deduplicate generated icons by their visual content.

Many items reuse the exact same icon: the same crop of the same sprite sheet
with the same recolour gradient. ``generate_icons.py`` emits one PNG per item,
so visually identical icons are written many times (610 PNGs, only 298 unique).

This tool reads ``generated/icons_manifest.json`` and compares two scenarios:

  * baseline      -- one icon file per item (no deduplication)
  * deduplicated  -- one icon file per unique (crop + colour), with the other
                     items aliased to a shared canonical icon

By default it only reports the comparison. With ``--write OUT`` it emits the
deduplicated icon set plus an ``aliases.json`` map so consumers can still
resolve every item id to a concrete icon file.

Note: Git LFS already stores blobs by content hash, so duplicate PNGs cost no
extra LFS storage. Deduplication shrinks the *working tree* (fewer files) and
makes the item -> icon relationship explicit.
"""

import argparse
import json
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_MANIFEST = Path("generated/icons_manifest.json")


def dedup_key(entry: dict):
    """A hashable key identifying an icon's visual content.

    Two icons are visually identical iff they crop the same region of the same
    sheet (file, size, x, y, width, height) and apply the same colour gradient
    (colours + positions), or both apply no gradient.
    """
    s = entry["source"]
    crop = (
        s["file"],
        s["size"],
        s["x"],
        s["y"],
        s.get("width", 1),
        s.get("height", 1),
    )
    color = entry.get("color")
    if color is None:
        gradient = None
    else:
        gradient = (tuple(color["colors"]), tuple(color["positions"]))
    return (crop, gradient)


@dataclass
class DedupReport:
    total: int
    unique: int
    aliases: dict  # duplicate id -> canonical id
    groups: dict  # canonical id -> [all ids sharing its content]
    largest_group: int

    @property
    def removable(self) -> int:
        return self.total - self.unique


def analyze(manifest: dict) -> DedupReport:
    icons = manifest["icons"]
    canonical_by_key: dict = {}
    groups: dict = {}
    aliases: dict = {}

    for icon_id, entry in icons.items():
        key = dedup_key(entry)
        canonical = canonical_by_key.get(key)
        if canonical is None:
            canonical_by_key[key] = icon_id
            groups[icon_id] = [icon_id]
        else:
            groups[canonical].append(icon_id)
            aliases[icon_id] = canonical

    largest = max((len(ids) for ids in groups.values()), default=0)
    return DedupReport(
        total=len(icons),
        unique=len(groups),
        aliases=aliases,
        groups=groups,
        largest_group=largest,
    )


def print_report(report: DedupReport, top: int = 10) -> None:
    pct = (report.removable / report.total * 100) if report.total else 0.0
    print("Icon deduplication (by crop + colour)")
    print("=" * 38)
    print(f"  baseline (no dedup) : {report.total} icons")
    print(f"  deduplicated        : {report.unique} icons")
    print(f"  removable duplicates: {report.removable} ({pct:.1f}%)")
    print(f"  largest shared group: {report.largest_group} icons")
    multi = {c: ids for c, ids in report.groups.items() if len(ids) > 1}
    print(f"  groups with >1 icon : {len(multi)}")
    if multi:
        print(f"\n  Top {min(top, len(multi))} shared icons:")
        for canonical, ids in sorted(multi.items(), key=lambda kv: -len(kv[1]))[:top]:
            sample = ", ".join(ids[1:6]) + (" ..." if len(ids) > 6 else "")
            print(f"    {canonical:<24} x{len(ids):<3} <- {sample}")


def build_alias_map(manifest: dict, report: DedupReport) -> dict:
    """Map every item id (canonical and alias) to its canonical icon filename."""
    icons = manifest["icons"]
    id_to_file = {}
    for canonical, ids in report.groups.items():
        fname = Path(icons[canonical]["output"]).name
        for icon_id in ids:
            id_to_file[icon_id] = fname
    return {
        "total": report.total,
        "unique": report.unique,
        "icons": dict(sorted(id_to_file.items())),
    }


def write_aliases(manifest: dict, report: DedupReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(build_alias_map(manifest, report), handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(f"\n  wrote {report.unique}->{report.total} alias map to {path}")


def write_deduplicated(manifest: dict, report: DedupReport, src_dir: Path, out_dir: Path) -> None:
    """Copy one canonical PNG per unique icon and write aliases.json."""
    icons = manifest["icons"]
    out_dir.mkdir(parents=True, exist_ok=True)
    copied = 0
    missing = []
    for canonical in report.groups:
        name = Path(icons[canonical]["output"]).name
        src = src_dir / name
        if not src.exists():
            missing.append(name)
            continue
        shutil.copy2(src, out_dir / name)
        copied += 1

    write_aliases(manifest, report, out_dir / "aliases.json")
    print(f"  wrote {copied} canonical icons to {out_dir}")
    if missing:
        print(f"  WARNING: {len(missing)} canonical source PNGs not found, e.g. {missing[:3]}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest", type=Path, default=DEFAULT_MANIFEST, help="path to icons_manifest.json"
    )
    parser.add_argument(
        "--write",
        type=Path,
        metavar="OUT",
        help="emit deduplicated icons + aliases.json into OUT dir",
    )
    parser.add_argument(
        "--aliases-out",
        type=Path,
        metavar="PATH",
        help="write only the alias map JSON to PATH (keeps all icons)",
    )
    parser.add_argument(
        "--icons-dir",
        type=Path,
        help="source icon dir for --write (default: sibling 'icons' of the manifest)",
    )
    parser.add_argument("--top", type=int, default=10, help="how many shared groups to list")
    args = parser.parse_args(argv)

    with args.manifest.open(encoding="utf-8") as handle:
        manifest = json.load(handle)

    report = analyze(manifest)
    print_report(report, top=args.top)

    if args.aliases_out:
        write_aliases(manifest, report, args.aliases_out)

    if args.write:
        src_dir = args.icons_dir or (args.manifest.parent / "icons")
        write_deduplicated(manifest, report, src_dir, args.write)

    return 0


if __name__ == "__main__":
    sys.exit(main())
