# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`sc` is a Python CLI that turns the SpaceCraft game's packed assets into lean,
downstream-friendly **release resources** under `generated/` (item/recipe JSON,
per-language translations, recolored icons). Those generated files are consumed
by other apps (a Discord bot, the in-repo HTML inspectors). The pipeline reads
raw game source (`unpacked/`), but raw source is **never committed** — only the
`generated/` output is tracked.

## Commands

Run the tool through the entry point (loads `.env` first via the Typer callback):

```bash
python sc.py                 # no args -> help
python sc.py pipeline        # parse-items, parse-craft, parse-translations, generate-icons
python sc.py <cmd> --dry-run # most parse/generate cmds support dry-run (no writes)
python sc.py serve           # dev static server + opens the inspector at http://localhost:8000/
```

Commands: `extract`, `parse-items`, `parse-craft`, `parse-translations`,
`generate-icons`, `deduplicate-icons`, `pipeline`, `serve`.

Tests (unittest discovery — same as CI; there is no pytest config):

```bash
python -m unittest discover -s tests -t . -p "test_*.py" -v   # full suite
python -m unittest tests.test_generated -v                    # one module
python -m unittest tests.lib.test_parse_craft -v              # one module (nested)
```

`tests/test_integration.py` runs the real parsers/icon generator end-to-end
against an unpacked dataset. `tests/support.py` resolves the root: the real
(gitignored) `unpacked/` when present — so local runs catch real-data
regressions — otherwise the committed mock at `tests/fixtures/unpacked/`, which
is what CI uses. Set `SC_TEST_UNPACKED=<dir>` to force a root. Integration
assertions check structure/invariants, not exact counts, so they hold for both
datasets.

Lint (Ruff — enforced by the `lint` job in CI; config in `ruff.toml`):

```bash
python -m ruff check .        # lint
python -m ruff check . --fix  # autofix the safe ones
```

Setup: `python -m pip install -r requirements.txt` (typer, python-dotenv, Pillow)
for runtime; `python -m pip install -r requirements-dev.txt` adds Ruff for
linting.

## Configuration

Every path/option resolves with precedence **CLI flag > env var > built-in
default**. Settings are declared once in `src/lib/config.py` (each a `Setting`
with an `SC_*` env name + default) and read via `resolve()` in `src/lib/env.py`.
`.env` (gitignored) overrides defaults; `.env.example` documents every key and
is schema-tested against `config.ALL_SETTINGS` (keep them in sync).

## Architecture

**CLI layer** — `src/cli.py` builds the Typer app and registers each command.
`src/commands/*.py` are thin wrappers: they resolve settings, build args, and
delegate. Each exposes a `run(...)` (callable, returns an int exit code, used by
`pipeline` and tests) plus a `command(...)` (Typer-decorated, raises
`typer.Exit`).

**Logic layer** — all implementation lives under `src/lib/`; commands never
contain real logic. Two module styles coexist:
- *Pure logic*, called directly by the command (the cleanest shape):
  `parse-craft` -> `src/lib/craft.py`, `serve` -> `src/lib/serve.py`.
- *Module with its own argparse `main()`*, which the command invokes by building
  an `argv` list: `extract`, `parse_items`, `parse_translations`,
  `generate_icons`, `deduplicate_icons` -> `src/lib/*.py`. New work should prefer
  the pure-logic shape.

**Inspectors** — `src/public/` holds the Vue 3 + Tailwind (CDN, no build step) UI;
`src/lib/serve.py` is a dev-only static server. It serves via a small mount table
(`/generated` -> `generated/`, `/` -> `src/public/`), refusing dotfiles, so the
page can `fetch()` `generated/*.json` over HTTP (browsers block `file://` fetches)
and the local URL layout matches GitHub Pages. The UI is a **single-page app**:
items and recipes are views switched client-side, not separate full-page documents
(see Conventions).

**Data flow** — `data.cdb` is a JSON export of the game's sheets. Parsers find a
named sheet (`item`, `craft`) and emit `{source, sheet, count, skipped, <map>}`
where the map is keyed by id. Output is intentionally lean: it keeps raw CDB
codes (type/tags/skills/attr ids) for downstream resolution, and **excludes
translatable strings** — names/descriptions live only in the per-language
`generated/i18n/translation.<lang>.json` files. `generate-icons` recolors sprite
tiles and deduplicates inline, writing `aliases.json` (item id -> canonical icon).

## Hard rules (enforced by tests/CI)

- **Never commit raw game source.** `tests/test_generated.py` fails if anything
  under `unpacked/` or with a `.cdb/.assets/.bundle/...` extension is tracked.
  `generated/` is the deliberate exception — it is committed.
- Icons (`generated/icons/*.webp`) are stored via **git LFS**.
- `test_generated.py` validates the committed `generated/` output's schema and
  that `aliases.json` is not stale — regenerate via the pipeline if it drifts.

## Conventions

**Python**
- Target 3.12; keep the style Ruff enforces (`E/W/F/I/UP/B`) — code must pass
  `ruff check .` before commit. Use builtin generics and `X | None`, not
  `typing.List`/`Optional` (Typer signatures included).
- Prefer the standard library; the runtime deps are deliberately minimal (typer,
  python-dotenv, Pillow). Don't add a dependency for something stdlib already does.
- Keep pure logic in `src/lib/` separate from CLI/IO in `src/commands/`; type-hint
  public functions; fail with clear `ValueError`/messages and a non-zero exit code.

**TDD for scripts** — write tests first when adding or changing parsing/generation
logic. Add a `tests/lib/test_<name>.py` (pure-logic unit tests) and, for a new
command, a `tests/commands/test_sc_<name>.py` (argv/exit-code wiring). Red → green
→ refactor; the suite must stay green.

**Vue / frontend (`src/public/`)**
- The inspector is a **single-page app**: navigate between items/recipes views via
  client-side state/routing, not `<a href>` to another `.html` (no full reloads).
  Share one app shell, header, and language state across views.
- Vue 3 Composition API, loaded from CDN (no build step); keep components small
  and data-driven from `generated/*.json`. Use `v-cloak`, `:key` on list renders,
  and computed properties over ad-hoc DOM work.
- The SPA core (`app.js`, `components/*.js`, `composables.js`) is entry-agnostic:
  it reads its data base from `data-data-base` on the `#app` element and imports
  siblings relatively. A single `src/public/index.html` (data-base `./generated`)
  serves both local dev and GitHub Pages, since the mount table gives them the
  same URL layout. Pages is deployed by `.github/workflows/pages.yml`, which
  assembles `_site/` from `src/public/` + `generated/` (structure guarded by
  `tests/test_server_spa.py`).

**Docs are local, never committed** — design specs and implementation plans live
under `docs/` (e.g. `docs/superpowers/{specs,plans}/`, dated markdown) and capture
the intended end-state of in-progress work. `docs/` is gitignored on purpose; do
not add it to version control.
