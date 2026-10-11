# Ported from Universal Modder (https://github.com/rehan-remade/universal-modder), tests/test_um.py.
# Copyright (c) 2026 Rehan and universal-modder contributors. MIT License; see LICENSE and NOTICE.
"""Offline tests for the web-game tools: scan, qa, board, loudness, dupframes.

    .venv/bin/python -m pytest -q tests/test_web.py

No network (URL scans talk to an http.server thread on 127.0.0.1), no audio playback (ffmpeg only measures,
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

from wisecraft import board, dupframes, loudness, qa, scan  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
FFMPEG = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg")
NODE = pytest.mark.skipif(shutil.which("node") is None, reason="needs node")
BODY = "aB3dE5fG7hJ9kL1mN3pQ5rS7tU9vW1xY3zA5bC7d"   # 40 harmless characters to hang a key prefix on


def wise(*argv):
    """Run `wise <argv>` in-process with only these five commands registered (the other groups are tested elsewhere)."""
    ap = argparse.ArgumentParser(prog="wise")
    sub = ap.add_subparsers(dest="group")
    for module in (scan, qa, board, loudness, dupframes):
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
    """serve(folder, headers=None) -> base URL of an http.server thread on 127.0.0.1 (closed after the test)."""
    servers = []

    def start(folder: Path, headers=None) -> str:
        class Handler(http.server.SimpleHTTPRequestHandler):
            def end_headers(self):
                for prefix, name, value in headers or []:
                    if self.path.startswith(prefix):
                        self.send_header(name, value)
                super().end_headers()

            def log_message(self, *args):
                pass

        srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Handler, directory=str(folder)))
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        servers.append(srv)
        return f"http://127.0.0.1:{srv.server_address[1]}"

    yield start
    for srv in servers:
        srv.shutdown()
        srv.server_close()


# --------------------------------------------------------------------------- scan: a project folder

APP_JS = """import * as THREE from "three";
import { VERSION } from "./data.js";
const SAVE_PREFIX = "tower.save.v2.";
const LANG_KEY = "tower.lang";
export function load(mode) { return JSON.parse(localStorage.getItem(SAVE_PREFIX + mode)); }
export function lang() { return localStorage.getItem(LANG_KEY) || localStorage.getItem("tower.audio"); }
function migrate(p) { p.schema = 3; return p; }
async function flush(batch) {
  await fetch("/api/events", { method: "POST", body: JSON.stringify(batch) });
  navigator.sendBeacon("https://collect.example.com/v1/batch?src=game", "{}");
}
// a brace in a comment } and in a string must not end the object early
window.__game = {
  guard,
  "quoted-key": 1,
  run: { nested: { deep: 1 }, list: [1, 2, { x: 1 }] },
  label: `stage ${stage} of ${ { a: 1 }.a }`,
  note: "a } brace, a comma",
  get profile() { return p(); },
  async start(mode, opts = {}) { return mode; },
  ...extras,
  store,
};
"""

GAME = {
    "package.json": json.dumps({
        "name": "tower-defense", "version": "1.4.0", "type": "module",
        "scripts": {"dev": "vite --host 0.0.0.0 --port 5196", "build": "vite build", "test": "node --test tests/*.test.js",
                    "deploy": "npm run build && npx vercel deploy --prebuilt"},
        "dependencies": {"three": "0.180.0"},
        "devDependencies": {"vite": "^7.3.6", "playwright": "1.55.0", "prettier": "^3.6.2"}}),
    "package-lock.json": json.dumps({"lockfileVersion": 3, "packages": {
        "node_modules/three": {"version": "0.180.0"}, "node_modules/vite": {"version": "7.3.9"}}}),
    "vite.config.js": 'import { defineConfig } from "vite";\nexport default defineConfig({ base: "./", build: { rollupOptions: '
                      '{ input: { lab: "index.html", play: "play.html" } } } });\n',
    "index.html": '<!doctype html><title>lab</title><script type="module" src="/src/lab.js"></script>',
    "play.html": '<!doctype html><title>play</title><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter">'
                 '<script>window.__boot = { started: false };</script><script type="module" src="/src/game/boot.js"></script>',
    "src/lab.js": "window.__lab = { density: 1 };\n",
    "src/game/boot.js": 'const start = () => import("./app.js");\nstart();\n',
    "src/game/app.js": APP_JS,
    "src/game/data.js": 'export const VERSION = "1.4.0";\nexport const COSTS = [10, 25, 60, 140, 320, 700];\n',
    "src/game/ramp.js": "export const RAMP = [\n" + "".join(f"  [{i}, {i * 12}, {i * 0.35:.2f}],\n" for i in range(1, 31)) + "];\n",
    "src/game/shop-view.js": "export const PRICES = [" + ", ".join(str(n) for n in range(60)) + "];\n",
    "src/i18n/index.js": 'import EN from "./en.js";\nexport const LANGS = ["en", "es"];\n',
    "src/i18n/en.js": "export default {};\n",
    "src/i18n/es.js": "export default {};\n",
    "tests/ramp.test.js": 'import test from "node:test";\n',
    "tests/shop.test.js": 'import test from "node:test";\n',
    "scripts/capture.mjs": 'import { chromium } from "playwright";\nawait page.evaluate(() => { window.__cap = { n: 1 }; });\n'
                           'await ctx.route("**/api/events", (r) => r.fulfill({ status: 204 }));\n',
    "public/audio/music.mp3": b"\0" * 5000,
    "public/audio/hit0.wav": b"\0" * 1200,
    "public/audio/hit1.wav": b"\0" * 800,
    "public/fonts/game.woff2": b"\0" * 300,
    "research/notes/reference.mp3": b"\0" * 90000,          # not shipped: outside src/ and public/
    "outputs/run-1/dist/assets/app-old.js": "window.__stale = {};\n",   # scratch output, never game code
    ".github/workflows/pages.yml": "jobs:\n  deploy:\n    steps:\n      - uses: actions/deploy-pages@v4\n",
    "dist/play.html": "<!doctype html>",
    "dist/assets/app-C1a2b3c4.js": 'window.__game={};typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent('
                                   'new CustomEvent("register",{detail:{revision:"180"}}));' + "var pad=0;" * 400,
    "dist/assets/app-D5e6f7g8.css": "body{margin:0}",
}


@pytest.fixture
def game(tmp_path):
    make(tmp_path, GAME)
    return scan.fingerprint(str(tmp_path))


def test_scan_threejs_vite_stack(game):
    assert game["kind"] == "dir" and game["name"] == "tower-defense" and game["version"] == "1.4.0"
    e = game["engine"]
    assert e["key"] == "threejs-vite" and e["version"] == "0.180.0" and e["vite"] is True and e["confidence"] == 100
    deps = game["package"]["deps"]
    assert deps["three"] == {"declared": "0.180.0", "resolved": "0.180.0", "dev": False}
    assert deps["vite"] == {"declared": "^7.3.6", "resolved": "7.3.9", "dev": True}
    assert deps["playwright"]["declared"] == "1.55.0" and "prettier" not in deps
    assert game["package"]["devDependencies"]["prettier"] == "^3.6.2"       # the JSON keeps every dependency
    assert game["lockfile"] == {"found": True, "file": "package-lock.json", "kind": "npm"}
    assert game["bundler"]["kind"] == "vite" and game["bundler"]["config"] == "vite.config.js"
    assert game["bundler"]["inputs"] == ["index.html", "play.html"]
    assert game["dev_server"] == {"found": True, "script": "dev", "port": 5196, "port_source": "scripts.dev"}


def test_scan_hooks_and_entries(game):
    hooks = {h["name"]: h for h in game["hooks"]}
    g = hooks["window.__game"]
    assert game["hooks"][0] is g and (g["file"], g["line"]) == ("src/game/app.js", 13)
    assert g["members"] == ["guard", "quoted-key", "run", "label", "note", "profile", "start", "store"]
    assert "members_truncated" not in g
    assert hooks["window.__lab"]["members"] == ["density"] and hooks["window.__boot"]["file"] == "play.html"
    # a capture script assigns window.__cap inside page.evaluate: that is not a hook of the game
    assert "window.__cap" not in hooks and "window.__stale" not in hooks
    assert [h["name"] for h in game["hooks_outside_game_code"]] == ["window.__cap"]
    entries = {x["file"]: x for x in game["entries"]}
    assert entries["play.html"]["modules"] == ["/src/game/boot.js"]
    assert entries["play.html"]["hooks"] == ["window.__game", "window.__boot"]      # through boot.js -> import("./app.js")
    assert entries["index.html"]["hooks"] == ["window.__lab"]


def test_scan_analytics_saves_i18n_tests(game):
    ends = {x["path"]: x for x in game["analytics"]["endpoints"]}
    assert ends["/api/events"]["file"] == "src/game/app.js" and ends["/api/events"]["via"] == "fetch"
    assert ends["/v1/batch"]["host"] == "collect.example.com" and ends["/v1/batch"]["via"] == "sendBeacon"
    assert game["analytics"]["sdks"] == []
    s = game["saves"]
    assert {k["key"] for k in s["local_storage"]} == {"tower.lang", "tower.audio"}
    assert [(k["constant"], k["value"]) for k in s["key_constants"]] == [("SAVE_PREFIX", "tower.save.v2.")]
    assert s["dynamic_keys"] == 1                                    # SAVE_PREFIX + mode is built at run time
    assert ("p.schema", "3") in {(v["name"], v["value"]) for v in s["versions"]}
    assert game["i18n"]["languages"] == ["en", "es"]
    t = game["tests"]
    assert t["files"] == 2 and [r["name"] for r in t["runners"]] == ["node --test", "playwright (library)"]


def test_scan_assets_deploy_bundle(game):
    a = game["audio"]
    assert (a["count"], a["bytes"]) == (3, 7000)                     # the research clip is not shipped audio
    assert a["formats"] == {"mp3": {"count": 1, "bytes": 5000}, "wav": {"count": 2, "bytes": 2000}}
    assert [f["file"] for f in a["largest"]] == ["public/audio/music.mp3", "public/audio/hit0.wav", "public/audio/hit1.wav"]
    assert game["fonts"]["count"] == 1 and game["fonts"]["external_hosts"] == ["fonts.googleapis.com"]
    assert game["pwa"] == {"service_worker": {"found": False}, "manifest": {"found": False}}
    assert {"kind": "github-pages", "file": ".github/workflows/pages.yml"} in game["deploy"]["configs"]
    assert game["deploy"]["scripts"] == ["deploy"] and game["deploy"]["tools"] == ["vercel"]
    b = game["bundle"]
    js = len(GAME["dist/assets/app-C1a2b3c4.js"])
    assert b["found"] and b["dir"] == "dist" and b["js_bytes"] == js and b["css_bytes"] == 14
    assert 0 < b["js_gzip_bytes"] < js / 4 and b["largest"][0]["gzip_bytes"] == b["js_gzip_bytes"]
    assert b["hooks"] == [{"name": "window.__game", "file": "dist/assets/app-C1a2b3c4.js"}]
    assert b["engine"][0]["key"] == "threejs-vite" and b["engine"][0]["version"] == "r180"
    assert game["git"] == {"found": False}


def test_scan_tuning_and_routes(game):
    files = [t["file"] for t in game["tuning"]]
    assert files[0] == "src/game/ramp.js" and "src/game/shop-view.js" not in files     # a view is not a table
    routes = [r["do"] for r in game["routes"]]
    assert routes[0] == "wise qa http://127.0.0.1:5196/play.html --ready 'window.__game'"
    assert "read src/game/app.js:13" in routes and "npm test" in routes
    assert any(r.startswith("read src/game/ramp.js") for r in routes)
    assert "wise loudness public/audio/*.mp3" in routes
    text = scan.format_report(game)
    for line in ("three.js + Vite  [threejs-vite, 100%]", "window.__game  src/game/app.js:13", "/api/events (src/game/app.js:9, fetch)",
                 "SDKs: not found", "service worker: not found; manifest: not found", "git:        not found"):
        assert line in text


@pytest.mark.parametrize("files, key, version", [
    ({"package.json": json.dumps({"dependencies": {"phaser": "^3.80.1"}})}, "phaser", "^3.80.1"),
    ({"package.json": json.dumps({"dependencies": {"pixi.js": "8.1.0"}})}, "pixi", "8.1.0"),
    ({"package.json": json.dumps({"dependencies": {"@babylonjs/core": "7.0.0"}})}, "babylon", "7.0.0"),
    ({"package.json": json.dumps({"dependencies": {"playcanvas": "2.1.0"}})}, "playcanvas", "2.1.0"),
    ({"index.html": "<canvas id=unity-canvas></canvas>", "Build/game.loader.js": "createUnityInstance", "Build/game.wasm.br": b"\0",
      "Build/game.data.br": b"\0"}, "unity-webgl", None),
    ({"index.html": "<script src=index.js></script>", "index.pck": b"GDPC", "index.wasm": b"\0asm"}, "godot-web", None),
    ({"index.html": "<script src=scripts/c3runtime.js></script>", "scripts/c3runtime.js": "// runtime", "data.json": "{}"}, "construct", None),
    ({"index.html": '<script type="importmap">{"imports":{"three":"https://unpkg.com/three@0.160.0/build/three.module.js"}}</script>'},
     "threejs-vite", "0.160.0"),
    ({"index.html": "<canvas></canvas><script src=game.js></script>", "game.js": 'const ctx = canvas.getContext("2d");'}, "canvas-2d", None),
    ({"index.html": "<h1>hello</h1>", "main.js": "console.log(1)"}, "unknown", None),
])
def test_scan_engine_keys(tmp_path, files, key, version):
    make(tmp_path, files)
    r = scan.fingerprint(str(tmp_path))
    assert r["engine"]["key"] == key and r["engine"].get("version") == version
    assert set(scan.ENGINES) >= {key}


def test_scan_says_not_found_and_never_guesses(tmp_path, capsys):
    make(tmp_path, {"readme.txt": "nothing here"})
    r = scan.fingerprint(str(tmp_path))
    assert r["engine"]["key"] == "unknown" and r["engine"]["evidence"] == ["no known engine signature"]
    for section in ("package", "bundler", "analytics", "saves", "i18n", "tests", "audio", "fonts", "deploy", "bundle", "git"):
        assert r[section]["found"] is False, section
    assert r["hooks"] == [] and r["entries"] == [] and r["tuning"] == []
    assert r["routes"][0]["do"] == "wise qa <url>"
    wise("scan", tmp_path)
    out = capsys.readouterr().out
    assert out.count("not found") >= 12 and "package.json not found" in out


def test_scan_reports_sdk_hosts_never_keys(tmp_path):
    key = "phc_" + BODY
    make(tmp_path, {"package.json": json.dumps({"dependencies": {"posthog-js": "^1.0.0"}}),
                    "src/analytics.js": f'import posthog from "posthog-js";\nposthog.init("{key}", {{ api_host: "https://eu.i.posthog.com" }});\n'
                                        'gtag("config", "G-ABC123");\nconst amplitude = Math.min(1.5, 0.2);\n'})
    r = scan.fingerprint(str(tmp_path))
    sdks = {s["name"]: s for s in r["analytics"]["sdks"]}
    assert set(sdks) == {"PostHog", "Google Analytics"}                 # a variable called amplitude is not the Amplitude SDK
    assert sdks["PostHog"]["hosts"] == ["eu.i.posthog.com"] and sdks["PostHog"]["package"] == "posthog-js"
    dump = json.dumps(r) + scan.format_report(r)
    assert key not in dump and BODY not in dump and "G-ABC123" not in dump


def test_object_keys_stops_at_the_cap():
    text = "x = {a: 1, b: {c: 2}, d() {}, [computed]: 3, e"
    assert scan.object_keys(text, text.index("{")) == (["a", "b", "d", "e"], False)       # never closed: flagged
    assert scan.object_keys("{ a, b: '}' }", 0) == (["a", "b"], True)


def test_scan_missing_folder_and_file(tmp_path, capsys):
    with pytest.raises(scan.ScanError):
        scan.fingerprint(str(tmp_path / "nope"))
    assert exit_code("scan", tmp_path / "nope") == 2
    make(tmp_path, {"page.html": "<html>"})
    assert exit_code("scan", tmp_path / "page.html") == 2
    assert "pass the project folder" in capsys.readouterr().err


def test_scan_cli_json(tmp_path, capsys):
    make(tmp_path, GAME)
    wise("scan", tmp_path, "--json")
    r = json.loads(capsys.readouterr().out)
    assert r["engine"]["key"] == "threejs-vite" and r["hooks"][0]["name"] == "window.__game"


@pytest.mark.skipif(shutil.which("git") is None, reason="needs git")
def test_scan_git_info(tmp_path):
    make(tmp_path, {"index.html": "<h1>x</h1>"})
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com", "GIT_COMMITTER_NAME": "t",
           "GIT_COMMITTER_EMAIL": "t@example.com", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull}
    for cmd in (["init", "-q", "-b", "main"], ["add", "."], ["commit", "-q", "-m", "first"], ["tag", "v0.1.0"]):
        subprocess.run(["git", "-C", str(tmp_path), *cmd], check=True, env=env, capture_output=True)
    g = scan.fingerprint(str(tmp_path))["git"]
    assert g["found"] and g["branch"] == "main" and g["last_tag"] == "v0.1.0" and len(g["head"]) >= 7


# --------------------------------------------------------------------------- scan: a URL

THREE_CHUNK = ('const REV="180";typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("register",'
               '{detail:{revision:"180"}}));typeof window<"u"&&(window.__THREE__="180");') + "var a=1;" * 300
SITE = {
    "play.html": '<!doctype html><html><head><title>Tower</title><meta name="viewport" content="width=device-width">'
                 '<link rel="stylesheet" href="./assets/play-Aa11bb22.css"><link rel="modulepreload" href="./assets/polyfill-Cc33dd44.js">'
                 '<link rel="manifest" href="./manifest.webmanifest">'
                 '<script>window.__boot={t:0};</script><script type="module" src="./assets/play-Ee55ff66.js"></script></head></html>',
    "assets/play-Aa11bb22.css": "body{margin:0}",
    "assets/polyfill-Cc33dd44.js": "(function(){})();",
    "assets/play-Ee55ff66.js": 'const __vite__mapDeps=(i,m=__vite__mapDeps,d=(m.f||(m.f=["./app-Gg77hh88.js","./three-Ii99jj00.js",'
                               '"./app-Kk11ll22.css"])))=>i.map(i=>d[i]);import"./polyfill-Cc33dd44.js";'
                               'const go=()=>import("./app-Gg77hh88.js");go();',
    "assets/app-Gg77hh88.js": 'import{W as R}from"./three-Ii99jj00.js";window.__game={run:1};'
                              'async function f(t){await t("/api/events",{method:"POST"})}navigator.serviceWorker.register("./sw.js");',
    "assets/three-Ii99jj00.js": THREE_CHUNK,
    "assets/app-Kk11ll22.css": ".hud{color:#fff}",
    "manifest.webmanifest": "{}",
}


def test_scan_url_against_a_local_server(tmp_path, serve, capsys):
    make(tmp_path, SITE)
    base = serve(tmp_path, headers=[("/assets/", "Cache-Control", "public, max-age=31536000, immutable"),
                                    ("/play.html", "Cache-Control", "no-cache")])
    r = scan.fingerprint(base + "/play.html")
    assert r["kind"] == "url" and r["title"] == "Tower" and r["status"] == 200
    e = r["engine"]
    assert e["key"] == "threejs-vite" and e["version"] == "r180" and e["vite"] is True
    assert "/assets/three-Ii99jj00.js" in e["evidence"][0]
    by = {a["path"]: a for a in r["assets"]}
    assert set(by) == {"/assets/" + n.split("/")[1] for n in SITE if n.startswith("assets/")}
    assert by["/assets/three-Ii99jj00.js"]["bytes"] == len(THREE_CHUNK) == by["/assets/three-Ii99jj00.js"]["transfer_bytes"]
    assert by["/assets/three-Ii99jj00.js"]["via"] == "import in play-Ee55ff66.js"       # found by following the entry chunk
    assert by["/assets/app-Kk11ll22.css"]["kind"] == "style" and by["/assets/play-Ee55ff66.js"]["via"] == "html"
    t = r["totals"]
    assert t["requests"] == 7 and t["skipped"] == 0 and t["js_files"] == 4
    assert t["transfer_bytes"] == len(SITE["play.html"]) + sum(len(v) for k, v in SITE.items() if k.startswith("assets/"))
    h = r["headers"]
    assert h["html_cache_control"] == "no-cache" and h["html_content_encoding"] is None
    assert (h["hashed_assets"], h["hashed_assets_long_cache"]) == (6, 6) and h["asset_encodings"] == {"none": 6}
    assert [x["name"] for x in r["hooks"]] == ["window.__game", "window.__boot"] and r["library_globals"] == ["window.__THREE__"]
    assert [x["path"] for x in r["analytics"]["endpoints"]] == ["/api/events"]
    assert r["pwa"]["service_worker"]["found"] and r["pwa"]["manifest"] == {"found": True, "href": "./manifest.webmanifest"}
    assert r["routes"][0]["do"] == f"wise qa {base}/play.html --ready 'window.__game'"
    wise("scan", base + "/play.html")
    out = capsys.readouterr().out
    assert "three.js + Vite  [threejs-vite, 90%]  version r180" in out and "content-encoding: not found" in out
    assert "hashed assets with a long or immutable cache: 6 of 6" in out


def test_scan_url_gzip_transfer_and_decoded_sizes():
    import gzip
    script = ("window.__game={};" + "var filler=0;" * 500).encode()
    packed = gzip.compress(script)

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            assert "gzip" in self.headers.get("Accept-Encoding", "") and "Mozilla" in self.headers.get("User-Agent", "")
            body, kind, enc = (packed, "text/javascript", "gzip") if self.path == "/app.js" else \
                (b'<script src="/app.js"></script>', "text/html", None)
            self.send_response(200)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(body)))
            if enc:
                self.send_header("Content-Encoding", enc)
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        r = scan.fingerprint(f"http://127.0.0.1:{srv.server_address[1]}/")
    finally:
        srv.shutdown()
        srv.server_close()
    a = r["assets"][0]
    assert (a["bytes"], a["transfer_bytes"], a["content_encoding"]) == (len(script), len(packed), "gzip")
    assert r["headers"]["asset_encodings"] == {"gzip": 1} and r["totals"]["js_bytes"] == len(script)
    assert r["hooks"] == [{"name": "window.__game", "file": "/app.js"}]             # read from the decoded script


def test_scan_url_stops_at_the_request_and_byte_caps():
    calls = []

    def fetch(url, method="GET", max_bytes=0):
        calls.append((method, url))
        if url.endswith("/"):
            tags = "".join(f'<script src="/js/s{i}.js"></script>' for i in range(50))
            return scan.Fetched(url, 200, {"content-type": "text/html"}, f"<html>{tags}</html>".encode(), 1900)
        return scan.Fetched(url, 200, {}, b"x" * 1000, 1000)

    r = scan.fingerprint_url("https://example.com/", fetch=fetch, max_requests=10)
    assert len(calls) == 10 and r["totals"]["requests"] == 10
    assert r["totals"]["skipped"] == 41 and r["totals"]["truncated"] is True and len(r["assets"]) == 9
    assert "41 asset(s) NOT fetched" in scan.format_report(r) and "limit reached" in r["routes"][-1]["why"]
    calls.clear()
    r = scan.fingerprint_url("https://example.com/", fetch=fetch, max_bytes=5000)
    assert len(calls) == 5 and r["totals"]["skipped"] == 46          # 1.9 kB of HTML, then 1 kB per script up to 5 kB
    assert r["engine"]["key"] == "unknown" and r["hooks"] == []


def test_scan_url_that_does_not_answer(capsys):
    def refuse(url, method="GET", max_bytes=0):
        return scan.Fetched(url, 0, {}, b"", None, "connection refused")

    with pytest.raises(scan.ScanError, match="connection refused"):
        scan.fingerprint_url("http://127.0.0.1:9/", fetch=refuse)
    assert scan.http_fetch("ftp://example.com/x").error == "only http and https are fetched"


def test_scan_url_404_is_a_failure(tmp_path, serve, capsys):
    base = serve(tmp_path)
    assert exit_code("scan", base + "/missing.html") == 1
    assert "HTTP 404" in capsys.readouterr().err


# --------------------------------------------------------------------------- qa

def qa_args(*argv):
    ap = argparse.ArgumentParser()
    qa.register(ap.add_subparsers())
    return ap.parse_args(["qa", *argv])


def test_qa_options_defaults():
    o = qa.options(qa_args("http://127.0.0.1:5173/play.html"))
    assert o == {"url": "http://127.0.0.1:5173/play.html", "engine": "chromium", "width": 390, "height": 844, "dpr": 2,
                 "out": os.path.join("qa-out", "chromium-390x844"), "seconds": 20, "seed": 1, "selectors": [],
                 "startSelector": None, "area": None, "ready": 'document.readyState === "complete"',
                 "block": ["**/api/events"], "noOverflow": False, "timeoutMs": 60000}


def test_qa_options_from_flags(tmp_path):
    o = qa.options(qa_args("https://example.com/play.html", "--engine", "webkit", "--size", "320x568", "--out", str(tmp_path),
                           "--seconds", "5", "--taps", "12", "--seed", "7", "--selector", "#shop", "[data-tab=pass]", "--selector", "#close",
                           "--start-selector", "#play", "--no-overflow", "--block", "**/collect", "--block", "**/api/*",
                           "--ready", "window.__game && __game.run", "--area", "canvas#field", "--timeout", "5", "--channel", "chrome"))
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
    assert o["out"] == os.path.join("qa-out", "webkit-360x740")


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
    assert r["blocked"]["requests"] >= 1 and r["failedRequests"] == []        # the beacon never left the browser
    names = [Path(s).name for s in r["screenshots"]]
    assert names == ["1-start.png", "step-1.png", "2-middle.png", "3-end.png"] and all((out / n).stat().st_size > 500 for n in names)

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


# --------------------------------------------------------------------------- loudness

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


def test_loudness_parse_log():
    r = loudness.parse(EBUR128_LOG)
    # integrated, range and peak come from loudnorm's two-decimal measurement, not the ebur128 summary
    assert (r["integrated_lufs"], r["lra_lu"], r["true_peak_dbfs"]) == (-16.12, 4.3, -1.23)
    assert (r["max_momentary_lufs"], r["max_short_term_lufs"]) == (-12.9, -15.1)       # -120.7 is "no window yet"
    assert (r["duration_s"], r["sample_rate"], r["channels"], r["channel_layout"], r["codec"]) == (64.5, 44100, 2, "stereo", "pcm_s16le")
    assert r["silent"] is False and "note" not in r
    without = loudness.parse(EBUR128_LOG.replace('"input_i"', '"other"'))                # an ffmpeg without loudnorm
    assert (without["integrated_lufs"], without["true_peak_dbfs"]) == (-16.1, -1.2)
    with pytest.raises(ValueError):
        loudness.parse("Stream map '0:a:0' matches no streams.")
    assert loudness._channels("5.1(side)") == 6 and loudness._channels("3 channels") == 3 and loudness._channels("odd") is None


def tone(path: Path, seconds: float = 3, volume: float = 1.0, stereo: bool = False):
    """A 1 kHz sine from ffmpeg's lavfi `sine` source, whose peak amplitude is 1/8, times `volume`."""
    af = f"volume={volume}" + (",pan=stereo|c0=c0|c1=c0" if stereo else "")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
                    f"sine=frequency=1000:duration={seconds}:sample_rate=48000", "-af", af, "-c:a", "pcm_s16le", str(path)], check=True)
    return path


@FFMPEG
def test_loudness_of_a_sine(tmp_path):
    # BS.1770: L = -0.691 + 10*log10(sum of K-weighted channel mean squares). The K filter adds +0.691 dB at 1 kHz,
    # so a mono sine of peak amplitude A reads 20*log10(A) - 3.01 LUFS: mean square A^2/2. A = 1/8 * 0.8 = 0.1
    # is -20 dBFS peak and -23.01 LUFS; the same signal on two channels sums to 3.01 dB more.
    expect = 20 * math.log10(0.1) - 3.01
    r = loudness.measure(str(tone(tmp_path / "tone.wav", volume=0.8)))
    assert abs(r["integrated_lufs"] - expect) < 1.5 and abs(r["integrated_lufs"] - -23.0) < 0.2
    assert abs(r["true_peak_dbfs"] - -20.0) < 0.5 and r["lra_lu"] < 1.0
    assert abs(r["max_momentary_lufs"] - expect) < 1.5
    assert r["max_short_term_lufs"] is None or abs(r["max_short_term_lufs"] - expect) < 1.5     # one 3 s window at most
    assert (r["duration_s"], r["sample_rate"], r["channels"], r["codec"]) == (3.0, 48000, 1, "pcm_s16le")
    stereo = loudness.measure(str(tone(tmp_path / "stereo.wav", volume=0.8, stereo=True)))
    assert abs(stereo["integrated_lufs"] - (expect + 3.01)) < 1.5 and stereo["channels"] == 2
    bare = loudness.measure(str(tone(tmp_path / "bare.wav")))                          # amplitude 1/8, no gain
    assert abs(bare["integrated_lufs"] - (20 * math.log10(1 / 8) - 3.01)) < 1.5


@FFMPEG
def test_loudness_target_gate_and_table(tmp_path, capsys):
    a, b = tone(tmp_path / "a.wav", volume=0.8), tone(tmp_path / "b.wav", seconds=4)
    wise("loudness", a, "--target", "-23", "--tolerance", "1")           # inside: no exit
    assert "inside -23 ±1 LUFS" in capsys.readouterr().out
    assert exit_code("loudness", a, "--target", "-15", "--tolerance", "1") == 1
    assert "OUTSIDE -15 ±1 LUFS by -8." in capsys.readouterr().out     # -23.0 against -15
    wise("loudness", a, "--target", "-15", "--tolerance", "9")           # a wide tolerance lets it through
    capsys.readouterr()
    assert exit_code("loudness", a, b, "--target", "-23", "--json") == 1               # b reads about -21.1
    r = json.loads(capsys.readouterr().out)
    assert r["ok"] is False and [f["target"]["ok"] for f in r["files"]] == [True, False] and r["files"][1]["target"]["delta"] > 1
    wise("loudness", a, b)
    table = capsys.readouterr().out.splitlines()
    assert table[0].split() == ["file", "I", "LUFS", "LRA", "TP", "dBFS", "max", "S", "max", "M", "dur", "s", "Hz", "ch"]
    assert table[1].startswith("a.wav") and table[2].startswith("b.wav") and table[3].startswith("Targets:")


@FFMPEG
def test_loudness_missing_file_and_unmeasurable_input(tmp_path, capsys):
    assert exit_code("loudness", tmp_path / "nope.wav") == 2
    assert "no such file" in capsys.readouterr().err
    make(tmp_path, {"notes.txt": "not audio"})
    assert exit_code("loudness", tmp_path / "notes.txt") == 1
    assert "could not measure" in capsys.readouterr().out
    # a 0.1 s clip never fills a 400 ms block: no loudness reading is invented, only the peak is real
    r = loudness.measure(str(tone(tmp_path / "blip.wav", seconds=0.1)))
    assert r["integrated_lufs"] is None and r["lra_lu"] is None and "too short" in r["note"]
    assert abs(r["true_peak_dbfs"] - 20 * math.log10(1 / 8)) < 0.6 and r["silent"] is False
    assert exit_code("loudness", tmp_path / "blip.wav", "--target", "-15") == 1


def test_loudness_never_plays():
    cmd = loudness.command("ffmpeg", "x.wav")
    assert cmd.count("null") == 2 and "ffplay" not in " ".join(cmd) and "-nostdin" in cmd      # both outputs are the null muxer


# --------------------------------------------------------------------------- dupframes

def video(path: Path, vf: str | None = None, seconds: int = 3):
    """testsrc2 at 30 fps (every frame differs), optionally through a filter that repeats frames."""
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i", f"testsrc2=size=160x120:rate=30:duration={seconds}"]
    subprocess.run(cmd + (["-vf", vf] if vf else []) + ["-pix_fmt", "yuv420p", str(path)], check=True)
    return path


def test_dupframes_parse_log():
    line = "[Parsed_showinfo_{f} @ 0x1] n:{n:4d} pts:{pts:7d} pts_time:{t:<8g} duration:    512 fmt:yuv420p"
    stamps = [(i * 512, i / 30) for i in range(8)]
    kept = [0, 1, 2, 6, 7]                                           # frames 3, 4, 5 repeat frame 2
    log = "  Stream #0:0[0x1](und): Video: h264 (High), yuv420p, 160x120, 27 kb/s, 30 fps, 30 tbr, 15360 tbn\n"
    log += "\n".join(line.format(f=0, n=i, pts=p, t=t) for i, (p, t) in enumerate(stamps)) + "\n"
    log += "\n".join(line.format(f=2, n=i, pts=stamps[k][0], t=stamps[k][1]) for i, k in enumerate(kept))
    r = dupframes.parse(log)
    assert (r["frames"], r["unique"], r["duplicates"], r["duplicate_pct"], r["fps"], r["runs"]) == (8, 5, 3, 37.5, 30.0, 1)
    assert r["longest_run"] == {"frames": 3, "start_s": 0.1, "seconds": 0.1}
    assert dupframes.parse(log, offset=2.0)["longest_run"]["start_s"] == 2.1                  # --start shifts the clock back
    assert dupframes.runs_of([False, True, True, False, True]) == [(1, 2), (4, 1)]
    with pytest.raises(ValueError):
        dupframes.parse("no frames here")


@FFMPEG
def test_dupframes_clean_video_has_none(tmp_path, capsys):
    r = dupframes.measure(str(video(tmp_path / "clean.mp4")))
    assert (r["frames"], r["duplicates"], r["unique"], r["fps"]) == (90, 0, 90, 30.0)
    assert r["longest_run"] == {"frames": 0, "start_s": None, "seconds": 0} and r["duplicate_pct"] == 0
    assert r["definition"] == {"filter": "mpdecimate", "hi": 768, "lo": 320, "frac": 0.33}    # dupframes.sh's definition
    wise("dupframes", tmp_path / "clean.mp4", "--max-run", "0")           # the gate passes
    assert "longest run:  none" in capsys.readouterr().out


@FFMPEG
def test_dupframes_counts_repeats_and_gates(tmp_path, capsys):
    stutter = video(tmp_path / "stutter.mp4", "fps=10,fps=30")         # every source frame shown three times
    r = dupframes.measure(str(stutter))
    assert (r["frames"], r["unique"], r["duplicates"], r["runs"]) == (90, 30, 60, 30)
    assert r["longest_run"]["frames"] == 2 and abs(r["longest_run"]["start_s"] - 1 / 30) < 0.01
    assert abs(r["duplicate_pct"] - 66.67) < 0.01
    assert exit_code("dupframes", stutter, "--max-run", "1") == 1
    assert "longest run 2 > --max-run 1: FAIL" in capsys.readouterr().out
    wise("dupframes", stutter, "--max-run", "2", "--json")
    assert json.loads(capsys.readouterr().out)["ok"] is True
    wise("dupframes", stutter, "--start", "1", "--end", "2", "--json")
    w = json.loads(capsys.readouterr().out)
    assert (w["frames"], w["duplicates"]) == (30, 20) and 1.0 <= w["longest_run"]["start_s"] < 2.0


@FFMPEG
def test_dupframes_finds_where_a_hold_starts(tmp_path):
    hold = video(tmp_path / "hold.mp4", "tpad=stop_mode=clone:stop_duration=1", seconds=2)     # 2 s of motion, a 1 s freeze
    r = dupframes.measure(str(hold))
    assert r["frames"] == 90 and r["longest_run"]["frames"] == 30 and r["runs"] == 1
    assert abs(r["longest_run"]["start_s"] - 2.0) < 0.05 and abs(r["longest_run"]["seconds"] - 1.0) < 0.01


@FFMPEG
def test_dupframes_errors(tmp_path, capsys):
    assert exit_code("dupframes", tmp_path / "nope.mp4") == 2
    clip = video(tmp_path / "clip.mp4", seconds=1)
    assert exit_code("dupframes", clip, "--threshold", "2") == 2
    assert exit_code("dupframes", clip, "--start", "3", "--end", "1") == 2
    capsys.readouterr()
    assert exit_code("dupframes", tone(tmp_path / "audio.wav", seconds=1)) == 1
    assert "no video stream" in capsys.readouterr().out


# --------------------------------------------------------------------------- the command line

@pytest.mark.parametrize("command", ["scan", "qa", "board", "loudness", "dupframes"])
def test_help_has_examples(command, capsys):
    assert exit_code(command, "--help") == 0
    out = capsys.readouterr().out
    assert out.count(f"    wise {command} ") >= 2 and "Exit 0" in out and "--json" in out
