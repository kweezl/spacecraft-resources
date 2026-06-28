"""Parse the `contract` sheet from SpaceCraft data.cdb into contracts.json.

Pure logic; src/commands/parse_contracts.py drives it. Mirrors craft.py.
The localized `title` is excluded (i18n section `contract`); so are the
editor-only `guid` and `creditFormula__f`. `creditFormula` is the precomputed
credit reward; `props.creditFactor` is its multiplier on item market value.
"""
import json
from pathlib import Path

ESSENTIAL_FIELDS = ("client", "npc", "level", "duration", "creditFormula")


def load_cdb(path) -> dict:
    with Path(path).open("r", encoding="utf-8") as file:
        return json.load(file)


def find_sheet(cdb: dict, name: str) -> dict:
    for sheet in cdb.get("sheets", []):
        if sheet.get("name") == name:
            return sheet
    raise ValueError(f"Sheet {name!r} not found in data.cdb")


def normalize_items(entries) -> list[dict]:
    """[{item, qty}] with qty defaulting to 1; drop entries without a non-empty item."""
    if not isinstance(entries, list):
        return []
    result = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        item = entry.get("item")
        if not isinstance(item, str) or not item:
            continue
        result.append({"item": item, "qty": entry.get("qty", 1)})
    return result


def normalize_rewards(entries) -> list[dict]:
    """[{item, count}] with count defaulting to 1; drop entries without a non-empty item."""
    if not isinstance(entries, list):
        return []
    result = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        item = entry.get("item")
        if not isinstance(item, str) or not item:
            continue
        result.append({"item": item, "count": entry.get("count", 1)})
    return result


def parse_contract(row: dict) -> dict | None:
    contract_id = row.get("id")
    if not isinstance(contract_id, str) or not contract_id:
        return None
    record = {"id": contract_id}
    for field in ESSENTIAL_FIELDS:
        if field in row:
            record[field] = row[field]
    items = normalize_items(row.get("items"))
    if items:
        record["items"] = items
    rewards = normalize_rewards(row.get("rewards"))
    if rewards:
        record["rewards"] = rewards
    props = row.get("props")
    if isinstance(props, dict) and props:
        record["props"] = props
    return record


def parse_contracts(cdb_path) -> dict:
    cdb_path = Path(cdb_path)
    cdb = load_cdb(cdb_path)
    sheet = find_sheet(cdb, "contract")

    contracts: dict[str, dict] = {}
    skipped = 0
    for row in sheet.get("lines", []):
        if not isinstance(row, dict):
            skipped += 1
            continue
        record = parse_contract(row)
        if record is None:
            skipped += 1
            continue
        if record["id"] in contracts:
            raise ValueError(f"Duplicate contract id {record['id']!r}")
        contracts[record["id"]] = record

    return {
        "source": cdb_path.as_posix(),
        "sheet": "contract",
        "count": len(contracts),
        "skipped": skipped,
        "contracts": contracts,
    }
