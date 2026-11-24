"""Usage stats: what Maggy saw agy do, kept per day.

The statusline calls observe() on every real render. It only touches disk
when agy's state changes, and only writes the stats file when a turn ends.

A turn starts when agy goes busy (working, tool_use, initializing,
authenticating) and ends when it goes idle or errors. Time in `reviewing`
(agy waiting for you to approve something) stays inside the turn but is
counted as waiting, not busy.

Files:
  $XDG_CACHE_HOME/maggy/stats-live.json   the open turn of each agy session
  $XDG_STATE_HOME/maggy/stats.json        per-day totals (default ~/.local/state)
"""

import fcntl
import json
import os
import re
import time
from datetime import date, datetime, timedelta

import config
from mascot import WORKING_STATES, atomic_write_json, get_cache_dir

WAIT_STATES = ("reviewing",)
MAX_SEGMENT = 2 * 3600   # a busy/waiting stretch longer than this means agy died mid-turn
KEEP_DAYS = 400          # enough for a year heatmap
KEEP_SESSIONS = 86400    # forget sessions not seen for a day
MAX_KEYS = 30            # models/projects kept per day (the busiest win)
SUMMARY_KEY = "_today"   # stats-live.json entry the statusline reads: today's tasks and streak
_CTRL_RE = re.compile(r"[\x00-\x1f\x7f-\x9f]")


def state_dir():
    base = os.environ.get("XDG_STATE_HOME") or os.path.join(os.path.expanduser("~"), ".local", "state")
    return os.path.join(base, "maggy")


def stats_path():
    return os.path.join(state_dir(), "stats.json")


def _live_path():
    return os.path.join(get_cache_dir(), "stats-live.json")


def _read_json(path):
    try:
        if os.path.islink(path):
            return {}
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _clean(text, limit=40):
    return _CTRL_RE.sub("", str(text)).strip()[:limit]


# ------------------------------------------------------------ recording

def observe(data, now=None):
    """Track agy's state from one statusline payload. Never raises.

    Returns today's {"tasks", "streak"} for the statusline, or None when
    stats are off or nothing is known yet.
    """
    try:
        if not config.flag("stats"):
            return None
        return _observe(data, time.time() if now is None else now)
    except Exception:
        return None


def _observe(data, now):
    state = str(data.get("agent_state") or "idle").lower()
    sid = _clean(data.get("session_id") or data.get("conversation_id") or "_", 80)
    path = _live_path()
    live = _read_json(path)
    cur = live.get(sid)
    if isinstance(cur, dict) and cur.get("s") == state:
        return _today(live.get(SUMMARY_KEY), now)  # hot path: nothing changed, no write

    busy = state in WORKING_STATES
    event = None
    if not isinstance(cur, dict):
        cur = {"s": state, "t": now, "ts": now if busy else None, "b": 0.0, "tl": 0.0, "w": 0.0, "x": False}
    else:
        prev = cur.get("s")
        dur = max(0.0, now - float(cur.get("t") or now))
        if cur.get("ts") is not None:
            if prev in WORKING_STATES or prev in WAIT_STATES:
                if dur > MAX_SEGMENT:
                    cur["x"] = True
                key = "b" if prev in WORKING_STATES else "w"
                cur[key] = float(cur.get(key) or 0) + dur
                if prev == "tool_use":
                    cur["tl"] = float(cur.get("tl") or 0) + dur
        if busy and cur.get("ts") is None:
            cur.update(ts=now, b=0.0, tl=0.0, w=0.0, x=False)
        elif not busy and state not in WAIT_STATES and cur.get("ts") is not None:
            if not cur.get("x") and cur["b"] > 0:
                event = {"start": float(cur["ts"]), "end": now, "busy": cur["b"], "tool": cur["tl"],
                         "wait": cur["w"], "error": state == "error"}
            cur["ts"] = None
        cur["s"], cur["t"] = state, now

    summary = live.get(SUMMARY_KEY)
    live[sid] = cur
    live = {k: v for k, v in live.items() if k != SUMMARY_KEY
            and isinstance(v, dict) and now - float(v.get("t") or 0) < KEEP_SESSIONS}
    if event:
        summary = record(event, data)
    if isinstance(summary, dict):
        live[SUMMARY_KEY] = summary
    atomic_write_json(path, live)
    return _today(summary, now)


def _today(summary, now):
    """The saved summary as seen today: a new day starts at 0 tasks, and the
    streak survives one quiet day (it counts back from yesterday)."""
    if not isinstance(summary, dict):
        return None
    try:
        day = date.fromisoformat(str(summary.get("date")))
        tasks, streak = int(summary.get("tasks") or 0), int(summary.get("streak") or 0)
    except (TypeError, ValueError):
        return None
    today = datetime.fromtimestamp(now).date()
    if day == today:
        return {"tasks": tasks, "streak": streak}
    return {"tasks": 0, "streak": streak if day == today - timedelta(days=1) else 0}


def _hour_chunks(start, end, total):
    """Spread `total` seconds over the local (day, hour) slots that [start, end] covers."""
    span = end - start
    if span <= 0:
        dt = datetime.fromtimestamp(end)
        return [(dt.date().isoformat(), dt.hour, total)]
    out = []
    t = start
    while t < end:
        dt = datetime.fromtimestamp(t)
        nxt = (dt.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)).timestamp()
        seg_end = min(end, nxt)
        out.append((dt.date().isoformat(), dt.hour, total * (seg_end - t) / span))
        t = seg_end
    return out


def _empty_day():
    return {"t": 0, "e": 0, "b": 0.0, "tl": 0.0, "w": 0.0, "lg": 0.0,
            "h": [0.0] * 24, "m": {}, "p": {}, "cx": 0, "q": {}}


def _day(stats, key):
    days = stats.setdefault("days", {})
    d = days.get(key)
    if not isinstance(d, dict):
        d = days[key] = _empty_day()
    for k, v in _empty_day().items():
        if not isinstance(d.get(k), type(v)):
            d[k] = v
    if len(d["h"]) != 24:
        d["h"] = [0.0] * 24
    return d


def _bump(table, name, busy):
    row = table.get(name)
    row = row if isinstance(row, list) and len(row) == 2 else [0, 0.0]
    table[name] = [row[0] + 1, round(row[1] + busy, 1)]
    if len(table) > MAX_KEYS:
        del table[min(table, key=lambda k: table[k][1])]


def _context_pct(data):
    cw = data.get("context_window") or {}
    pct = cw.get("used_percentage")
    if pct is not None:
        return int(round(float(pct)))
    u = cw.get("current_usage") or {}
    tok = sum(int(u.get(k) or 0) for k in
              ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
    size = cw.get("context_window_size") or 200000
    return int(round(tok * 100 / size)) if size else 0


def record(event, data, path=None):
    """Add one finished turn to the per-day totals; return today's summary."""
    path = path or stats_path()
    os.makedirs(os.path.dirname(path), mode=0o700, exist_ok=True)
    with open(path + ".lock", "a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        stats = _read_json(path)
        _apply(stats, event, data)
        atomic_write_json(path, stats)
    end_day = datetime.fromtimestamp(event["end"]).date()
    days = stats.get("days") or {}
    return {"date": end_day.isoformat(), "tasks": days.get(end_day.isoformat(), {}).get("t", 0),
            "streak": streaks(days, end_day)[0]}


def _apply(stats, event, data):
    for day_key, hour, secs in _hour_chunks(event["start"], event["end"], event["busy"]):
        d = _day(stats, day_key)
        d["b"] = round(d["b"] + secs, 1)
        d["h"][hour] = round(d["h"][hour] + secs, 1)

    d = _day(stats, datetime.fromtimestamp(event["end"]).date().isoformat())
    d["t"] += 1
    d["e"] += 1 if event["error"] else 0
    d["tl"] = round(d["tl"] + event["tool"], 1)
    d["w"] = round(d["w"] + event["wait"], 1)
    d["lg"] = round(max(d["lg"], event["busy"]), 1)

    m = data.get("model") or {}
    model = _clean(m.get("display_name") or m.get("id") or "")
    if model:
        _bump(d["m"], model, event["busy"])
    cwd = data.get("cwd") or (data.get("workspace") or {}).get("current_dir") or ""
    project = _clean(os.path.basename(str(cwd).rstrip("/")))
    if project:
        _bump(d["p"], project, event["busy"])
    try:
        d["cx"] = max(d["cx"], _context_pct(data))
    except (TypeError, ValueError):
        pass

    # Quota burned: add up increases in used %, a drop means the window reset.
    q = data.get("quota")
    last = stats.get("quota_last") if isinstance(stats.get("quota_last"), dict) else {}
    if isinstance(q, dict):
        for k, info in q.items():
            if not isinstance(info, dict) or info.get("remaining_fraction") is None:
                continue
            try:
                used = max(0.0, min(100.0, (1.0 - float(info["remaining_fraction"])) * 100))
            except (TypeError, ValueError):
                continue
            k = _clean(k)
            prev = last.get(k)
            if isinstance(prev, (int, float)):
                burned = used - prev if used >= prev else used
                if burned > 0:
                    d["q"][k] = round(d["q"].get(k, 0) + burned, 1)
            last[k] = round(used, 1)
        stats["quota_last"] = last

    cutoff = (date.today() - timedelta(days=KEEP_DAYS)).isoformat()
    stats["days"] = {k: v for k, v in stats["days"].items() if k >= cutoff}
    stats["version"] = 1


def reset():
    for p in (stats_path(), stats_path() + ".lock"):
        try:
            os.unlink(p)
        except OSError:
            pass
    try:
        os.unlink(_live_path())
    except OSError:
        pass


# ------------------------------------------------------------ reporting

def load_days():
    days = _read_json(stats_path()).get("days") or {}
    return {k: v for k, v in days.items() if isinstance(v, dict)}


def summarize(days, start, end):
    """Totals for the dates start..end (inclusive), as a plain dict."""
    keys = []
    d = start
    while d <= end:
        keys.append(d.isoformat())
        d += timedelta(days=1)
    s = {"from": start.isoformat(), "to": end.isoformat(), "days": len(keys),
         "tasks": 0, "errors": 0, "busy": 0.0, "tool": 0.0, "wait": 0.0,
         "longest": 0.0, "longest_day": None, "peak_context": 0,
         "hours": [0.0] * 24, "per_day": [], "models": {}, "projects": {}, "quota": {}}
    for k in keys:
        day = _day({"days": {k: dict(days.get(k) or {})}}, k)
        s["tasks"] += day["t"]
        s["errors"] += day["e"]
        s["busy"] += day["b"]
        s["tool"] += day["tl"]
        s["wait"] += day["w"]
        if day["lg"] > s["longest"]:
            s["longest"], s["longest_day"] = day["lg"], k
        s["peak_context"] = max(s["peak_context"], day["cx"])
        s["hours"] = [a + b for a, b in zip(s["hours"], day["h"])]
        s["per_day"].append({"date": k, "tasks": day["t"], "busy": round(day["b"], 1)})
        for src, dst in ((day["m"], s["models"]), (day["p"], s["projects"])):
            for name, row in src.items():
                if isinstance(row, list) and len(row) == 2:
                    t, b = dst.get(name, [0, 0.0])
                    dst[name] = [t + row[0], b + row[1]]
        for name, pct in day["q"].items():
            s["quota"][name] = round(s["quota"].get(name, 0) + pct, 1)
    for k in ("busy", "tool", "wait", "longest"):
        s[k] = round(s[k], 1)
    s["hours"] = [round(h, 1) for h in s["hours"]]
    s["streak"], s["best_streak"] = streaks(days, end)
    return s


def streaks(days, today):
    """(current, best) runs of consecutive days with at least one task.

    The current streak survives a quiet today: it counts back from yesterday.
    """
    active = {k for k, v in days.items() if isinstance(v, dict) and (v.get("t") or 0) > 0}
    cur = 0
    d = today if today.isoformat() in active else today - timedelta(days=1)
    while d.isoformat() in active:
        cur += 1
        d -= timedelta(days=1)
    best, run, prev = 0, 0, None
    for k in sorted(active):
        dd = date.fromisoformat(k)
        run = run + 1 if prev and dd - prev == timedelta(days=1) else 1
        best, prev = max(best, run), dd
    return cur, max(best, cur)
