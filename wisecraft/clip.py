"""Fingerprint a video file, or a folder of them: `wise scan trailer.mp4`, `wise scan captures/`.

What it reads, all with ffprobe and ffmpeg and never by playing anything: container, duration, resolution, frame
rate, codecs, bitrate; the audio's integrated loudness and true peak (EBU R128); how many scene cuts there are and
the average shot length; the time of the first real frame (after a black or flat opening); and, with --sheet, a
contact sheet of timestamped frames to look at.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

from wisecraft.music_enhance import measure

VIDEO_EXT = (".mp4", ".mov", ".webm", ".mkv", ".m4v", ".avi")
SCENE = 0.30          # ffmpeg's scene score above which two frames count as a cut


class ClipError(ValueError):
    pass


def is_video(p: Path) -> bool:
    return p.suffix.lower() in VIDEO_EXT


def videos_in(folder: Path, limit: int = 200) -> list[Path]:
    return sorted(p for p in folder.iterdir() if p.is_file() and is_video(p))[:limit]


def _rate(s: str | None) -> float | None:
    try:
        n, d = (s or "0/1").split("/")
        return round(float(n) / float(d), 3) if float(d) else None
    except ValueError:
        return None


def probe(path: Path) -> dict:
    """Container and stream facts from ffprobe."""
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise ClipError("ffprobe not found on PATH: install ffmpeg (brew install ffmpeg / apt install ffmpeg / winget install ffmpeg)")
    r = subprocess.run([ffprobe, "-v", "error", "-print_format", "json", "-show_streams", "-show_format", str(path)],
                       capture_output=True, text=True, errors="replace")
    if r.returncode:
        raise ClipError(f"cannot read {path}: {(r.stderr.strip().splitlines() or ['ffprobe failed'])[-1]}")
    d = json.loads(r.stdout or "{}")
    fmt, streams = d.get("format") or {}, d.get("streams") or []
    v = next((s for s in streams if s.get("codec_type") == "video" and (s.get("disposition") or {}).get("attached_pic") != 1), None)
    a = next((s for s in streams if s.get("codec_type") == "audio"), None)
    if not v:
        raise ClipError(f"{path} has no video stream (for an audio file use: wise music-enhance {path.name} --check)")
    duration = float(fmt.get("duration") or v.get("duration") or 0)
    rotate = next((sd.get("rotation") for sd in v.get("side_data_list") or [] if "rotation" in sd), None)
    w, h = v.get("width"), v.get("height")
    if rotate and abs(int(rotate)) % 180 == 90:
        w, h = h, w
    fps = _rate(v.get("avg_frame_rate")) or _rate(v.get("r_frame_rate"))
    frames = int(v["nb_frames"]) if str(v.get("nb_frames", "")).isdigit() else (round(duration * fps) if fps else None)
    return dict(
        file=str(path), container=(fmt.get("format_name") or "").split(",")[0] or None, bytes=int(fmt.get("size") or path.stat().st_size),
        duration_s=round(duration, 3), bitrate_kbps=round(int(fmt["bit_rate"]) / 1000) if str(fmt.get("bit_rate", "")).isdigit() else None,
        video=dict(codec=v.get("codec_name"), profile=v.get("profile"), width=w, height=h, fps=fps, frames=frames,
                   pix_fmt=v.get("pix_fmt"), orientation="portrait" if (w or 0) < (h or 0) else ("square" if w == h else "landscape"),
                   bitrate_kbps=round(int(v["bit_rate"]) / 1000) if str(v.get("bit_rate", "")).isdigit() else None),
        audio=dict(found=True, codec=a.get("codec_name"), sample_rate=int(a["sample_rate"]) if a.get("sample_rate") else None,
                   channels=a.get("channels"), bitrate_kbps=round(int(a["bit_rate"]) / 1000) if str(a.get("bit_rate", "")).isdigit() else None,
                   streams=sum(1 for s in streams if s.get("codec_type") == "audio")) if a else dict(found=False))


def cuts(path: Path, duration: float, threshold: float = SCENE, timeout: float = 900) -> dict:
    """Scene cuts by ffmpeg's scene score, on a small copy of the picture. A cut is a frame that differs a lot from
    the one before; fades and fast pans can add or hide a few, so read the count as a close estimate."""
    ffmpeg = shutil.which("ffmpeg")
    try:
        p = subprocess.run([ffmpeg, "-hide_banner", "-nostats", "-nostdin", "-i", str(path), "-an", "-map", "0:v:0",
                            "-vf", f"scale=320:-2,select='gt(scene,{threshold})',showinfo", "-f", "null", "-"],
                           capture_output=True, text=True, errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired:
        return dict(found=False, note=f"ffmpeg did not finish within {timeout:.0f} s")
    if p.returncode:
        return dict(found=False, note=(p.stderr.strip().splitlines() or ["ffmpeg failed"])[-1][-200:])
    times = [round(float(t), 3) for t in re.findall(r"Parsed_showinfo.*?pts_time:([\d.]+)", p.stderr)]
    shots = len(times) + 1
    return dict(found=True, count=len(times), threshold=threshold, shots=shots,
                average_shot_s=round(duration / shots, 2) if duration else None, at_s=times[:60], listed=min(len(times), 60))


def first_real_frame(path: Path, duration: float, timeout: float = 300) -> dict:
    """When the picture first shows something: the end of the black (or near-black) opening, 0 when there is none."""
    ffmpeg = shutil.which("ffmpeg")
    look = min(duration, 60) if duration else 60
    try:
        p = subprocess.run([ffmpeg, "-hide_banner", "-nostats", "-nostdin", "-t", f"{look:.2f}", "-i", str(path), "-an", "-map", "0:v:0",
                            "-vf", "scale=320:-2,blackdetect=d=0.05:pic_th=0.97:pix_th=0.10", "-f", "null", "-"],
                           capture_output=True, text=True, errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired:
        return dict(found=False, note="ffmpeg did not finish")
    if p.returncode:
        return dict(found=False, note=(p.stderr.strip().splitlines() or ["ffmpeg failed"])[-1][-200:])
    spans = [(float(a), float(b)) for a, b in re.findall(r"black_start:([\d.]+)\s+black_end:([\d.]+)", p.stderr)]
    lead = next((b for a, b in spans if a <= 0.05), 0.0)
    if lead >= look - 0.05:
        return dict(found=False, note=f"the first {look:.0f} s are black", black_spans=len(spans))
    return dict(found=True, at_s=round(lead, 3), black_spans=len(spans),
                note="starts on a picture" if lead == 0 else f"{lead:.2f} s of black first")


def sheet(path: Path, out: Path, duration: float) -> dict:
    """A contact sheet next to the report: about 24 timestamped frames (needs pillow)."""
    try:
        from wisecraft import video
        import PIL  # noqa: F401
    except ImportError:
        return dict(written=False, note="the contact sheet needs pillow: pip install pillow (or run through bin/wise)")
    every = max(0.5, round(duration / 24, 2)) if duration else 2.0
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()):
        video.contact(str(path), str(out), every=every, cols=6, width=320)
    return dict(written=True, file=str(out), every_s=every)


def fingerprint(path: Path, want_sheet: str | None = None, scene: float = SCENE) -> dict:
    """Facts about one video file. Raises ClipError when ffprobe can't read it."""
    r = probe(path)
    r["kind"] = "video"
    if r["audio"]["found"]:
        m = measure(str(path))
        if "error" in m:
            r["audio"]["loudness"] = dict(found=False, note=m["error"])
        else:
            r["audio"]["loudness"] = dict(found=m["integrated_lufs"] is not None, integrated_lufs=m["integrated_lufs"], lra_lu=m["lra_lu"],
                                          true_peak_dbtp=m["true_peak_dbfs"], max_short_term_lufs=m["max_short_term_lufs"],
                                          silent=m["silent"], note=m.get("note"))
    r["cuts"] = cuts(path, r["duration_s"], scene)
    r["first_real_frame"] = first_real_frame(path, r["duration_s"])
    if want_sheet is not None:
        out = Path(want_sheet) if want_sheet else path.with_name(path.stem + ".sheet.png")
        if want_sheet and Path(want_sheet).is_dir():
            out = Path(want_sheet) / (path.stem + ".sheet.png")
        r["sheet"] = sheet(path, out, r["duration_s"])
    r["routes"] = routes(r)
    return r


def routes(r: dict) -> list[dict]:
    out, name = [], Path(r["file"]).name
    a = r["audio"]
    loud = a.get("loudness") or {}
    if not a["found"]:
        out.append(dict(do="add a music or sound track before publishing", why="the file has no audio stream"))
    elif loud.get("integrated_lufs") is not None:
        i, tp = loud["integrated_lufs"], loud.get("true_peak_dbtp")
        if abs(i - (-14)) > 1 or (tp is not None and tp > -1):
            out.append(dict(do=f'wise music-enhance "{name}" --for trailer',
                            why=f"audio is {i:.1f} LUFS, true peak {tp:.1f} dBTP; the trailer target is -14 LUFS and -1 dBTP (the picture is copied, not re-encoded)"
                            if tp is not None else f"audio is {i:.1f} LUFS; the trailer target is -14 LUFS"))
    f = r["first_real_frame"]
    if f.get("found") and f["at_s"] > 0.3:
        out.append(dict(do=f"trim the first {f['at_s']:.2f} s", why="the clip opens on black; the first second decides whether people keep watching"))
    c = r["cuts"]
    if c.get("found") and r["duration_s"] >= 6 and c["count"] == 0:
        out.append(dict(do=f'wise video contact "{name}" sheet.png', why="one unbroken shot: pick moments from a contact sheet and cut a trailer with wise video compile"))
    if "sheet" not in r:
        out.append(dict(do=f'wise scan "{name}" --sheet', why="writes a contact sheet of timestamped frames to look at"))
    return out


def fingerprint_folder(folder: Path, want_sheet: str | None = None, scene: float = SCENE) -> dict:
    files = videos_in(folder)
    clips = []
    for p in files:
        try:
            clips.append(fingerprint(p, want_sheet, scene))
        except ClipError as e:
            clips.append(dict(kind="video", file=str(p), error=str(e)))
    good = [c for c in clips if "error" not in c]
    return dict(kind="videos", path=str(folder.resolve()), count=len(clips), total_s=round(sum(c["duration_s"] for c in good), 3),
                total_bytes=sum(c["bytes"] for c in good), clips=clips)


def _human(n: int) -> str:
    for unit, size in (("GB", 1 << 30), ("MB", 1 << 20), ("kB", 1 << 10)):
        if n >= size:
            return f"{n / size:.1f} {unit}"
    return f"{n} B"


def format_video(r: dict) -> str:
    if "error" in r:
        return f"{r['file']}\n  could not read: {r['error']}"
    v, a = r["video"], r["audio"]
    lines = [f"{Path(r['file']).name}  (video file)", f"  path:        {r['file']}",
             f"  container:   {r['container']}, {_human(r['bytes'])}, {r['duration_s']:.2f} s"
             + (f", {r['bitrate_kbps']} kb/s" if r["bitrate_kbps"] else ", bitrate not found"),
             f"  picture:     {v['width']}x{v['height']} {v['orientation']}, {v['fps']:g} fps" if v["fps"] else f"  picture:     {v['width']}x{v['height']}, fps not found",
             f"               {v['codec']}" + (f" {v['profile']}" if v["profile"] else "") + (f", {v['pix_fmt']}" if v["pix_fmt"] else "")
             + (f", {v['frames']} frames" if v["frames"] else "")]
    if not a["found"]:
        lines.append("  audio:       not found (no audio stream)")
    else:
        lines.append(f"  audio:       {a['codec']}, {a['sample_rate'] or '?'} Hz, {a['channels'] or '?'} ch"
                     + (f", {a['bitrate_kbps']} kb/s" if a["bitrate_kbps"] else "") + (f", {a['streams']} streams" if a["streams"] > 1 else ""))
        lo = a["loudness"]
        if lo.get("integrated_lufs") is not None:
            lines.append(f"  loudness:    {lo['integrated_lufs']:.1f} LUFS integrated, true peak {lo['true_peak_dbtp']:.1f} dBTP"
                         + (f", range {lo['lra_lu']:.1f} LU" if lo.get("lra_lu") is not None else "") + "  (measured, never played)")
        else:
            lines.append(f"  loudness:    not measured ({lo.get('note') or 'no reading'})")
    c = r["cuts"]
    lines.append(f"  cuts:        {c['count']} scene cuts, {c['shots']} shots, average shot {c['average_shot_s']} s" if c.get("found")
                 else f"  cuts:        not measured ({c.get('note')})")
    if c.get("found") and c["count"]:
        lines.append("               at " + ", ".join(f"{t:.2f}" for t in c["at_s"][:12]) + (" ..." if c["count"] > 12 else "") + " s")
    f = r["first_real_frame"]
    lines.append(f"  first frame: {f['at_s']:.2f} s ({f['note']})" if f.get("found") else f"  first frame: not found ({f.get('note')})")
    if "sheet" in r:
        s = r["sheet"]
        lines.append(f"  sheet:       {s['file']} (a frame every {s['every_s']} s)" if s["written"] else f"  sheet:       not written ({s['note']})")
    if r["routes"]:
        lines.append("  what to try next:")
        lines += [f"    {n}. {rt['do']}  ({rt['why']})" for n, rt in enumerate(r["routes"], 1)]
    return "\n".join(lines)


def format_folder(r: dict) -> str:
    lines = [f"{Path(r['path']).name}  (folder of videos)", f"  path:   {r['path']}",
             f"  clips:  {r['count']}, {r['total_s']:.1f} s in all, {_human(r['total_bytes'])}", ""]
    names = [Path(c["file"]).name for c in r["clips"]]
    w = max([4] + [len(n) for n in names])
    lines.append(f"  {'file':<{w}}  {'dur s':>7} {'size':>10} {'fps':>6} {'codec':>6} {'kb/s':>6} {'LUFS':>6} {'TP':>6} {'cuts':>5} {'shot s':>6} {'first':>6}")
    for n, c in zip(names, r["clips"]):
        if "error" in c:
            lines.append(f"  {n:<{w}}  could not read: {c['error']}")
            continue
        v, lo, cu, f = c["video"], c["audio"].get("loudness") or {}, c["cuts"], c["first_real_frame"]

        def num(x, fmt="{:.1f}"):
            return "n/a" if x is None else fmt.format(x)
        lines.append(f"  {n:<{w}}  {c['duration_s']:>7.2f} {str(v['width']) + 'x' + str(v['height']):>10} {num(v['fps'], '{:g}'):>6} {str(v['codec'])[:6]:>6} "
                     f"{num(c['bitrate_kbps'], '{}'):>6} {num(lo.get('integrated_lufs')):>6} {num(lo.get('true_peak_dbtp')):>6} "
                     f"{num(cu.get('count'), '{}'):>5} {num(cu.get('average_shot_s'), '{}'):>6} {num(f.get('at_s'), '{:.2f}'):>6}")
    sheets = [c["sheet"]["file"] for c in r["clips"] if c.get("sheet", {}).get("written")]
    if sheets:
        lines += ["", "  sheets: " + ", ".join(sheets)]
    lines += ["", "  LUFS and TP are the audio's integrated loudness and true peak; n/a means no audio stream or too short to measure.",
              "  For one clip in full: wise scan <file>"]
    return "\n".join(lines)
