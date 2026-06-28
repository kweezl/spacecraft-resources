#!/usr/bin/env python3
"""Parse the `item` sheet from SpaceCraft data.cdb into a bot-friendly items.json.

Pure logic plus a thin argparse ``main`` driven by src/commands/parse_items.py.

Re-run after the game updates its data.cdb to regenerate the output.
Output is intentionally lean ("bot essentials") and keeps raw CDB codes for
`type`, `tags`, `skills` and attribute `attr` ids so the bot can resolve them
from its own tables.

Translatable strings (`name`, `desc`) are NOT included here; they live in the
per-language translation files produced by parse_translations.py.
"""
import argparse
import json
import sys
from pathlib import Path

# Top-level fields copied verbatim from each item row when present.
ESSENTIAL_FIELDS = ("id", "type", "price", "lootLevel", "storage")
# Icon sub-fields kept (drops nothing useful; bot crops or maps to an emoji).
ICON_FIELDS = ("file", "size", "x", "y", "width", "height")


def load_cdb(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def find_sheet(cdb: dict, name: str) -> dict:
    for sheet in cdb.get("sheets", []):
        if sheet.get("name") == name:
            return sheet
    raise ValueError(f"Sheet {name!r} not found in data.cdb")


def clean_icon(icon) -> dict | None:
    if not isinstance(icon, dict):
        return None
    out = {key: icon[key] for key in ICON_FIELDS if key in icon}
    # Tiles are 1x1 unless stated; make that explicit for the bot.
    out.setdefault("width", 1)
    out.setdefault("height", 1)
    return out or None


def clean_attributes(attributes) -> list[dict]:
    if not isinstance(attributes, list):
        return []
    result = []
    for entry in attributes:
        if not isinstance(entry, dict):
            continue
        attr = entry.get("attr")
        if attr is None:
            continue
        result.append({"attr": attr, "value": entry.get("value")})
    return result


def collect_ids(value, key: str) -> list:
    """Flatten a CDB list-of-objects (e.g. [{"skill": "X"}]) to a list of ids."""
    if not isinstance(value, list):
        return []
    out = []
    for entry in value:
        if isinstance(entry, dict) and entry.get(key) is not None:
            out.append(entry[key])
    return out


def collect_tags(props: dict) -> list:
    """Merge the singular `tag` string and the `tags` list into one list."""
    tags = []
    single = props.get("tag")
    if isinstance(single, str) and single:
        tags.append(single)
    for tag in collect_ids(props.get("tags"), "tag"):
        if tag not in tags:
            tags.append(tag)
    return tags


def parse_item(row: dict) -> dict | None:
    item_id = row.get("id")
    if not isinstance(item_id, str) or not item_id:
        return None

    record = {field: row[field] for field in ESSENTIAL_FIELDS if field in row}
    record["id"] = item_id  # guarantee id is first/present

    props = row.get("props") if isinstance(row.get("props"), dict) else {}
    if props.get("refDesc"):
        record["refDesc"] = props["refDesc"]

    tags = collect_tags(props)
    if tags:
        record["tags"] = tags
    skills = collect_ids(props.get("skills"), "skill")
    if skills:
        record["skills"] = skills
    compatible = collect_ids(props.get("compatibleSkills"), "skill")
    if compatible:
        record["compatibleSkills"] = compatible
    loot = collect_ids(props.get("lootMaterial"), "item")
    if loot:
        record["lootMaterial"] = loot

    record["attributes"] = clean_attributes(row.get("attributes"))
    icon = clean_icon(row.get("icon"))
    if icon is not None:
        record["icon"] = icon
    return record


def parse_items(cdb_path: Path) -> dict:
    cdb = load_cdb(cdb_path)
    sheet = find_sheet(cdb, "item")

    items: dict[str, dict] = {}
    skipped = 0
    for row in sheet.get("lines", []):
        if not isinstance(row, dict):
            skipped += 1
            continue
        record = parse_item(row)
        if record is None:
            skipped += 1
            continue
        if record["id"] in items:
            raise ValueError(f"Duplicate item id {record['id']!r}")
        items[record["id"]] = record

    return {
        "source": cdb_path.as_posix(),
        "sheet": "item",
        "count": len(items),
        "skipped": skipped,
        "items": items,
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Parse items from SpaceCraft data.cdb into items.json.")
    parser.add_argument("--data", type=Path, default=Path("unpacked/data.cdb"), help="Path to data.cdb JSON.")
    parser.add_argument("--out", type=Path, default=Path("generated/items.json"), help="Output JSON path.")
    parser.add_argument("--dry-run", action="store_true", help="Parse and report counts without writing the file.")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    try:
        result = parse_items(args.data)
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    if not args.dry_run:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    action = "Would parse" if args.dry_run else "Parsed"
    print(f"{action} {result['count']} items ({result['skipped']} skipped)")
    if not args.dry_run:
        print(f"Output: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
