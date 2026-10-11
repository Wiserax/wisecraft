"""Render HTML mockups to phone-sized PNG screens and one review board.

    wise board --init design/pacts                                    # starter mockups.html + board.html
    wise board design/pacts/mockups.html --board design/pacts/board.html
    wise board mockups.html --board board.html --out shots --size 390x844 --scale 2 --ids s1,s3
    wise board mockups.html --dry-run                                 # print the node command, run nothing

Every element with class "screen" and an id in mockups.html (every element with an id when none is marked) is
written to <out>/<id>.png at --scale; then board.html, which shows those shots with captions, is rendered full
page to board.png next to it. --out defaults to shots/ beside the board (beside the mockups without one), which
is where the starter board looks. Screens that are not --size CSS px are listed as warnings.

Needs node and Playwright, found the same way as `wise qa` (--playwright DIR, the current folder, $WISE_PLAYWRIGHT).
Exit 0 rendered, 1 the render failed, 2 usage or a missing tool.
"""
from __future__ import annotations

import argparse
import json
import shlex
import shutil
import sys
from pathlib import Path

from wisecraft.common import JS, die, parse_size
from wisecraft.qa import find_playwright, missing_playwright, need_node, node_command, run_harness

RENDER = JS / "render-board.mjs"
TEMPLATES = {"mockups.html": JS / "mockups-template.html", "board.html": JS / "board-template.html"}


def init(folder: str, force: bool = False) -> list[Path]:
    """Write the starter pair into `folder`; existing files are kept unless forced."""
    d = Path(folder).expanduser()
    existing = [d / name for name in TEMPLATES if (d / name).exists()]
    if existing and not force:
        die(f"{', '.join(map(str, existing))} already exist; pass --force to overwrite, or pick another folder", 1)
    d.mkdir(parents=True, exist_ok=True)
    written = []
    for name, src in TEMPLATES.items():
        (d / name).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        written.append(d / name)
    return written


def options(a) -> dict:
    mockups = Path(a.mockups).expanduser()
    if not mockups.is_file():
        die(f"mockups file not found: {a.mockups} (start one with `wise board --init DIR`)", 2)
    board = Path(a.board).expanduser() if a.board else None
    if board and not board.is_file():
        die(f"board file not found: {a.board} (start one with `wise board --init DIR`)", 2)
    try:
        w, h = parse_size(a.size)
        if w < 1 or h < 1 or a.scale <= 0:
            raise ValueError
    except ValueError:
        die(f"--size wants WIDTHxHEIGHT in CSS px, e.g. 390x844, and --scale a positive number (got {a.size!r}, {a.scale})", 2)
    out = Path(a.out).expanduser() if a.out else (board or mockups).parent / "shots"
    return {"mockups": str(mockups), "out": str(out), "ids": [i for i in (a.ids or "").split(",") if i],
            "board": str(board) if board else None, "width": w, "height": h, "scale": a.scale,
            **({"channel": a.channel} if a.channel else {})}


def main(a):
    if a.init:
        written = init(a.init, a.force)
        if a.json:
            print(json.dumps({"written": [str(p) for p in written]}))
        else:
            print("wrote " + ", ".join(map(str, written)))
            print(f"next: edit the screens, then  wise board {written[0]} --board {written[1]}")
        return
    if not a.mockups:
        die("give the mockups HTML file, or --init DIR for a starter pair", 2)
    opts = options(a)
    node = shutil.which("node") if a.dry_run else need_node()
    pw = find_playwright(node, a.playwright) if node else None
    if a.dry_run:
        print(shlex.join(node_command(RENDER, {**opts, "playwright": pw}, node or "node")))
        if not pw:
            print("wise: " + missing_playwright(a.playwright), file=sys.stderr)
        return
    if not pw:
        die(missing_playwright(a.playwright), 2)
    result, code = run_harness(node_command(RENDER, {**opts, "playwright": pw}, node), timeout=300)
    if code != 0:
        die(f"the render failed (exit {code})", 1)
    if a.json:
        print(json.dumps(result))
    else:
        print(f"rendered {len(result['screens'])} screen(s) at {result['size']} x{result['scale']:g} into {opts['out']}: "
              + ", ".join(s["id"] for s in result["screens"]))
        if result.get("board"):
            print(f"board: {result['board']}")
        for w in result["warnings"]:
            print(f"warning: {w}")
    if not result["screens"]:
        die("no screens were rendered: mockups need elements with an id (class \"screen\")", 1)


def register(sub):
    p = sub.add_parser("board", help="render HTML mockups to phone-sized PNG screens and one review board",
                       description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("mockups", nargs="?", help="HTML file with one element per screen (class \"screen\", an id each)")
    p.add_argument("--board", metavar="HTML", help="board page to render to a PNG next to it, after the screens")
    p.add_argument("--out", metavar="DIR", help="folder for the screen PNGs (default: shots/ beside the board)")
    p.add_argument("--size", default="390x844", help="expected screen size in CSS px (default 390x844)")
    p.add_argument("--scale", type=float, default=2, help="device scale factor of the screen PNGs (default 2)")
    p.add_argument("--ids", metavar="A,B", help="render only these ids (default: every screen)")
    p.add_argument("--init", metavar="DIR", help="write a starter mockups.html + board.html into DIR and stop")
    p.add_argument("--force", action="store_true", help="with --init: overwrite an existing pair")
    p.add_argument("--channel", help="use an installed browser instead of Playwright's Chromium, e.g. chrome")
    p.add_argument("--playwright", metavar="DIR", help="a folder node can load Playwright from (or set WISE_PLAYWRIGHT)")
    p.add_argument("--dry-run", action="store_true", help="print the node command and stop")
    p.add_argument("--json", action="store_true", help="print the result as one JSON line")
    p.set_defaults(func=main)
