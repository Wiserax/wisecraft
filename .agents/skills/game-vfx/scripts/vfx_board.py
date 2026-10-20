#!/usr/bin/env python3
"""A comparison board for one effect: the references on top, our captured frames below, each with its
silhouette (the squint test) and four value bands sampled from its saturated pixels.

    uv run --with pillow python3 vfx_board.py --refs refs/poison/*.png --ours shots/poison/*.png \\
        --out shots/poison/board.png --title "poison cloud, round 2"

The silhouette is every pixel that differs from the image's border colour: if the effect does not read as a
shape there, it will not read on a phone. The bands print as hex, darkest first, so a palette can be checked
against the style rules without eyeballing. Nothing is uploaded; the board is a local PNG.
"""
import argparse
import colorsys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

CELL = 300  # a tile is at most this wide and tall, its silhouette sits under it
LABEL = 22


def pixels(im):
    return list(im.get_flattened_data() if hasattr(im, "get_flattened_data") else im.getdata())


def border_colour(im):
    w, h = im.size
    edge = [im.getpixel((x, y)) for x in range(0, w, max(1, w // 40)) for y in (0, h - 1)]
    edge += [im.getpixel((x, y)) for y in range(0, h, max(1, h // 40)) for x in (0, w - 1)]
    return tuple(sorted(c[i] for c in edge)[len(edge) // 2] for i in range(3))


def silhouette(im):
    bg = border_colour(im)
    mask = Image.new("L", im.size)
    mask.putdata([255 if sum(abs(p[i] - bg[i]) for i in range(3)) > 60 else 0 for p in pixels(im)])
    return mask.filter(ImageFilter.MedianFilter(3))


def bands(im):
    px = [p for p in pixels(im) if max(p) > 40 and colorsys.rgb_to_hsv(*[c / 255 for c in p])[1] > 0.45]
    if len(px) < 50:
        return []
    px.sort(key=lambda p: 0.2126 * p[0] + 0.7152 * p[1] + 0.0722 * p[2])
    return [px[int(len(px) * f)] for f in (0.05, 0.35, 0.65, 0.97)]


def tile(path):
    im = Image.open(path).convert("RGB")
    im.thumbnail((CELL, CELL))
    sil = silhouette(im)
    out = Image.new("RGB", (CELL, im.height * 2 + LABEL + 18), "#101216")
    x = (CELL - im.width) // 2
    out.paste(im, (x, LABEL))
    out.paste(Image.composite(Image.new("RGB", im.size, "#f2f2f2"), Image.new("RGB", im.size, "#000000"), sil),
              (x, LABEL + im.height + 2))
    d = ImageDraw.Draw(out)
    d.text((4, 4), Path(path).name[:44], fill="#c8ccd4")
    b = bands(im)
    for i, c in enumerate(b):
        d.rectangle((4 + i * 40, out.height - 13, 40 + i * 40, out.height - 3), fill=c)
    return out, b


def row(paths, name):
    tiles = []
    for p in paths:
        t, b = tile(p)
        print(f"{name:4s} {Path(p).name}: bands " + (" ".join("#%02x%02x%02x" % c for c in b) or "(too few saturated pixels)"))
        tiles.append(t)
    return tiles


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--refs", nargs="+", required=True, help="reference images")
    ap.add_argument("--ours", nargs="*", default=[], help="our captured frames (anticipation, impact, peak, dissipation)")
    ap.add_argument("--out", required=True, help="the board PNG to write")
    ap.add_argument("--title", default="", help="a line at the top")
    a = ap.parse_args()
    rows = [("refs", row(a.refs, "ref"))] + ([("ours", row(a.ours, "ours"))] if a.ours else [])
    cols = max(len(r) for _, r in rows)
    heights = [max(t.height for t in tiles) for _, tiles in rows]
    board = Image.new("RGB", (60 + cols * (CELL + 8), 34 + sum(h + 8 for h in heights)), "#0b0c0f")
    d = ImageDraw.Draw(board)
    d.text((10, 10), a.title or "vfx board", fill="#ffffff")
    y = 34
    for (name, tiles), h in zip(rows, heights):
        d.text((10, y + h // 2), name, fill="#8b93a3")
        for c, t in enumerate(tiles):
            board.paste(t, (60 + c * (CELL + 8), y))
        y += h + 8
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    board.save(a.out)
    print(f"board: {a.out}")


if __name__ == "__main__":
    main()
