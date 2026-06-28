import typer

from src.lib import config
from src.lib import serve as server
from src.lib.env import resolve


def run(
    host: str | None = None,
    port: str | None = None,
    open_browser: bool = True,
) -> int:
    return server.serve(
        host=resolve(host, config.SERVE_HOST),
        port=int(resolve(port, config.SERVE_PORT)),
        open_browser=open_browser,
    )


def command(
    host: str | None = typer.Option(None, "--host", help="Bind host. Env: SC_SERVE_HOST."),
    port: str | None = typer.Option(None, "--port", help="Bind port. Env: SC_SERVE_PORT."),
    open_browser: bool = typer.Option(True, "--open/--no-open", help="Open a browser tab (default: open)."),
) -> None:
    raise typer.Exit(run(host=host, port=port, open_browser=open_browser))
