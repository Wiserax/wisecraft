#!/usr/bin/env python3
"""Draw the README art into docs/media/: the logo, the pipeline, the skills grid, the charts, the terminal.

    python3 scripts/make_art.py --inter /path/to/Inter[opsz,wght].ttf [--terminal out.txt]

Needs fonttools and Pillow. Inter (SIL OFL) is not shipped: get the variable font from
https://github.com/google/fonts/tree/main/ofl/inter . JetBrains Mono comes from wisecraft/fonts/.
Text is converted to outlines, so the SVGs look the same on every machine and in GitHub's image proxy (which
has no web fonts). Every picture is written twice, `-light.svg` and `-dark.svg`, for <picture> in the README.
Numbers in the charts are read from scripts/art_data.json: real measurements with their sources, never typed in here.
"""
import argparse
import json
import math
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "media"
ACCENT = "#FFB020"
THEMES = {
    "light": {"ink": "#0B0B0F", "sub": "#6B6B76", "line": "#E4E4EA", "card": "#F6F6F8", "bg": "#FFFFFF", "muted": "#C9C9D2", "accent": "#F5A300"},
    "dark": {"ink": "#F5F5F7", "sub": "#9A9AA6", "line": "#2A2A33", "card": "#16161C", "bg": "#0B0B0F", "muted": "#4A4A56", "accent": ACCENT},
}
_fonts = {}
INTER = None
MONO = (ROOT / "wisecraft" if (ROOT / "wisecraft").exists() else ROOT / "wisecraft") / "fonts" / "JetBrainsMono-Bold.ttf"


def font(weight):
    """Inter at a weight (a static instance of the variable font), or 'mono'."""
    if weight not in _fonts:
        if weight == "mono":
            f = TTFont(str(MONO))
        else:
            f = instancer.instantiateVariableFont(TTFont(str(INTER)), {"wght": weight, "opsz": 28}, inplace=False)
        _fonts[weight] = (f, f.getGlyphSet(), f.getBestCmap(), f["head"].unitsPerEm)
    return _fonts[weight]


def measure(s, size, weight=500, track=0.0):
    _, glyphs, cmap, upm = font(weight)
    return sum(glyphs[cmap.get(ord(c), ".notdef")].width * size / upm + track for c in s) - (track if s else 0)


def text(s, x, y, size, fill, weight=500, anchor="start", track=0.0):
    """One <path> for a line of text; (x, y) is the baseline at its start, middle or end."""
    _, glyphs, cmap, upm = font(weight)
    k = size / upm
    width = measure(s, size, weight, track)
    cx = x - (width / 2 if anchor == "middle" else width if anchor == "end" else 0)
    d = []
    for c in s:
        g = glyphs[cmap.get(ord(c), ".notdef")]
        pen = SVGPathPen(glyphs, ntos=lambda v: f"{v:.1f}")
        g.draw(TransformPen(pen, (k, 0, 0, -k, cx, y)))
        cmd = pen.getCommands()
        if cmd:
            d.append(cmd)
        cx += g.width * k + track
    return f'<path fill="{fill}" d="{" ".join(d)}"/>'


def svg(w, h, body, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{title}">'
            f"<title>{title}</title>{body}</svg>\n")


def write(name, w, h, draw, title):
    for theme, T in THEMES.items():
        (OUT / f"{name}-{theme}.svg").write_text(svg(w, h, draw(T), title))


# ----------------------------------------------------------------------------------------------- the mark
# A "W" that is also a castle wall: three merlons on top, two points below. One shape, one colour.
MARK = [(8, 10), (30, 10), (30, 27), (39, 27), (39, 10), (61, 10), (61, 27), (70, 27), (70, 10), (92, 10), (92, 54), (71, 90), (50, 58), (29, 90), (8, 54)]


def mark(x, y, s, fill):
    pts = " ".join(f"{x + px * s / 100:.1f},{y + py * s / 100:.1f}" for px, py in MARK)
    return f'<polygon points="{pts}" fill="{fill}" stroke="{fill}" stroke-width="{s * 0.03:.1f}" stroke-linejoin="round"/>'


def hero(T):
    W, H, s = 1200, 260, 124
    size = 118
    ww = measure("wisecraft", size, 700, -3.5)
    x0 = (W - (s + 34 + ww)) / 2
    return mark(x0, (H - s) / 2 - 2, s, T["accent"]) + text("wisecraft", x0 + s + 34, H / 2 + 40, size, T["ink"], 700, track=-3.5)


def logo_png(size, path):
    s = size * 4
    im = Image.new("RGBA", (s, s))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, s - 1, s - 1], radius=int(s * 0.225), fill="#0B0B0F")
    m, o = s * 0.62, s * 0.19
    d.polygon([(o + px * m / 100, o + py * m / 100) for px, py in MARK], fill=ACCENT)
    im.resize((size, size), Image.LANCZOS).save(path)


# ----------------------------------------------------------------------------------------------- icons
# 24 x 24 line icons, stroke only: [("path", d) | ("circle", cx, cy, r)].
ICONS = {
    "recon": [("circle", 10.5, 10.5, 6), ("path", "M15 15 L20.5 20.5")],
    "slice": [("path", "M7 4.5 L19 12 L7 19.5 Z")],
    "economy": [("path", "M3 17 C6 17 6 11 9 11 S12 14 15 9 S18 6 21 5"), ("path", "M3 21 H21")],
    "ui": [("path", "M8 2.5 H16 A2 2 0 0 1 18 4.5 V19.5 A2 2 0 0 1 16 21.5 H8 A2 2 0 0 1 6 19.5 V4.5 A2 2 0 0 1 8 2.5 Z"), ("path", "M10 17.5 H14")],
    "feel": [("path", "M4 10 V14 M8 6.5 V17.5 M12 3 V21 M16 7.5 V16.5 M20 10 V14")],
    "performance": [("path", "M13 2.5 L5 13.5 H11.5 L10.5 21.5 L19 10 H12.5 Z")],
    "qa": [("path", "M3 5.5 H21 V18.5 H3 Z"), ("path", "M8 12 L11 15 L16.5 9")],
    "release": [("path", "M12 16 V3.5 M7 8.5 L12 3.5 L17 8.5"), ("path", "M4 15 V20.5 H20 V15")],
    "trailer": [("path", "M3 5 H21 V19 H3 Z"), ("path", "M10 9 L15.5 12 L10 15 Z")],
    "note": [("path", "M6 3 H14.5 L19 7.5 V21 H6 Z"), ("path", "M9.5 12 H15.5 M9.5 16 H15.5")],
}


def icon(name, cx, cy, size, stroke, width=1.7):
    k = size / 24
    parts = []
    for item in ICONS[name]:
        if item[0] == "circle":
            parts.append(f'<circle cx="{item[1]}" cy="{item[2]}" r="{item[3]}"/>')
        else:
            parts.append(f'<path d="{item[1]}"/>')
    return (f'<g transform="translate({cx - size / 2:.1f},{cy - size / 2:.1f}) scale({k:.3f})" fill="none" stroke="{stroke}" '
            f'stroke-width="{width / k:.2f}" stroke-linecap="round" stroke-linejoin="round">{"".join(parts)}</g>')


STAGES = [("recon", "Recon", "wise scan"), ("slice", "Slice", "one playable loop"), ("economy", "Economy", "player-model bots"),
          ("ui", "UI kit", "one golden CTA"), ("feel", "Feel + audio", "a measured mix"), ("performance", "Performance", "60 fps that holds"),
          ("qa", "Browser QA", "wise qa"), ("release", "Release", "wise publish check"), ("trailer", "Trailer", "wise video compile"),
          ("note", "Field note", "wise kb add")]


def pipeline(T):
    W, H, n = 1600, 250, len(STAGES)
    pad, r = 80, 34
    step = (W - 2 * pad) / (n - 1)
    cy = 84
    out = [f'<path d="M{pad} {cy} H{W - pad}" stroke="{T["line"]}" stroke-width="2"/>']
    for i, (ic, name, hint) in enumerate(STAGES):
        cx = pad + i * step
        last = i == n - 1
        out.append(f'<circle cx="{cx:.1f}" cy="{cy}" r="{r}" fill="{T["accent"] if last else T["bg"]}" stroke="{T["accent"] if last else T["line"]}" stroke-width="2"/>')
        out.append(icon(ic, cx, cy, 30, "#0B0B0F" if last else T["ink"]))
        out.append(text(f"{i + 1:02d}", cx, cy + r + 34, 13, T["accent"], 600, "middle", 0.6))
        out.append(text(name, cx, cy + r + 62, 19, T["ink"], 600, "middle", -0.2))
        mono = hint.startswith("wise ")
        out.append(text(hint, cx, cy + r + 88, 12.5 if mono else 14, T["sub"], "mono" if mono else 400, "middle"))
    return "".join(out)


SKILLS = [("make-web-game", "The loop, the rules, which skill next"), ("web-game-recon", "Stack, saves, hooks, baseline"),
          ("game-economy", "Bots A–D, difficulty index, bosses"), ("game-ui-kit", "Hub, one golden CTA, 320 px"),
          ("game-feel-audio", "Presence beats, a measured mix"), ("game-performance", "Budgets, a guard that recovers"),
          ("browser-qa", "Muted phone bots that tap"), ("release-web-game", "Version, deploy, live checks"),
          ("agent-orchestration", "Lead, workers, file ownership"), ("trailer-video", "Hook in 3 s, slow-motion finale"),
          ("design-boards", "Mockups to PNG boards"), ("share-field-notes", "Search, write, open the PR")]


def skills(T):
    W, cols, gap, pad = 1600, 4, 20, 2
    cw, ch = (W - 2 * pad - (cols - 1) * gap) / cols, 124
    rows = math.ceil(len(SKILLS) / cols)
    out = []
    for i, (name, line) in enumerate(SKILLS):
        r, c = divmod(i, cols)
        x, y = pad + c * (cw + gap), pad + r * (ch + gap)
        first = i == 0
        out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cw:.1f}" height="{ch}" rx="18" fill="{T["card"]}" stroke="{T["accent"] if first else T["line"]}" stroke-width="{2 if first else 1.5}"/>')
        out.append(text(f"{i + 1:02d}", x + 26, y + 38, 13, T["accent"], 600, track=0.6))
        out.append(text(name, x + 26, y + 72, 21, T["ink"], 600, track=-0.3))
        out.append(text(line, x + 26, y + 100, 15, T["sub"], 400))
    return "".join(out), W, pad * 2 + rows * ch + (rows - 1) * gap


# ----------------------------------------------------------------------------------------------- charts
def before_after(T, rows):
    """One row per metric: the label, a 'before' bar, an 'after' bar, both on the metric's own scale."""
    W, pad, rh = 1600, 2, 96
    lx, bx, bw = pad + 8, 560, 800
    out = []
    y = pad + 34
    out.append(text("BEFORE", bx, y, 12.5, T["sub"], 600, track=1.2))
    out.append(f'<rect x="{bx + 74}" y="{y - 10}" width="26" height="10" rx="5" fill="{T["muted"]}"/>')
    out.append(text("AFTER", bx + 130, y, 12.5, T["sub"], 600, track=1.2))
    out.append(f'<rect x="{bx + 190}" y="{y - 10}" width="26" height="10" rx="5" fill="{T["accent"]}"/>')
    y += 26
    for row in rows:
        out.append(f'<path d="M{pad} {y} H{W - pad}" stroke="{T["line"]}" stroke-width="1.5"/>')
        out.append(text(row["label"], lx, y + 42, 21, T["ink"], 600, track=-0.3))
        out.append(text(row["note"], lx, y + 68, 14.5, T["sub"], 400))
        top = max(abs(row["before"]), abs(row["after"]))
        for j, key in enumerate(("before", "after")):
            v = row[key]
            w = max(6, abs(v) / top * (bw - 190))
            yy = y + 24 + j * 30
            out.append(f'<rect x="{bx}" y="{yy}" width="{w:.1f}" height="20" rx="10" fill="{T["accent"] if j else T["muted"]}"/>')
            out.append(text(row[key + "_text"], bx + w + 14, yy + 16, 17, T["ink"] if j else T["sub"], 600 if j else 500))
        out.append(text(row["change"], W - pad - 8, y + 56, 30, T["ink"], 700, "end", -0.8))
        y += rh
    out.append(f'<path d="M{pad} {y} H{W - pad}" stroke="{T["line"]}" stroke-width="1.5"/>')
    return "".join(out), W, y + pad


def benchmark_soon(T):
    W, H = 1600, 220
    out = [f'<rect x="2" y="2" width="{W - 4}" height="{H - 4}" rx="22" fill="{T["card"]}" stroke="{T["line"]}" stroke-width="1.5" stroke-dasharray="6 8"/>',
           text("With vs without Wisecraft", W / 2, 92, 30, T["ink"], 700, "middle", -0.6),
           text("Benchmark: coming soon. The harness is in benchmarks/. No numbers until it has run.", W / 2, 134, 18, T["sub"], 400, "middle")]
    return "".join(out), W, H


# ----------------------------------------------------------------------------------------------- terminal
def terminal(lines):
    """Real command output, drawn as a terminal window (one dark look for both themes)."""
    size, lh, padx, top = 15.5, 25, 34, 66
    cw = measure("M", size, "mono")
    cols = max(60, max((len(l) for l in lines), default=60))
    W = min(1600, round(padx * 2 + cols * cw))
    H = top + len(lines) * lh + 30
    out = [f'<rect width="{W}" height="{H}" rx="18" fill="#0B0B0F" stroke="#2A2A33" stroke-width="1.5"/>',
           '<circle cx="30" cy="30" r="6.5" fill="#3A3A44"/><circle cx="52" cy="30" r="6.5" fill="#3A3A44"/><circle cx="74" cy="30" r="6.5" fill="#3A3A44"/>']
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        prompt = line.startswith("$ ")
        fill = "#F5F5F7" if prompt else "#9A9AA6"
        if any(k in line for k in ("PASS", "clean", '"errors": []', "0 fail")):
            fill = ACCENT
        out.append(text(line[: int((W - 2 * padx) / cw)], padx, top + i * lh, size, fill, "mono"))
    return "".join(out), W, H


def main():
    global INTER
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--inter", required=True, help="path to the Inter variable font (.ttf)")
    ap.add_argument("--terminal", help="a text file with real command output to draw as docs/media/terminal.svg")
    a = ap.parse_args()
    INTER = Path(a.inter)
    OUT.mkdir(parents=True, exist_ok=True)
    data = json.loads((ROOT / "scripts" / "art_data.json").read_text())
    write("logo", 1200, 260, hero, "wisecraft")
    write("pipeline", 1600, 250, pipeline, "The loop: recon, slice, economy, UI kit, feel and audio, performance, browser QA, release, trailer, field note")
    for theme, T in THEMES.items():
        for name, fn, title in (("skills", lambda T: skills(T), "The twelve skills"),
                                ("before-after", lambda T: before_after(T, data["before_after"]), "Before and after, measured on a real project"),
                                ("benchmark", benchmark_soon, "With vs without Wisecraft: benchmark coming soon")):
            if name == "benchmark" and data.get("benchmark"):
                continue
            body, w, h = fn(T)
            (OUT / f"{name}-{theme}.svg").write_text(svg(w, round(h), body, title))
    if a.terminal:
        body, w, h = terminal(Path(a.terminal).read_text().rstrip("\n").split("\n"))
        (OUT / "terminal.svg").write_text(svg(w, h, body, "wise qa and wise publish check, real output"))
    logo_png(512, OUT / "logo.png")
    logo_png(128, OUT / "logo-128.png")
    files = sorted(p for p in OUT.rglob("*") if p.is_file())
    print(f"wrote {len(files)} files, {sum(p.stat().st_size for p in files) / 1e6:.2f} MB in docs/media/")


if __name__ == "__main__":
    main()
