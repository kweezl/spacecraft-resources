import os
import unittest
from unittest import mock

from src.commands import generate_icons as cmd


class GenerateIconsCommandTests(unittest.TestCase):
    def test_run_defaults(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch("generate_icons.main", return_value=0) as m:
                code = cmd.run()
        self.assertEqual(code, 0)
        self.assertEqual(
            m.call_args.args[0],
            [
                "--data", "unpacked/data.cdb",
                "--assets", "unpacked",
                "--out", "generated/icons",
                "--manifest", "generated/icons_manifest.json",
                "--aliases", "generated/aliases.json",
                "--sheet", "item",
                "--dedup",
            ],
        )

    def test_sheet_env(self):
        with mock.patch.dict(os.environ, {"SC_GENERATE_ICONS_SHEET": "resource"}, clear=True):
            with mock.patch("generate_icons.main", return_value=0) as m:
                cmd.run()
        argv = m.call_args.args[0]
        self.assertEqual(argv[argv.index("--sheet") + 1], "resource")

    def test_no_dedup_flag(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch("generate_icons.main", return_value=0) as m:
                cmd.run(dedup=False)
        argv = m.call_args.args[0]
        self.assertIn("--no-dedup", argv)
        self.assertNotIn("--dedup", argv)

    def test_aliases_env(self):
        with mock.patch.dict(os.environ, {"SC_GENERATE_ICONS_ALIASES": "a.json"}, clear=True):
            with mock.patch("generate_icons.main", return_value=0) as m:
                cmd.run()
        argv = m.call_args.args[0]
        self.assertEqual(argv[argv.index("--aliases") + 1], "a.json")

    def test_flags_and_icon_files(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch("generate_icons.main", return_value=0) as m:
                cmd.run(
                    icon_file=["ui/a.png", "ui/b.png"],
                    all_icon_files=True,
                    no_recolor=True,
                    clean=True,
                    dry_run=True,
                )
        argv = m.call_args.args[0]
        self.assertEqual(argv.count("--icon-file"), 2)
        for flag in ("--all-icon-files", "--no-recolor", "--clean", "--dry-run"):
            self.assertIn(flag, argv)

    def test_manifest_env(self):
        with mock.patch.dict(os.environ, {"SC_GENERATE_ICONS_MANIFEST": "m.json"}, clear=True):
            with mock.patch("generate_icons.main", return_value=0) as m:
                cmd.run()
        self.assertIn("m.json", m.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
