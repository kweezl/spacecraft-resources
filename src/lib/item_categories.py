"""Parse the `itemType` sheet from SpaceCraft data.cdb into item_categories.json.

Pure logic; src/commands/parse_item_categories.py drives it. Mirrors craft.py.
The localized `name` is excluded — it already ships in the i18n `itemType`
section produced by parse_translations. Reuses parse_items' icon/attribute
cleaners so categories and items share one normalization.
"""
import json
from pathlib import Path

from src.lib.parse_items import clean_attributes, clean_icon


def load_cdb(path) -> dict:
    with Path(path).open("r", encoding="utf-8") as file:
        return json.load(file)


def find_sheet(cdb: dict, name: str) -> dict:
    for sheet in cdb.get("sheets", []):
        if sheet.get("name") == name:
            return sheet
    raise ValueError(f"Sheet {name!r} not found in data.cdb")


def parse_category(row: dict) -> dict | None:
    category_id = row.get("id")
    if not isinstance(category_id, str) or not category_id:
        return None
    record = {"id": category_id}
    parent = row.get("parent")
    if isinstance(parent, str) and parent:
        record["parent"] = parent
    icon = clean_icon(row.get("icon"))
    if icon is not None:
        record["icon"] = icon
    attributes = clean_attributes(row.get("defaultAttributes"))
    if attributes:
        record["defaultAttributes"] = attributes
    props = row.get("props")
    if isinstance(props, dict) and props:
        record["props"] = props
    return record


def parse_item_categories(cdb_path) -> dict:
    cdb_path = Path(cdb_path)
    cdb = load_cdb(cdb_path)
    sheet = find_sheet(cdb, "itemType")

    categories: dict[str, dict] = {}
    skipped = 0
    for row in sheet.get("lines", []):
        if not isinstance(row, dict):
            skipped += 1
            continue
        record = parse_category(row)
        if record is None:
            skipped += 1
            continue
        if record["id"] in categories:
            raise ValueError(f"Duplicate category id {record['id']!r}")
        categories[record["id"]] = record

    return {
        "source": cdb_path.as_posix(),
        "sheet": "itemType",
        "count": len(categories),
        "skipped": skipped,
        "categories": categories,
    }
