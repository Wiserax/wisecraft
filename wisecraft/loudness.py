"""Measure loudness and true peak of audio or video files (EBU R128) without ever playing them.

    wise loudness trailer.mp4                               # integrated LUFS, range, true peak, max short-term and momentary
    wise loudness public/audio/*.mp3                        # several files: one table
    wise loudness trailer.mp4 --target -15 --tolerance 1    # exit 1 when integrated loudness is outside -16..-14
    wise loudness music.ogg --json

ffmpeg decodes the first audio stream and measures it in one pass; nothing reaches a speaker. Integrated loudness,
range and true peak come from loudnorm's measurement (reliable on short files too), the short-term and momentary
maxima from the ebur128 frame log. A clip under 0.4 s is too short for a loudness reading: only its peak is given.
Targets that worked: trailer/social about -15 LUFS integrated, true peak <= -1.5 dBTP; in-game music about
-20 LUFS short-term, a single SFX no more than music + 6 dB.
Exit 0 measured (and inside --target), 1 outside the target or a file could not be measured, 2 usage or no ffmpeg.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from wisecraft.common import die

TARGETS = ("Targets: trailer/social ~ -15 LUFS integrated, true peak <= -1.5 dBTP; in-game music ~ -20 LUFS short-term, "
           "SFX <= music + 6 dB.")
FLOOR = -120.0      # ebur128 prints -120.7 until a window has filled: not a measurement
FRAME_RE = re.compile(r"\bt:\s*[\d.]+\s+TARGET:.*?\bM:\s*(-?[\d.]+|-?inf|nan)\s+S:\s*(-?[\d.]+|-?inf|nan)")
NUM = r"(-?[\d.]+|-?inf|nan)"
LAYOUTS = {"mono": 1, "stereo": 2, "2.1": 3, "3.0": 3, "quad": 4, "4.0": 4, "5.0": 5, "5.1": 6, "6.1": 7, "7.1": 8}


def need_ffmpeg() -> str:
    return shutil.which("ffmpeg") or die("ffmpeg not found on PATH: install it (brew install ffmpeg / apt install ffmpeg / "
                                         "winget install ffmpeg)", 2)


def _num(s: str | None) -> float | None:
    """A finite reading, or None for inf/nan (digital silence has no peak)."""
    try:
        v = float(s)
    except (TypeError, ValueError):
        return None
    return v if v == v and abs(v) != float("inf") else None


def _channels(layout: str) -> int | None:
    m = re.match(r"(\d+) channels", layout)
    return int(m.group(1)) if m else LAYOUTS.get(layout.split("(")[0].strip())


def parse(log: str) -> dict:
    """ffmpeg's stderr for the ebur128 + loudnorm graph built by command()  ->  the readings.

    Raises ValueError when there is no summary (the file has no audio, or ffmpeg failed)."""
    head, sep, summary = log.rpartition("Summary:")
    if not sep:
        raise ValueError("no loudness summary in ffmpeg's output")

    def pick(pattern):
        m = re.search(pattern, summary)
        return _num(m.group(1)) if m else None

    momentary, short = [], []
    for m in FRAME_RE.finditer(log):
        for value, into in ((_num(m.group(1)), momentary), (_num(m.group(2)), short)):
            if value is not None and value > FLOOR:
                into.append(value)
    norm = None
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", log)
    if m:
        try:
            norm = json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    if norm:
        integrated, lra, peak = _num(norm.get("input_i")), _num(norm.get("input_lra")), _num(norm.get("input_tp"))
    else:   # an ffmpeg without loudnorm: the ebur128 summary, whose -70.0 is a floor, not a reading
        integrated, lra, peak = pick(rf"\bI:\s+{NUM} LUFS"), pick(rf"\bLRA:\s+{NUM} LU"), pick(rf"\bPeak:\s+{NUM} dBFS")
        integrated = None if integrated is not None and integrated <= -70 else integrated
    if integrated is None or not momentary:
        integrated = lra = None
    out = {"integrated_lufs": integrated, "lra_lu": lra, "true_peak_dbfs": peak,
           "max_short_term_lufs": max(short) if short else None,
           "max_momentary_lufs": max(momentary) if momentary else None}
    m = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", head)
    out["duration_s"] = round(int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)), 3) if m else None
    m = re.search(r"Stream #0:[^\n]*?Audio:\s*(\w+)[^\n]*?,\s*(\d+) Hz,\s*([^,\n]+)", head)
    out["codec"], out["sample_rate"], layout = (m.group(1), int(m.group(2)), m.group(3).strip()) if m else (None, None, None)
    out["channel_layout"] = layout
    out["channels"] = _channels(layout) if layout else None
    out["silent"] = peak is None         # digital silence has no peak
    if integrated is None:
        out["note"] = "digital silence: nothing to measure" if out["silent"] else \
            "too short for a loudness reading (a 0.4 s block never filled); the peak still counts"
    return out


def command(ffmpeg: str, path: str) -> list[str]:
    # Two branches, so each meter reads the stream as decoded: chained, ffmpeg resamples to loudnorm's 192 kHz
    # ahead of ebur128 and its readings drift by a tenth. Both outputs go to the null muxer: no file, no device.
    graph = "[0:a:0]asplit=2[a][b];[a]ebur128=peak=true[x];[b]loudnorm=print_format=json[y]"
    return [ffmpeg, "-hide_banner", "-nostats", "-nostdin", "-i", path, "-filter_complex", graph,
            "-map", "[x]", "-f", "null", "-", "-map", "[y]", "-f", "null", "-"]


def measure(path: str, ffmpeg: str | None = None, timeout: float = 600) -> dict:
    """Readings for one file, or {"file", "error"} when ffmpeg can't measure it. Never plays anything."""
    ffmpeg = ffmpeg or need_ffmpeg()
    try:
        p = subprocess.run(command(ffmpeg, path), capture_output=True, text=True, errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"file": path, "error": f"ffmpeg did not finish within {timeout:.0f} s"}
    log = p.stderr
    try:
        if p.returncode != 0:
            raise ValueError
        return {"file": path, **parse(log)}
    except ValueError:
        if "matches no streams" in log:
            return {"file": path, "error": "no audio stream"}
        last = next((ln.strip() for ln in reversed(log.splitlines()) if ln.strip()), "ffmpeg failed")
        return {"file": path, "error": last[-300:]}


def gate(r: dict, target: float | None, tolerance: float) -> dict:
    if target is None or "error" in r:
        return r
    i = r["integrated_lufs"]
    delta = None if i is None else round(i - target, 2)
    r["target"] = {"lufs": target, "tolerance": tolerance, "delta": delta, "ok": delta is not None and abs(delta) <= tolerance + 1e-9}
    return r


def _f(v, unit="", width=0) -> str:
    return ("n/a" if v is None else f"{v:.1f}{unit}").rjust(width)


def _verdict(r: dict) -> str:
    t = r.get("target")
    if not t:
        return ""
    return (f"inside {t['lufs']:g} ±{t['tolerance']:g} LUFS" if t["ok"] else
            f"OUTSIDE {t['lufs']:g} ±{t['tolerance']:g} LUFS" + (f" by {t['delta']:+.1f}" if t["delta"] is not None else ""))


def format_one(r: dict) -> str:
    if "error" in r:
        return f"{r['file']}\n  could not measure: {r['error']}"
    ch = f"{r['channels']} ch" if r["channels"] else "channels n/a"
    lines = [r["file"],
             f"  integrated:      {_f(r['integrated_lufs'], ' LUFS')}" + (f"  ({r['note']})" if r.get("note") else ""),
             f"  range (LRA):     {_f(r['lra_lu'], ' LU')}",
             f"  true peak:       {_f(r['true_peak_dbfs'], ' dBFS')}",
             f"  max short-term:  {_f(r['max_short_term_lufs'], ' LUFS')}" + ("  (needs 3 s of audio)" if r["max_short_term_lufs"] is None else ""),
             f"  max momentary:   {_f(r['max_momentary_lufs'], ' LUFS')}" + ("  (needs 0.4 s of audio)" if r["max_momentary_lufs"] is None else ""),
             f"  stream:          {_f(r['duration_s'], ' s')}, {r['sample_rate'] or 'n/a'} Hz, {ch} ({r['channel_layout'] or 'layout n/a'}), {r['codec'] or 'codec n/a'}"]
    if r.get("target"):
        lines.append(f"  target:          {_verdict(r)}")
    return "\n".join(lines)


def format_table(results: list[dict]) -> str:
    names = [Path(r["file"]).name for r in results]
    w = max(4, *(len(n) for n in names))
    lines = [f"{'file':<{w}}  {'I LUFS':>7} {'LRA':>5} {'TP dBFS':>8} {'max S':>7} {'max M':>7} {'dur s':>8} {'Hz':>6} {'ch':>3}"]
    for name, r in zip(names, results):
        if "error" in r:
            lines.append(f"{name:<{w}}  could not measure: {r['error']}")
            continue
        lines.append(f"{name:<{w}}  {_f(r['integrated_lufs'], width=7)} {_f(r['lra_lu'], width=5)} {_f(r['true_peak_dbfs'], width=8)} "
                     f"{_f(r['max_short_term_lufs'], width=7)} {_f(r['max_momentary_lufs'], width=7)} {_f(r['duration_s'], width=8)} "
                     f"{r['sample_rate'] or 'n/a':>6} {r['channels'] or 'n/a':>3}" + (f"  {_verdict(r)}" if r.get("target") else ""))
    return "\n".join(lines)


def main(a):
    missing = [f for f in a.files if not Path(f).is_file()]
    if missing:
        die("no such file: " + ", ".join(missing), 2)
    if a.tolerance < 0:
        die("--tolerance can't be negative", 2)
    ffmpeg = need_ffmpeg()
    results = [gate(measure(f, ffmpeg), a.target, a.tolerance) for f in a.files]
    ok = all("error" not in r and r.get("target", {}).get("ok", True) for r in results)
    if a.json:
        print(json.dumps({"ok": ok, "target": a.target, "tolerance": a.tolerance if a.target is not None else None, "files": results}, indent=2))
    else:
        print(format_one(results[0]) if len(results) == 1 else format_table(results))
        print(TARGETS)
    if not ok:
        sys.exit(1)


def register(sub):
    p = sub.add_parser("loudness", help="measure loudness and true peak of audio or video files (EBU R128), without playing them",
                       description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("files", nargs="+", metavar="file", help="audio or video files (mp3, wav, ogg, m4a, mp4, webm ...)")
    p.add_argument("--target", type=float, metavar="LUFS", help="gate: the integrated loudness to hit, e.g. -15")
    p.add_argument("--tolerance", type=float, default=1.0, metavar="DB", help="allowed distance from --target (default 1)")
    p.add_argument("--json", action="store_true", help="print the readings as JSON")
    p.set_defaults(func=main)
