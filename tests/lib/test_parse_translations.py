import tempfile
import unittest
from pathlib import Path

import parse_translations as script


class TranslationsFromCdbTests(unittest.TestCase):
    def test_includes_itemtype_names(self):
        cdb = {
            "sheets": [
                {"name": "itemType", "lines": [
                    {"id": "Craft_Alloy", "name": "Alloy"},
                    {"id": "Virtual", "name": "Virtual Item"},
                ]},
                {"name": "item", "lines": [{"id": "IronOre", "name": "Iron Ore"}]},
            ]
        }
        out = script.translations_from_cdb(cdb)
        self.assertIn("itemType", out)
        self.assertEqual(out["itemType"]["Craft_Alloy"], {"name": "Alloy"})
        # item sheet still extracted alongside.
        self.assertEqual(out["item"]["IronOre"], {"name": "Iron Ore"})


class TranslationsFromXmlTests(unittest.TestCase):
    def test_includes_itemtype_names(self):
        xml = (
            '<root><sheet name="itemType">'
            '<Craft_Alloy><name>Legierung</name></Craft_Alloy>'
            "</sheet></root>"
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "export_de.xml"
            path.write_text(xml, encoding="utf-8")
            out = script.translations_from_xml(path)
        self.assertEqual(out["itemType"]["Craft_Alloy"], {"name": "Legierung"})


if __name__ == "__main__":
    unittest.main()
