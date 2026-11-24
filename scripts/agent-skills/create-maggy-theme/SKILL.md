---
name: create-maggy-theme
description: Create a custom Maggy theme (JSON file) that recolors the agy statusline mascot, swaps sparkles, adds a side prop and picks the dates it shows. Use when a user wants their own Maggy look, e.g. for a holiday or team colors.
---

# Create a Maggy theme

A theme is a JSON file in `~/.config/maggy/themes/`. The file name is the theme name (`paddy.json` → `maggy theme paddy`). Names use letters, digits, `-` and `_` and can't reuse a built-in name (`default`, `xmas`, `halloween`, `cny`).

The JSON Schema with every key: https://agy-pet.github.io/theme.schema.json. Put it in `$schema` so editors validate the file.

## Example

```json
{
  "$schema": "https://agy-pet.github.io/theme.schema.json",
  "description": "St Patrick's Day",
  "colors": { "crown": "#1f9d55", "feet": [20, 120, 60] },
  "sparkles": { "✦": "☘", "·": "·" },
  "sparkle_color": "#a3e635",
  "eye_color": "#ffffff",
  "prop": ["c c", "ccc", " s "],
  "prop_cells": {
    "c": { "bg": "#1f9d55" },
    "s": { "fg": "#3f6212", "glyphs": ["│"] }
  },
  "dates": ["03-17"]
}
```

## Keys (all optional)

The logo is a grid of cells `a`–`p`:

```text
    aabb        crown: a b
  ccddeeff      arch:  c d e f
  gghhiijj      body:  g h i j
  kk    ll      legs:  k l
mmnn    oopp    feet:  m n o p
```

- `colors`: by region (`crown`, `arch`, `body`, `legs`, `feet`) or by cell (`a`–`p`). Values are `"#rrggbb"` or `[r, g, b]`.
- `sparkles`: replace `✦` and `·` with other single-width characters.
- `prop`: up to 5 rows of up to 8 characters drawn beside the logo. Every non-space character needs a `prop_cells` entry with at least `bg` or `glyphs`; optional `fg`, `chase` (list of colors cycled along the prop), `blink` (`"all"` or `"alt"`).
- `base`: start from `xmas`, `halloween` or `cny` and override only what you set. `"prop": null` drops the built-in prop.
- `dates`: `"MM-DD"` or `"YYYY-MM-DD"` days when `auto` shows this theme; it wins over built-ins on those days.

## Check and enable

```bash
maggy theme list                              # lists themes; names skipped files and why
maggy preview working --theme paddy --once    # print one frame
maggy theme paddy                             # use it now (or leave on auto for its dates)
```
