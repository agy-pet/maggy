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

# A small Christmas tree drawn to the right of the sprite. One char per
# column: G = green needle cell, o = ornament on a needle cell, T = trunk,
# * = twinkling star, space = empty.
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
TREE_GAP = 1  # blank columns between the logo and the tree

# Seasonal themes. A theme recolors logo cells, swaps sparkle glyphs and adds
# extra decorations; poses and frames stay the same. `current_theme()` picks
# one from today's date; a theme saved with `maggy theme` or the
# MAGGY_THEME env var overrides it (`default` opts out).
THEMES = {
    "default": {},
    # Christmas Day: the crown becomes a Santa hat with a white pom-pom
    # drooping off its side, sparkles turn into snowflakes, snow falls around
    # the logo, a string of twinkling lights wraps the arch, and a little
    # decorated tree with a star stands beside it.
    "xmas": {
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
        "light_colors": ((255, 59, 59), (255, 214, 64), (255, 255, 255), (96, 200, 255)),
        "tree": TREE,
    },
}

# (month, day) -> theme name.
THEME_DATES = {
    (12, 25): "xmas",
}


def theme_config_path():
    """Config file holding the saved theme (kept for older callers)."""
    return config.config_path()


def saved_theme():
    """Theme name saved with `maggy theme`, or None for auto (by date)."""
    name = str(config.load().get("theme") or "").strip().lower()
    return name if name in THEMES else None


def current_theme(today=None):
    """Return the theme to show now.

    Order: MAGGY_THEME env var, then the theme saved with
    `maggy theme`, then the date (THEME_DATES), else "default".
    """
    override = (os.environ.get("MAGGY_THEME") or "").strip().lower()
    if override in THEMES:
        return override
    saved = saved_theme()
    if saved:
        return saved
    today = today or date.today()
    return THEME_DATES.get((today.month, today.day), "default")


def _theme(theme):
    if theme is None:
        theme = current_theme()
    return THEMES.get(theme, THEMES["default"])


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
    except (TypeError, ValueError):
        frame, last_ts, last_busy, prev_busy, last_fidget = 0, 0.0, now, False, -1

    if now - last_ts >= min_interval:
        frame = (frame + 1) % 100000
        last_ts = now
    busy = (agent_state or "").lower() in WORKING_STATES if track else prev_busy
    if busy and track:
        last_busy = now

    activity = {
        "idle_for": 0.0 if busy else max(0.0, now - last_busy),
        "just_finished": track and prev_busy and not busy,
    }
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
                "busy": busy, "fidget": fidget,
            })
        except Exception:
            pass
    return frame, activity


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
    head_row = next(i for i, row in enumerate(pose) if row[EYE_COLS[0] - 2] != " ")
    if eyes:
        for glyph, col in zip(eyes, EYE_COLS):
            eye_at[(head_row, col + offset)] = (glyph, EYE_COLOR, False)
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
        if th.get("tree"):
            out.append(" " * TREE_GAP + _render_tree_row(th["tree"], row_idx, frame_idx, light_colors or (TREE_STAR,), blink))
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
    "idle": "{name} is chilling",
    "sleep": "{name} is sleepy z",
}


def mood_key(agent_state="idle", activity=None):
    """Which MOODS entry fits this state (mirrors _pick_frame)."""
    state = (agent_state or "idle").lower()
    if state == "tool_use":
        return "tool_use"
    if state in LOADING_STATES:
        return "loading"
    if state in WORKING_STATES:
        return "working"
    if state in ("reviewing", "error"):
        return state
    activity = activity or {}
    idle_for = activity.get("idle_for", DONE_SECONDS)
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
    return MOODS[mood_key(agent_state, activity)].format(name=pet_name(cfg))


def sprite_width(theme=None):
    """Visible width of render_sprite() lines for the given theme."""
    tree = _theme(theme).get("tree")
    return SPRITE_WIDTH + (TREE_GAP + len(tree[0]) if tree else 0)


def _render_tree_row(tree, row_idx, frame_idx, ornament_colors, blink=False):
    """One row of the tree; ornaments and the star twinkle with the frame.

    With blink on (idle), the star and every other ornament blink instead.
    """
    if row_idx >= len(tree):
        return " " * len(tree[0])
    out = []
    for col, key in enumerate(tree[row_idx]):
        if key == "G":
            out.append(_bg(TREE_GREEN) + " " + RESET)
        elif key == "o":
            color = ornament_colors[(row_idx * 2 + col // 2 + frame_idx) % len(ornament_colors)]
            code = BLINK if blink and (row_idx * 2 + col // 2) % 2 == 0 else ""
            out.append(_bg(TREE_GREEN) + _fg(color) + code + "•" + RESET)
        elif key == "T":
            out.append(_bg(TREE_TRUNK) + " " + RESET)
        elif key == "*":
            out.append(_fg(TREE_STAR) + (BLINK if blink else "") + TREE_STAR_GLYPHS[frame_idx % 2] + RESET)
        else:
            out.append(" ")
    return "".join(out)


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
