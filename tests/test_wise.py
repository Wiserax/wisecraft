# Ported from Universal Modder (https://github.com/rehan-remade/universal-modder), tests/test_um.py.
# Copyright (c) 2026 Rehan and universal-modder contributors. MIT License; see LICENSE and NOTICE.
"""Offline tests for the CLI shell, the trailer compiler, the skills and the manifests.

    .venv/bin/python -m pytest -q tests/test_wise.py

No network, no audio playback. The ffmpeg tests skip when ffmpeg is not installed.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import wave
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import wisecraft  # noqa: E402
from wisecraft import cli, video  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
FFMPEG = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg")


def make(root: Path, files: dict):
    for rel, data in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data if isinstance(data, bytes) else data.encode())


def exit_code(argv) -> int:
    with pytest.raises(SystemExit) as e:
        cli.main(argv)
    return e.value.code or 0


# --------------------------------------------------------------------------- cli

@pytest.mark.parametrize("group", cli.GROUPS)
def test_cli_help_for_every_group(group, capsys):
    assert exit_code([group, "--help"]) == 0
    assert f"wise {group}" in capsys.readouterr().out


@pytest.mark.parametrize("argv", [
    ["video", "probe"], ["video", "contact"], ["video", "first-frame"], ["video", "beats"], ["video", "compile"],
])
def test_cli_help_for_subcommands(argv, capsys):
    assert exit_code(argv + ["--help"]) == 0
    assert "usage: wise " + argv[0] in capsys.readouterr().out


def test_cli_group_docstrings_show_wz_examples(capsys):
    for group in ("video",):
        assert exit_code([group, "--help"]) == 0
        out = capsys.readouterr().out
        assert f"wise {group} " in out and "um " + group not in out


def test_cli_version_and_no_group(capsys):
    assert exit_code(["--version"]) == 0
    assert capsys.readouterr().out.strip() == f"wisecraft {wisecraft.__version__}"
    assert exit_code([]) == 1


def test_video_mux_is_not_ported(capsys):
    # mux joined the Windows recorder's raw output; there is no such recorder here
    assert exit_code(["video", "mux", "--help"]) == 2
    assert not hasattr(video, "mux")


def test_help_lists_only_the_kept_commands(capsys):
    assert cli.GROUPS == ["scan", "qa", "board", "music-enhance", "video"]
    assert exit_code(["--help"]) == 0
    out = capsys.readouterr().out
    listed = re.findall(r"^    ([a-z][\w-]+)", out, re.M)
    assert listed == cli.GROUPS, listed
    for gone in ("kb", "publish", "dupframes"):
        assert exit_code([gone, "--help"]) == 2          # argparse: invalid choice
        assert "invalid choice" in capsys.readouterr().err
    assert exit_code(["loudness", "--help"]) == 0        # the old name still answers for one release, unlisted
    assert "music-enhance --check" in capsys.readouterr().out


def test_unicode_output_on_cp1252_console(tmp_path):
    # a project name outside cp1252 must not UnicodeEncodeError when stdout isn't UTF-8
    make(tmp_path, {"project.godot": 'config_version=5\n[application]\nconfig/name="Señor → test"\n'})
    env = dict(os.environ, PYTHONIOENCODING="cp1252", PYTHONPATH=str(REPO))
    r = subprocess.run([sys.executable, "-m", "wisecraft", "scan", str(tmp_path)], capture_output=True, encoding="utf-8", env=env)
    assert r.returncode == 0 and "Señor →" in r.stdout


# --------------------------------------------------------------------------- attribution

@pytest.mark.parametrize("rel", ["wisecraft/cli.py", "wisecraft/common.py", "wisecraft/scan.py", "wisecraft/video.py", "tests/test_wise.py"])
def test_ported_files_carry_the_attribution_header(rel):
    head = (REPO / rel).read_text(encoding="utf-8").splitlines()[:2]
    assert head[0].startswith("# Ported from Universal Modder (https://github.com/rehan-remade/universal-modder), ")
    assert head[1] == "# Copyright (c) 2026 Rehan and universal-modder contributors. MIT License; see LICENSE and NOTICE."


# --------------------------------------------------------------------------- video

def test_video_fonts_ship_with_their_licences():
    for font in (video.TITLE_FONT, video.BODY_FONT, video.MONO_FONT):
        assert font.is_file() and font.stat().st_size > 50_000, font
    for name in ("OFL-SpaceGrotesk.txt", "OFL-JetBrainsMono.txt"):
        assert "SIL OPEN FONT LICENSE" in (video.FONTS / name).read_text(encoding="utf-8").upper()


def test_video_helpers():
    assert list(video.frange(0, 1, 0.5)) == [0, 0.5, 1.0]
    assert video._seg_dur({"beats": 4}, 120) == 2.0 and video._seg_dur({"dur": 1.5}, None) == 1.5 and video._seg_dur({}, None) == 4.0
    with pytest.raises(SystemExit):
        video._seg_dur({"beats": 4}, None)                         # beats need a bpm
    assert video._rgba("#B6FF3B") == (182, 255, 59, 255) and video._rgba("#0A0D12E0") == (10, 13, 18, 224)
    assert video._rgba(None, "#FFFFFF") == (255, 255, 255, 255)
    assert video._fill_filter("crop", 640, 360).startswith("scale=640:360:force_original_aspect_ratio=increase")
    assert "pad=640:360" in video._fill_filter("pad", 640, 360)
    blur = video._fill_filter("blur", 640, 360, zoom=1.2, crop=[0, 10, 300, 200])
    assert blur.startswith("crop=300:200:0:10,split[fa][fb]") and "boxblur" in blur and blur.endswith(",scale=iw*1.2:ih*1.2,crop=640:360")
    # text is drawn for a 1080-high landscape frame; a vertical frame scales with its width, not its height
    assert video._scale(1920, 1080) == 1.0 and video._scale(1080, 1920) == 1.0 and video._scale(640, 360) == pytest.approx(1 / 3)


def right_edge(png) -> int:
    return Image.open(png).getchannel("A").getbbox()[2]


def test_video_graphics(tmp_path):
    theme = {"accent": "#B6FF3B"}
    x0 = video.title_chip("Build. Merge. Survive.", "wave 12", 1920, 1080, theme, tmp_path / "t.png")
    assert x0 == 64 and Image.open(tmp_path / "t.png").size == (1920, 1080) and right_edge(tmp_path / "t.png") < 1920 - 64
    # a long title on a phone-width frame shrinks to fit instead of running off the right edge
    long = "A very long title that would never fit on one line of a vertical trailer at full size"
    x0 = video.title_chip(long, "@studio", 1080, 1920, theme, tmp_path / "v.png")
    assert Image.open(tmp_path / "v.png").size == (1080, 1920) and right_edge(tmp_path / "v.png") <= 1080 - x0
    video.hook_text("Hold the wall, hold the wall, hold the wall, hold the wall.", 1080, 1920, theme, tmp_path / "h.png")
    box = Image.open(tmp_path / "h.png").getchannel("A").point(lambda v: 255 if v > 200 else 0).getbbox()   # the letters, not their shadow
    assert 0 < box[0] and box[2] < 1080 and box[2] - box[0] > 0.8 * 1080
    video.card({"title": "Game name", "sub": "Play free in your browser"}, 640, 360, theme, tmp_path / "c.png")
    video.badge("01/05", 640, 360, theme, tmp_path / "b.png")
    assert Image.open(tmp_path / "c.png").size == (640, 360) and Image.open(tmp_path / "c.png").mode == "RGB"
    assert Image.open(tmp_path / "b.png").getchannel("A").getbbox()


def clip(path, size="640x360", dur=3, fps=30):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"testsrc2=s={size}:d={dur}:r={fps}", "-f", "lavfi", "-i", f"sine=f=440:d={dur}",
                    "-shortest", str(path)], check=True)


@FFMPEG
def test_compile_small_edl(tmp_path):
    for i in range(2):
        clip(tmp_path / f"c{i}.mp4")
    edl = {"size": [640, 360], "fps": 30, "bpm": 120, "beat_lock": True, "transition": {"type": "cut"},
           "segments": [{"clip": "c0.mp4", "in": 0, "beats": 4, "hook": "Hello"},
                        {"clip": "c1.mp4", "in": 0.5, "beats": 4, "title": "A title", "credit": "@someone", "transition": {"type": "fade", "duration": 0.3}},
                        {"card": {"title": "The end"}, "dur": 1.5}]}
    (tmp_path / "edl.json").write_text(json.dumps(edl))
    video.compile_edl(tmp_path / "edl.json", str(tmp_path / "out.mp4"))
    info = video.probe(tmp_path / "out.mp4")
    assert abs(info["duration"] - (2 + 2 + 1.5)) < 0.15 and info["audio"]
    assert (info["width"], info["height"], info["fps"]) == (640, 360, 30)


@FFMPEG
def test_compile_cut_then_fade(tmp_path, monkeypatch):
    # a cut then a fade: xfade's first input is concat's output (AVTB), so every join input must end at AVTB.
    # FFmpeg 7.0/7.1's setpts marks the frame rate unknown (1/0), which xfade refuses, so each join input also
    # declares fps=. Newer FFmpeg passes without it, hence the graph check.
    calls, real_ff = [], video.ff

    def spy(*args, **kw):
        calls.append([str(a) for a in args])
        return real_ff(*args, **kw)

    monkeypatch.setattr(video, "ff", spy)
    clip(tmp_path / "c.mp4", dur=2, fps=24)
    edl = {"size": [640, 360], "fps": 24, "transition": {"type": "cut"},
           "segments": [{"clip": "c.mp4", "dur": 1.0}, {"clip": "c.mp4", "in": 0.5, "dur": 1.0},
                        {"card": {"title": "The end"}, "dur": 1.0, "transition": {"type": "fade", "duration": 0.25}}]}
    (tmp_path / "edl.json").write_text(json.dumps(edl))
    video.compile_edl(tmp_path / "edl.json", str(tmp_path / "out.mp4"))
    graph = calls[-1][calls[-1].index("-filter_complex") + 1].split(";")
    assert all(any(g.startswith(f"[{k}:v]") and "fps=24" in g for g in graph) for k in range(3))
    assert abs(video.probe(tmp_path / "out.mp4")["duration"] - (1 + 1 + 1 - 0.25)) < 0.15


@FFMPEG
def test_compile_vertical_with_per_segment_speed(tmp_path, monkeypatch, capsys):
    # a phone-shaped trailer: slow motion reads less of the clip, fast motion more, and "dur" stays output seconds
    calls, real_ff = [], video.ff

    def spy(*args, **kw):
        calls.append([str(a) for a in args])
        return real_ff(*args, **kw)

    monkeypatch.setattr(video, "ff", spy)
    clip(tmp_path / "c.mp4", size="360x640", dur=3)
    edl = {"size": [360, 640], "fps": 30, "transition": {"type": "cut"}, "fade_out": 0.2,
           "segments": [{"clip": "c.mp4", "in": 0.5, "dur": 1.0, "speed": 0.5, "title": "Slow"},
                        {"clip": "c.mp4", "in": 0, "dur": 1.0, "speed": 2.0, "fill": "crop"}]}
    (tmp_path / "edl.json").write_text(json.dumps(edl))
    video.compile_edl(tmp_path / "edl.json", str(tmp_path / "out.mp4"), preview=True)
    info = video.probe(tmp_path / "out.mp4")
    assert (info["width"], info["height"]) == (180, 320) and abs(info["duration"] - 2.0) < 0.15
    slow, fast = calls[0], calls[1]
    assert slow[slow.index("-t") + 1] == "0.600" and "setpts=(PTS-STARTPTS)/0.5" in slow[slow.index("-filter_complex") + 1]
    assert fast[fast.index("-t") + 1] == "2.100" and "atempo=2.0000" in fast[fast.index("-filter_complex") + 1]
    # a segment that asks for more of the clip than there is stops with the reason
    edl["segments"][1]["dur"] = 2.0
    (tmp_path / "edl.json").write_text(json.dumps(edl))
    with pytest.raises(SystemExit):
        video.compile_edl(tmp_path / "edl.json", str(tmp_path / "out2.mp4"), preview=True)
    assert "runs past the end" in capsys.readouterr().err


@FFMPEG
def test_probe_contact_first_frame(tmp_path, capsys):
    # one second of black (a loading screen), then two of a busy test pattern
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=black:s=320x180:d=1:r=30", "-f", "lavfi", "-i", "testsrc2=s=320x180:d=2:r=30",
                    "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0", str(tmp_path / "cap.mp4")], check=True)
    info = video.probe(tmp_path / "cap.mp4")
    assert (info["width"], info["height"], info["audio"]) == (320, 180, False) and abs(info["duration"] - 3) < 0.1
    assert video._probe_ffmpeg(tmp_path / "cap.mp4")["width"] == 320            # the fallback when ffprobe is missing
    assert video.first_frame(tmp_path / "cap.mp4") == 1.0
    video.contact(tmp_path / "cap.mp4", tmp_path / "sheet.png", every=0.5, cols=4, width=160)
    sheet = Image.open(tmp_path / "sheet.png")
    assert sheet.size[0] == 4 * 160 and sheet.size[1] % (90 + 22) == 0 and "frames" in capsys.readouterr().out
    cli.main(["video", "probe", str(tmp_path / "cap.mp4")])
    assert json.loads(capsys.readouterr().out)["fps"] == 30


@FFMPEG
def test_beats_finds_the_tempo(tmp_path):
    import numpy as np
    sr, bpm = 22050, 120
    x = np.zeros(sr * 8, np.float32)
    tick = (np.hanning(600) * np.sin(np.arange(600) * 0.9)).astype(np.float32)
    for start in range(0, x.size - 600, int(sr * 60 / bpm)):
        x[start:start + 600] += tick
    with wave.open(str(tmp_path / "click.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((x * 20000).astype("<i2").tobytes())
    found = video.beats(tmp_path / "click.wav")
    assert abs(found["bpm"] - bpm) < 4 and found["duration"] == 8.0 and found["first_beat"] < 0.5


# --------------------------------------------------------------------------- skills and manifests

def skill_files() -> list[Path]:
    return sorted((REPO / "skills").glob("*/SKILL.md"))


def tree(d: Path) -> dict:
    return {p.relative_to(d).as_posix(): p.read_bytes() for p in sorted(d.rglob("*")) if p.is_file()}


def test_skill_copies_match():
    # .agents/skills and .claude/skills are real copies of skills/ (Windows clones turn symlinks into text files)
    if not skill_files():
        pytest.skip("no skills/*/SKILL.md yet")
    src = tree(REPO / "skills")
    for copy in (".agents/skills", ".claude/skills"):
        assert (REPO / copy).is_dir(), f"{copy} is missing: copy skills/ into it"
        assert not (REPO / copy).is_symlink(), f"{copy} must be a folder, not a symlink"
        assert tree(REPO / copy) == src, f"{copy} differs from skills/: replace it with a fresh copy of skills/"


def test_skills_have_front_matter():
    if not skill_files():
        pytest.skip("no skills/*/SKILL.md yet")
    for f in skill_files():
        m = re.match(r"---\n(.*?)\n---\n(.*)", f.read_text(encoding="utf-8"), re.S)
        assert m, f"{f}: needs YAML front matter"
        meta, body = dict(re.findall(r"^(\w[\w-]*):\s*(.*)$", m.group(1), re.M)), m.group(2)
        assert meta.get("name") == f.parent.name, f"{f}: name {meta.get('name')!r} must equal its folder name"
        assert len(str(meta.get("description") or "")) >= 200, f"{f}: the description decides when the skill is used; write 200+ characters"
        assert body.strip(), f"{f}: empty skill"


def test_manifests_agree():
    # one name and one version everywhere a tool reads them; files that don't exist yet are skipped
    found = {"wisecraft.__version__": ("wisecraft", wisecraft.__version__)}
    for rel in ("plugin.json", ".claude-plugin/plugin.json", ".codex-plugin/plugin.json", "gemini-extension.json"):
        if (REPO / rel).exists():
            d = json.loads((REPO / rel).read_text(encoding="utf-8"))
            found[rel] = (d.get("name"), d.get("version"))
    if (REPO / "pyproject.toml").exists():
        project = (REPO / "pyproject.toml").read_text(encoding="utf-8").split("[project]", 1)[1].split("\n[", 1)[0]
        field = lambda k: re.search(rf'^{k}\s*=\s*"([^"]+)"', project, re.M).group(1)
        found["pyproject.toml"] = (field("name"), field("version"))
    assert set(found.values()) == {("wisecraft", wisecraft.__version__)}, found
