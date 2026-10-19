"""Offline tests for `wise studio`: the path guard, the transcript parser, attribution, redaction and the server.

    uv run --with pytest pytest -q tests/test_studio.py

No network: the server binds 127.0.0.1 on a free port and reads only temp folders.
"""
import http.client
import json
import os
import sys
import threading
import time
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from wisecraft import studio  # noqa: E402


def iso(t):
    return datetime.fromtimestamp(t, timezone.utc).isoformat().replace("+00:00", "Z")


# --------------------------------------------------------------------------- path guard

@pytest.fixture
def roots(tmp_path):
    root = tmp_path / "game" / "outputs"
    (root / "shots").mkdir(parents=True)
    (root / "shots" / "a.png").write_bytes(b"png")
    (root / "notes.txt").write_text("x")
    secret = tmp_path / "secret"
    secret.mkdir()
    (secret / "b.png").write_bytes(b"png")
    evil = tmp_path / "game" / "outputs-evil"
    evil.mkdir()
    (evil / "c.png").write_bytes(b"png")
    (root / "link.png").symlink_to(secret / "b.png")
    (root / "linkdir").symlink_to(secret)
    return tmp_path, [os.path.realpath(root)]


def test_guard_serves_media_inside_a_root(roots):
    tmp, r = roots
    p = studio.guard(str(tmp / "game/outputs/shots/a.png"), r)
    assert p and p.name == "a.png"


@pytest.mark.parametrize("rel", [
    "game/outputs/../../secret/b.png",        # traversal
    "game/outputs/shots/../../../secret/b.png",
    "game/outputs/link.png",                  # a symlink that points out
    "game/outputs/linkdir/b.png",             # a folder symlink that points out
    "game/outputs-evil/c.png",                # a sibling that shares the root's prefix
    "game/outputs/notes.txt",                 # not media
    "game/outputs/shots/missing.png",         # not there
    "game/outputs/shots",                     # a folder
])
def test_guard_blocks(roots, rel):
    tmp, r = roots
    assert studio.guard(str(tmp / rel), r) is None


@pytest.mark.parametrize("raw", ["", None, "shots/a.png", "/etc/passwd", "/tmp/x.png\x00.png", 42])
def test_guard_rejects_odd_input(roots, raw):
    assert studio.guard(raw, roots[1]) is None


def test_expand_roots_drops_nested_and_missing(tmp_path):
    (tmp_path / "g1" / "outputs" / "qa").mkdir(parents=True)
    (tmp_path / "g2" / "qa").mkdir(parents=True)
    cfg = dict(studio.DEFAULTS, base=str(tmp_path), roots=["*/outputs", "*/qa", "*/outputs/qa", "nope/**"])
    got = studio.expand_roots(cfg)
    assert got == sorted([os.path.realpath(tmp_path / "g1/outputs"), os.path.realpath(tmp_path / "g2/qa")])


# --------------------------------------------------------------------------- transcripts

def claude_lines(t0, shot):
    return [
        {"type": "ai-title", "aiTitle": "Hero select", "sessionId": "s"},
        {"type": "assistant", "timestamp": iso(t0), "requestId": "r1", "cwd": "/w/game",
         "message": {"model": "claude-opus-4", "stop_reason": "tool_use",
                     "usage": {"input_tokens": 1000, "output_tokens": 200, "cache_read_input_tokens": 0},
                     "content": [{"type": "tool_use", "name": "Bash",
                                  "input": {"command": "node probe.mjs --out outputs/run", "description": "Running probe on both heroes"}}]}},
        {"type": "user", "timestamp": iso(t0 + 5), "cwd": "/w/game",
         "message": {"content": [{"type": "tool_result", "content": [
             {"type": "text", "text": f"wrote {shot}"},
             {"type": "image", "source": {"type": "base64", "data": "iVBOR" + "A" * 5000 + ".png"}}]}]}},
    ]


def write_jsonl(path, rows, mode="w"):
    with open(path, mode) as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def test_claude_transcript_parser_and_incremental_read(tmp_path):
    t0 = time.time() - 60
    f = tmp_path / "agent-abc.jsonl"
    write_jsonl(f, claude_lines(t0, "outputs/run/hero-select.png"))
    m = studio.Mentions()
    tail = studio.ClaudeTail(str(f), t0 - 3600, "abc", m)
    r = tail.read(os.stat(f))
    assert r["title"] == "Hero select" and r["doing"] == "Running probe on both heroes"
    assert r["tokens"] == 1200 and r["cost"] > 0 and r["cwd"] == "/w/game"
    # nothing new: no reparse; then one more call is read from where it stopped
    assert tail.read(os.stat(f))["tokens"] == 1200
    write_jsonl(f, [{"type": "assistant", "timestamp": iso(t0 + 30), "requestId": "r2",
                     "message": {"stop_reason": "end_turn", "usage": {"input_tokens": 10, "output_tokens": 5},
                                 "content": [{"type": "tool_use", "name": "Read", "input": {"file_path": "/w/game/src/hero.js"}}]}}], "a")
    r = tail.read(os.stat(f))
    assert r["tokens"] == 1215 and r["doing"] == "Read hero.js" and r["stop"] == "end_turn"
    # the agent that named a file is found for it; an unrelated file is not
    who, sure = m.who("/w/game/outputs/run/hero-select.png", t0 + 10)
    assert (who, sure) == ("abc", True)
    assert m.who("/w/other/outputs/zzz.png", t0 + 10) == (None, False)
    # a file the agent's command only names the folder of: a "likely" match
    assert m.who("/w/game/outputs/run/frame-0042.png", t0 + 20) == ("abc", False)


def test_partial_last_line_waits_for_its_newline(tmp_path):
    t0 = time.time()
    f = tmp_path / "t.jsonl"
    line = json.dumps(claude_lines(t0, "x.png")[1])
    f.write_text(line[:40])
    tail = studio.ClaudeTail(str(f), t0 - 10, "k", studio.Mentions())
    assert tail.read(os.stat(f))["tokens"] == 0
    with open(f, "a") as fh:
        fh.write(line[40:] + "\n")
    assert tail.read(os.stat(f))["tokens"] == 1200


def test_big_transcript_starts_near_the_window(tmp_path, monkeypatch):
    monkeypatch.setattr(studio.Tail, "BISECT_OVER", 1000)
    t0 = time.time() - 10 * 3600
    rows = []
    for i in range(4000):  # ten hours of calls, one usage each
        rows.append({"type": "assistant", "timestamp": iso(t0 + i * 9), "requestId": f"r{i}",
                     "message": {"usage": {"input_tokens": 1, "output_tokens": 0}, "content": []}})
    f = tmp_path / "big.jsonl"
    write_jsonl(f, rows)
    tail = studio.ClaudeTail(str(f), time.time() - 3600, "k", studio.Mentions())
    r = tail.read(os.stat(f))
    assert 380 <= r["tokens"] <= 420  # the last hour only
    assert tail.offset == os.path.getsize(f)


def test_codex_session(tmp_path):
    t0 = time.time() - 30
    f = tmp_path / "rollout.jsonl"
    write_jsonl(f, [
        {"timestamp": iso(t0), "type": "session_meta", "payload": {"cwd": "/w/heroes"}},
        {"timestamp": iso(t0), "type": "response_item", "payload": {"type": "message", "role": "user", "content": [
            {"type": "input_text", "text": "# AGENTS.md instructions"}, {"type": "input_text", "text": "Read venom/BRIEF.md and do it."}]}},
        {"timestamp": iso(t0 + 1), "type": "event_msg", "payload": {"type": "task_started"}},
        {"timestamp": iso(t0 + 2), "type": "response_item", "payload": {"type": "custom_tool_call", "name": "exec",
                                                                       "input": 'text(await tools.exec_command({cmd:"cp a.png venom/ref/vistas.png"}))'}},
        {"timestamp": iso(t0 + 3), "type": "event_msg", "payload": {"type": "token_count", "info": {"total_token_usage": {"total_tokens": 4321}}}},
    ])
    m = studio.Mentions()
    t = studio.CodexTail(str(f), t0 - 60, "codex-1", m).read(os.stat(f))
    assert t.cwd == "/w/heroes" and t.title == "Read venom/BRIEF.md and do it."
    assert t.doing == "cp a.png venom/ref/vistas.png" and t.tokens == 4321 and not t.done
    assert m.who("/w/heroes/venom/ref/vistas.png", t0 + 5) == ("codex-1", True)


def test_lead_ranks_below_its_worker_for_the_same_file():
    m = studio.Mentions()
    m.add_text("saved /w/g/outputs/x1.png", "worker", 100, 2, None)
    m.add_text("look at /w/g/outputs/x1.png", "lead:s1", 110, 2, None)
    assert m.who("/w/g/outputs/x1.png", 105)[0] == "worker"


@pytest.mark.parametrize("text", [
    "curl -H 'Authorization: Bearer abcdef0123456789' https://x",
    "export OPENAI_API_KEY=sk-proj-abcdefghijklmnop",
    "TOKEN=ghp_abcdefghijklmnopqrstuvwxyz0123",
    "password: hunter2hunter2",
])
def test_redact_hides_secrets(text):
    out = studio.redact(text)
    for s in ("abcdef0123456789", "sk-proj-abcdefghijklmnop", "ghp_abcdefghijklmnopqrstuvwxyz0123", "hunter2hunter2"):
        assert s not in out


def test_redact_hides_private_settings_and_keeps_plain_text():
    assert studio.redact("cat ~/.config/gh/hosts.yml") == "(hidden: reads private settings)"
    assert studio.redact("printenv | sort").startswith("(hidden")
    assert studio.redact("Running probe.py on both heroes") == "Running probe.py on both heroes"
    assert studio.redact("ls /Users/me/project/outputs") == "ls /Users/me/project/outputs"


# --------------------------------------------------------------------------- the server

@pytest.fixture
def server(tmp_path, monkeypatch):
    base = tmp_path / "codex"
    shots = base / "game" / "outputs"
    shots.mkdir(parents=True)
    from PIL import Image
    Image.new("RGB", (40, 80), (200, 20, 20)).save(shots / "new.png")
    (tmp_path / "outside.png").write_bytes(b"x")
    monkeypatch.setattr(studio, "THUMBS", tmp_path / "thumbs")
    monkeypatch.setattr(studio, "orca", lambda *a, **k: None)
    cfg = dict(studio.DEFAULTS, base=str(base), roots=["*/outputs"], reviews=str(tmp_path / "reviews.jsonl"),
               claude_dirs=[str(tmp_path / "noclaude")], codex_dir=str(tmp_path / "nocodex"))
    st = studio.Studio(cfg, 0)
    studio.Handler.studio = st
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), studio.Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield httpd.server_address[1], shots, tmp_path
    httpd.shutdown()
    httpd.server_close()


def req(port, method, path, body=None, host="127.0.0.1"):
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    headers = {"Host": f"{host}:{port}"}
    if body is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(body)
    c.request(method, path, body=body, headers=headers)
    r = c.getresponse()
    return r.status, r.read()


def test_server_feed_file_thumb_review(server):
    port, shots, tmp = server
    code, body = req(port, "GET", "/api/feed?limit=10")
    feed = json.loads(body)
    assert code == 200 and [c["name"] for c in feed["items"]] == ["new.png"]
    path = feed["items"][0]["path"]
    q = "?p=" + path
    assert req(port, "GET", "/file" + q)[0] == 200
    code, thumb = req(port, "GET", "/thumb" + q)
    assert code == 200 and thumb[:2] == b"\xff\xd8"
    assert req(port, "GET", "/file?p=" + str(tmp / "outside.png"))[0] == 404
    assert req(port, "GET", "/file?p=" + str(shots / ".." / ".." / ".." / "outside.png"))[0] == 404
    code, body = req(port, "POST", "/api/review", {"path": path, "verdict": "down", "note": "hero too dark"})
    assert code == 200
    row = json.loads((tmp / "reviews.jsonl").read_text().splitlines()[-1])
    assert row["verdict"] == "down" and row["note"] == "hero too dark" and row["path"] == path
    assert req(port, "POST", "/api/review", {"path": str(tmp / "outside.png"), "verdict": "up"})[0] == 400
    assert req(port, "GET", "/api/state")[0] == 200
    assert req(port, "GET", "/api/term?h=../../etc")[0] == 400


def test_server_refuses_other_hosts(server):
    port = server[0]
    assert req(port, "GET", "/api/feed", host="evil.example")[0] == 403
    assert req(port, "POST", "/api/review", {"path": "/x.png", "verdict": "up"}, host="evil.example")[0] == 403
