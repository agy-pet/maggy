#!/usr/bin/env python3
"""Render brand images from the real mascot sprite and colors.

    python3 scripts/make_brand.py    # writes assets/social-preview.png, assets/avatar.png,
                                     # docs/favicon.svg, docs/favicon.ico

social-preview.png (1280x640) is the GitHub repo social preview;
avatar.png (512x512) is the agy-pet org avatar.
favicon.svg is a vector version of the avatar for the site tab icon;
favicon.ico (16/32/48) is the fallback for browsers without SVG favicons. Needs Pillow (macOS fonts).
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import mascot  # noqa: E402

OUT_DIR = os.path.join(ROOT, "assets")
BG = (24, 24, 32)
FG = (230, 230, 236)
MUTED = (150, 150, 165)
MENLO = "/System/Library/Fonts/Menlo.ttc"


def font(size, bold=False):
    return ImageFont.truetype(MENLO, size, index=1 if bold else 0)


def draw_eye(draw, cx, cy, r, kind):
    """◕ = white eye with a dark pupil up-right; ◠ = happy closed arc."""
    if kind == "◠":
        w = max(3, r // 3)
        draw.arc([cx - r, cy - r * 0.6, cx + r, cy + r * 1.4], 200, 340, fill=mascot.EYE_COLOR, width=w)
        return
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=mascot.EYE_COLOR)
    p = r * 0.55
    draw.ellipse([cx - p + r * 0.3, cy - p - r * 0.25, cx + p + r * 0.3, cy + p - r * 0.25], fill=BG)


def draw_sprite(img, x0, y0, u, pose=mascot.BASE, eyes="◕◕", sparkles=()):
    """Draw a pose with each terminal char cell as u wide by 2u tall (pairs form squares)."""
    draw = ImageDraw.Draw(img)
    head_row = next(r for r, row in enumerate(pose) if " " not in row[2:10])
    for r, row in enumerate(pose):
        for c, ch in enumerate(row):
            if ch == " ":
                continue
            x, y = x0 + c * u, y0 + r * 2 * u
            draw.rectangle([x, y, x + u - 1, y + 2 * u - 1], fill=mascot.LOGO_COLORS[ch])
    for col, kind in zip(mascot.EYE_COLS, eyes):
        draw_eye(draw, x0 + col * u + u / 2, y0 + head_row * 2 * u + u, u * 0.42, kind)
    for r, c, glyph in sparkles:
        cx, cy = x0 + c * u + u / 2, y0 + r * 2 * u + u
        if glyph == "✦":
            draw_star(draw, cx, cy, u * 0.75)
        else:
            d = u * 0.14
            draw.ellipse([cx - d, cy - d, cx + d, cy + d], fill=mascot.SPARKLE_COLOR)


def draw_star(draw, cx, cy, r):
    """Four-pointed sparkle (✦)."""
    k = r * 0.28
    pts = [(cx, cy - r), (cx + k, cy - k), (cx + r, cy), (cx + k, cy + k),
           (cx, cy + r), (cx - k, cy + k), (cx - r, cy), (cx - k, cy - k)]
    draw.polygon(pts, fill=mascot.SPARKLE_COLOR)


def sprite_size(u):
    return mascot.POSE_WIDTH * u, mascot.SPRITE_HEIGHT * 2 * u


def social_preview():
    W, H = 1280, 640
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # rainbow strip along the bottom, using the logo's colors left to right
    colors = [mascot.LOGO_COLORS[k] for k in "mnkgcabdefjilop"]
    seg = W / len(colors)
    for i, col in enumerate(colors):
        draw.rectangle([round(i * seg), H - 12, round((i + 1) * seg), H], fill=col)

    u = 36
    sw, sh = sprite_size(u)
    sx, sy = 110, (H - sh) // 2 - 6
    sparkles = ((0, 0, "✦"), (0, 12, "·"), (2, -1, "·"), (4, 11, "✦"))
    draw_sprite(img, sx, sy, u, mascot.TIPTOE, "◕◕", sparkles)

    tx = sx + sw + 90
    draw.text((tx, 170), "maggy", font=font(112, bold=True), fill=FG)
    draw.text((tx, 318), "the dancing Antigravity logo", font=font(32), fill=MUTED)
    draw.text((tx, 360), "for your agy statusline", font=font(32), fill=MUTED)

    cmd = "brew install agy-pet/tap/maggy"
    f = font(26)
    pad_x, pad_y = 22, 14
    l, t, r, b = draw.textbbox((0, 0), "$ " + cmd, font=f)
    box = [tx, 438, tx + (r - l) + 2 * pad_x, 438 + (b - t) + 2 * pad_y]
    draw.rounded_rectangle(box, radius=12, fill=(36, 36, 48), outline=(60, 60, 78), width=2)
    draw.text((tx + pad_x, box[1] + pad_y - t), "$ ", font=f, fill=mascot.LOGO_COLORS["k"])
    draw.text((tx + pad_x + draw.textlength("$ ", font=f), box[1] + pad_y - t), cmd, font=f, fill=FG)

    path = os.path.join(OUT_DIR, "social-preview.png")
    img.save(path, optimize=True)
    return path


def avatar():
    S = 512
    img = Image.new("RGB", (S, S), BG)
    u = 26
    sw, sh = sprite_size(u)
    draw_sprite(img, (S - sw) // 2, (S - sh) // 2 + u // 2, u, mascot.BASE, "◕◕",
                ((0, 1, "✦"), (0, 10, "·")))
    path = os.path.join(OUT_DIR, "avatar.png")
    img.save(path, optimize=True)
    return path


DOCS_DIR = os.path.join(ROOT, "docs")
FAVICON_U = 34  # cell width in a 512 box: a tighter crop than the avatar so it reads at 16px
FAVICON_SPARKLES = ((0, 1, "✦"), (0, 10, "·"))


def favicon_origin(S, u):
    sw, sh = sprite_size(u)
    return (S - sw) / 2, (S - sh) / 2 + u / 2


def favicon_svg():
    """Vector favicon: the avatar's sprite, eyes and sparkles on a rounded dark tile."""
    S, u = 512, FAVICON_U
    x0, y0 = favicon_origin(S, u)
    pose, eyes = mascot.BASE, "◕◕"
    hexc = lambda c: "#%02x%02x%02x" % tuple(c)
    n = lambda v: f"{v:g}" if v == int(v) else f"{v:.2f}".rstrip("0")
    parts = [f'<rect width="{S}" height="{S}" rx="96" fill="{hexc(BG)}"/>']
    # merge each colored char-pair into one square so there are no hairline seams
    for r, row in enumerate(pose):
        c = 0
        while c < len(row):
            ch = row[c]
            if ch == " ":
                c += 1
                continue
            w = 1
            while c + w < len(row) and row[c + w] == ch:
                w += 1
            parts.append(f'<rect x="{n(x0 + c * u)}" y="{n(y0 + r * 2 * u)}" width="{w * u}" '
                         f'height="{2 * u}" fill="{hexc(mascot.LOGO_COLORS[ch])}"/>')
            c += w
    head_row = next(r for r, row in enumerate(pose) if " " not in row[2:10])
    er, p = u * 0.42, u * 0.42 * 0.55
    for col, _ in zip(mascot.EYE_COLS, eyes):
        cx, cy = x0 + col * u + u / 2, y0 + head_row * 2 * u + u
        parts.append(f'<circle cx="{n(cx)}" cy="{n(cy)}" r="{n(er)}" fill="{hexc(mascot.EYE_COLOR)}"/>')
        parts.append(f'<circle cx="{n(cx + er * 0.3)}" cy="{n(cy - er * 0.25)}" r="{n(p)}" fill="{hexc(BG)}"/>')
    for r, c, glyph in FAVICON_SPARKLES:
        cx, cy = x0 + c * u + u / 2, y0 + r * 2 * u + u
        if glyph == "✦":
            R = u * 0.75
            k = R * 0.28
            pts = [(cx, cy - R), (cx + k, cy - k), (cx + R, cy), (cx + k, cy + k),
                   (cx, cy + R), (cx - k, cy + k), (cx - R, cy), (cx - k, cy - k)]
            parts.append(f'<polygon points="{" ".join(f"{n(x)},{n(y)}" for x, y in pts)}" '
                         f'fill="{hexc(mascot.SPARKLE_COLOR)}"/>')
        else:
            parts.append(f'<circle cx="{n(cx)}" cy="{n(cy)}" r="{n(u * 0.14)}" '
                         f'fill="{hexc(mascot.SPARKLE_COLOR)}"/>')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {S} {S}">'
           + "".join(parts) + "</svg>\n")
    path = os.path.join(DOCS_DIR, "favicon.svg")
    with open(path, "w") as f:
        f.write(svg)
    return path


def favicon_ico():
    """Raster fallback, drawn at 512 with a rounded tile and downsampled."""
    S, u = 512, FAVICON_U
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(img).rounded_rectangle([0, 0, S - 1, S - 1], radius=96, fill=BG)
    x0, y0 = favicon_origin(S, u)
    draw_sprite(img, round(x0), round(y0), u, mascot.BASE, "◕◕", FAVICON_SPARKLES)
    path = os.path.join(DOCS_DIR, "favicon.ico")
    img.save(path, sizes=[(16, 16), (32, 32), (48, 48)])
    return path


if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    print("wrote", social_preview(), avatar(), favicon_svg(), favicon_ico())
