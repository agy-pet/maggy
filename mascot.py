"""Dancing Antigravity logo mascot for the CLI statusline.

The pixel layout and colors are taken verbatim from the startup banner that
`agy` itself prints: a 6x5 grid of 2-column background-colored cells forming
an arch whose gradient runs orange/red (crown) -> green/teal/purple (body)
-> blue (feet). On top of that we add a pair of eyes on the head row, which
change with each pose and agent state. The dance poses only move or bend the
legs and feet, so the logo always stays recognisable.

Every rendered line is exactly sprite_width() columns wide (spaces and
single-width glyphs only) so the adjacent statusline columns never jitter.
"""

import json
import os
import random
import stat
import tempfile
import time
from datetime import date

import config

RESET = "\033[0m"
BLINK = "\033[5m"

# Cell colors as emitted by the agy banner (\033[48;2;R;G;Bm). One letter per
# logo cell; poses below spell each cell twice because a cell is 2 columns.
LOGO_COLORS = {
    # row 1: crown
    "a": (242, 146, 46),
    "b": (240, 114, 54),
    # row 2: upper arch
    "c": (158, 195, 69),
    "d": (226, 153, 61),
    "e": (246, 122, 52),
    "f": (239, 84, 66),
    # row 3: lower arch
    "g": (124, 194, 81),
    "h": (92, 169, 143),
    "i": (116, 111, 195),
    "j": (153, 93, 168),
    # row 4: legs
    "k": (97, 195, 125),
    "l": (74, 128, 234),
    # row 5: feet
    "m": (103, 185, 244),
    "n": (100, 182, 246),
    "o": (56, 131, 249),
    "p": (61, 133, 252),
}

SPARKLE_COLOR = (253, 224, 71)
EYE_COLOR = (255, 255, 255)  # white eyes on the colored head-row cells
ERROR_TINT = (239, 68, 68)

POSE_WIDTH = 12
SPRITE_WIDTH = POSE_WIDTH + 2  # 1 column of sway room on each side
SPRITE_HEIGHT = 5

# The exact agy banner logo.
BASE = (
    "    aabb    ",
    "  ccddeeff  ",
    "  gghhiijj  ",
    "  kk    ll  ",
    "mmnn    oopp",
)

# Knees bent: body drops a row, legs fold away.
SQUAT = (
    "            ",
    "    aabb    ",
    "  ccddeeff  ",
    "  gghhiijj  ",
    "mmnn    oopp",
)

# On tiptoe: feet pulled in under the legs.
TIPTOE = (
    "    aabb    ",
    "  ccddeeff  ",
    "  gghhiijj  ",
    "  kk    ll  ",
    "  mn    op  ",
)

# Left foot kicks up beside the leg.
KICK_LEFT = (
    "    aabb    ",
    "  ccddeeff  ",
    "  gghhiijj  ",
    "mnkk    ll  ",
    "        oopp",
)

# Right foot kicks up beside the leg.
KICK_RIGHT = (
    "    aabb    ",
    "  ccddeeff  ",
    "  gghhiijj  ",
    "  kk    llop",
    "mmnn        ",
)

# Side stretches: the crown leans over one way, then the other.
STRETCH_LEFT = (
    "  aabb      ",
    "  ccddeeff  ",
    "  gghhiijj  ",
    "  kk    ll  ",
    "mmnn    oopp",
)
STRETCH_RIGHT = (
    "      aabb  ",
    "  ccddeeff  ",
    "  gghhiijj  ",
    "  kk    ll  ",
    "mmnn    oopp",
)

# Eyes sit on the first full-width (head) row of a pose, at these pose columns:
# one in the second cell, one in the third, leaving a 2-column gap between.
EYE_COLS = (4, 7)

# A frame is (pose, x offset within the sprite, sparkles, brightness, eyes).
# Sparkles are (row, col, glyph) in sprite coordinates, drawn on empty cells.
# Eyes are a 2-char string (left, right), or "" for none.
SPARKLES_L = ((0, 1, "✦"), (0, 12, "·"))
SPARKLES_R = ((0, 1, "·"), (0, 12, "✦"))

WORKING_FRAMES = [
    (BASE, 1, (), 1.0, "◕◕"),
    (SQUAT, 1, (), 1.0, "◠◠"),        # happy squint on the way down
    (TIPTOE, 1, SPARKLES_L, 1.08, "◕◕"),
    (KICK_LEFT, 0, (), 1.0, "─◕"),    # wink
    (BASE, 1, (), 1.0, "◕◕"),
    (SQUAT, 1, (), 1.0, "◠◠"),
    (TIPTOE, 1, SPARKLES_R, 1.08, "◕◕"),
    (KICK_RIGHT, 2, (), 1.0, "◕─"),   # wink
]

# tool_use: running in place, stomping between kicks.
TOOL_FRAMES = [
    (KICK_LEFT, 0, (), 1.0, "◕◕"),
    (SQUAT, 1, (), 1.0, "◡◡"),
    (KICK_RIGHT, 2, (), 1.0, "◕◕"),
    (SQUAT, 1, (), 1.0, "◡◡"),
]

# initializing / authenticating: standing still, eyes spin like a loader.
LOADING_FRAMES = [
    (BASE, 1, (), 1.0, "◐◐"),
    (BASE, 1, (), 1.0, "◓◓"),
    (BASE, 1, (), 1.0, "◑◑"),
    (BASE, 1, (), 1.0, "◒◒"),
]

# agy only redraws the status line on state changes, so while idle each
# redraw is a single still frame that stays on screen until the next one.
# Instead of cycling, idle picks the frame that fits the moment:

# Right after a busy stretch ends: a happy "done!" pose.
DONE_FRAME = (TIPTOE, 1, ((0, 1, "✦"), (0, 12, "✦")), 1.08, "◠◠")

# A random fidget on each idle redraw (never the same one twice in a row).
IDLE_FIDGETS = [
    (BASE, 1, (), 1.0, "◕◕"),          # neutral
    (BASE, 0, (), 1.0, "◔◔"),          # glance left
    (BASE, 2, (), 1.0, "◔◔"),          # glance right
    (BASE, 1, (), 1.0, "◕─"),          # wink
    (BASE, 1, (), 1.0, "──"),          # blink
    (SQUAT, 1, (), 1.0, "◡◡"),         # sit down, content
    (TIPTOE, 1, (), 1.0, "◠◠"),        # stretch
    (KICK_LEFT, 0, (), 1.0, "◕◕"),     # tap a foot
    (BASE, 1, ((0, 12, "✦"),), 1.0, "◠◠"),  # admire a sparkle
]

# After a long idle: dozing, slightly dimmed.
SLEEP_FRAMES = [
    (SQUAT, 1, ((0, 11, "z"),), 0.8, "──"),
    (SQUAT, 1, ((0, 11, "z"), (0, 12, "Z")), 0.8, "──"),
]
# agy stops redrawing while idle, so idle motion comes from the terminal's
# own blink attribute (SGR 5): sparkles, snow and other decorations keep
# twinkling with no redraws. These extra twinkles are added to idle frames.
# Set MAGGY_BLINK=0 to turn blinking off.
IDLE_TWINKLES = ((0, 2, "·"), (2, 13, "✦"), (4, 0, "·"))

# Stretch reminder: after a long stretch of work, idle redraws show a side
# stretch (and the mood line nags) until there is a real break.
STRETCH_FRAMES = [
    (STRETCH_LEFT, 1, (), 1.0, "◠◠"),
    (STRETCH_RIGHT, 1, (), 1.0, "◠◠"),
]
BREAK_SECONDS = 300   # idle this long counts as a break and resets the work timer

DONE_SECONDS = 4      # idle redraws within this long after work show DONE_FRAME
SLEEP_SECONDS = 120   # idle longer than this shows SLEEP_FRAMES

# Kept for backwards compatibility with older callers.
IDLE_FRAMES = IDLE_FIDGETS

# Curious lean from side to side.
REVIEWING_FRAMES = [
    (BASE, 0, (), 1.0, "◔◔"),
    (BASE, 1, (), 1.0, "◕◕"),
    (BASE, 2, (), 1.0, "◔◔"),
    (BASE, 1, (), 1.0, "◕◕"),
]

# Dizzy wobble, tinted red.
ERROR_FRAMES = [
    (KICK_LEFT, 0, (), 1.0, "××"),
    (KICK_RIGHT, 2, (), 1.0, "××"),
]

# Props: a small picture drawn to the right of the sprite (a theme's "prop").
# One char per column; each char maps to a cell spec in the theme's
# "prop_cells":
#   bg      background color (a filled cell)
#   fg      glyph color, or
#   chase   a list of glyph colors that cycle by position and frame
#   glyphs  glyphs cycled one per frame (default: a blank)
#   blink   "all" or "alt" (every other cell): blink while idle
# Space = empty.
PROP_GAP = 1  # blank columns between the logo and the prop

# Christmas tree: needles, ornaments, trunk and a twinkling star.
TREE = (
    "  *  ",
    "  G  ",
    " GoG ",
    "oGGGo",
    "  T  ",
)
TREE_GREEN = (22, 128, 61)
TREE_TRUNK = (120, 72, 36)
TREE_STAR = (255, 214, 64)
TREE_STAR_GLYPHS = ("★", "✦")
TREE_GAP = PROP_GAP  # kept for older callers
XMAS_LIGHTS = ((255, 59, 59), (255, 214, 64), (255, 255, 255), (96, 200, 255))

# Jack-o'-lantern with flickering candle-lit eyes and grin.
PUMPKIN = (
    "     ",
    "  s  ",
    " PPP ",
    "PePeP",
    " PmP ",
)
PUMPKIN_ORANGE = (240, 110, 20)
CANDLE = (255, 214, 64)

# Chinese New Year: a red lantern on a gold cord with a swaying tassel.
LANTERN = (
    "  |  ",
    " RRR ",
    "RRgRR",
    " RRR ",
    "  t  ",
)
LANTERN_RED = (214, 32, 32)
GOLD = (255, 196, 37)

# Seasonal themes. A theme recolors logo cells, swaps sparkle glyphs and adds
# extra decorations; poses and frames stay the same. `current_theme()` picks
# one from today's date; a theme saved with `maggy theme` or the
# MAGGY_THEME env var overrides it (`default` opts out).
THEMES = {
    "default": {"description": "the plain logo"},
    # Christmas Day: the crown becomes a Santa hat with a white pom-pom
    # drooping off its side, sparkles turn into snowflakes, snow falls around
    # the logo, a string of twinkling lights wraps the arch, and a little
    # decorated tree with a star stands beside it.
    "xmas": {
        "description": "Santa hat, snow, lights and a tree",
        "colors": {"a": (220, 38, 38), "b": (185, 28, 28)},
        "sparkles": {"✦": "❄", "·": "*"},
        "sparkle_color": (226, 240, 255),
        "pompom": "●",
        "pompom_color": (255, 255, 255),
        # Falling snow: (sprite col, phase, glyph). Each flake moves down one
        # row per frame and wraps; it only shows on empty cells.
        "snowfall": ((0, 0, "*"), (1, 3, "·"), (2, 1, "·"), (11, 4, "·"),
                     (12, 2, "*"), (13, 0, "·"), (10, 3, "*")),
        # Lights on the lower-arch row (pose cols), colors chase each frame.
        "lights": (2, 4, 7, 9),
        "light_glyph": "•",
        "light_colors": XMAS_LIGHTS,
        "prop": TREE,
        "prop_cells": {
            "G": {"bg": TREE_GREEN},
            "o": {"bg": TREE_GREEN, "chase": XMAS_LIGHTS, "glyphs": ("•",), "blink": "alt"},
            "T": {"bg": TREE_TRUNK},
            "*": {"fg": TREE_STAR, "glyphs": TREE_STAR_GLYPHS, "blink": "all"},
        },
    },
    # Halloween: a witch-purple hat, glowing eyes, purple sparkles and a
    # jack-o'-lantern whose candle flickers.
    "halloween": {
        "description": "witch hat, glowing eyes and a jack-o'-lantern",
        "colors": {"a": (88, 44, 130), "b": (60, 28, 96)},
        "eye_color": (255, 196, 37),
        "sparkles": {"✦": "✧", "·": "˙"},
        "sparkle_color": (190, 120, 255),
        "prop": PUMPKIN,
        "prop_cells": {
            "s": {"bg": (70, 120, 40)},
            "P": {"bg": PUMPKIN_ORANGE},
            "e": {"bg": PUMPKIN_ORANGE, "fg": CANDLE, "glyphs": ("▲", "△"), "blink": "all"},
            "m": {"bg": PUMPKIN_ORANGE, "fg": CANDLE, "glyphs": ("◡",)},
        },
    },
    # Chinese New Year: a gold crown, gold sparkles drifting down like
    # confetti and a red lantern with a swaying tassel.
    "cny": {
        "description": "gold crown, gold confetti and a red lantern",
        "colors": {"a": GOLD, "b": (235, 165, 20)},
        "sparkles": {"✦": "✺", "·": "·"},
        "sparkle_color": GOLD,
        "snowfall": ((0, 0, "·"), (1, 3, "✧"), (12, 1, "·"), (13, 4, "✧")),
        "prop": LANTERN,
        "prop_cells": {
            "|": {"fg": GOLD, "glyphs": ("│",)},
            "R": {"bg": LANTERN_RED},
            "g": {"bg": LANTERN_RED, "fg": GOLD, "glyphs": ("◆", "◇"), "blink": "all"},
            "t": {"fg": GOLD, "glyphs": ("┆", "╎"), "blink": "all"},
        },
    },
}

# (month, day) -> theme name.
THEME_DATES = {
    (10, 31): "halloween",
    (12, 25): "xmas",
}

# Chinese New Year follows the lunisolar calendar, so list each date.
CNY_DATES = (
    date(2026, 2, 17), date(2027, 2, 6), date(2028, 1, 26), date(2029, 2, 13),
    date(2030, 2, 3), date(2031, 1, 23), date(2032, 2, 11), date(2033, 1, 31),
    date(2034, 2, 19), date(2035, 2, 8), date(2036, 1, 28),
)
THEME_DAYS = {d: "cny" for d in CNY_DATES}

# Words that can't be theme names (they mean something to `maggy theme`).
RESERVED_THEME_NAMES = ("auto", "list")


def theme_config_path():
    """Config file holding the saved theme (kept for older callers)."""
    return config.config_path()


# ------------------------------------------------------------ user themes
#
# ~/.config/maggy/themes/<name>.json, e.g.
#   {"description": "St Patrick's",
#    "colors": {"crown": "#1f9d55", "feet": [20, 120, 60]},
#    "sparkles": {"✦": "☘"}, "sparkle_color": "#a3e635",
#    "eye_color": "#ffffff", "dates": ["03-17"]}
# Colors are "#rrggbb" or [r, g, b]. Color keys are logo regions (below) or
# single cell letters a-p. Dates are "MM-DD" or "YYYY-MM-DD".
# JSON Schema: docs/theme.schema.json (https://agy-pet.github.io/theme.schema.json).
# Optional "prop" (up to 5 rows x 8 columns) with "prop_cells" draws a
# decoration beside the logo, in the same format as the built-in props
# (see PROP_GAP); glyphs and chase are lists. Optional "base" starts from a
# built-in theme, e.g. "xmas" keeps its tree, snow and lights; "prop": null
# drops the base's prop.

COLOR_REGIONS = {
    "crown": "ab",
    "arch": "cdef",
    "body": "ghij",
    "legs": "kl",
    "feet": "mnop",
}
SPARKLE_GLYPHS = ("✦", "·")
_USER_THEMES = None  # per-process cache: (themes, errors)


def user_themes_dir():
    return os.path.join(config.config_dir(), "themes")


def _parse_color(value):
    if isinstance(value, str):
        v = value.strip().lstrip("#")
        if len(v) == 6:
            try:
                return tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))
            except ValueError:
                pass
    elif isinstance(value, (list, tuple)) and len(value) == 3 and all(
            isinstance(c, int) and not isinstance(c, bool) and 0 <= c <= 255 for c in value):
        return tuple(value)
    raise ValueError(f"bad color {value!r} (use \"#rrggbb\" or [r, g, b])")


def _parse_glyph(value):
    import unicodedata
    g = str(value)
    if len(g) != 1 or not g.isprintable() or g.isspace() or unicodedata.east_asian_width(g) in ("W", "F"):
        raise ValueError(f"bad glyph {value!r} (one printable, single-width character)")
    return g


def _parse_day(value):
    parts = str(value).strip().split("-")
    try:
        nums = [int(p) for p in parts]
        if len(nums) == 2:
            date(2000, nums[0], nums[1])  # leap year, so 02-29 is allowed
            return (nums[0], nums[1])
        if len(nums) == 3:
            return date(*nums)
    except (TypeError, ValueError):
        pass
    raise ValueError(f"bad date {value!r} (use MM-DD or YYYY-MM-DD)")


def parse_user_theme(data):
    """Validate a user theme JSON object into a theme dict; raise ValueError."""
    if not isinstance(data, dict):
        raise ValueError("must be a JSON object")
    th = {}
    colors = {}
    for key, val in (data.get("colors") or {}).items():
        cells = COLOR_REGIONS.get(key, key if key in LOGO_COLORS else None)
        if not cells:
            raise ValueError(f"unknown color key {key!r} (use {', '.join(COLOR_REGIONS)} or a-p)")
        for c in cells:
            colors[c] = _parse_color(val)
    if colors:
        th["colors"] = colors
    sparkles = {}
    for key, val in (data.get("sparkles") or {}).items():
        if key not in SPARKLE_GLYPHS:
            raise ValueError(f"sparkles keys must be {' or '.join(SPARKLE_GLYPHS)}")
        sparkles[key] = _parse_glyph(val)
    if sparkles:
        th["sparkles"] = sparkles
    for key in ("sparkle_color", "eye_color"):
        if key in data:
            th[key] = _parse_color(data[key])
    if "prop" in data:
        prop = data["prop"]
        if prop in (None, []):
            th["prop"] = None  # drop the base theme's prop
        else:
            th["prop"], th["prop_cells"] = _parse_prop(prop, data.get("prop_cells"))
    elif "prop_cells" in data:
        raise ValueError("prop_cells needs a prop")
    dates = data.get("dates") or []
    if not isinstance(dates, list):
        raise ValueError("dates must be a list")
    th["dates"] = [_parse_day(d) for d in dates]
    desc = "".join(ch for ch in str(data.get("description") or "") if ch.isprintable())
    th["description"] = desc[:60] or "your theme"
    # "base": start from a built-in theme (its tree, snow, lights...) and
    # override only what this file sets.
    base = data.get("base", "default")
    if base not in THEMES:
        raise ValueError(f"unknown base {base!r} (use {', '.join(THEMES)})")
    merged = {k: v for k, v in THEMES[base].items() if k != "description"}
    for key in ("colors", "sparkles"):
        if key in th:
            th[key] = {**merged.get(key, {}), **th[key]}
    merged.update(th)
    if merged.get("prop") is None:
        merged.pop("prop", None)
        merged.pop("prop_cells", None)
    return merged


PROP_MAX_WIDTH = 8  # keeps the statusline from growing too wide
PROP_CELL_KEYS = ("bg", "fg", "chase", "glyphs", "blink")
PROP_MAX_FRAMES = 8  # longest glyphs / chase cycle


def _parse_list(value, what, parse):
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list) or not 1 <= len(value) <= PROP_MAX_FRAMES:
        raise ValueError(f"{what} must be a list of 1-{PROP_MAX_FRAMES} items")
    return tuple(parse(v) for v in value)


def _parse_prop(prop, cells):
    """Validate a user prop grid and its cell specs (see PROP_GAP)."""
    if not isinstance(prop, list) or not all(isinstance(r, str) for r in prop):
        raise ValueError("prop must be a list of strings (one per row)")
    if len(prop) > SPRITE_HEIGHT:
        raise ValueError(f"prop can have at most {SPRITE_HEIGHT} rows")
    width = max(len(r) for r in prop)
    if not 1 <= width <= PROP_MAX_WIDTH:
        raise ValueError(f"prop rows must be 1-{PROP_MAX_WIDTH} characters wide")
    # Pad to a full-height, even-width grid; short props stand on the ground.
    rows = [" " * width] * (SPRITE_HEIGHT - len(prop)) + [r.ljust(width) for r in prop]
    if not isinstance(cells, dict):
        raise ValueError("prop needs prop_cells: an object mapping each prop character to a cell")
    used = {ch for r in rows for ch in r if ch != " "}
    if not used:
        raise ValueError("prop is empty")
    missing = sorted(used - set(cells))
    if missing:
        raise ValueError(f"prop_cells has no entry for {', '.join(repr(c) for c in missing)}")
    parsed = {}
    for key in sorted(used):
        spec = cells[key]
        where = f"prop_cells[{key!r}]"
        if not isinstance(spec, dict):
            raise ValueError(f"{where} must be an object")
        unknown = [k for k in spec if k not in PROP_CELL_KEYS]
        if unknown:
            raise ValueError(f"{where}: unknown key {unknown[0]!r} (use {', '.join(PROP_CELL_KEYS)})")
        out = {}
        for k in ("bg", "fg"):
            if k in spec:
                out[k] = _parse_color(spec[k])
        if "chase" in spec:
            out["chase"] = _parse_list(spec["chase"], f"{where}.chase", _parse_color)
        if "glyphs" in spec:
            out["glyphs"] = _parse_list(spec["glyphs"], f"{where}.glyphs", _parse_glyph)
        if "blink" in spec:
            if spec["blink"] not in ("all", "alt"):
                raise ValueError(f"{where}.blink must be \"all\" or \"alt\"")
            out["blink"] = spec["blink"]
        if "bg" not in out and "glyphs" not in out:
            raise ValueError(f"{where} needs bg or glyphs, or it draws nothing")
        parsed[key] = out
    return tuple(rows), parsed


def load_user_themes(refresh=False):
    """Return ({name: theme}, {filename: error}) from user_themes_dir()."""
    global _USER_THEMES
    if _USER_THEMES is not None and not refresh:
        return _USER_THEMES
    themes, errors = {}, {}
    folder = user_themes_dir()
    try:
        names = sorted(os.listdir(folder))
    except OSError:
        names = []
    for fname in names:
        stem, ext = os.path.splitext(fname)
        if ext != ".json" or fname.startswith("."):
            continue
        name = stem.lower()
        if not name.replace("-", "").replace("_", "").isalnum() or not name.isascii() or len(name) > 24:
            errors[fname] = "name must be letters, digits, - or _ (max 24)"
            continue
        if name in THEMES or name in RESERVED_THEME_NAMES:
            errors[fname] = f"{name!r} is a built-in name"
            continue
        path = os.path.join(folder, fname)
        try:
            if os.path.getsize(path) > 64 * 1024:
                raise ValueError("file is too big")
            with open(path, encoding="utf-8") as f:
                th = parse_user_theme(json.load(f))
        except (OSError, ValueError) as e:
            errors[fname] = str(e)
            continue
        th["source"] = path
        themes[name] = th
    _USER_THEMES = (themes, errors)
    return _USER_THEMES


def all_themes():
    """Built-in themes followed by the user's (load_user_themes skips clashes)."""
    return {**THEMES, **load_user_themes()[0]}


def theme_names():
    return list(all_themes())


def saved_theme():
    """Theme name saved with `maggy theme`, or None for auto (by date)."""
    name = str(config.load().get("theme") or "").strip().lower()
    return name if name in all_themes() else None


def theme_for_date(today):
    """Theme picked by date: user themes' dates first, then the built-in ones."""
    for name, th in load_user_themes()[0].items():
        for d in th.get("dates", ()):
            if d == today or d == (today.month, today.day):
                return name
    return THEME_DAYS.get(today) or THEME_DATES.get((today.month, today.day), "default")


def next_cny(today=None):
    today = today or date.today()
    return next((d for d in CNY_DATES if d >= today), None)


def current_theme(today=None):
    """Return the theme to show now.

    Order: MAGGY_THEME env var, then the theme saved with
    `maggy theme`, then the date (theme_for_date), else "default".
    """
    override = (os.environ.get("MAGGY_THEME") or "").strip().lower()
    if override in all_themes():
        return override
    saved = saved_theme()
    if saved:
        return saved
    return theme_for_date(today or date.today())


def _theme(theme):
    if theme is None:
        theme = current_theme()
    themes = all_themes()
    return themes.get(theme, THEMES["default"])


# Narrow-terminal fallback: a 3-column arch, one glyph per logo region.
COMPACT_FRAMES = [
    ("▟", "▀", "▙"),
    ("▘", "▀", "▙"),
    ("▟", "▀", "▙"),
    ("▟", "▀", "▝"),
]
COMPACT_COLORS = (LOGO_COLORS["g"], LOGO_COLORS["b"], LOGO_COLORS["o"])

WORKING_STATES = ("working", "tool_use", "initializing", "authenticating")
LOADING_STATES = ("initializing", "authenticating")


def get_cache_dir():
    """Return a user-private (0700) cache directory, verifying ownership."""
    base = os.environ.get("XDG_CACHE_HOME") or os.path.join(os.path.expanduser("~"), ".cache")
    cache_dir = os.path.join(base, "maggy")
    os.makedirs(cache_dir, mode=0o700, exist_ok=True)
    st = os.lstat(cache_dir)
    if not stat.S_ISDIR(st.st_mode) or stat.S_ISLNK(st.st_mode) or st.st_uid != os.getuid():
        raise PermissionError("Unsafe cache directory")
    os.chmod(cache_dir, 0o700)
    return cache_dir


def atomic_write_json(path, payload):
    """Write JSON atomically with 0600 permissions inside the target directory."""
    parent = os.path.dirname(path)
    fd, tmp_path = tempfile.mkstemp(prefix=".tmp-", dir=parent)
    try:
        os.chmod(tmp_path, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def tick(agent_state=None, state_file=None, min_interval=0.14):
    """Advance the frame counter and track activity across statusline runs.

    Returns (frame, activity) where activity is a dict with:
      idle_for       seconds since agy was last in a busy state
      just_finished  True on the first non-busy redraw after a busy one
    """
    now = time.time()
    track = agent_state is not None  # None: just advance the frame counter
    saved = {}
    if state_file is None:
        try:
            state_file = os.path.join(get_cache_dir(), "state.json")
        except Exception:
            state_file = None
    try:
        if state_file and os.path.isfile(state_file) and not os.path.islink(state_file):
            with open(state_file, "r", encoding="utf-8") as f:
                saved = json.load(f)
    except Exception:
        saved = {}

    try:
        frame = int(saved.get("frame", 0))
        last_ts = float(saved.get("ts", 0.0))
        last_busy = float(saved.get("last_busy", now))
        prev_busy = bool(saved.get("busy", False))
        last_fidget = int(saved.get("fidget", -1))
        work_since = saved.get("work_since")
        work_since = float(work_since) if work_since is not None else None
    except (TypeError, ValueError):
        frame, last_ts, last_busy, prev_busy, last_fidget, work_since = 0, 0.0, now, False, -1, None

    if now - last_ts >= min_interval:
        frame = (frame + 1) % 100000
        last_ts = now
    busy = (agent_state or "").lower() in WORKING_STATES if track else prev_busy
    if track:
        # Continuous work survives short pauses between turns; a pause of
        # BREAK_SECONDS or more starts the clock over.
        on_break = now - last_busy >= BREAK_SECONDS
        if busy and (work_since is None or (not prev_busy and on_break)):
            work_since = now
        elif not busy and on_break:
            work_since = None
    if busy and track:
        last_busy = now

    activity = {
        "idle_for": 0.0 if busy else max(0.0, now - last_busy),
        "just_finished": track and prev_busy and not busy,
        "worked_for": max(0.0, last_busy - work_since) if work_since is not None else 0.0,
    }
    activity["stretch_due"] = _stretch_due(activity)
    # Pick the idle fidget here so it can be persisted and never repeat.
    fidget = last_fidget
    if track and not busy:
        choices = [i for i in range(len(IDLE_FIDGETS)) if i != last_fidget]
        fidget = random.choice(choices)
    activity["fidget"] = fidget

    if state_file:
        try:
            atomic_write_json(state_file, {
                "frame": frame, "ts": last_ts, "last_busy": last_busy,
                "busy": busy, "fidget": fidget, "work_since": work_since,
            })
        except Exception:
            pass
    return frame, activity


def _stretch_due(activity, cfg=None):
    """True once work has run past the user's stretch_after minutes."""
    cfg = cfg if cfg is not None else config.load()
    if not config.flag("stretch", cfg):
        return False
    return (activity["worked_for"] >= cfg["stretch_after"] * 60
            and activity["idle_for"] < BREAK_SECONDS)


def next_frame_index(state_file=None, min_interval=0.14):
    """Advance and return the frame counter (without state tracking)."""
    return tick(None, state_file, min_interval)[0]


def _adjust(rgb, brightness=1.0, tint=None, tint_amount=0.0):
    r, g, b = rgb
    if tint is not None:
        r = r + (tint[0] - r) * tint_amount
        g = g + (tint[1] - g) * tint_amount
        b = b + (tint[2] - b) * tint_amount
    return tuple(max(0, min(255, int(round(c * brightness)))) for c in (r, g, b))


def _bg(rgb):
    return "\033[48;2;%d;%d;%dm" % rgb


def _fg(rgb):
    return "\033[38;2;%d;%d;%dm" % rgb


def _frames_for(state):
    state = (state or "idle").lower()
    if state == "tool_use":
        return TOOL_FRAMES, None
    if state in LOADING_STATES:
        return LOADING_FRAMES, None
    if state in WORKING_STATES:
        return WORKING_FRAMES, None
    if state == "reviewing":
        return REVIEWING_FRAMES, None
    if state == "error":
        return ERROR_FRAMES, ERROR_TINT
    return IDLE_FRAMES, None


def _pick_frame(agent_state, frame_idx, activity):
    frames, tint = _frames_for(agent_state)
    if frames is not IDLE_FIDGETS:
        return frames[frame_idx % len(frames)], tint
    activity = activity or {}
    idle_for = activity.get("idle_for", DONE_SECONDS)
    if activity.get("stretch_due") and idle_for < SLEEP_SECONDS:
        return STRETCH_FRAMES[frame_idx % len(STRETCH_FRAMES)], tint
    if activity.get("just_finished") or idle_for < DONE_SECONDS:
        return DONE_FRAME, tint
    if idle_for >= SLEEP_SECONDS:
        return SLEEP_FRAMES[frame_idx % len(SLEEP_FRAMES)], tint
    fidget = activity.get("fidget")
    if fidget is None or not 0 <= fidget < len(IDLE_FIDGETS):
        fidget = random.Random(frame_idx).randrange(len(IDLE_FIDGETS))
    return IDLE_FIDGETS[fidget], tint


# `maggy motion off`: one still BASE pose per mood, no sway or sparkles. Only
# the eyes (and the error tint / sleepy dimming) still show the state.
STILL_EYES = {
    "reviewing": "◔◔",
    "error": "××",
    "done": "◠◠",
    "sleep": "──",
    "stretch": "◠◠",
}


def _still_frame(agent_state, activity):
    key = mood_key(agent_state, activity)
    tint = ERROR_TINT if key == "error" else None
    brightness = 0.8 if key == "sleep" else 1.0
    return (BASE, 1, (), brightness, STILL_EYES.get(key, "◕◕")), tint


def _motion_enabled():
    return config.flag("motion")


def render_sprite(agent_state="idle", frame_idx=None, activity=None, theme=None, motion=None):
    """Return SPRITE_HEIGHT ANSI lines, each exactly sprite_width(theme) columns wide."""
    if frame_idx is None:
        frame_idx, activity = tick(agent_state)
    if motion is None:
        motion = _motion_enabled()

    th = _theme(theme)
    colors = dict(LOGO_COLORS, **th.get("colors", {}))
    glyph_map = th.get("sparkles", {})
    sparkle_color = th.get("sparkle_color", SPARKLE_COLOR)

    if motion:
        frame, tint = _pick_frame(agent_state, frame_idx, activity)
    else:
        frame, tint = _still_frame(agent_state, activity)
        frame_idx = 0  # freeze snow, lights and the tree star too
    pose, offset, sparkles, brightness, eyes = frame
    # While idle nothing redraws, so decorations blink instead of moving.
    blink = motion and _is_idle(agent_state) and _blink_enabled()
    sparkle_at = {}  # (row, col) -> (glyph, fg color, blinks)
    for c, phase, glyph in th.get("snowfall", ()):
        sparkle_at[((frame_idx + phase) % SPRITE_HEIGHT, c)] = (glyph, sparkle_color, blink)
    if blink:
        for r, c, glyph in IDLE_TWINKLES:
            sparkle_at[(r, c)] = (glyph_map.get(glyph, glyph), sparkle_color, True)
    for r, c, glyph in sparkles:
        sparkle_at[(r, c)] = (glyph_map.get(glyph, glyph), sparkle_color, blink)
    if th.get("pompom"):
        # Just right of the crown (pose cols 4-7), on the crown's row.
        crown_row = next(i for i, row in enumerate(pose) if row.strip())
        sparkle_at[(crown_row, 8 + offset)] = (th["pompom"], th["pompom_color"], False)
    eye_at = {}  # (row, col) -> (glyph, fg color, blinks) drawn on a logo cell
    # The head is the first row at least 4 cells wide (a leaning crown isn't).
    head_row = next(i for i, row in enumerate(pose) if len(row.strip()) >= 8)
    if eyes:
        for glyph, col in zip(eyes, EYE_COLS):
            eye_at[(head_row, col + offset)] = (glyph, th.get("eye_color", EYE_COLOR), False)
    light_colors = th.get("light_colors")
    if light_colors and head_row + 1 < len(pose):
        for i, col in enumerate(th.get("lights", ())):
            color = light_colors[(i + frame_idx) % len(light_colors)]
            # Every other bulb blinks so the string twinkles.
            eye_at[(head_row + 1, col + offset)] = (th.get("light_glyph", "•"), color, blink and i % 2 == 0)

    lines = []
    for row_idx, row in enumerate(pose):
        cells = " " * offset + row + " " * (SPRITE_WIDTH - offset - len(row))
        out = []
        current = None  # active escape sequence, or None for plain
        for col, key in enumerate(cells):
            if key in colors:
                code = _bg(_adjust(colors[key], brightness, tint, 0.6))
                ch = " "
                if (row_idx, col) in eye_at:
                    ch, fg, blinks = eye_at[(row_idx, col)]
                    code += _fg(fg) + (BLINK if blinks else "")
            elif (row_idx, col) in sparkle_at:
                ch, color, blinks = sparkle_at[(row_idx, col)]
                code = _fg(color) + (BLINK if blinks else "")
            else:
                code, ch = None, " "
            if code != current:
                out.append(RESET if code is None else (RESET if current else "") + code)
                current = code
            out.append(ch)
        if current is not None:
            out.append(RESET)
        if th.get("prop"):
            out.append(" " * PROP_GAP + _render_prop_row(th["prop"], th.get("prop_cells", {}), row_idx, frame_idx, blink))
        lines.append("".join(out))
    return lines


def _is_idle(agent_state):
    return _frames_for(agent_state)[0] is IDLE_FIDGETS


def _blink_enabled():
    return config.flag("blink")


# Mood captions, "{name}" is the pet name from config (default Maggy).
MOODS = {
    "working": "{name} is dancing ♪",
    "tool_use": "{name} is stomping around",
    "loading": "{name} is waking up…",
    "reviewing": "{name} is peeking",
    "error": "{name} feels dizzy",
    "done": "{name}: done! ✦",
    "done_n": "{name}: task #{n} today ✦",  # done, with `maggy stats` on
    "idle": "{name} is chilling",
    "sleep": "{name} is sleepy z",
    "stretch": "{name} thinks you should stretch",
}


def mood_key(agent_state="idle", activity=None):
    """Which MOODS entry fits this state (mirrors _pick_frame)."""
    state = (agent_state or "idle").lower()
    activity = activity or {}
    idle_for = activity.get("idle_for", DONE_SECONDS)
    if state == "error":
        return state
    if activity.get("stretch_due") and idle_for < SLEEP_SECONDS:
        return "stretch"
    if state == "tool_use":
        return "tool_use"
    if state in LOADING_STATES:
        return "loading"
    if state in WORKING_STATES:
        return "working"
    if state == "reviewing":
        return state
    if activity.get("just_finished") or idle_for < DONE_SECONDS:
        return "done"
    if idle_for >= SLEEP_SECONDS:
        return "sleep"
    return "idle"


def pet_name(cfg=None):
    cfg = cfg if cfg is not None else config.load()
    name = "".join(ch for ch in str(cfg.get("name") or "") if ch.isprintable()).strip()
    return name[:config.NAME_MAX] or config.DEFAULTS["name"]


def mood_text(agent_state="idle", activity=None, cfg=None):
    """Plain-text mood caption, e.g. "Maggy is dancing ♪"."""
    key = mood_key(agent_state, activity)
    n = (activity or {}).get("tasks_today")
    if key == "done" and n:
        return MOODS["done_n"].format(name=pet_name(cfg), n=n)
    return MOODS[key].format(name=pet_name(cfg))


def sprite_width(theme=None):
    """Visible width of render_sprite() lines for the given theme."""
    prop = _theme(theme).get("prop")
    return SPRITE_WIDTH + (PROP_GAP + len(prop[0]) if prop else 0)


def _render_prop_row(prop, cells, row_idx, frame_idx, blink=False):
    """One row of a theme prop (see PROP_GAP for the cell spec format)."""
    if row_idx >= len(prop):
        return " " * len(prop[0])
    out = []
    for col, key in enumerate(prop[row_idx]):
        spec = cells.get(key)
        if not spec:
            out.append(" ")
            continue
        pos = row_idx * 2 + col // 2
        code = _bg(spec["bg"]) if "bg" in spec else ""
        if spec.get("chase"):
            chase = spec["chase"]
            code += _fg(chase[(pos + frame_idx) % len(chase)])
        elif "fg" in spec:
            code += _fg(spec["fg"])
        mode = spec.get("blink")
        if blink and (mode == "all" or (mode == "alt" and pos % 2 == 0)):
            code += BLINK
        glyphs = spec.get("glyphs") or (" ",)
        out.append(code + glyphs[frame_idx % len(glyphs)] + RESET)
    return "".join(out)


def _render_tree_row(tree, row_idx, frame_idx, ornament_colors, blink=False):
    """Kept for older callers: one row of the Christmas tree."""
    cells = dict(THEMES["xmas"]["prop_cells"])
    cells["o"] = dict(cells["o"], chase=ornament_colors)
    return _render_prop_row(tree, cells, row_idx, frame_idx, blink)


def render_compact(agent_state="idle", frame_idx=None, theme=None, motion=None):
    """Single-line 3-column arch for narrow terminals."""
    if frame_idx is None:
        frame_idx = next_frame_index()
    if motion is None:
        motion = _motion_enabled()
    th_colors = _theme(theme).get("colors", {})
    compact_colors = (COMPACT_COLORS[0], th_colors.get("b", COMPACT_COLORS[1]), COMPACT_COLORS[2])
    state = (agent_state or "idle").lower()
    tint = ERROR_TINT if state == "error" else None
    glyphs = COMPACT_FRAMES[frame_idx % len(COMPACT_FRAMES)] if motion and state in WORKING_STATES else COMPACT_FRAMES[0]
    return "".join(
        f"{_fg(_adjust(color, 1.0, tint, 0.6))}{glyph}"
        for glyph, color in zip(glyphs, compact_colors)
    ) + RESET
