# Wiring the generated resources

This folder ships the parsed SpaceCraft **release resources**. Everything is
keyed so the files join into one consistent database. The primary key is the
item **`id`**; secondary keys are the attribute **`code`**, the itemType /
category **`id`**, and tag / skill codes. Translatable strings live *only* in the
per-language `i18n/translation.<lang>.json` files — the data files carry raw
codes, never display text.

## Files

| File | Keyed by | What it gives you |
|------|----------|-------------------|
| `items.json` | item `id` | `items[<id>]`: item data + raw CDB codes (`type`, `tags`, `skills`, `compatibleSkills`, `attributes`) and an `icon` crop block. |
| `craft.json` | recipe `id` | `recipes[<id>]`: `inputs`/`outputs` (each references an item `id` + `qty`), `where` (workshop), `category` (itemType id), and recipe `props`. |
| `i18n/translation.<lang>.json` | id / code | `item` (by item id), `attribute` (by attr code), `itemType` (by category id) → `{ "name": ..., "desc"?: ... }`. |
| `aliases.json` | item `id` | `icons[<id>]` → canonical icon **filename** (the dedup-safe lookup). |
| `icons_manifest.json` | item `id` | `icons[<id>]`: produced icon (`output`) + provenance (`source` crop, `color`). |
| `icons/<name>.webp` | filename | Pre-cropped, recoloured 64px icons (lossless WebP). |

## How everything joins

```
            i18n/translation.<lang>.json
            item[id] / attribute[code] / itemType[id]
                          |  (names & descriptions)
                          v
items.json  --- id --->  (an item)  <--- item id ---  craft.json
   |  icon block            ^                         inputs[].item
   |                        | item id                 outputs[].item
   v                        |                         where / category(itemType id)
aliases.json.icons[id] --> canonical filename --> icons/<name>.webp
   (icons_manifest.json[id].output gives the same file with provenance)
```

- **Items ⇄ recipes:** `craft.json` `inputs[].item` / `outputs[].item` are item
  `id`s — look them up in `items.json` `items[<id>]`.
- **Items ⇄ translations:** `translation.<lang>.json` `item[<id>].name` /
  `.desc` localize an item; `attribute[<code>].name` localizes an item's
  `attributes[].attr` code; `itemType[<id>].name` localizes a recipe `category`
  (and item `type`).
- **Items ⇄ icons:** resolve `aliases.json` `icons[<id>]` to a filename, then
  open `icons/<filename>`. Never assume `icons/<id>.webp` exists (see caveats).

## Resolving an item's icon

Use the `id` to look up the **canonical filename**, then open that file. Always
go through `aliases.json` (or the manifest `output`) — never build the path from
the id directly.

```python
import json

items   = json.load(open("items.json", encoding="utf-8"))["items"]
aliases = json.load(open("aliases.json", encoding="utf-8"))["icons"]

item_id  = "IronOre"
filename = aliases.get(item_id)        # -> "IronOre.webp" (or a shared canonical)
icon_path = f"icons/{filename}" if filename else None
```

## Localizing an item or recipe

```python
import json

items = json.load(open("items.json", encoding="utf-8"))["items"]
craft = json.load(open("craft.json", encoding="utf-8"))["recipes"]
tr    = json.load(open("i18n/translation.en.json", encoding="utf-8"))

item = items["IronOre"]
name = tr["item"].get("IronOre", {}).get("name", "IronOre")        # "Iron Ore"

recipe = craft["IronIngot"]
out_id = recipe["outputs"][0]["item"]                              # "IronIngot"
out_name = tr["item"].get(out_id, {}).get("name", out_id)
category = tr["itemType"].get(recipe["category"], {}).get("name", recipe["category"])
for a in item["attributes"]:
    attr_label = tr["attribute"].get(a["attr"], {}).get("name", a["attr"])
```

## Caveats

1. **Do not assume `icons/<id>.webp` exists.** Visually identical icons are
   deduplicated: only the *canonical* files are on disk (see `aliases.json`
   `unique` vs `total`). Many ids resolve to a **shared** file (e.g.
   `Access_Corpo2` → `Access_Corpo1.webp`). Resolve through `aliases.json` /
   the manifest, then open it.

2. **A few items have no icon at all.** Pseudo/virtual entries (e.g.
   `ScriptItem`, `*_Virtual` hulls, loot tokens, spawn markers) carry no `icon`
   block and therefore no file. A lookup returns nothing for those — handle it.

3. **Names/descriptions are not in the data files.** They live only in
   `i18n/translation.<lang>.json`. Join by item `id` (`item`), attribute `code`
   (`attribute`), or itemType `id` (`itemType`). `en` is the base language;
   the available languages are `en, de, es, fr, pl, pt-BR, ru, zh`.

4. **You can crop from the source yourself.** `items.json[<id>].icon` includes
   the crop coordinates (`file`, `size`, `x`, `y`, `width`, `height`); the
   manifest adds any `color` gradient, so a consumer can reproduce an icon from
   the original sprite sheet instead of using the pre-rendered WebP.

## Field reference

`items.json` → `items[<id>].icon`:

| Field | Meaning |
|-------|---------|
| `file` | Source sprite sheet path (under the unpacked assets). |
| `size` | Tile size in pixels (e.g. `64`). |
| `x`, `y` | Tile column/row in the sheet. The pixel crop is `x*size, y*size`. |
| `width`, `height` | Tile span (usually `1`×`1`). |

`craft.json` → `recipes[<id>]`:

| Field | Meaning |
|-------|---------|
| `id` | Recipe id (same as the key; usually the primary output's item id). |
| `inputs` | List of `{ "item": <item id>, "qty": <int> }` ingredients. |
| `outputs` | List of `{ "item": <item id>, "qty": <int> }` products. |
| `where` | Workshop/station that crafts it. |
| `category` | itemType id (localize via `translation.<lang>.json` `itemType`). |
| `unlockType` | Unlock gating code (raw). |
| `props` | Optional extra recipe properties (e.g. `craftTimeFactor`, `manualTimeFactor`, `autoTime`). |

`icons_manifest.json` → `icons[<id>]`:

| Field | Meaning |
|-------|---------|
| `id` | Item id (same as the key). |
| `name` | Display name if present, else `null`. |
| `sheet` | CDB sheet the row came from. |
| `output` | Path to the canonical icon file (after dedup). |
| `source` | The crop used (`file`, `size`, `x`, `y`, `width`, `height`). |
| `color` | Optional gradient (`colors`, `positions`) applied when recolouring. |

`aliases.json`:

| Field | Meaning |
|-------|---------|
| `total` | Number of item ids covered. |
| `unique` | Number of distinct icon files on disk. |
| `icons` | Map of every item `id` → its canonical icon filename. |

---

Regenerate this folder after a game update with `python sc.py pipeline` (or the
individual `parse-items` / `parse-craft` / `parse-translations` / `generate-icons`
commands).

To browse these resources visually (icons + properties, search, filters), run
`python sc.py serve` from the repo root and open
`http://localhost:8000/`. The same generated data powers the
published GitHub Pages inspector.
