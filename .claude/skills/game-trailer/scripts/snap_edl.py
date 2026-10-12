#!/usr/bin/env python3
"""Snap an EDL's segment lengths to whole frames against the running total, so every cut lands on the beat grid.

    python3 snap_edl.py edl.json                 # writes edl.snapped.json next to it and prints the cut table
    python3 snap_edl.py edl.json -o cut.json     # choose the output path
    python3 snap_edl.py edl.json --check         # print the table only, write nothing

Why: `wise video compile` renders each segment on its own, to whole frames. A beat is rarely a whole number of
frames (91.44 BPM at 30 fps is 19.685 frames), so each cut is off by a fraction of a frame and the error adds up
cut after cut. This script turns every segment's "beats" (or "dur") into a "dur" whose frame count makes the cut
land on the nearest frame to the ideal beat time. The error then stays under half a frame at every cut instead of
growing. The output keeps every other key as it was; "beats" is replaced by "dur".

The written "dur" is frames / fps less 0.4 ms: compile cuts each segment with ffmpeg's -t at millisecond
precision, and frames / fps rounded to the millisecond can land just past a frame boundary and gain a frame. The
0.4 ms margin gives the intended count (checked for 1 to 45 frames at 30 and 60 fps) and keeps the total length
within a millisecond per segment, so the end card is not trimmed.

Hard cuts only are exact. With xfade transitions the segments overlap by the transition length; set "beat_lock"
and keep every transition a whole number of frames (0.3 s is 9 frames at 30 fps, 18 at 60) and the grid holds.
Standard library only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def seg_seconds(seg: dict, bpm: float | None) -> float:
    if "beats" in seg:
        if not bpm:
            sys.exit("snap_edl: a segment uses 'beats' but the EDL has no 'bpm'")
        return seg["beats"] * 60.0 / bpm
    return float(seg.get("dur", 4.0))


def snap(edl: dict) -> tuple[dict, list[dict]]:
    fps, bpm = edl.get("fps", 30), edl.get("bpm")
    out = json.loads(json.dumps(edl))
    rows, ideal, naive_frames, snapped_frames = [], 0.0, 0, 0
    for i, seg in enumerate(out["segments"]):
        sec = seg_seconds(seg, bpm)
        ideal += sec
        # what compile does with the raw value: about ceil(dur * fps) frames per segment
        naive_frames += max(1, -(-round(sec * fps * 1000) // 1000))
        target = round(ideal * fps)                     # the frame nearest to the ideal cut time
        n = max(1, target - snapped_frames)
        snapped_frames += n
        seg.pop("beats", None)
        seg["dur"] = round(n / fps - 0.0004, 4)
        rows.append(dict(cut=i + 1, ideal_s=ideal, frames=n, naive_ms=(naive_frames / fps - ideal) * 1000,
                         snapped_ms=(snapped_frames / fps - ideal) * 1000))
    for t in [t for t in [edl.get("transition", {})] + [s.get("transition", {}) for s in edl["segments"]] if t]:
        d = float(t.get("duration", 0) or 0)
        if t.get("type") != "cut" and d and abs(d * fps - round(d * fps)) > 1e-6:
            print(f"snap_edl: a {d} s transition is not a whole number of frames at {fps} fps; cuts after it drift", file=sys.stderr)
    return out, rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("edl")
    ap.add_argument("-o", "--out", help="output path (default <name>.snapped.json)")
    ap.add_argument("--check", action="store_true", help="print the table, write nothing")
    a = ap.parse_args()
    src = Path(a.edl)
    edl = json.loads(src.read_text(encoding="utf-8"))
    out, rows = snap(edl)
    fps = edl.get("fps", 30)
    print(f"fps {fps}, bpm {edl.get('bpm')}: cut time error, as compiled raw vs snapped (+ late, - early)")
    print(f"  {'cut':>3} {'ideal s':>8} {'frames':>6} {'raw ms':>8} {'snapped ms':>10}")
    for r in rows:
        print(f"  {r['cut']:>3} {r['ideal_s']:>8.3f} {r['frames']:>6} {r['naive_ms']:>+8.1f} {r['snapped_ms']:>+10.1f}")
    worst = max(abs(r["snapped_ms"]) for r in rows)
    print(f"  worst snapped error {worst:.1f} ms (half a frame is {500 / fps:.1f} ms)")
    if not a.check:
        dst = Path(a.out) if a.out else src.with_name(src.stem + ".snapped.json")
        dst.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {dst}; compile that one: wise video compile {dst.name} out.mp4")


if __name__ == "__main__":
    main()
