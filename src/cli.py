from pathlib import Path

import typer

from src.commands import (
    deduplicate_icons,
    extract,
    generate_icons,
    parse_items,
    parse_translations,
    pipeline,
    serve,
)
from src.lib.env import load_env

ROOT = Path(__file__).resolve().parents[1]

app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help="SpaceCraft resources tool. Run a command, or no command for help.",
)


@app.callback()
def _bootstrap() -> None:
    """Load .env before any command resolves its options."""
    load_env(ROOT)


app.command("extract")(extract.command)
app.command("parse-items")(parse_items.command)
app.command("parse-translations")(parse_translations.command)
app.command("generate-icons")(generate_icons.command)
app.command("deduplicate-icons")(deduplicate_icons.command)
app.command("pipeline")(pipeline.command)
app.command("serve")(serve.command)
