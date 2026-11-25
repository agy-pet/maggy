#!/usr/bin/env python3
"""Render README preview images (animated GIFs + a PNG screenshot).

Renders the real statusline output (ANSI truecolor) onto a terminal-like
canvas with Pillow, so the previews always match the code.

Usage (macOS, needs Pillow + fontTools):
    python3 scripts/make_preview.py            # writes into assets/
"""

import os
import re
import sys
import tempfile

from fontTools.ttLib import TTCollection, TTFont
from PIL import Image, ImageDraw, ImageFont

# Keep the sample quota data out of the user's real cache.
os.environ["XDG_CACHE_HOME"] = tempfile.mkdtemp(prefix="agy-preview-")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import statusline  # noqa: E402
from preview import SAMPLE_DATA  # noqa: E402

OUT_DIR = os.path.join(ROOT, "assets")
FONT_SIZE = 26
PAD = 28
TERM_BG = (24, 24, 32)
TERM_FG = (220, 220, 220)

# Fonts tried in order for each character (path, collection index).
FONT_CHAIN = [
    ("/System/Library/Fonts/Menlo.ttc", 0),
    ("/System/Library/Fonts/Apple Symbols.ttf", 0),
    ("/System/Library/Fonts/Apple Color Emoji.ttc", 0),
]
EMOJI_FONT = "/System/Library/Fonts/Apple Color Emoji.ttc"
EMOJI_NATIVE = 160  # Apple Color Emoji only has bitmap strikes (e.g. 160px)

SGR_RE = re.compile(r"\x1b\[([0-9;]*)m")


def _cmap(path, index):
    if path.endswith(".ttc"):
        font = TTCollection(path).fonts[index]
    else:
        font = TTFont(path)
    return set(font.getBestCmap() or {})


class Fonts:
    def __init__(self):
        self.chain = []
        for path, index in FONT_CHAIN:
            if path == EMOJI_FONT:
                pil = ImageFont.truetype(path, EMOJI_NATIVE, index=index)
            else:
                pil = ImageFont.truetype(path, FONT_SIZE, index=index)
            self.chain.append((path, pil, _cmap(path, index)))
        base = self.chain[0][1]
        self.cell_w = round(base.getlength("M"))
        ascent, descent = base.getmetrics()
        self.cell_h = round((ascent + descent) * 1.15)
        self.baseline_off = (self.cell_h - (ascent + descent)) // 2

    def pick(self, ch, emoji=False):
        chain = self.chain
        if emoji:  # wide (emoji-presentation) chars prefer the color emoji font
            chain = sorted(chain, key=lambda f: f[0] != EMOJI_FONT)
        for path, pil, cmap in chain:
            if ord(ch) in cmap:
                return path, pil
        return self.chain[0][0], self.chain[0][1]


def parse_ansi(line):
    """Yield (text, fg, bg, dim) runs for one line of SGR-coded text."""
    fg, bg, dim = None, None, False
    pos = 0
    for m in SGR_RE.finditer(line):
        if m.start() > pos:
            yield line[pos:m.start()], fg, bg, dim
        params = [int(p) if p else 0 for p in m.group(1).split(";")]
        i = 0
        while i < len(params):
            p = params[i]
            if p == 0:
                fg, bg, dim = None, None, False
            elif p == 2:
                dim = True
            elif p == 22:
                dim = False
            elif p == 39:
                fg = None
            elif p == 49:
                bg = None
            elif p in (38, 48) and i + 4 < len(params) and params[i + 1] == 2:
                rgb = tuple(params[i + 2:i + 5])
                if p == 38:
                    fg = rgb
                else:
                    bg = rgb
                i += 4
            i += 1
        pos = m.end()
    if pos < len(line):
        yield line[pos:], fg, bg, dim


def cells(line):
    """Split a line into terminal cells: (char, width, fg, bg, dim)."""
    out = []
    for text, fg, bg, dim in parse_ansi(line):
        for ch in text:
            if ch == "️":  # variation selector: makes previous emoji wide
                if out:
                    out[-1] = (out[-1][0], 2) + out[-1][2:]
                continue
            width = 2 if ord(ch) >= 0x1F000 else 1
            out.append((ch, width, fg, bg, dim))
    return out


def render(lines, fonts, cols):
    rows = len(lines)
    img = Image.new("RGB", (PAD * 2 + cols * fonts.cell_w, PAD * 2 + rows * fonts.cell_h), TERM_BG)
    draw = ImageDraw.Draw(img)
    for r, line in enumerate(lines):
        x = 0
        y = PAD + r * fonts.cell_h
        for ch, width, fg, bg, dim in cells(line):
            px = PAD + x * fonts.cell_w
            w = width * fonts.cell_w
            if bg is not None:
                draw.rectangle([px, y, px + w - 1, y + fonts.cell_h - 1], fill=bg)
            if ch != " ":
                color = fg or TERM_FG
                if dim:
                    base = bg or TERM_BG
                    color = tuple((c + b) // 2 for c, b in zip(color, base))
                path, pil = fonts.pick(ch, emoji=width == 2)
                if path == EMOJI_FONT:
                    glyph = Image.new("RGBA", (EMOJI_NATIVE * 2, EMOJI_NATIVE * 2), (0, 0, 0, 0))
                    ImageDraw.Draw(glyph).text((0, 0), ch, font=pil, embedded_color=True)
                    glyph = glyph.crop(glyph.getbbox() or (0, 0, 1, 1))
                    size = int(fonts.cell_h * 0.8)
                    glyph.thumbnail((size, size), Image.LANCZOS)
                    img.paste(glyph, (px + (w - glyph.width) // 2, y + (fonts.cell_h - glyph.height) // 2), glyph)
                else:
                    gw = pil.getlength(ch)
                    draw.text((px + (w - gw) / 2, y + fonts.baseline_off), ch, font=pil, fill=color)
            x += width
    return img


def frames_for(state, count, activity=None, theme="default"):
    os.environ["MAGGY_THEME"] = theme
    data = dict(SAMPLE_DATA, agent_state=state, cwd="/home/you/my-app")
    return [statusline.render_statusline(data, frame_idx=i, activity=activity).split("\n")
            for i in range(count)]


def save_gif(path, frame_lines, fonts, duration=280):
    cols = max(sum(c[1] for c in cells(l)) for f in frame_lines for l in f)
    images = [render(f, fonts, cols) for f in frame_lines]
    images[0].save(path, save_all=True, append_images=images[1:], duration=duration,
                   loop=0, optimize=True, disposal=2)
    return images


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    fonts = Fonts()
    dance = frames_for("working", 8) * 2 + frames_for("tool_use", 4) * 2
    save_gif(os.path.join(OUT_DIR, "dance.gif"), dance, fonts)

    xmas = frames_for("working", 8, theme="xmas") * 2 + frames_for("tool_use", 4, theme="xmas") * 2
    images = save_gif(os.path.join(OUT_DIR, "xmas.gif"), xmas, fonts)
    images[2].save(os.path.join(OUT_DIR, "xmas.png"))
    print("wrote", ", ".join(os.path.join("assets", n) for n in ("dance.gif", "xmas.gif", "xmas.png")))


if __name__ == "__main__":
    main()
