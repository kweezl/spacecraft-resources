"""Parse the `spaceObject` sheet from SpaceCraft data.cdb into space_objects.json.

Pure logic; src/commands/parse_space_objects.py drives it. Mirrors craft.py.
The localized `name` is excluded (i18n section `spaceObject`). `props.floors`
and `props.buyout` are normalized; other props keys pass through.
"""
import json
from pathlib import Path


def load_cdb(path) -> dict:
    with Path(path).open("r", encoding="utf-8") as file:
        return json.load(file)


def find_sheet(cdb: dict, name: str) -> dict:
    for sheet in cdb.get("sheets", []):
        if sheet.get("name") == name:
            return sheet
    raise ValueError(f"Sheet {name!r} not found in data.cdb")


def normalize_floors(entries) -> list[dict]:
    """[{instance}] dropping entries without a non-empty `instance`."""
    if not isinstance(entries, list):
        return []
    result = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        instance = entry.get("instance")
        if not isinstance(instance, str) or not instance:
            continue
        result.append({"instance": instance})
    return result


def normalize_buyout(entries) -> list[dict]:
    """[{item, price?, value?, props?}] dropping entries without a non-empty `item`."""
    if not isinstance(entries, list):
        return []
    result = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        item = entry.get("item")
        if not isinstance(item, str) or not item:
            continue
        offer = {"item": item}
        for field in ("price", "value"):
            if field in entry:
                offer[field] = entry[field]
        props = entry.get("props")
        if isinstance(props, dict) and props:
            offer["props"] = props
        result.append(offer)
    return result


def normalize_props(props) -> dict:
    if not isinstance(props, dict):
        return {}
    out = {}
    floors = normalize_floors(props.get("floors"))
    if floors:
        out["floors"] = floors
    buyout = normalize_buyout(props.get("buyout"))
    if buyout:
        out["buyout"] = buyout
    for key, value in props.items():
        if key not in ("floors", "buyout"):
            out[key] = value
    return out


def parse_space_object(row: dict) -> dict | None:
    object_id = row.get("id")
    if not isinstance(object_id, str) or not object_id:
        return None
    record = {"id": object_id}
    for field in ("owner", "building"):
        value = row.get(field)
        if isinstance(value, str) and value:
            record[field] = value
    region = row.get("region")
    if isinstance(region, dict) and region:
        record["region"] = region
    props = normalize_props(row.get("props"))
    if props:
        record["props"] = props
    return record


def parse_space_objects(cdb_path) -> dict:
    cdb_path = Path(cdb_path)
    cdb = load_cdb(cdb_path)
    sheet = find_sheet(cdb, "spaceObject")

    objects: dict[str, dict] = {}
    skipped = 0
    for row in sheet.get("lines", []):
        if not isinstance(row, dict):
            skipped += 1
            continue
        record = parse_space_object(row)
        if record is None:
            skipped += 1
            continue
        if record["id"] in objects:
            raise ValueError(f"Duplicate space object id {record['id']!r}")
        objects[record["id"]] = record

    return {
        "source": cdb_path.as_posix(),
        "sheet": "spaceObject",
        "count": len(objects),
        "skipped": skipped,
        "spaceObjects": objects,
    }
