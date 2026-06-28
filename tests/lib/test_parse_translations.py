import tempfile
import unittest
from pathlib import Path

from src.lib import parse_translations as pt
from src.lib import parse_translations as script


class CdbSectionsTests(unittest.TestCase):
    def test_workshop_from_itemtag_filtered_and_label(self):
        cdb = {"sheets": [{"name": "itemTag", "lines": [
            {"id": "Workshop_Smelter", "props": {"label": "Smelter"}},
            {"id": "NotAWorkshop", "props": {"label": "nope"}},
        ]}]}
        out = pt.translations_from_cdb(cdb)
        self.assertEqual(out["workshop"], {"Workshop_Smelter": {"name": "Smelter"}})

    def test_contract_title_becomes_name(self):
        cdb = {"sheets": [{"name": "contract", "lines": [
            {"id": "Tuto", "title": "Module Kit Sample"}]}]}
        out = pt.translations_from_cdb(cdb)
        self.assertEqual(out["contract"], {"Tuto": {"name": "Module Kit Sample"}})

    def test_faction_and_instance_names(self):
        cdb = {"sheets": [
            {"name": "faction", "lines": [{"id": "TheCo", "name": "The Company"}]},
            {"name": "instance", "lines": [{"id": "DockStart", "name": "Docking Bay"}]},
        ]}
        out = pt.translations_from_cdb(cdb)
        self.assertEqual(out["faction"], {"TheCo": {"name": "The Company"}})
        self.assertEqual(out["instance"], {"DockStart": {"name": "Docking Bay"}})


class XmlSectionsTests(unittest.TestCase):
    XML = """<?xml version="1.0" encoding="utf-8"?>
<root>
  <sheet name="itemTag">
    <Workshop_Smelter><props.label>Fonderie</props.label></Workshop_Smelter>
    <NotAWorkshop><props.label>nope</props.label></NotAWorkshop>
  </sheet>
  <sheet name="contract">
    <Tuto><title>Echantillon</title></Tuto>
  </sheet>
</root>"""

    def test_xml_source_and_prefix(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "export_fr.xml"
            path.write_text(self.XML, encoding="utf-8")
            out = pt.translations_from_xml(path)
        self.assertEqual(out["workshop"], {"Workshop_Smelter": {"name": "Fonderie"}})
        self.assertEqual(out["contract"], {"Tuto": {"name": "Echantillon"}})


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
