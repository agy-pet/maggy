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
import shlex  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
import tempfile  # noqa: E402
import time  # noqa: E402

STATES = ("working", "tool_use", "initializing", "idle", "reviewing", "error")
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
        die(f"{path} already has a custom statusLine:\n  {status.get('command')}\n"
            "re-run with --force to replace it (the old file is kept as settings.json.bak)")
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
    for key in ("blink", "mood", "pet", "motion", "side"):
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
        cache_base = os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache")
        for d in (config.config_dir(), os.path.join(cache_base, "maggy")):
            shutil.rmtree(d, ignore_errors=True)
            print(dim(f"    removed {d}"))
    kind = install_kind()
    if kind == "homebrew":
        print(dim("    to remove the program too: brew uninstall maggy"))
    elif kind == "git":
        print(dim(f"    to remove the program too: rm -rf {ROOT} ~/.local/bin/maggy"))


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
    from mascot import THEMES, current_theme, saved_theme, _blink_enabled, pet_name
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
    theme_note = "env override" if env_theme in THEMES else (
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
        ("config", config.config_path()),
    ]
    for k, v in rows:
        print(f"  {dim(k.ljust(10))} {v}")
    if not args.quiet:
        print()
        _print_sample("idle", {"idle_for": 10, "fidget": 0})


def cmd_theme(args):
    import config
    from mascot import THEMES, THEME_DATES, current_theme, saved_theme
    if args.name:
        name = args.name.strip().lower()
        if name != "auto" and name not in THEMES:
            die(f"unknown theme: {args.name} (choose from: auto, {', '.join(THEMES)})", 2)
        cfg = config.load()
        cfg["theme"] = name
        config.save(cfg)
    saved = saved_theme()
    print(f"active theme: {bold(current_theme())}  {dim('[' + (f'set to {saved}' if saved else 'auto (by date)') + ']')}")
    env = (os.environ.get("MAGGY_THEME") or "").strip().lower()
    if env in THEMES:
        print(dim(f"  (MAGGY_THEME={env} is set and takes precedence)"))
    days = {}
    for (month, day), name in THEME_DATES.items():
        days.setdefault(name, []).append(f"{month:02d}-{day:02d}")
    print("themes:")
    for name in ["auto", *THEMES]:
        note = "pick by date" if name == "auto" else (
            "auto on " + ", ".join(days[name]) if name in days else "the plain logo")
        print(f"  {name:<8} {dim(note)}")
    print(dim("  see them all: maggy preview --once"))


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
        print(json.dumps(val) if isinstance(val, (bool, list)) else val)
    elif action == "set":
        if args.key not in config.DEFAULTS or args.value is None:
            die(f"usage: maggy config set <{'|'.join(config.DEFAULTS)}> <value>", 2)
        if args.key in config.BOOL_KEYS:
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
            from mascot import THEMES
            if args.value not in ("auto", *THEMES):
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


def cmd_update(_args):
    kind = install_kind()
    if kind == "homebrew":
        say(f"brew upgrade {FORMULA}")
        os.execvp("brew", ["brew", "upgrade", FORMULA])
    if kind == "git":
        say(f"Updating {ROOT}")
        subprocess.run(["git", "-C", ROOT, "pull", "--ff-only"], check=True)
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
                                 text=True, timeout=5)
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


def _add_pet_commands(add):
    add("on", _pet_shortcut("on"), "show the logo")
    add("off", _pet_shortcut("off"), "hide the logo, keep the metrics")
    add("toggle", _pet_shortcut("toggle"), "show or hide the logo")

    sp = add("theme", cmd_theme, "show or switch the theme (auto, default, xmas)")
    sp.add_argument("name", nargs="?", metavar="THEME")

    sp = add("blink", cmd_blink, "show or set idle twinkling (on/off/toggle)")
    sp.add_argument("value", nargs="?", metavar="on|off|toggle")
    sp = add("mood", cmd_mood, "show or set the mood caption (on/off/toggle)")
    sp.add_argument("value", nargs="?", metavar="on|off|toggle")
    sp = add("motion", cmd_motion, "animate, or hold a still pose (on/off/toggle)")
    sp.add_argument("value", nargs="?", metavar="on|off|toggle")
    sp = add("side", cmd_side, "put the logo left or right of the metrics (left/right/toggle)")
    sp.add_argument("value", nargs="?", metavar="left|right|toggle")

    sp = add("name", cmd_name, "show or rename your pet")
    sp.add_argument("new_name", nargs="*", metavar="NAME")
    sp.add_argument("--reset", action="store_true", help="back to Maggy")

    sp = add("preview", cmd_preview, "watch Maggy dance in your terminal (Ctrl+C to stop)")
    sp.add_argument("state", nargs="?", default="working", choices=STATES)
    sp.add_argument("--theme", choices=["default", "xmas"], help="preview one theme without saving it (default: all themes, each with its name)")
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
    sp.add_argument("--theme", choices=["auto", "default", "xmas"], help="also set the theme")
    sp.add_argument("--name", type=_name_arg, help="also set the pet name")
    sp.add_argument("--no-blink", dest="blink", action="store_false", default=None, help="turn off idle twinkling")
    sp.add_argument("--no-mood", dest="mood", action="store_false", default=None, help="hide the mood caption")
    sp.add_argument("--no-pet", dest="pet", action="store_false", default=None, help="hide the logo, keep the metrics")
    sp.add_argument("--no-motion", dest="motion", action="store_false", default=None, help="hold a still pose")
    sp.add_argument("--side", choices=["left", "right"], help="put the logo left or right of the metrics")

    sp = add("uninstall", cmd_uninstall, "remove Maggy from agy's statusLine", settings=True)
    sp.add_argument("--purge", action="store_true", help="also delete config and cache")

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
    sp.add_argument("action", nargs="?", choices=["show", "get", "set", "reset", "path"])
    sp.add_argument("key", nargs="?")
    sp.add_argument("value", nargs="?")

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
