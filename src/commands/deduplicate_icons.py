from typing import Optional

import typer

import deduplicate_icons as script
from src.lib import config
from src.lib.env import resolve


def run(
    manifest: Optional[str] = None,
    write: Optional[str] = None,
    aliases_out: Optional[str] = None,
    icons_dir: Optional[str] = None,
    top: int = 10,
) -> int:
    argv = [
        "--manifest", resolve(manifest, config.DEDUPLICATE_ICONS_MANIFEST),
        "--top", str(top),
    ]
    if write:
        argv += ["--write", str(write)]
    if aliases_out:
        argv += ["--aliases-out", str(aliases_out)]
    if icons_dir:
        argv += ["--icons-dir", str(icons_dir)]
    return script.main(argv)


def command(
    manifest: Optional[str] = typer.Option(None, "--manifest", help="icons_manifest.json. Env: SC_DEDUPLICATE_ICONS_MANIFEST."),
    write: Optional[str] = typer.Option(None, "--write", help="Emit deduplicated icons + aliases.json into this dir."),
    aliases_out: Optional[str] = typer.Option(None, "--aliases-out", help="Write only the alias map JSON to this path."),
    icons_dir: Optional[str] = typer.Option(None, "--icons-dir", help="Source icon dir for --write."),
    top: int = typer.Option(10, "--top", help="How many shared groups to list."),
) -> None:
    raise typer.Exit(
        run(manifest=manifest, write=write, aliases_out=aliases_out, icons_dir=icons_dir, top=top)
    )
