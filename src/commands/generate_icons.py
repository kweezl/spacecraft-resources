
import typer

from src.lib import config
from src.lib import generate_icons as script
from src.lib.env import resolve


def run(
    data: str | None = None,
    assets: str | None = None,
    out: str | None = None,
    manifest: str | None = None,
    aliases: str | None = None,
    sheet: str | None = None,
    icon_path: str | None = None,
    fmt: str | None = None,
    icon_file: list[str] | None = None,
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
        "--format", resolve(fmt, config.GENERATE_ICONS_FORMAT),
        "--icon-path", icon_path if icon_path is not None else "icon",
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
    data: str | None = typer.Option(None, "--data", help="Path to data.cdb. Env: SC_DATA."),
    assets: str | None = typer.Option(None, "--assets", help="Unpacked assets root. Env: SC_ASSETS."),
    out: str | None = typer.Option(None, "--out", help="Icon output dir. Env: SC_GENERATE_ICONS_OUT."),
    manifest: str | None = typer.Option(None, "--manifest", help="Manifest path. Env: SC_GENERATE_ICONS_MANIFEST."),
    aliases: str | None = typer.Option(None, "--aliases", help="Alias map path (dedup mode). Env: SC_GENERATE_ICONS_ALIASES."),
    sheet: str | None = typer.Option(None, "--sheet", help="CDB sheet to generate from (default item). Env: SC_GENERATE_ICONS_SHEET."),
    icon_path: str | None = typer.Option(None, "--icon-path", help="Dotted row path to the icon object (default icon)."),
    fmt: str | None = typer.Option(None, "--format", help="Icon format: webp (default) or png. Env: SC_GENERATE_ICONS_FORMAT."),
    icon_file: list[str] | None = typer.Option(None, "--icon-file", help="Restrict to this CDB icon file (repeatable)."),
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
            icon_path=icon_path,
            fmt=fmt,
            icon_file=icon_file,
            all_icon_files=all_icon_files,
            no_recolor=no_recolor,
            clean=clean,
            dry_run=dry_run,
            dedup=dedup,
        )
    )
