"""Count repeated frames in a video: the stutter check for slow motion and for screen captures.

    wise dupframes trailer.mp4                        # frames, duplicates, the longest run and where it starts
    wise dupframes slowmo.mp4 --max-run 1             # exit 1 when more than 1 frame in a row repeats
    wise dupframes capture.mp4 --start 2 --end 8 --json

A frame is a duplicate when ffmpeg's mpdecimate would drop it (hi=768, lo=320, frac=0.33): compared with the last
kept frame, no 8x8 block differs by more than hi and at most a third of the blocks differ by more than lo. That
survives re-encoding, where repeated frames are never bit-identical. --threshold sets that fraction (0..1).
Smooth slow motion has no runs at all; only a deliberate logo or end-card hold should repeat.
Exit 0 measured (and inside --max-run), 1 the longest run is over --max-run or the file has no video, 2 usage or no ffmpeg.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from wisecraft.common import die
from wisecraft.loudness import need_ffmpeg

HI, LO, FRAC = 768, 320, 0.33      # mpdecimate's own defaults, written out so the definition can't drift
INFO_RE = re.compile(r"\[Parsed_showinfo_(\d+) @ [^\]]+\]\s+n:\s*\d+\s+pts:\s*(-?\d+)\s+pts_time:\s*(-?[\d.]+)")
HINT = "Only a deliberate logo/end-card hold should account for duplicates."


def command(ffmpeg: str, path: str, frac: float = FRAC, start: float | None = None, end: float | None = None) -> list[str]:
    seek = (["-ss", f"{start:g}"] if start else []) + (["-to", f"{end:g}"] if end is not None else [])
    # showinfo before the decimator lists every frame, showinfo after it lists the ones that were kept
    vf = f"showinfo=checksum=0,mpdecimate=hi={HI}:lo={LO}:frac={frac:g},showinfo=checksum=0"
    return [ffmpeg, "-hide_banner", "-nostats", "-nostdin", *seek, "-i", path, "-map", "0:v:0", "-an", "-vf", vf, "-f", "null", "-"]


def runs_of(dup: list[bool]) -> list[tuple[int, int]]:
    """[(index of the first repeated frame, how many frames repeat in a row)]."""
    out, i, n = [], 0, len(dup)
    while i < n:
        if dup[i]:
            j = i
            while j < n and dup[j]:
                j += 1
            out.append((i, j - i))
            i = j
        else:
            i += 1
    return out


def parse(log: str, offset: float = 0.0) -> dict:
    """ffmpeg's stderr for the showinfo,mpdecimate,showinfo chain  ->  counts and runs. `offset` is --start."""
    every, kept = [], []
    for m in INFO_RE.finditer(log):
        (every if m.group(1) == "0" else kept).append((int(m.group(2)), float(m.group(3))))
    if not every:
        raise ValueError("no video frames were decoded")
    dup, k = [], 0
    for pts, _ in every:        # the kept frames are a subsequence of all frames, in order
        if k < len(kept) and kept[k][0] == pts:
            dup.append(False)
            k += 1
        else:
            dup.append(True)
    m = re.search(r"Stream #0:[^\n]*?Video:[^\n]*?\b([\d.]+) fps", log)
    span = every[-1][1] - every[0][1]
    fps = float(m.group(1)) if m else (round((len(every) - 1) / span, 3) if span > 0 else None)
    runs = sorted(runs_of(dup), key=lambda r: (-r[1], r[0]))
    at = lambda i: round(every[i][1] + offset, 3)
    duplicates = sum(dup)
    return {"frames": len(every), "unique": len(every) - duplicates, "duplicates": duplicates,
            "duplicate_pct": round(100 * duplicates / len(every), 2), "fps": fps,
            "duration_s": round(span + (1 / fps if fps else 0), 3),
            "longest_run": {"frames": runs[0][1], "start_s": at(runs[0][0]),
                            "seconds": round(runs[0][1] / fps, 3) if fps else None} if runs else {"frames": 0, "start_s": None, "seconds": 0},
            "runs": len(runs),
            "longest_runs": [{"frames": n, "start_s": at(i)} for i, n in runs[:5]]}


def measure(path: str, frac: float = FRAC, start: float | None = None, end: float | None = None,
            ffmpeg: str | None = None, timeout: float = 1800) -> dict:
    ffmpeg = ffmpeg or need_ffmpeg()
    try:
        p = subprocess.run(command(ffmpeg, path, frac, start, end), capture_output=True, text=True, errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"file": path, "error": f"ffmpeg did not finish within {timeout:.0f} s"}
    base = {"file": path, "definition": {"filter": "mpdecimate", "hi": HI, "lo": LO, "frac": frac},
            "window": {"start_s": start or 0, "end_s": end}}
    try:
        if p.returncode != 0:
            raise ValueError
        return {**base, **parse(p.stderr, start or 0.0)}
    except ValueError as e:
        if "matches no streams" in p.stderr:
            return {**base, "error": "no video stream"}
        last = next((ln.strip() for ln in reversed(p.stderr.splitlines()) if ln.strip()), "ffmpeg failed")
        return {**base, "error": str(e) or last[-300:]}


def format_result(r: dict) -> str:
    if "error" in r:
        return f"{r['file']}\n  could not measure: {r['error']}"
    w, lr = r["window"], r["longest_run"]
    until = "end" if w["end_s"] is None else f"{w['end_s']:g} s"
    lines = [r["file"] + (f"  [{w['start_s']:g} s .. {until}]" if w["start_s"] or w["end_s"] is not None else ""),
             f"  frames:       {r['frames']}  ({r['fps'] if r['fps'] else 'fps n/a'} fps, {r['duration_s']} s)",
             f"  unique:       {r['unique']}",
             f"  duplicates:   {r['duplicates']}  ({r['duplicate_pct']}%) in {r['runs']} run(s)"]
    if lr["frames"]:
        lines.append(f"  longest run:  {lr['frames']} frame(s) in a row, starting at {lr['start_s']} s" + (f" ({lr['seconds']} s long)" if lr["seconds"] else ""))
        if len(r["longest_runs"]) > 1:
            lines.append("  next runs:    " + ", ".join(f"{x['frames']} at {x['start_s']} s" for x in r["longest_runs"][1:]))
    else:
        lines.append("  longest run:  none")
    if "max_run" in r:
        lines.append(f"  gate:         longest run {lr['frames']} {'<=' if r['ok'] else '>'} --max-run {r['max_run']}: {'pass' if r['ok'] else 'FAIL'}")
    return "\n".join(lines)


def main(a):
    if not Path(a.video).is_file():
        die(f"no such file: {a.video}", 2)
    if not 0 <= a.threshold <= 1:
        die("--threshold is a fraction of the frame's blocks: 0..1 (default 0.33)", 2)
    if (a.start is not None and a.start < 0) or (a.end is not None and a.end <= (a.start or 0)):
        die("--start can't be negative and --end must come after it", 2)
    if a.max_run is not None and a.max_run < 0:
        die("--max-run can't be negative", 2)
    r = measure(a.video, a.threshold, a.start, a.end)
    r["ok"] = "error" not in r
    if a.max_run is not None and "error" not in r:
        r["max_run"] = a.max_run
        r["ok"] = r["longest_run"]["frames"] <= a.max_run
    if a.json:
        print(json.dumps(r, indent=2))
    else:
        print(format_result(r))
        print(HINT)
    if not r["ok"]:
        sys.exit(1)


def register(sub):
    p = sub.add_parser("dupframes", help="count repeated frames in a video (the stutter check for slow motion)",
                       description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("video", help="a video file ffmpeg can read")
    p.add_argument("--max-run", type=int, metavar="N", help="gate: exit 1 when more than N frames repeat in a row (default: report only)")
    p.add_argument("--threshold", type=float, default=FRAC, metavar="X",
                   help="share of 8x8 blocks that may differ slightly in a duplicate (mpdecimate frac, default 0.33; 0 = strictest)")
    p.add_argument("--start", type=float, metavar="S", help="only look from this second")
    p.add_argument("--end", type=float, metavar="S", help="only look up to this second")
    p.add_argument("--json", action="store_true", help="print the result as JSON")
    p.set_defaults(func=main)
