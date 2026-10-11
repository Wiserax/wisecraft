#!/usr/bin/env python3
"""Draw the README media in docs/media/: an 8-bit look on a dark ground. The layout is adapted from Universal
Modder's README (MIT): a pixel wordmark, a frame grid, pill badges, 12 x 12 pixel icons, a two-row pipeline.

    python3 scripts/make_media.py --frames DIR --silkscreen Silkscreen-Regular.ttf [--tile tile.png]

Writes banner.png, badges/*.png, icons/*-{dark,light}.svg, pipeline.png, before-after-{dark,light}.png,
benchmark-{dark,light}.png, made-with-{dark,light}.svg and, with --tile, the end tile for the teaser.

--frames holds stills of your own game: boss, horde, titan, vault, blade, clear (.png, 16:9) and qa-1..qa-4
(.png, portrait). They are not in the repo: check each one for titles, logos and names before you use it.
Type is Silkscreen (SIL OFL), drawn at multiples of 8 px with no smoothing, so every pixel stays square.
Numbers come from scripts/art_data.json and benchmarks/results.json; nothing is typed in here.
"""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "media"
GOLD, PINK, CYAN, LIME = "#FFC531", "#FF4FD8", "#3EE6FF", "#8DFF4F"
DARK = {"bg": "#0E0C10", "ink": "#FFFFFF", "muted": "#8E8796", "panel": "#1A171E", "line": "#2A2630", "grey": "#4A4552",
        "bright": [GOLD, PINK, CYAN, LIME]}
LIGHT = {"bg": "#F2ECE2", "ink": "#0E0C10", "muted": "#6E6776", "panel": "#E6DFD3", "line": "#CFC7BA", "grey": "#B9B2BF",
         "bright": ["#E0A400", "#E01FB8", "#00A3C4", "#48B000"]}
BG, INK, MUTED, PANEL, LINE = DARK["bg"], DARK["ink"], DARK["muted"], DARK["panel"], DARK["line"]
FONT = None

# The castle-W of the logo on a pixel grid: three merlons up, two points down (11 x 8 cells).
CASTLE = ([(x, y) for y in (0, 1) for x in (0, 1, 2, 4, 5, 6, 8, 9, 10)] + [(x, y) for y in (2, 3, 4) for x in range(11)]
          + [(x, 5) for x in (0, 1, 2, 3, 4, 6, 7, 8, 9, 10)] + [(x, 6) for x in (1, 2, 3, 7, 8, 9)] + [(2, 7), (8, 7)])


def font(size):
    return ImageFont.truetype(str(FONT), size)


def px(d, xy, s, size, fill, anchor="l"):
    """Silkscreen with no smoothing. Returns the width drawn."""
    s = s.replace("\u2212", "-")  # the font has no true minus sign
    w = d.textlength(s, font=font(size))
    x = xy[0] - (w if anchor == "r" else w / 2 if anchor == "m" else 0)
    d.fontmode = "1"
    d.text((round(x), xy[1]), s, font=font(size), fill=fill)
    d.fontmode = "L"
    return w


def castle(d, x, y, cell, fill=GOLD):
    for cx, cy in CASTLE:
        d.rectangle([x + cx * cell, y + cy * cell, x + (cx + 1) * cell - 1, y + (cy + 1) * cell - 1], fill=fill)


def blocks(d, x, y, w, h, fill, step=16, gap=4):
    """A chunky pixel bar: square-edged blocks on a fixed grid."""
    n = max(1, round(w / step))
    for i in range(n):
        d.rectangle([x + i * step, y, x + i * step + step - gap - 1, y + h - 1], fill=fill)
    return n * step


def fit(im, w, h, box=None):
    """Crop to the box (fractions of the frame: left, top, right, bottom), then cover w x h."""
    im = im.convert("RGB")
    if box:
        W, H = im.size
        im = im.crop((int(box[0] * W), int(box[1] * H), int(box[2] * W), int(box[3] * H)))
    W, H = im.size
    k = max(w / W, h / H)
    im = im.resize((max(w, round(W * k)), max(h, round(H * k))), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


CROPS = {"vault": (0.42, 0.03, 0.92, 0.53), "clear": (0.415, 0.07, 0.915, 0.57)}
TILES = [("boss", "2x boss slam", GOLD), ("horde", "8,000 at 60 fps", CYAN), ("titan", "titan wave", PINK), ("vault", "vault reveal", LIME),
         ("blade", "blade frenzy", PINK), ("clear", "chapter clear", GOLD)]


def banner(frames):
    W, H = 1280, 640
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    castle(d, 70, 86, 4)
    px(d, (128, 84), "wisecraft", 32, INK)
    w = px(d, (68, 196), "ship any game", 48, INK)
    d.rectangle([68 + w + 4, 196 + 40, 68 + w + 15, 196 + 51], fill=PINK)
    for i, line in enumerate(["point any ai coding agent at your", "web game. balance it, polish it,", "test it on real phones, ship it,", "cut the trailer."]):
        px(d, (70, 284 + i * 30), line, 16, MUTED)
    for i, c in enumerate((GOLD, PINK, CYAN, LIME)):
        d.rectangle([70 + i * 20, 440, 70 + i * 20 + 11, 451], fill=c)
    w = px(d, (70, 500), "mit", 16, INK)
    px(d, (70 + w + 20, 500), "github.com/Wiserax/wisecraft", 16, MUTED)
    px(d, (70, 540), "works with any agent that reads agents.md", 16, MUTED)
    tw, th, gap, x0, y0 = 310, 174, 7, 602, 52
    for i, (name, cap, col) in enumerate(TILES):
        x, y = x0 + (i % 2) * (tw + gap), y0 + (i // 2) * (th + gap)
        im.paste(fit(Image.open(frames / f"{name}.png"), tw, th, CROPS.get(name)), (x, y))
        cw = d.textlength(cap, font=font(16))
        d.rectangle([x + 8, y + th - 36, x + 8 + cw + 30, y + th - 8], fill=BG)
        d.rectangle([x + 16, y + th - 26, x + 23, y + th - 19], fill=col)
        px(d, (x + 30, y + th - 33), cap, 16, INK)
    im.save(OUT / "banner.png", optimize=True)


def badge(slug, lead, items, col):
    H, size = 52, 24
    probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    wl, wi = probe.textlength(lead + " ", font=font(size)), probe.textlength(items, font=font(size))
    im = Image.new("RGBA", (round(46 + wl + wi + 22), H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([4, 0, im.width - 5, H - 1], fill=BG)
    d.rectangle([0, 4, im.width - 1, H - 5], fill=BG)
    d.rectangle([20, 20, 31, 31], fill=col)
    px(d, (46, 8), lead, size, MUTED)
    px(d, (46 + wl, 8), items, size, INK)
    (OUT / "badges").mkdir(parents=True, exist_ok=True)
    im.save(OUT / "badges" / f"{slug}.png", optimize=True)


# 12 x 12 pixel icons: (bright colour index, accent path, ink path). scan, video, kb and publish are Universal Modder's.
ICONS = {
    "scan": (0, "M4 3h2v2h-2zM6 5h2v2h-2z", "M0 0h3v1h-3zM9 0h3v1h-3zM0 1h1v2h-1zM11 1h1v2h-1zM0 8h12v1h-12zM0 9h1v2h-1zM11 9h1v2h-1zM0 11h3v1h-3zM9 11h3v1h-3z"),
    "qa": (3, "M4 6h1v1h-1zM5 7h1v1h-1zM6 6h1v1h-1zM7 5h1v1h-1z", "M2 0h8v1h-8zM2 1h1v10h-1zM9 1h1v10h-1zM2 11h8v1h-8zM5 9h2v1h-2z"),
    "board": (2, "M2 2h3v6h-3z", "M0 0h12v1h-12zM0 1h1v10h-1zM11 1h1v10h-1zM0 11h12v1h-12zM6 2h4v2h-4zM6 5h4v3h-4zM2 9h8v1h-8z"),
    "loudness": (1, "M5 1h2v10h-2z", "M1 7h1v4h-1zM3 4h1v7h-1zM8 5h1v6h-1zM10 8h1v3h-1zM0 11h12v1h-12z"),
    "dupframes": (2, "M6 6h4v4h-4z", "M0 0h8v1h-8zM0 1h1v6h-1zM7 1h1v3h-1zM0 7h4v1h-4zM4 4h8v1h-8zM4 5h1v6h-1zM11 5h1v6h-1zM4 11h8v1h-8z"),
    "video": (1, "M4 4h2v1h-2zM4 5h4v1h-4zM4 6h6v1h-6zM4 7h4v1h-4zM4 8h2v1h-2z", "M0 0h12v1h-12zM0 1h1v1h-1zM2 1h1v1h-1zM4 1h1v1h-1zM6 1h1v1h-1zM8 1h1v1h-1zM10 1h2v1h-2zM0 2h12v1h-12zM0 3h1v6h-1zM11 3h1v6h-1zM0 9h12v1h-12zM0 10h1v1h-1zM2 10h1v1h-1zM4 10h1v1h-1zM6 10h1v1h-1zM8 10h1v1h-1zM10 10h2v1h-2zM0 11h12v1h-12z"),
    "kb": (0, "M4 8h2v1h-2zM6 9h2v1h-2z", "M1 0h9v1h-9zM9 1h2v1h-2zM3 2h5v1h-5zM9 2h1v1h-1zM11 2h1v1h-1zM9 3h3v1h-3zM3 4h5v1h-5zM3 6h4v1h-4zM1 1h1v10h-1zM11 4h1v7h-1zM1 11h11v1h-11z"),
    "publish": (3, "M5 0h2v1h-2zM4 1h4v1h-4zM3 2h6v1h-6zM5 3h2v3h-2z", "M0 5h4v1h-4zM8 5h4v1h-4zM3 7h6v1h-6zM0 6h1v5h-1zM11 6h1v5h-1zM0 11h12v1h-12z"),
}


def icons():
    (OUT / "icons").mkdir(parents=True, exist_ok=True)
    for name, (ci, accent, ink) in ICONS.items():
        for theme, T, col in (("dark", DARK, "#F2ECE2"), ("light", LIGHT, "#0E0C10")):
            (OUT / "icons" / f"{name}-{theme}.svg").write_text(
                f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 12 12" width="96" height="96" shape-rendering="crispEdges" role="img" aria-label="wise {name}">'
                f'<path fill="{T["bright"][ci]}" d="{accent}"/><path fill="{col}" d="{ink}"/></svg>\n')


def runs(s, size=8):
    """Pixels of a Silkscreen string at its native size, as (x, y, width) runs; returns (runs, width)."""
    probe = ImageDraw.Draw(Image.new("1", (1, 1)))
    w = int(probe.textlength(s, font=font(size))) + 1
    im = Image.new("1", (w, size + 2), 0)
    d = ImageDraw.Draw(im)
    d.fontmode = "1"
    d.text((0, 0), s, font=font(size), fill=1)
    p, out = im.load(), []
    for y in range(im.height):
        x = 0
        while x < w:
            if p[x, y]:
                x1 = x
                while x1 < w and p[x1, y]:
                    x1 += 1
                out.append((x, y, x1 - x))
                x = x1
            else:
                x += 1
    return out, w


def made_with():
    a, wa = runs("made with")
    b, wb = runs("wisecraft")
    tx = 18
    W, H = tx + wa + 4 + wb + 4, 16
    for theme, bg, ink, muted, gold in (("dark", "#0E0C10", "#F2ECE2", "#8E8796", GOLD), ("light", "#F2ECE2", "#0E0C10", "#5D5765", "#E0A400")):
        path = lambda rs, ox: "".join(f"M{ox + x} {4 + y}h{w}v1h-{w}z" for x, y, w in rs)
        mark = "".join(f"M{4 + cx} {4 + cy}h1v1h-1z" for cx, cy in CASTLE)
        (OUT / f"made-with-{theme}.svg").write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W * 8}" height="{H * 8}" shape-rendering="crispEdges" role="img" aria-label="made with wisecraft">'
            f'<path fill="{bg}" d="M1 0h{W - 2}v{H}h-{W - 2}zM0 1h{W}v{H - 2}h-{W}z"/><path fill="{gold}" d="{mark}"/>'
            f'<path fill="{muted}" d="{path(a, tx)}"/><path fill="{ink}" d="{path(b, tx + wa + 4)}"/></svg>\n')


def card(d, x, y, w, h, caption, dot=None):
    """A panel with notched corners, room for a picture, and a pixel caption on its last line."""
    d.rectangle([x, y, x + w, y + h], fill=PANEL)
    for cx, cy in ((x, y), (x + w - 7, y), (x, y + h - 7), (x + w - 7, y + h - 7)):
        d.rectangle([cx, cy, cx + 7, cy + 7], fill=BG)
    tx = x + 22
    if dot:
        d.rectangle([tx, y + h - 40, tx + 11, y + h - 29], fill=dot)
        tx += 24
    head, _, rest = caption.partition(" ")
    hw = px(d, (tx, y + h - 50), head, 24, INK)
    if rest:
        px(d, (tx + hw + 14, y + h - 50), rest, 24, MUTED)
    return (x + 18, y + 18, w - 36, h - 84)


def arrow(d, x, y, col):
    for i in range(5):
        d.rectangle([x + i * 4, y - (5 - i) * 4, x + i * 4 + 3, y + (5 - i) * 4 - 1], fill=col)


def rows(d, box, items):
    x, y, w, h = box
    d.rectangle([x, y, x + w, y + h], fill=BG)
    lh = 32
    yy = y + (h - len(items) * lh) // 2
    for key, val, col in items:
        px(d, (x + 14, yy), key, 16, MUTED)
        px(d, (x + w - 14, yy), val, 16, col or INK, "r")
        yy += lh


def pipeline(frames, data):
    W, H = 1600, 866
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    ch, x0 = 290, 40
    px(d, (x0, 44), "balance: bots first, then a real phone", 40, INK)
    y = 120
    b = card(d, x0, y, 300, ch, "wise scan")
    rows(d, b, [("engine", "three.js + vite", None), ("versions", "0.180 · 7.3", None), ("hook", "window.__game", CYAN), ("analytics", "/api/events", None), ("audio", "135 files", None)])
    arrow(d, x0 + 320, y + ch // 2, GOLD)
    b = card(d, x0 + 360, y, 300, ch, "bots ×8 seeds")
    rows(d, b, [("walls left", "min – max", None), ("tutorial", "22 – 61 %", None), ("fast tapper", "16 – 52 %", None), ("sieges lost", "0 of 16", LIME)])
    arrow(d, x0 + 680, y + ch // 2, GOLD)
    b = card(d, x0 + 720, y, 800, ch, "wise qa --size 390x844")
    n, gap = 4, 12
    pw = (b[2] - (n - 1) * gap) // n
    for i in range(n):
        im.paste(fit(Image.open(frames / f"qa-{i + 1}.png"), pw, b[3], (0, 0.115, 1, 0.70)), (b[0] + i * (pw + gap), b[1]))
    px(d, (x0, 464), "ship: a measured mix, a smooth trailer", 40, INK)
    y = 540
    boom = next(r for r in data if "boom" in r["label"])
    slow = next(r for r in data if "Slow-motion" in r["label"])
    b = card(d, x0, y, 300, ch, "wise loudness")
    rows(d, b, [("music", "-34.1 to -20.0", None), ("", "lufs", None), ("boss boom", boom["before_text"] + " to", None), ("over music", boom["after_text"], PINK)])
    arrow(d, x0 + 320, y + ch // 2, GOLD)
    b = card(d, x0 + 360, y, 300, ch, "wise dupframes")
    d.rectangle([b[0], b[1], b[0] + b[2], b[1] + b[3]], fill=BG)
    cell, cols = 28, 8
    gx, gy = b[0] + (b[2] - cols * cell) // 2, b[1] + 22
    for i in range(24):
        cx, cy = gx + (i % cols) * cell, gy + (i // cols) * cell
        d.rectangle([cx + 2, cy + 2, cx + cell - 3, cy + cell - 3], fill=CYAN if i < slow["after"] else DARK["grey"])
    px(d, (b[0] + b[2] // 2, gy + 3 * cell + 14), f"{slow['after_text']} frames move", 16, INK, "m")
    px(d, (b[0] + b[2] // 2, gy + 3 * cell + 40), f"was {slow['before_text']}", 16, MUTED, "m")
    arrow(d, x0 + 680, y + ch // 2, GOLD)
    b = card(d, x0 + 720, y, 400, ch, "wise video compile")
    im.paste(fit(Image.open(frames / "titan.png"), b[2], b[3]), (b[0], b[1]))
    arrow(d, x0 + 1140, y + ch // 2, GOLD)
    b = card(d, x0 + 1180, y, 340, ch, "8,000 at 60 fps", dot=LIME)
    im.paste(fit(Image.open(frames / "horde.png"), b[2], b[3]), (b[0], b[1]))
    im.save(OUT / "pipeline.png", optimize=True)


def before_after(data, T, name):
    W, rh, pad = 1600, 112, 40
    H = pad * 2 + 56 + len(data) * rh
    im = Image.new("RGB", (W, H), T["bg"])
    d = ImageDraw.Draw(im)
    bx, bw = 740, 440
    y = pad
    px(d, (pad, y), "measured on the shipped game", 16, T["muted"])
    blocks(d, bx, y + 2, 48, 16, T["grey"])
    px(d, (bx + 60, y), "before", 16, T["muted"])
    for i, c in enumerate(T["bright"][:3]):
        d.rectangle([bx + 200 + i * 16, y + 2, bx + 200 + i * 16 + 11, y + 17], fill=c)
    px(d, (bx + 260, y), "after", 16, T["muted"])
    y += 56
    for i, r in enumerate(data):
        col = T["bright"][i % 4]
        d.rectangle([pad, y, W - pad, y + 3], fill=T["line"])
        px(d, (pad, y + 20), r["label"], 24, T["ink"])
        px(d, (pad, y + 62), r["note"], 16, T["muted"])
        top = max(abs(r["before"]), abs(r["after"]))
        for j, key in enumerate(("before", "after")):
            w = max(16, abs(r[key]) / top * bw)
            yy = y + 22 + j * 40
            w = blocks(d, bx, yy, w, 28, col if j else T["grey"])
            px(d, (bx + w + 12, yy - 2), r[key + "_text"], 24, T["ink"] if j else T["muted"])
        px(d, (W - pad, y + 34), r["change"], 32, col, "r")
        y += rh
    d.rectangle([pad, y, W - pad, y + 3], fill=T["line"])
    im.save(OUT / f"{name}.png", optimize=True)


def benchmark(R, T, name):
    """With vs without, from benchmarks/results.json: share of checks passed, minutes, tokens; mean, sd and n per arm."""
    W, H, pad, gap = 1600, 380, 40, 32
    im = Image.new("RGB", (W, H), T["bg"])
    d = ImageDraw.Draw(im)
    S, pw = R["summary"], (W - 2 * pad - 2 * gap) // 3
    tok = lambda v: f"{v / 1e6:.2f} M" if v >= 1e6 else f"{v / 1e3:.0f} K"
    panels = [("checks passed", "pass_rate", lambda v: f"{v * 100:.0f}%", lambda v: f"± {v * 100:.0f}"),
              ("minutes per task", "minutes", lambda v: f"{v:.1f}", lambda v: f"± {v:.1f}"),
              ("tokens per task", "tokens", tok, lambda v: "± " + tok(v))]
    px(d, (pad, pad), f"with vs without wisecraft · {R['meta']['runs']} runs on 3 toy tasks", 16, T["muted"])
    for i, (title, key, fmt, fsd) in enumerate(panels):
        x, y = pad + i * (pw + gap), pad + 44
        col = T["bright"][i]
        d.rectangle([x, y, x + pw, y + 3], fill=T["line"])
        px(d, (x, y + 20), title, 24, T["ink"])
        cells = [(arm, S[arm][key]) for arm in ("without", "with")]
        top = max(c["mean"] for _, c in cells)
        for j, (arm, c) in enumerate(cells):
            yy = y + 70 + j * 104
            px(d, (x, yy), "with wisecraft" if arm == "with" else "without", 16, T["muted"])
            w = blocks(d, x, yy + 28, max(16, c["mean"] / top * (pw - 200)), 28, col if arm == "with" else T["grey"])
            px(d, (x + w + 12, yy + 26), fmt(c["mean"]), 24, T["ink"])
            px(d, (x, yy + 66), f"{fsd(c['sd'])}   n = {c['n']}", 16, T["muted"])
    im.save(OUT / f"{name}.png", optimize=True)


def tile(path):
    im = Image.new("RGB", (560, 315), BG)
    d = ImageDraw.Draw(im)
    w = d.textlength("wisecraft", font=font(40))
    x = round((560 - (55 + 16 + w)) / 2)
    castle(d, x, 126, 5)
    px(d, (x + 71, 122), "wisecraft", 40, INK)
    px(d, (280, 196), "the game studio in a skill", 16, MUTED, "m")
    for i, c in enumerate((GOLD, PINK, CYAN, LIME)):
        d.rectangle([250 + i * 16, 236, 250 + i * 16 + 11, 247], fill=c)
    im.save(path)


def main():
    global FONT
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--frames", required=True)
    ap.add_argument("--silkscreen", required=True)
    ap.add_argument("--tile", help="also write the 560x315 end tile for the teaser to this path")
    a = ap.parse_args()
    FONT = Path(a.silkscreen)
    frames = Path(a.frames)
    data = json.loads((ROOT / "scripts" / "art_data.json").read_text())["before_after"]
    results = json.loads((ROOT / "benchmarks" / "results.json").read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    banner(frames)
    badge("agents", "works with", "claude code · codex · cursor · gemini · copilot · opencode", GOLD)
    badge("knowledge", "knowledge base:", "field notes by agents, for agents", CYAN)
    badge("license", "license:", "mit", LIME)
    icons()
    made_with()
    pipeline(frames, data)
    for theme, T in (("dark", DARK), ("light", LIGHT)):
        before_after(data, T, f"before-after-{theme}")
        benchmark(results, T, f"benchmark-{theme}")
    if a.tile:
        tile(a.tile)
    files = sorted(p for p in OUT.rglob("*") if p.is_file())
    print(f"{len(files)} files, {sum(p.stat().st_size for p in files) / 1e6:.2f} MB in docs/media/")


if __name__ == "__main__":
    main()
