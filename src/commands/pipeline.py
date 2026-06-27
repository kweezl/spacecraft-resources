import typer

from src.commands import (
    deduplicate_icons,
    generate_icons,
    parse_items,
    parse_translations,
)

# Each step runs with env/default-resolved settings. deduplicate-icons has no
# dry-run mode; it only reports (no writes) unless --write is given, so it is
# safe to include under a dry-run pipeline.
STEPS = [
    ("parse-items", lambda dry_run: parse_items.run(dry_run=dry_run)),
    ("parse-translations", lambda dry_run: parse_translations.run(dry_run=dry_run)),
    ("generate-icons", lambda dry_run: generate_icons.run(dry_run=dry_run)),
    ("deduplicate-icons", lambda dry_run: deduplicate_icons.run()),
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
