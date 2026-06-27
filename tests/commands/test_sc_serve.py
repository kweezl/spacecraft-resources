import os
import unittest
from unittest import mock

from src.commands import serve as cmd


class ServeCommandTests(unittest.TestCase):
    def test_run_defaults(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch("server.serve.main", return_value=0) as m:
                code = cmd.run()
        self.assertEqual(code, 0)
        argv = m.call_args.args[0]
        # No SC_SERVE_DIR -> no --dir (server defaults to repo root).
        self.assertNotIn("--dir", argv)
        self.assertEqual(argv[argv.index("--host") + 1], "127.0.0.1")
        self.assertEqual(argv[argv.index("--port") + 1], "8000")
        self.assertNotIn("--no-open", argv)

    def test_no_open(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch("server.serve.main", return_value=0) as m:
                cmd.run(open_browser=False)
        self.assertIn("--no-open", m.call_args.args[0])

    def test_env_overrides(self):
        env = {"SC_SERVE_PORT": "9000", "SC_SERVE_DIR": "generated"}
        with mock.patch.dict(os.environ, env, clear=True):
            with mock.patch("server.serve.main", return_value=0) as m:
                cmd.run()
        argv = m.call_args.args[0]
        self.assertEqual(argv[argv.index("--port") + 1], "9000")
        self.assertEqual(argv[argv.index("--dir") + 1], "generated")

    def test_cli_overrides_env(self):
        with mock.patch.dict(os.environ, {"SC_SERVE_PORT": "9000"}, clear=True):
            with mock.patch("server.serve.main", return_value=0) as m:
                cmd.run(port="7777")
        argv = m.call_args.args[0]
        self.assertEqual(argv[argv.index("--port") + 1], "7777")


if __name__ == "__main__":
    unittest.main()
