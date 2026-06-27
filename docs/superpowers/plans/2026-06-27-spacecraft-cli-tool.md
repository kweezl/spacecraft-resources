# SpaceCraft Resources CLI Tool Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Aggregate the five standalone Python scripts into a single Typer-based console tool (`sc`) that reads a gitignored `.env`, documents every variable in `.env.example`, and resolves each option as CLI flag > env var > built-in default.

**Architecture:** A `src/` package holds a thin command layer (`src/commands/`) and shared helpers (`src/lib/`). Each command builds an argument list from resolved options and delegates to the existing root script's `main(argv)` — the root scripts remain the single source of truth and stay runnable standalone. A `pipeline` command chains the four regen commands. Entry point is `sc.py` (`python sc.py <command>`).

**Tech Stack:** Python 3.14, Typer (on Click), python-dotenv, stdlib `unittest` for tests.

## Global Constraints

- Python 3.14 (`.venv/Scripts/python`); all commands below use that interpreter.
- Dependencies limited to `typer` and `python-dotenv`, pinned in `requirements.txt`. No other runtime deps.
- Tests use stdlib `unittest`, run via `python -m unittest`. No pytest.
- Env var prefix is `SC_`. Shared vars carry no command name; command-specific vars are prefixed with the command name uppercased, `-` → `_`.
- Option precedence per option: **CLI flag > env var > built-in default**.
- The five root scripts (`extract.py`, `parse_items.py`, `parse_translations.py`, `generate_icons.py`, `deduplicate_icons.py`) and their tests MUST remain present and runnable. Only `extract.py` gets a minimal, backward-compatible signature change (Task 3).
- Built-in default paths (verbatim from current scripts):
  - data.cdb: `unpacked/data.cdb`
  - assets root: `unpacked`
  - extract out: `unpacked`
  - items out: `generated/items.json`
  - translations out: `generated/i18n`
  - lang dir: `unpacked/extra/lang`
  - icons out: `generated/icons`
  - icons manifest: `generated/icons_manifest.json`
- `.env` is gitignored (already in `.gitignore`); never commit real values. `.env.example` documents every `SC_` var, all lines commented, defaults shown as illustrative non-secret values.

## File Structure

```
sc.py                          # entry point (Task 9)
requirements.txt               # typer, python-dotenv (Task 1)
.env.example                   # documents all SC_ vars (Task 10)
src/
  __init__.py                  # (Task 1)
  cli.py                       # Typer app + registration + load_env callback (Task 9)
  lib/
    __init__.py                # (Task 1)
    config.py                  # Setting dataclass + all settings + ALL_SETTINGS (Task 2)
    env.py                     # load_env(), resolve() (Task 2)
  commands/
    __init__.py                # (Task 1)
    extract.py                 # (Task 3)
    parse_items.py             # (Task 4)
    parse_translations.py      # (Task 5)
    generate_icons.py          # (Task 6)
    deduplicate_icons.py       # (Task 7)
    pipeline.py                # (Task 8)
test_sc_env.py                 # (Task 2)
test_sc_extract.py             # (Task 3)
test_sc_parse_items.py         # (Task 4)
test_sc_parse_translations.py  # (Task 5)
test_sc_generate_icons.py      # (Task 6)
test_sc_deduplicate_icons.py   # (Task 7)
test_sc_pipeline.py            # (Task 8)
test_sc_cli.py                 # (Task 9)
test_sc_env_example.py         # (Task 10)
```

---

### Task 1: Scaffolding, dependencies, package skeleton

**Files:**
- Create: `requirements.txt`
- Create: `src/__init__.py`, `src/lib/__init__.py`, `src/commands/__init__.py` (all empty)

**Interfaces:**
- Consumes: nothing.
- Produces: importable `src`, `src.lib`, `src.commands` packages; `typer` and `dotenv` installed in `.venv`.

- [ ] **Step 1: Create `requirements.txt`**

```
typer>=0.12
python-dotenv>=1.0
```

- [ ] **Step 2: Create the three empty package init files**

Create `src/__init__.py`, `src/lib/__init__.py`, `src/commands/__init__.py`, each as an empty file (0 bytes).

- [ ] **Step 3: Install dependencies**

Run: `.venv/Scripts/python -m pip install -r requirements.txt`
Expected: ends with `Successfully installed ... typer-... python-dotenv-... click-...`

- [ ] **Step 4: Verify imports**

Run: `.venv/Scripts/python -c "import typer, dotenv, src, src.lib, src.commands; print('ok')"`
Expected: prints `ok`

- [ ] **Step 5: Commit**

```bash
git add requirements.txt src/__init__.py src/lib/__init__.py src/commands/__init__.py
git commit -m "Add CLI package skeleton and dependencies"
```

---

### Task 2: Config settings and env resolution

**Files:**
- Create: `src/lib/config.py`
- Create: `src/lib/env.py`
- Test: `test_sc_env.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `src.lib.config.Setting` — frozen dataclass with `.env: str` and `.default: str`.
  - `src.lib.config.{DATA, ASSETS, EXTRACT_OUT, PARSE_ITEMS_OUT, PARSE_TRANSLATIONS_OUT, PARSE_TRANSLATIONS_LANG_DIR, GENERATE_ICONS_OUT, GENERATE_ICONS_MANIFEST, DEDUPLICATE_ICONS_MANIFEST}` — `Setting` instances.
  - `src.lib.config.ALL_SETTINGS: list[Setting]`.
  - `src.lib.env.load_env(root: pathlib.Path) -> None` — loads `<root>/.env` via dotenv, `override=False`, missing file tolerated.
  - `src.lib.env.resolve(cli_value, setting: Setting) -> str` — returns `str(cli_value)` if `cli_value is not None`, else the env var value if set and non-empty, else `setting.default`.

- [ ] **Step 1: Write the failing test**

Create `test_sc_env.py`:

```python
import os
import unittest
from unittest import mock

from src.lib import config
from src.lib.env import resolve


class ResolveTests(unittest.TestCase):
    def setUp(self):
        self.setting = config.PARSE_ITEMS_OUT  # SC_PARSE_ITEMS_OUT / generated/items.json

    def test_default_used_when_no_cli_and_no_env(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(resolve(None, self.setting), "generated/items.json")

    def test_env_used_when_no_cli(self):
        with mock.patch.dict(os.environ, {self.setting.env: "from_env.json"}, clear=True):
            self.assertEqual(resolve(None, self.setting), "from_env.json")

    def test_cli_overrides_env(self):
        with mock.patch.dict(os.environ, {self.setting.env: "from_env.json"}, clear=True):
            self.assertEqual(resolve("from_cli.json", self.setting), "from_cli.json")

    def test_empty_env_falls_back_to_default(self):
        with mock.patch.dict(os.environ, {self.setting.env: ""}, clear=True):
            self.assertEqual(resolve(None, self.setting), "generated/items.json")

    def test_cli_value_coerced_to_str(self):
        from pathlib import Path
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(resolve(Path("a/b.json"), self.setting), str(Path("a/b.json")))

    def test_all_settings_unique_env_names(self):
        names = [s.env for s in config.ALL_SETTINGS]
        # DATA used by 3 commands but is one Setting; manifest shared by 2 commands
        # but those are two distinct Settings with the same env name by design.
        self.assertTrue(all(n.startswith("SC_") for n in names))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m unittest test_sc_env -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.lib.config'`

- [ ] **Step 3: Create `src/lib/config.py`**

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Setting:
    env: str
    default: str


DATA = Setting("SC_DATA", "unpacked/data.cdb")
ASSETS = Setting("SC_ASSETS", "unpacked")
EXTRACT_OUT = Setting("SC_EXTRACT_OUT", "unpacked")
PARSE_ITEMS_OUT = Setting("SC_PARSE_ITEMS_OUT", "generated/items.json")
PARSE_TRANSLATIONS_OUT = Setting("SC_PARSE_TRANSLATIONS_OUT", "generated/i18n")
PARSE_TRANSLATIONS_LANG_DIR = Setting("SC_PARSE_TRANSLATIONS_LANG_DIR", "unpacked/extra/lang")
GENERATE_ICONS_OUT = Setting("SC_GENERATE_ICONS_OUT", "generated/icons")
GENERATE_ICONS_MANIFEST = Setting("SC_GENERATE_ICONS_MANIFEST", "generated/icons_manifest.json")
DEDUPLICATE_ICONS_MANIFEST = Setting("SC_DEDUPLICATE_ICONS_MANIFEST", "generated/icons_manifest.json")

# Order groups shared settings first, then per-command settings. Used to
# generate and validate .env.example.
ALL_SETTINGS = [
    DATA,
    ASSETS,
    EXTRACT_OUT,
    PARSE_ITEMS_OUT,
    PARSE_TRANSLATIONS_OUT,
    PARSE_TRANSLATIONS_LANG_DIR,
    GENERATE_ICONS_OUT,
    GENERATE_ICONS_MANIFEST,
    DEDUPLICATE_ICONS_MANIFEST,
]
```

- [ ] **Step 4: Create `src/lib/env.py`**

```python
import os
from pathlib import Path

from dotenv import load_dotenv

from src.lib.config import Setting


def load_env(root: Path) -> None:
    """Populate os.environ from <root>/.env. Missing file is fine.

    override=False so a variable already present in the real environment
    wins over the .env file.
    """
    load_dotenv(dotenv_path=root / ".env", override=False)


def resolve(cli_value, setting: Setting) -> str:
    """CLI value > env var > built-in default. Returns a string path/value."""
    if cli_value is not None:
        return str(cli_value)
    env_value = os.environ.get(setting.env)
    if env_value:
        return env_value
    return setting.default
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv/Scripts/python -m unittest test_sc_env -v`
Expected: `OK` (6 tests)

- [ ] **Step 6: Commit**

```bash
git add src/lib/config.py src/lib/env.py test_sc_env.py
git commit -m "Add config settings and env resolution helper"
```

---

### Task 3: extract command

**Files:**
- Modify: `extract.py` (function `main`, lines ~393 and ~402)
- Create: `src/commands/extract.py`
- Test: `test_sc_extract.py`

**Interfaces:**
- Consumes: `src.lib.env.resolve`, `src.lib.config.EXTRACT_OUT`; root module `extract`.
- Produces:
  - `extract.main(argv=None)` — now accepts an explicit argv list.
  - `src.commands.extract.run(pak, out=None, list_files=False, ext=None, contains=None, kind2=None, debug_at=None) -> int` — builds argv and calls `extract.main`; returns `0` on success (extract raises `SystemExit` on parse failure).
  - `src.commands.extract.command(...)` — Typer command function.

- [ ] **Step 1: Write the failing test**

Create `test_sc_extract.py`:

```python
import unittest
from unittest import mock

import extract
from src.commands import extract as cmd


class ExtractMainArgvTests(unittest.TestCase):
    def test_main_accepts_argv_for_help(self):
        # argparse prints help and exits 0 when --help is in the passed argv
        with self.assertRaises(SystemExit) as ctx:
            extract.main(["--help"])
        self.assertEqual(ctx.exception.code, 0)


class ExtractCommandTests(unittest.TestCase):
    def test_run_builds_argv_with_default_out(self):
        with mock.patch("extract.main") as m:
            code = cmd.run("game.pak")
        self.assertEqual(code, 0)
        self.assertEqual(m.call_args.args[0], ["game.pak", "--out", "unpacked"])

    def test_run_passes_list_and_filters(self):
        with mock.patch("extract.main") as m:
            cmd.run("game.pak", list_files=True, ext=["png", "txt"], contains=["icon"])
        argv = m.call_args.args[0]
        self.assertIn("--list", argv)
        self.assertEqual(argv[argv.index("--ext") + 1:argv.index("--ext") + 3], ["png", "txt"])
        self.assertEqual(argv[argv.index("--contains") + 1], "icon")

    def test_cli_out_overrides_env(self):
        with mock.patch.dict("os.environ", {"SC_EXTRACT_OUT": "from_env"}):
            with mock.patch("extract.main") as m:
                cmd.run("game.pak", out="from_cli")
        argv = m.call_args.args[0]
        self.assertIn("from_cli", argv)
        self.assertNotIn("from_env", argv)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m unittest test_sc_extract -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.commands.extract'` (and the argv test would also fail because current `main()` ignores argv).

- [ ] **Step 3: Make `extract.main` accept argv**

In `extract.py`, change the signature and the parse call.

Replace:
```python
def main():
    parser = argparse.ArgumentParser()
```
with:
```python
def main(argv=None):
    parser = argparse.ArgumentParser()
```

Replace:
```python
    args = parser.parse_args()
```
with:
```python
    args = parser.parse_args(argv)
```

(The `if __name__ == "__main__": main()` call at the bottom stays unchanged; `main()` with no argv still reads `sys.argv`.)

- [ ] **Step 4: Create `src/commands/extract.py`**

```python
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
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv/Scripts/python -m unittest test_sc_extract -v`
Expected: `OK` (4 tests)

- [ ] **Step 6: Confirm the original extract test still passes**

Run: `.venv/Scripts/python -m unittest test_extract -v`
Expected: `OK`

- [ ] **Step 7: Commit**

```bash
git add extract.py src/commands/extract.py test_sc_extract.py
git commit -m "Add extract command wrapping extract.py"
```

---

### Task 4: parse-items command

**Files:**
- Create: `src/commands/parse_items.py`
- Test: `test_sc_parse_items.py`

**Interfaces:**
- Consumes: `resolve`, `config.DATA`, `config.PARSE_ITEMS_OUT`; root module `parse_items` (which exposes `main(argv=None)`).
- Produces:
  - `src.commands.parse_items.run(data=None, out=None, dry_run=False) -> int`.
  - `src.commands.parse_items.command(...)` — Typer command function.

- [ ] **Step 1: Write the failing test**

Create `test_sc_parse_items.py`:

```python
import os
import unittest
from unittest import mock

from src.commands import parse_items as cmd


class ParseItemsCommandTests(unittest.TestCase):
    def test_run_defaults(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch("parse_items.main", return_value=0) as m:
                code = cmd.run()
        self.assertEqual(code, 0)
        self.assertEqual(
            m.call_args.args[0],
            ["--data", "unpacked/data.cdb", "--out", "generated/items.json"],
        )

    def test_dry_run_flag(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch("parse_items.main", return_value=0) as m:
                cmd.run(dry_run=True)
        self.assertIn("--dry-run", m.call_args.args[0])

    def test_env_then_cli_precedence(self):
        with mock.patch.dict(os.environ, {"SC_DATA": "env.cdb"}, clear=True):
            with mock.patch("parse_items.main", return_value=0) as m:
                cmd.run()  # env applies
            argv = m.call_args.args[0]
            self.assertIn("env.cdb", argv)
            with mock.patch("parse_items.main", return_value=0) as m:
                cmd.run(data="cli.cdb")  # cli overrides env
            self.assertIn("cli.cdb", m.call_args.args[0])
            self.assertNotIn("env.cdb", m.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m unittest test_sc_parse_items -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.commands.parse_items'`

- [ ] **Step 3: Create `src/commands/parse_items.py`**

```python
from typing import Optional

import typer

import parse_items as script
from src.lib import config
from src.lib.env import resolve


def run(data: Optional[str] = None, out: Optional[str] = None, dry_run: bool = False) -> int:
    argv = [
        "--data", resolve(data, config.DATA),
        "--out", resolve(out, config.PARSE_ITEMS_OUT),
    ]
    if dry_run:
        argv.append("--dry-run")
    return script.main(argv)


def command(
    data: Optional[str] = typer.Option(None, "--data", help="Path to data.cdb. Env: SC_DATA."),
    out: Optional[str] = typer.Option(None, "--out", help="Output JSON path. Env: SC_PARSE_ITEMS_OUT."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Report counts without writing."),
) -> None:
    raise typer.Exit(run(data=data, out=out, dry_run=dry_run))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/Scripts/python -m unittest test_sc_parse_items -v`
Expected: `OK` (3 tests)

- [ ] **Step 5: Commit**

```bash
git add src/commands/parse_items.py test_sc_parse_items.py
git commit -m "Add parse-items command"
```

---

### Task 5: parse-translations command

**Files:**
- Create: `src/commands/parse_translations.py`
- Test: `test_sc_parse_translations.py`

**Interfaces:**
- Consumes: `resolve`, `config.DATA`, `config.PARSE_TRANSLATIONS_LANG_DIR`, `config.PARSE_TRANSLATIONS_OUT`; root module `parse_translations` (`main(argv=None)`).
- Produces:
  - `src.commands.parse_translations.run(data=None, lang_dir=None, out=None, dry_run=False) -> int`.
  - `src.commands.parse_translations.command(...)`.

- [ ] **Step 1: Write the failing test**

Create `test_sc_parse_translations.py`:

```python
import os
import unittest
from unittest import mock

from src.commands import parse_translations as cmd


class ParseTranslationsCommandTests(unittest.TestCase):
    def test_run_defaults(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch("parse_translations.main", return_value=0) as m:
                code = cmd.run()
        self.assertEqual(code, 0)
        self.assertEqual(
            m.call_args.args[0],
            [
                "--data", "unpacked/data.cdb",
                "--lang-dir", "unpacked/extra/lang",
                "--out", "generated/i18n",
            ],
        )

    def test_lang_dir_env(self):
        with mock.patch.dict(os.environ, {"SC_PARSE_TRANSLATIONS_LANG_DIR": "langs"}, clear=True):
            with mock.patch("parse_translations.main", return_value=0) as m:
                cmd.run()
        self.assertIn("langs", m.call_args.args[0])

    def test_dry_run(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch("parse_translations.main", return_value=0) as m:
                cmd.run(dry_run=True)
        self.assertIn("--dry-run", m.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m unittest test_sc_parse_translations -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.commands.parse_translations'`

- [ ] **Step 3: Create `src/commands/parse_translations.py`**

```python
from typing import Optional

import typer

import parse_translations as script
from src.lib import config
from src.lib.env import resolve


def run(
    data: Optional[str] = None,
    lang_dir: Optional[str] = None,
    out: Optional[str] = None,
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
    data: Optional[str] = typer.Option(None, "--data", help="Path to data.cdb. Env: SC_DATA."),
    lang_dir: Optional[str] = typer.Option(None, "--lang-dir", help="export_<lang>.xml folder. Env: SC_PARSE_TRANSLATIONS_LANG_DIR."),
    out: Optional[str] = typer.Option(None, "--out", help="Output dir. Env: SC_PARSE_TRANSLATIONS_OUT."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Report counts without writing."),
) -> None:
    raise typer.Exit(run(data=data, lang_dir=lang_dir, out=out, dry_run=dry_run))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/Scripts/python -m unittest test_sc_parse_translations -v`
Expected: `OK` (3 tests)

- [ ] **Step 5: Commit**

```bash
git add src/commands/parse_translations.py test_sc_parse_translations.py
git commit -m "Add parse-translations command"
```

---

### Task 6: generate-icons command

**Files:**
- Create: `src/commands/generate_icons.py`
- Test: `test_sc_generate_icons.py`

**Interfaces:**
- Consumes: `resolve`, `config.DATA`, `config.ASSETS`, `config.GENERATE_ICONS_OUT`, `config.GENERATE_ICONS_MANIFEST`; root module `generate_icons` (`main(argv=None)`).
- Produces:
  - `src.commands.generate_icons.run(data=None, assets=None, out=None, manifest=None, icon_file=None, all_icon_files=False, no_recolor=False, clean=False, dry_run=False) -> int`.
  - `src.commands.generate_icons.command(...)`.

- [ ] **Step 1: Write the failing test**

Create `test_sc_generate_icons.py`:

```python
import os
import unittest
from unittest import mock

from src.commands import generate_icons as cmd


class GenerateIconsCommandTests(unittest.TestCase):
    def test_run_defaults(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch("generate_icons.main", return_value=0) as m:
                code = cmd.run()
        self.assertEqual(code, 0)
        self.assertEqual(
            m.call_args.args[0],
            [
                "--data", "unpacked/data.cdb",
                "--assets", "unpacked",
                "--out", "generated/icons",
                "--manifest", "generated/icons_manifest.json",
            ],
        )

    def test_flags_and_icon_files(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch("generate_icons.main", return_value=0) as m:
                cmd.run(
                    icon_file=["ui/a.png", "ui/b.png"],
                    all_icon_files=True,
                    no_recolor=True,
                    clean=True,
                    dry_run=True,
                )
        argv = m.call_args.args[0]
        self.assertEqual(argv.count("--icon-file"), 2)
        for flag in ("--all-icon-files", "--no-recolor", "--clean", "--dry-run"):
            self.assertIn(flag, argv)

    def test_manifest_env(self):
        with mock.patch.dict(os.environ, {"SC_GENERATE_ICONS_MANIFEST": "m.json"}, clear=True):
            with mock.patch("generate_icons.main", return_value=0) as m:
                cmd.run()
        self.assertIn("m.json", m.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m unittest test_sc_generate_icons -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.commands.generate_icons'`

- [ ] **Step 3: Create `src/commands/generate_icons.py`**

```python
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
    icon_file: Optional[List[str]] = None,
    all_icon_files: bool = False,
    no_recolor: bool = False,
    clean: bool = False,
    dry_run: bool = False,
) -> int:
    argv = [
        "--data", resolve(data, config.DATA),
        "--assets", resolve(assets, config.ASSETS),
        "--out", resolve(out, config.GENERATE_ICONS_OUT),
        "--manifest", resolve(manifest, config.GENERATE_ICONS_MANIFEST),
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
    return script.main(argv)


def command(
    data: Optional[str] = typer.Option(None, "--data", help="Path to data.cdb. Env: SC_DATA."),
    assets: Optional[str] = typer.Option(None, "--assets", help="Unpacked assets root. Env: SC_ASSETS."),
    out: Optional[str] = typer.Option(None, "--out", help="Icon output dir. Env: SC_GENERATE_ICONS_OUT."),
    manifest: Optional[str] = typer.Option(None, "--manifest", help="Manifest path. Env: SC_GENERATE_ICONS_MANIFEST."),
    icon_file: Optional[List[str]] = typer.Option(None, "--icon-file", help="Restrict to this CDB icon file (repeatable)."),
    all_icon_files: bool = typer.Option(False, "--all-icon-files", help="Generate every CDB icon entry."),
    no_recolor: bool = typer.Option(False, "--no-recolor", help="Skip CDB color gradients."),
    clean: bool = typer.Option(False, "--clean", help="Delete stale PNGs in the output dir."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Report without writing files."),
) -> None:
    raise typer.Exit(
        run(
            data=data,
            assets=assets,
            out=out,
            manifest=manifest,
            icon_file=icon_file,
            all_icon_files=all_icon_files,
            no_recolor=no_recolor,
            clean=clean,
            dry_run=dry_run,
        )
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/Scripts/python -m unittest test_sc_generate_icons -v`
Expected: `OK` (3 tests)

- [ ] **Step 5: Commit**

```bash
git add src/commands/generate_icons.py test_sc_generate_icons.py
git commit -m "Add generate-icons command"
```

---

### Task 7: deduplicate-icons command

**Files:**
- Create: `src/commands/deduplicate_icons.py`
- Test: `test_sc_deduplicate_icons.py`

**Interfaces:**
- Consumes: `resolve`, `config.DEDUPLICATE_ICONS_MANIFEST`; root module `deduplicate_icons` (`main(argv=None)`).
- Produces:
  - `src.commands.deduplicate_icons.run(manifest=None, write=None, aliases_out=None, icons_dir=None, top=10) -> int`.
  - `src.commands.deduplicate_icons.command(...)`.

- [ ] **Step 1: Write the failing test**

Create `test_sc_deduplicate_icons.py`:

```python
import os
import unittest
from unittest import mock

from src.commands import deduplicate_icons as cmd


class DeduplicateIconsCommandTests(unittest.TestCase):
    def test_run_defaults(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch("deduplicate_icons.main", return_value=0) as m:
                code = cmd.run()
        self.assertEqual(code, 0)
        self.assertEqual(
            m.call_args.args[0],
            ["--manifest", "generated/icons_manifest.json", "--top", "10"],
        )

    def test_write_and_aliases(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch("deduplicate_icons.main", return_value=0) as m:
                cmd.run(write="out/dir", aliases_out="aliases.json", icons_dir="icons", top=5)
        argv = m.call_args.args[0]
        self.assertEqual(argv[argv.index("--write") + 1], "out/dir")
        self.assertEqual(argv[argv.index("--aliases-out") + 1], "aliases.json")
        self.assertEqual(argv[argv.index("--icons-dir") + 1], "icons")
        self.assertEqual(argv[argv.index("--top") + 1], "5")

    def test_manifest_env(self):
        with mock.patch.dict(os.environ, {"SC_DEDUPLICATE_ICONS_MANIFEST": "m.json"}, clear=True):
            with mock.patch("deduplicate_icons.main", return_value=0) as m:
                cmd.run()
        self.assertIn("m.json", m.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m unittest test_sc_deduplicate_icons -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.commands.deduplicate_icons'`

- [ ] **Step 3: Create `src/commands/deduplicate_icons.py`**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/Scripts/python -m unittest test_sc_deduplicate_icons -v`
Expected: `OK` (3 tests)

- [ ] **Step 5: Commit**

```bash
git add src/commands/deduplicate_icons.py test_sc_deduplicate_icons.py
git commit -m "Add deduplicate-icons command"
```

---

### Task 8: pipeline command

**Files:**
- Create: `src/commands/pipeline.py`
- Test: `test_sc_pipeline.py`

**Interfaces:**
- Consumes: `src.commands.parse_items.run`, `src.commands.parse_translations.run`, `src.commands.generate_icons.run`, `src.commands.deduplicate_icons.run`.
- Produces:
  - `src.commands.pipeline.STEPS` — list of `(name, callable)` where each callable takes `dry_run: bool` and returns `int`.
  - `src.commands.pipeline.run(dry_run=False) -> int` — runs steps in order, aborts on first non-zero, returns that code (or 0).
  - `src.commands.pipeline.command(dry_run=False)`.

- [ ] **Step 1: Write the failing test**

Create `test_sc_pipeline.py`:

```python
import unittest
from unittest import mock

from src.commands import pipeline as cmd


class PipelineTests(unittest.TestCase):
    def test_runs_all_steps_in_order(self):
        calls = []
        patches = {
            "src.commands.parse_items.run": "parse-items",
            "src.commands.parse_translations.run": "parse-translations",
            "src.commands.generate_icons.run": "generate-icons",
            "src.commands.deduplicate_icons.run": "deduplicate-icons",
        }
        with mock.patch("src.commands.parse_items.run", side_effect=lambda **k: calls.append("parse-items") or 0), \
             mock.patch("src.commands.parse_translations.run", side_effect=lambda **k: calls.append("parse-translations") or 0), \
             mock.patch("src.commands.generate_icons.run", side_effect=lambda **k: calls.append("generate-icons") or 0), \
             mock.patch("src.commands.deduplicate_icons.run", side_effect=lambda **k: calls.append("deduplicate-icons") or 0):
            code = cmd.run()
        self.assertEqual(code, 0)
        self.assertEqual(
            calls,
            ["parse-items", "parse-translations", "generate-icons", "deduplicate-icons"],
        )

    def test_aborts_on_first_failure(self):
        with mock.patch("src.commands.parse_items.run", return_value=0), \
             mock.patch("src.commands.parse_translations.run", return_value=3), \
             mock.patch("src.commands.generate_icons.run", return_value=0) as gen, \
             mock.patch("src.commands.deduplicate_icons.run", return_value=0):
            code = cmd.run()
        self.assertEqual(code, 3)
        gen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m unittest test_sc_pipeline -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.commands.pipeline'`

- [ ] **Step 3: Create `src/commands/pipeline.py`**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/Scripts/python -m unittest test_sc_pipeline -v`
Expected: `OK` (2 tests)

- [ ] **Step 5: Commit**

```bash
git add src/commands/pipeline.py test_sc_pipeline.py
git commit -m "Add pipeline command"
```

---

### Task 9: CLI app wiring and entry point

**Files:**
- Create: `src/cli.py`
- Create: `sc.py`
- Test: `test_sc_cli.py`

**Interfaces:**
- Consumes: all six command modules' `command` functions; `src.lib.env.load_env`.
- Produces:
  - `src.cli.app` — configured `typer.Typer` with commands `extract`, `parse-items`, `parse-translations`, `generate-icons`, `deduplicate-icons`, `pipeline`, and a callback that calls `load_env`.
  - `sc.py` — runnable entry (`python sc.py`).

- [ ] **Step 1: Write the failing test**

Create `test_sc_cli.py`:

```python
import unittest

from typer.testing import CliRunner

from src.cli import app

runner = CliRunner()

EXPECTED_COMMANDS = [
    "extract",
    "parse-items",
    "parse-translations",
    "generate-icons",
    "deduplicate-icons",
    "pipeline",
]


class CliTests(unittest.TestCase):
    def test_help_lists_all_commands(self):
        result = runner.invoke(app, ["--help"])
        self.assertEqual(result.exit_code, 0)
        for name in EXPECTED_COMMANDS:
            self.assertIn(name, result.output)

    def test_no_args_shows_usage(self):
        result = runner.invoke(app, [])
        self.assertIn("Usage", result.output)

    def test_command_help_works(self):
        result = runner.invoke(app, ["parse-items", "--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("--data", result.output)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m unittest test_sc_cli -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.cli'`

- [ ] **Step 3: Create `src/cli.py`**

```python
from pathlib import Path

import typer

from src.commands import (
    deduplicate_icons,
    extract,
    generate_icons,
    parse_items,
    parse_translations,
    pipeline,
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
```

- [ ] **Step 4: Create `sc.py`**

```python
#!/usr/bin/env python3
from src.cli import app

if __name__ == "__main__":
    app()
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv/Scripts/python -m unittest test_sc_cli -v`
Expected: `OK` (3 tests)

- [ ] **Step 6: Verify the bare entry point prints commands**

Run: `.venv/Scripts/python sc.py`
Expected: usage/help text listing `extract`, `parse-items`, `parse-translations`, `generate-icons`, `deduplicate-icons`, `pipeline`.

- [ ] **Step 7: Commit**

```bash
git add src/cli.py sc.py test_sc_cli.py
git commit -m "Wire Typer app and sc.py entry point"
```

---

### Task 10: .env.example and full-suite verification

**Files:**
- Modify: `.env.example` (currently empty)
- Test: `test_sc_env_example.py`

**Interfaces:**
- Consumes: `src.lib.config.ALL_SETTINGS`.
- Produces: committed `.env.example` documenting every `SC_` var; a test asserting coverage.

- [ ] **Step 1: Write the failing test**

Create `test_sc_env_example.py`:

```python
import unittest
from pathlib import Path

from src.lib import config

ENV_EXAMPLE = Path(__file__).resolve().parent / ".env.example"


class EnvExampleTests(unittest.TestCase):
    def test_documents_every_setting(self):
        text = ENV_EXAMPLE.read_text(encoding="utf-8")
        for setting in config.ALL_SETTINGS:
            self.assertIn(setting.env, text, f"{setting.env} missing from .env.example")

    def test_contains_no_uncommented_assignments(self):
        # Every SC_ line must be commented so the file carries no real values.
        for line in ENV_EXAMPLE.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("SC_"):
                self.fail(f"Uncommented assignment in .env.example: {line!r}")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m unittest test_sc_env_example -v`
Expected: FAIL (`.env.example` is empty → `test_documents_every_setting` fails on the first setting).

- [ ] **Step 3: Write `.env.example`**

```
# SpaceCraft resources tool (sc) configuration.
# Copy to .env (gitignored) and uncomment/edit the lines you need.
# Precedence: CLI flag > env var > built-in default (shown below).

# --- Shared ---
# SC_DATA=unpacked/data.cdb
# SC_ASSETS=unpacked

# --- extract ---
# SC_EXTRACT_OUT=unpacked

# --- parse-items ---
# SC_PARSE_ITEMS_OUT=generated/items.json

# --- parse-translations ---
# SC_PARSE_TRANSLATIONS_OUT=generated/i18n
# SC_PARSE_TRANSLATIONS_LANG_DIR=unpacked/extra/lang

# --- generate-icons ---
# SC_GENERATE_ICONS_OUT=generated/icons
# SC_GENERATE_ICONS_MANIFEST=generated/icons_manifest.json

# --- deduplicate-icons ---
# SC_DEDUPLICATE_ICONS_MANIFEST=generated/icons_manifest.json
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/Scripts/python -m unittest test_sc_env_example -v`
Expected: `OK` (2 tests)

- [ ] **Step 5: Run the full test suite (new + existing)**

Run: `.venv/Scripts/python -m unittest discover -p "test_*.py" -v`
Expected: `OK` — all new `test_sc_*` tests plus the existing `test_extract`, `test_generate_icons`, `test_deduplicate_icons`, `test_generated` tests pass.

- [ ] **Step 6: Commit**

```bash
git add .env.example test_sc_env_example.py
git commit -m "Document env vars in .env.example and verify full suite"
```

---

## Manual verification checklist (the gate for deleting root scripts)

Per the design's deferred-cleanup requirement, the root `.py` scripts stay until **all** commands are manually confirmed against real data. After Task 10, run each and confirm output matches the standalone script:

- [ ] `python sc.py` — prints all six commands.
- [ ] `python sc.py extract <some>.pak --list` — lists archive contents.
- [ ] `python sc.py parse-items --dry-run` — same counts as `python parse_items.py --dry-run`.
- [ ] `python sc.py parse-translations --dry-run` — same per-language counts as `python parse_translations.py --dry-run`.
- [ ] `python sc.py generate-icons --dry-run` — same icon count as `python generate_icons.py --dry-run`.
- [ ] `python sc.py deduplicate-icons` — same report as `python deduplicate_icons.py`.
- [ ] `python sc.py pipeline --dry-run` — runs the four regen steps in order.
- [ ] Env override spot-check: set `SC_PARSE_ITEMS_OUT` in `.env`, run `python sc.py parse-items --dry-run` and confirm the resolved output path; then pass `--out` and confirm the flag wins.

Only after this checklist passes should a follow-up change migrate domain logic into `src/lib/` and remove the root scripts (out of scope for this plan).

## Self-Review Notes

- **Spec coverage:** single tool with subcommands (Tasks 3–9), `.env` read + gitignored (Task 2 `load_env`; gitignore already covers `.env`), `.env.example` documents all vars with no real values (Task 10), shared vs command-prefixed env vars (Task 2 config), args override env override default (Task 2 `resolve` + every command test), all five scripts aggregated (Tasks 3–7), `pipeline` improvement (Task 8), no-command prints help (Task 9 `no_args_is_help`), root scripts kept until manual test (Global Constraints + manual checklist).
- **Type consistency:** every command module exposes `run(...) -> int` and `command(...) -> None`; `resolve(cli_value, setting) -> str`; root scripts called via `script.main(argv) -> int` (extract returns None → command `run` returns 0). `extract`'s flag option is named `list_files` in Python (maps to `--list`) to avoid shadowing the builtin `list`.
- **No placeholders:** all steps contain complete code and exact commands.
