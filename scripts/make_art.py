#!/usr/bin/env python3
"""Draw the README art: docs/media/banner.svg, pipeline.svg, badges/*.svg, logo.png, logo-128.png.

    python3 scripts/make_art.py            # needs fonttools and Pillow; reads the fonts in wz/fonts/

Text is converted to outlines (Space Grotesk, SIL OFL), so the SVGs look the same on every machine and in
GitHub's image proxy, which has no web fonts.
"""
import math
import sys
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
FONTS = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "wz" / "fonts"
OUT = ROOT / "docs" / "media"
INK, GOLD, CREAM, DIM, LINE = "#1B1030", "#FFB52E", "#FFF6DE", "#B9A9D9", "#4A3478"
_cache = {}


def font(name):
    if name not in _cache:
        f = TTFont(str(FONTS / name))
        _cache[name] = (f, f.getGlyphSet(), f.getBestCmap(), f["head"].unitsPerEm)
    return _cache[name]


def text(s, x, y, size, fill, name="SpaceGrotesk-Bold.ttf", anchor="start", track=0.0):
    """One <path> for a line of text; (x, y) is the baseline start, middle or end."""
    f, glyphs, cmap, upm = font(name)
    k = size / upm
    width = sum(glyphs[cmap.get(ord(c), ".notdef")].width * k + track for c in s) - track
    cx = x - (width / 2 if anchor == "middle" else width if anchor == "end" else 0)
    d = []
    for c in s:
        g = glyphs[cmap.get(ord(c), ".notdef")]
        pen = SVGPathPen(glyphs, ntos=lambda v: f"{v:.1f}")
        g.draw(TransformPen(pen, (k, 0, 0, -k, cx, y)))
        d.append(pen.getCommands())
        cx += g.width * k + track
    return f'<path fill="{fill}" d="{" ".join(d)}"/>', width


def sine(x0, y0, w, h, waves=3.5, rise=0.55, n=120):
    """A rising sine: the difficulty curve the skills teach (push, breathe, push higher)."""
    pts = []
    for i in range(n + 1):
        t = i / n
        y = y0 + h - (rise * t + (1 - rise) * 0.5 * (1 - math.cos(t * waves * 2 * math.pi)) * (0.35 + 0.65 * t)) * h
        pts.append(f"{x0 + t * w:.1f},{y:.1f}")
    return "M" + " L".join(pts)


def emblem(x, y, s):
    r = s * 0.22
    return (f'<rect x="{x}" y="{y}" width="{s}" height="{s}" rx="{r}" fill="#2B1650" stroke="{LINE}" stroke-width="{s * 0.02:.1f}"/>'
            f'<path d="{sine(x + s * 0.16, y + s * 0.24, s * 0.68, s * 0.52)}" fill="none" stroke="{GOLD}" stroke-width="{s * 0.075:.1f}" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<circle cx="{x + s * 0.84:.1f}" cy="{y + s * 0.24:.1f}" r="{s * 0.06:.1f}" fill="{CREAM}"/>')


def svg(w, h, body, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{title}">'
            f"<title>{title}</title>{body}</svg>\n")


def banner():
    W, H = 1600, 520
    dots = "".join(f'<circle cx="{x}" cy="{y}" r="1.6" fill="{LINE}"/>' for x in range(40, W, 40) for y in range(40, H, 40))
    word, ww = text("wizerax", 330, 268, 190, CREAM, track=-2)
    tag, _ = text("the game studio in a skill", 336, 344, 54, GOLD, "SpaceGrotesk-Medium.ttf")
    sub, _ = text("skills  ·  the wz CLI  ·  a knowledge base  —  for web games built with AI agents", 338, 412, 27, DIM, "SpaceGrotesk-Medium.ttf")
    curve = f'<path d="{sine(330 + ww + 60, 120, W - (330 + ww + 60) - 90, 250, waves=4.5)}" fill="none" stroke="{LINE}" stroke-width="10" stroke-linecap="round"/>'
    body = (f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{INK}"/><stop offset="1" stop-color="#2B1650"/></linearGradient></defs>'
            f'<rect width="{W}" height="{H}" rx="28" fill="url(#g)"/>{dots}{curve}{emblem(90, 150, 200)}{word}{tag}{sub}')
    (OUT / "banner.svg").write_text(svg(W, H, body, "wizerax: the game studio in a skill"))


STEPS = [("recon", "wz scan"), ("slice", "one playable loop"), ("economy", "player-model bots"), ("UI kit", "one golden CTA"),
         ("feel + audio", "measured mix"), ("performance", "60 fps, recovers"), ("browser QA", "wz qa"), ("release", "wz publish check"),
         ("trailer", "wz video compile"), ("field note", "wz kb new")]


def pipeline():
    W, H, cols = 1600, 420, 5
    bw, bh, gx, gy, x0, y0 = 252, 112, 60, 64, 62, 86
    body = [f'<rect width="{W}" height="{H}" rx="24" fill="{INK}"/>']
    head, _ = text("the loop every wizerax session runs", x0, 52, 28, DIM, "SpaceGrotesk-Medium.ttf")
    body.append(head)
    for i, (name, hint) in enumerate(STEPS):
        r, c = divmod(i, cols)
        x, y = x0 + c * (bw + gx), y0 + r * (bh + gy)
        body.append(f'<rect x="{x}" y="{y}" width="{bw}" height="{bh}" rx="18" fill="#2B1650" stroke="{LINE}" stroke-width="2"/>')
        num, _ = text(f"{i + 1:02d}", x + 20, y + 34, 18, GOLD, "JetBrainsMono-Bold.ttf")
        t1, _ = text(name, x + 20, y + 70, 30, CREAM)
        t2, _ = text(hint, x + 20, y + 97, 17, DIM, "JetBrainsMono-Bold.ttf" if hint.startswith("wz ") else "SpaceGrotesk-Medium.ttf")
        body += [num, t1, t2]
        if c < cols - 1:
            ax, ay = x + bw + 12, y + bh / 2
            body.append(f'<path d="M{ax},{ay} h{gx - 30} m-10,-8 l10,8 l-10,8" fill="none" stroke="{GOLD}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>')
    # the turn from the end of row 1 to the start of row 2
    xr, y1, y2 = x0 + cols * bw + (cols - 1) * gx + 22, y0 + bh / 2, y0 + bh + gy / 2
    body.append(f'<path d="M{xr - 22},{y1} h14 a8,8 0 0 1 8,8 v{y2 - y1 - 16} a8,8 0 0 1 -8,8 H{x0 - 22} a8,8 0 0 0 -8,8 v{bh / 2 + gy / 2 - 16} a8,8 0 0 0 8,8 h12 m-10,-8 l10,8 l-10,8" '
                f'fill="none" stroke="{GOLD}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" opacity="0.7"/>')
    (OUT / "pipeline.svg").write_text(svg(W, H, "".join(body), "The loop: recon, slice, economy, UI kit, feel and audio, performance, browser QA, release, trailer, field note"))


def badge(slug, left, right):
    l, lw = text(left, 0, 0, 15, DIM, "SpaceGrotesk-Medium.ttf")
    r, rw = text(right, 0, 0, 15, INK)
    w1, w2, h = lw + 24, rw + 24, 30
    l, _ = text(left, 12, 20.5, 15, DIM, "SpaceGrotesk-Medium.ttf")
    r, _ = text(right, w1 + 12, 20.5, 15, INK)
    body = (f'<clipPath id="c"><rect width="{w1 + w2:.0f}" height="{h}" rx="8"/></clipPath><g clip-path="url(#c)">'
            f'<rect width="{w1:.0f}" height="{h}" fill="{INK}"/><rect x="{w1:.0f}" width="{w2:.0f}" height="{h}" fill="{GOLD}"/></g>{l}{r}')
    (OUT / "badges").mkdir(parents=True, exist_ok=True)
    (OUT / "badges" / f"{slug}.svg").write_text(svg(round(w1 + w2), h, body, f"{left}: {right}"))


def logo(size):
    s = size * 4
    im = Image.new("RGBA", (s, s))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, s - 1, s - 1], radius=int(s * 0.22), fill="#2B1650", outline=LINE, width=max(2, s // 50))
    pts, n = [], 160
    for i in range(n + 1):
        t = i / n
        y = s * 0.24 + s * 0.52 - (0.55 * t + 0.45 * 0.5 * (1 - math.cos(t * 3.5 * 2 * math.pi)) * (0.35 + 0.65 * t)) * s * 0.52
        pts.append((s * 0.16 + t * s * 0.68, y))
    lw = int(s * 0.075)
    d.line(pts, fill=GOLD, width=lw, joint="curve")
    for p in (pts[0], pts[-1]):
        d.ellipse([p[0] - lw / 2, p[1] - lw / 2, p[0] + lw / 2, p[1] + lw / 2], fill=GOLD)
    r = s * 0.06
    d.ellipse([s * 0.84 - r, s * 0.24 - r, s * 0.84 + r, s * 0.24 + r], fill=CREAM)
    return im.resize((size, size), Image.LANCZOS)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    banner()
    pipeline()
    badge("agents", "works with", "Claude Code · Codex · Cursor · Gemini CLI · Copilot · OpenCode")
    badge("knowledge", "knowledge base", "field notes by agents, for agents")
    badge("stack", "for", "mobile web games · Vite + three.js")
    badge("license", "license", "MIT")
    logo(512).save(OUT / "logo.png")
    logo(128).save(OUT / "logo-128.png")
    print("wrote", ", ".join(sorted(p.relative_to(ROOT).as_posix() for p in OUT.rglob("*") if p.is_file())))


if __name__ == "__main__":
    main()
