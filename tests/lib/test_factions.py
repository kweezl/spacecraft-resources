import json
import tempfile
import unittest
from pathlib import Path

from src.lib import factions


def make_cdb(lines):
    return {"sheets": [{"name": "faction", "lines": lines}]}


class ParseFactionTests(unittest.TestCase):
    def test_keeps_props_drops_name_and_icon(self):
        row = {
            "id": "TheCo", "name": "The Company",
            "icon": {"file": "ui/actionIcons.png", "size": 24, "x": 0, "y": 0},
            "props": {"logo": {"file": "ui/icons/FactionIcons.png", "size": 16,
                               "x": 0, "y": 0, "width": 4, "height": 4}},
        }
        self.assertEqual(factions.parse_faction(row), {
            "id": "TheCo",
            "props": {"logo": {"file": "ui/icons/FactionIcons.png", "size": 16,
                              "x": 0, "y": 0, "width": 4, "height": 4}},
        })

    def test_empty_props_omitted(self):
        self.assertEqual(factions.parse_faction({"id": "Players", "props": {}}), {"id": "Players"})

    def test_missing_id_returns_none(self):
        self.assertIsNone(factions.parse_faction({"name": "x"}))


class ParseFactionsTests(unittest.TestCase):
    def _run(self, lines):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data.cdb"
            path.write_text(json.dumps(make_cdb(lines)), encoding="utf-8")
            return factions.parse_factions(path)

    def test_envelope_and_count(self):
        result = self._run([{"id": "A"}, {"id": "B"}, "not-a-dict"])
        self.assertEqual(result["sheet"], "faction")
        self.assertEqual(result["count"], 2)
        self.assertEqual(result["skipped"], 1)
        self.assertEqual(set(result["factions"]), {"A", "B"})

    def test_duplicate_id_raises(self):
        with self.assertRaises(ValueError):
            self._run([{"id": "A"}, {"id": "A"}])

    def test_missing_sheet_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data.cdb"
            path.write_text(json.dumps({"sheets": []}), encoding="utf-8")
            with self.assertRaises(ValueError):
                factions.parse_factions(path)


if __name__ == "__main__":
    unittest.main()
