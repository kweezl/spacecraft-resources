from typing import List, Optional

import typer

import generate_icons as script
from src.lib import config
from src.lib.env import resolve


def run(
    data: Optional[str] = None,
    assets: Optional[str] = None,
    out: Optional[str] = None,
    manifest: Optional[str] = None,
    aliases: Optional[str] = None,
    sheet: Optional[str] = None,
    icon_file: Optional[List[str]] = None,
    all_icon_files: bool = False,
    no_recolor: bool = False,
    clean: bool = False,
    dry_run: bool = False,
    dedup: bool = True,
) -> int:
    argv = [
        "--data", resolve(data, config.DATA),
        "--assets", resolve(assets, config.ASSETS),
        "--out", resolve(out, config.GENERATE_ICONS_OUT),
        "--manifest", resolve(manifest, config.GENERATE_ICONS_MANIFEST),
        "--aliases", resolve(aliases, config.GENERATE_ICONS_ALIASES),
        "--sheet", resolve(sheet, config.GENERATE_ICONS_SHEET),
    ]
    for value in icon_file or []:
        argv += ["--icon-file", value]
    if all_icon_files:
        argv.append("--all-icon-files")
    if no_recolor:
        argv.append("--no-recolor")
    if clean:
        argv.append("--clean")
    if dry_run:
        argv.append("--dry-run")
    argv.append("--dedup" if dedup else "--no-dedup")
    return script.main(argv)


def command(
    data: Optional[str] = typer.Option(None, "--data", help="Path to data.cdb. Env: SC_DATA."),
    assets: Optional[str] = typer.Option(None, "--assets", help="Unpacked assets root. Env: SC_ASSETS."),
    out: Optional[str] = typer.Option(None, "--out", help="Icon output dir. Env: SC_GENERATE_ICONS_OUT."),
    manifest: Optional[str] = typer.Option(None, "--manifest", help="Manifest path. Env: SC_GENERATE_ICONS_MANIFEST."),
    aliases: Optional[str] = typer.Option(None, "--aliases", help="Alias map path (dedup mode). Env: SC_GENERATE_ICONS_ALIASES."),
    sheet: Optional[str] = typer.Option(None, "--sheet", help="CDB sheet to generate from (default item). Env: SC_GENERATE_ICONS_SHEET."),
    icon_file: Optional[List[str]] = typer.Option(None, "--icon-file", help="Restrict to this CDB icon file (repeatable)."),
    all_icon_files: bool = typer.Option(False, "--all-icon-files", help="Generate every CDB icon entry."),
    no_recolor: bool = typer.Option(False, "--no-recolor", help="Skip CDB color gradients."),
    clean: bool = typer.Option(False, "--clean", help="Delete stale PNGs in the output dir."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Report without writing files."),
    dedup: bool = typer.Option(True, "--dedup/--no-dedup", help="Write only unique icons + aliases.json (default), or one PNG per item."),
) -> None:
    raise typer.Exit(
        run(
            data=data,
            assets=assets,
            out=out,
            manifest=manifest,
            aliases=aliases,
            sheet=sheet,
            icon_file=icon_file,
            all_icon_files=all_icon_files,
            no_recolor=no_recolor,
            clean=clean,
            dry_run=dry_run,
            dedup=dedup,
        )
    )
