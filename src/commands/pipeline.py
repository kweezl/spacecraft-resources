import typer

from src.commands import (
    generate_icons,
    parse_contracts,
    parse_craft,
    parse_factions,
    parse_item_categories,
    parse_items,
    parse_space_objects,
    parse_translations,
    parse_workshops,
)
from src.lib import config
from src.lib.env import resolve

# Each step runs with env/default-resolved settings. generate-icons deduplicates
# inline by default and writes aliases.json. The two extra icon sets (categories,
# factions) write to their own dirs + alias maps because their ids are not
# globally unique and so cannot share aliases.json.
STEPS = [
    ("parse-items", lambda dry_run: parse_items.run(dry_run=dry_run)),
    ("parse-craft", lambda dry_run: parse_craft.run(dry_run=dry_run)),
    ("parse-workshops", lambda dry_run: parse_workshops.run(dry_run=dry_run)),
    ("parse-contracts", lambda dry_run: parse_contracts.run(dry_run=dry_run)),
    ("parse-item-categories", lambda dry_run: parse_item_categories.run(dry_run=dry_run)),
    ("parse-space-objects", lambda dry_run: parse_space_objects.run(dry_run=dry_run)),
    ("parse-factions", lambda dry_run: parse_factions.run(dry_run=dry_run)),
    ("parse-translations", lambda dry_run: parse_translations.run(dry_run=dry_run)),
    ("generate-icons", lambda dry_run: generate_icons.run(dry_run=dry_run)),
    ("generate-icons-categories", lambda dry_run: generate_icons.run(
        dry_run=dry_run,
        sheet="itemType",
        out=resolve(None, config.GENERATE_ICONS_CATEGORIES_OUT),
        manifest=resolve(None, config.GENERATE_ICONS_CATEGORIES_MANIFEST),
        aliases=resolve(None, config.GENERATE_ICONS_CATEGORIES_ALIASES),
    )),
    ("generate-icons-factions", lambda dry_run: generate_icons.run(
        dry_run=dry_run,
        sheet="faction",
        icon_path="props.logo",
        out=resolve(None, config.GENERATE_ICONS_FACTIONS_OUT),
        manifest=resolve(None, config.GENERATE_ICONS_FACTIONS_MANIFEST),
        aliases=resolve(None, config.GENERATE_ICONS_FACTIONS_ALIASES),
    )),
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
