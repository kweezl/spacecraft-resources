"""Parse the `faction` sheet from SpaceCraft data.cdb into factions.json.

Pure logic; src/commands/parse_factions.py drives it. Mirrors craft.py.
The localized `name` is excluded (i18n section `faction`). The row-level `icon`
is a generic placeholder (identical for all factions) and is dropped; the real
per-faction art lives in `props.logo`, kept inside `props`.
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


def parse_faction(row: dict) -> dict | None:
    faction_id = row.get("id")
    if not isinstance(faction_id, str) or not faction_id:
        return None
    record = {"id": faction_id}
    props = row.get("props")
    if isinstance(props, dict) and props:
        record["props"] = props
    return record


def parse_factions(cdb_path) -> dict:
    cdb_path = Path(cdb_path)
    cdb = load_cdb(cdb_path)
    sheet = find_sheet(cdb, "faction")

    factions: dict[str, dict] = {}
    skipped = 0
    for row in sheet.get("lines", []):
        if not isinstance(row, dict):
            skipped += 1
            continue
        record = parse_faction(row)
        if record is None:
            skipped += 1
            continue
        if record["id"] in factions:
            raise ValueError(f"Duplicate faction id {record['id']!r}")
        factions[record["id"]] = record

    return {
        "source": cdb_path.as_posix(),
        "sheet": "faction",
        "count": len(factions),
        "skipped": skipped,
        "factions": factions,
    }
