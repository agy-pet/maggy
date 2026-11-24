#!/usr/bin/env python3
"""Antigravity CLI custom statusline with a dancing Antigravity logo."""

import fcntl
import json
import os
import re
import select
import sys
import time
import unicodedata
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import config
from mascot import (
    SPRITE_HEIGHT,
    current_theme,
    mood_text,
    sprite_width,
    atomic_write_json,
    get_cache_dir,
    tick,
    render_compact,
    render_sprite,
)

_CTRL_RE = re.compile(r"[\x00-\x1f\x7f-\x9f]")
_SGR_RE = re.compile(r"\x1b\[[0-9;]*m")


def visible_width(text):
    """Terminal columns taken by text: ANSI stripped, wide/emoji chars count 2."""
    chars = _SGR_RE.sub("", text)
    width = 0
    for i, ch in enumerate(chars):
        if ch == "\ufe0f":
            # Emoji presentation selector: ✍️ renders 2 wide though ✍ alone is 1.
            if i and unicodedata.east_asian_width(chars[i - 1]) not in ("W", "F"):
                width += 1
            continue
        if unicodedata.combining(ch) or unicodedata.category(ch) in ("Mn", "Me", "Cf"):
            continue
        width += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
    return width


def sanitize_text(val):
    """Strip ASCII/C1 control characters to prevent terminal escape injection."""
    return _CTRL_RE.sub("", str(val))


def read_stdin(timeout_sec=0.3):
    if sys.stdin.isatty():
        return ""
    try:
        r, _, _ = select.select([sys.stdin], [], [], timeout_sec)
        if not r:
            return ""
    except Exception:
        return ""

    fd = sys.stdin.fileno()
    try:
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
    except Exception:
        pass

    chunks = []
    deadline = time.time() + 0.5
    while time.time() < deadline:
        try:
            chunk = os.read(fd, 65536)
            if not chunk:
                break
            chunks.append(chunk)
            r2, _, _ = select.select([fd], [], [], 0.02)
            if not r2:
                break
        except (BlockingIOError, InterruptedError):
            break
        except Exception:
            break

    return b"".join(chunks).decode("utf-8", errors="replace")


BLUE = "\033[38;2;0;153;255m"
ORANGE = "\033[38;2;255;176;85m"
GREEN = "\033[38;2;0;175;80m"
CYAN = "\033[38;2;86;182;194m"
RED = "\033[38;2;255;85;85m"
YELLOW = "\033[38;2;230;200;0m"
WHITE = "\033[38;2;220;220;220m"
MAGENTA = "\033[38;2;180;140;255m"
DIM = "\033[2m"
RESET = "\033[0m"
SEP = f" {DIM}│{RESET} "


def color_for_pct(p):
    if p >= 90:
        return RED
    if p >= 70:
        return YELLOW
    if p >= 50:
        return ORANGE
    return GREEN


def build_bar(p, w=10):
    p = max(0, min(100, int(round(p))))
    f = int(round(p * w / 100))
    e = w - f
    c = color_for_pct(p)
    return f"{c}{'●' * f}{DIM}{'○' * e}{RESET}"


def fmt_cd(s):
    if s <= 0:
        return "now"
    if s >= 86400:
        d = s // 86400
        h = (s % 86400) // 3600
        return f"{d}d {h}h" if h > 0 else f"{d}d"
    if s >= 3600:
        h = s // 3600
        m = (s % 3600) // 60
        return f"{h}h {m}m" if m > 0 else f"{h}h"
    if s >= 60:
        return f"{s // 60}m"
    return f"{s}s"


def fmt_time(now, iso, sec, style="datetime"):
    target = None
    if sec and sec > 0:
        target = now + sec
    elif iso:
        try:
            iso_clean = iso.replace("Z", "+00:00")
            dt = datetime.fromisoformat(iso_clean)
            target = dt.timestamp()
        except Exception:
            pass
    if not target:
        return ""
    rem = int(target - now)
    cd = fmt_cd(rem)
    dt_local = datetime.fromtimestamp(target)
    h = dt_local.strftime("%I").lstrip("0")
    if style == "time":
        t_str = f"{h}:{dt_local.strftime('%M%p').lower()}"
    else:
        t_str = f"{dt_local.strftime('%b').lower()} {dt_local.day}, {h}:{dt_local.strftime('%M%p').lower()}"
    return f"{t_str} {DIM}({cd}){RESET}"


def stats_segment(summary):
    """`✓12 🔥5`: tasks finished today, and the daily streak once it's 2+ days."""
    if not summary or not (summary.get("tasks") or summary.get("streak", 0) >= 2):
        return ""
    seg = f"{GREEN}✓{RESET}{WHITE}{summary.get('tasks', 0)}{RESET}"
    if summary.get("streak", 0) >= 2:
        seg += f" 🔥{ORANGE}{summary['streak']}{RESET}"
    return seg


def render_statusline(data, frame_idx=None, activity=None, summary=None):
    now = time.time()
    agent_state = data.get("agent_state") or "idle"
    term_width = int(data.get("terminal_width") or 120)

    if frame_idx is None:
        frame_idx, activity = tick(agent_state)
        import stats
        summary = stats.observe(data, now)
        if summary:
            activity["tasks_today"] = summary["tasks"]

    m = data.get("model") or {}
    model_name = sanitize_text(m.get("display_name") or m.get("id") or "Gemini")
    effort = sanitize_text(m.get("effort") or "medium")

    cw = data.get("context_window") or {}
    pct = cw.get("used_percentage")
    if pct is None:
        u = cw.get("current_usage") or {}
        tok = (
            (u.get("input_tokens") or 0)
            + (u.get("cache_creation_input_tokens") or 0)
            + (u.get("cache_read_input_tokens") or 0)
        )
        sz = cw.get("context_window_size") or 200000
        pct = round(tok * 100 / sz) if sz else 0
    else:
        pct = round(pct)

    q = data.get("quota")
    cache_p = None
    try:
        cache_p = os.path.join(get_cache_dir(), "quota-cache.json")
    except Exception:
        pass
    if isinstance(q, dict) and q:
        if cache_p:
            try:
                atomic_write_json(cache_p, q)
            except Exception:
                pass
    elif cache_p and os.path.isfile(cache_p) and not os.path.islink(cache_p):
        try:
            with open(cache_p, encoding="utf-8") as f:
                q = json.load(f)
        except Exception:
            q = {}
    else:
        q = {}

    rate_rows = []
    inline_quota = ""

    if isinstance(q, dict) and q:
        def get_family_rank(k, current_model):
            k_low = k.lower()
            mod_low = current_model.lower()

            if "gemini" in k_low:
                key_fam = "gemini"
            elif "3p" in k_low or "claude" in k_low:
                key_fam = "3p"
            else:
                key_fam = "other"

            if "gemini" in mod_low:
                active_fam = "gemini"
            elif "3p" in mod_low or "claude" in mod_low:
                active_fam = "3p"
            else:
                active_fam = "other"

            if key_fam == active_fam:
                fam_rank = 0
            elif key_fam == "gemini":
                fam_rank = 1
            elif key_fam == "3p":
                fam_rank = 2
            else:
                fam_rank = 3

            if "5h" in k_low or "current" in k_low:
                period_rank = 0
            elif "wk" in k_low or "weekly" in k_low:
                period_rank = 1
            else:
                period_rank = 2

            return (fam_rank, period_rank, k)

        label_map = {
            "gemini-5h": "gemini 5h",
            "gemini-weekly": "gemini wk",
            "3p-5h": "3p 5h",
            "3p-weekly": "3p wk",
            "current": "current",
            "weekly": "weekly",
        }

        valid_keys = [
            k
            for k in q.keys()
            if isinstance(q[k], dict)
            and not q[k].get("disabled")
            and q[k].get("remaining_fraction") is not None
        ]
        valid_keys.sort(key=lambda k: get_family_rank(k, model_name))
        max_lbl_len = max(
            [len(sanitize_text(label_map.get(k, k))) for k in valid_keys],
            default=9,
        )

        for k in valid_keys:
            info = q[k]
            rem_frac = info.get("remaining_fraction")
            used_p = max(0, min(100, round((1.0 - float(rem_frac)) * 100)))
            lbl = sanitize_text(label_map.get(k, k)).ljust(max_lbl_len)
            bar = build_bar(used_p, 10)
            col = color_for_pct(used_p)
            style = "time" if ("5h" in k or "current" in k) else "datetime"
            r_str = fmt_time(now, info.get("reset_time"), info.get("reset_in_seconds"), style)

            row = f"{WHITE}{lbl}{RESET} {bar} {col}{used_p:3d}%{RESET}"
            if r_str:
                row += f" {DIM}⟳{RESET} {WHITE}{r_str}{RESET}"
            rate_rows.append(row)

            if not inline_quota:
                inline_quota = f"📊 {col}{used_p}%{RESET}"
                if r_str:
                    inline_quota += f" {DIM}⟳{RESET} {WHITE}{r_str}{RESET}"

    cwd = data.get("cwd") or (data.get("workspace") or {}).get("current_dir") or os.getcwd()
    dirname = sanitize_text(os.path.basename(cwd))
    git_str = ""
    try:
        git_dir = os.path.join(cwd, ".git")
        if os.path.isfile(git_dir):
            with open(git_dir, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read().strip()
            if content.startswith("gitdir:"):
                git_dir = content[7:].strip()
                if not os.path.isabs(git_dir):
                    git_dir = os.path.normpath(os.path.join(cwd, git_dir))
        head_path = os.path.join(git_dir, "HEAD")
        if os.path.isfile(head_path):
            with open(head_path, "r", encoding="utf-8", errors="ignore") as f:
                ref = f.read().strip()
            if ref.startswith("ref: refs/heads/"):
                git_str = f" {GREEN}({sanitize_text(ref[16:])}){RESET}"
            elif ref:
                git_str = f" {GREEN}({sanitize_text(ref[:7])}){RESET}"
    except Exception:
        pass

    eff_sym = (
        f"{MAGENTA}● {effort}{RESET}"
        if effort in ("high", "max")
        else (f"{DIM}◔ {effort}{RESET}" if effort == "low" else f"{DIM}◑ {effort}{RESET}")
    )

    cfg = config.load()
    hidden = set(cfg["hide"])
    if "quota" in hidden:
        rate_rows, inline_quota = [], ""

    segments = []
    if "model" not in hidden:
        segments.append(f"{BLUE}{model_name}{RESET}")
    if "context" not in hidden:
        segments.append(f"✍️ {color_for_pct(pct)}{pct}%{RESET}")
    if inline_quota:
        segments.append(inline_quota)
    ws = []
    if "workspace" not in hidden:
        ws.append(f"{CYAN}{dirname}{RESET}")
    if git_str and "git" not in hidden:
        ws.append(git_str.lstrip())
    if ws:
        segments.append(" ".join(ws))
    if "effort" not in hidden:
        segments.append(eff_sym)
    if "stats" not in hidden and config.flag("stats", cfg):
        seg = stats_segment(summary)
        if seg:
            segments.append(seg)
    line1 = SEP.join(segments)
    metrics = ([line1] if line1 else []) + rate_rows
    right_side = cfg["side"] == "right"

    # `maggy pet off`: just the metrics, no logo and no caption.
    if not config.flag("pet", cfg):
        return "\n".join(metrics)

    # Narrow terminal fallback: inline compact arch
    if term_width < 60:
        compact = render_compact(agent_state, frame_idx)
        if not line1:
            first = compact
        else:
            first = f"{line1} {compact}" if right_side else f"{compact} {line1}"
        return "\n".join([first] + rate_rows)

    # Full layout: 5-line dancing Antigravity logo beside the metrics
    theme = current_theme()
    sprite_lines = render_sprite(agent_state, frame_idx, activity, theme)
    right_lines = list(metrics)
    if config.flag("mood", cfg) and len(right_lines) < SPRITE_HEIGHT:
        # Free row beside the logo: a dim caption like "Maggy is dancing ♪".
        right_lines.append(f"{DIM}{sanitize_text(mood_text(agent_state, activity, cfg))}{RESET}")
    pad = " " * sprite_width(theme)
    gap = "  "

    total = max(len(sprite_lines), len(right_lines))
    if right_side:
        # Metric lines vary in width; pad them so the logo stays in one column.
        col = max((visible_width(line) for line in right_lines), default=0)
    out = []
    for i in range(total):
        logo = sprite_lines[i] if i < len(sprite_lines) else pad
        text = right_lines[i] if i < len(right_lines) else ""
        if right_side:
            text += " " * (col - visible_width(text))
            out.append(f"{text}{gap}{logo}" if col else logo)
        else:
            out.append(f"{logo}{gap}{text}" if text else logo)
    return "\n".join(out)


def main():
    raw = read_stdin(0.3)
    if not raw.strip():
        sprite = render_sprite("idle")
        print(f"{sprite[0]}  Gemini\n" + "\n".join(sprite[1:]))
        return

    try:
        data = json.loads(raw)
    except Exception:
        data = {}

    print(render_statusline(data))


if __name__ == "__main__":
    main()
