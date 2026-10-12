# Ported from Universal Modder (https://github.com/rehan-remade/universal-modder), tests/test_um.py.
# Copyright (c) 2026 Rehan and universal-modder contributors. MIT License; see LICENSE and NOTICE.
"""Offline tests for qa (the virtual testers) and board, and for the loudness meter in music-enhance.

    .venv/bin/python -m pytest -q tests/test_web.py

No network (browser runs talk to an http.server thread on 127.0.0.1), no audio playback (ffmpeg only measures,
browsers run muted). The ffmpeg tests skip without ffmpeg; the real browser runs skip unless WISE_PLAYWRIGHT
names a folder node can load Playwright from, e.g. a game project that has it installed.
"""
import argparse
import functools
import http.server
import json
import math
import os
import shlex
import shutil
import subprocess
import sys
import threading
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from wisecraft import board, music_enhance, qa  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
FFMPEG = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg")
NODE = pytest.mark.skipif(shutil.which("node") is None, reason="needs node")


def wise(*argv):
    """Run `wise <argv>` in-process with only these commands registered (the other groups are tested elsewhere)."""
    ap = argparse.ArgumentParser(prog="wise")
    sub = ap.add_subparsers(dest="group")
    for module in (qa, board, music_enhance):
        module.register(sub)
    a = ap.parse_args([str(x) for x in argv])
    a.func(a)


def exit_code(*argv) -> int:
    with pytest.raises(SystemExit) as e:
        wise(*argv)
    return e.value.code


def make(root: Path, files: dict):
    for rel, data in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data if isinstance(data, bytes) else data.encode())


@pytest.fixture
def serve():
    """serve(folder, headers=None) -> base URL of an http.server thread on 127.0.0.1 (closed after the test).
    POSTs are answered 200 and their paths kept in serve.posts, so a test can see a beacon reach the server."""
    servers, posts = [], []

    def start(folder: Path, headers=None) -> str:
        class Handler(http.server.SimpleHTTPRequestHandler):
            def end_headers(self):
                for prefix, name, value in headers or []:
                    if self.path.startswith(prefix):
                        self.send_header(name, value)
                super().end_headers()

            def do_POST(self):
                self.rfile.read(int(self.headers.get("Content-Length") or 0))
                posts.append(self.path)
                self.send_response(200)
                self.send_header("Content-Length", "0")
                self.end_headers()

            def log_message(self, *args):
                pass

        srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Handler, directory=str(folder)))
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        servers.append(srv)
        return f"http://127.0.0.1:{srv.server_address[1]}"

    start.posts = posts
    yield start
    for srv in servers:
        srv.shutdown()
        srv.server_close()


# --------------------------------------------------------------------------- qa

def qa_args(*argv):
    ap = argparse.ArgumentParser()
    qa.register(ap.add_subparsers())
    return ap.parse_args(["qa", *argv])


def test_qa_options_defaults():
    o = qa.options(qa_args("http://127.0.0.1:5173/play.html"))
    assert o == {"url": "http://127.0.0.1:5173/play.html", "engine": "chromium", "width": 390, "height": 844, "dpr": 2,
                 "out": os.path.join("qa-out", "chromium-390x844-casual"), "seconds": 20, "seed": 1, "selectors": [],
                 "startSelector": None, "area": None, "ready": 'document.readyState === "complete"',
                 "block": [], "noOverflow": False, "timeoutMs": 60000, "persona": "casual", "buy": None, "maxP95": None}


def test_qa_options_from_flags(tmp_path):
    o = qa.options(qa_args("https://example.com/play.html", "--engine", "webkit", "--size", "320x568", "--out", str(tmp_path),
                           "--seconds", "5", "--taps", "12", "--seed", "7", "--selector", "#shop", "[data-tab=pass]", "--selector", "#close",
                           "--start-selector", "#play", "--no-overflow", "--block", "**/collect", "--block", "**/api/*",
                           "--ready", "window.__game && __game.run", "--area", "canvas#field", "--timeout", "5", "--channel", "chrome",
                           "--persona", "spender", "--buy", "[data-buy]", "--max-p95", "20"))
    assert (o["persona"], o["buy"], o["maxP95"]) == ("spender", "[data-buy]", 20)
    assert (o["engine"], o["width"], o["height"], o["out"]) == ("webkit", 320, 568, str(tmp_path))
    assert (o["seconds"], o["taps"], o["seed"]) == (5, 12, 7)
    assert o["selectors"] == ["#shop", "[data-tab=pass]", "#close"] and o["startSelector"] == "#play" and o["area"] == "canvas#field"
    assert o["block"] == ["**/collect", "**/api/*"] and o["noOverflow"] is True
    assert o["ready"] == "window.__game && __game.run" and o["timeoutMs"] == 5000 and o["channel"] == "chrome"
    cmd = qa.node_command(qa.HARNESS, o, "node")
    assert cmd[:2] == ["node", str(qa.HARNESS)] and len(cmd) == 3 and json.loads(cmd[2]) == o     # one JSON argument
    assert qa.HARNESS.is_file()


def test_qa_local_file_becomes_a_file_url(tmp_path):
    make(tmp_path, {"index.html": "<canvas></canvas>"})
    assert qa.options(qa_args(str(tmp_path / "index.html")))["url"] == (tmp_path / "index.html").resolve().as_uri()


def test_qa_dry_run_prints_the_command_and_runs_nothing(monkeypatch, capsys):
    entry = os.path.join("proj", "node_modules", "playwright", "index.js")
    monkeypatch.setattr(qa, "find_playwright", lambda node, explicit=None, cwd=None: entry)
    monkeypatch.setattr(qa, "run_harness", lambda *a, **k: pytest.fail("a dry run must not start a browser"))
    wise("qa", "http://127.0.0.1:5173/play.html", "--engine", "webkit", "--size", "360x740", "--dry-run")
    cmd = shlex.split(capsys.readouterr().out.strip())
    assert cmd[1] == str(qa.HARNESS) and len(cmd) == 3
    o = json.loads(cmd[2])
    assert (o["url"], o["engine"], o["width"], o["playwright"]) == ("http://127.0.0.1:5173/play.html", "webkit", 360, entry)
    assert o["out"] == os.path.join("qa-out", "webkit-360x740-casual")


def test_qa_missing_playwright_says_how_to_install(monkeypatch, capsys):
    monkeypatch.setattr(qa, "need_node", lambda: "node")
    monkeypatch.setattr(qa, "_resolve", lambda node, base: None)
    monkeypatch.delenv("WISE_PLAYWRIGHT", raising=False)
    assert exit_code("qa", "http://127.0.0.1:5173") == 2
    err = capsys.readouterr().err
    assert "playwright not found" in err and "npm i -D playwright && npx playwright install chromium webkit" in err
    assert "WISE_PLAYWRIGHT" in err and "--playwright DIR" in err
    # the dry run still prints the command, with the same advice on stderr
    wise("qa", "http://127.0.0.1:5173", "--dry-run")
    io = capsys.readouterr()
    assert '"playwright":null' in io.out and "npm i -D playwright" in io.err


def test_qa_usage_errors_exit_2(capsys):
    assert exit_code("qa", "http://127.0.0.1:5173", "--size", "banana") == 2
    assert exit_code("qa", "not-a-url") == 2
    assert exit_code("qa", "http://127.0.0.1:5173", "--seconds", "-1") == 2
    assert "--size wants WIDTHxHEIGHT" in capsys.readouterr().err
    assert exit_code("qa", "http://127.0.0.1:5173", "--persona", "whale") == 2
    assert exit_code("qa", "http://127.0.0.1:5173", "--max-p95", "0") == 2


def test_qa_report_and_board(tmp_path):
    from PIL import Image
    shots = []
    for i, size in enumerate([(390, 844), (390, 844), (320, 568)]):
        f = tmp_path / f"{i + 1}-shot.png"
        Image.new("RGB", size, (20 * i, 40, 60)).save(f)
        shots.append(str(f))
    board_png = qa.make_board(shots + [str(tmp_path / "missing.png")], tmp_path, "PASS  chromium 390x844  spender")
    im = Image.open(board_png)
    assert Path(board_png).name == "board.png" and im.width > 3 * 290 and im.height > 640
    r = {"ok": True, "engine": "chromium", "size": "390x844", "url": "http://x/", "persona": "spender",
         "ready": {"ok": True, "ms": 10, "expression": "1"}, "game": {"found": False, "keys": [], "hooks": []}, "steps": [],
         "taps": {"done": 4, "planned": 4, "seconds": 2, "seed": 1, "area": {"source": "canvas"}},
         "spends": [{"at": 0.5, "label": "Upgrade"}, {"at": 1.5, "label": "Upgrade"}, {"at": 1.9, "label": "Open chest"}],
         "frameTime": {"frames": 120, "fps": 60.0, "p50": 16.7, "p95": 17.1, "p99": 18.0, "over33": 0, "worst": 19.0, "maxP95": None},
         "blocked": {"patterns": [], "requests": 0}, "errors": [], "overflow": [], "failedRequests": [], "screenshots": shots, "board": board_png}
    text = qa.format_result(r)
    assert "persona:      spender" in text and "bought:       3" in text and "- Upgrade  x2" in text
    assert "p95 17.1 ms" in text and "headless" in text and "board:        " + board_png in text


@NODE
def test_find_playwright_from_flag_env_and_cwd(tmp_path, monkeypatch):
    make(tmp_path, {"proj/node_modules/playwright/package.json": '{"name":"playwright","version":"0.0.0","main":"index.js"}',
                    "proj/node_modules/playwright/index.js": "module.exports = {};", "empty/keep.txt": ""})
    node = shutil.which("node")
    want = (tmp_path / "proj/node_modules/playwright/index.js").resolve()
    monkeypatch.delenv("WISE_PLAYWRIGHT", raising=False)
    assert qa.find_playwright(node, cwd=str(tmp_path / "empty")) is None
    assert Path(qa.find_playwright(node, cwd=str(tmp_path / "proj"))).resolve() == want
    for folder in ("proj", "proj/node_modules", "proj/node_modules/playwright"):          # any of the three will do
        assert Path(qa.find_playwright(node, explicit=str(tmp_path / folder), cwd=str(tmp_path / "empty"))).resolve() == want
    monkeypatch.setenv("WISE_PLAYWRIGHT", str(tmp_path / "proj"))
    assert Path(qa.find_playwright(node, cwd=str(tmp_path / "empty"))).resolve() == want
    assert qa.find_playwright(node, explicit=str(tmp_path / "empty"), cwd=str(tmp_path / "proj")) is None  # the flag is final


def real_playwright():
    """Skip unless WISE_PLAYWRIGHT names a folder node can load Playwright from."""
    node, where = shutil.which("node"), os.environ.get("WISE_PLAYWRIGHT")
    if not node or not where or not qa._resolve(node, where):
        pytest.skip("set WISE_PLAYWRIGHT to a folder that has Playwright installed to run the real browser tests")


def run_qa(capsys, *argv):
    """-> (exit code, result). Skips when the browser itself is missing (exit 2)."""
    capsys.readouterr()
    code = 0
    try:
        wise("qa", *argv, "--json")
    except SystemExit as e:
        code = e.code
    io = capsys.readouterr()
    if code == 2:
        pytest.skip("browser not installed: " + io.err.strip()[:200])
    return code, json.loads(io.out)


@pytest.mark.parametrize("engine, ready", [("chromium", "window.__game"),
                                           ("webkit", "window.__game && window.__game.audioMuted === true")])
def test_qa_real_run_gate(tmp_path, serve, capsys, engine, ready):
    real_playwright()
    base = serve(FIXTURES / "qa")
    out = tmp_path / "shots"
    code, r = run_qa(capsys, base + "/clean.html", "--engine", engine, "--seconds", "2", "--out", out, "--ready", ready,
                     "--start-selector", "#play", "--timeout", "20")
    assert code == 0 and r["ok"] is True and r["errors"] == [] and r["overflow"] == [], r
    assert r["engine"] == engine and r["size"] == "390x844" and r["ready"]["ok"]
    assert r["game"]["found"] and {"taps", "started", "run"} <= set(r["game"]["keys"])
    assert r["steps"] == [{"selector": "#play", "found": True, "via": "tap"}]
    assert r["taps"]["done"] == 4 and r["taps"]["area"]["source"] == "canvas"
    assert r["blocked"]["requests"] == 0 and r["failedRequests"] == []        # nothing is blocked by default
    assert "/api/events" in serve.posts                                         # the beacon reached the real server
    names = [Path(s).name for s in r["screenshots"]]
    assert names == ["1-start.png", "step-1.png", "2-middle.png", "3-end.png"] and all((out / n).stat().st_size > 500 for n in names)
    assert r["persona"] == "casual" and r["frameTime"]["frames"] > 0 and r["frameTime"]["p95"] > 0
    assert Path(r["board"]).name == "board.png" and (out / "board.png").stat().st_size > 1000

    code, r = run_qa(capsys, base + "/broken.html", "--engine", engine, "--seconds", "1", "--out", out, "--timeout", "20")
    assert code == 1 and r["ok"] is False
    assert any("boom from the game" in e for e in r["errors"]) and any("late crash" in e for e in r["errors"])
    kinds = {o["selector"]: o for o in r["overflow"]}
    assert kinds["html"]["scrollWidth"] == 520 and kinds["div#hud"]["right"] == 520 and kinds["div#hud"]["innerWidth"] == 390
    # --no-overflow drops that half of the gate; the errors still fail it
    code, r = run_qa(capsys, base + "/broken.html", "--engine", engine, "--seconds", "0", "--out", out, "--no-overflow")
    assert code == 1 and r["gate"] == {"errors": True, "overflow": False} and r["overflow"]


def test_qa_real_run_missing_selector_fails(tmp_path, serve, capsys):
    real_playwright()
    code, r = run_qa(capsys, serve(FIXTURES / "qa") + "/clean.html", "--seconds", "0", "--out", tmp_path, "--selector", "#nope")
    assert code == 1 and r["errors"] == ["selector not found: #nope"] and r["steps"][0]["found"] is False


def test_qa_real_run_block_is_opt_in(tmp_path, serve, capsys):
    real_playwright()
    base = serve(FIXTURES / "qa")
    code, r = run_qa(capsys, base + "/clean.html", "--engine", "webkit", "--seconds", "1", "--out", tmp_path,
                     "--start-selector", "#play", "--block", "**/api/events", "--timeout", "20")
    assert code == 0 and r["blocked"]["patterns"] == ["**/api/events"] and r["blocked"]["requests"] >= 1
    assert serve.posts == [] and r["failedRequests"] == []                     # answered in the browser, never sent


def test_qa_real_run_spender_never_pays_real_money(tmp_path, serve, capsys):
    real_playwright()
    code, r = run_qa(capsys, serve(FIXTURES / "qa") + "/shop.html", "--persona", "spender", "--seconds", "3", "--taps", "12",
                     "--out", tmp_path, "--ready", "window.__game", "--timeout", "20", "--no-board")
    assert code == 0 and r["persona"] == "spender", r
    labels = {x["label"] for x in r["spends"]}
    assert labels and labels <= {"Upgrade", "Open chest"} and r["spends"][0]["label"] in {"Upgrade", "Open chest"}
    assert "board" not in r


# --------------------------------------------------------------------------- board

def test_board_init_writes_a_starter_pair(tmp_path, capsys):
    d = tmp_path / "design" / "pacts"
    wise("board", "--init", d)
    mock, brd = (d / "mockups.html").read_text(), (d / "board.html").read_text()
    assert 'class="screen" id="s1"' in mock and 'class="screen" id="s2"' in mock and "width:390px;height:844px" in mock
    assert 'src="shots/s1.png"' in brd and 'src="shots/s2.png"' in brd and "wise board mockups.html --board board.html" in brd
    assert "next: edit the screens" in capsys.readouterr().out
    (d / "mockups.html").write_text("mine")
    assert exit_code("board", "--init", d) == 1                       # never overwrites work
    assert (d / "mockups.html").read_text() == "mine" and "--force" in capsys.readouterr().err
    wise("board", "--init", d, "--force")
    assert (d / "mockups.html").read_text() == mock


def test_board_dry_run_command(tmp_path, monkeypatch, capsys):
    wise("board", "--init", tmp_path)
    capsys.readouterr()
    entry = os.path.join("proj", "node_modules", "playwright", "index.js")
    monkeypatch.setattr(board, "find_playwright", lambda node, explicit=None, cwd=None: entry)
    monkeypatch.setattr(board, "run_harness", lambda *a, **k: pytest.fail("a dry run must not start a browser"))
    wise("board", tmp_path / "mockups.html", "--board", tmp_path / "board.html", "--dry-run")
    cmd = shlex.split(capsys.readouterr().out.strip())
    assert cmd[1] == str(board.RENDER) and board.RENDER.is_file() and len(cmd) == 3
    assert json.loads(cmd[2]) == {"mockups": str(tmp_path / "mockups.html"), "out": str(tmp_path / "shots"), "ids": [],
                                  "board": str(tmp_path / "board.html"), "width": 390, "height": 844, "scale": 2.0, "playwright": entry}
    wise("board", tmp_path / "mockups.html", "--out", tmp_path / "png", "--size", "320x568", "--scale", "3", "--ids", "s2,s1", "--dry-run")
    o = json.loads(shlex.split(capsys.readouterr().out.strip())[2])
    assert (o["out"], o["width"], o["height"], o["scale"], o["ids"], o["board"]) == (str(tmp_path / "png"), 320, 568, 3.0, ["s2", "s1"], None)


def test_board_missing_input_exits_2(tmp_path, capsys):
    assert exit_code("board", tmp_path / "nope.html") == 2
    assert "mockups file not found" in capsys.readouterr().err
    wise("board", "--init", tmp_path)
    assert exit_code("board", tmp_path / "mockups.html", "--board", tmp_path / "other.html") == 2
    assert "board file not found" in capsys.readouterr().err
    assert exit_code("board") == 2
    assert exit_code("board", tmp_path / "mockups.html", "--size", "x") == 2


def test_board_real_render_of_the_starter_screens(tmp_path, capsys):
    real_playwright()
    from PIL import Image
    wise("board", "--init", tmp_path)
    capsys.readouterr()
    try:
        wise("board", tmp_path / "mockups.html", "--json")              # screens only: the starter board loads web fonts
    except SystemExit as e:
        if e.code == 2:
            pytest.skip("browser not installed: " + capsys.readouterr().err.strip()[:200])
        raise
    r = json.loads(capsys.readouterr().out)
    assert [(s["id"], s["width"], s["height"]) for s in r["screens"]] == [("s1", 390, 844), ("s2", 390, 844)]
    assert r["warnings"] == [] and r["board"] is None
    assert Image.open(tmp_path / "shots" / "s1.png").size == (780, 1688)


# --------------------------------------------------------------------------- the loudness meter (music-enhance --check)

EBUR128_LOG = """Input #0, wav, from 'tone.wav':
  Duration: 00:01:04.50, bitrate: 768 kb/s
  Stream #0:0: Audio: pcm_s16le ([1][0][0][0] / 0x0001), 44100 Hz, stereo, s16, 1411 kb/s
[Parsed_ebur128_1 @ 0x1] t: 0.0999792  TARGET:-23 LUFS    M:-120.7 S:-120.7     I: -70.0 LUFS       LRA:   0.0 LU  FTPK: -20.0 dBFS  TPK: -20.0 dBFS
[Parsed_ebur128_1 @ 0x1] t: 0.399979   TARGET:-23 LUFS    M: -14.2 S:-120.7     I: -16.0 LUFS       LRA:   0.0 LU  FTPK: -2.0 dBFS  TPK: -2.0 dBFS
[Parsed_ebur128_1 @ 0x1] t: 2.999979   TARGET:-23 LUFS    M: -12.9 S: -15.4     I: -16.0 LUFS       LRA:   0.0 LU  FTPK: -2.0 dBFS  TPK: -1.2 dBFS
[Parsed_ebur128_1 @ 0x1] t: 3.099979   TARGET:-23 LUFS    M: -19.0 S: -15.1     I: -16.1 LUFS       LRA:   2.0 LU  FTPK: -9.0 dBFS  TPK: -1.2 dBFS
[Parsed_loudnorm_2 @ 0x2]
{
	"input_i" : "-16.12",
	"input_tp" : "-1.23",
	"input_lra" : "4.30",
	"input_thresh" : "-26.40",
	"output_i" : "-24.01"
}
[Parsed_ebur128_1 @ 0x1] Summary:

  Integrated loudness:
    I:         -16.1 LUFS
    Threshold: -26.4 LUFS

  Loudness range:
    LRA:        20.0 LU
    Threshold: -36.4 LUFS

  True peak:
    Peak:       -1.2 dBFS
"""


def test_meter_parse_log():
    r = music_enhance.parse(EBUR128_LOG)
    # integrated, range and peak come from loudnorm's two-decimal measurement, not the ebur128 summary
    assert (r["integrated_lufs"], r["lra_lu"], r["true_peak_dbfs"]) == (-16.12, 4.3, -1.23)
    assert (r["max_momentary_lufs"], r["max_short_term_lufs"]) == (-12.9, -15.1)       # -120.7 is "no window yet"
    assert (r["duration_s"], r["sample_rate"], r["channels"], r["channel_layout"], r["codec"]) == (64.5, 44100, 2, "stereo", "pcm_s16le")
    assert r["silent"] is False and "note" not in r
    without = music_enhance.parse(EBUR128_LOG.replace('"input_i"', '"other"'))                # an ffmpeg without loudnorm
    assert (without["integrated_lufs"], without["true_peak_dbfs"]) == (-16.1, -1.2)
    with pytest.raises(ValueError):
        music_enhance.parse("Stream map '0:a:0' matches no streams.")
    assert music_enhance._channels("5.1(side)") == 6 and music_enhance._channels("3 channels") == 3 and music_enhance._channels("odd") is None


def tone(path: Path, seconds: float = 3, volume: float = 1.0, stereo: bool = False):
    """A 1 kHz sine from ffmpeg's lavfi `sine` source, whose peak amplitude is 1/8, times `volume`."""
    af = f"volume={volume}" + (",pan=stereo|c0=c0|c1=c0" if stereo else "")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
                    f"sine=frequency=1000:duration={seconds}:sample_rate=48000", "-af", af, "-c:a", "pcm_s16le", str(path)], check=True)
    return path


@FFMPEG
def test_meter_of_a_sine(tmp_path):
    # BS.1770: L = -0.691 + 10*log10(sum of K-weighted channel mean squares). The K filter adds +0.691 dB at 1 kHz,
    # so a mono sine of peak amplitude A reads 20*log10(A) - 3.01 LUFS: mean square A^2/2. A = 1/8 * 0.8 = 0.1
    # is -20 dBFS peak and -23.01 LUFS; the same signal on two channels sums to 3.01 dB more.
    expect = 20 * math.log10(0.1) - 3.01
    r = music_enhance.measure(str(tone(tmp_path / "tone.wav", volume=0.8)))
    assert abs(r["integrated_lufs"] - expect) < 1.5 and abs(r["integrated_lufs"] - -23.0) < 0.2
    assert abs(r["true_peak_dbfs"] - -20.0) < 0.5 and r["lra_lu"] < 1.0
    assert abs(r["max_momentary_lufs"] - expect) < 1.5
    assert r["max_short_term_lufs"] is None or abs(r["max_short_term_lufs"] - expect) < 1.5     # one 3 s window at most
    assert (r["duration_s"], r["sample_rate"], r["channels"], r["codec"]) == (3.0, 48000, 1, "pcm_s16le")
    stereo = music_enhance.measure(str(tone(tmp_path / "stereo.wav", volume=0.8, stereo=True)))
    assert abs(stereo["integrated_lufs"] - (expect + 3.01)) < 1.5 and stereo["channels"] == 2
    bare = music_enhance.measure(str(tone(tmp_path / "bare.wav")))                          # amplitude 1/8, no gain
    assert abs(bare["integrated_lufs"] - (20 * math.log10(1 / 8) - 3.01)) < 1.5


@FFMPEG
def test_meter_target_gate_and_table(tmp_path, capsys):
    a, b = tone(tmp_path / "a.wav", volume=0.8), tone(tmp_path / "b.wav", seconds=4)
    wise("music-enhance", a, "--check", "--target", "-23", "--tolerance", "1")           # inside: no exit
    assert "inside -23 ±1 LUFS" in capsys.readouterr().out
    assert exit_code("music-enhance", a, "--check", "--target", "-15", "--tolerance", "1") == 1
    assert "OUTSIDE -15 ±1 LUFS by -8." in capsys.readouterr().out     # -23.0 against -15
    wise("music-enhance", a, "--check", "--target", "-15", "--tolerance", "9")           # a wide tolerance lets it through
    capsys.readouterr()
    assert exit_code("music-enhance", a, b, "--check", "--target", "-23", "--json") == 1               # b reads about -21.1
    r = json.loads(capsys.readouterr().out)
    assert r["ok"] is False and [f["target"]["ok"] for f in r["files"]] == [True, False] and r["files"][1]["target"]["delta"] > 1
    assert not any(k.startswith("_") for f in r["files"] for k in f)                     # no private fields leak out
    assert exit_code("music-enhance", a, b, "--check") == 1                              # the preset's -14 is the gate
    table = capsys.readouterr().out.splitlines()
    assert table[0].split() == ["file", "I", "LUFS", "LRA", "TP", "dBFS", "max", "S", "max", "M", "dur", "s", "Hz", "ch"]
    assert table[1].startswith("a.wav") and "OUTSIDE -14" in table[1] and table[2].startswith("b.wav") and table[3].startswith("Targets:")
    assert not list(tmp_path.glob("*.enhanced.*"))                                       # --check writes nothing


@FFMPEG
def test_old_loudness_name_still_measures(tmp_path, capsys):
    a = tone(tmp_path / "a.wav", volume=0.8)
    wise("loudness", a)                                                  # no target: a reading and exit 0, as before
    out = capsys.readouterr()
    assert "integrated:      -23." in out.out and "target:" not in out.out and "music-enhance --check" in out.err
    assert exit_code("loudness", a, "--target", "-15") == 1
    assert not list(tmp_path.glob("*.enhanced.*"))


@FFMPEG
def test_meter_missing_file_and_unmeasurable_input(tmp_path, capsys):
    assert exit_code("music-enhance", tmp_path / "nope.wav", "--check") == 2
    assert "no such file" in capsys.readouterr().err
    make(tmp_path, {"notes.txt": "not audio"})
    assert exit_code("music-enhance", tmp_path / "notes.txt", "--check") == 1
    assert "could not measure" in capsys.readouterr().out
    # a 0.1 s clip never fills a 400 ms block: no loudness reading is invented, only the peak is real
    r = music_enhance.measure(str(tone(tmp_path / "blip.wav", seconds=0.1)))
    assert r["integrated_lufs"] is None and r["lra_lu"] is None and "too short" in r["note"]
    assert abs(r["true_peak_dbfs"] - 20 * math.log10(1 / 8)) < 0.6 and r["silent"] is False
    assert exit_code("music-enhance", tmp_path / "blip.wav", "--check", "--target", "-15") == 1


def test_meter_never_plays():
    cmd = music_enhance.command("ffmpeg", "x.wav")
    assert cmd.count("null") == 2 and "ffplay" not in " ".join(cmd) and "-nostdin" in cmd      # both outputs are the null muxer


# --------------------------------------------------------------------------- the command line

@pytest.mark.parametrize("command", ["qa", "board", "music-enhance"])
def test_help_has_examples(command, capsys):
    assert exit_code(command, "--help") == 0
    out = capsys.readouterr().out
    assert out.count(f"    wise {command} ") >= 2 and "Exit 0" in out and "--json" in out
