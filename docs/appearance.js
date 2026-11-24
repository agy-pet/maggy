// Site appearance: light, dark, or follow the system (default).
// Loaded without defer in <head> so a saved choice applies before first
// paint (no flash). style.css keys off :root[data-theme="light"|"dark"].
(() => {
  "use strict";

  const KEY = "maggy.appearance";
  const MODES = ["light", "system", "dark"];
  const BG = { light: "#ffffff", dark: "#141019" };
  const root = document.documentElement;

  const read = () => {
    try {
      const v = localStorage.getItem(KEY);
      return v === "light" || v === "dark" ? v : "system";
    } catch (e) {
      return "system";
    }
  };

  const apply = (mode) => {
    if (mode === "system") delete root.dataset.theme;
    else root.dataset.theme = mode;
    // Browser chrome color: pin both media variants to the forced scheme,
    // or restore each one's own color when following the system.
    document.querySelectorAll('meta[name="theme-color"]').forEach((m) => {
      const own = /dark/.test(m.media) ? BG.dark : BG.light;
      m.content = mode === "system" ? own : BG[mode];
    });
    document.querySelectorAll("[data-appearance]").forEach((b) => {
      b.setAttribute("aria-pressed", String(b.dataset.appearance === mode));
    });
  };

  apply(read());

  document.addEventListener("DOMContentLoaded", () => {
    apply(read());
    document.querySelectorAll("[data-appearance]").forEach((b) => {
      b.addEventListener("click", () => {
        const mode = MODES.includes(b.dataset.appearance) ? b.dataset.appearance : "system";
        try {
          if (mode === "system") localStorage.removeItem(KEY);
          else localStorage.setItem(KEY, mode);
        } catch (e) {}
        apply(mode);
      });
    });
  });
})();
