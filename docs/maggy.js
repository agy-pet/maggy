// Maggy renderer: a port of mascot.py / statusline.py so the page shows
// exactly what the terminal shows. Keep in sync with mascot.py.
(() => {
  "use strict";

  const LOGO_COLORS = {
    a: [242, 146, 46], b: [240, 114, 54],
    c: [158, 195, 69], d: [226, 153, 61], e: [246, 122, 52], f: [239, 84, 66],
    g: [124, 194, 81], h: [92, 169, 143], i: [116, 111, 195], j: [153, 93, 168],
    k: [97, 195, 125], l: [74, 128, 234],
    m: [103, 185, 244], n: [100, 182, 246], o: [56, 131, 249], p: [61, 133, 252],
  };
  const SPARKLE_COLOR = [253, 224, 71];
  const EYE_COLOR = [255, 255, 255];
  const ERROR_TINT = [239, 68, 68];
  const POSE_WIDTH = 12, SPRITE_WIDTH = 14, SPRITE_HEIGHT = 5;
  const EYE_COLS = [4, 7];

  const BASE = ["    aabb    ", "  ccddeeff  ", "  gghhiijj  ", "  kk    ll  ", "mmnn    oopp"];
  const SQUAT = ["            ", "    aabb    ", "  ccddeeff  ", "  gghhiijj  ", "mmnn    oopp"];
  const TIPTOE = ["    aabb    ", "  ccddeeff  ", "  gghhiijj  ", "  kk    ll  ", "  mn    op  "];
  const KICK_LEFT = ["    aabb    ", "  ccddeeff  ", "  gghhiijj  ", "mnkk    ll  ", "        oopp"];
  const KICK_RIGHT = ["    aabb    ", "  ccddeeff  ", "  gghhiijj  ", "  kk    llop", "mmnn        "];

  const SPARKLES_L = [[0, 1, "✦"], [0, 12, "·"]];
  const SPARKLES_R = [[0, 1, "·"], [0, 12, "✦"]];

  // [pose, x offset, sparkles, brightness, eyes]
  const FRAMES = {
    working: [
      [BASE, 1, [], 1, "◕◕"], [SQUAT, 1, [], 1, "◠◠"], [TIPTOE, 1, SPARKLES_L, 1.08, "◕◕"],
      [KICK_LEFT, 0, [], 1, "─◕"], [BASE, 1, [], 1, "◕◕"], [SQUAT, 1, [], 1, "◠◠"],
      [TIPTOE, 1, SPARKLES_R, 1.08, "◕◕"], [KICK_RIGHT, 2, [], 1, "◕─"],
    ],
    tool_use: [
      [KICK_LEFT, 0, [], 1, "◕◕"], [SQUAT, 1, [], 1, "◡◡"],
      [KICK_RIGHT, 2, [], 1, "◕◕"], [SQUAT, 1, [], 1, "◡◡"],
    ],
    initializing: [
      [BASE, 1, [], 1, "◐◐"], [BASE, 1, [], 1, "◓◓"], [BASE, 1, [], 1, "◑◑"], [BASE, 1, [], 1, "◒◒"],
    ],
    reviewing: [
      [BASE, 0, [], 1, "◔◔"], [BASE, 1, [], 1, "◕◕"], [BASE, 2, [], 1, "◔◔"], [BASE, 1, [], 1, "◕◕"],
    ],
    error: [[KICK_LEFT, 0, [], 1, "××"], [KICK_RIGHT, 2, [], 1, "××"]],
    done: [[TIPTOE, 1, [[0, 1, "✦"], [0, 12, "✦"]], 1.08, "◠◠"]],
    sleep: [
      [SQUAT, 1, [[0, 11, "z"]], 0.8, "──"],
      [SQUAT, 1, [[0, 11, "z"], [0, 12, "Z"]], 0.8, "──"],
    ],
  };
  const IDLE_FIDGETS = [
    [BASE, 1, [], 1, "◕◕"], [BASE, 0, [], 1, "◔◔"], [BASE, 2, [], 1, "◔◔"],
    [BASE, 1, [], 1, "◕─"], [BASE, 1, [], 1, "──"], [SQUAT, 1, [], 1, "◡◡"],
    [TIPTOE, 1, [], 1, "◠◠"], [KICK_LEFT, 0, [], 1, "◕◕"], [BASE, 1, [[0, 12, "✦"]], 1, "◠◠"],
  ];
  const IDLE_TWINKLES = [[0, 2, "·"], [2, 13, "✦"], [4, 0, "·"]];
  const IDLE_MOODS = new Set(["idle", "done", "sleep"]);

  const MOODS = {
    working: "{name} is dancing ♪",
    tool_use: "{name} is stomping around",
    initializing: "{name} is waking up…",
    reviewing: "{name} is peeking",
    error: "{name} feels dizzy",
    done: "{name}: done! ✦",
    idle: "{name} is chilling",
    sleep: "{name} is sleepy z",
  };

  const TREE = ["  *  ", "  G  ", " GoG ", "oGGGo", "  T  "];
  const TREE_GREEN = [22, 128, 61], TREE_TRUNK = [120, 72, 36], TREE_STAR = [255, 214, 64];

  const THEMES = {
    default: {},
    xmas: {
      colors: { a: [220, 38, 38], b: [185, 28, 28] },
      sparkles: { "✦": "❄", "·": "*" },
      sparkle_color: [226, 240, 255],
      pompom: "●", pompom_color: [255, 255, 255],
      snowfall: [[0, 0, "*"], [1, 3, "·"], [2, 1, "·"], [11, 4, "·"], [12, 2, "*"], [13, 0, "·"], [10, 3, "*"]],
      lights: [2, 4, 7, 9], light_glyph: "•",
      light_colors: [[255, 59, 59], [255, 214, 64], [255, 255, 255], [96, 200, 255]],
      tree: TREE,
    },
  };

  const rgb = (c) => `rgb(${c[0]},${c[1]},${c[2]})`;
  const adjust = (c, b, tint) => c.map((v, i) => {
    const t = tint ? v + (tint[i] - v) * 0.6 : v;
    return Math.max(0, Math.min(255, Math.round(t * b)));
  });

  function pickFrame(mood, frame, fidget) {
    if (mood === "idle") return IDLE_FIDGETS[fidget % IDLE_FIDGETS.length];
    const list = FRAMES[mood] || FRAMES.working;
    return list[frame % list.length];
  }

  // Returns SPRITE_HEIGHT rows of cells: {ch, bg, fg, blink}.
  function renderSprite(mood, frame, opts = {}) {
    const th = THEMES[opts.theme] || THEMES.default;
    const colors = Object.assign({}, LOGO_COLORS, th.colors || {});
    const glyphMap = th.sparkles || {};
    const sparkleColor = th.sparkle_color || SPARKLE_COLOR;
    const tint = mood === "error" ? ERROR_TINT : null;
    const [pose, offset, sparkles, brightness, eyes] = pickFrame(mood, frame, opts.fidget || 0);
    const blink = IDLE_MOODS.has(mood) && opts.blink !== false;

    const sparkleAt = new Map();
    const key = (r, c) => r * 100 + c;
    for (const [c, phase, g] of th.snowfall || []) sparkleAt.set(key((frame + phase) % SPRITE_HEIGHT, c), [g, sparkleColor, blink]);
    if (blink) for (const [r, c, g] of IDLE_TWINKLES) sparkleAt.set(key(r, c), [glyphMap[g] || g, sparkleColor, true]);
    for (const [r, c, g] of sparkles) sparkleAt.set(key(r, c), [glyphMap[g] || g, sparkleColor, blink]);
    if (th.pompom) {
      const crown = pose.findIndex((row) => row.trim());
      sparkleAt.set(key(crown, 8 + offset), [th.pompom, th.pompom_color, false]);
    }
    const eyeAt = new Map();
    const head = pose.findIndex((row) => row[EYE_COLS[0] - 2] !== " ");
    if (eyes) [...eyes].forEach((g, i) => eyeAt.set(key(head, EYE_COLS[i] + offset), [g, EYE_COLOR, false]));
    if (th.light_colors && head + 1 < pose.length) {
      th.lights.forEach((col, i) => {
        const color = th.light_colors[(i + frame) % th.light_colors.length];
        eyeAt.set(key(head + 1, col + offset), [th.light_glyph, color, blink && i % 2 === 0]);
      });
    }

    const rows = [];
    for (let r = 0; r < pose.length; r++) {
      const cells = " ".repeat(offset) + pose[r] + " ".repeat(SPRITE_WIDTH - offset - POSE_WIDTH);
      const out = [];
      for (let c = 0; c < SPRITE_WIDTH; c++) {
        const k = cells[c];
        if (colors[k]) {
          const cell = { ch: " ", bg: rgb(adjust(colors[k], brightness, tint)) };
          const e = eyeAt.get(key(r, c));
          if (e) Object.assign(cell, { ch: e[0], fg: rgb(e[1]), blink: e[2] });
          out.push(cell);
        } else if (sparkleAt.has(key(r, c))) {
          const [g, col, b] = sparkleAt.get(key(r, c));
          out.push({ ch: g, fg: rgb(col), blink: b });
        } else {
          out.push({ ch: " " });
        }
      }
      if (th.tree) {
        out.push({ ch: " " });
        const lights = th.light_colors || [TREE_STAR];
        [...th.tree[r]].forEach((t, col) => {
          if (t === "G") out.push({ ch: " ", bg: rgb(TREE_GREEN) });
          else if (t === "o") out.push({
            ch: "•", bg: rgb(TREE_GREEN), fg: rgb(lights[(r * 2 + (col >> 1) + frame) % lights.length]),
            blink: blink && (r * 2 + (col >> 1)) % 2 === 0,
          });
          else if (t === "T") out.push({ ch: " ", bg: rgb(TREE_TRUNK) });
          else if (t === "*") out.push({ ch: frame % 2 ? "✦" : "★", fg: rgb(TREE_STAR), blink });
          else out.push({ ch: " " });
        });
      }
      rows.push(out);
    }
    return rows;
  }

  const esc = (s) => s.replace(/[&<>"]/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[ch]));

  function cellsHTML(cells) {
    return cells.map((c) => {
      let style = "";
      if (c.bg) style += `background:${c.bg};`;
      if (c.fg) style += `color:${c.fg};`;
      return `<span class="px${c.blink ? " blink" : ""}"${style ? ` style="${style}"` : ""}>${esc(c.ch)}</span>`;
    }).join("");
  }

  function moodText(mood, name) {
    return (MOODS[mood] || MOODS.idle).replace("{name}", name);
  }

  // Statusline mock, colors from statusline.py.
  const T = {
    blue: "rgb(0,153,255)", orange: "rgb(255,176,85)", green: "rgb(0,175,80)", cyan: "rgb(86,182,194)",
    white: "rgb(220,220,220)", magenta: "rgb(180,140,255)",
  };
  const span = (color, text, cls = "") => `<span class="${cls}" style="color:${color}">${esc(text)}</span>`;
  const dim = (text) => `<span class="dim">${esc(text)}</span>`;
  const SEP = ` ${dim("│")} `;
  const bar = (p) => {
    const f = Math.round(p / 10);
    return span(T.green, "●".repeat(f)) + dim("○".repeat(10 - f));
  };
  const quota = (label, p, reset) =>
    `${span(T.white, label.padEnd(9))} ${bar(p)} ${span(T.green, String(p).padStart(3) + "%")} ${dim("⟳")} ${span(T.white, reset)}`;

  function statuslineRight(mood, opts) {
    const lines = [
      `${span(T.blue, "Gemini 3 Pro")}${SEP}✍️ ${span(T.green, "18%")}${SEP}📊 ${span(T.green, "16%")} ${dim("⟳")} ${span(T.white, "2:56pm")} ${dim("(4h)")}${SEP}${span(T.cyan, "my-app")} ${span(T.green, "(main)")}${SEP}${dim("◑ medium")}`,
      quota("gemini 5h", 16, "2:56pm (4h)"),
      quota("gemini wk", 8, "nov 30, 10:56am (5d)"),
      quota("3p 5h", 0, "3:56pm (5h)"),
    ];
    if (opts.mood !== false) lines.push(dim(moodText(mood, opts.name)));
    return lines;
  }

  window.Maggy = { renderSprite, cellsHTML, moodText, statuslineRight, IDLE_FIDGETS, IDLE_MOODS };
})();

// ------------------------------------------------------------------ page
(() => {
  "use strict";
  const M = window.Maggy;
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)");
  const state = { mood: "working", theme: "default", name: "Maggy", mood_line: true, blink: true, frame: 0, fidget: 0 };

  const now = new Date();
  const isXmas = now.getMonth() === 11 && now.getDate() === 25;
  const big = document.getElementById("maggy");
  const caption = document.getElementById("mood");
  const term = document.getElementById("term-body");

  function draw() {
    const opts = { theme: state.theme, fidget: state.fidget, blink: state.blink };
    const rows = M.renderSprite(state.mood, state.frame, opts);
    big.innerHTML = rows.map((r) => `<div class="row">${M.cellsHTML(r)}</div>`).join("");
    big.classList.toggle("xmas", state.theme === "xmas");
    caption.textContent = M.moodText(state.mood, state.name);

    const right = M.statuslineRight(state.mood, { name: state.name, mood: state.mood_line });
    const width = rows[0].length;
    const blank = `<span class="px">${" ".repeat(1)}</span>`.repeat(width);
    term.innerHTML = Array.from({ length: Math.max(rows.length, right.length) }, (_, i) =>
      `<div class="row">${rows[i] ? M.cellsHTML(rows[i]) : blank}<span class="rt">  ${right[i] || ""}</span></div>`
    ).join("");
  }

  function step() {
    // agy never redraws on a timer while idle: the pose stays put and only
    // the blink-attribute sparkles (CSS .blink) twinkle, like a real terminal.
    if (M.IDLE_MOODS.has(state.mood)) return;
    state.frame++;
    draw();
  }

  // One idle "redraw": a new fidget, never the same one twice in a row.
  function nextFidget() {
    let next;
    do { next = Math.floor(Math.random() * M.IDLE_FIDGETS.length); } while (next === state.fidget);
    state.fidget = next;
  }

  let timer = null;
  function play() {
    clearInterval(timer);
    timer = reduced.matches ? null : setInterval(step, 280);
  }
  reduced.addEventListener?.("change", play);
  document.addEventListener("visibilitychange", () => (document.hidden ? clearInterval(timer) : play()));

  // agent_state chips
  const chips = document.querySelectorAll("[data-mood]");
  chips.forEach((b) => b.addEventListener("click", () => {
    // Clicking an idle chip again acts as one agy redraw: a new still pose.
    if (b.dataset.mood === "idle" && state.mood === "idle") nextFidget();
    if (b.dataset.mood === "sleep" && state.mood === "sleep") state.frame++;
    else state.frame = 0;
    state.mood = b.dataset.mood;
    chips.forEach((c) => c.setAttribute("aria-pressed", String(c === b)));
    draw();
  }));

  // Playground: every control echoes the maggy command it maps to.
  const cmd = (id, text) => { document.getElementById(id).textContent = text; };
  const nameInput = document.getElementById("pet-name");
  nameInput.addEventListener("input", () => {
    const v = nameInput.value.replace(/[^\P{C}]/gu, "").trim().slice(0, 16);
    state.name = v || "Maggy";
    // Shell-quote the echoed command so pasting it can't run anything else.
    const q = /^[\w.@%+=:,\/-]+$/u.test(v) ? v : `'${v.replace(/'/g, `'\\''`)}'`;
    cmd("cmd-name", v && v !== "Maggy" ? `maggy name ${q}` : "maggy name --reset");
    draw();
  });
  document.querySelectorAll("[name=theme]").forEach((r) => r.addEventListener("change", () => {
    state.theme = r.value === "xmas" || (r.value === "auto" && isXmas) ? "xmas" : "default";
    cmd("cmd-theme", `maggy theme ${r.value}`);
    draw();
  }));
  const toggle = (id, key, cmdId, word) => {
    const el = document.getElementById(id);
    el.addEventListener("change", () => {
      state[key] = el.checked;
      cmd(cmdId, `maggy ${word} ${el.checked ? "on" : "off"}`);
      draw();
    });
  };
  toggle("opt-mood", "mood_line", "cmd-mood", "mood");
  toggle("opt-blink", "blink", "cmd-blink", "blink");

  // Install tabs
  const tabs = document.querySelectorAll("[role=tab]");
  tabs.forEach((t, i) => {
    const select = () => {
      tabs.forEach((o) => {
        const on = o === t;
        o.setAttribute("aria-selected", String(on));
        o.tabIndex = on ? 0 : -1;
        document.getElementById(o.getAttribute("aria-controls")).hidden = !on;
      });
    };
    t.addEventListener("click", select);
    t.addEventListener("keydown", (e) => {
      const dir = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
      if (!dir) return;
      const next = tabs[(i + dir + tabs.length) % tabs.length];
      next.focus();
      next.click();
    });
  });

  // Copy buttons
  const t = (key, fallback) => (window.MaggyI18n ? window.MaggyI18n.t(key) : fallback);
  document.querySelectorAll("[data-copy]").forEach((btn) => btn.addEventListener("click", async () => {
    const text = document.getElementById(btn.dataset.copy).textContent.trim();
    try {
      await navigator.clipboard.writeText(text);
      btn.textContent = t("copy.copied", "Copied");
    } catch {
      btn.textContent = t("copy.fallback", "Select and copy");
    }
    setTimeout(() => (btn.textContent = t("copy.idle", "Copy")), 1600);
  }));

  // On Christmas Day "auto" dresses up, like the real thing.
  if (isXmas) state.theme = "xmas";

  draw();
  play();
})();
