import os
import unittest
from unittest import mock

from src.commands import parse_items as cmd


class ParseItemsCommandTests(unittest.TestCase):
    def test_run_defaults(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch("src.lib.parse_items.main", return_value=0) as m:
                code = cmd.run()
        self.assertEqual(code, 0)
        self.assertEqual(
            m.call_args.args[0],
            ["--data", "unpacked/data.cdb", "--out", "generated/items.json"],
        )

    def test_dry_run_flag(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch("src.lib.parse_items.main", return_value=0) as m:
                cmd.run(dry_run=True)
        self.assertIn("--dry-run", m.call_args.args[0])

    def test_env_then_cli_precedence(self):
        with mock.patch.dict(os.environ, {"SC_DATA": "env.cdb"}, clear=True):
            with mock.patch("src.lib.parse_items.main", return_value=0) as m:
                cmd.run()  # env applies
            argv = m.call_args.args[0]
            self.assertIn("env.cdb", argv)
            with mock.patch("src.lib.parse_items.main", return_value=0) as m:
                cmd.run(data="cli.cdb")  # cli overrides env
            self.assertIn("cli.cdb", m.call_args.args[0])
            self.assertNotIn("env.cdb", m.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
