"""Virtual testers for a web game: a muted phone-sized browser that plays like a player and reports what broke.

    wise qa http://127.0.0.1:5173/play.html                        # Chromium 390x844, 20 s of a casual player, the gate
    wise qa http://127.0.0.1:5173 --engine webkit --size 320x568   # the small-phone WebKit pass
    wise qa http://127.0.0.1:5173 --persona spender --seconds 60   # buys whatever in-game currency allows
    wise qa http://127.0.0.1:5173 --persona tapper --max-p95 20    # taps fast; fails when p95 frame time > 20 ms
    wise qa https://example.com/play.html --ready "window.__game" --start-selector "#play" --selector "#shop" "#close" --json
    wise qa http://127.0.0.1:5173 --dry-run                        # print the node command, run nothing

The browser never makes sound (Chromium --mute-audio; WebKit gets a zero-gain AudioContext destination).
Every request goes through to the real servers, analytics included; --block PATTERN is an opt-in that answers
matching requests itself with an empty 200 instead (nothing is blocked by default).
Personas: casual (2 taps a second, buys nothing; the default), tapper (5 a second), idler (a tap every 5 s: idle
timers and piles that grow unattended), spender (every other action taps a visible buy / upgrade / claim / open
control, least-tapped first; --buy CSS picks the controls). No persona ever taps a control that shows a real-money
price or says pay, purchase or subscribe: spending real money needs a person's yes.
The gate: no console or page errors and no horizontal overflow (and, with --max-p95, the frame-time limit). Exit 0
pass, 1 gate failed, 2 usage or a missing tool (node, Playwright, a browser). Screenshots (start, each step, middle,
end) and board.png, all of them on one sheet, land in ./qa-out/<engine>-<WxH>-<persona>/. Frame times come from
requestAnimationFrame in a headless browser: compare builds on one machine with them, don't quote them as phone fps.

Playwright is looked up in --playwright DIR, then the current folder, then $WISE_PLAYWRIGHT. Without it:
    npm i -D playwright && npx playwright install chromium webkit
"""
from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

from wisecraft.common import JS, die, parse_size

INSTALL = "npm i -D playwright && npx playwright install chromium webkit"
HARNESS = JS / "qa-harness.mjs"
PACKAGES = ("playwright", "@playwright/test", "playwright-core")
RESOLVE = ("const names=%s;for(const n of names){try{process.stdout.write(require.resolve(n,{paths:[process.argv[1]]}));"
           "process.exit(0)}catch(e){}}process.exit(3)") % json.dumps(list(PACKAGES))


def need_node() -> str:
    return shutil.which("node") or die("node not found on PATH: install Node.js 18 or newer (https://nodejs.org)", 2)


def _resolve(node: str, base: str) -> str | None:
    """The entry file of a Playwright package that node can load from `base` (a project, node_modules or package folder)."""
    try:
        p = subprocess.run([node, "-e", RESOLVE, str(Path(base).expanduser().resolve())], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return p.stdout.strip() if p.returncode == 0 and p.stdout.strip() else None


def find_playwright(node: str, explicit: str | None = None, cwd: str | None = None) -> str | None:
    """Where Playwright lives: --playwright DIR, then the current folder, then $WISE_PLAYWRIGHT. None when nowhere."""
    if explicit:
        return _resolve(node, explicit)      # an explicit folder is the answer, right or wrong
    for base in (cwd or os.getcwd(), os.environ.get("WISE_PLAYWRIGHT")):
        if base:
            found = _resolve(node, base)
            if found:
                return found
    return None


def missing_playwright(explicit: str | None = None) -> str:
    looked = [f"--playwright {explicit}"] if explicit else []
    looked += [f"the current folder ({os.getcwd()})"]
    looked += [f"$WISE_PLAYWRIGHT ({os.environ['WISE_PLAYWRIGHT']})"] if os.environ.get("WISE_PLAYWRIGHT") else ["$WISE_PLAYWRIGHT (not set)"]
    return ("playwright not found; looked in " + ", ".join(looked) + ".\n"
            "  Install it in the game project:\n"
            f"    {INSTALL}\n"
            "  or point at a project that already has it: --playwright DIR, or export WISE_PLAYWRIGHT=DIR")


def node_command(script: Path, opts: dict, node: str = "node") -> list[str]:
    """Every option travels as one JSON argument, so nothing is lost to quoting."""
    return [node, str(script), json.dumps(opts, separators=(",", ":"))]


def target_url(target: str) -> str:
    if target.lower().startswith(("http://", "https://", "file://")):
        return target
    p = Path(target).expanduser()
    if p.is_file():
        return p.resolve().as_uri()
    die(f"{target!r} is not a URL (http://, https://, file://) or an existing HTML file", 2)


def options(a) -> dict:
    """The harness options for these arguments (no Playwright path yet)."""
    try:
        w, h = parse_size(a.size)
        if w < 100 or h < 100:
            raise ValueError
    except ValueError:
        die(f"--size wants WIDTHxHEIGHT in CSS px, e.g. 390x844 (got {a.size!r})", 2)
    if a.seconds < 0 or (a.taps is not None and a.taps < 0):
        die("--seconds and --taps can't be negative", 2)
    if a.max_p95 is not None and a.max_p95 <= 0:
        die("--max-p95 wants milliseconds above 0, e.g. 20", 2)
    out = a.out or os.path.join("qa-out", f"{a.engine}-{w}x{h}-{a.persona}")
    opts = {"url": target_url(a.url), "engine": a.engine, "width": w, "height": h, "dpr": a.dpr, "out": out,
            "seconds": a.seconds, "seed": a.seed, "selectors": [s for group in a.selector or [] for s in group],
            "startSelector": a.start_selector,
            "area": a.area, "ready": a.ready, "block": a.block or [], "noOverflow": a.no_overflow,
            "timeoutMs": int(a.timeout * 1000), "persona": a.persona, "buy": a.buy, "maxP95": a.max_p95}
    if a.taps is not None:
        opts["taps"] = a.taps
    if a.channel:
        opts["channel"] = a.channel
    return opts


def run_harness(cmd: list[str], timeout: float) -> tuple[dict, int]:
    """Run a node script that prints one JSON line last; -> (result, exit code). Exits 2 when it could not start."""
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        die(f"the browser run did not finish within {timeout:.0f} s", 1)
    except OSError as e:
        die(f"could not start node: {e}", 2)
    lines = [ln for ln in p.stdout.splitlines() if ln.strip()]
    try:
        result = json.loads(lines[-1])
        if not isinstance(result, dict):
            raise ValueError
    except (IndexError, ValueError):
        die(f"the browser run ended without a result (exit {p.returncode}):\n{(p.stderr or p.stdout).strip()[-2000:]}", 1)
    if "fatal" in result:
        die(result["fatal"], 2)
    return result, p.returncode


def format_result(r: dict) -> str:
    gate_overflow = r.get("gate", {}).get("overflow", True)
    lines = [f"{'PASS' if r['ok'] else 'FAIL'}  {r['engine']} {r['size']}  {r['url']}" + (f"  (system {r['channel']})" if r.get("channel") else "")]
    rd = r["ready"]
    lines.append(f"  ready:        {'yes' if rd['ok'] else 'NO'} after {rd['ms']} ms  ({rd['expression']})")
    g = r["game"]
    lines.append("  game:         " + (f"window.__game found, keys: {', '.join(g['keys'][:16]) or '(none enumerable)'}" + (" ..." if len(g["keys"]) > 16 else "")
                                       if g["found"] else "window.__game not found") +
                 (f"; other hooks: {', '.join(k for k in g['hooks'] if k != '__game')}" if [k for k in g["hooks"] if k != "__game"] else ""))
    for s in r["steps"]:
        lines.append(f"  step:         {s['selector']}  " + (f"tapped ({s['via']})" if s["found"] else "NOT FOUND"))
    t = r["taps"]
    lines.append(f"  persona:      {r.get('persona', 'casual')}")
    lines.append(f"  taps:         {t['done']} of {t['planned']} over {t['seconds']} s in {t['area']['source']}, seed {t['seed']}")
    if r.get("persona") == "spender":
        sp = r.get("spends") or []
        lines.append(f"  bought:       {len(sp) or 'nothing (no visible buy / upgrade / claim control)'}")
        counts: dict[str, int] = {}
        for x in sp:
            counts[x["label"]] = counts.get(x["label"], 0) + 1
        lines += [f"    - {k}  x{n}" for k, n in sorted(counts.items(), key=lambda kv: -kv[1])[:10]]
    ft = r.get("frameTime") or {}
    if ft.get("frames"):
        lines.append(f"  frame time:   {ft['frames']} frames, {ft['fps']} fps, p50 {ft['p50']} ms, p95 {ft['p95']} ms, p99 {ft['p99']} ms, "
                     f"{ft['over33']} over 33 ms, worst {ft['worst']} ms" + (f"  (gate: p95 <= {ft['maxP95']} ms)" if ft.get("maxP95") else "")
                     + "  (headless; compare builds, not phones)")
    else:
        lines.append("  frame time:   no frames drawn (a page that never calls requestAnimationFrame)")
    b = r["blocked"]
    lines.append(f"  blocked:      {b['requests']} request(s) matching {', '.join(b['patterns'])}" if b["patterns"]
                 else "  blocked:      nothing (every request went through; --block is opt-in)")
    lines.append(f"  errors:       {len(r['errors']) or 'none'}")
    lines += [f"    - {e}" for e in r["errors"][:20]]
    lines.append(f"  overflow:     {len(r['overflow']) or 'none'}" + ("" if gate_overflow else "  (not gated: --no-overflow)"))
    for o in r["overflow"]:
        what = {"document": lambda: f"scrollWidth {o['scrollWidth']} > {o['innerWidth']}",
                "viewport": lambda: f"missing: the page lays out {o['layoutWidth']} px wide on a {o['innerWidth']} px phone"}.get(
                    o["kind"], lambda: f"right edge {o['right']} > {o['innerWidth']}")()
        lines.append(f"    - {o['selector']}  {what}  (at {o['at']})")
    lines.append(f"  failed requests: {len(r['failedRequests']) or 'none'}")
    lines += [f"    - {f.get('status') or f.get('error')}  {f['url']}" for f in r["failedRequests"][:10]]
    lines.append("  screenshots:  " + (", ".join(r["screenshots"]) or "none"))
    if r.get("board"):
        lines.append(f"  board:        {r['board']}")
    return "\n".join(lines)


def make_board(shots: list[str], out: Path, title: str) -> str | None:
    """All screenshots of a run side by side on one PNG, each labelled with its file name: evidence a person reads at a glance."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return None
    ims = []
    for f in shots:
        try:
            ims.append((Path(f).stem, Image.open(f).convert("RGB")))
        except OSError:
            continue
    if not ims:
        return None
    h = 640
    ims = [(n, im.resize((max(1, round(im.width * h / im.height)), h))) for n, im in ims]
    cols = min(len(ims), 6)
    rows = -(-len(ims) // cols)
    cw = max(im.width for _, im in ims)
    pad, label, head = 16, 30, 44
    board = Image.new("RGB", (pad + cols * (cw + pad), head + rows * (h + label + pad) + pad), "#0a0a0c")
    d = ImageDraw.Draw(board)
    try:
        font = ImageFont.truetype(str(Path(__file__).parent / "fonts" / "JetBrainsMono-Bold.ttf"), 18)
    except OSError:
        font = ImageFont.load_default()
    d.text((pad, 12), title, fill="#f5f5f5", font=font)
    for i, (name, im) in enumerate(ims):
        x, y = pad + (i % cols) * (cw + pad), head + (i // cols) * (h + label + pad)
        board.paste(im, (x, y))
        d.text((x, y + h + 6), name, fill="#45e3e0", font=font)
    path = out / "board.png"
    board.save(path)
    return str(path)


def main(a):
    opts = options(a)
    node = shutil.which("node") if a.dry_run else need_node()
    pw = find_playwright(node, a.playwright) if node else None
    if a.dry_run:
        print(shlex.join(node_command(HARNESS, {**opts, "playwright": pw}, node or "node")))
        if not pw:
            print("wise: " + missing_playwright(a.playwright), file=sys.stderr)
        return
    if not pw:
        die(missing_playwright(a.playwright), 2)
    result, _ = run_harness(node_command(HARNESS, {**opts, "playwright": pw}, node), timeout=a.seconds + 2 * a.timeout + 120)
    if not a.no_board and result.get("screenshots"):
        verdict = "PASS" if result.get("ok") else "FAIL"
        result["board"] = make_board(result["screenshots"], Path(opts["out"]),
                                     f"{verdict}  {result['engine']} {result['size']}  {result.get('persona', 'casual')}  {result['url']}")
    print(json.dumps(result) if a.json else format_result(result))
    if not result.get("ok"):
        sys.exit(1)


def register(sub):
    p = sub.add_parser("qa", help="virtual testers: a muted phone browser plays like a player (casual, tapper, idler, spender); errors, overflow, frame time, screenshots",
                       description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("url", help="the running game (http://, https://, file://) or a local HTML file")
    p.add_argument("--engine", choices=["chromium", "webkit"], default="chromium")
    p.add_argument("--size", default="390x844", help="viewport in CSS px (default 390x844; also try 320x568 and 360x740)")
    p.add_argument("--dpr", type=float, default=2, help="device scale factor (default 2)")
    p.add_argument("--out", metavar="DIR", help="screenshot folder (default ./qa-out/<engine>-<WxH>/)")
    p.add_argument("--persona", choices=["casual", "tapper", "idler", "spender"], default="casual",
                   help="how the virtual player plays (default casual): tapper 5 taps/s, idler a tap every 5 s, spender buys with in-game currency")
    p.add_argument("--buy", metavar="CSS", help="for the spender: the controls it may tap (default: visible buttons that say buy, upgrade, claim, open...)")
    p.add_argument("--seconds", type=float, default=20, help="how long to play (default 20)")
    p.add_argument("--taps", type=int, help="how many actions over those seconds (default: the persona's rate)")
    p.add_argument("--seed", type=int, default=1, help="seed of the tap points (default 1): the same seed taps the same places")
    p.add_argument("--ready", metavar="JS", default='document.readyState === "complete"',
                   help="JS expression that turns true when the game can be played, e.g. \"window.__game\"")
    p.add_argument("--timeout", type=float, default=60, metavar="S", help="seconds to wait for the page and for --ready (default 60)")
    p.add_argument("--start-selector", metavar="CSS", help="tap this first (a Play button)")
    p.add_argument("--selector", metavar="CSS", action="append", nargs="+",
                   help="then tap these, in order (several after one flag, or repeat it); a missing one is an error")
    p.add_argument("--area", metavar="CSS", help="element to tap inside (default: the largest canvas on screen, else the viewport)")
    p.add_argument("--block", metavar="PATTERN", action="append", help="opt-in: answer matching requests with an empty 200 instead of sending them; repeatable (default: none, everything goes through)")
    p.add_argument("--no-overflow", action="store_true", help="report horizontal overflow but leave it out of the gate")
    p.add_argument("--max-p95", type=float, metavar="MS", help="also fail when the 95th-percentile frame time is above MS milliseconds")
    p.add_argument("--no-board", action="store_true", help="skip board.png, the sheet of every screenshot")
    p.add_argument("--channel", help="use an installed browser instead of Playwright's Chromium, e.g. chrome")
    p.add_argument("--playwright", metavar="DIR", help="a folder node can load Playwright from (or set WISE_PLAYWRIGHT)")
    p.add_argument("--dry-run", action="store_true", help="print the node command and stop")
    p.add_argument("--json", action="store_true", help="print the result as one JSON line")
    p.set_defaults(func=main)
