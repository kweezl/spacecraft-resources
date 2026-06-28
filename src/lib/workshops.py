"""Parse Workshop_* rows from the `itemTag` sheet into workshops.json.

Pure logic; src/commands/parse_workshops.py drives it. Mirrors craft.py.
Workshops are the crafting stations recipes reference via `where`. Their
localized label (`props.label`) is excluded here — it lives in the per-language
translation files (i18n section `workshop`).
"""
import json
from pathlib import Path

WORKSHOP_PREFIX = "Workshop_"
# props sub-fields kept (structural); the translatable `label` is excluded.
PROP_FIELDS = ("craftAction", "autoCraftTime", "manualCraftTime", "craftIndex")


def load_cdb(path) -> dict:
    with Path(path).open("r", encoding="utf-8") as file:
        return json.load(file)


def find_sheet(cdb: dict, name: str) -> dict:
    for sheet in cdb.get("sheets", []):
        if sheet.get("name") == name:
            return sheet
    raise ValueError(f"Sheet {name!r} not found in data.cdb")


def parse_workshop(row: dict) -> dict | None:
    workshop_id = row.get("id")
    if not isinstance(workshop_id, str) or not workshop_id.startswith(WORKSHOP_PREFIX):
        return None
    props = row.get("props") if isinstance(row.get("props"), dict) else {}
    record = {"id": workshop_id}
    for field in PROP_FIELDS:
        if field in props:
            record[field] = props[field]
    return record


def workshop_times(cdb: dict) -> dict[str, dict]:
    """Map workshop id -> {"auto": autoCraftTime|None, "manual": manualCraftTime|None}.

    Tolerant of a missing `itemTag` sheet (returns {}), so craft-time derivation
    degrades gracefully when called on a CDB that has no workshops.
    """
    try:
        sheet = find_sheet(cdb, "itemTag")
    except ValueError:
        return {}
    times: dict[str, dict] = {}
    for row in sheet.get("lines", []):
        if not isinstance(row, dict):
            continue
        workshop_id = row.get("id")
        if not isinstance(workshop_id, str) or not workshop_id.startswith(WORKSHOP_PREFIX):
            continue
        props = row.get("props") if isinstance(row.get("props"), dict) else {}
        times[workshop_id] = {
            "auto": props.get("autoCraftTime"),
            "manual": props.get("manualCraftTime"),
        }
    return times


def parse_workshops(cdb_path) -> dict:
    cdb_path = Path(cdb_path)
    cdb = load_cdb(cdb_path)
    sheet = find_sheet(cdb, "itemTag")

    workshops: dict[str, dict] = {}
    skipped = 0
    for row in sheet.get("lines", []):
        if not isinstance(row, dict):
            skipped += 1
            continue
        record = parse_workshop(row)
        if record is None:
            continue  # non-workshop tag: out of scope, not a skip
        if record["id"] in workshops:
            raise ValueError(f"Duplicate workshop id {record['id']!r}")
        workshops[record["id"]] = record

    return {
        "source": cdb_path.as_posix(),
        "sheet": "itemTag",
        "count": len(workshops),
        "skipped": skipped,
        "workshops": workshops,
    }
