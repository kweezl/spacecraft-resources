import json
import tempfile
import unittest
from pathlib import Path

from src.lib import item_categories


def make_cdb(lines):
    return {"sheets": [{"name": "itemType", "lines": lines}]}


class ParseCategoryTests(unittest.TestCase):
    def test_keeps_parent_icon_attrs_props_drops_name(self):
        row = {
            "id": "InstanceItem", "name": "Instance Item", "parent": "QuestItem",
            "icon": {"file": "ui/itemIcons.png", "size": 18, "x": 0, "y": 0},
            "defaultAttributes": [{"attr": "StorageUnits", "value": 0}],
            "props": {"flags": 1024},
        }
        rec = item_categories.parse_category(row)
        self.assertNotIn("name", rec)
        self.assertEqual(rec["id"], "InstanceItem")
        self.assertEqual(rec["parent"], "QuestItem")
        self.assertEqual(rec["icon"], {"file": "ui/itemIcons.png", "size": 18, "x": 0, "y": 0, "width": 1, "height": 1})
        self.assertEqual(rec["defaultAttributes"], [{"attr": "StorageUnits", "value": 0}])
        self.assertEqual(rec["props"], {"flags": 1024})

    def test_omits_absent_optional_fields(self):
        rec = item_categories.parse_category({"id": "Virtual"})
        self.assertEqual(rec, {"id": "Virtual"})

    def test_missing_id_returns_none(self):
        self.assertIsNone(item_categories.parse_category({"name": "x"}))


class ParseItemCategoriesTests(unittest.TestCase):
    def _run(self, lines):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data.cdb"
            path.write_text(json.dumps(make_cdb(lines)), encoding="utf-8")
            return item_categories.parse_item_categories(path)

    def test_envelope_and_count(self):
        result = self._run([{"id": "A"}, {"id": "B", "parent": "A"}, "not-a-dict"])
        self.assertEqual(result["sheet"], "itemType")
        self.assertEqual(result["count"], 2)
        self.assertEqual(result["skipped"], 1)
        self.assertEqual(result["categories"]["B"]["parent"], "A")

    def test_duplicate_id_raises(self):
        with self.assertRaises(ValueError):
            self._run([{"id": "A"}, {"id": "A"}])

    def test_missing_sheet_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data.cdb"
            path.write_text(json.dumps({"sheets": []}), encoding="utf-8")
            with self.assertRaises(ValueError):
                item_categories.parse_item_categories(path)


if __name__ == "__main__":
    unittest.main()
