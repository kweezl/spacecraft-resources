
import typer

from src.lib import config
from src.lib import parse_items as script
from src.lib.env import resolve


def run(data: str | None = None, out: str | None = None, dry_run: bool = False) -> int:
    argv = [
        "--data", resolve(data, config.DATA),
        "--out", resolve(out, config.PARSE_ITEMS_OUT),
    ]
    if dry_run:
        argv.append("--dry-run")
    return script.main(argv)


def command(
    data: str | None = typer.Option(None, "--data", help="Path to data.cdb. Env: SC_DATA."),
    out: str | None = typer.Option(None, "--out", help="Output JSON path. Env: SC_PARSE_ITEMS_OUT."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Report counts without writing."),
) -> None:
    raise typer.Exit(run(data=data, out=out, dry_run=dry_run))
