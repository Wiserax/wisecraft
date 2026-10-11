#!/usr/bin/env python3
"""Draw the README media in docs/media/. The look is adapted from Universal Modder's README (MIT): a dark
ground, a pixel wordmark, mono captions, one accent colour.

    python3 scripts/make_media.py --frames DIR --silkscreen Silkscreen-Regular.ttf --mono-dir ~/Library/Fonts

Writes banner.png, badges/*.png, icons/*-{dark,light}.svg, pipeline.png, before-after.png,
made-with-{dark,light}.svg, logo.png, logo-128.png and (with --tile) the end tile for the teaser.

--frames holds stills of your own game, named boss, horde, titan, vault, blade, clear (.png) and qa-1..qa-4
(.png, portrait). They are not in the repo: check each one for titles, logos and names before you use it.
Fonts: Silkscreen and JetBrains Mono (SIL OFL) are read from the paths given; Space Grotesk ships in wisecraft/fonts.
Numbers on the charts come from scripts/art_data.json, each with its source.
"""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "media"
BG, INK, MUTED, PANEL, LINE, ACCENT = "#0E0C10", "#F2ECE2", "#8E8796", "#1A171E", "#2A2630", "#FFC531"
F = {}

# The mark: a pixel "W" in a frame with an accent block on its corner (9 x 9 cells, the block sticks out by one).
MARK_FRAME = [(x, y) for x in range(9) for y in range(9) if x in (0, 8) or y in (0, 8)]
MARK_W = [(2, 2), (2, 3), (2, 4), (2, 5), (2, 6), (6, 2), (6, 3), (6, 4), (6, 5), (6, 6), (4, 4), (3, 5), (5, 5), (4, 5)]
MARK_DOT = [(8, -1), (9, -1), (8, 0), (9, 0)]


def font(kind, size):
    return ImageFont.truetype(str(F[kind]), size)


def mark(d, x, y, cell, ink=INK):
    for cells, fill in ((MARK_FRAME, ink), (MARK_W, ACCENT), (MARK_DOT, ACCENT)):
        for cx, cy in cells:
            d.rectangle([x + cx * cell, y + cy * cell, x + (cx + 1) * cell - 1, y + (cy + 1) * cell - 1], fill=fill)


def pixel(d, xy, s, size, fill):
    """Silkscreen at a multiple of 8 px, drawn without smoothing so every pixel stays square."""
    d.fontmode = "1"
    d.text(xy, s, font=font("pixel", size), fill=fill)
    w = d.textlength(s, font=font("pixel", size))
    d.fontmode = "L"
    return w


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


def chip(d, x, y, s, size=12):
    f = font("mono", size)
    w = d.textlength(s, font=f)
    d.rectangle([x, y - size - 9, x + w + 14, y], fill=BG)
    d.text((x + 7, y - size - 6), s, font=f, fill=INK)


CROPS = {"vault": (0.42, 0.03, 0.92, 0.53), "clear": (0.415, 0.07, 0.915, 0.57)}
TILES = [("boss", "2x boss slam"), ("horde", "8,000 at 60 fps"), ("titan", "titan wave"), ("vault", "vault reveal"), ("blade", "blade frenzy"), ("clear", "chapter clear")]


def banner(frames):
    W, H = 1280, 640
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    mark(d, 70, 90, 3)
    pixel(d, (114, 84), "wisecraft", 32, INK)
    w = pixel(d, (68, 196), "ship any game", 48, INK)
    d.rectangle([68 + w + 4, 196 + 40, 68 + w + 15, 196 + 51], fill=ACCENT)
    f = font("sans", 22)
    for i, line in enumerate(["point any ai coding agent at your web game.", "balance it, polish it, test it on real phones,", "ship it, cut the trailer."]):
        d.text((70, 290 + i * 32), line, font=f, fill=MUTED)
    d.text((70, 503), "mit", font=font("monob", 15), fill=INK)
    d.text((120, 503), "github.com/Wiserax/wisecraft", font=font("mono", 15), fill=MUTED)
    d.text((70, 544), "works with any agent that reads agents.md", font=font("mono", 15), fill=MUTED)
    tw, th, gap, x0, y0 = 310, 174, 7, 602, 52
    for i, (name, cap) in enumerate(TILES):
        x, y = x0 + (i % 2) * (tw + gap), y0 + (i // 2) * (th + gap)
        im.paste(fit(Image.open(frames / f"{name}.png"), tw, th, CROPS.get(name)), (x, y))
        chip(d, x + 8, y + th - 8, cap)
    im.save(OUT / "banner.png", optimize=True)


def badge(slug, lead, items):
    f, H = font("mono", 26), 52
    probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    w = 50 + probe.textlength(lead + " ", font=f) + probe.textlength(items, font=f) + 22
    im = Image.new("RGBA", (round(w), H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, im.width - 1, H - 1], radius=7, fill=BG, outline=LINE, width=2)
    d.rectangle([20, 20, 31, 31], fill=ACCENT)
    d.text((44, 9), lead, font=f, fill=MUTED)
    d.text((44 + d.textlength(lead + " ", font=f), 9), items, font=f, fill=INK)
    (OUT / "badges").mkdir(parents=True, exist_ok=True)
    im.save(OUT / "badges" / f"{slug}.png", optimize=True)


# 12 x 12 pixel icons, two colours: (accent path, ink path). scan, video, kb and publish are Universal Modder's.
ICONS = {
    "scan": ("M4 3h2v2h-2zM6 5h2v2h-2z", "M0 0h3v1h-3zM9 0h3v1h-3zM0 1h1v2h-1zM11 1h1v2h-1zM0 8h12v1h-12zM0 9h1v2h-1zM11 9h1v2h-1zM0 11h3v1h-3zM9 11h3v1h-3z"),
    "qa": ("M4 6h1v1h-1zM5 7h1v1h-1zM6 6h1v1h-1zM7 5h1v1h-1z", "M2 0h8v1h-8zM2 1h1v10h-1zM9 1h1v10h-1zM2 11h8v1h-8zM5 9h2v1h-2z"),
    "board": ("M2 2h3v6h-3z", "M0 0h12v1h-12zM0 1h1v10h-1zM11 1h1v10h-1zM0 11h12v1h-12zM6 2h4v2h-4zM6 5h4v3h-4zM2 9h8v1h-8z"),
    "loudness": ("M5 1h2v10h-2z", "M1 7h1v4h-1zM3 4h1v7h-1zM8 5h1v6h-1zM10 8h1v3h-1zM0 11h12v1h-12z"),
    "dupframes": ("M6 6h4v4h-4z", "M0 0h8v1h-8zM0 1h1v6h-1zM7 1h1v3h-1zM0 7h4v1h-4zM4 4h8v1h-8zM4 5h1v6h-1zM11 5h1v6h-1zM4 11h8v1h-8z"),
    "video": ("M4 4h2v1h-2zM4 5h4v1h-4zM4 6h6v1h-6zM4 7h4v1h-4zM4 8h2v1h-2z", "M0 0h12v1h-12zM0 1h1v1h-1zM2 1h1v1h-1zM4 1h1v1h-1zM6 1h1v1h-1zM8 1h1v1h-1zM10 1h2v1h-2zM0 2h12v1h-12zM0 3h1v6h-1zM11 3h1v6h-1zM0 9h12v1h-12zM0 10h1v1h-1zM2 10h1v1h-1zM4 10h1v1h-1zM6 10h1v1h-1zM8 10h1v1h-1zM10 10h2v1h-2zM0 11h12v1h-12z"),
    "kb": ("M4 8h2v1h-2zM6 9h2v1h-2z", "M1 0h9v1h-9zM9 1h2v1h-2zM3 2h5v1h-5zM9 2h1v1h-1zM11 2h1v1h-1zM9 3h3v1h-3zM3 4h5v1h-5zM3 6h4v1h-4zM1 1h1v10h-1zM11 4h1v7h-1zM1 11h11v1h-11z"),
    "publish": ("M5 0h2v1h-2zM4 1h4v1h-4zM3 2h6v1h-6zM5 3h2v3h-2z", "M0 5h4v1h-4zM8 5h4v1h-4zM3 7h6v1h-6zM0 6h1v5h-1zM11 6h1v5h-1zM0 11h12v1h-12z"),
}


def icons():
    (OUT / "icons").mkdir(parents=True, exist_ok=True)
    for name, (accent, ink) in ICONS.items():
        for theme, col in (("dark", INK), ("light", BG)):
            a = "#E0A400" if theme == "light" else ACCENT
            (OUT / "icons" / f"{name}-{theme}.svg").write_text(
                f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 12 12" width="96" height="96" shape-rendering="crispEdges" role="img" aria-label="wise {name}">'
                f'<path fill="{a}" d="{accent}"/><path fill="{col}" d="{ink}"/></svg>\n')


def runs(s, size=8):
    """Pixels of a Silkscreen string at its native size, as SVG path rectangles; returns (path, width)."""
    f = font("pixel", size)
    probe = ImageDraw.Draw(Image.new("1", (1, 1)))
    w = int(probe.textlength(s, font=f)) + 1
    im = Image.new("1", (w, size + 2), 0)
    d = ImageDraw.Draw(im)
    d.fontmode = "1"
    d.text((0, 0), s, font=f, fill=1)
    px, out = im.load(), []
    for y in range(im.height):
        x = 0
        while x < w:
            if px[x, y]:
                x1 = x
                while x1 < w and px[x1, y]:
                    x1 += 1
                out.append((x, y, x1 - x))
                x = x1
            else:
                x += 1
    return out, w


def made_with():
    a, wa = runs("made with")
    b, wb = runs("wisecraft")
    W, H, tx = 16 + wa + 4 + wb + 5, 16, 16
    for theme, bg, ink, muted in (("dark", BG, INK, MUTED), ("light", INK, BG, "#5D5765")):
        path = lambda rs, ox: "".join(f"M{ox + x} {4 + y}h{w}v1h-{w}z" for x, y, w in rs)
        cells = lambda cs, k=1: "".join(f"M{3 + cx} {4 + cy}h1v1h-1z" for cx, cy in cs)
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W * 8}" height="{H * 8}" shape-rendering="crispEdges" role="img" aria-label="made with wisecraft">'
               f'<path fill="{bg}" d="M1 0h{W - 2}v{H}h-{W - 2}zM0 1h{W}v{H - 2}h-{W}z"/>'
               f'<path fill="{ink}" d="{cells(MARK_FRAME)}"/><path fill="{ACCENT if theme == "dark" else "#E0A400"}" d="{cells(MARK_W)}{cells(MARK_DOT)}"/>'
               f'<path fill="{muted}" d="{path(a, tx)}"/><path fill="{ink}" d="{path(b, tx + wa + 4)}"/></svg>\n')
        (OUT / f"made-with-{theme}.svg").write_text(svg)


def card(im, d, x, y, w, h, caption, dot=False):
    """A panel with notched corners, room for a picture, and a mono caption on its last line."""
    d.rectangle([x, y, x + w, y + h], fill=PANEL)
    for cx, cy in ((x, y), (x + w - 7, y), (x, y + h - 7), (x + w - 7, y + h - 7)):
        d.rectangle([cx, cy, cx + 7, cy + 7], fill=BG)
    f, tx = font("mono", 22), x + 22
    if dot:
        d.rectangle([tx, y + h - 37, tx + 10, y + h - 27], fill=ACCENT)
        tx += 22
    head, _, rest = caption.partition(" ")
    d.text((tx, y + h - 46), head, font=f, fill=INK)
    d.text((tx + d.textlength(head + " ", font=f), y + h - 46), rest, font=f, fill=MUTED)
    return (x + 18, y + 18, w - 36, h - 78)


def arrow(d, x, y):
    for i in range(10):
        d.rectangle([x + i * 2, y - (10 - i) * 2, x + i * 2 + 1, y + (10 - i) * 2], fill="#5D5765")


def lines(d, box, rows, size=17):
    x, y, w, h = box
    d.rectangle([x, y, x + w, y + h], fill=BG)
    lh = size + 12
    yy = y + (h - len(rows) * lh) // 2 + 2
    for key, val, hot in rows:
        d.text((x + 16, yy), key, font=font("mono", size), fill=MUTED)
        d.text((x + w - 16 - d.textlength(val, font=font("monob", size)), yy), val, font=font("monob", size), fill=ACCENT if hot else INK)
        yy += lh


def pipeline(frames, data):
    W, H = 1600, 866
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    ch, x0 = 290, 40
    # row 1
    pixel(d, (x0, 44), "balance: bots first, then a real phone", 40, INK)
    y = 120
    b = card(im, d, x0, y, 300, ch, "wise scan")
    lines(d, b, [("engine", "three.js + vite", False), ("versions", "0.180 · 7.3", False), ("hook", "window.__game", True), ("analytics", "/api/events", False), ("audio", "135 files, 9.0 MB", False)], 15)
    arrow(d, x0 + 320, y + ch // 2)
    b = card(im, d, x0 + 360, y, 300, ch, "bots · 8 seeds each")
    lines(d, b, [("walls left", "min – max", False), ("tutorial", "22 – 61 %", False), ("fast tapper", "16 – 52 %", False), ("sieges lost", "0 of 16", True)], 15)
    arrow(d, x0 + 680, y + ch // 2)
    b = card(im, d, x0 + 720, y, 800, ch, "wise qa --size 390x844  (walks in, hits the wall)")
    n, gap = 4, 12
    pw = (b[2] - (n - 1) * gap) // n
    for i in range(n):
        im.paste(fit(Image.open(frames / f"qa-{i + 1}.png"), pw, b[3], (0, 0.115, 1, 0.70)), (b[0] + i * (pw + gap), b[1]))
    # row 2
    pixel(d, (x0, 464), "ship: a measured mix, a smooth trailer", 40, INK)
    y = 540
    rows = {r["skill"] + r["label"]: r for r in data}
    boom = next(r for r in data if "boom" in r["label"])
    slow = next(r for r in data if "Slow-motion" in r["label"])
    b = card(im, d, x0, y, 300, ch, "wise loudness")
    lines(d, b, [("music", "-34.1 → -20.0", False), ("", "LUFS", False), ("boss boom", f"{boom['before_text'].replace(' dB', '')} → {boom['after_text'].replace(' dB', '').replace('−', '-')}", True), ("", "dB over music", False)], 15)
    arrow(d, x0 + 320, y + ch // 2)
    b = card(im, d, x0 + 360, y, 300, ch, "wise dupframes")
    d.rectangle([b[0], b[1], b[0] + b[2], b[1] + b[3]], fill=BG)
    cell, cols = 26, 8
    gx, gy = b[0] + (b[2] - cols * cell) // 2, b[1] + 26
    for i in range(24):
        cx, cy = gx + (i % cols) * cell, gy + (i // cols) * cell
        d.rectangle([cx + 2, cy + 2, cx + cell - 3, cy + cell - 3], fill=ACCENT if i < slow["after"] else "#3A3540")
    t = f"{slow['after_text']} frames move"
    d.text((b[0] + (b[2] - d.textlength(t, font=font("mono", 15))) // 2, gy + 3 * cell + 16), t, font=font("mono", 15), fill=MUTED)
    t = f"was {slow['before_text']}"
    d.text((b[0] + (b[2] - d.textlength(t, font=font("mono", 15))) // 2, gy + 3 * cell + 40), t, font=font("mono", 15), fill=MUTED)
    arrow(d, x0 + 680, y + ch // 2)
    b = card(im, d, x0 + 720, y, 400, ch, "wise video compile")
    im.paste(fit(Image.open(frames / "titan.png"), b[2], b[3]), (b[0], b[1]))
    arrow(d, x0 + 1140, y + ch // 2)
    b = card(im, d, x0 + 1180, y, 340, ch, "live: 8,000 at 60 fps", dot=True)
    im.paste(fit(Image.open(frames / "horde.png"), b[2], b[3]), (b[0], b[1]))
    im.save(OUT / "pipeline.png", optimize=True)


def before_after(data):
    W, rh, pad = 1600, 92, 40
    H = pad * 2 + 54 + len(data) * rh
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W - 1, H - 1], outline=LINE, width=2)
    bx, bw = 640, 650
    y = pad
    d.text((pad, y), "measured on the shipped game", font=font("mono", 17), fill=MUTED)
    d.rectangle([bx, y + 5, bx + 26, y + 15], fill="#3A3540")
    d.text((bx + 38, y), "before", font=font("mono", 17), fill=MUTED)
    d.rectangle([bx + 150, y + 5, bx + 176, y + 15], fill=ACCENT)
    d.text((bx + 188, y), "after", font=font("mono", 17), fill=MUTED)
    y += 54
    for r in data:
        d.line([pad, y, W - pad, y], fill=LINE, width=2)
        d.text((pad, y + 18), r["label"].lower(), font=font("monob", 20), fill=INK)
        d.text((pad, y + 50), r["note"], font=font("mono", 14), fill=MUTED)
        top = max(abs(r["before"]), abs(r["after"]))
        for j, key in enumerate(("before", "after")):
            w = max(8, abs(r[key]) / top * (bw - 170))
            yy = y + 20 + j * 30
            d.rectangle([bx, yy, bx + w, yy + 18], fill=ACCENT if j else "#3A3540")
            d.text((bx + w + 14, yy - 2), r[key + "_text"].replace("−", "-"), font=font("monob" if j else "mono", 17), fill=INK if j else MUTED)
        t = r["change"].replace("−", "-")
        d.text((W - pad - d.textlength(t, font=font("monob", 28)), y + 26), t, font=font("monob", 28), fill=ACCENT)
        y += rh
    im.save(OUT / "before-after.png", optimize=True)


def logo(size):
    cell = 40
    im = Image.new("RGB", (cell * 12, cell * 12), BG)
    mark(ImageDraw.Draw(im), cell, int(cell * 1.5), cell)
    im.resize((size, size), Image.NEAREST if size >= 480 else Image.LANCZOS).save(OUT / ("logo.png" if size == 512 else f"logo-{size}.png"), optimize=True)


def tile(path):
    im = Image.new("RGB", (560, 315), BG)
    d = ImageDraw.Draw(im)
    w = d.textlength("wisecraft", font=font("pixel", 40))
    x = (560 - (40 + 16 + w)) // 2
    mark(d, x, 128, 4)
    pixel(d, (x + 56, 124), "wisecraft", 40, INK)
    t = "the game studio in a skill"
    d.text(((560 - d.textlength(t, font=font("mono", 15))) // 2, 196), t, font=font("mono", 15), fill=MUTED)
    im.save(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--frames", required=True)
    ap.add_argument("--silkscreen", required=True)
    ap.add_argument("--mono-dir", required=True, help="folder with JetBrainsMono-Regular.ttf and JetBrainsMono-Bold.ttf")
    ap.add_argument("--tile", help="also write the 560x315 end tile for the teaser to this path")
    a = ap.parse_args()
    mono = Path(a.mono_dir).expanduser()
    F.update(pixel=Path(a.silkscreen), mono=mono / "JetBrainsMono-Regular.ttf", monob=mono / "JetBrainsMono-Bold.ttf",
             sans=ROOT / "wisecraft" / "fonts" / "SpaceGrotesk-Medium.ttf")
    frames = Path(a.frames)
    data = json.loads((ROOT / "scripts" / "art_data.json").read_text())["before_after"]
    OUT.mkdir(parents=True, exist_ok=True)
    banner(frames)
    badge("agents", "works with", "claude code · codex · cursor · gemini · copilot · opencode")
    badge("knowledge", "knowledge base:", "field notes by agents, for agents")
    badge("license", "license:", "mit")
    icons()
    made_with()
    pipeline(frames, data)
    before_after(data)
    logo(512)
    logo(128)
    if a.tile:
        tile(a.tile)
    files = sorted(p for p in OUT.rglob("*") if p.is_file())
    print(f"{len(files)} files, {sum(p.stat().st_size for p in files) / 1e6:.2f} MB in docs/media/")


if __name__ == "__main__":
    main()
