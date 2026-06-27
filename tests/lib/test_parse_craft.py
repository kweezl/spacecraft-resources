import json
import tempfile
import unittest
from pathlib import Path

from src.lib import craft


def make_cdb(lines):
    return {"sheets": [{"name": "craft", "lines": lines}]}


class NormalizeIoTests(unittest.TestCase):
    def test_qty_defaults_to_one(self):
        self.assertEqual(
            craft.normalize_io([{"item": "IronOre"}]),
            [{"item": "IronOre", "qty": 1}],
        )

    def test_qty_preserved(self):
        self.assertEqual(
            craft.normalize_io([{"item": "Steel", "qty": 3}]),
            [{"item": "Steel", "qty": 3}],
        )

    def test_drops_itemless_entries(self):
        self.assertEqual(craft.normalize_io([{"qty": 2}, {"item": ""}]), [])

    def test_non_list_returns_empty(self):
        self.assertEqual(craft.normalize_io(None), [])


class ParseRecipeTests(unittest.TestCase):
    def test_full_recipe_drops_guid_and_note(self):
        row = {
            "id": "Steel",
            "guid": "#abc",
            "note": "x",
            "inputs": [{"qty": 4, "item": "IronIngot"}, {"qty": 4, "item": "Carbon"}],
            "outputs": [{"item": "Steel", "qty": 3}],
            "where": "Workshop_Smelter",
            "category": "Craft_Alloy",
            "unlockType": 0,
            "props": {"craftTimeFactor": 2},
        }
        self.assertEqual(craft.parse_recipe(row), {
            "id": "Steel",
            "inputs": [{"item": "IronIngot", "qty": 4}, {"item": "Carbon", "qty": 4}],
            "outputs": [{"item": "Steel", "qty": 3}],
            "where": "Workshop_Smelter",
            "category": "Craft_Alloy",
            "unlockType": 0,
            "props": {"craftTimeFactor": 2},
        })

    def test_null_where_omitted(self):
        rec = craft.parse_recipe({"id": "X", "where": None, "outputs": [{"item": "X"}]})
        self.assertNotIn("where", rec)

    def test_empty_props_omitted(self):
        rec = craft.parse_recipe({"id": "X", "props": {}, "outputs": [{"item": "X"}]})
        self.assertNotIn("props", rec)

    def test_loot_level_present_and_absent(self):
        self.assertEqual(
            craft.parse_recipe({"id": "X", "lootLevel": 5, "outputs": [{"item": "X"}]})["lootLevel"], 5
        )
        self.assertNotIn(
            "lootLevel", craft.parse_recipe({"id": "X", "outputs": [{"item": "X"}]})
        )

    def test_missing_id_returns_none(self):
        self.assertIsNone(craft.parse_recipe({"outputs": [{"item": "X"}]}))


class ParseCraftTests(unittest.TestCase):
    def _run(self, lines):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data.cdb"
            path.write_text(json.dumps(make_cdb(lines)), encoding="utf-8")
            return craft.parse_craft(path)

    def test_envelope_and_count(self):
        result = self._run([
            {"id": "A", "outputs": [{"item": "A"}]},
            {"id": "B", "outputs": [{"item": "B"}]},
        ])
        self.assertEqual(result["sheet"], "craft")
        self.assertEqual(result["count"], 2)
        self.assertEqual(result["skipped"], 0)
        self.assertEqual(set(result["recipes"]), {"A", "B"})

    def test_skips_idless_and_nondict_rows(self):
        result = self._run([
            {"id": "A", "outputs": [{"item": "A"}]},
            {"outputs": [{"item": "B"}]},
            "not-a-dict",
        ])
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["skipped"], 2)

    def test_duplicate_id_raises(self):
        with self.assertRaises(ValueError):
            self._run([
                {"id": "A", "outputs": [{"item": "A"}]},
                {"id": "A", "outputs": [{"item": "A"}]},
            ])

    def test_missing_sheet_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data.cdb"
            path.write_text(json.dumps({"sheets": []}), encoding="utf-8")
            with self.assertRaises(ValueError):
                craft.parse_craft(path)


if __name__ == "__main__":
    unittest.main()
