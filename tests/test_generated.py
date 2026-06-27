"""Validation of the committed ``generated/`` release resources.

These tests validate the *output* that ships in the repository. They do NOT
need ``unpacked/`` (the raw game source) and therefore run anywhere, including
CI. Three concerns are covered:

1. Source-leak guardrail -- raw game source must never be tracked by git.
2. JSON validity + schema -- every generated JSON parses and has the shape
   downstream apps rely on.
3. PNG asset sanity -- every icon is a valid, non-empty image.
"""

import json
import subprocess
import unittest
from pathlib import Path

import deduplicate_icons
import generate_icons

REPO = Path(__file__).resolve().parents[1]
GENERATED = REPO / "generated"
I18N = GENERATED / "i18n"
ICONS = GENERATED / "icons"

# Raw game source / assets must never be committed (game policy). The guardrail
# fails if anything tracked lives under these dirs or carries these extensions.
FORBIDDEN_TRACKED_DIRS = ("unpacked/", "__pycache__/")
FORBIDDEN_TRACKED_SUFFIXES = (".cdb", ".assets", ".bundle", ".resource", ".resS", ".unity3d")

# Generous ceiling: recoloured 64px icons are a few KB; anything near this is a
# sign a full sprite sheet or source asset slipped in.
MAX_ICON_BYTES = 256 * 1024


def tracked_files():
    out = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return [line.strip() for line in out.splitlines() if line.strip()]


class SourceLeakGuardTests(unittest.TestCase):
    """The policy tripwire: raw game source may never enter version control."""

    def setUp(self):
        try:
            self.tracked = tracked_files()
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            self.skipTest(f"git not available: {exc}")

    def test_no_source_directories_tracked(self):
        leaked = [
            path
            for path in self.tracked
            for bad in FORBIDDEN_TRACKED_DIRS
            if path == bad.rstrip("/") or path.startswith(bad)
        ]
        self.assertEqual(leaked, [], f"Raw source committed to git: {leaked}")

    def test_no_source_asset_extensions_tracked(self):
        leaked = [
            path
            for path in self.tracked
            if path.lower().endswith(tuple(s.lower() for s in FORBIDDEN_TRACKED_SUFFIXES))
        ]
        self.assertEqual(leaked, [], f"Raw game asset committed to git: {leaked}")


class JsonValidityTests(unittest.TestCase):
    """Every generated JSON parses and matches the documented shape."""

    def _load(self, path):
        self.assertTrue(path.exists(), f"missing: {path}")
        with path.open(encoding="utf-8") as handle:
            try:
                return json.load(handle)
            except json.JSONDecodeError as exc:
                self.fail(f"invalid JSON in {path.name}: {exc}")

    def test_all_generated_json_parses(self):
        files = sorted(GENERATED.rglob("*.json"))
        self.assertTrue(files, "no JSON found under generated/")
        for path in files:
            with self.subTest(file=path.name):
                self._load(path)

    def test_translation_schema(self):
        files = sorted(I18N.glob("translation.*.json"))
        self.assertTrue(files, "no translation files found")
        for path in files:
            with self.subTest(file=path.name):
                data = self._load(path)
                # filename token: translation.<lang>.json
                lang = path.name[len("translation."):-len(".json")]
                self.assertEqual(data.get("lang"), lang, "lang must match filename")
                items = data.get("item")
                self.assertIsInstance(items, dict, "missing 'item' object")
                self.assertTrue(items, "'item' object is empty")
                for key, entry in items.items():
                    self.assertIsInstance(entry, dict, f"{key}: entry not an object")
                    # An entry carries a 'name' and/or a 'desc' (a few are
                    # desc-only, e.g. EmptyAttachment); present fields must be
                    # non-empty strings.
                    self.assertTrue(
                        {"name", "desc"} & entry.keys(),
                        f"{key}: entry has neither 'name' nor 'desc'",
                    )
                    for field in ("name", "desc"):
                        if field in entry:
                            self.assertIsInstance(
                                entry[field], str, f"{key}: '{field}' not a string"
                            )
                            self.assertTrue(entry[field], f"{key}: empty '{field}'")

    def test_items_schema(self):
        data = self._load(GENERATED / "items.json")
        items = data.get("items")
        self.assertIsInstance(items, dict, "missing 'items' object")
        self.assertEqual(data.get("count"), len(items), "'count' must match item total")
        for key, entry in items.items():
            self.assertIsInstance(entry, dict, f"{key}: entry not an object")
            self.assertEqual(entry.get("id"), key, f"{key}: 'id' must match its key")
            self.assertIsInstance(entry.get("type"), str, f"{key}: missing string 'type'")

    def test_icons_manifest_schema(self):
        data = self._load(GENERATED / "icons_manifest.json")
        icons = data.get("icons")
        self.assertIsInstance(icons, dict, "missing 'icons' object")
        self.assertEqual(data.get("count"), len(icons), "'count' must match icon total")
        for key, entry in icons.items():
            self.assertIsInstance(entry, dict, f"{key}: entry not an object")
            self.assertEqual(entry.get("id"), key, f"{key}: 'id' must match its key")
            self.assertIsInstance(entry.get("output"), str, f"{key}: missing 'output' path")


class AliasMapTests(unittest.TestCase):
    """generated/aliases.json must stay in sync with the manifest and resolve."""

    def setUp(self):
        path = GENERATED / "aliases.json"
        if not path.exists():
            self.skipTest("aliases.json not present")
        with path.open(encoding="utf-8") as handle:
            self.aliases = json.load(handle)
        with (GENERATED / "icons_manifest.json").open(encoding="utf-8") as handle:
            self.manifest = json.load(handle)

    def test_alias_map_matches_manifest(self):
        # Recompute from the manifest; a drifted aliases.json fails here.
        report = deduplicate_icons.analyze(self.manifest)
        expected = deduplicate_icons.build_alias_map(self.manifest, report)
        self.assertEqual(self.aliases, expected, "aliases.json is stale; regenerate it")

    def test_every_aliased_icon_file_exists(self):
        for icon_id, fname in self.aliases["icons"].items():
            with self.subTest(icon=icon_id):
                self.assertTrue((ICONS / fname).exists(), f"{icon_id} -> missing {fname}")


class IconAssetSanityTests(unittest.TestCase):
    """Every shipped icon is a valid, non-empty, reasonably-sized image."""

    def _icon_files(self):
        return sorted(list(ICONS.glob("*.png")) + list(ICONS.glob("*.webp")))

    def test_icons_directory_present(self):
        self.assertTrue(ICONS.is_dir(), "generated/icons/ is missing")
        self.assertTrue(self._icon_files(), "no icons found")

    def test_every_icon_is_valid_and_bounded(self):
        from PIL import Image

        for path in self._icon_files():
            with self.subTest(icon=path.name):
                raw = path.read_bytes()
                self.assertTrue(raw, "empty file")
                self.assertLessEqual(
                    len(raw), MAX_ICON_BYTES, "icon larger than expected ceiling"
                )
                with Image.open(path) as image:
                    image.load()
                    self.assertGreater(image.width, 0, "zero width")
                    self.assertGreater(image.height, 0, "zero height")


if __name__ == "__main__":
    unittest.main()
