
import typer

from src.lib import config
from src.lib import parse_translations as script
from src.lib.env import resolve


def run(
    data: str | None = None,
    lang_dir: str | None = None,
    out: str | None = None,
    dry_run: bool = False,
) -> int:
    argv = [
        "--data", resolve(data, config.DATA),
        "--lang-dir", resolve(lang_dir, config.PARSE_TRANSLATIONS_LANG_DIR),
        "--out", resolve(out, config.PARSE_TRANSLATIONS_OUT),
    ]
    if dry_run:
        argv.append("--dry-run")
    return script.main(argv)


def command(
    data: str | None = typer.Option(None, "--data", help="Path to data.cdb. Env: SC_DATA."),
    lang_dir: str | None = typer.Option(None, "--lang-dir", help="export_<lang>.xml folder. Env: SC_PARSE_TRANSLATIONS_LANG_DIR."),
    out: str | None = typer.Option(None, "--out", help="Output dir. Env: SC_PARSE_TRANSLATIONS_OUT."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Report counts without writing."),
) -> None:
    raise typer.Exit(run(data=data, lang_dir=lang_dir, out=out, dry_run=dry_run))
