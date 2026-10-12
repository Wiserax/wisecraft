"""Measure and fix the loudness of music, trailers, game sounds and voice (EBU R128), without ever playing them.

    wise music-enhance theme.mp3                        # -> theme.enhanced.mp3 at -14 LUFS, true peak <= -1 dBTP
    wise music-enhance trailer.mp4 --for trailer        # fixes the audio track; the picture is copied, not re-encoded
    wise music-enhance sfx/*.wav --for game-sfx --out-dir sfx-fixed
    wise music-enhance voice.wav --for voice --eq --fade-in 0.05 --fade-out 0.3 -o voice-clean.wav
    wise music-enhance trailer.mp4 --check              # measure only; exit 1 when it is off the target
    wise music-enhance music.ogg --check --target -20 --tolerance 1.5 --json

It works in two passes. Pass one measures the file: integrated loudness, range (LRA), true peak. Pass two writes a
new file at the target: one clean gain change when the peaks allow it, otherwise ffmpeg's loudnorm fed with the
measured values, whose limiter holds the true peak under the ceiling. The result is measured again and both
readings are printed as a before/after report (add --report FILE to keep it as .json or .md). Your input file is
never changed, and nothing reaches a speaker: ffmpeg decodes to a file or to the null muxer.

Presets (--for): music -14 LUFS, trailer -14 LUFS, voice -16 LUFS, game-sfx -18 LUFS; all with a -1 dBTP ceiling.
--target and --true-peak override them. --eq adds a gentle cleanup before the level is set: a low cut under 30 Hz
(rumble no speaker plays but every limiter reacts to) and a -1.5 dB shelf above 6.5 kHz (harshness).
A video keeps its picture stream bit for bit; only the first audio track is rewritten (other audio and subtitle
tracks are left out). A clip under 0.4 s is too short for a loudness reading: only its peak is held under the ceiling.
Exit 0 written (or measured and inside the target), 1 off the target or a file could not be handled, 2 usage or no ffmpeg.
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

PRESETS = {"music": -14.0, "trailer": -14.0, "voice": -16.0, "game-sfx": -18.0}     # integrated LUFS
CEILING = -1.0                                                                    # true peak, dBTP
TARGETS = ("Targets: music and trailers -14 LUFS integrated, voice -16, game sounds -18 (set relative levels in the game's mixer); "
           "true peak <= -1 dBTP.")
VIDEO_EXT = (".mp4", ".mov", ".m4v", ".webm", ".mkv")
EQ = ["highpass=f=30", "highshelf=f=6500:g=-1.5"]      # rumble out, a little harshness down
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
    m = re.search(r"Stream #0:[^\n]*?Audio:[^\n]*?(\d+) kb/s", head)
    out["bitrate_kbps"] = int(m.group(1)) if m else None
    out["has_video"] = bool(re.search(r"Stream #0:[^\n]*?Video:(?![^\n]*attached pic)", head))
    out["_norm"] = norm
    out["silent"] = peak is None         # digital silence has no peak
    if integrated is None:
        out["note"] = "digital silence: nothing to measure" if out["silent"] else \
            "too short for a loudness reading (a 0.4 s block never filled); the peak still counts"
    return out


def command(ffmpeg: str, path: str, pre: list[str] | None = None) -> list[str]:
    # Two branches, so each meter reads the stream as decoded: chained, ffmpeg resamples to loudnorm's 192 kHz
    # ahead of ebur128 and its readings drift by a tenth. Both outputs go to the null muxer: no file, no device.
    graph = "[0:a:0]" + "".join(f + "," for f in pre or []) + "asplit=2[a][b];[a]ebur128=peak=true[x];[b]loudnorm=print_format=json[y]"
    return [ffmpeg, "-hide_banner", "-nostats", "-nostdin", "-i", path, "-filter_complex", graph,
            "-map", "[x]", "-f", "null", "-", "-map", "[y]", "-f", "null", "-"]


def measure(path: str, ffmpeg: str | None = None, timeout: float = 600, pre: list[str] | None = None) -> dict:
    """Readings for one file, or {"file", "error"} when ffmpeg can't measure it. Never plays anything.

    `pre` is a list of audio filters to run ahead of the meters (what the file would read after an EQ or a fade)."""
    ffmpeg = ffmpeg or need_ffmpeg()
    try:
        p = subprocess.run(command(ffmpeg, path, pre), capture_output=True, text=True, errors="replace", timeout=timeout)
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


# --------------------------------------------------------------------------- fix

def _encoders(ffmpeg: str) -> str:
    return subprocess.run([ffmpeg, "-hide_banner", "-encoders"], capture_output=True, text=True, errors="replace").stdout


def codec_args(out: Path, before: dict, ffmpeg: str) -> list[str]:
    """Encoder settings for the output's extension, as close to the source as the format allows. Raises ValueError."""
    ext = out.suffix.lower()
    kbps = min(320, max(128, before.get("bitrate_kbps") or 192))
    src = before.get("codec") or ""
    if ext == ".wav":
        return ["-c:a", src if src in ("pcm_s16le", "pcm_s24le", "pcm_s32le", "pcm_f32le") else "pcm_s16le"]
    if ext in (".aif", ".aiff"):
        return ["-c:a", "pcm_s24be" if "24" in src else "pcm_s16be"]
    if ext == ".flac":
        return ["-c:a", "flac"]
    if ext == ".mp3":
        return ["-c:a", "libmp3lame", "-b:a", f"{kbps}k"]
    if ext in (".ogg", ".oga"):
        if "libvorbis" not in _encoders(ffmpeg):
            raise ValueError("this ffmpeg has no Vorbis encoder: pass -o with a .opus, .mp3, .flac or .wav name")
        return ["-c:a", "libvorbis", "-q:a", "6"]
    if ext in (".opus", ".webm", ".weba"):
        return ["-c:a", "libopus", "-b:a", "160k"]
    if ext in (".m4a", ".aac", ".mp4", ".mov", ".m4v", ".mkv"):
        return ["-c:a", "aac", "-b:a", "256k"]
    raise ValueError(f"don't know how to write {ext or 'a file with no extension'}: pass -o with a .wav, .flac, .mp3, .m4a, .opus, .mp4, .mov, .webm or .mkv name")


def plan(m: dict, target: float, ceiling: float) -> dict:
    """From pass one's readings: how to reach the target. `m` is measure() of the signal after any EQ and fades."""
    i, tp = m["integrated_lufs"], m["true_peak_dbfs"]
    if m["silent"]:
        return dict(method="copy", filters=[], gain_db=0.0, why="digital silence: nothing to level")
    if i is None:
        gain = min(0.0, ceiling - tp)
        return dict(method="peak", filters=[f"volume={gain:.2f}dB"] if gain else [], gain_db=round(gain, 2),
                    why="too short for a loudness reading: only the peak is held under the ceiling")
    gain = target - i
    if tp + gain <= ceiling + 1e-6:
        return dict(method="gain", filters=[f"volume={gain:.2f}dB"], gain_db=round(gain, 2),
                    why=f"one gain change of {gain:+.1f} dB; the peaks stay under the ceiling, so the dynamics are untouched")
    n = m.get("_norm") or {}
    lra = min(50.0, max(1.0, m["lra_lu"] or 7.0))
    f = f"loudnorm=I={target:.2f}:TP={ceiling:.2f}:LRA={lra:.1f}"
    if all(_num(n.get(k)) is not None for k in ("input_i", "input_tp", "input_lra", "input_thresh", "target_offset")):
        f += (f":measured_I={n['input_i']}:measured_TP={n['input_tp']}:measured_LRA={n['input_lra']}"
              f":measured_thresh={n['input_thresh']}:offset={n['target_offset']}:linear=true")
    return dict(method="loudnorm", filters=[f + ":print_format=summary"], gain_db=round(gain, 2),
                why=f"a plain {gain:+.1f} dB would push the peak to {tp + gain:+.1f} dBTP: loudnorm's second pass levels it and its limiter holds the ceiling")


def render(ffmpeg: str, src: str, out: Path, filters: list[str], before: dict, timeout: float = 1800) -> str | None:
    """Write `out`; the error text when ffmpeg fails."""
    is_video = out.suffix.lower() in VIDEO_EXT and before.get("has_video")
    cmd = [ffmpeg, "-hide_banner", "-nostats", "-nostdin", "-y", "-i", src]
    cmd += ["-map", "0:v:0", "-map", "0:a:0", "-c:v", "copy"] if is_video else ["-map", "0:a:0", "-vn"]
    if filters:
        cmd += ["-af", ",".join(filters)]
    cmd += codec_args(out, before, ffmpeg)
    if before.get("sample_rate"):
        cmd += ["-ar", str(48000 if out.suffix.lower() in (".opus", ".webm", ".weba") else before["sample_rate"])]
    if out.suffix.lower() in (".mp4", ".mov", ".m4v", ".m4a"):
        cmd += ["-movflags", "+faststart"]
    try:
        p = subprocess.run(cmd + [str(out)], capture_output=True, text=True, errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired:
        return f"ffmpeg did not finish within {timeout:.0f} s"
    if p.returncode:
        return next((ln.strip() for ln in reversed(p.stderr.splitlines()) if ln.strip()), "ffmpeg failed")[-300:]
    return None


def _public(m: dict) -> dict:
    return {k: m.get(k) for k in ("integrated_lufs", "lra_lu", "true_peak_dbfs", "max_short_term_lufs", "max_momentary_lufs", "duration_s")}


def enhance(src: str, out: Path, target: float = -14.0, ceiling: float = CEILING, eq: bool = False, fade_in: float = 0.0,
            fade_out: float = 0.0, ffmpeg: str | None = None, tolerance: float = 0.5) -> dict:
    """Measure `src`, write `out` at the target, measure `out`. Returns the before/after report for the file."""
    ffmpeg = ffmpeg or need_ffmpeg()
    before = measure(src, ffmpeg)
    if "error" in before:
        return dict(file=src, error=before["error"])
    pre = list(EQ) if eq else []
    dur = before["duration_s"] or 0
    if fade_in > 0:
        pre.append(f"afade=t=in:st=0:d={min(fade_in, dur or fade_in):.3f}")
    if fade_out > 0 and dur:
        pre.append(f"afade=t=out:st={max(0.0, dur - fade_out):.3f}:d={min(fade_out, dur):.3f}")
    shaped = measure(src, ffmpeg, pre=pre) if pre else before
    if "error" in shaped:
        return dict(file=src, error=shaped["error"])
    try:
        codec_args(out, before, ffmpeg)
    except ValueError as e:
        return dict(file=src, error=str(e))
    step = plan(shaped, target, ceiling)
    aim, after, tries = target, None, 0
    while True:
        tries += 1
        tail = [f"aresample={before['sample_rate']}"] if step["method"] == "loudnorm" and before.get("sample_rate") else []
        err = render(ffmpeg, src, out, pre + step["filters"] + tail, before)
        if err:
            return dict(file=src, error=err)
        after = measure(str(out), ffmpeg)
        if "error" in after:
            return dict(file=src, error=f"wrote {out} but could not measure it: {after['error']}")
        i = after["integrated_lufs"]
        # loudnorm's dynamic mode can land a little off on short or very dynamic files: aim again by the miss
        if step["method"] != "loudnorm" or i is None or abs(i - target) <= 0.3 or tries >= 3:
            break
        aim += target - i
        step = dict(plan(shaped, aim, ceiling), gain_db=step["gain_db"], why=step["why"])
    i, tp = after["integrated_lufs"], after["true_peak_dbfs"]
    hit = i is None or abs(i - target) <= tolerance + 1e-9
    under = tp is None or tp <= ceiling + 0.3          # encoders (mp3, aac, opus) move a true peak by a few tenths
    r = dict(file=src, out=str(out), method=step["method"], why=step["why"], gain_db=step["gain_db"], passes=tries + (2 if pre else 1),
             filters=pre + step["filters"], target=dict(lufs=target, true_peak_dbtp=ceiling, tolerance=tolerance),
             before=_public(before), after=_public(after), video_copied=bool(out.suffix.lower() in VIDEO_EXT and before.get("has_video")),
             ok=bool(hit and under))
    if not hit:
        r["note"] = f"landed {i - target:+.1f} LU from the target"
    elif not under:
        r["note"] = f"true peak {tp:.1f} dBTP is over the {ceiling:g} dBTP ceiling after encoding: lower --true-peak by a few tenths or write a .wav/.flac"
    elif i is None:
        r["note"] = before.get("note") or step["why"]
    return r


def format_enhanced(r: dict) -> str:
    if "error" in r:
        return f"{r['file']}\n  could not enhance: {r['error']}"
    b, a, t = r["before"], r["after"], r["target"]
    lines = [f"{r['file']}  ->  {r['out']}",
             f"  target:        {t['lufs']:g} LUFS integrated, true peak <= {t['true_peak_dbtp']:g} dBTP",
             f"  {'':<14}{'before':>10} {'after':>10}",
             f"  {'integrated':<14}{_f(b['integrated_lufs'], width=10)} {_f(a['integrated_lufs'], width=10)}  LUFS",
             f"  {'range (LRA)':<14}{_f(b['lra_lu'], width=10)} {_f(a['lra_lu'], width=10)}  LU",
             f"  {'true peak':<14}{_f(b['true_peak_dbfs'], width=10)} {_f(a['true_peak_dbfs'], width=10)}  dBTP",
             f"  method:        {r['why']}"]
    extra = [f for f in r["filters"] if not f.startswith(("volume=", "loudnorm="))]
    if extra:
        lines.append(f"  also:          {', '.join(extra)}")
    if r["video_copied"]:
        lines.append("  picture:       copied as it is (not re-encoded)")
    lines.append("  result:        " + ("on target" if r["ok"] else "OFF TARGET") + (f" ({r['note']})" if r.get("note") else ""))
    return "\n".join(lines)


def out_path(src: Path, a) -> Path:
    if a.out:
        return Path(a.out)
    if a.out_dir:
        return Path(a.out_dir) / src.name
    return src.with_name(f"{src.stem}.enhanced{src.suffix}")


def write_report(path: Path, payload: dict, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".json":
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    else:
        path.write_text("# Loudness: before and after\n\n```\n" + text + "\n```\n", encoding="utf-8")


def _strip(r: dict) -> dict:
    return {k: v for k, v in r.items() if not k.startswith("_")}


def main(a):
    missing = [f for f in a.files if not Path(f).is_file()]
    if missing:
        die("no such file: " + ", ".join(missing), 2)
    if a.tolerance is not None and a.tolerance < 0:
        die("--tolerance can't be negative", 2)
    ffmpeg = need_ffmpeg()
    preset = getattr(a, "preset", None) or "music"
    explicit = a.target is not None
    target = a.target if explicit else PRESETS[preset]
    if getattr(a, "check", False):
        # the gate: measure only. The hidden `loudness` alias gates only when --target is given, as it always did.
        gate_on = target if (explicit or not getattr(a, "alias", False)) else None
        tol = 1.0 if a.tolerance is None else a.tolerance
        results = [_strip(gate(measure(f, ffmpeg), gate_on, tol)) for f in a.files]
        ok = all("error" not in r and r.get("target", {}).get("ok", True) for r in results)
        payload = {"ok": ok, "target": gate_on, "tolerance": tol if gate_on is not None else None, "files": results}
        text = format_one(results[0]) if len(results) == 1 else format_table(results)
        print(json.dumps(payload, indent=2) if a.json else text + "\n" + TARGETS)
    else:
        if a.out and len(a.files) > 1:
            die("-o names one output file: for several inputs use --out-dir", 2)
        if a.fade_in < 0 or a.fade_out < 0:
            die("fades can't be negative", 2)
        if a.true_peak > 0:
            die("--true-peak is a ceiling in dBTP: 0 or lower", 2)
        if a.out_dir:
            Path(a.out_dir).mkdir(parents=True, exist_ok=True)
        results = []
        for f in a.files:
            out = out_path(Path(f), a)
            if out.resolve() == Path(f).resolve():
                results.append(dict(file=f, error="the output would overwrite the input: pick another -o or --out-dir"))
                continue
            out.parent.mkdir(parents=True, exist_ok=True)
            results.append(enhance(f, out, target, a.true_peak, a.eq, a.fade_in, a.fade_out, ffmpeg,
                                   0.5 if a.tolerance is None else a.tolerance))
        ok = all(r.get("ok") for r in results)
        payload = {"ok": ok, "preset": None if explicit else preset, "target": {"lufs": target, "true_peak_dbtp": a.true_peak}, "files": results}
        text = "\n\n".join(format_enhanced(r) for r in results)
        print(json.dumps(payload, indent=2) if a.json else text)
    if getattr(a, "report", None):
        write_report(Path(a.report), payload, text)
        if not a.json:
            print(f"report: {a.report}")
    if not ok:
        sys.exit(1)


def main_alias(a):
    print("wise: `loudness` is now `wise music-enhance --check` (same readings; without --check it also fixes the level)", file=sys.stderr)
    a.check, a.alias, a.report = True, True, None
    main(a)


def register(sub):
    p = sub.add_parser("music-enhance", help="measure and fix loudness of music, trailers, game sounds and voice (EBU R128); never plays audio",
                       description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("files", nargs="+", metavar="file", help="audio or video files (mp3, wav, ogg, m4a, flac, mp4, mov, webm ...)")
    p.add_argument("--for", dest="preset", choices=sorted(PRESETS), default="music",
                   help="what the file is: music and trailer -14 LUFS, voice -16, game-sfx -18 (default music)")
    p.add_argument("--target", type=float, metavar="LUFS", help="integrated loudness to hit, instead of the preset's")
    p.add_argument("--true-peak", type=float, default=CEILING, metavar="DBTP", help="true-peak ceiling (default -1)")
    p.add_argument("--eq", action="store_true", help="gentle cleanup first: low cut under 30 Hz and a -1.5 dB shelf above 6.5 kHz")
    p.add_argument("--fade-in", type=float, default=0.0, metavar="S", help="fade in over S seconds")
    p.add_argument("--fade-out", type=float, default=0.0, metavar="S", help="fade out over the last S seconds")
    p.add_argument("-o", "--out", metavar="FILE", help="output file (one input); default <name>.enhanced.<ext> next to the input")
    p.add_argument("--out-dir", metavar="DIR", help="write outputs here under their own names")
    p.add_argument("--check", action="store_true", help="measure only and gate: exit 1 when a file is off the target")
    p.add_argument("--tolerance", type=float, metavar="LU", help="allowed distance from the target (default 1 with --check, 0.5 for the written file)")
    p.add_argument("--report", metavar="FILE", help="also save the before/after report as .json or .md")
    p.add_argument("--json", action="store_true", help="print the report as JSON")
    p.set_defaults(func=main)
    # the old name, kept working (and out of the help) for one release
    q = sub.add_parser("loudness", description="Old name of `wise music-enhance --check`: measures, and gates with --target.")
    q.add_argument("files", nargs="+", metavar="file")
    q.add_argument("--target", type=float, metavar="LUFS")
    q.add_argument("--tolerance", type=float, default=1.0, metavar="DB")
    q.add_argument("--json", action="store_true")
    q.set_defaults(func=main_alias)
