#!/usr/bin/env python3
"""Write the README's pixel icons, its badges' template and the made-with badge.

    python3 scripts/make_site.py --icons                   # docs/media/icons/*-{dark,light}.svg
    python3 scripts/make_site.py --media build.html        # the badge template (+ icons, made-with-*.svg)
    node scripts/shoot.mjs <folder with node_modules/playwright> build.html   # screenshots -> docs/media, _preview
    python3 scripts/make_site.py --shrink                  # 256-colour banner.png

The live page is docs/index.html, edited by hand; this script never writes into docs/ except docs/media.
"""
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARK = "8,10 30,10 30,27 39,27 39,10 61,10 61,27 70,27 70,10 92,10 92,54 71,90 50,58 29,90 8,54"
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">')
CSS = """:root{--bg:#050507;--ink-6:oklch(66% .006 280);--ink-9:oklch(97% 0 0);--accent:oklch(84% .13 195);--mono:"JetBrains Mono",ui-monospace,monospace}
*{box-sizing:border-box;margin:0;padding:0}body{padding:24px;display:grid;gap:24px;justify-items:start;background:#222}
.label{font:500 10px/1 var(--mono);letter-spacing:.14em;text-transform:uppercase;color:var(--ink-6)}"""

# 12 x 12 pixel icons: (accent path, ink path). The four pillars, then the four commands. video is Universal Modder's (MIT).
ICONS = {
    "trailer": ("M4 6h2v4h-2zM6 7h2v2h-2z",
                "M0 1h3v2h-3zM5 1h3v2h-3zM10 1h2v2h-2zM0 3h1v1h-1zM0 4h12v1h-12zM0 5h1v6h-1zM11 5h1v6h-1zM0 11h12v1h-12z"),
    "balance": ("M0 7h4v1h-4zM8 5h4v1h-4z",
                "M5 1h2v9h-2zM1 3h10v1h-10zM1 4h1v3h-1zM10 4h1v1h-1zM3 10h6v1h-6zM2 11h8v1h-8z"),
    "meta": ("M5 5h2v3h-2zM5 0h2v1h-2z",
             "M1 2h10v1h-10zM0 3h1v3h-1zM11 3h1v3h-1zM0 6h5v1h-5zM7 6h5v1h-5zM0 7h1v4h-1zM11 7h1v4h-1zM0 11h12v1h-12z"),
    "qa": ("M4 6h1v1h-1zM5 7h1v1h-1zM6 6h1v1h-1zM7 5h1v1h-1z", "M2 0h8v1h-8zM2 1h1v10h-1zM9 1h1v10h-1zM2 11h8v1h-8zM5 9h2v1h-2z"),
    "board": ("M2 2h3v6h-3z", "M0 0h12v1h-12zM0 1h1v10h-1zM11 1h1v10h-1zM0 11h12v1h-12zM6 2h4v2h-4zM6 5h4v3h-4zM2 9h8v1h-8z"),
    "music-enhance": ("M5 1h2v10h-2z", "M1 7h1v4h-1zM3 4h1v7h-1zM8 5h1v6h-1zM10 8h1v3h-1zM0 11h12v1h-12z"),
    "video": ("M4 4h2v1h-2zM4 5h4v1h-4zM4 6h6v1h-6zM4 7h4v1h-4zM4 8h2v1h-2z", "M0 0h12v1h-12zM0 1h1v1h-1zM2 1h1v1h-1zM4 1h1v1h-1zM6 1h1v1h-1zM8 1h1v1h-1zM10 1h2v1h-2zM0 2h12v1h-12zM0 3h1v6h-1zM11 3h1v6h-1zM0 9h12v1h-12zM0 10h1v1h-1zM2 10h1v1h-1zM4 10h1v1h-1zM6 10h1v1h-1zM8 10h1v1h-1zM10 10h2v1h-2zM0 11h12v1h-12z"),
}
LABELS = {"trailer": "game trailer", "balance": "balance and economy", "meta": "meta and monetization", "qa": "virtual QA testers"}


def icons(out):
    (out / "icons").mkdir(parents=True, exist_ok=True)
    for name, (accent, ink) in ICONS.items():
        label = LABELS.get(name, f"wise {name}")
        for theme, a, col in (("dark", "#45E3E0", "#F5F5F5"), ("light", "#0E9AA1", "#0A0A0C")):
            (out / "icons" / f"{name}-{theme}.svg").write_text(
                f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 12 12" width="96" height="96" shape-rendering="crispEdges" role="img" aria-label="{label}">'
                f'<path fill="{a}" d="{accent}"/><path fill="{col}" d="{ink}"/></svg>\n')


def media():
    """The README badges as screenshot templates; scripts/shoot.mjs screenshots every [data-shot] element."""
    badge = lambda slug, a, b: (f'<div data-shot="badges/{slug}" data-scale="2" data-clear="1" style="display:inline-flex;align-items:center;gap:9px;height:26px;padding:0 11px;border:1px solid #ffffff24;background:#050507">'
                                f'<i style="width:5px;height:5px;background:var(--accent)"></i><span class="label">{a}</span>'
                                f'<span class="label" style="color:var(--ink-9)">{b}</span></div>')
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8">{FONTS}<style>{CSS}</style></head><body>'
            f'{badge("agents", "works with", "claude code · codex · cursor · gemini · copilot · opencode")}'
            f'{badge("knowledge", "knowledge base", "field notes by agents, for agents")}{badge("license", "license", "mit")}</body></html>\n')


def made_with(out, mono):
    """The "made with wisecraft" badge: a hairline box, the mark, mono capitals drawn as outlines (no web font needed)."""
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.transformPen import TransformPen
    from fontTools.ttLib import TTFont
    f = TTFont(str(mono))
    glyphs, cmap, k, track = f.getGlyphSet(), f.getBestCmap(), 11 / f["head"].unitsPerEm, 2.4

    def text(s, x, y, fill):
        d = []
        for ch in s:
            g = glyphs[cmap[ord(ch)]]
            pen = SVGPathPen(glyphs, ntos=lambda v: f"{v:.1f}")
            g.draw(TransformPen(pen, (k, 0, 0, -k, x, y)))
            d.append(pen.getCommands())
            x += g.width * k + track
        return f'<path fill="{fill}" d="{" ".join(c for c in d if c)}"/>', x

    for theme, bg, ink, muted, line, accent in (("dark", "#050507", "#F5F5F5", "#8A8B92", "#FFFFFF2E", "#45E3E0"), ("light", "#FFFFFF", "#0A0A0C", "#6E6E78", "#0A0A0C2E", "#0E9AA1")):
        a, x = text("MADE WITH", 36, 20, muted)
        b, x = text("WISECRAFT", x + 6, 20, ink)
        W = round(x + 10)
        (out / f"made-with-{theme}.svg").write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} 32" width="{W * 2}" height="64" role="img" aria-label="made with wisecraft">'
            f'<rect x=".5" y=".5" width="{W - 1}" height="31" fill="{bg}" stroke="{line}"/>'
            f'<g transform="translate(12 8) scale(.16)"><polygon points="{MARK}" fill="{ink}"/><rect x="39" y="10" width="22" height="17" fill="{accent}"/></g>{a}{b}</svg>\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--icons", action="store_true", help="write docs/media/icons and stop")
    ap.add_argument("--media", help="write the badge template page to this path, plus the icons and the made-with badge")
    ap.add_argument("--mono", default="~/Library/Fonts/JetBrainsMono-Medium.ttf", help="JetBrains Mono .ttf for the made-with badge outlines")
    ap.add_argument("--shrink", action="store_true", help="quantize docs/media/banner.png to 256 colours and exit")
    a = ap.parse_args()
    if a.shrink:
        from PIL import Image
        f = ROOT / "docs" / "media" / "banner.png"
        Image.open(f).convert("RGB").quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG).save(f, optimize=True)
        return
    if a.icons or a.media:
        icons(ROOT / "docs" / "media")
        print("wrote docs/media/icons")
    if a.media:
        Path(a.media).write_text(media())
        made_with(ROOT / "docs" / "media", Path(a.mono).expanduser())
        print("wrote", a.media, "and made-with-*.svg")
    if not (a.icons or a.media):
        ap.print_help()


if __name__ == "__main__":
    main()
