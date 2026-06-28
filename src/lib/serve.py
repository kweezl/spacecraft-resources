"""Dev-only static server for the resources inspector (src/public/index.html).

The inspector loads generated/*.json over HTTP (browsers block file:// fetches).
A small mount table maps URL prefixes to directories (the nginx `location` idea):

    /generated  ->  <repo>/generated     # committed pipeline output, read in place
    /           ->  <repo>/src/public     # the single-page-app source

This gives the local server the *same* URL layout as GitHub Pages, so one
`index.html` (data-base="./generated") works in both. Dotfiles (.env, .git, ...)
are refused so a local server never hands them out. Reached via `python sc.py serve`.
"""
import functools
import os
import posixpath
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

# Repo root is two levels up from this file (src/lib/serve.py).
REPO_ROOT = Path(__file__).resolve().parents[2]
PUBLIC_DIR = REPO_ROOT / "src" / "public"
GENERATED_DIR = REPO_ROOT / "generated"


def default_mounts() -> list[tuple[str, Path]]:
    """URL prefix -> directory, longest prefix first ('/' is the fallback)."""
    return [
        ("/generated", GENERATED_DIR),
        ("/", PUBLIC_DIR),
    ]


def is_hidden_path(request_path: str) -> bool:
    """True if any component of the URL path is a dotfile/dot-dir (.env, .git)."""
    path = unquote(urlsplit(request_path).path)
    return any(part.startswith(".") for part in path.split("/") if part)


def resolve_fs_path(url_path: str, mounts: list[tuple[str, Path]]) -> str:
    """Map a URL path to a filesystem path via the mount table.

    Mirrors SimpleHTTPRequestHandler.translate_path's sanitization (no traversal
    escapes the mount root), but routes to the directory of the longest matching
    URL prefix instead of a single fixed root.
    """
    raw = url_path.split("?", 1)[0].split("#", 1)[0]
    trailing_slash = raw.rstrip().endswith("/")
    try:
        decoded = unquote(raw, errors="surrogatepass")
    except UnicodeDecodeError:
        decoded = unquote(raw)
    decoded = posixpath.normpath(decoded)
    if not decoded.startswith("/"):
        decoded = "/" + decoded

    root, rest = _match_mount(decoded, mounts)
    fs = str(root)
    for word in filter(None, rest.split("/")):
        if os.path.dirname(word) or word in (os.curdir, os.pardir):
            continue
        fs = os.path.join(fs, word)
    if trailing_slash:
        fs += "/"
    return fs


def _match_mount(path: str, mounts: list[tuple[str, Path]]) -> tuple[Path, str]:
    for prefix, root in mounts:
        if prefix == "/":
            return root, path
        if path == prefix:
            return root, "/"
        if path.startswith(prefix + "/"):
            return root, path[len(prefix):]
    return mounts[-1][1], path


class MountHandler(SimpleHTTPRequestHandler):
    """Static handler that routes by mount table and refuses dotfiles/dot-dirs."""

    def __init__(self, *args, mounts: list[tuple[str, Path]], **kwargs):
        self._mounts = mounts
        super().__init__(*args, **kwargs)

    def translate_path(self, path: str) -> str:
        return resolve_fs_path(path, self._mounts)

    def end_headers(self):
        # Dev-only: never cache, so edited JS/HTML/JSON always reload fresh.
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def send_head(self):
        if is_hidden_path(self.path):
            self.send_error(404, "Not found")
            return None
        return super().send_head()


def serve(
    host: str,
    port: int,
    open_browser: bool = True,
    mounts: list[tuple[str, Path]] | None = None,
) -> int:
    mounts = list(mounts) if mounts is not None else default_mounts()
    public_root = Path(mounts[-1][1])
    if not public_root.is_dir():
        print(f"serve: directory not found: {public_root}")
        return 2

    handler = functools.partial(MountHandler, mounts=mounts, directory=str(REPO_ROOT))
    httpd = ThreadingHTTPServer((host, port), handler)
    url = f"http://{host}:{port}/"
    print(f"Serving the inspector at {url}  (Ctrl+C to stop)")

    if open_browser:
        webbrowser.open(url)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        httpd.server_close()
    return 0
