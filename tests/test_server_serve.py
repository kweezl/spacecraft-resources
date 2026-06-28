import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src.lib import serve

# A fixed mount table for path-resolution tests (longest URL prefix first).
MOUNTS = [("/generated", Path("gen")), ("/", Path("pub"))]


def norm(path: str) -> str:
    return os.path.normpath(path)


class IsHiddenPathTests(unittest.TestCase):
    def test_blocks_dotfiles_and_dotdirs(self):
        self.assertTrue(serve.is_hidden_path("/.env"))
        self.assertTrue(serve.is_hidden_path("/.git/config"))
        self.assertTrue(serve.is_hidden_path("/generated/.secret"))

    def test_allows_normal_paths(self):
        self.assertFalse(serve.is_hidden_path("/index.html"))
        self.assertFalse(serve.is_hidden_path("/app.js"))
        self.assertFalse(serve.is_hidden_path("/generated/items.json"))


class ResolveFsPathTests(unittest.TestCase):
    def test_root_maps_to_public(self):
        self.assertEqual(norm(serve.resolve_fs_path("/", MOUNTS)), norm("pub"))

    def test_app_js_maps_to_public(self):
        self.assertEqual(serve.resolve_fs_path("/app.js", MOUNTS), os.path.join("pub", "app.js"))

    def test_components_map_to_public(self):
        self.assertEqual(
            serve.resolve_fs_path("/components/items-view.js", MOUNTS),
            os.path.join("pub", "components", "items-view.js"),
        )

    def test_generated_maps_to_generated_dir(self):
        self.assertEqual(
            serve.resolve_fs_path("/generated/items.json", MOUNTS),
            os.path.join("gen", "items.json"),
        )

    def test_generated_icons_map_to_generated_dir(self):
        self.assertEqual(
            serve.resolve_fs_path("/generated/icons/IronOre.webp", MOUNTS),
            os.path.join("gen", "icons", "IronOre.webp"),
        )

    def test_query_and_fragment_are_stripped(self):
        self.assertEqual(
            serve.resolve_fs_path("/generated/items.json?v=1#x", MOUNTS),
            os.path.join("gen", "items.json"),
        )

    def test_traversal_cannot_escape_root(self):
        resolved = norm(serve.resolve_fs_path("/../../etc/passwd", MOUNTS))
        self.assertTrue(resolved.startswith(norm("pub")), resolved)


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
    def test_missing_public_dir_returns_2(self):
        mounts = [("/generated", Path("gen")), ("/", Path("does/not/exist"))]
        code = serve.serve("127.0.0.1", 8000, open_browser=False, mounts=mounts)
        self.assertEqual(code, 2)

    def test_binds_and_opens_browser_at_root(self):
        opened = {}
        with tempfile.TemporaryDirectory() as tmp:
            mounts = [("/generated", Path(tmp)), ("/", Path(tmp))]
            with mock.patch.object(serve, "ThreadingHTTPServer", _FakeServer), \
                 mock.patch.object(serve, "webbrowser") as wb:
                wb.open.side_effect = lambda url: opened.setdefault("url", url)
                code = serve.serve("127.0.0.1", 8123, open_browser=True, mounts=mounts)
        self.assertEqual(code, 0)
        self.assertEqual(_FakeServer.last.address, ("127.0.0.1", 8123))
        self.assertEqual(opened["url"], "http://127.0.0.1:8123/")

    def test_no_open_does_not_launch_browser(self):
        with tempfile.TemporaryDirectory() as tmp:
            mounts = [("/generated", Path(tmp)), ("/", Path(tmp))]
            with mock.patch.object(serve, "ThreadingHTTPServer", _FakeServer), \
                 mock.patch.object(serve, "webbrowser") as wb:
                serve.serve("127.0.0.1", 8123, open_browser=False, mounts=mounts)
                wb.open.assert_not_called()


if __name__ == "__main__":
    unittest.main()
