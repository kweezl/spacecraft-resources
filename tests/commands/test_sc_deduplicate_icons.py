import os
import unittest
from unittest import mock

from src.commands import deduplicate_icons as cmd


class DeduplicateIconsCommandTests(unittest.TestCase):
    def test_run_defaults(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch("deduplicate_icons.main", return_value=0) as m:
                code = cmd.run()
        self.assertEqual(code, 0)
        self.assertEqual(
            m.call_args.args[0],
            ["--manifest", "generated/icons_manifest.json", "--top", "10"],
        )

    def test_write_and_aliases(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch("deduplicate_icons.main", return_value=0) as m:
                cmd.run(write="out/dir", aliases_out="aliases.json", icons_dir="icons", top=5)
        argv = m.call_args.args[0]
        self.assertEqual(argv[argv.index("--write") + 1], "out/dir")
        self.assertEqual(argv[argv.index("--aliases-out") + 1], "aliases.json")
        self.assertEqual(argv[argv.index("--icons-dir") + 1], "icons")
        self.assertEqual(argv[argv.index("--top") + 1], "5")

    def test_manifest_env(self):
        with mock.patch.dict(os.environ, {"SC_DEDUPLICATE_ICONS_MANIFEST": "m.json"}, clear=True):
            with mock.patch("deduplicate_icons.main", return_value=0) as m:
                cmd.run()
        self.assertIn("m.json", m.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
