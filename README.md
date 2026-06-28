# spacecraft-resources

`sc` is a Python CLI that turns the SpaceCraft game's packed assets into lean,
downstream-friendly **release resources** under [`generated/`](generated/) —
item/recipe JSON, per-language translations, and recolored icons. Those outputs
are consumed by other apps (a Discord bot, the in-repo HTML inspectors). Raw
game source is never committed; only the `generated/` output is tracked.

## Live inspector

A single-page Vue inspector for the generated items and recipes is published via
GitHub Pages:

**➡️ https://kweezl.github.io/spacecraft-resources/**

## Usage

Install deps and run the pipeline:

```bash
python -m pip install -r requirements.txt
python sc.py pipeline   # parse items/recipes/translations + generate icons
python sc.py serve      # run the inspector locally
```

Full command list, configuration, architecture, and contribution conventions
(tests, lint, hard rules) live in **[CLAUDE.md](CLAUDE.md)**.

## Resources

- [`generated/`](generated/) — the tracked release output (consume these files).
- [`generated/wiring.md`](generated/wiring.md) — guide to the generated resources.
- [`.env.example`](.env.example) — documents every configurable `SC_*` setting.

## License & attribution

The `sc` tooling is released under the [MIT License](LICENSE). The generated
resources are derived from the SpaceCraft game and remain the property of its
creators — see [NOTICE](NOTICE).
