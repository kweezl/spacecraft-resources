from typing import Optional

import typer

from server import serve as script
from src.lib import config
from src.lib.env import resolve


def run(
    directory: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[str] = None,
    page: Optional[str] = None,
    open_browser: bool = True,
) -> int:
    argv = []
    resolved_dir = resolve(directory, config.SERVE_DIR)
    if resolved_dir:
        argv += ["--dir", resolved_dir]
    argv += ["--host", resolve(host, config.SERVE_HOST)]
    argv += ["--port", resolve(port, config.SERVE_PORT)]
    if page:
        argv += ["--page", page]
    if not open_browser:
        argv.append("--no-open")
    return script.main(argv)


def command(
    directory: Optional[str] = typer.Option(None, "--dir", help="Directory to serve. Env: SC_SERVE_DIR (default: repo root)."),
    host: Optional[str] = typer.Option(None, "--host", help="Bind host. Env: SC_SERVE_HOST."),
    port: Optional[str] = typer.Option(None, "--port", help="Bind port. Env: SC_SERVE_PORT."),
    page: Optional[str] = typer.Option(None, "--page", help="Page to open (default: server/items.html)."),
    open_browser: bool = typer.Option(True, "--open/--no-open", help="Open a browser tab (default: open)."),
) -> None:
    raise typer.Exit(run(directory=directory, host=host, port=port, page=page, open_browser=open_browser))
