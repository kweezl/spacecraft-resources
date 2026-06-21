import unittest

import deduplicate_icons as dd


def entry(file="sheet.png", size=64, x=0, y=0, w=1, h=1, colors=None, positions=None):
    e = {
        "id": f"{file}:{x},{y}",
        "source": {"file": file, "size": size, "x": x, "y": y, "width": w, "height": h},
    }
    if colors is not None:
        e["color"] = {"colors": colors, "positions": positions}
    return e


class DedupKeyTests(unittest.TestCase):
    def test_same_crop_same_color_share_key(self):
        a = entry(x=2, y=3, colors=["#fff"], positions=[0.0])
        b = entry(x=2, y=3, colors=["#fff"], positions=[0.0])
        self.assertEqual(dd.dedup_key(a), dd.dedup_key(b))

    def test_same_crop_different_color_differ(self):
        a = entry(x=2, y=3, colors=["#fff"], positions=[0.0])
        b = entry(x=2, y=3, colors=["#000"], positions=[0.0])
        self.assertNotEqual(dd.dedup_key(a), dd.dedup_key(b))

    def test_same_xy_different_sheet_or_size_differ(self):
        base = entry(x=2, y=3)
        self.assertNotEqual(dd.dedup_key(base), dd.dedup_key(entry(file="other.png", x=2, y=3)))
        self.assertNotEqual(dd.dedup_key(base), dd.dedup_key(entry(size=32, x=2, y=3)))

    def test_colored_and_uncolored_same_crop_differ(self):
        self.assertNotEqual(
            dd.dedup_key(entry(x=2, y=3)),
            dd.dedup_key(entry(x=2, y=3, colors=["#fff"], positions=[0.0])),
        )


class AnalyzeTests(unittest.TestCase):
    def test_counts_and_grouping(self):
        manifest = {
            "icons": {
                "A": entry(x=0, y=0),
                "B": entry(x=0, y=0),  # dup of A
                "C": entry(x=0, y=0),  # dup of A
                "D": entry(x=1, y=1, colors=["#abc"], positions=[0.0]),
                "E": entry(x=1, y=1, colors=["#abc"], positions=[0.0]),  # dup of D
                "F": entry(x=9, y=9),  # unique
            }
        }
        report = dd.analyze(manifest)
        self.assertEqual(report.total, 6)
        self.assertEqual(report.unique, 3)
        self.assertEqual(report.removable, 3)
        # canonical = first id seen per group; aliases map dup -> canonical
        self.assertEqual(report.aliases["B"], "A")
        self.assertEqual(report.aliases["C"], "A")
        self.assertEqual(report.aliases["E"], "D")
        self.assertNotIn("A", report.aliases)
        self.assertNotIn("F", report.aliases)
        self.assertEqual(report.largest_group, 3)


if __name__ == "__main__":
    unittest.main()
