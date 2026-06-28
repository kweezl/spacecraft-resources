import typer

from src.commands import (
    generate_icons,
    parse_craft,
    parse_items,
    parse_translations,
)

# Each step runs with env/default-resolved settings. generate-icons deduplicates
# inline by default and writes aliases.json, so no separate deduplicate-icons
# step is needed here; that command remains available standalone for analysis.
STEPS = [
    ("parse-items", lambda dry_run: parse_items.run(dry_run=dry_run)),
    ("parse-craft", lambda dry_run: parse_craft.run(dry_run=dry_run)),
    ("parse-translations", lambda dry_run: parse_translations.run(dry_run=dry_run)),
    ("generate-icons", lambda dry_run: generate_icons.run(dry_run=dry_run)),
]


def run(dry_run: bool = False) -> int:
    for name, step in STEPS:
        typer.echo(f"== {name} ==")
        code = step(dry_run)
        if code != 0:
            typer.echo(f"pipeline aborted at {name} (exit {code})", err=True)
            return code
    return 0


def command(
    dry_run: bool = typer.Option(False, "--dry-run", help="Run each step in dry-run mode where supported."),
) -> None:
    raise typer.Exit(run(dry_run=dry_run))
