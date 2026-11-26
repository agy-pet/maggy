#!/usr/bin/env python3
"""maggy: Maggy, the dancing Antigravity logo for the agy statusline.

Run `maggy help` for the command list.
"""

import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Hot path: agy runs this every few hundred ms, so render before importing
# anything the other commands need.
RENDER_ARGV = (["statusline"], ["render"], ["statusline", "render"])
if __name__ == "__main__" and sys.argv[1:] in RENDER_ARGV:
    import statusline
    statusline.main()
    sys.exit(0)

import argparse  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
import shlex  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
import tempfile  # noqa: E402
import time  # noqa: E402

STATES = ("working", "tool_use", "initializing", "idle", "reviewing", "error")
PREVIEW_STATES = STATES + ("stretch",)
FORMULA = "agy-pet/tap/maggy"
REPO_URL = "https://github.com/agy-pet/maggy"


# ---------------------------------------------------------------- helpers

def _color(code):
    use = sys.stdout.isatty() and not os.environ.get("NO_COLOR")
    return (lambda s: f"\033[{code}m{s}\033[0m") if use else (lambda s: str(s))


bold, dim, green, red, yellow, cyan = (_color(c) for c in ("1", "2", "32", "31", "33", "36"))


def say(msg):
    print(f"{cyan('==>')} {msg}")


def warn(msg):
    print(f"{yellow('warning:')} {msg}", file=sys.stderr)


def die(msg, code=1):
    print(f"{red('error:')} {msg}", file=sys.stderr)
    sys.exit(code)


def version():
    try:
        with open(os.path.join(ROOT, "VERSION"), encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return "dev"


def install_kind():
    if "/Cellar/" in ROOT or os.environ.get("MAGGY_BREW"):
        return "homebrew"
    if os.path.isdir(os.path.join(ROOT, ".git")):
        return "git"
    return "manual"


def settings_path(override=None):
    return os.path.expanduser(
        override or os.environ.get("AGY_SETTINGS") or "~/.gemini/antigravity-cli/settings.json")


def maggy_bin():
    """Stable path to the maggy executable, used in agy's statusLine command.

    Homebrew's wrapper sets MAGGY_BIN to the opt/ path so upgrades keep working.
    """
    return os.environ.get("MAGGY_BIN") or shutil.which("maggy") or os.path.join(ROOT, "bin", "maggy")


def statusline_command():
    return f"{shlex.quote(maggy_bin())} statusline"


def is_ours(status):
    cmd = (status or {}).get("command") or ""
    return "maggy" in cmd


def read_settings(path):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except ValueError as e:
        die(f"{path} is not valid JSON ({e}); fix it and re-run")
    if not isinstance(data, dict):
        die(f"{path} must contain a JSON object")
    return data


def write_settings(path, data, backup=True):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if backup and os.path.exists(path):
        shutil.copy2(path, path + ".bak")
    fd, tmp = tempfile.mkstemp(prefix=".settings-", dir=os.path.dirname(path))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def our_status(path):
    """(settings, statusLine dict) or die if Maggy isn't hooked up."""
    data = read_settings(path)
    status = data.get("statusLine")
    if not isinstance(status, dict) or not is_ours(status):
        die(f"Maggy isn't set up in {path}; run `maggy setup` first")
    return data, status


def _name_arg(value):
    import config
    try:
        return config.parse_name(value)
    except ValueError as e:
        raise argparse.ArgumentTypeError(str(e))


def _theme_arg(allow_auto=True):
    def check(value):
        from mascot import theme_names
        name = value.strip().lower()
        names = (["auto"] if allow_auto else []) + theme_names()
        if name not in names:
            raise argparse.ArgumentTypeError(f"unknown theme: {value} (choose from: {', '.join(names)})")
        return name
    return check


# --------------------------------------------------------------- commands

def cmd_statusline(_args=None):
    import statusline
    statusline.main()


def cmd_setup(args):
    import config
    path = settings_path(args.settings)
    data = read_settings(path)
    status = data.get("statusLine") if isinstance(data.get("statusLine"), dict) else {}
    if status and not is_ours(status) and not args.force:
        found = f"{path} already has a custom status line:\n  {status.get('command')}\n"
        if sys.stdin.isatty():
            print(f"{yellow('note:')} {found}")
            try:
                answer = input(f"Replace it with Maggy? Your settings will be backed up to "
                               f"{path}.bak first. [y/N] ")
            except (EOFError, KeyboardInterrupt):
                answer = ""
                print()
            if answer.strip().lower() not in ("y", "yes"):
                say("Left your status line as it is.")
                sys.exit(1)
        else:
            executable = "maggy" if shutil.which("maggy") else maggy_bin()
            retry = [executable, "setup", "--force", *args.argv[1:]]
            if os.environ.get("AGY_SETTINGS") and not args.settings:
                retry.extend(["--settings", path])
            die(f"{found}\n"
                f"To use Maggy instead, run this command:\n  {shlex.join(retry)}\n\n"
                f"Maggy will back up your current settings to {path}.bak before switching.")
    status.update({"type": "command", "command": statusline_command(), "enabled": True})
    if args.padding is not None:
        status["padding"] = max(0, args.padding)
    if args.stack is not None:
        status["stack_with_default"] = args.stack
    data["statusLine"] = status
    write_settings(path, data)
    say(f"Hooked Maggy into {path}")
    if os.path.exists(path + ".bak"):
        print(dim(f"    previous settings backed up to {path}.bak"))

    cfg = config.load()
    changed = False
    for key in ("name", "theme"):
        val = getattr(args, key)
        if val is not None:
            cfg[key] = val
            changed = True
    for key in ("blink", "mood", "pet", "motion", "side", "stretch"):
        val = getattr(args, key)
        if val is not None:
            cfg[key] = val
            changed = True
    if changed:
        config.save(cfg)
    print()
    _print_sample("idle", {"idle_for": 0, "just_finished": True, "fidget": 0})
    print()
    say(f"Done! Restart agy (or run {bold('/statusline enable')}) to meet {cfg.get('name') or 'Maggy'}.")
    print(dim("    try: maggy preview working   ·   maggy theme xmas   ·   maggy help"))


def cmd_uninstall(args):
    import config
    path = settings_path(args.settings)
    data = read_settings(path)
    status = data.get("statusLine")
    if isinstance(status, dict) and is_ours(status):
        data.pop("statusLine")
        write_settings(path, data)
        say(f"Removed Maggy's statusLine from {path} (backup: settings.json.bak)")
    else:
        say(f"Maggy isn't hooked into {path}; settings left alone")
    if args.purge:
        import stats
        cache_base = os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache")
        for d in (config.config_dir(), os.path.join(cache_base, "maggy"), stats.state_dir()):
            shutil.rmtree(d, ignore_errors=True)
            print(dim(f"    removed {d}"))
    kind = install_kind()
    if kind == "homebrew":
        print(dim("    to remove the program too: brew uninstall maggy"))
    elif kind == "git":
        print(dim(f"    to remove the program too: rm -rf {ROOT} ~/.local/bin/maggy"))
        print(dim("    and its completion links: rm -f ~/.config/fish/completions/maggy.fish"
                  " ~/.local/share/bash-completion/completions/maggy"))


def _set_enabled(value):
    """value: True, False, or None to toggle."""
    def run(args):
        path = settings_path(args.settings)
        data, status = our_status(path)
        status["enabled"] = (not status.get("enabled", True)) if value is None else value
        write_settings(path, data, backup=False)
        say(f"statusline {'on' if status['enabled'] else 'off'} "
            + dim("(agy picks this up on its next redraw)"))
    return run


cmd_enable = _set_enabled(True)
cmd_disable = _set_enabled(False)
cmd_sl_toggle = _set_enabled(None)


def _print_sample(state, activity, frame=0):
    from mascot import SPRITE_HEIGHT, mood_text, render_sprite
    lines = render_sprite(state, frame, activity)
    caption = dim(mood_text(state, activity))
    for i, line in enumerate(lines):
        print("  " + line + ("  " + caption if i == SPRITE_HEIGHT // 2 else ""))


def cmd_status(args):
    import config
    from mascot import all_themes, current_theme, saved_theme, _blink_enabled, pet_name
    path = settings_path(args.settings)
    data = read_settings(path) if os.path.exists(path) else {}
    status = data.get("statusLine") if isinstance(data.get("statusLine"), dict) else {}
    cfg = config.load()

    if not status:
        hooked = red("not set up") + dim("  (run: maggy setup)")
    elif not is_ours(status):
        hooked = yellow("another statusLine is configured") + dim(f"  ({status.get('command')})")
    elif status.get("enabled", True):
        hooked = green("enabled")
    else:
        hooked = yellow("off") + dim("  (run: maggy statusline on)")

    env_theme = (os.environ.get("MAGGY_THEME") or "").strip().lower()
    theme_note = "env override" if env_theme in all_themes() else (
        "saved" if saved_theme() else "auto, by date")

    print(f"{bold(pet_name(cfg))}  {dim('v' + version() + ' · ' + install_kind())}")
    rows = [
        ("statusline", hooked),
        ("settings", path),
        ("theme", f"{current_theme()} {dim('(' + theme_note + ')')}"),
        ("pet", "on" if config.flag("pet", cfg) else "off"),
        ("motion", "on" if config.flag("motion", cfg) else "off"),
        ("side", cfg["side"]),
        ("blink", "on" if _blink_enabled() else "off"),
        ("mood line", "on" if config.flag("mood", cfg) else "off"),
        ("hidden", ", ".join(cfg["hide"]) or dim("nothing")),
        ("stretch", f"after {cfg['stretch_after']} min" if config.flag("stretch", cfg) else "off"),
        ("stats", "on" if config.flag("stats", cfg) else "off"),
        ("config", config.config_path()),
    ]
    for k, v in rows:
        print(f"  {dim(k.ljust(10))} {v}")
    if not args.quiet:
        print()
        _print_sample("idle", {"idle_for": 10, "fidget": 0})


def cmd_theme(args):
    import config
    from mascot import all_themes, current_theme, saved_theme
    name = (args.name or "").strip().lower()
    if name == "list":
        return _theme_list()
    if name:
        if name != "auto" and name not in all_themes():
            die(f"unknown theme: {args.name} (choose from: auto, {', '.join(all_themes())})", 2)
        cfg = config.load()
        cfg["theme"] = name
        config.save(cfg)
    saved = saved_theme()
    print(f"active theme: {bold(current_theme())}  {dim('[' + (f'set to {saved}' if saved else 'auto (by date)') + ']')}")
    env = (os.environ.get("MAGGY_THEME") or "").strip().lower()
    if env in all_themes():
        print(dim(f"  (MAGGY_THEME={env} is set and takes precedence)"))
    _theme_list()


def _theme_list():
    from mascot import (THEME_DATES, THEMES, all_themes, current_theme, load_user_themes,
                        next_cny, user_themes_dir)
    days = {}
    for (month, day), name in THEME_DATES.items():
        days.setdefault(name, []).append(f"{month:02d}-{day:02d}")
    cny = next_cny()
    if cny:
        days.setdefault("cny", []).append(f"Chinese New Year (next: {cny.isoformat()})")
    themes, errors = load_user_themes()
    for name, th in themes.items():
        for d in th.get("dates", ()):
            days.setdefault(name, []).append(d.isoformat() if hasattr(d, "isoformat") else f"{d[0]:02d}-{d[1]:02d}")
    active = current_theme()
    print("themes:")
    rows = [("auto", "pick by date")] + [(n, th.get("description", "")) for n, th in all_themes().items()]
    width = max(len(n) for n, _ in rows) + 2
    for name, desc in rows:
        note = desc + (" · auto on " + ", ".join(days[name]) if name in days else "")
        if name not in THEMES and name != "auto":
            note = "(yours) " + note
        mark = green("●") if name == active else " "
        print(f" {mark}{name:<{width}}{dim(note)}")
    home = os.path.expanduser("~")
    folder = user_themes_dir()
    folder = "~" + folder[len(home):] if folder.startswith(home) else folder
    print(dim(f"your themes: {folder}/NAME.json (format: {REPO_URL}#themes)"))
    for fname, err in errors.items():
        warn(f"skipped {fname}: {err}")
    print(dim("see them all: maggy preview --once"))


def _bool_setting(key, label):
    def run(args):
        import config
        cfg = config.load()
        if args.value is not None:
            if args.value.strip().lower() == "toggle":
                cfg[key] = not cfg[key]
            else:
                try:
                    cfg[key] = config.parse_bool(args.value)
                except ValueError as e:
                    die(f"{e} (or toggle)", 2)
            config.save(cfg)
        print(f"{label}: {bold('on' if cfg[key] else 'off')}")
        env = config.env_flag("MAGGY_" + key.upper())
        if env is not None and env != cfg[key]:
            print(dim(f"  (MAGGY_{key.upper()} is set and takes precedence)"))
    return run


cmd_blink = _bool_setting("blink", "blink")
cmd_mood = _bool_setting("mood", "mood line")
cmd_pet = _bool_setting("pet", "pet")
cmd_motion = _bool_setting("motion", "motion")


def cmd_stretch(args):
    """on / off / toggle, or a number of minutes (which also turns it on)."""
    import config
    cfg = config.load()
    v = (args.value or "").strip().lower()
    if v:
        if v == "toggle":
            cfg["stretch"] = not cfg["stretch"]
        elif v[:1].isdigit():
            try:
                cfg["stretch_after"] = config.parse_minutes(v)
            except ValueError as e:
                die(str(e), 2)
            cfg["stretch"] = True
        else:
            try:
                cfg["stretch"] = config.parse_bool(v)
            except ValueError as e:
                die(f"{e} (or toggle, or minutes)", 2)
        config.save(cfg)
    if cfg["stretch"]:
        print(f"stretch reminder: {bold('on')}, after {bold(cfg['stretch_after'])} min of continuous work")
    else:
        print(f"stretch reminder: {bold('off')}")
    env = config.env_flag("MAGGY_STRETCH")
    if env is not None and env != cfg["stretch"]:
        print(dim("  (MAGGY_STRETCH is set and takes precedence)"))


SPARKS = "▁▂▃▄▅▆▇█"
HEAT = "·░▒▓█"
STATS_RANGES = {"today": 1, "week": 7, "month": 30, "year": 365}


def _dur(secs):
    secs = int(round(secs))
    if secs < 60:
        return f"{secs}s"
    h, m = divmod(secs // 60, 60)
    if h:
        return f"{h}h {m:02d}m"
    return f"{m}m {secs % 60:02d}s"


def _spark(values, chars=SPARKS):
    top = max(values, default=0)
    if top <= 0:
        return chars[0] * len(values)
    return "".join(chars[0] if v <= 0 else chars[max(1, min(len(chars) - 1, round(v / top * (len(chars) - 1))))]
                   for v in values)


def _heatmap(per_day):
    """GitHub-style grid: one column per week, Monday on top."""
    import datetime as dt
    if not per_day:
        return []
    first = dt.date.fromisoformat(per_day[0]["date"])
    busy = {r["date"]: r["busy"] for r in per_day}
    start = first - dt.timedelta(days=first.weekday())
    end = dt.date.fromisoformat(per_day[-1]["date"])
    weeks = (end - start).days // 7 + 1
    top = max(busy.values(), default=0)
    rows = []
    for wd in range(7):
        cells = []
        for w in range(weeks):
            d = start + dt.timedelta(days=w * 7 + wd)
            v = busy.get(d.isoformat())
            if v is None or d > end:
                cells.append(" ")
            elif v <= 0 or top <= 0:
                cells.append(dim(HEAT[0]))
            else:
                cells.append(green(HEAT[max(1, min(4, round(v / top * 4)))]))
        rows.append("".join(cells))
    labels = ["mon", "", "wed", "", "fri", "", "sun"]
    return [f"{dim(labels[i].ljust(4))}{r}" for i, r in enumerate(rows)]


def _table(rows, total_busy, limit=5):
    ranked = sorted(rows.items(), key=lambda kv: -kv[1][1])[:limit]
    width = max((len(n) for n, _ in ranked), default=0)
    out = []
    for name, (tasks, busy) in ranked:
        share = busy / total_busy if total_busy else 0
        bar = "█" * round(share * 10)
        noun = "task " if tasks == 1 else "tasks"
        out.append(f"{name.ljust(width)}  {tasks:>4} {noun}  {_dur(busy):>8}  {cyan(bar.ljust(10, '·'))}")
    return out


def cmd_stats(args):
    import datetime as dt
    import config
    import stats
    from mascot import pet_name
    what = (args.what or "today").lower()
    cfg = config.load()
    if what in ("on", "off", "toggle"):
        cfg["stats"] = (not cfg["stats"]) if what == "toggle" else what == "on"
        config.save(cfg)
        print(f"stats: {bold('on' if cfg['stats'] else 'off')}"
              + dim("  (counting stops, saved stats stay)" if not cfg["stats"] else ""))
        return
    if what == "reset":
        if not args.yes:
            die("this deletes all saved stats; re-run with --yes", 2)
        stats.reset()
        say("stats reset")
        return
    if what == "path":
        print(stats.stats_path())
        return
    if what == "web":
        import dashboard
        import webbrowser
        from pathlib import Path
        path = dashboard.build(args.out, name=pet_name(cfg))
        say(f"Dashboard written to {path}")
        if not args.no_open:
            webbrowser.open(Path(path).as_uri())
        return

    days = stats.load_days()
    today = dt.date.today()
    if args.days:
        n = max(1, args.days)
    elif what == "all":
        first = min(days, default=today.isoformat())
        n = (today - dt.date.fromisoformat(first)).days + 1
    else:
        n = STATS_RANGES[what]
    s = stats.summarize(days, today - dt.timedelta(days=n - 1), today)
    if args.json:
        print(json.dumps(s, indent=2, ensure_ascii=False))
        return

    def fmt_day(iso, year=False):
        d = dt.date.fromisoformat(iso)
        return f"{d.strftime('%b')} {d.day}" + (f", {d.year}" if year else "")

    label = "today" if n == 1 else f"last {n} days"
    long_span = s["from"][:4] != s["to"][:4]
    span = fmt_day(s["to"]) if n == 1 else f"{fmt_day(s['from'], long_span)} – {fmt_day(s['to'], long_span)}"
    print(f"{bold(pet_name(cfg))}'s stats · {label} {dim('(' + span + ')')}")
    if not config.flag("stats", cfg):
        print(dim("  counting is off (turn it on: maggy stats on)"))
    if not s["tasks"] and not s["busy"]:
        print(dim("  nothing yet: Maggy counts a task each time agy finishes a turn"))
        if s["streak"] or s["best_streak"]:
            print(f"  {dim('streak'.ljust(10))} {s['streak']} days · best {s['best_streak']}")
        return

    rows = []
    err = f" · {red(str(s['errors']) + ' errors')} ({round(s['errors'] * 100 / max(1, s['tasks']))}%)" if s["errors"] else ""
    rows.append(("tasks", f"{bold(s['tasks'])}{err}"))
    tool = f" · tool use {round(s['tool'] * 100 / s['busy'])}%" if s["busy"] else ""
    rows.append(("dancing", f"{bold(_dur(s['busy']))}{dim(tool)}"))
    if s["tasks"]:
        longest = _dur(s["longest"]) + (dim(f" ({fmt_day(s['longest_day'])})") if n > 1 and s["longest_day"] else "")
        rows.append(("per task", f"avg {_dur(s['busy'] / s['tasks'])} · longest {longest}"))
    if s["wait"] >= 1:
        rows.append(("waited", f"{_dur(s['wait'])} {dim('for your approval')}"))
    if s["peak_context"]:
        rows.append(("peak ctx", f"{s['peak_context']}%"))
    if s["quota"]:
        q = " · ".join(f"{k} {v:g}%" for k, v in sorted(s["quota"].items()))
        rows.append(("quota", f"{q} {dim('burned')}"))
    streak = f"{bold(s['streak'])} day{'s' if s['streak'] != 1 else ''}"
    rows.append(("streak", streak + dim(f" · best {s['best_streak']}")))
    if s["busy"]:
        peak = max(range(24), key=lambda h: s["hours"][h])
        night = sum(s["hours"][h] for h in range(0, 6)) / s["busy"]
        fun = f"busiest hour {peak:02d}:00"
        if night >= 0.05:
            fun += f" · night owl {round(night * 100)}%"
        rows.append(("rhythm", fun))
    for k, v in rows:
        print(f"  {dim(k.ljust(10))} {v}")

    print()
    print(f"  {dim('by hour'.ljust(10))} {cyan(_spark(s['hours']))}")
    print(f"  {' ' * 10} {dim('0     6     12    18  23')}")
    per_day = s["per_day"]
    if 1 < n <= 60:
        print(f"  {dim('by day'.ljust(10))} {cyan(_spark([d['busy'] for d in per_day]))}"
              + dim(f"  busy time, {fmt_day(per_day[0]['date'])} → today"))
    elif n > 60:
        print()
        for line in _heatmap(per_day[-371:]):
            print(f"  {line}")
    for title, table in (("models", s["models"]), ("projects", s["projects"])):
        lines = _table(table, s["busy"])
        if lines:
            print()
            for i, line in enumerate(lines):
                print(f"  {dim((title if i == 0 else '').ljust(10))} {line}")
    print()
    print(dim("  charts and heatmaps in your browser: maggy stats web"))


def _pet_shortcut(value):
    return lambda args: cmd_pet(argparse.Namespace(value=value))


def cmd_side(args):
    import config
    cfg = config.load()
    if args.value:
        v = args.value.strip().lower()
        if v == "toggle":
            v = "right" if cfg["side"] == "left" else "left"
        if v not in config.SIDES:
            die(f"expected left, right or toggle, got {args.value!r}", 2)
        cfg["side"] = v
        config.save(cfg)
    print(f"side: {bold(cfg['side'])}")


def _segments_state(cfg):
    import config
    hidden = set(cfg["hide"])
    for name in config.SEGMENTS:
        print(f"  {name:<10} {dim('hidden') if name in hidden else green('shown')}")


def _show_hide(hide):
    def run(args):
        import config
        cfg = config.load()
        if args.segments:
            try:
                names = config.parse_segments(args.segments)
            except ValueError as e:
                die(str(e), 2)
            hidden = set(cfg["hide"])
            hidden = hidden | set(names) if hide else hidden - set(names)
            cfg["hide"] = [s for s in config.SEGMENTS if s in hidden]
            config.save(cfg)
        _segments_state(cfg)
    return run


cmd_show = _show_hide(False)
cmd_hide = _show_hide(True)


def cmd_name(args):
    import config
    from mascot import pet_name
    cfg = config.load()
    if args.reset:
        cfg["name"] = config.DEFAULTS["name"]
        config.save(cfg)
    elif args.new_name:
        try:
            cfg["name"] = config.parse_name(" ".join(args.new_name))
        except ValueError as e:
            die(str(e), 2)
        config.save(cfg)
    print(f"pet name: {bold(pet_name(cfg))}")


def cmd_config(args):
    import config
    cfg = config.load()
    action = args.action or "show"
    if action == "path":
        print(config.config_path())
    elif action == "show":
        print(json.dumps(cfg, indent=2, ensure_ascii=False))
    elif action == "get":
        if args.key not in config.DEFAULTS:
            die(f"unknown key: {args.key} (keys: {', '.join(config.DEFAULTS)})", 2)
        val = cfg[args.key]
        print(json.dumps(val) if isinstance(val, (bool, list, int)) else val)
    elif action == "set":
        if args.key not in config.DEFAULTS or args.value is None:
            die(f"usage: maggy config set <{'|'.join(config.DEFAULTS)}> <value>", 2)
        if args.key == "stretch_after":
            try:
                cfg[args.key] = config.parse_minutes(args.value)
            except ValueError as e:
                die(str(e), 2)
        elif args.key in config.BOOL_KEYS:
            try:
                cfg[args.key] = config.parse_bool(args.value)
            except ValueError as e:
                die(str(e), 2)
        elif args.key == "hide":
            try:
                cfg["hide"] = [s for s in config.SEGMENTS if s in config.parse_segments([args.value])]
            except ValueError as e:
                die(str(e), 2)
        elif args.key == "side":
            if args.value not in config.SIDES:
                die(f"side must be one of: {', '.join(config.SIDES)}", 2)
            cfg["side"] = args.value
        elif args.key == "theme":
            from mascot import all_themes
            if args.value not in ("auto", *all_themes()):
                die(f"unknown theme: {args.value}", 2)
            cfg["theme"] = args.value
        elif args.key == "name":
            try:
                cfg["name"] = config.parse_name(args.value)
            except ValueError as e:
                die(str(e), 2)
        else:
            cfg[args.key] = args.value
        config.save(cfg)
        val = cfg[args.key]
        print(f"{args.key} = {json.dumps(val) if isinstance(val, (bool, list)) else val}")
    elif action == "reset":
        try:
            os.unlink(config.config_path())
        except OSError:
            pass
        say("config reset to defaults")


def cmd_preview(args):
    if args.name:
        import config
        _load = config.load
        config.load = lambda: dict(_load(), name=args.name)
    import preview
    preview.main(args.state, once=args.once, width=args.width,
                 themes=[args.theme] if args.theme else None)


def latest_release_tag():
    """Newest vX.Y.Z tag on origin, or None."""
    res = subprocess.run(["git", "-C", ROOT, "ls-remote", "--tags", "--refs", "origin", "v*"],
                         capture_output=True, text=True, timeout=30)
    best = None
    for line in res.stdout.splitlines():
        m = re.fullmatch(r"\S+\s+refs/tags/(v(\d+)\.(\d+)\.(\d+))", line.strip())
        if m:
            key = tuple(int(n) for n in m.groups()[1:])
            if best is None or key > best[0]:
                best = (key, m.group(1))
    return best[1] if best else None


def cmd_update(_args):
    kind = install_kind()
    if kind == "homebrew":
        say(f"brew upgrade {FORMULA}")
        os.execvp("brew", ["brew", "upgrade", FORMULA])
    if kind == "git":
        git = ["git", "-C", ROOT]
        branch = subprocess.run(git + ["symbolic-ref", "-q", "--short", "HEAD"],
                                capture_output=True, text=True).stdout.strip()
        if branch:  # a dev checkout on a branch: follow it
            say(f"Updating {ROOT} ({branch})")
            subprocess.run(git + ["pull", "--ff-only"], check=True)
        else:  # the installer pins a release tag: move to the newest one
            tag = latest_release_tag()
            if not tag:
                die("couldn't find a release tag on origin; check your network and try again")
            say(f"Updating {ROOT} to {tag}")
            subprocess.run(git + ["fetch", "--depth", "1", "--quiet", "origin", f"refs/tags/{tag}"], check=True)
            subprocess.run(git + ["checkout", "--quiet", "--detach", "FETCH_HEAD"], check=True)
        say(f"Now at v{version()}")
        return
    die(f"don't know how to update a manual install; re-run the installer from {REPO_URL}")


def cmd_doctor(args):
    ok_all = True

    def check(ok, label, hint=""):
        nonlocal ok_all
        ok_all &= bool(ok) or ok is None
        mark = green("✔") if ok else (yellow("!") if ok is None else red("✘"))
        print(f"  {mark} {label}" + (dim(f"  → {hint}") if hint and not ok else ""))

    print(bold("maggy doctor"))
    py = sys.version_info
    check(py >= (3, 8), f"python {py.major}.{py.minor}", "needs python 3.8+")
    check(sys.platform != "win32", f"platform {sys.platform}", "macOS or Linux only")
    agy = shutil.which("agy")
    check(bool(agy) or None, f"agy on PATH{': ' + agy if agy else ''}", "install Antigravity CLI")
    check(bool(shutil.which("maggy")) or None, "maggy on PATH",
          "add ~/.local/bin (or your brew bin) to PATH")
    term = (os.environ.get("COLORTERM") or "").lower()
    check(term in ("truecolor", "24bit") or None, f"truecolor terminal (COLORTERM={term or 'unset'})",
          "the logo uses 24-bit colors; most modern terminals support it")

    path = settings_path(args.settings)
    status = {}
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            check(True, f"settings is valid JSON ({path})")
            status = data.get("statusLine") if isinstance(data.get("statusLine"), dict) else {}
        except ValueError as e:
            check(False, f"settings is valid JSON ({path})", str(e))
    else:
        check(False, f"settings exists ({path})", "run: maggy setup")
    check(is_ours(status), "statusLine points at maggy", "run: maggy setup")
    if is_ours(status):
        check(status.get("enabled", True), "statusLine enabled", "run: maggy statusline on")
        sample = json.dumps({"agent_state": "working", "model": {"display_name": "Gemini"},
                             "terminal_width": 120})
        t0 = time.time()
        try:
            res = subprocess.run(status["command"], shell=True, input=sample, capture_output=True,
                                 text=True, timeout=5, env=dict(os.environ, MAGGY_STATS="0"))
            elapsed = time.time() - t0
            check(res.returncode == 0 and "Gemini" in res.stdout,
                  f"statusline command renders ({elapsed * 1000:.0f} ms)",
                  (res.stderr.strip().splitlines() or ["no output"])[-1])
            check(elapsed < 1.0 or None, "renders under 1s", "agy gives up after 5s")
        except subprocess.TimeoutExpired:
            check(False, "statusline command renders", "timed out after 5s")
    print()
    print(green("All good!") if ok_all else yellow("Some checks need attention."))
    return 0 if ok_all else 1


def cmd_version(_args):
    print(f"maggy {version()} ({install_kind()})")


# ------------------------------------------------------------------- main

def _adder(sub):
    def add(name, func, help_, settings=False, aliases=()):
        sp = sub.add_parser(name, help=help_, description=help_, aliases=list(aliases))
        sp.set_defaults(func=func)
        if settings:
            sp.add_argument("--settings", metavar="PATH",
                            help="agy settings.json (default: $AGY_SETTINGS or ~/.gemini/antigravity-cli/settings.json)")
        return sp
    return add


def _config_keys_help():
    import config
    d = config.DEFAULTS
    onoff = lambda k: "on/off (default: " + ("on" if d[k] else "off") + ")"
    rows = [
        ("name", f"pet name, up to {config.NAME_MAX} chars (default: {d['name']})"),
        ("theme", f"auto or a theme name, see `maggy theme list` (default: {d['theme']})"),
        ("blink", "idle twinkling, " + onoff("blink")),
        ("mood", "mood caption, " + onoff("mood")),
        ("pet", "show the logo, " + onoff("pet")),
        ("motion", "animate, " + onoff("motion")),
        ("side", f"{'/'.join(config.SIDES)} (default: {d['side']})"),
        ("hide", "segments to hide, comma list or all: " + " ".join(config.SEGMENTS)),
        ("stretch", "stretch reminders, " + onoff("stretch")),
        ("stretch_after", "minutes of work before the reminder, %d-%d (default: %d)"
         % (*config.STRETCH_RANGE, d["stretch_after"])),
        ("stats", "count tasks for `maggy stats`, " + onoff("stats")),
    ]
    rows += [(k, f"(default: {d[k]})") for k in d if k not in dict(rows)]  # undocumented new keys
    lines = ["keys:"] + [f"  {k:<14} {v}" for k, v in rows]
    lines += ["", "Env vars win over the file: "
              + ", ".join("MAGGY_" + k.upper() for k in ("theme", *config.BOOL_KEYS)) + "."]
    return "\n".join(lines)


def _add_pet_commands(add):
    add("on", _pet_shortcut("on"), "show the logo")
    add("off", _pet_shortcut("off"), "hide the logo, keep the metrics")
    add("toggle", _pet_shortcut("toggle"), "show or hide the logo")

    sp = add("theme", cmd_theme, "show or switch the theme (list: show them all)")
    sp.add_argument("name", nargs="?", metavar="THEME|list")

    sp = add("blink", cmd_blink, "show or set idle twinkling (on/off/toggle)")
    sp.add_argument("value", nargs="?", metavar="on|off|toggle")
    sp = add("mood", cmd_mood, "show or set the mood caption (on/off/toggle)")
    sp.add_argument("value", nargs="?", metavar="on|off|toggle")
    sp = add("motion", cmd_motion, "animate, or hold a still pose (on/off/toggle)")
    sp.add_argument("value", nargs="?", metavar="on|off|toggle")
    sp = add("stretch", cmd_stretch, "remind you to stretch after long work (on/off/toggle/MINUTES)")
    sp.add_argument("value", nargs="?", metavar="on|off|toggle|MINUTES")
    sp = add("side", cmd_side, "put the logo left or right of the metrics (left/right/toggle)")
    sp.add_argument("value", nargs="?", metavar="left|right|toggle")

    sp = add("name", cmd_name, "show or rename your pet")
    sp.add_argument("new_name", nargs="*", metavar="NAME")
    sp.add_argument("--reset", action="store_true", help="back to Maggy")

    sp = add("preview", cmd_preview, "watch Maggy dance in your terminal (Ctrl+C to stop)")
    sp.add_argument("state", nargs="?", default="working", choices=PREVIEW_STATES,
                    help="which agy state to act out (default: working)")
    sp.add_argument("--theme", type=_theme_arg(allow_auto=False), metavar="THEME",
                    help="preview one theme without saving it (default: all themes, each with its name)")
    sp.add_argument("--name", help="preview another pet name")
    sp.add_argument("--once", action="store_true", help="print a single frame and exit")
    sp.add_argument("--width", type=int, default=120, help="simulated terminal width (default 120)")


def _add_statusline_commands(add):
    add("on", cmd_enable, "turn the statusline on", settings=True, aliases=["enable"])
    add("off", cmd_disable, "turn the statusline off (keeps settings)", settings=True, aliases=["disable"])
    add("toggle", cmd_sl_toggle, "turn the statusline on or off", settings=True)

    import config
    seg_help = "segments: " + " ".join((*config.SEGMENTS, "all"))
    sp = add("show", cmd_show, "show statusline segments (no args: list them)")
    sp.add_argument("segments", nargs="*", metavar="SEGMENT", help=seg_help)
    sp = add("hide", cmd_hide, "hide statusline segments (no args: list them)")
    sp.add_argument("segments", nargs="*", metavar="SEGMENT", help=seg_help)

    add("render", cmd_statusline, "render one statusline from agy's JSON on stdin (what agy runs)")


def build_parser():
    p = argparse.ArgumentParser(
        prog="maggy",
        description="Maggy, the dancing Antigravity logo for the agy statusline.",
    )
    p.add_argument("-V", "--version", action="store_true", help="print the version and exit")
    sub = p.add_subparsers(dest="cmd", metavar="<command>")
    add = _adder(sub)

    sp = add("setup", cmd_setup, "hook Maggy into agy's statusLine (safe to re-run)", settings=True,
             aliases=["install"])
    sp.add_argument("--force", action="store_true", help="replace another tool's statusLine")
    sp.add_argument("--padding", type=int, metavar="N", help="blank lines above the statusline")
    stack = sp.add_mutually_exclusive_group()
    stack.add_argument("--stack", dest="stack", action="store_true", default=None,
                       help="show below agy's built-in statusline")
    stack.add_argument("--no-stack", dest="stack", action="store_false", help="replace agy's built-in statusline")
    sp.add_argument("--theme", type=_theme_arg(), metavar="THEME", help="also set the theme (see: maggy theme list)")
    sp.add_argument("--name", type=_name_arg, help="also set the pet name")
    sp.add_argument("--no-blink", dest="blink", action="store_false", default=None, help="turn off idle twinkling")
    sp.add_argument("--no-mood", dest="mood", action="store_false", default=None, help="hide the mood caption")
    sp.add_argument("--no-pet", dest="pet", action="store_false", default=None, help="hide the logo, keep the metrics")
    sp.add_argument("--no-motion", dest="motion", action="store_false", default=None, help="hold a still pose")
    sp.add_argument("--side", choices=["left", "right"], help="put the logo left or right of the metrics")
    sp.add_argument("--no-stretch", dest="stretch", action="store_false", default=None,
                    help="no stretch reminders")

    sp = add("uninstall", cmd_uninstall, "remove Maggy from agy's statusLine", settings=True)
    sp.add_argument("--purge", action="store_true", help="also delete config, cache and stats")

    sp = add("status", cmd_status, "show setup, settings and a sample of Maggy", settings=True)
    sp.add_argument("-q", "--quiet", action="store_true", help="skip the sample render")

    # Pet commands: `maggy pet <cmd>`, or just `maggy <cmd>` since pet is the default group.
    _add_pet_commands(add)
    sp = add("pet", cmd_pet, "pet commands (the default group: `maggy pet theme` = `maggy theme`)")
    sp.set_defaults(value=None)
    pet_sub = sp.add_subparsers(dest="pet_cmd", metavar="<command>")
    _add_pet_commands(_adder(pet_sub))

    sp = add("statusline", cmd_statusline,
             "statusline commands; with no command it renders agy's JSON on stdin (what agy runs)")
    sl_sub = sp.add_subparsers(dest="sl_cmd", metavar="<command>")
    _add_statusline_commands(_adder(sl_sub))

    # Old top-level spellings, kept working but unlisted.
    for name, func, seg in (("enable", cmd_enable, False), ("disable", cmd_disable, False),
                            ("show", cmd_show, True), ("hide", cmd_hide, True)):
        sp = sub.add_parser(name)
        sp.set_defaults(func=func)
        if seg:
            sp.add_argument("segments", nargs="*")
        else:
            sp.add_argument("--settings", metavar="PATH")

    sp = add("config", cmd_config, "show, get or set config values")
    sp.add_argument("action", nargs="?", choices=["show", "get", "set", "reset", "path"],
                    help="show (default): print the config; get KEY; set KEY VALUE; "
                         "reset: back to defaults; path: print the file's location")
    sp.add_argument("key", nargs="?")
    sp.add_argument("value", nargs="?")
    sp.formatter_class = argparse.RawDescriptionHelpFormatter
    sp.epilog = _config_keys_help()

    sp = add("stats", cmd_stats, "tasks, busy time and streaks (today/week/month/year/all, web, on/off)")
    sp.formatter_class = argparse.RawDescriptionHelpFormatter
    sp.epilog = (
        "actions:\n"
        "  today|week|month|year|all  stats for that range (default: today)\n"
        "  web                        open the dashboard in your browser\n"
        "  on | off | toggle          start or stop counting (default: on; off keeps saved stats)\n"
        "  reset --yes                delete all saved stats\n"
        "  path                       print where stats are saved\n"
        "\n"
        "Stats stay on this machine. Also: config key `stats`, env MAGGY_STATS=0.")
    sp.add_argument("what", nargs="?", metavar="RANGE|web|on|off|toggle|reset|path",
                    choices=[*STATS_RANGES, "all", "web", "on", "off", "toggle", "reset", "path"])
    sp.add_argument("--out", metavar="PATH", help="where `stats web` writes the page")
    sp.add_argument("--no-open", action="store_true", help="`stats web`: don't open a browser")
    sp.add_argument("--days", type=int, metavar="N", help="the last N days instead of a named range")
    sp.add_argument("--json", action="store_true", help="print the numbers as JSON")
    sp.add_argument("--yes", action="store_true", help="confirm `stats reset`")

    add("doctor", cmd_doctor, "check python, terminal and agy settings", settings=True)
    add("update", cmd_update, "upgrade to the latest version", aliases=["upgrade"])
    add("version", cmd_version, "print the version")
    sub.add_parser("help", help="show this help").set_defaults(func=None)
    p.format_help = lambda: _grouped_help(sub, pet_sub, sl_sub)
    return p


def _grouped_help(sub, pet_sub, sl_sub):
    """Top-level help, grouped into pet / statusline / general commands."""
    def rows(action, prefix=""):
        return [(prefix + a.metavar, a.help) for a in action._choices_actions]

    pet_names = set(pet_sub.choices)
    top = [(n, h) for n, h in rows(sub) if n.split()[0] not in pet_names | {"pet", "statusline"}]
    sections = [
        ("Pet commands (the `pet` prefix is optional: maggy theme xmas = maggy pet theme xmas)",
         rows(pet_sub, "[pet] ")),
        ("Statusline commands", [("statusline", "render agy's JSON from stdin (what agy runs)")]
         + rows(sl_sub, "statusline ")),
        ("General", top),
    ]
    width = max(len(n) for _, items in sections for n, _ in items) + 2
    out = [bold("Maggy") + ", the dancing Antigravity logo for the agy statusline.", "",
           "usage: maggy [pet] <command>  |  maggy statusline <command>  |  maggy <command>", ""]
    for title, items in sections:
        out.append(title + ":")
        out += [f"  {n.ljust(width)}{dim(h)}" for n, h in items]
        out.append("")
    out += ["options: -h, --help   -V, --version", "",
            "Run `maggy <command> -h` for a command's options.  Docs: " + REPO_URL]
    return "\n".join(out) + "\n"


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    # Hot path: agy calls this every few hundred ms, skip argparse.
    if argv in RENDER_ARGV:
        return cmd_statusline()
    parser = build_parser()
    args = parser.parse_args(argv)
    args.argv = argv
    if args.version:
        return cmd_version(args)
    if not getattr(args, "func", None):
        parser.print_help()
        return 0
    return args.func(args) or 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
