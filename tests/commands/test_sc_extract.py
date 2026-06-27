import os
import unittest
from unittest import mock

import extract
from src.commands import extract as cmd


class ExtractMainArgvTests(unittest.TestCase):
    def test_main_accepts_argv_for_help(self):
        # argparse prints help and exits 0 when --help is in the passed argv
        with self.assertRaises(SystemExit) as ctx:
            extract.main(["--help"])
        self.assertEqual(ctx.exception.code, 0)


class ExtractCommandTests(unittest.TestCase):
    def test_run_builds_argv_with_default_out(self):
        with mock.patch("extract.main") as m:
            code = cmd.run("game.pak")
        self.assertEqual(code, 0)
        self.assertEqual(m.call_args.args[0], ["game.pak", "--out", "unpacked"])

    def test_run_passes_list_and_filters(self):
        with mock.patch("extract.main") as m:
            cmd.run("game.pak", list_files=True, ext=["png", "txt"], contains=["icon"])
        argv = m.call_args.args[0]
        self.assertIn("--list", argv)
        self.assertEqual(argv[argv.index("--ext") + 1:argv.index("--ext") + 3], ["png", "txt"])
        self.assertEqual(argv[argv.index("--contains") + 1], "icon")

    def test_cli_out_overrides_env(self):
        with mock.patch.dict("os.environ", {"SC_EXTRACT_OUT": "from_env"}):
            with mock.patch("extract.main") as m:
                cmd.run("game.pak", out="from_cli")
        argv = m.call_args.args[0]
        self.assertIn("from_cli", argv)
        self.assertNotIn("from_env", argv)

    def test_pak_from_env_when_no_argument(self):
        with mock.patch.dict(os.environ, {"SC_EXTRACT_PAK": "env.pak"}, clear=True):
            with mock.patch("extract.main") as m:
                code = cmd.run()
        self.assertEqual(code, 0)
        self.assertEqual(m.call_args.args[0][0], "env.pak")

    def test_cli_pak_overrides_env(self):
        with mock.patch.dict(os.environ, {"SC_EXTRACT_PAK": "env.pak"}, clear=True):
            with mock.patch("extract.main") as m:
                cmd.run(pak="cli.pak")
        self.assertEqual(m.call_args.args[0][0], "cli.pak")

    def test_missing_pak_errors_without_calling_main(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch("extract.main") as m:
                code = cmd.run()
        self.assertEqual(code, 2)
        m.assert_not_called()


if __name__ == "__main__":
    unittest.main()
