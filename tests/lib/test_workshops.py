import json
import tempfile
import unittest
from pathlib import Path

from src.lib import workshops


def make_cdb(lines):
    return {"sheets": [{"name": "itemTag", "lines": lines}]}


class ParseWorkshopTests(unittest.TestCase):
    def test_keeps_prop_fields_drops_label(self):
        row = {"id": "Workshop_Smelter", "props": {
            "label": "Smelter", "craftAction": "SmelterButton",
            "autoCraftTime": 180, "manualCraftTime": 5, "craftIndex": 0}}
        self.assertEqual(workshops.parse_workshop(row), {
            "id": "Workshop_Smelter", "craftAction": "SmelterButton",
            "autoCraftTime": 180, "manualCraftTime": 5, "craftIndex": 0})

    def test_non_workshop_id_returns_none(self):
        self.assertIsNone(workshops.parse_workshop({"id": "SomeTag", "props": {}}))

    def test_missing_id_returns_none(self):
        self.assertIsNone(workshops.parse_workshop({"props": {}}))


class ParseWorkshopsTests(unittest.TestCase):
    def _run(self, lines):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data.cdb"
            path.write_text(json.dumps(make_cdb(lines)), encoding="utf-8")
            return workshops.parse_workshops(path)

    def test_envelope_filters_to_workshops(self):
        result = self._run([
            {"id": "Workshop_Smelter", "props": {"label": "S"}},
            {"id": "NotAWorkshop", "props": {}},
            "not-a-dict",
        ])
        self.assertEqual(result["sheet"], "itemTag")
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["skipped"], 1)
        self.assertEqual(set(result["workshops"]), {"Workshop_Smelter"})

    def test_duplicate_id_raises(self):
        with self.assertRaises(ValueError):
            self._run([
                {"id": "Workshop_A", "props": {}},
                {"id": "Workshop_A", "props": {}},
            ])

    def test_missing_sheet_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data.cdb"
            path.write_text(json.dumps({"sheets": []}), encoding="utf-8")
            with self.assertRaises(ValueError):
                workshops.parse_workshops(path)


class WorkshopTimesTests(unittest.TestCase):
    def test_maps_auto_and_manual(self):
        cdb = make_cdb([
            {"id": "Workshop_Smelter", "props": {"autoCraftTime": 180, "manualCraftTime": 5}},
            {"id": "Workshop_Bottle", "props": {"autoCraftTime": 5}},
            {"id": "NotAWorkshop", "props": {"autoCraftTime": 1}},
        ])
        self.assertEqual(workshops.workshop_times(cdb), {
            "Workshop_Smelter": {"auto": 180, "manual": 5},
            "Workshop_Bottle": {"auto": 5, "manual": None},
        })

    def test_missing_itemtag_sheet_is_tolerated(self):
        self.assertEqual(workshops.workshop_times({"sheets": []}), {})


if __name__ == "__main__":
    unittest.main()
