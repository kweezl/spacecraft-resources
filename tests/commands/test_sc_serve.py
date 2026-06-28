import os
import unittest
from unittest import mock

from src.commands import serve as cmd


class ServeCommandTests(unittest.TestCase):
    def test_run_defaults(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch("src.lib.serve.serve", return_value=0) as m:
                code = cmd.run()
        self.assertEqual(code, 0)
        kwargs = m.call_args.kwargs
        self.assertEqual(kwargs["host"], "127.0.0.1")
        self.assertEqual(kwargs["port"], 8000)
        self.assertTrue(kwargs["open_browser"])

    def test_no_open(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch("src.lib.serve.serve", return_value=0) as m:
                cmd.run(open_browser=False)
        self.assertFalse(m.call_args.kwargs["open_browser"])

    def test_env_overrides(self):
        with mock.patch.dict(os.environ, {"SC_SERVE_PORT": "9000"}, clear=True):
            with mock.patch("src.lib.serve.serve", return_value=0) as m:
                cmd.run()
        self.assertEqual(m.call_args.kwargs["port"], 9000)

    def test_cli_overrides_env(self):
        with mock.patch.dict(os.environ, {"SC_SERVE_PORT": "9000"}, clear=True):
            with mock.patch("src.lib.serve.serve", return_value=0) as m:
                cmd.run(port="7777")
        self.assertEqual(m.call_args.kwargs["port"], 7777)


if __name__ == "__main__":
    unittest.main()
