import unittest

from src.lib import generate_icons


def make_cdb(sheet_name, lines):
    return {"sheets": [{"name": sheet_name, "lines": lines}]}


class IconPathTests(unittest.TestCase):
    def test_dig_resolves_dotted_path(self):
        self.assertEqual(generate_icons.dig({"props": {"logo": 7}}, "props.logo"), 7)
        self.assertIsNone(generate_icons.dig({"props": {}}, "props.logo"))

    def test_iter_jobs_default_uses_row_icon(self):
        cdb = make_cdb("item", [{"id": "A", "icon": {"file": "f.png", "size": 8, "x": 0, "y": 0}}])
        jobs = list(generate_icons.iter_icon_jobs(cdb, sheet="item"))
        self.assertEqual([j.item_id for j in jobs], ["A"])

    def test_iter_jobs_icon_path_reads_nested(self):
        cdb = make_cdb("faction", [
            {"id": "TheCo", "props": {"logo": {"file": "f.png", "size": 16, "x": 0, "y": 0}}},
            {"id": "Players", "props": {}},
        ])
        jobs = list(generate_icons.iter_icon_jobs(cdb, sheet="faction", icon_path="props.logo"))
        self.assertEqual([j.item_id for j in jobs], ["TheCo"])  # Players has no logo


if __name__ == "__main__":
    unittest.main()
