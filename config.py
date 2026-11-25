"""User config for Maggy, stored as JSON.

Location: $XDG_CONFIG_HOME/maggy/config.json (default
~/.config/maggy/config.json). Env vars still win over it:
MAGGY_THEME, MAGGY_BLINK, MAGGY_MOOD, MAGGY_PET, MAGGY_MOTION, MAGGY_STRETCH,
MAGGY_STATS.
"""

import json
import os
import tempfile

DEFAULTS = {
    "name": "Maggy",   # pet name shown in the mood line
    "theme": "auto",   # auto | a theme name (`maggy theme list`)
    "blink": True,     # twinkle idle decorations with the terminal blink attribute
    "mood": True,      # show "Maggy is dancing ♪" under the metrics when there is room
    "pet": True,       # show the logo; off leaves just the metrics
    "motion": True,    # animate; off holds one still pose per state
    "side": "left",    # which side of the metrics the logo sits on: left | right
    "hide": [],        # metric segments to hide, see SEGMENTS
    "stretch": True,   # remind you to stretch after a long run of work
    "stretch_after": 45,  # minutes of continuous work before the reminder
    "stats": True,     # count turns and busy time for `maggy stats` (stays on this machine)
}

BOOL_KEYS = ("blink", "mood", "pet", "motion", "stretch", "stats")
STRETCH_RANGE = (5, 600)  # allowed stretch_after minutes
SIDES = ("left", "right")
# Statusline segments that `maggy show/hide` can toggle, in display order.
SEGMENTS = ("model", "context", "quota", "workspace", "git", "effort", "stats")
NAME_MAX = 16


def config_dir():
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(base, "maggy")


def config_path():
    return os.path.join(config_dir(), "config.json")


_CACHE = None  # one statusline render calls load() several times


def load():
    """Return the merged config (defaults + file). Never raises."""
    global _CACHE
    if _CACHE is None:
        _CACHE = _read()
    return dict(_CACHE, hide=list(_CACHE["hide"]))


def _read():
    cfg = dict(DEFAULTS)
    try:
        with open(config_path(), encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            cfg.update({k: v for k, v in data.items() if k in DEFAULTS})
    except (OSError, ValueError):
        pass
    # Hand-edited files: fall back to defaults instead of crashing the statusline.
    for k in BOOL_KEYS:
        if not isinstance(cfg[k], bool):
            cfg[k] = DEFAULTS[k]
    if cfg["side"] not in SIDES:
        cfg["side"] = DEFAULTS["side"]
    try:
        cfg["stretch_after"] = parse_minutes(cfg["stretch_after"])
    except ValueError:
        cfg["stretch_after"] = DEFAULTS["stretch_after"]
    hide = cfg["hide"] if isinstance(cfg["hide"], list) else []
    cfg["hide"] = [s for s in SEGMENTS if s in hide]
    return cfg


def flag(key, cfg=None):
    """A bool setting with its MAGGY_<KEY> env override applied."""
    env = env_flag("MAGGY_" + key.upper())
    if env is not None:
        return env
    cfg = cfg if cfg is not None else load()
    return bool(cfg.get(key, DEFAULTS[key]))


def parse_segments(values):
    """Expand `all` and comma lists into segment names; raise on unknown ones."""
    out = []
    for v in values:
        for name in str(v).replace(",", " ").split():
            name = name.strip().lower()
            if name == "all":
                out.extend(SEGMENTS)
            elif name in SEGMENTS:
                out.append(name)
            else:
                raise ValueError(f"unknown segment: {name} (choose from: {', '.join(SEGMENTS)}, all)")
    return out


def save(cfg):
    """Write only non-default keys, atomically."""
    global _CACHE
    _CACHE = None
    os.makedirs(config_dir(), mode=0o700, exist_ok=True)
    data = {k: v for k, v in cfg.items() if k in DEFAULTS and v != DEFAULTS[k]}
    fd, tmp = tempfile.mkstemp(prefix=".tmp-", dir=config_dir())
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp, config_path())
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def parse_bool(value):
    v = str(value).strip().lower()
    if v in ("1", "true", "yes", "on"):
        return True
    if v in ("0", "false", "no", "off"):
        return False
    raise ValueError(f"expected on/off, got {value!r}")


def parse_minutes(value):
    """stretch_after minutes: a whole number within STRETCH_RANGE."""
    lo, hi = STRETCH_RANGE
    if isinstance(value, bool):
        raise ValueError("expected minutes")
    try:
        n = int(str(value).strip().rstrip("m"))
    except ValueError:
        raise ValueError(f"expected minutes, got {value!r}") from None
    if not lo <= n <= hi:
        raise ValueError(f"minutes must be {lo}-{hi}")
    return n


def parse_name(value):
    """A pet name: 1-NAME_MAX printable characters; raise ValueError otherwise."""
    name = str(value).strip()
    if not name or len(name) > NAME_MAX or not name.isprintable():
        raise ValueError(f"name must be 1-{NAME_MAX} printable characters")
    return name


def env_flag(name):
    """Tri-state env bool: True/False if set, None if unset or unparseable."""
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return None
    try:
        return parse_bool(raw)
    except ValueError:
        return None
