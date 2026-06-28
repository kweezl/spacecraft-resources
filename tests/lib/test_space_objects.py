import json
import tempfile
import unittest
from pathlib import Path

from src.lib import space_objects


def make_cdb(lines):
    return {"sheets": [{"name": "spaceObject", "lines": lines}]}


class ParseSpaceObjectTests(unittest.TestCase):
    def test_normalizes_floors_and_buyout_drops_name(self):
        row = {
            "id": "Station_Start", "name": "Babylon", "owner": "TheCo",
            "building": "SpaceStation1",
            "props": {
                "floors": [{"instance": "DockStart", "props": {}}, {"props": {}}],
                "buyout": [
                    {"item": "Quartz", "value": 24.99, "props": {"mission": "M"}},
                    {"item": "MetalBolt", "props": {}, "price": 6, "value": 5.99},
                    {"props": {}},
                ],
            },
        }
        rec = space_objects.parse_space_object(row)
        self.assertNotIn("name", rec)
        self.assertEqual(rec["owner"], "TheCo")
        self.assertEqual(rec["building"], "SpaceStation1")
        self.assertEqual(rec["props"]["floors"], [{"instance": "DockStart"}])
        self.assertEqual(rec["props"]["buyout"], [
            {"item": "Quartz", "value": 24.99, "props": {"mission": "M"}},
            {"item": "MetalBolt", "price": 6, "value": 5.99},
        ])

    def test_other_props_pass_through(self):
        rec = space_objects.parse_space_object({"id": "X", "props": {"foo": 1}})
        self.assertEqual(rec["props"], {"foo": 1})

    def test_empty_props_omitted(self):
        rec = space_objects.parse_space_object({"id": "Empty", "props": {}})
        self.assertEqual(rec, {"id": "Empty"})

    def test_missing_id_returns_none(self):
        self.assertIsNone(space_objects.parse_space_object({"name": "x"}))


class ParseSpaceObjectsTests(unittest.TestCase):
    def _run(self, lines):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data.cdb"
            path.write_text(json.dumps(make_cdb(lines)), encoding="utf-8")
            return space_objects.parse_space_objects(path)

    def test_envelope_and_count(self):
        result = self._run([{"id": "A"}, {"id": "B"}, "not-a-dict"])
        self.assertEqual(result["sheet"], "spaceObject")
        self.assertEqual(result["count"], 2)
        self.assertEqual(result["skipped"], 1)
        self.assertEqual(set(result["spaceObjects"]), {"A", "B"})

    def test_duplicate_id_raises(self):
        with self.assertRaises(ValueError):
            self._run([{"id": "A"}, {"id": "A"}])

    def test_missing_sheet_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data.cdb"
            path.write_text(json.dumps({"sheets": []}), encoding="utf-8")
            with self.assertRaises(ValueError):
                space_objects.parse_space_objects(path)


if __name__ == "__main__":
    unittest.main()
