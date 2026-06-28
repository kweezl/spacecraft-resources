"""Parse the `craft` sheet from SpaceCraft data.cdb into a bot-friendly craft.json.

Pure logic, no CLI — the Typer command in src/commands/parse_craft.py drives it.
Mirrors parse_items' shape but lives under src/ (the target project structure).

Translatable strings (item names) are NOT included here; the recipes inspector
resolves them from the per-language translation files.
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


def normalize_io(entries) -> list[dict]:
    """Normalize an inputs/outputs list to [{item, qty}] with qty always explicit.

    qty defaults to 1 when absent. Entries without a non-empty `item` are dropped.
    """
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


def parse_recipe(row: dict) -> dict | None:
    recipe_id = row.get("id")
    if not isinstance(recipe_id, str) or not recipe_id:
        return None

    record = {
        "id": recipe_id,
        "inputs": normalize_io(row.get("inputs")),
        "outputs": normalize_io(row.get("outputs")),
    }

    where = row.get("where")
    if isinstance(where, str) and where:
        record["where"] = where
    category = row.get("category")
    if isinstance(category, str) and category:
        record["category"] = category
    if "unlockType" in row:
        record["unlockType"] = row["unlockType"]
    if "lootLevel" in row:
        record["lootLevel"] = row["lootLevel"]

    props = row.get("props")
    if isinstance(props, dict) and props:
        record["props"] = props
    return record


def parse_craft(cdb_path) -> dict:
    cdb_path = Path(cdb_path)
    cdb = load_cdb(cdb_path)
    sheet = find_sheet(cdb, "craft")

    recipes: dict[str, dict] = {}
    skipped = 0
    for row in sheet.get("lines", []):
        if not isinstance(row, dict):
            skipped += 1
            continue
        record = parse_recipe(row)
        if record is None:
            skipped += 1
            continue
        if record["id"] in recipes:
            raise ValueError(f"Duplicate recipe id {record['id']!r}")
        recipes[record["id"]] = record

    return {
        "source": cdb_path.as_posix(),
        "sheet": "craft",
        "count": len(recipes),
        "skipped": skipped,
        "recipes": recipes,
    }
