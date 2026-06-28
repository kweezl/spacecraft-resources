import json
import tempfile
import unittest
from pathlib import Path

from src.lib import parse_items


def make_cdb(item_lines, itemtype_lines=None):
    sheets = [{"name": "item", "lines": item_lines}]
    if itemtype_lines is not None:
        sheets.append({"name": "itemType", "lines": itemtype_lines})
    return {"sheets": sheets}


# itemType hierarchy mirroring the real shape: a leaf (no flags) under a
# sub-category (flags 14) under a top-level UI category (flags & 1).
TYPES = [
    {"id": "ShipElement", "props": {"flags": 8448}},
    {"id": "ShipTool", "parent": "ShipElement", "props": {"flags": 1, "categoryIndex": 300}},
    {"id": "ShipGatheringTools", "parent": "ShipTool", "props": {"flags": 14, "categoryIndex": 301}},
    {"id": "MiningTool", "parent": "ShipGatheringTools", "props": {}},
    {"id": "Patch", "props": {"flags": 1, "categoryIndex": 800}},
    {"id": "Orphan", "props": {"flags": 0}},
]


class DisplayCategoryTests(unittest.TestCase):
    def setUp(self):
        self.types = {row["id"]: row for row in TYPES}

    def test_walks_to_nearest_flag_ancestor(self):
        self.assertEqual(parse_items.display_category("MiningTool", self.types), "ShipTool")

    def test_leaf_that_is_a_category_returns_itself(self):
        self.assertEqual(parse_items.display_category("Patch", self.types), "Patch")

    def test_none_when_no_flagged_ancestor(self):
        self.assertIsNone(parse_items.display_category("Orphan", self.types))

    def test_unknown_type_returns_none(self):
        self.assertIsNone(parse_items.display_category("Nope", self.types))

    def test_handles_parent_cycle(self):
        cyclic = {
            "A": {"id": "A", "parent": "B", "props": {}},
            "B": {"id": "B", "parent": "A", "props": {}},
        }
        self.assertIsNone(parse_items.display_category("A", cyclic))


class SubcategoryTests(unittest.TestCase):
    def setUp(self):
        self.types = {row["id"]: row for row in TYPES}

    def test_nearest_indexed_non_main_below_leaf(self):
        self.assertEqual(parse_items.subcategory("MiningTool", self.types), "ShipGatheringTools")

    def test_none_when_leaf_is_a_main_category(self):
        self.assertIsNone(parse_items.subcategory("Patch", self.types))

    def test_leaf_that_is_itself_a_subcategory_returns_itself(self):
        self.assertEqual(parse_items.subcategory("ShipGatheringTools", self.types), "ShipGatheringTools")

    def test_none_for_unknown_type(self):
        self.assertIsNone(parse_items.subcategory("Nope", self.types))


class BuildTypeIndexTests(unittest.TestCase):
    def test_indexes_by_id(self):
        index = parse_items.build_type_index(make_cdb([], TYPES))
        self.assertEqual(set(index), {row["id"] for row in TYPES})

    def test_missing_sheet_is_tolerated(self):
        self.assertEqual(parse_items.build_type_index(make_cdb([])), {})


class ParseItemsDisplayCategoryTests(unittest.TestCase):
    def _run(self, item_lines, itemtype_lines):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data.cdb"
            path.write_text(json.dumps(make_cdb(item_lines, itemtype_lines)), encoding="utf-8")
            return parse_items.parse_items(path)

    def test_item_gets_display_category_and_subcategory(self):
        result = self._run(
            [{"id": "MiningTool_Cold", "type": "MiningTool", "attributes": []}], TYPES
        )
        entry = result["items"]["MiningTool_Cold"]
        self.assertEqual(entry["displayCategory"], "ShipTool")
        self.assertEqual(entry["subcategory"], "ShipGatheringTools")

    def test_unresolved_type_has_no_display_category(self):
        result = self._run(
            [{"id": "Weird", "type": "Orphan", "attributes": []}], TYPES
        )
        self.assertNotIn("displayCategory", result["items"]["Weird"])

    def test_no_itemtype_sheet_means_no_display_category(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data.cdb"
            path.write_text(json.dumps(make_cdb([{"id": "X", "type": "MiningTool", "attributes": []}])), encoding="utf-8")
            result = parse_items.parse_items(path)
        self.assertNotIn("displayCategory", result["items"]["X"])


if __name__ == "__main__":
    unittest.main()
