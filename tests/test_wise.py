# Ported from Universal Modder (https://github.com/rehan-remade/universal-modder), tests/test_um.py.
# Copyright (c) 2026 Rehan and universal-modder contributors. MIT License; see LICENSE and NOTICE.
"""Offline tests for the knowledge base, the publish lint, the trailer compiler and the CLI shell.

    .venv/bin/python -m pytest -q tests/test_wise.py

No network, no audio playback. The ffmpeg tests skip when ffmpeg is not installed. Every fake key, private
URL, user path and denylist term below is assembled at runtime, so this file passes `wise publish check .`.
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
from wisecraft import cli, kb, publish, video  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
FFMPEG = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg")
BODY = "aB3dE5fG7hJ9kL1mN3pQ5rS7tU9vW1xY3zA5bC7d"   # 40 harmless characters to hang a key prefix on
TERM = "foo" + "corp"                                 # a made-up name for denylist tests
TERM2 = "project" + "-" + "nimbus"


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    # the developer's own settings must not leak into the tests
    for k in ("WISE_DENY", "WISE_KB", "WISE_AGENT"):
        monkeypatch.delenv(k, raising=False)


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
    ["kb", "search"], ["kb", "show"], ["kb", "new"], ["kb", "add"], ["kb", "check"], ["kb", "index"], ["kb", "sync"], ["kb", "pr"],
    ["publish", "check"],
    ["video", "probe"], ["video", "contact"], ["video", "first-frame"], ["video", "beats"], ["video", "compile"],
])
def test_cli_help_for_subcommands(argv, capsys):
    assert exit_code(argv + ["--help"]) == 0
    assert "usage: wise " + argv[0] in capsys.readouterr().out


def test_cli_group_docstrings_show_wz_examples(capsys):
    for group in ("kb", "publish", "video"):
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


def test_unicode_output_on_cp1252_console(tmp_path):
    # `wise kb show` must not UnicodeEncodeError when stdout isn't UTF-8
    root = tmp_path / "kb"
    (root / "games/x").mkdir(parents=True)
    (root / "games/x/n.md").write_text("---\ntitle: Señor → test\n---\n# Señor →\n", encoding="utf-8")
    env = dict(os.environ, PYTHONIOENCODING="cp1252", WISE_KB=str(root), PYTHONPATH=str(REPO))
    r = subprocess.run([sys.executable, "-m", "wisecraft", "kb", "show", "n.md"], capture_output=True, encoding="utf-8", env=env)
    assert r.returncode == 0 and "Señor →" in r.stdout


# --------------------------------------------------------------------------- publish

CLEAN = {"README.md": "# My game\nRun `npm run dev` and open http://127.0.0.1:5173 or http://localhost:4173/.\n",
         "LICENSE": "MIT\n",
         "src/main.js": "posthog.init('" + "phc" + "_" + BODY + "')  // project keys are public by design\n"
                        "// deploys go to https://<name>.vercel.app; docs at https://vercel.com/docs and https://ngrok.com/download\n"}


def test_publish_clean_folder_passes(tmp_path, capsys):
    make(tmp_path, CLEAN)
    assert publish.check(str(tmp_path)) == 0
    assert capsys.readouterr().out.strip() == "PASS: 3 files, 0 failures, 0 warnings"


def test_publish_check(tmp_path, capsys):
    # fixtures assembled at runtime so this file doesn't trip the toolkit's own publish check
    fake_key = "FAL" + "_KEY=" + "abcdefghijklmnopqrstuvwxyz0123"
    make(tmp_path, {**CLEAN, "config.txt": "# settings\n" + fake_key + "\n", ".env": "A=1\n", "web/.env.local": "B=2\n"})
    assert publish.check(str(tmp_path)) == 1
    out = capsys.readouterr().out
    assert "FAL_KEY assignment in config.txt:2" in out
    assert "env file (secrets?): .env\n" in out and "env file (secrets?): web/.env.local" in out
    assert out.strip().endswith("FAIL: 6 files, 3 failures, 0 warnings")
    assert "abcdefghijklmnopqrstuvwxyz0123" not in out            # the report never repeats a secret


KEYS = [
    # assembled at runtime so this file doesn't trip the toolkit's own publish check
    ("OpenAI key", "sk-" + "proj-" + "Ab3_dE-f" + "Gh1jK2lM3nO4pQ5rS6tU7vW8xY9z0" * 4),
    ("OpenAI key", "sk-" + "svcacct-" + "Ab3_dE-f" + "Gh1jK2lM3nO4pQ5rS6tU7vW8xY9z0" * 4),
    ("OpenAI key", "sk-" + "Gh1jK2lM3nO4pQ5rS6tU7vW8xY9z0" * 2),
    ("GitHub token", "github" + "_pat_" + "11ABCDEFG0123456789abc" + "_" + "aB3dE5fG7hJ9kL1mN3pQ5rS7tU9vW1xY3zA5bC7dE9fG1hJ3kL5mN7pQ9rS1t"),
    ("GitHub token", "gh" + "p_" + "aB3dE5fG7hJ9kL1mN3pQ5rS7tU9vW1xY3z"),
    ("Anthropic key", "sk-" + "ant-" + "api03-" + BODY),
    ("AWS key id", "AK" + "IA" + "ABCDEFGHIJKLMNOP"),
    ("Google API key", "AI" + "za" + "SyD" + "x9" * 16),
    ("Stripe live key", "sk" + "_live_" + "51H" + BODY[:24]),
    ("Stripe live key", "rk" + "_live_" + "51H" + BODY[:24]),
    ("Slack token", "xo" + "xb-" + "123456789012-1234567890123-" + BODY[:24]),
    ("Slack token", "xo" + "xp-" + "123456789012-" + BODY[:24]),
    ("Vercel token", "vc" + "p_" + BODY),
    ("Vercel token", "vercel" + "_blob_rw_" + BODY[:20] + "_" + BODY[20:]),
    ("Vercel token assignment", "VERCEL" + "_TOKEN=" + BODY[:24]),
    ("Vercel token assignment", "VERCEL" + "_API_TOKEN: '" + BODY[:24] + "'"),
    ("PostHog personal API key", "ph" + "x_" + BODY),
    ("private key", "-----BEGIN " + "PRIVATE KEY-----"),
    ("private key", "-----BEGIN " + "RSA PRIVATE KEY-----"),
    ("private key", "-----BEGIN " + "OPENSSH PRIVATE KEY-----"),
]


@pytest.mark.parametrize("label,key", KEYS)
def test_secret_patterns_catch_current_key_formats(label, key):
    rx = dict(publish.SECRET_PATTERNS)[label]
    assert rx.search(f"key = {key}\n"), key


@pytest.mark.parametrize("label,key", KEYS)
def test_publish_fails_on_each_key(tmp_path, capsys, label, key):
    make(tmp_path, {**CLEAN, "src/config.js": f"// config\n\nexport const token = '{key}'\n"})
    assert publish.check(str(tmp_path)) == 1
    out = capsys.readouterr().out
    assert f"{label} in src/config.js:3" in out and key not in out


@pytest.mark.parametrize("text", [
    "sk-learn-style-kebab-case-identifiers-are-not-keys and github_pat_ alone",
    "phc" + "_" + BODY,                                   # PostHog project key: public by design
    "pk" + "_live_" + BODY[:24] + " and sk" + "_test_" + BODY[:24],   # publishable and test Stripe keys
    "xoxo-gossip and AIza-is-how-they-start",
    "VERCEL_TOKEN=${{ secrets.VERCEL_TOKEN }} and VERCEL_TOKEN=$VERCEL_TOKEN",
    "-----BEGIN PUBLIC KEY----- and -----BEGIN CERTIFICATE-----",
    "a vcp_short one and the word phx_ alone",
])
def test_secret_patterns_ignore_ordinary_text(text):
    assert not [label for label, rx in publish.SECRET_PATTERNS if rx.search(text)]


@pytest.mark.parametrize("label,host", [
    ("Vercel deploy URL", "my-game-git-boss-team." + "vercel.app"),
    ("Vercel deploy URL", "My-Game." + "Vercel.App"),
    ("Netlify deploy URL", "deploy-preview-12--my-game." + "netlify.app"),
    ("Cloudflare Pages URL", "a1b2c3d4.my-game." + "pages.dev"),
    ("ngrok tunnel URL", "0a1b-203-0-113-7." + "ngrok-free.app"),
    ("ngrok tunnel URL", "abc123.eu." + "ngrok.io"),
])
def test_publish_fails_on_private_deploy_urls(tmp_path, capsys, label, host):
    url = "https://" + host + "/play?stage=3"
    make(tmp_path, {**CLEAN, "docs/notes.md": f"# Notes\nPreview: {url}\n"})
    assert publish.check(str(tmp_path)) == 1
    out = capsys.readouterr().out
    assert f"private {label} in docs/notes.md:2" in out
    assert host not in out and host.lower() not in out.lower()      # where it is, not what it is


@pytest.mark.parametrize("text", [
    "http://127.0.0.1:5173", "http://localhost:4173/?debug=1", "https://<name>.vercel.app", "https://vercel.com/docs",
    "https://ngrok.com/download", "https://pages.dev", "https://app.netlify.com/teams", "vercel.app is a host",
])
def test_private_url_patterns_ignore_loopback_and_docs(text):
    assert not [label for label, rx in publish.PRIVATE_URL_PATTERNS if rx.search(text)]


def deny_fixture(tmp_path):
    make(tmp_path, {**CLEAN, "docs/plan.md": f"# Plan\n\nBuilt for {TERM.upper()} under a roadmap-marker-xyz contract.\n"
                                             f"Second mention: Team{TERM.title()}Internal.\n"})


def test_publish_denylist_from_file(tmp_path, capsys):
    deny_fixture(tmp_path / "site")
    deny = tmp_path / "names.txt"
    deny.write_text(f"# names that stay private\n\n{TERM.title()}   # the client\n{TERM2}\n", encoding="utf-8")
    assert publish.check(str(tmp_path / "site")) == 0             # no list, nothing to find
    capsys.readouterr()
    assert publish.check(str(tmp_path / "site"), deny=str(deny)) == 1
    out = capsys.readouterr().out
    assert f"denylisted name {TERM!r} in docs/plan.md:3,4" in out
    assert "roadmap-marker-xyz" not in out and TERM2 not in out   # file:line and the term, never the line's text


def test_publish_denylist_in_the_folder_is_used_and_not_scanned(tmp_path, capsys):
    deny_fixture(tmp_path)
    (tmp_path / publish.DENY_FILE).write_text(TERM + "\n", encoding="utf-8")
    assert publish.check(str(tmp_path)) == 1
    out = capsys.readouterr().out
    assert f"denylisted name {TERM!r} in docs/plan.md:3,4" in out and publish.DENY_FILE not in out
    assert out.count("FAIL ") == 1


def test_publish_denylist_from_env_and_precedence(tmp_path, capsys, monkeypatch):
    deny_fixture(tmp_path)
    monkeypatch.setenv("WISE_DENY", f"something-else, {TERM.upper()} ,")
    assert publish.load_denylist(tmp_path) == (["something-else", TERM], None)
    assert publish.check(str(tmp_path)) == 1
    assert f"denylisted name {TERM!r} in docs/plan.md:3,4" in capsys.readouterr().out
    # a list in the folder wins over the environment, --deny wins over both
    (tmp_path / publish.DENY_FILE).write_text("unrelated-name\n", encoding="utf-8")
    assert publish.check(str(tmp_path)) == 0
    other = tmp_path.parent / "other-names.txt"
    other.write_text(TERM + "\n", encoding="utf-8")
    assert publish.check(str(tmp_path), deny=str(other)) == 1


def test_publish_denylist_catches_file_names_and_ignores_tiny_terms(tmp_path, capsys):
    make(tmp_path, {**CLEAN, f"art/{TERM.title()}-logo.svg": "<svg/>\n"})
    (tmp_path / publish.DENY_FILE).write_text(f"{TERM}\nmy\n", encoding="utf-8")
    assert publish.check(str(tmp_path)) == 1
    out = capsys.readouterr().out
    assert f"denylisted name {TERM!r} in the path art/{TERM.title()}-logo.svg" in out
    assert "denylist terms under 3 characters are ignored: 'my'" in out and "denylisted name 'my'" not in out


def test_publish_skips_vendor_and_build_folders(tmp_path, capsys):
    bad = "export const k = '" + KEYS[0][1] + "'\n"
    make(tmp_path, {**CLEAN, "node_modules/pkg/index.js": bad, "dist/assets/app.js": bad, ".venv/lib/x.py": bad,
                    ".git/config": bad, "node_modules/pkg/.env": "A=1\n"})
    assert publish.check(str(tmp_path)) == 0
    assert capsys.readouterr().out.strip() == "PASS: 3 files, 0 failures, 0 warnings"


def test_publish_env_files(tmp_path, capsys):
    make(tmp_path, {**CLEAN, ".env.example": "POSTHOG_KEY=\nVERCEL_TOKEN=\n", "prod.env": "A=1\n", ".env.production": "A=1\n"})
    assert publish.check(str(tmp_path)) == 1
    out = capsys.readouterr().out
    assert "env file (secrets?): prod.env" in out and "env file (secrets?): .env.production" in out
    assert ".env.example" not in out
    assert [publish.is_env_file(n) for n in (".env", ".ENV.local", "a.env", ".env.sample", "environment.ts")] == [True, True, True, False, False]


def test_publish_warnings_do_not_fail(tmp_path, capsys):
    mac_path, win_path = "/Us" + "ers/alice/games/run.mjs", "C:" + "\\Users\\alice\\game"
    make(tmp_path, {"src/main.js": f"// built at {mac_path}\n// and {win_path}\n// but not /Users/<name>/ or ~/games\n",
                    "public/music.ogg": b"\0" * 4096, "public/tiny.png": b"\0" * 16})
    assert publish.check(str(tmp_path), max_mb=0.002) == 0
    out = capsys.readouterr().out
    assert "large file (0.0 MB, limit 0.002): public/music.ogg" in out and "tiny.png" not in out
    assert "absolute user path in src/main.js:1,2" in out
    assert "no README" in out and "no LICENSE" in out
    assert out.strip().endswith("WARN: 3 files, 0 failures, 4 warnings")
    assert publish.check(str(tmp_path)) == 0                      # default limit: 5 MB
    assert "large file" not in capsys.readouterr().out


def test_publish_cli_exit_status(tmp_path, capsys):
    make(tmp_path / "ok", CLEAN)
    make(tmp_path / "bad", {**CLEAN, "notes.txt": "see https://staging-build." + "vercel.app\n"})
    deny = tmp_path / "deny.txt"
    deny.write_text("readme\n", encoding="utf-8")                  # matches README.md by path
    assert exit_code(["publish", "check", str(tmp_path / "ok")]) == 0
    assert exit_code(["publish", "check", str(tmp_path / "bad")]) == 1
    assert exit_code(["publish", "check", str(tmp_path / "ok"), "--deny", str(deny), "--max-mb", "1"]) == 1
    assert exit_code(["publish", "check", str(tmp_path / "nowhere")]) == 1
    assert exit_code(["publish", "check", str(tmp_path / "ok"), "--deny", str(tmp_path / "missing.txt")]) == 1


MINE = ["wisecraft/kb.py", "wisecraft/publish.py", "wisecraft/video.py", "tests/test_wise.py", "knowledge/TEMPLATE.md", "knowledge/README.md"]


@pytest.mark.parametrize("rel", MINE)
def test_ported_files_pass_their_own_lint(rel):
    # the toolkit must be able to publish itself: nothing in these files may look like a key, a private URL,
    # a user path or a name on the repo's own denylist
    text = (REPO / rel).read_text(encoding="utf-8")
    found = [label for label, rx in publish.SECRET_PATTERNS + publish.PRIVATE_URL_PATTERNS if rx.search(text)]
    assert not found and not publish.USER_PATH.search(text)
    assert not publish.deny_hits(text, publish.load_denylist(REPO)[0])


@pytest.mark.parametrize("rel", ["wisecraft/kb.py", "wisecraft/publish.py", "wisecraft/video.py", "tests/test_wise.py"])
def test_ported_files_carry_the_attribution_header(rel):
    head = (REPO / rel).read_text(encoding="utf-8").splitlines()[:2]
    assert head[0].startswith("# Ported from Universal Modder (https://github.com/rehan-remade/universal-modder), ")
    assert head[1] == "# Copyright (c) 2026 Rehan and universal-modder contributors. MIT License; see LICENSE and NOTICE."


# --------------------------------------------------------------------------- knowledge base

GAME_NOTE = """---
kind: game
title: "Waves that breathe"
game: "Lane defense (mobile web)"
engine: threejs-vite
route: data-tuning
status: working
date: 2026-10-01
agents: ["Codex (gpt-6)"]
---
# Waves that breathe

> Spawn budgets follow a rising sine, checked with player-model bots.

## Setup
Vite 7, three.js 0.180, node 22. Dev server at http://127.0.0.1:5173.

## Route and why
Data only: the wave table.

## Verification
A headless simulation of 200 runs, then `wise qa` on a phone-sized browser.

## Gotchas
1. **Stage 4 was a wall.** **Cause:** two peaks overlapped. **Fix:** offset the elite wave by half a period.
"""


def kb_root(tmp_path) -> Path:
    root = tmp_path / "knowledge"
    root.mkdir()
    shutil.copy(REPO / "knowledge" / "TEMPLATE.md", root / "TEMPLATE.md")
    return root


def write_note(root: Path, rel: str, text: str = GAME_NOTE) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def test_repo_knowledge_is_valid():
    # passes on an empty knowledge folder; every note someone adds must pass `wise kb check`
    root = REPO / "knowledge"
    for p, _, _ in kb.notes(root):
        fails, _ = kb.check_note(p, root)
        assert not fails, (p, fails)


def test_repo_knowledge_index_is_fresh():
    root = REPO / "knowledge"
    if not (root / "INDEX.md").exists():
        pytest.skip("knowledge/INDEX.md not generated yet")
    for f, want in kb.index_files(root).items():
        assert f.exists() and f.read_text(encoding="utf-8") == want, f"{f.name} is stale: run `wise kb index`"


def test_kb_schema_constants():
    assert (kb.REPO, kb.BRANCH) == ("Wiserax/wisecraft", "main") or os.environ.get("WISE_KB_REPO") or os.environ.get("WISE_KB_BRANCH")
    assert kb.ROUTES == ["design", "data-tuning", "engine-code", "ui", "audio", "performance", "tooling", "release", "process", "other"]
    assert kb.PLATFORMS == ["web-mobile", "web-desktop", "pwa", "webview", "other"]
    assert kb.STATUSES == ["idea", "in-progress", "working", "released", "abandoned"]
    assert kb.GAME_KEYS == ["kind", "title", "game", "engine", "route", "status", "date", "agents"]
    assert kb.TECH_KEYS == ["kind", "title", "tags", "date", "agents"]
    assert kb.GAME_SECTIONS == ["setup", "route", "verification", "gotchas"]
    assert kb.ENGINES == ["threejs-vite", "phaser", "pixi", "babylon", "playcanvas", "unity-webgl", "godot-web", "construct", "canvas-2d"]
    assert "unknown" not in kb.engine_keys() and set(kb.ENGINES) <= set(kb.engine_keys())     # scan may know more, never fewer


def test_template_follows_the_schema():
    meta, body = kb.parse(REPO / "knowledge" / "TEMPLATE.md")
    assert not [k for k in kb.GAME_KEYS if not meta.get(k)]
    assert set(meta) == set(kb.GAME_KEYS) | {"games_also", "game_version", "platform", "tools", "humans", "links", "tags"}
    assert "anti_cheat" not in meta
    assert meta["title"] == kb.TEMPLATE_TITLE and meta["kind"] == "game"
    assert meta["route"] in kb.ROUTES and meta["platform"] in kb.PLATFORMS and meta["engine"] in kb.ENGINES and meta["status"] in kb.STATUSES
    assert re.findall(r"^## (.+)$", body, re.M) == ["Setup", "Route and why", "How the game works (what we had to learn)", "Build steps",
                                                    "Verification", "Gotchas", "Assets", "Cost and time", "Open questions"]
    front = (REPO / "knowledge" / "TEMPLATE.md").read_text(encoding="utf-8").split("---")[1]
    for name, values in (("route", kb.ROUTES), ("platform", kb.PLATFORMS), ("status", kb.STATUSES)):
        line = next(ln for ln in front.splitlines() if ln.startswith(name + ":"))
        assert line.split("#", 1)[1].strip() == " | ".join(values), name      # the comment lists exactly the allowed values


def test_kb_new_check_search(tmp_path):
    root = kb_root(tmp_path)
    p = kb.new_note(root, "Lane defense (mobile web)", "A new boss wave", agent="Codex (gpt-6)", route="engine-code")
    assert p == root / "games" / "lane-defense-mobile-web" / "a-new-boss-wave.md"
    meta, _ = kb.parse(p)
    assert meta["platform"] == "web-mobile" and meta["status"] == "in-progress" and "anti_cheat" not in meta
    fails, _ = kb.check_note(p, root)
    assert any("unfilled template text" in f for f in fails)          # a fresh scaffold must not pass
    good = p.read_text(encoding="utf-8")
    good = good.replace("FILL IN: exact build and stack versions", "1.0.1, Vite 7")
    good = good.replace("> Two to four sentences: what you built", "> Added a boss wave to the stage table")
    good = good.replace("The most valuable section. Numbered; each one symptom → cause → fix.", "")
    good = good.replace("1. **Symptom.** What you saw. **Cause:** what it really was. **Fix:** what worked.",
                        "1. **The boss never spawned.** **Cause:** the pool was sized at load. **Fix:** reserve a slot before the wave.")
    p.write_text(good, encoding="utf-8")
    fails, _ = kb.check_note(p, root)
    assert not fails, fails
    res = kb.search(root, ["boss"])
    assert res and res[0]["path"].endswith("a-new-boss-wave.md")
    assert kb.search(root, ["boss"], route="audio") == []
    assert kb.search(root, ["boss"], game="lane defense") and kb.search(root, ["boss"], engine="phaser") == []
    with pytest.raises(SystemExit):
        kb.new_note(root, "Lane defense (mobile web)", "A new boss wave")     # never overwrite a note


def test_kb_new_technique_and_add_alias(tmp_path, capsys):
    root = kb_root(tmp_path)
    assert cli.main(["kb", "add", "--root", str(root), "--kind", "technique", "--title", "Measure the mix without playing it",
                     "--agent", "Claude Code (Opus 5.5)"]) is None
    p = root / "techniques" / "measure-the-mix-without-playing-it.md"
    assert str(p) in capsys.readouterr().out
    meta, body = kb.parse(p)
    assert meta["kind"] == "technique" and meta["agents"] == ["Claude Code (Opus 5.5)"]
    assert not {"game", "engine", "route", "platform", "game_version", "tools"} & set(meta)
    assert body.startswith("# Measure the mix without playing it") and "## Gotchas" in body
    fails, _ = kb.check_note(p, root)
    assert fails == ["missing front-matter key: tags"]              # the one thing a technique scaffold still needs
    cli.main(["kb", "new", "--root", str(root), "--title", "Another", "--game", "Idle miner (web)"])
    assert (root / "games" / "idle-miner-web" / "another.md").exists()


def test_kb_new_from_scan(tmp_path, monkeypatch, capsys):
    import wisecraft.scan as scan
    root = kb_root(tmp_path)
    monkeypatch.setattr(scan, "fingerprint", lambda target: {"engine": "threejs-vite", "name": "lane-defense",
                                                             "versions": {"vite": "7.1.0", "three": "0.180.0", "phaser": None}}, raising=False)
    meta, _ = kb.parse(kb.new_note(root, None, "From a scan", from_scan="./game"))
    assert (meta["game"], meta["engine"]) == ("lane-defense", "threejs-vite")
    assert meta["game_version"] == "FILL IN: game build (vite 7.1.0, three 0.180.0)"
    # what the caller says wins over what the scan found; an engine given as {"key": ...} is read too
    monkeypatch.setattr(scan, "fingerprint", lambda target: {"engine": {"key": "phaser", "version": "3.90.0"}, "name": "x", "version": "1.2.0"},
                        raising=False)
    meta, _ = kb.parse(kb.new_note(root, "Lane defense", "Named by hand", from_scan="./game"))
    assert (meta["game"], meta["engine"], meta["game_version"]) == ("Lane defense", "phaser", "FILL IN: confirm build 1.2.0 (phaser 3.90.0)")
    monkeypatch.setattr(scan, "fingerprint", lambda target: {"engine": {"key": "unknown"}, "name": None, "versions": {}}, raising=False)
    meta, _ = kb.parse(kb.new_note(root, None, "Nothing found", from_scan="./game"))
    assert (meta["game"], meta["engine"], meta["game_version"]) == ("FILL IN", "unknown", "FILL IN: game build")
    meta, _ = kb.parse(kb.new_note(root, "Lane defense", "Engine by hand", from_scan="./game", engine="pixi"))
    assert meta["engine"] == "pixi"


@pytest.mark.parametrize("error", [RuntimeError("boom"), SystemExit(1), FileNotFoundError("no such folder")])
def test_kb_new_survives_a_failing_scan(tmp_path, monkeypatch, capsys, error):
    import wisecraft.scan as scan
    root = kb_root(tmp_path)

    def broken(target):
        raise error

    monkeypatch.setattr(scan, "fingerprint", broken, raising=False)
    meta, _ = kb.parse(kb.new_note(root, None, "Scan failed", from_scan="./missing"))
    assert (meta["game"], meta["engine"]) == ("FILL IN", "unknown")
    assert "--from-scan found nothing to pre-fill" in capsys.readouterr().err


def test_kb_new_without_a_scan_module(tmp_path, monkeypatch, capsys):
    import wisecraft.scan as scan
    root = kb_root(tmp_path)
    monkeypatch.delattr(scan, "fingerprint", raising=False)        # the stub module has no fingerprint()
    meta, _ = kb.parse(kb.new_note(root, "Lane defense", "No scan yet", from_scan="./game"))
    assert meta["engine"] == "unknown" and "ImportError" in capsys.readouterr().err


def test_kb_search_matches_word_starts(tmp_path):
    root = tmp_path / "knowledge" / "games" / "x"
    root.mkdir(parents=True)
    for name, title in [("a.md", "Trust and frustum culling"), ("b.md", "A Rust server for leaderboards"), ("c.md", "Rusty gears idle game"),
                        ("d.md", "Loading boss.glb lazily")]:
        (root / name).write_text(f"---\nkind: game\ntitle: {title}\ngame: X\n---\n# {title}\n", encoding="utf-8")
    found = {r["title"] for r in kb.search(tmp_path / "knowledge", ["rust"])}
    assert found == {"A Rust server for leaderboards", "Rusty gears idle game"}
    assert [r["title"] for r in kb.search(tmp_path / "knowledge", [".glb"])] == ["Loading boss.glb lazily"]   # punctuation-led terms match anywhere


def test_kb_check_accepts_a_minimal_game_note(tmp_path):
    root = kb_root(tmp_path)
    p = write_note(root, "games/lane-defense/waves.md")
    assert kb.check_note(p, root) == ([], [])                       # no anti_cheat, no optional keys, a loopback URL
    assert kb.check_note(p) == ([], [])


def test_kb_check_schema_errors(tmp_path):
    root = kb_root(tmp_path)
    bad = GAME_NOTE.replace("route: data-tuning", "route: loader-api").replace("status: working", "status: done")
    bad = bad.replace("engine: threejs-vite", "engine: three.js + vite\nplatform: windows").replace('agents: ["Codex (gpt-6)"]\n', "")
    bad = bad.replace("## Verification", "## Checks").replace("1. **Stage 4", "- **Stage 4")
    fails, warns = kb.check_note(write_note(root, "games/x/bad.md", bad), root)
    assert "missing front-matter key: agents" in fails
    assert any(f.startswith("route 'loader-api' not one of: design, data-tuning") for f in fails)
    assert any(f.startswith("status 'done' not one of") for f in fails)
    assert "missing section: ## Verification..." in fails
    assert any(w.startswith("platform 'windows' not one of: web-mobile") for w in warns)
    assert any(w.startswith("engine 'three.js + vite' isn't one of wise scan's keys") for w in warns)   # free text: a hint, not a failure
    assert "Gotchas section has no numbered items" in warns
    assert not any(f.startswith(("engine", "platform")) or "anti_cheat" in f for f in fails)
    tech = "---\nkind: technique\ntitle: t\ndate: 2026-10-01\nagents: [a]\n---\n# t\n"
    assert kb.check_note(write_note(root, "techniques/t.md", tech), root)[0] == ["missing front-matter key: tags"]
    assert "no YAML front matter" in kb.check_note(write_note(root, "techniques/plain.md", "# just text\n"), root)[0][0]
    still = GAME_NOTE.replace('title: "Waves that breathe"', f'title: "{kb.TEMPLATE_TITLE}"')
    assert "title is still the template's example title" in kb.check_note(write_note(root, "games/x/copy.md", still), root)[0]


def test_kb_check_rejects_secrets_and_dumps(tmp_path):
    note = tmp_path / "n.md"
    code = "\n".join(f"const x{i} = {i};" for i in range(160))
    note.write_text("---\nkind: technique\ntitle: t\ntags: [x]\ndate: 2026-09-30\nagents: [a]\n---\n# t\n"
                    f"```js\n{code}\n```\n" + "FAL" + "_KEY=abcdefghijklmnopqrstuvwxyz0123\n" + "token " + KEYS[-4][1] + "\n")
    fails, _ = kb.check_note(note)
    assert any("code block" in f for f in fails) and any("FAL_KEY" in f for f in fails)
    assert "PostHog personal API key in the note - remove it" in fails
    medium = "\n".join(f"const x{i} = {i};" for i in range(80))
    note.write_text(f"---\nkind: technique\ntitle: t\ntags: [x]\ndate: 2026-09-30\nagents: [a]\n---\n# t\n```js\n{medium}\n```\n")
    fails, warns = kb.check_note(note)
    assert not fails and any("80-line code block" in w for w in warns)


def test_kb_check_rejects_private_urls(tmp_path):
    root = kb_root(tmp_path)
    url = "https://lane-defense-git-boss." + "vercel.app"
    p = write_note(root, "games/lane-defense/waves.md", GAME_NOTE.replace("http://127.0.0.1:5173", url))
    fails, _ = kb.check_note(p, root)
    assert len(fails) == 1 and fails[0].startswith("private Vercel deploy URL on line 16")
    assert url not in fails[0]
    front = GAME_NOTE.replace('agents: ["Codex (gpt-6)"]', 'agents: ["Codex (gpt-6)"]\nlinks: ["https://abc.' + 'ngrok-free.app"]')
    fails, _ = kb.check_note(write_note(root, "games/lane-defense/linked.md", front), root)
    assert len(fails) == 1 and fails[0].startswith("private ngrok tunnel URL on line 10")


def test_kb_check_rejects_denylisted_names(tmp_path, monkeypatch, capsys):
    root = kb_root(tmp_path)
    named = GAME_NOTE.replace("Data only: the wave table.", f"Data only, as {TERM.title()} asked.")
    p = write_note(root, "games/lane-defense/waves.md", named)
    assert kb.check_note(p, root) == ([], [])                       # no denylist anywhere: nothing to match
    want = [f"denylisted name {TERM!r} on line 19: describe the game neutrally"]
    monkeypatch.setenv("WISE_DENY", TERM)
    assert kb.check_note(p, root)[0] == want
    monkeypatch.delenv("WISE_DENY")
    other = tmp_path / "names.txt"
    other.write_text(f"# clients\n{TERM.upper()}\n", encoding="utf-8")
    assert kb.check_note(p, root, deny=str(other))[0] == want
    assert exit_code(["kb", "check", str(p), "--root", str(root), "--deny", str(other)]) == 1
    assert f"denylisted name {TERM!r} on line 19" in capsys.readouterr().out
    # the repo's own list, next to knowledge/, is found with or without --root
    (tmp_path / publish.DENY_FILE).write_text(f"{TERM}\n", encoding="utf-8")
    assert kb.check_note(p, root)[0] == want and kb.check_note(p)[0] == want
    (tmp_path / publish.DENY_FILE).write_text("unrelated-name\n", encoding="utf-8")
    assert kb.check_note(p, root) == ([], [])


def test_kb_impossible_date_is_reported_not_raised(tmp_path):
    # YAML turns an unquoted YYYY-MM-DD into a date; a day that doesn't exist raises ValueError, not YAMLError
    root = tmp_path / "knowledge"
    (root / "techniques").mkdir(parents=True)
    note = root / "techniques" / "t.md"
    note.write_text("---\nkind: technique\ntitle: t\ntags: [x]\ndate: 2026-09-31\nagents: [a]\n---\n# t\n", encoding="utf-8")
    fails, _ = kb.check_note(note, root)
    assert any("front matter is not valid YAML" in f for f in fails), fails   # the date error's wording varies by Python
    kb.search(root, ["t"])                                             # one bad note must not break search or index
    kb.build_index(root)


def test_kb_check_rejects_unquoted_list_items(tmp_path):
    # YAML reads `[Vite 7: dev server]` as a dict and `2048` as an int, and splits `node (20, 22)` on the comma;
    # the dict reached the index as "{'Vite 7': ...}" and `kb search --game` crashed on .lower()
    root = tmp_path / "knowledge"
    (root / "games" / "x").mkdir(parents=True)
    note = root / "games" / "x" / "n.md"
    front = "kind: game\ntitle: t\ngame: Lane defense\ngames_also: [Merge puzzle: endless mode]\ntools: [node (20, 22), vitest]\ntags: [merge, 2048]\n"
    note.write_text(f"---\n{front}---\n# t\n", encoding="utf-8")
    fails, _ = kb.check_note(note, root)
    for key in ("games_also", "tools", "tags"):
        assert any(f.startswith(key) and "quote" in f for f in fails), (key, fails)
    assert [r["path"] for r in kb.search(root, [], game="merge puzzle")] == ["games/x/n.md"]
    assert kb.search(root, ["node"], game="lane")
    kb.build_index(root)
    for bare in ("Merge puzzle: endless mode", "node (20, 22)", "2048"):
        front = front.replace(bare, f'"{bare}"')
    note.write_text(f"---\n{front}---\n# t\n", encoding="utf-8")
    fails, _ = kb.check_note(note, root)
    assert not [f for f in fails if f.startswith(("games_also", "tools", "tags"))], fails


def test_kb_index_and_check_index(tmp_path, capsys):
    root = kb_root(tmp_path)
    (root / "README.md").write_text("# readme\n", encoding="utf-8")
    write_note(root, "games/lane-defense/waves.md")
    write_note(root, "games/idle-miner/pipes.md", GAME_NOTE.replace("Waves that breathe", "Pipes | valves").replace(
        'game: "Lane defense (mobile web)"', 'game: "Idle miner (web)"\ngames_also: ["Lane defense (mobile web)"]'))
    write_note(root, "techniques/bots.md", "---\nkind: technique\ntitle: Player-model bots\ntags: [balance, simulation]\n"
                                           "date: 2026-10-02\nagents: [\"Claude Code (Opus 5.5)\"]\n---\n# Player-model bots\n")
    assert exit_code(["kb", "check", "--root", str(root), "--index"]) == 1     # no index yet
    assert "knowledge/INDEX.md is out of date: run `wise kb index`" in capsys.readouterr().out
    cli.main(["kb", "index", "--root", str(root)])
    assert capsys.readouterr().out.strip() == f"{root / 'INDEX.md'}: 3 notes"
    idx = (root / "INDEX.md").read_text(encoding="utf-8")
    assert idx.splitlines()[:8] == [
        "# Knowledge base index", "",
        "_Generated by `wise kb index` from the notes' front matter; don't edit by hand. Machine-readable: `index.json`._", "",
        "## Games (2 notes)", "",
        "| Game | Note | Engine | Route | Status | Agents | Date |", "|---|---|---|---|---|---|---|"]
    assert ("| Idle miner (web) + Lane defense (mobile web) | [Pipes \\| valves](games/idle-miner/pipes.md) | threejs-vite | data-tuning | "
            "working | Codex (gpt-6) | 2026-10-01 |") in idx
    assert idx.index("Idle miner") < idx.index("| Lane defense (mobile web) | [Waves that breathe]")      # sorted by game
    assert "## Techniques (1 notes)" in idx and "- [Player-model bots](techniques/bots.md) · balance, simulation" in idx
    assert "TEMPLATE" not in idx and "readme" not in idx.lower()
    rows = json.loads((root / "index.json").read_text(encoding="utf-8"))
    assert [r["path"] for r in rows] == ["games/idle-miner/pipes.md", "games/lane-defense/waves.md", "techniques/bots.md"]
    assert rows[1]["date"] == "2026-10-01" and rows[2]["tags"] == ["balance", "simulation"]
    assert exit_code(["kb", "check", "--root", str(root), "--index"]) == 0
    assert capsys.readouterr().out.strip() == "PASS: 3 notes checked"
    write_note(root, "games/lane-defense/waves.md", GAME_NOTE.replace("Waves that breathe", "Waves that breathe out"))
    assert exit_code(["kb", "check", "--root", str(root), "--index"]) == 1     # both generated files are now stale
    out = capsys.readouterr().out
    assert "knowledge/INDEX.md is out of date" in out and "knowledge/index.json is out of date" in out
    assert exit_code(["kb", "check", "--root", str(root)]) == 0                # without --index the notes alone decide


def test_kb_cli_search_and_show(tmp_path, capsys):
    root = kb_root(tmp_path)
    write_note(root, "games/lane-defense/waves.md")
    cli.main(["kb", "search", "sine", "--root", str(root)])
    out = capsys.readouterr().out
    assert "games/lane-defense/waves.md" in out and "[Lane defense (mobile web) | threejs-vite | data-tuning | working]" in out
    cli.main(["kb", "search", "sine", "--root", str(root), "--json"])
    assert json.loads(capsys.readouterr().out)[0]["title"] == "Waves that breathe"
    cli.main(["kb", "search", "nothing-like-this", "--root", str(root)])
    assert "you may be first - write it up afterwards (`wise kb new`)" in capsys.readouterr().out
    cli.main(["kb", "show", "waves.md", "--root", str(root)])
    assert "# Waves that breathe" in capsys.readouterr().out
    assert exit_code(["kb", "show", "missing.md", "--root", str(root)]) == 1


@pytest.mark.parametrize("url", ["https://github.com/alice/wisecraft.git", "https://github.com/alice/wisecraft",
                                 "git@github.com:alice/wisecraft.git", "ssh://git@github.com/alice/wisecraft.git"])
def test_pr_head_from_fork(url):
    # gh looks a bare --head branch up in the base repo; a PR from a fork needs "<owner>:<branch>"
    assert kb.pr_head("kb/a-b", url) == "alice:kb/a-b"


def test_pr_head_same_repo():
    assert kb.pr_head("kb/a-b", None) == "kb/a-b"


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
        meta, body = kb.parse(f)
        assert meta and "_yaml_error" not in meta, f"{f}: needs YAML front matter"
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
