import json
from pathlib import Path

import typer

from src.lib import config, craft
from src.lib.env import resolve


def run(data: str | None = None, out: str | None = None, dry_run: bool = False) -> int:
    data_path = resolve(data, config.DATA)
    out_path = resolve(out, config.PARSE_CRAFT_OUT)
    try:
        result = craft.parse_craft(data_path)
    except Exception as error:
        typer.echo(f"Error: {error}", err=True)
        return 1

    if not dry_run:
        out_file = Path(out_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(
            json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )

    action = "Would parse" if dry_run else "Parsed"
    typer.echo(f"{action} {result['count']} recipes ({result['skipped']} skipped)")
    if not dry_run:
        typer.echo(f"Output: {out_path}")
    return 0


def command(
    data: str | None = typer.Option(None, "--data", help="Path to data.cdb. Env: SC_DATA."),
    out: str | None = typer.Option(None, "--out", help="Output JSON path. Env: SC_PARSE_CRAFT_OUT."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Report counts without writing."),
) -> None:
    raise typer.Exit(run(data=data, out=out, dry_run=dry_run))
