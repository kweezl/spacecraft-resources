# Linking icons to items

This folder ships the parsed SpaceCraft resources. Items and icons are linked by
the **item `id`**, which is the shared key across every file here.

## Files

| File | Keyed by | What it gives you |
|------|----------|-------------------|
| `items.json` | item `id` | Item data + an `icon` block with the raw crop into the source sprite sheet. |
| `icons_manifest.json` | item `id` | The produced icon file (`output`) + provenance (`source` crop, `color`). |
| `aliases.json` | item `id` | `id` → canonical icon **filename** (the dedup-safe lookup). |
| `icons/<name>.png` | filename | The pre-cropped, recoloured 64px PNG icons. |

```
items.json                 icons_manifest.json              aliases.json
  "IronOre": {               "IronOre": {                     "icons": {
    "id": "IronOre",           "id": "IronOre",                 "IronOre": "IronDeposit.png",
    "icon": {                  "output": ".../IronDeposit.png", "Access_Corpo2": "Access_Corpo1.png",
      "file","x","y",... }     "source": { "file","x",... }     ...
  }                          }                                }
        |                            |                               |
        +--------------- shared key: the item id ---------------------+
```

Note how `IronOre` resolves to `IronDeposit.png` — its icon is visually
identical to `IronDeposit`'s, so after deduplication they share one file. This
is exactly why you must resolve the filename through the map instead of assuming
`IronOre.png`.

## How to resolve an item's icon

Use the `id` to look up the **canonical filename**, then open that file. Always
go through `aliases.json` (or the manifest `output`) — never build the path from
the id directly (see caveats).

```python
import json

items    = json.load(open("items.json", encoding="utf-8"))["items"]
aliases  = json.load(open("aliases.json", encoding="utf-8"))["icons"]

item_id  = "IronOre"
filename = aliases.get(item_id)              # -> "IronDeposit.png" (shared canonical)
if filename:
    icon_path = f"icons/{filename}"          # the file that exists on disk
else:
    icon_path = None                         # item has no generated icon
```

Equivalent lookup via the manifest:

```python
manifest = json.load(open("icons_manifest.json", encoding="utf-8"))["icons"]
entry    = manifest.get("IronOre")
icon_path = entry["output"] if entry else None   # e.g. "generated/icons/IronDeposit.png"
```

## Caveats

1. **Do not assume `icons/<id>.png` exists.** Visually identical icons are
   deduplicated: only the ~298 *canonical* PNGs are on disk. Many ids resolve to
   a **shared** file (e.g. `Access_Corpo2` → `Access_Corpo1.png`). Resolve the
   filename through `aliases.json` / the manifest, then open it.

2. **Not every item has a generated icon.** The shipped icons cover the
   `sprite_sheet_icon_64` sheet variants. An item can carry an `icon` block in
   `items.json` yet have no PNG here. `items.json` (the `item` sheet) and the
   icon set are not 1:1, so a lookup may return nothing — handle that case.

3. **You can crop from the source yourself.** `items.json` includes the crop
   coordinates (`file`, `size`, `x`, `y`, `width`, `height`) and any `color`
   gradient, so a consumer can reproduce an icon straight from the original
   sprite sheet instead of using the pre-rendered PNGs.

## Field reference

`items.json` → `items[<id>].icon`:

| Field | Meaning |
|-------|---------|
| `file` | Source sprite sheet path (under the unpacked assets). |
| `size` | Tile size in pixels (e.g. `64`). |
| `x`, `y` | Tile column/row in the sheet. The pixel crop is `x*size, y*size`. |
| `width`, `height` | Tile span (usually `1`×`1`). |

`icons_manifest.json` → `icons[<id>]`:

| Field | Meaning |
|-------|---------|
| `id` | Item id (same as the key). |
| `name` | Display name if present, else `null`. |
| `sheet` | CDB sheet the row came from. |
| `output` | Path to the icon PNG (canonical file after dedup). |
| `source` | The crop used (`file`, `size`, `x`, `y`, `width`, `height`). |
| `color` | Optional gradient (`colors`, `positions`) applied when recolouring. |

`aliases.json`:

| Field | Meaning |
|-------|---------|
| `total` | Number of item ids covered. |
| `unique` | Number of distinct icon files on disk. |
| `icons` | Map of every item `id` → its canonical icon filename. |

---

Regenerate this folder after a game update with `python sc.py pipeline`
(or the individual `parse-items` / `parse-translations` / `generate-icons`
commands). See the repository README/tooling for details.
