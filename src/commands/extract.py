from typing import List, Optional

import typer

import extract as script
from src.lib import config
from src.lib.env import resolve


def run(
    pak: str,
    out: Optional[str] = None,
    list_files: bool = False,
    ext: Optional[List[str]] = None,
    contains: Optional[List[str]] = None,
    kind2: Optional[int] = None,
    debug_at: Optional[str] = None,
) -> int:
    argv = [pak, "--out", resolve(out, config.EXTRACT_OUT)]
    if list_files:
        argv.append("--list")
    if ext:
        argv += ["--ext", *ext]
    if contains:
        argv += ["--contains", *contains]
    if kind2 is not None:
        argv += ["--kind2", str(kind2)]
    if debug_at is not None:
        argv += ["--debug-at", debug_at]
    script.main(argv)
    return 0


def command(
    pak: str = typer.Argument(..., help="Path to the .pak archive."),
    out: Optional[str] = typer.Option(None, "--out", help="Output dir. Env: SC_EXTRACT_OUT (default: unpacked)."),
    list_files: bool = typer.Option(False, "--list", help="List archive contents instead of extracting."),
    ext: Optional[List[str]] = typer.Option(None, "--ext", help="Only files with these extensions."),
    contains: Optional[List[str]] = typer.Option(None, "--contains", help="Only paths containing these substrings."),
    kind2: Optional[int] = typer.Option(None, "--kind2", hidden=True),
    debug_at: Optional[str] = typer.Option(None, "--debug-at", hidden=True, help="Hex offset to dump."),
) -> None:
    code = run(
        pak,
        out=out,
        list_files=list_files,
        ext=ext,
        contains=contains,
        kind2=kind2,
        debug_at=debug_at,
    )
    raise typer.Exit(code)
