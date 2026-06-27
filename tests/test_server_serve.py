import tempfile
import unittest
from pathlib import Path
from unittest import mock

from server import serve


class IsHiddenPathTests(unittest.TestCase):
    def test_blocks_dotfiles_and_dotdirs(self):
        self.assertTrue(serve.is_hidden_path("/.env"))
        self.assertTrue(serve.is_hidden_path("/.git/config"))
        self.assertTrue(serve.is_hidden_path("/sub/.secret"))

    def test_allows_normal_paths(self):
        self.assertFalse(serve.is_hidden_path("/server/items.html"))
        self.assertFalse(serve.is_hidden_path("/generated/items.json"))
        self.assertFalse(serve.is_hidden_path("/generated/icons/IronOre.webp"))


class _FakeServer:
    last = None

    def __init__(self, address, handler):
        self.address = address
        self.handler = handler
        _FakeServer.last = self

    def serve_forever(self):
        raise KeyboardInterrupt  # simulate Ctrl+C immediately

    def server_close(self):
        pass


class ServeTests(unittest.TestCase):
    def test_missing_directory_returns_2(self):
        code = serve.serve(Path("does/not/exist"), "127.0.0.1", 8000, "server/items.html", False)
        self.assertEqual(code, 2)

    def test_binds_and_opens_browser(self):
        opened = {}
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(serve, "ThreadingHTTPServer", _FakeServer), \
                 mock.patch.object(serve, "webbrowser") as wb:
                wb.open.side_effect = lambda url: opened.setdefault("url", url)
                code = serve.serve(Path(tmp), "127.0.0.1", 8123, "server/items.html", True)
        self.assertEqual(code, 0)
        self.assertEqual(_FakeServer.last.address, ("127.0.0.1", 8123))
        self.assertEqual(opened["url"], "http://127.0.0.1:8123/server/items.html")

    def test_no_open_does_not_launch_browser(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(serve, "ThreadingHTTPServer", _FakeServer), \
                 mock.patch.object(serve, "webbrowser") as wb:
                serve.serve(Path(tmp), "127.0.0.1", 8123, "server/items.html", False)
                wb.open.assert_not_called()


if __name__ == "__main__":
    unittest.main()
