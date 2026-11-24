"""`maggy stats web`: a self-contained HTML dashboard for the stats.

Everything (data, styles, script, the Maggy sprite) is inlined into one file,
so it works offline and nothing leaves the machine. The template lives in this
module rather than a separate file so every install method ships it.
"""

import html
import json
import os
import re
import tempfile
import time
from datetime import date

import stats

_SGR = re.compile(r"(\x1b\[[0-9;]*m)")


def ansi_to_html(line):
    """Convert one truecolor ANSI line (as render_sprite makes) to HTML spans."""
    out = []
    fg = bg = None
    blink = dim = False
    for part in _SGR.split(line):
        if not part:
            continue
        if part.startswith("\x1b["):
            codes = [int(c) if c else 0 for c in part[2:-1].split(";")]
            i = 0
            while i < len(codes):
                c = codes[i]
                if c == 0:
                    fg = bg = None
                    blink = dim = False
                elif c == 2:
                    dim = True
                elif c == 5:
                    blink = True
                elif c == 22:
                    dim = False
                elif c == 25:
                    blink = False
                elif c == 39:
                    fg = None
                elif c == 49:
                    bg = None
                elif c in (38, 48) and i + 4 < len(codes) + 1 and codes[i + 1:i + 2] == [2]:
                    rgb = "rgb(%d,%d,%d)" % tuple(codes[i + 2:i + 5])
                    if c == 38:
                        fg = rgb
                    else:
                        bg = rgb
                    i += 4
                i += 1
            continue
        style = []
        if fg:
            style.append(f"color:{fg}")
        if bg:
            style.append(f"background:{bg}")
        if dim:
            style.append("opacity:.6")
        text = html.escape(part)
        if style or blink:
            cls = ' class="tw"' if blink else ""
            out.append(f'<span{cls} style="{";".join(style)}">{text}</span>')
        else:
            out.append(text)
    return "".join(out)


def sprite_html():
    """Maggy's happy "done!" pose in the active theme."""
    from mascot import current_theme, render_sprite
    activity = {"just_finished": True, "idle_for": 0.0, "fidget": 0, "worked_for": 0.0,
                "stretch_due": False}
    lines = render_sprite("idle", 0, activity, current_theme(), motion=True)
    return "\n".join(ansi_to_html(line) for line in lines)


def default_path():
    return os.path.join(stats.state_dir(), "dashboard.html")


def build(out=None, name="Maggy"):
    """Write the dashboard and return its path."""
    path = os.path.abspath(os.path.expanduser(out or default_path()))
    payload = {
        "name": name,
        "today": date.today().isoformat(),
        "generated": time.strftime("%b %-d, %Y %H:%M"),
        "days": stats.load_days(),
        "path": stats.stats_path(),
    }
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    page = (TEMPLATE.replace("__NAME__", html.escape(name))
            .replace("__SPRITE__", sprite_html())
            .replace("__DATA__", data))
    parent = os.path.dirname(path)
    os.makedirs(parent, mode=0o700, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".dashboard-", suffix=".html", dir=parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(page)
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return path


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__NAME__'s stats</title>
<style>
:root {
  --bg: #eeebf3; --card: #fbfafd; --card-2: #f3f0f7; --ink: #1d1726; --muted: #625a70;
  --line: #ddd6e7; --grid: #e7e2ee; --accent: #d9442a; --term: #17121e;
  --s1: #257de0; --s2: #f47230; --hover: rgba(29, 23, 38, .06);
  --h0: #e4dfec; --h1: #b6d5f8; --h2: #6aabf1; --h3: #2370cd; --h4: #0f4a96;
  --mono: ui-monospace, "SF Mono", "JetBrains Mono", Menlo, Consolas, monospace;
  --body: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  color-scheme: light;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #141019; --card: #1b1522; --card-2: #221b2b; --ink: #ece7f2; --muted: #a59db3;
    --line: #2f2839; --grid: #2a2333; --accent: #ff7a4d; --term: #0c0910;
    --s1: #338ced; --s2: #e76624; --hover: rgba(236, 231, 242, .07);
    --h0: #2a2333; --h1: #0f4a96; --h2: #1b64be; --h3: #338ced; --h4: #84b9f3;
    color-scheme: dark;
  }
}
:root[data-theme="dark"] {
  --bg: #141019; --card: #1b1522; --card-2: #221b2b; --ink: #ece7f2; --muted: #a59db3;
  --line: #2f2839; --grid: #2a2333; --accent: #ff7a4d; --term: #0c0910;
  --s1: #338ced; --s2: #e76624; --hover: rgba(236, 231, 242, .07);
  --h0: #2a2333; --h1: #0f4a96; --h2: #1b64be; --h3: #338ced; --h4: #84b9f3;
  color-scheme: dark;
}
*, *::before, *::after { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink); font: 400 15px/1.5 var(--body);
  -webkit-font-smoothing: antialiased; }
main { max-width: 1180px; margin: 0 auto; padding: 32px clamp(16px, 4vw, 40px) 56px; }
.num, .mono { font-family: var(--mono); font-variant-numeric: tabular-nums; }
h1, h2 { margin: 0; font-weight: 650; letter-spacing: -.01em; }

/* header */
header { display: flex; align-items: center; gap: 22px; flex-wrap: wrap; margin-bottom: 26px; }
.term { background: var(--term); border-radius: 14px; padding: 14px 16px 12px;
  box-shadow: 0 1px 0 rgba(255,255,255,.06) inset, 0 10px 30px -12px rgba(23,18,30,.55); }
.term pre { margin: 0; font: 400 15px/1 var(--mono); color: #dcdcdc; white-space: pre; }
.tw { animation: tw 1.6s steps(1) infinite; }
@keyframes tw { 50% { opacity: .15; } }
@media (prefers-reduced-motion: reduce) { .tw { animation: none; } }
.titles { flex: 1 1 260px; min-width: 0; }
.eyebrow { font: 600 11px/1 var(--mono); letter-spacing: .14em; text-transform: uppercase;
  color: var(--accent); margin-bottom: 8px; }
h1 { font-size: clamp(26px, 4vw, 36px); line-height: 1.1; }
.sub { color: var(--muted); margin-top: 6px; font-size: 14px; }
.icon-btn { border: 1px solid var(--line); background: var(--card); color: var(--ink); border-radius: 10px;
  height: 36px; padding: 0 12px; font: 500 13px var(--body); cursor: pointer; display: inline-flex;
  align-items: center; gap: 6px; }
.icon-btn:hover { background: var(--card-2); }

/* range bar */
.rangebar { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 18px; }
.seg { display: inline-flex; background: var(--card); border: 1px solid var(--line); border-radius: 11px;
  padding: 3px; gap: 2px; flex-wrap: wrap; }
.seg button { border: 0; background: transparent; color: var(--muted); font: 500 13px var(--body);
  padding: 6px 12px; border-radius: 8px; cursor: pointer; }
.seg button:hover { color: var(--ink); }
.seg button[aria-pressed="true"] { background: var(--ink); color: var(--bg); }
.chip { display: none; align-items: center; gap: 6px; border: 1px solid var(--accent); color: var(--accent);
  border-radius: 999px; padding: 4px 6px 4px 12px; font: 500 13px var(--body); }
.chip.on { display: inline-flex; }
.chip button { border: 0; background: transparent; color: inherit; cursor: pointer; font-size: 15px;
  line-height: 1; padding: 0 4px; }

/* cards */
.grid { display: grid; gap: 14px; }
.kpis { grid-template-columns: repeat(auto-fit, minmax(165px, 1fr)); margin-bottom: 14px; }
.card { background: var(--card); border: 1px solid var(--line); border-radius: 16px; padding: 18px 20px; min-width: 0; }
.card h2 { font-size: 15px; }
.card-head { display: flex; align-items: baseline; justify-content: space-between; gap: 12px;
  flex-wrap: wrap; margin-bottom: 12px; }
.card-head .meta { color: var(--muted); font-size: 13px; }
.kpi { position: relative; padding: 16px 18px; }
.kpi .label { font: 600 11px/1 var(--mono); letter-spacing: .1em; text-transform: uppercase; color: var(--muted); }
.kpi .value { font: 600 28px/1.15 var(--mono); font-variant-numeric: tabular-nums; margin: 10px 0 4px;
  white-space: nowrap; }
.kpi .detail { color: var(--muted); font-size: 13px; }
.kpi .delta { position: absolute; top: 13px; right: 14px; font: 500 12px var(--mono); color: var(--muted);
  background: var(--card-2); border-radius: 6px; padding: 2px 6px; }
.two { grid-template-columns: minmax(0, 2fr) minmax(0, 1fr); margin-top: 14px; }
.three { grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); margin-top: 14px; }
.full { margin-top: 14px; }
@media (max-width: 820px) { .two { grid-template-columns: minmax(0, 1fr); } }

.legend { display: flex; gap: 16px; flex-wrap: wrap; color: var(--muted); font-size: 13px; }
.legend i { display: inline-block; width: 10px; height: 10px; border-radius: 3px; margin-right: 6px;
  vertical-align: -1px; }
.chart { width: 100%; }
.chart svg { display: block; overflow: visible; }
.scroll-x { overflow-x: auto; }
svg text { fill: var(--muted); font: 11px var(--mono); }
.hit { fill: transparent; cursor: default; }
.hit:hover, .hit.on { fill: var(--hover); }
.cell { cursor: pointer; }
.cell:hover { stroke: var(--ink); stroke-width: 1.5; }
.cell.sel { stroke: var(--accent); stroke-width: 2; }
.scale { display: flex; align-items: center; gap: 4px; color: var(--muted); font-size: 12px; margin-top: 10px; }
.scale i { width: 11px; height: 11px; border-radius: 3px; display: inline-block; }

/* ranked lists */
.rank { list-style: none; margin: 0; padding: 0; display: grid; gap: 12px; }
.rank li { display: grid; gap: 5px; }
.rank .row { display: flex; justify-content: space-between; gap: 10px; font-size: 14px; }
.rank .name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-weight: 550; }
.rank .val { color: var(--muted); font: 12.5px var(--mono); white-space: nowrap; }
.rank .bar { height: 6px; background: var(--card-2); border-radius: 4px; overflow: hidden; }
.rank .bar span { display: block; height: 100%; background: var(--s1); border-radius: 4px; }
.empty-note { color: var(--muted); font-size: 14px; }

/* highlights */
.facts { margin: 0; display: grid; gap: 12px; }
.facts div { display: flex; justify-content: space-between; gap: 12px; border-bottom: 1px solid var(--grid);
  padding-bottom: 10px; }
.facts div:last-child { border-bottom: 0; padding-bottom: 0; }
.facts dt { color: var(--muted); font-size: 14px; }
.facts dd { margin: 0; font: 500 13.5px var(--mono); text-align: right; }

/* table */
details { margin-top: 14px; }
summary { cursor: pointer; font-weight: 600; font-size: 15px; }
table { width: 100%; border-collapse: collapse; margin-top: 14px; font-size: 13.5px; }
th, td { text-align: right; padding: 7px 10px; border-bottom: 1px solid var(--grid); white-space: nowrap; }
th:first-child, td:first-child { text-align: left; }
th { color: var(--muted); font: 600 11px var(--mono); letter-spacing: .08em; text-transform: uppercase; }
td { font-family: var(--mono); font-variant-numeric: tabular-nums; }

.hero-empty { text-align: center; padding: 60px 20px; }
.hero-empty p { color: var(--muted); max-width: 46ch; margin: 10px auto 0; }
code { font-family: var(--mono); font-size: .92em; background: var(--card-2); padding: 1px 6px; border-radius: 5px; }
footer { color: var(--muted); font-size: 13px; margin-top: 28px; display: flex; gap: 8px 18px; flex-wrap: wrap; }

#tip { position: fixed; z-index: 10; pointer-events: none; background: var(--ink); color: var(--bg);
  font: 12.5px/1.45 var(--body); padding: 8px 10px; border-radius: 8px; max-width: 260px;
  box-shadow: 0 8px 24px -8px rgba(0,0,0,.4); opacity: 0; transform: translateY(4px);
  transition: opacity .08s, transform .08s; }
#tip.on { opacity: 1; transform: none; }
#tip b { font-weight: 650; }
#tip .k { opacity: .7; }
</style>
</head>
<body>
<main>
  <header>
    <div class="term" aria-hidden="true"><pre>__SPRITE__</pre></div>
    <div class="titles">
      <div class="eyebrow">maggy stats</div>
      <h1>__NAME__'s stats</h1>
      <div class="sub" id="sub"></div>
    </div>
    <button class="icon-btn" id="theme" type="button" title="Switch light/dark">◐ <span>auto</span></button>
  </header>

  <div id="app"></div>

  <footer>
    <span>Data: <code id="path"></code></span>
    <span>Refresh: <code>maggy stats web</code></span>
    <span>Nothing here leaves your machine.</span>
  </footer>
</main>
<div id="tip" role="tooltip"></div>

<script type="application/json" id="maggy-data">__DATA__</script>
<script>
(() => {
  "use strict";
  const D = JSON.parse(document.getElementById("maggy-data").textContent);
  const $ = (s, el = document) => el.querySelector(s);
  const pad = (n) => String(n).padStart(2, "0");
  const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const WD = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  const parse = (s) => { const [y, m, d] = s.split("-").map(Number); return new Date(y, m - 1, d); };
  const iso = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  const addDays = (s, n) => { const d = parse(s); d.setDate(d.getDate() + n); return iso(d); };
  const wdIdx = (s) => (parse(s).getDay() + 6) % 7;
  const fmtDay = (s, year) => { const d = parse(s); return `${MON[d.getMonth()]} ${d.getDate()}` + (year ? `, ${d.getFullYear()}` : ""); };
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const pct = (x) => (isFinite(x) ? Math.round(x * 100) : 0) + "%";
  const plural = (n, w) => `${n.toLocaleString()} ${w}${n === 1 ? "" : "s"}`;
  function dur(sec) {
    sec = Math.round(sec || 0);
    if (sec < 60) return sec + "s";
    const m = Math.floor(sec / 60), h = Math.floor(m / 60);
    return h ? `${h}h ${pad(m % 60)}m` : `${m}m ${pad(sec % 60)}s`;
  }
  const obj = (x) => (x && typeof x === "object" && !Array.isArray(x) ? x : {});
  const store = {
    get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* private mode */ } },
  };

  const DAYS = obj(D.days);
  const TODAY = D.today;
  const KEYS = Object.keys(DAYS).sort();
  const FIRST = KEYS[0] && KEYS[0] < TODAY ? KEYS[0] : TODAY;
  $("#path").textContent = D.path;

  function day(k) {
    const v = obj(DAYS[k]);
    const h = Array.isArray(v.h) && v.h.length === 24 ? v.h.map((x) => +x || 0) : new Array(24).fill(0);
    return { t: +v.t || 0, e: +v.e || 0, b: +v.b || 0, tl: +v.tl || 0, w: +v.w || 0, lg: +v.lg || 0,
             h, m: obj(v.m), p: obj(v.p), cx: +v.cx || 0, q: obj(v.q) };
  }
  function spanKeys(from, to) { const out = []; for (let k = from; k <= to; k = addDays(k, 1)) out.push(k); return out; }
  function merge(src, dst) {
    for (const [n, r] of Object.entries(src)) {
      if (!Array.isArray(r) || r.length !== 2) continue;
      const c = dst[n] || [0, 0];
      dst[n] = [c[0] + (+r[0] || 0), c[1] + (+r[1] || 0)];
    }
  }
  function summarize(keys) {
    const s = { tasks: 0, errors: 0, busy: 0, tool: 0, wait: 0, longest: 0, longestDay: null, ctx: 0, active: 0,
                hours: new Array(24).fill(0), wh: Array.from({ length: 7 }, () => new Array(24).fill(0)),
                models: {}, projects: {}, quota: {}, perDay: [] };
    for (const k of keys) {
      const d = day(k);
      s.tasks += d.t; s.errors += d.e; s.busy += d.b; s.tool += Math.min(d.tl, d.b); s.wait += d.w;
      if (d.lg > s.longest) { s.longest = d.lg; s.longestDay = k; }
      s.ctx = Math.max(s.ctx, d.cx);
      if (d.t > 0) s.active++;
      const wd = wdIdx(k);
      d.h.forEach((v, i) => { s.hours[i] += v; s.wh[wd][i] += v; });
      merge(d.m, s.models); merge(d.p, s.projects);
      for (const [q, v] of Object.entries(d.q)) s.quota[q] = (s.quota[q] || 0) + (+v || 0);
      s.perDay.push({ date: k, ...d });
    }
    return s;
  }
  function streaks() {
    const active = new Set(KEYS.filter((k) => day(k).t > 0));
    let cur = 0;
    let k = active.has(TODAY) ? TODAY : addDays(TODAY, -1);
    while (active.has(k)) { cur++; k = addDays(k, -1); }
    let best = 0, run = 0, prev = null;
    for (const a of [...active].sort()) {
      run = prev && addDays(prev, 1) === a ? run + 1 : 1;
      best = Math.max(best, run); prev = a;
    }
    return { cur, best: Math.max(best, cur) };
  }

  // ------------------------------------------------------------ state
  const RANGES = [["1", "Today"], ["7", "7 days"], ["30", "30 days"], ["90", "90 days"], ["365", "Year"], ["all", "All time"]];
  const state = { range: RANGES.some((r) => r[0] === store.get("maggy.range")) ? store.get("maggy.range") : "7", day: null };
  function currentSpan() {
    if (state.day) return [state.day, state.day];
    if (state.range === "all") return [FIRST, TODAY];
    return [addDays(TODAY, -(+state.range - 1)), TODAY];
  }

  // ------------------------------------------------------------ tooltip
  const tip = $("#tip");
  function showTip(html, ev) {
    tip.innerHTML = html;
    tip.classList.add("on");
    const r = tip.getBoundingClientRect();
    let x = ev.clientX + 14, y = ev.clientY + 14;
    if (x + r.width > innerWidth - 8) x = ev.clientX - r.width - 14;
    if (y + r.height > innerHeight - 8) y = ev.clientY - r.height - 14;
    tip.style.left = Math.max(8, x) + "px";
    tip.style.top = Math.max(8, y) + "px";
  }
  function hideTip() { tip.classList.remove("on"); }
  function bindTips(root, tipFor, onClick) {
    root.addEventListener("mousemove", (ev) => {
      const t = ev.target.closest("[data-i]");
      root.querySelectorAll(".hit.on").forEach((n) => n !== t && n.classList.remove("on"));
      if (!t) return hideTip();
      if (t.classList.contains("hit")) t.classList.add("on");
      showTip(tipFor(t.dataset.i), ev);
    });
    root.addEventListener("mouseleave", () => { hideTip(); root.querySelectorAll(".hit.on").forEach((n) => n.classList.remove("on")); });
    root.addEventListener("click", (ev) => {
      const t = ev.target.closest("[data-i]");
      if (!t) return;
      if (onClick) { hideTip(); onClick(t.dataset.i); } else showTip(tipFor(t.dataset.i), ev);
    });
  }

  // ------------------------------------------------------------ svg helpers
  const NS = "http://www.w3.org/2000/svg";
  function svg(w, h, label) {
    const s = document.createElementNS(NS, "svg");
    s.setAttribute("width", w); s.setAttribute("height", h); s.setAttribute("viewBox", `0 0 ${w} ${h}`);
    s.setAttribute("role", "img"); s.setAttribute("aria-label", label);
    return s;
  }
  function el(parent, tag, attrs, text) {
    const n = document.createElementNS(NS, tag);
    for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
    if (text != null) n.textContent = text;
    parent.appendChild(n);
    return n;
  }
  function topRounded(x, y, w, h, r) {
    r = Math.max(0, Math.min(r, w / 2, h));
    return `M${x},${y + h}V${y + r}A${r},${r} 0 0 1 ${x + r},${y}H${x + w - r}A${r},${r} 0 0 1 ${x + w},${y + r}V${y + h}Z`;
  }
  function niceMax(max) {
    const steps = [60, 300, 600, 900, 1800, 3600, 7200, 10800, 14400, 21600, 43200, 86400, 172800, 432000, 864000];
    for (const st of steps) if (max <= st * 4) return { step: st, top: Math.max(st, Math.ceil(max / st) * st) };
    const st = steps[steps.length - 1];
    return { step: st, top: Math.ceil(max / st) * st };
  }
  const axisDur = (s) => (s === 0 ? "0" : s < 3600 ? `${s / 60}m` : `${+(s / 3600).toFixed(1)}h`);
  function levels(values) {
    const nz = values.filter((v) => v > 0).sort((a, b) => a - b);
    const q = (p) => nz[Math.min(nz.length - 1, Math.floor(p * nz.length))];
    const t = nz.length ? [q(.25), q(.5), q(.75)] : [0, 0, 0];
    return (v) => (v <= 0 ? 0 : v <= t[0] ? 1 : v <= t[1] ? 2 : v <= t[2] ? 3 : 4);
  }

  // ------------------------------------------------------------ sections
  function kpiCard(label, value, detail, delta) {
    return `<div class="card kpi"><div class="label">${label}</div>` +
      (delta ? `<span class="delta" title="vs the previous period">${delta}</span>` : "") +
      `<div class="value">${value}</div><div class="detail">${detail}</div></div>`;
  }
  function delta(cur, prev) {
    if (prev == null) return "";
    if (prev <= 0) return cur > 0 ? "new" : "";
    const d = (cur - prev) / prev;
    if (Math.abs(d) < 0.005) return "± 0%";
    return `${d > 0 ? "▲" : "▼"} ${Math.round(Math.abs(d) * 100)}%`;
  }

  function renderActivity(host, keys, s) {
    host.innerHTML = "";
    const W = Math.max(280, host.clientWidth), H = 230, m = { l: 42, r: 4, t: 10, b: 24 };
    let cols, stacked = true;
    if (keys.length === 1) {
      stacked = false;
      cols = s.hours.map((v, i) => ({ a: v, b: 0, tick: i % 3 === 0 ? String(i) : "",
        tip: `<b>${pad(i)}:00–${pad((i + 1) % 24)}:00</b><br>${dur(v)} busy` }));
    } else {
      let groups = s.perDay.map((d) => ({ from: d.date, to: d.date, days: [d] }));
      if (keys.length > 120) {
        const byWeek = new Map();
        for (const d of s.perDay) {
          const wk = addDays(d.date, -wdIdx(d.date));
          if (!byWeek.has(wk)) byWeek.set(wk, { from: d.date, to: d.date, days: [] });
          const g = byWeek.get(wk); g.to = d.date; g.days.push(d);
        }
        groups = [...byWeek.values()];
      }
      const every = Math.ceil(groups.length / Math.max(3, Math.floor(W / 90)));
      cols = groups.map((g, i) => {
        const b = g.days.reduce((a, d) => a + d.b, 0);
        const tl = g.days.reduce((a, d) => a + Math.min(d.tl, d.b), 0);
        const t = g.days.reduce((a, d) => a + d.t, 0);
        const e = g.days.reduce((a, d) => a + d.e, 0);
        const label = g.from === g.to ? fmtDay(g.from) : `${fmtDay(g.from)} – ${fmtDay(g.to)}`;
        return { a: b - tl, b: tl, tick: i % every === 0 ? fmtDay(g.from) : "",
          tip: `<b>${label}</b><br>${dur(b)} busy · ${plural(t, "task")}${e ? ` · ${plural(e, "error")}` : ""}` +
               `<br><span class="k">working</span> ${dur(b - tl)} · <span class="k">tools</span> ${dur(tl)}` };
      });
    }
    const max = Math.max(0, ...cols.map((c) => c.a + c.b));
    const { step, top } = niceMax(max || 3600);
    const pw = W - m.l - m.r, ph = H - m.t - m.b;
    const y = (v) => m.t + ph - (v / top) * ph;
    const band = pw / cols.length;
    const bw = Math.max(1, Math.min(28, band * 0.68));
    const s0 = svg(W, H, stacked ? "Busy time per day, split into working and tool use" : "Busy time by hour of day");
    for (let v = 0; v <= top + 1e-6; v += step) {
      el(s0, "line", { x1: m.l, x2: W - m.r, y1: y(v), y2: y(v), stroke: "var(--grid)", "stroke-width": 1 });
      el(s0, "text", { x: m.l - 8, y: y(v) + 4, "text-anchor": "end" }, axisDur(v));
    }
    cols.forEach((c, i) => {
      const cx = m.l + band * i + band / 2, x = cx - bw / 2;
      const ha = (c.a / top) * ph, hb = (c.b / top) * ph;
      const gapPx = ha > 0 && hb > 0 ? Math.min(2, hb / 2) : 0;
      const r = Math.min(4, bw / 2);
      if (ha > 0) {
        const roundA = hb <= 0;
        el(s0, "path", { d: roundA ? topRounded(x, y(c.a), bw, ha, r) : `M${x},${y(0)}V${y(c.a)}H${x + bw}V${y(0)}Z`, fill: "var(--s1)" });
      }
      if (hb > 0) {
        el(s0, "path", { d: topRounded(x, y(c.a + c.b), bw, Math.max(0.5, hb - gapPx), r), fill: "var(--s2)" });
      }
      if (c.tick) el(s0, "text", { x: cx, y: H - 6, "text-anchor": "middle" }, c.tick);
      el(s0, "rect", { class: "hit", x: m.l + band * i, y: m.t, width: band, height: ph, "data-i": i, rx: 4 });
    });
    el(s0, "line", { x1: m.l, x2: W - m.r, y1: y(0), y2: y(0), stroke: "var(--line)", "stroke-width": 1 });
    host.appendChild(s0);
    bindTips(s0, (i) => cols[i].tip);
    return stacked;
  }

  function renderHeatmap(host, onPick) {
    host.innerHTML = "";
    const weeks = 53, labelW = 30, gap = 3;
    const start = addDays(TODAY, -(52 * 7 + wdIdx(TODAY)));
    const cell = Math.max(8, Math.min(18, Math.floor((host.clientWidth - labelW) / weeks) - gap));
    const W = labelW + weeks * (cell + gap), H = 18 + 7 * (cell + gap);
    const s0 = svg(W, H, "Busy time per day over the last year");
    const keys = spanKeys(start, TODAY);
    const lv = levels(keys.map((k) => day(k).b));
    let lastMonth = -1;
    let active = 0;
    keys.forEach((k, idx) => {
      const w = Math.floor(idx / 7), wd = idx % 7;
      const d = day(k);
      if (d.t > 0) active++;
      const x = labelW + w * (cell + gap), yy = 18 + wd * (cell + gap);
      const mo = parse(k).getMonth();
      if (wd === 0 && mo !== lastMonth) {
        // skip a label squeezed against the edges (the first partial month, the last week)
        if (w > 0 ? w < weeks - 2 : parse(addDays(k, 14)).getMonth() === mo) el(s0, "text", { x, y: 10 }, MON[mo]);
        lastMonth = mo;
      }
      el(s0, "rect", { class: "cell" + (state.day === k ? " sel" : ""), x, y: yy, width: cell, height: cell, rx: 2.5,
                       fill: `var(--h${lv(d.b)})`, "data-i": k });
    });
    [[0, "Mon"], [2, "Wed"], [4, "Fri"]].forEach(([r, t]) =>
      el(s0, "text", { x: 0, y: 18 + r * (cell + gap) + cell - 2 }, t));
    host.appendChild(s0);
    host.scrollLeft = host.scrollWidth;  // narrow screens: start at the recent weeks
    bindTips(s0, (k) => {
      const d = day(k);
      return `<b>${fmtDay(k, true)}</b> · ${WD[wdIdx(k)]}<br>` +
        (d.t || d.b ? `${plural(d.t, "task")} · ${dur(d.b)} busy` : "no tasks") + `<br><span class="k">click to open this day</span>`;
    }, onPick);
    return active;
  }

  function renderRhythm(host, s) {
    host.innerHTML = "";
    const labelW = 34, gap = 2;
    const cw = Math.max(8, (host.clientWidth - labelW) / 24 - gap), ch = Math.round(Math.min(34, Math.max(18, cw)));
    const W = labelW + 24 * (cw + gap), H = 7 * (ch + gap) + 18;
    const s0 = svg(W, H, "Busy time by weekday and hour");
    const lv = levels(s.wh.flat());
    s.wh.forEach((row, r) => {
      el(s0, "text", { x: 0, y: r * (ch + gap) + ch / 2 + 4 }, WD[r]);
      row.forEach((v, c) => {
        el(s0, "rect", { x: labelW + c * (cw + gap), y: r * (ch + gap), width: cw, height: ch, rx: 3,
                         fill: `var(--h${lv(v)})`, "data-i": `${r},${c}` });
      });
    });
    [0, 6, 12, 18, 23].forEach((h) => el(s0, "text", { x: labelW + h * (cw + gap) + cw / 2, y: H - 3, "text-anchor": "middle" }, pad(h)));
    host.appendChild(s0);
    bindTips(s0, (i) => {
      const [r, c] = i.split(",").map(Number);
      return `<b>${WD[r]} ${pad(c)}:00–${pad((c + 1) % 24)}:00</b><br>${dur(s.wh[r][c])} busy`;
    });
  }

  function rankList(rows, empty) {
    if (!rows.length) return `<p class="empty-note">${empty}</p>`;
    const max = Math.max(...rows.map((r) => r.v)) || 1;
    return `<ul class="rank">` + rows.map((r) =>
      `<li><div class="row"><span class="name" title="${esc(r.name)}">${esc(r.name)}</span><span class="val">${r.label}</span></div>` +
      `<div class="bar"><span style="width:${Math.max(2, (r.v / max) * 100)}%"></span></div></li>`).join("") + `</ul>`;
  }
  function tableRows(name, total) {
    return Object.entries(name).sort((a, b) => b[1][1] - a[1][1]).slice(0, 6)
      .map(([n, [t, b]]) => ({ name: n, v: b, label: `${plural(t, "task")} · ${dur(b)}${total ? ` · ${pct(b / total)}` : ""}` }));
  }

  // ------------------------------------------------------------ main render
  const app = $("#app");
  function render() {
    hideTip();
    const [from, to] = currentSpan();
    const keys = spanKeys(from, to);
    const s = summarize(keys);
    const n = keys.length;
    const prev = state.range === "all" ? null : summarize(spanKeys(addDays(from, -n), addDays(from, -1)));
    const st = streaks();
    const multiYear = from.slice(0, 4) !== to.slice(0, 4);
    $("#sub").textContent = (n === 1 ? fmtDay(from, true) : `${fmtDay(from, multiYear)} – ${fmtDay(to, true)}`) +
      ` · generated ${D.generated}`;

    if (!KEYS.length) {
      app.innerHTML = `<div class="card hero-empty"><h2>Nothing counted yet</h2>
        <p>${esc(D.name)} counts a task every time agy finishes a turn. Use agy for a bit, then run <code>maggy stats web</code> again.</p></div>`;
      return;
    }
    const avg = s.tasks ? s.busy / s.tasks : 0;
    const pavg = prev && prev.tasks ? prev.busy / prev.tasks : prev ? 0 : null;
    const vs = n === 1 ? "the day before" : `the previous ${n} days`;

    app.innerHTML = `
      <div class="rangebar">
        <div class="seg" role="group" aria-label="Date range">${RANGES.map(([k, l]) =>
          `<button type="button" data-range="${k}" aria-pressed="${!state.day && state.range === k}">${l}</button>`).join("")}</div>
        <span class="chip ${state.day ? "on" : ""}">${state.day ? fmtDay(state.day, true) : ""}<button type="button" id="clear-day" aria-label="Back to the range">×</button></span>
      </div>
      <div class="grid kpis">
        ${kpiCard("Tasks", s.tasks.toLocaleString(), s.errors ? `${plural(s.errors, "error")} · ${pct(s.errors / s.tasks)}` : "no errors", delta(s.tasks, prev && prev.tasks))}
        ${kpiCard("Busy time", dur(s.busy), s.busy ? `tool use ${pct(s.tool / s.busy)}` : "–", delta(s.busy, prev && prev.busy))}
        ${kpiCard("Avg task", s.tasks ? dur(avg) : "–", s.longest ? `longest ${dur(s.longest)}` : "–", s.tasks ? delta(avg, pavg) : "")}
        ${kpiCard("Waited on you", dur(s.wait), s.busy + s.wait ? `${pct(s.wait / (s.busy + s.wait))} of turn time` : "–", "")}
        ${kpiCard("Streak", plural(st.cur, "day"), `best ${plural(st.best, "day")}`, "")}
        ${kpiCard("Peak context", s.ctx ? s.ctx + "%" : "–", `active ${s.active} of ${plural(n, "day")}`, "")}
      </div>
      <section class="card full">
        <div class="card-head"><h2>${n === 1 ? "Busy time by hour" : n > 120 ? "Busy time per week" : "Busy time per day"}</h2>
          <div class="legend" id="act-legend"></div></div>
        <div class="chart" id="activity"></div>
      </section>
      <section class="card full">
        <div class="card-head"><h2>Last 12 months</h2><span class="meta" id="heat-meta"></span></div>
        <div class="chart scroll-x" id="heatmap"></div>
        <div class="scale">less <i style="background:var(--h0)"></i><i style="background:var(--h1)"></i><i style="background:var(--h2)"></i><i style="background:var(--h3)"></i><i style="background:var(--h4)"></i> more</div>
      </section>
      <div class="grid two">
        <section class="card">
          <div class="card-head"><h2>Rhythm</h2><span class="meta">when agy works, by weekday and hour</span></div>
          <div class="chart" id="rhythm"></div>
        </section>
        <section class="card">
          <div class="card-head"><h2>Highlights</h2></div>
          <dl class="facts" id="facts"></dl>
        </section>
      </div>
      <div class="grid three">
        <section class="card"><div class="card-head"><h2>Models</h2></div>${rankList(tableRows(s.models, s.busy), "No model info yet.")}</section>
        <section class="card"><div class="card-head"><h2>Projects</h2></div>${rankList(tableRows(s.projects, s.busy), "No projects yet.")}</section>
        <section class="card"><div class="card-head"><h2>Quota burned</h2><span class="meta">100% = one full window</span></div>
          ${rankList(Object.entries(s.quota).sort((a, b) => b[1] - a[1]).map(([k, v]) => ({ name: k, v, label: `${Math.round(v)}%` })), "No quota data in this range.")}</section>
      </div>
      <details class="card">
        <summary>Daily table</summary>
        <div class="scroll-x"><table>
          <thead><tr><th>Day</th><th>Tasks</th><th>Errors</th><th>Busy</th><th>Tools</th><th>Waited</th><th>Longest</th><th>Peak ctx</th></tr></thead>
          <tbody>${s.perDay.filter((d) => d.t || d.b).reverse().map((d) =>
            `<tr><td>${WD[wdIdx(d.date)]} ${fmtDay(d.date, true)}</td><td>${d.t}</td><td>${d.e}</td><td>${dur(d.b)}</td>` +
            `<td>${dur(Math.min(d.tl, d.b))}</td><td>${dur(d.w)}</td><td>${dur(d.lg)}</td><td>${d.cx ? d.cx + "%" : "–"}</td></tr>`).join("") ||
            `<tr><td colspan="8">No tasks in this range.</td></tr>`}</tbody>
        </table></div>
      </details>`;

    // delta badges explain themselves on hover
    app.querySelectorAll(".delta").forEach((b) => (b.title = `vs ${vs}`));
    app.querySelectorAll("[data-range]").forEach((b) => b.addEventListener("click", () => {
      state.range = b.dataset.range; state.day = null; store.set("maggy.range", state.range); render();
    }));
    $("#clear-day").addEventListener("click", () => { state.day = null; render(); });

    drawCharts(keys, s);

    // highlights
    const all = summarize(spanKeys(FIRST, TODAY));
    const best = all.perDay.reduce((a, d) => (d.b > (a ? a.b : 0) ? d : a), null);
    const facts = [];
    if (s.busy) {
      const hr = s.hours.indexOf(Math.max(...s.hours));
      const wdTot = s.wh.map((r) => r.reduce((a, v) => a + v, 0));
      facts.push(["Busiest hour", `${pad(hr)}:00–${pad((hr + 1) % 24)}:00`]);
      if (n >= 7) facts.push(["Busiest weekday", WD[wdTot.indexOf(Math.max(...wdTot))]]);
      const night = s.hours.slice(0, 6).reduce((a, v) => a + v, 0) / s.busy;
      facts.push(["Night owl (00–06)", pct(night)]);
    }
    const topModel = Object.entries(s.models).sort((a, b) => b[1][1] - a[1][1])[0];
    if (topModel) facts.push(["Top model", esc(topModel[0])]);
    if (best) facts.push(["Best day ever", `${fmtDay(best.date, true)} · ${dur(best.b)}`]);
    facts.push(["All time", `${plural(all.tasks, "task")} · ${dur(all.busy)}`]);
    facts.push(["Counting since", fmtDay(FIRST, true)]);
    $("#facts").innerHTML = facts.map(([k, v]) => `<div><dt>${k}</dt><dd>${v}</dd></div>`).join("");
  }

  let last = null;
  function drawCharts(keys, s) {
    last = [keys, s];
    const stacked = renderActivity($("#activity"), keys, s);
    $("#act-legend").innerHTML = stacked
      ? `<span><i style="background:var(--s1)"></i>working</span><span><i style="background:var(--s2)"></i>tool use</span>`
      : "";
    const active = renderHeatmap($("#heatmap"), (k) => { state.day = k; render(); window.scrollTo({ top: 0, behavior: "smooth" }); });
    $("#heat-meta").textContent = `${plural(active, "active day")} · click a day to open it`;
    renderRhythm($("#rhythm"), s);
  }

  let raf = 0, lastW = 0;
  new ResizeObserver((entries) => {
    const w = Math.round(entries[0].contentRect.width);
    if (w === lastW) return;  // charts depend on width only
    lastW = w;
    cancelAnimationFrame(raf);
    raf = requestAnimationFrame(() => last && drawCharts(...last));
  }).observe(app);

  // ------------------------------------------------------------ theme toggle
  const modes = ["auto", "light", "dark"];
  let mode = modes.includes(store.get("maggy.theme")) ? store.get("maggy.theme") : "auto";
  function applyMode() {
    if (mode === "auto") document.documentElement.removeAttribute("data-theme");
    else document.documentElement.setAttribute("data-theme", mode);
    $("#theme span").textContent = mode;
  }
  $("#theme").addEventListener("click", () => {
    mode = modes[(modes.indexOf(mode) + 1) % modes.length];
    store.set("maggy.theme", mode);
    applyMode();
  });
  applyMode();
  render();
})();
</script>
</body>
</html>
"""
