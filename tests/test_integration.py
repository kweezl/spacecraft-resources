"""End-to-end parsing/generation against the unpacked game resources.

These exercise the real ``src/lib`` logic over an actual unpacked dataset:
the real ``unpacked/`` locally (when present) or the committed mock fixture
otherwise (CI). Assertions check structure and invariants rather than exact
counts, so they hold for both the rich real data and the tiny fixture.

See ``tests/support.py`` for how the unpacked root is resolved.
"""
import json
import tempfile
import unittest
from pathlib import Path

from src.lib import (
    contracts,
    craft,
    factions,
    generate_icons,
    item_categories,
    parse_items,
    parse_translations,
    space_objects,
    workshops,
)
from tests.support import cdb_path, lang_dir, unpacked_root


class ParseItemsIntegration(unittest.TestCase):
    def test_items_parse_with_valid_shape(self):
        result = parse_items.parse_items(cdb_path())
        items = result["items"]
        self.assertGreater(result["count"], 0, "no items parsed")
        self.assertEqual(result["count"], len(items))
        for item_id, item in items.items():
            self.assertEqual(item["id"], item_id, "id must match its key")
            self.assertIsInstance(item.get("type"), str, "item needs a string type")


class ParseCraftIntegration(unittest.TestCase):
    def test_recipes_parse_with_valid_shape(self):
        result = craft.parse_craft(cdb_path())
        recipes = result["recipes"]
        self.assertGreater(result["count"], 0, "no recipes parsed")
        self.assertEqual(result["count"], len(recipes))
        for recipe_id, recipe in recipes.items():
            self.assertEqual(recipe["id"], recipe_id)
            for io_field in ("inputs", "outputs"):
                self.assertIsInstance(recipe.get(io_field), list)
                for io in recipe[io_field]:
                    self.assertIn("item", io)
                    self.assertIn("qty", io)


class ParseTranslationsIntegration(unittest.TestCase):
    def test_english_from_cdb(self):
        cdb = parse_translations.load_cdb(cdb_path())
        sheets = parse_translations.translations_from_cdb(cdb)
        items = sheets.get("item")
        self.assertTrue(items, "no English item translations")
        for entry in items.values():
            self.assertTrue({"name", "desc"} & entry.keys())

    def test_each_export_xml_parses(self):
        exports = sorted(lang_dir().glob("export_*.xml"))
        self.assertTrue(exports, "no export_<lang>.xml files found")
        for xml_path in exports:
            with self.subTest(lang=parse_translations.lang_of(xml_path)):
                sheets = parse_translations.translations_from_xml(xml_path)
                self.assertTrue(sheets.get("item"), "no item translations in export")


class GenerateIconsIntegration(unittest.TestCase):
    def test_full_icon_generation(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            out_dir = tmp / "icons"
            manifest = tmp / "icons_manifest.json"
            aliases = tmp / "aliases.json"
            count, records = generate_icons.generate_icons(
                cdb_path=cdb_path(),
                assets_root=unpacked_root(),
                out_dir=out_dir,
                manifest_path=manifest,
                allowed_icon_files=None,
                recolor=True,
                clean=False,
                dry_run=False,
                dedup=True,
                aliases_path=aliases,
                sheet="item",
                fmt="png",
            )
            self.assertGreater(count, 0, "no icons generated")
            self.assertEqual(count, len(records))

            manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(manifest_data["count"], count)

            alias_data = json.loads(aliases.read_text(encoding="utf-8"))
            # Every aliased id resolves to an icon file that was written.
            for icon_id, fname in alias_data["icons"].items():
                self.assertTrue((out_dir / fname).exists(), f"{icon_id} -> missing {fname}")


class NewParsersIntegration(unittest.TestCase):
    def test_workshops_shape(self):
        result = workshops.parse_workshops(cdb_path())
        self.assertGreater(result["count"], 0)
        for wid, rec in result["workshops"].items():
            self.assertEqual(rec["id"], wid)
            self.assertTrue(wid.startswith("Workshop_"))
            self.assertNotIn("label", rec)

    def test_contracts_shape(self):
        result = contracts.parse_contracts(cdb_path())
        self.assertGreater(result["count"], 0)
        for cid, rec in result["contracts"].items():
            self.assertEqual(rec["id"], cid)
            self.assertNotIn("title", rec)

    def test_item_categories_shape(self):
        result = item_categories.parse_item_categories(cdb_path())
        self.assertGreater(result["count"], 0)
        for cid, rec in result["categories"].items():
            self.assertEqual(rec["id"], cid)
            self.assertNotIn("name", rec)

    def test_space_objects_shape(self):
        result = space_objects.parse_space_objects(cdb_path())
        self.assertGreater(result["count"], 0)
        for oid, rec in result["spaceObjects"].items():
            self.assertEqual(rec["id"], oid)
            self.assertNotIn("name", rec)

    def test_factions_shape(self):
        result = factions.parse_factions(cdb_path())
        self.assertGreater(result["count"], 0)
        for fid, rec in result["factions"].items():
            self.assertEqual(rec["id"], fid)
            self.assertNotIn("name", rec)


class NewTranslationSectionsIntegration(unittest.TestCase):
    def test_cdb_has_new_sections(self):
        sheets = parse_translations.translations_from_cdb(parse_translations.load_cdb(cdb_path()))
        for section in ("workshop", "contract", "spaceObject", "faction", "instance"):
            self.assertIn(section, sheets)
        for entry in sheets["workshop"].values():
            self.assertIn("name", entry)


if __name__ == "__main__":
    unittest.main()
