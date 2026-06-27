# SpaceCraft Resources CLI Tool — Design

Date: 2026-06-27
Status: Approved (design); pending spec review

## 1. Goal

Aggregate the project's standalone Python scripts into a single console tool,
`sc`, that accepts subcommands. The tool reads configuration from a gitignored
`.env` file, documents every variable in `.env.example`, and lets CLI arguments
override env values per option. Running the tool with no command prints the
list of available commands.

## 2. Scope

In scope — wrap these existing scripts as commands:

| Command | Backing script | Purpose |
|---|---|---|
| `extract` | `extract.py` | Unpack a `.pak` archive |
| `parse-items` | `parse_items.py` | `data.cdb` → `items.json` |
| `parse-translations` | `parse_translations.py` | `data.cdb` + lang XML → per-language i18n JSON |
| `generate-icons` | `generate_icons.py` | Crop/recolor item icons + write manifest |
| `deduplicate-icons` | `deduplicate_icons.py` | Deduplicate icons by visual content |
| `pipeline` | (new) | Run `parse-items` → `parse-translations` → `generate-icons` → `deduplicate-icons` in order |

Out of scope (for now): `--env-file` flag, a `pip`-installed `sc` console
script entry point, and migrating domain logic out of the root scripts (that
happens only after manual verification — see §8).

## 3. Decisions (confirmed with user)

- **CLI framework:** Typer (built on Click).
- **Layout:** `src/commands/` (one file per command) and `src/lib/` (shared
  helpers). Tool entry point is `sc.py` at the repo root.
- **Dependencies allowed:** `typer` and `python-dotenv`, pinned in
  `requirements.txt`. No packaging / console_scripts entry; run as
  `python sc.py <command>`.
- **Command names:** verbose, mirroring the scripts (`extract`,
  `parse-items`, `parse-translations`, `generate-icons`,
  `deduplicate-icons`).
- **Env prefix:** `SC_`.
- **Improvements included:** `pipeline` command only.

## 4. Architecture

### 4.1 Entry point — `sc.py`

```python
from src.cli import app

if __name__ == "__main__":
    app()
```

### 4.2 `src/cli.py`

- Calls `load_env()` from `src/lib/env.py` to populate `os.environ` from `.env`
  before the Typer app reads any `envvar` defaults.
- Creates `typer.Typer(no_args_is_help=True, add_completion=False)`.
- Registers each command module's command function.
- Registers the `pipeline` command.

### 4.3 `src/lib/env.py`

- `load_env()` — loads `.env` from the repo root using `python-dotenv`
  (`load_dotenv(dotenv_path=<repo-root>/.env, override=False)`). Missing `.env`
  is not an error. `override=False` means a variable already set in the real
  environment wins over the `.env` file.
- Provides the canonical env-variable name constants (or a small helper) so
  command modules and `.env.example` stay in sync.

### 4.4 `src/lib/paths.py`

- Holds the built-in default paths (the current argparse defaults) as
  constants, so commands and the spec share one definition.

### 4.5 `src/commands/<command>.py`

Each module:

1. Defines a Typer command function with typed options.
2. Each path/config option sets `envvar="SC_..."` and the built-in default, so
   Typer resolves **CLI value → env var → default** automatically.
3. Flags (`--list`, `--dry-run`, `--clean`, etc.) and positionals (`extract`'s
   `pak`, `--ext`, `--contains`) stay CLI-only — no env var.
4. Calls the existing root script's functions to do the real work. **No logic is
   copied** during this phase; the root scripts remain the single source of
   truth.

### 4.6 Single-source-of-truth note

`src/commands/parse_items.py` imports and calls `parse_items.parse_items(...)`,
`src/commands/generate_icons.py` calls `generate_icons.generate_icons(...)`,
etc. Because the root scripts already separate their core function from
`argparse`/`main()`, the command layer only builds arguments and delegates.

## 5. Environment variable scheme

Global prefix `SC_`. Shared vars carry no command name; command-specific vars
are prefixed with the command name (uppercased, `-` → `_`).

| Var | Command(s) | Replaces default |
|---|---|---|
| `SC_DATA` | parse-items, parse-translations, generate-icons | `unpacked/data.cdb` |
| `SC_ASSETS` | generate-icons | `unpacked` |
| `SC_EXTRACT_OUT` | extract | `unpacked` |
| `SC_PARSE_ITEMS_OUT` | parse-items | `generated/items.json` |
| `SC_PARSE_TRANSLATIONS_OUT` | parse-translations | `generated/i18n` |
| `SC_PARSE_TRANSLATIONS_LANG_DIR` | parse-translations | `unpacked/extra/lang` |
| `SC_GENERATE_ICONS_OUT` | generate-icons | `generated/icons` |
| `SC_GENERATE_ICONS_MANIFEST` | generate-icons | `generated/icons_manifest.json` |
| `SC_DEDUPLICATE_ICONS_MANIFEST` | deduplicate-icons | `generated/icons_manifest.json` |

Precedence per option: **CLI flag > env var > built-in default**.

Note: `extract` previously defaulted `--out` to `unpacked`; the project also
gitignores `unpacked/`. The env var `SC_EXTRACT_OUT` preserves that default.

## 6. Per-command option mapping

For each command, the Typer options mirror the script's current argparse
options. Path/config options gain an `envvar`; flags do not.

- **extract** — `pak` (positional, CLI-only), `--out` (`SC_EXTRACT_OUT`),
  `--list`, `--ext`, `--contains` (CLI-only). The hidden `--kind2` and
  `--debug-at` diagnostics are preserved as CLI-only options.
- **parse-items** — `--data` (`SC_DATA`), `--out` (`SC_PARSE_ITEMS_OUT`),
  `--dry-run`.
- **parse-translations** — `--data` (`SC_DATA`), `--lang-dir`
  (`SC_PARSE_TRANSLATIONS_LANG_DIR`), `--out`
  (`SC_PARSE_TRANSLATIONS_OUT`), `--dry-run`.
- **generate-icons** — `--data` (`SC_DATA`), `--assets` (`SC_ASSETS`),
  `--out` (`SC_GENERATE_ICONS_OUT`), `--manifest`
  (`SC_GENERATE_ICONS_MANIFEST`), `--icon-file` (repeatable, CLI-only),
  `--all-icon-files`, `--no-recolor`, `--clean`, `--dry-run`.
- **deduplicate-icons** — `--manifest` (`SC_DEDUPLICATE_ICONS_MANIFEST`),
  `--write`, `--aliases-out`, `--icons-dir`, `--top` (CLI-only).
- **pipeline** — accepts `--dry-run`; runs the four regen commands in order
  using their resolved env/defaults. Stops on the first failure.

## 7. Config files

- **`.env`** — already gitignored (`.gitignore` includes `.env`). Holds real
  local values. Created/edited by the user; the tool only reads it.
- **`.env.example`** — committed; lists every `SC_` variable from §5 with a
  short comment and its default as an illustrative (non-secret) value, all
  lines commented out or set to placeholders so it carries no real
  environment-specific values. This is a core requirement.
- **`requirements.txt`** — `typer` and `python-dotenv`, pinned.

## 8. Migration / cleanup (deferred, not in this implementation)

Per the user's requirement "keep python files until tool manually tested for
all commands":

1. This implementation leaves the 5 root scripts and their tests untouched and
   working standalone.
2. After the user manually verifies every command (including `pipeline`), a
   follow-up change moves the domain logic (`Reader`, `RgbaImage`, `IconJob`,
   gradient/PNG/PAK helpers, parse functions) into `src/lib/`, reduces or
   removes the root scripts, and relocates the tests. That cleanup is tracked
   separately and is out of scope here.

## 9. Error handling

- The Typer app surfaces command exceptions as non-zero exits; each command
  preserves the underlying script's existing error messages and exit codes
  (the scripts already print `Error: ...` to stderr and return `1`).
- `pipeline` runs commands sequentially and aborts on the first non-zero
  result, reporting which step failed.
- Missing `.env` is silently tolerated (defaults apply).

## 10. Testing

- Manual: run every command and `pipeline` against the existing
  `unpacked/`/`generated/` data and confirm output matches the standalone
  scripts. This manual pass is the gate for the §8 cleanup.
- Automated (light): a test that the Typer app builds, lists all six commands,
  prints help with no args, and that env→option resolution works for one
  representative option (CLI overrides env overrides default). Existing
  per-script tests continue to run unchanged.

## 11. Success criteria

- `python sc.py` with no args prints all commands.
- `python sc.py <command> --help` shows that command's options.
- Each command produces the same result as its standalone script.
- Setting an `SC_` var changes the corresponding default; passing the CLI flag
  overrides the env var.
- `.env` is gitignored; `.env.example` documents every variable with no real
  values.
- All root `.py` scripts remain present and runnable.
