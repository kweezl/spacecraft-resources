#!/usr/bin/env python3
"""Tiny static file server for the items inspector (server/items.html).

The inspector loads generated/*.json over HTTP (browsers block file:// fetches),
so this serves the repo root and opens the page. Dotfiles (.env, .git, ...) are
blocked so a local server never hands them out.

Runnable standalone (`python server/serve.py`) or via `python sc.py serve`.
"""
import argparse
import functools
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

# Repo root is the parent of this server/ directory.
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PAGE = "server/items.html"


def is_hidden_path(request_path: str) -> bool:
    """True if any component of the URL path is a dotfile/dot-dir (.env, .git)."""
    path = unquote(urlsplit(request_path).path)
    return any(part.startswith(".") for part in path.split("/") if part)


class SafeHandler(SimpleHTTPRequestHandler):
    """SimpleHTTPRequestHandler that refuses to serve dotfiles/dot-dirs."""

    def send_head(self):
        if is_hidden_path(self.path):
            self.send_error(404, "Not found")
            return None
        return super().send_head()


def serve(directory: Path, host: str, port: int, page: str, open_browser: bool) -> int:
    directory = Path(directory).resolve()
    if not directory.is_dir():
        print(f"serve: directory not found: {directory}")
        return 2

    handler = functools.partial(SafeHandler, directory=str(directory))
    httpd = ThreadingHTTPServer((host, port), handler)
    url = f"http://{host}:{port}/{page.lstrip('/')}"
    print(f"Serving {directory} at http://{host}:{port}/  (Ctrl+C to stop)")
    print(f"Open: {url}")

    if open_browser:
        webbrowser.open(url)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        httpd.server_close()
    return 0


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Serve the items inspector over HTTP.")
    parser.add_argument("--dir", type=Path, default=REPO_ROOT, help="Directory to serve (default: repo root).")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1).")
    parser.add_argument("--port", type=int, default=8000, help="Bind port (default: 8000).")
    parser.add_argument("--page", default=DEFAULT_PAGE, help="Page path to open (default: server/items.html).")
    parser.add_argument("--no-open", dest="open_browser", action="store_false", help="Do not open a browser.")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    return serve(args.dir, args.host, args.port, args.page, args.open_browser)


if __name__ == "__main__":
    raise SystemExit(main())
