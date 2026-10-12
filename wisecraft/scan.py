# Ported from Universal Modder (https://github.com/rehan-remade/universal-modder), um/scan.py.
# Copyright (c) 2026 Rehan and universal-modder contributors. MIT License; see LICENSE and NOTICE.
"""Fingerprint any game, or any video clip: what it is built with, how to run and build it, what to try next.

    wise scan .                                 # a project folder: the engine is detected from its files
    wise scan ~/games/tower --json              # machine-readable, for agents
    wise scan https://example.com/play.html     # a deployed web build: scripts, sizes, engine, cache headers
    wise scan http://127.0.0.1:5173 --json      # a dev server works too
    wise scan trailer.mp4                       # a video: duration, size, fps, codecs, loudness, cuts, first frame
    wise scan captures/ --sheet                 # a folder of videos: one table, and a contact sheet per clip

The input type is detected. A folder is read as Unity, Godot, Unreal, GameMaker, Defold, Cocos, a Rust, C/C++
or C# project, an Android or iOS app, or a web game (three.js, Phaser, PixiJS, Babylon.js, PlayCanvas, exported
Unity/Godot/Construct builds, plain canvas). For each it reports versions, entry points, build targets, asset and
audio folders with sizes, and ends with what to try next. A web game also gets debug hooks, analytics hosts,
saves, tuning tables and bundle sizes; a URL is fetched (at most 30 requests, 20 MB). A video is measured with
ffprobe and ffmpeg and never played.

Every fact is marked found or not found; nothing is guessed. Everything here is read-only. Analytics are
reported as hosts and paths, never keys.
Exit 0 scanned, 1 the URL or the video could not be read, 2 usage (no such folder or file).
"""
from __future__ import annotations

import fnmatch
import gzip
import json
import os
import re
import shutil
import subprocess
import urllib.error
import urllib.request
import zlib
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable, NamedTuple
from urllib.parse import urljoin, urlsplit

from wisecraft.common import die

MAX_ENTRIES = 40_000
MAX_DEPTH = 8
MAX_SOURCE_BYTES = 1_500_000      # one source file; bigger ones are bundles or data, not hand-written code
MAX_URL_REQUESTS = 30
MAX_URL_BYTES = 20 << 20
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/126.0.0.0 Safari/537.36")

SKIP_DIRS = {"node_modules", ".git", "__pycache__", ".venv", "venv", ".cache", ".turbo", ".parcel-cache", ".next",
             ".nuxt", ".svelte-kit", "coverage", ".idea", ".vscode", ".pytest_cache"}
BUILD_DIRS = ("dist", "build", "out", ".output")   # where a bundle report is looked for
# top-level folders that hold build output, deploy staging or scratch renders, never the game's source
BUILD_TOP = re.compile(r"^(?:(?:dist|build|out|output|outputs|release|releases|tmp|temp)(?:[-_.].*)?|\.output|\.vercel|\.netlify)$", re.I)
SOURCE_ROOTS = ("src", "app", "client", "game", "js", "lib", "source")
ASSET_ROOTS = SOURCE_ROOTS + ("public", "assets", "static", "resources", "res", "media", "audio", "sound", "sounds", "sfx",
                              "music", "fonts", "www")
BACKEND_DIRS = ("server/", "api/", "functions/", "backend/")
# folders whose code is not the game itself: tests, tooling, capture scripts, docs
SIDE_DIRS = {"tests", "test", "__tests__", "e2e", "qa", "scripts", "tools", "docs", "concept", "server", "api"}
CODE_EXT = (".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".vue", ".svelte")
AUDIO_EXT = (".mp3", ".ogg", ".oga", ".wav", ".m4a", ".aac", ".opus", ".flac", ".weba")
FONT_EXT = (".woff2", ".woff", ".ttf", ".otf")

# dependencies worth a line in the report (the JSON carries all of them)
KEY_DEPS = ["vite", "three", "phaser", "pixi.js", "@babylonjs/core", "babylonjs", "playcanvas", "react", "react-dom",
            "@react-three/fiber", "vue", "svelte", "typescript", "playwright", "@playwright/test", "vitest", "jest",
            "webpack", "parcel", "rollup", "esbuild", "howler", "tone", "matter-js", "cannon-es",
            "@dimforge/rapier3d-compat", "gsap", "i18next"]

ENGINES = {
    # key: label
    "threejs-vite": "three.js",
    "phaser": "Phaser",
    "pixi": "PixiJS",
    "babylon": "Babylon.js",
    "playcanvas": "PlayCanvas",
    "unity-webgl": "Unity (WebGL build)",
    "godot-web": "Godot (web export)",
    "construct": "Construct",
    "canvas-2d": "Canvas 2D (no engine library)",
    "unknown": "Unknown",
}


class ScanError(ValueError):
    """The target can't be scanned (no such folder, unreachable URL)."""


def human(n: int | None) -> str:
    if n is None:
        return "size not reported"
    for unit, div in (("MB", 1 << 20), ("kB", 1 << 10)):
        if n >= div:
            return f"{n / div:.1f} {unit}"
    return f"{n} B"


def line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


# --------------------------------------------------------------------------- the file index


class Index:
    """Relative paths of a project folder (bounded walk); patterns match case-insensitively."""

    def __init__(self, root: Path):
        self.root = root
        self.files: list[str] = []
        self.dirs: set[str] = set()
        self.truncated = False
        base = len(str(root)) + 1
        for dirpath, dirnames, filenames in os.walk(root):
            rel = dirpath[base:].replace("\\", "/")
            depth = rel.count("/") + 1 if rel else 0
            if depth >= MAX_DEPTH:
                dirnames[:] = []
            dirnames[:] = sorted((d for d in dirnames if d.lower() not in SKIP_DIRS),
                                 key=lambda d: (bool(not rel and BUILD_TOP.match(d)), d))
            for d in dirnames:
                self.dirs.add((rel + "/" + d if rel else d).lower())
            for f in sorted(filenames):
                self.files.append(rel + "/" + f if rel else f)
            if len(self.files) > MAX_ENTRIES:
                self.truncated = True
                break
        self._lower = [f.lower() for f in self.files]
        self._text: dict[str, str | None] = {}
        self._sources: list[str] | None = None
        self._game: list[str] | None = None

    def find(self, *patterns: str) -> list[str]:
        return [f for f, low in zip(self.files, self._lower) if any(fnmatch.fnmatch(low, p) for p in patterns)]

    def has(self, *patterns: str) -> bool:
        return any(fnmatch.fnmatch(low, p) for p in patterns for low in self._lower)

    def has_dir(self, *patterns: str) -> bool:
        return any(fnmatch.fnmatch(d, p) for p in patterns for d in self.dirs)

    def size(self, rel: str) -> int:
        try:
            return (self.root / rel).stat().st_size
        except OSError:
            return 0

    def text(self, rel: str, limit: int = MAX_SOURCE_BYTES) -> str | None:
        """File contents, or None when it is unreadable or over the size limit (read once)."""
        if rel not in self._text:
            try:
                p = self.root / rel
                self._text[rel] = p.read_text(encoding="utf-8", errors="replace") if p.stat().st_size <= limit else None
            except OSError:
                self._text[rel] = None
        return self._text[rel]

    def sources(self) -> list[str]:
        """Hand-written code and HTML: everything outside build output."""
        if self._sources is None:
            self._sources = [f for f in self.files if f.lower().endswith(CODE_EXT + (".html",)) and not in_build(f)
                             and not f.lower().endswith((".min.js", ".d.ts"))]
        return self._sources

    def game_sources(self) -> list[str]:
        """The game's own code: under src/ (or a sibling source root), root-level files and public/ when such a
        root exists; otherwise every source file that isn't tests, tooling or docs."""
        if self._game is None:
            self._game = [f for f in self.sources() if self.is_game(f)]
        return self._game

    def is_game(self, rel: str) -> bool:
        if is_side(rel) or in_build(rel):
            return False
        roots = tuple(r + "/" for r in SOURCE_ROOTS if r in self.dirs)
        return not roots or "/" not in rel or rel.lower().startswith(roots + ("public/",))

    def is_asset(self, rel: str) -> bool:
        """Shipped with the game: under an asset or source root when one exists, never build output or tooling."""
        if is_side(rel) or in_build(rel):
            return False
        roots = tuple(r + "/" for r in ASSET_ROOTS if r in self.dirs)
        return not roots or "/" not in rel or rel.lower().startswith(roots)


def in_dirs(rel: str, names) -> bool:
    return any(part.lower() in names for part in rel.split("/")[:-1])


def in_build(rel: str) -> bool:
    """Under a top-level build/output folder (dist/, build/, outputs/, .vercel/ ...)."""
    return "/" in rel and bool(BUILD_TOP.match(rel.split("/", 1)[0]))


def is_side(rel: str) -> bool:
    return in_dirs(rel, SIDE_DIRS) or bool(re.search(r"\.(test|spec)\.[a-z]+$", rel.lower()))


AUTOMATION_RE = re.compile(r"page\.evaluate\s*\(|addInitScript\s*\(|from\s*[\"'](?:playwright|@playwright/test|puppeteer)[\"']")


def is_automation(text: str) -> bool:
    """A script that drives a browser: what it assigns on `window` runs in a test page, not in the game."""
    return bool(AUTOMATION_RE.search(text))


# --------------------------------------------------------------------------- reading JavaScript cheaply

IDENT = re.compile(r"[A-Za-z_$][\w$]*|\d+")


def _skip_string(text: str, i: int, n: int) -> int:
    """Index just past the string or template literal that opens at text[i]."""
    q, j = text[i], i + 1
    while j < n:
        c = text[j]
        if c == "\\":
            j += 2
        elif c == q:
            return j + 1
        elif q == "`" and text.startswith("${", j):
            depth, j = 1, j + 2
            while j < n and depth:
                if text[j] in "\"'`":
                    j = _skip_string(text, j, n)
                    continue
                depth += (text[j] == "{") - (text[j] == "}")
                j += 1
        elif c == "\n" and q != "`":
            return j        # not a string after all (an apostrophe in a regex): give up on this line
        else:
            j += 1
    return n


def object_keys(text: str, start: int, limit: int = 400_000) -> tuple[list[str], bool]:
    """Top-level keys of the object literal opening at text[start] == '{'  ->  (keys, reached the closing brace).

    A scanner, not a parser: strings, comments and nesting are tracked; getters, methods and shorthand count."""
    keys: list[str] = []
    depth, i, n, expect = 0, start, min(len(text), start + limit), False
    while i < n:
        c = text[i]
        if c in "\"'`":
            j = _skip_string(text, i, n)
            if expect and depth == 1 and c != "`" and j - i >= 2:
                keys.append(text[i + 1:j - 1])
                expect = False
            i = j
        elif c == "/" and text.startswith("//", i):
            j = text.find("\n", i)
            i = n if j < 0 else j
        elif c == "/" and text.startswith("/*", i):
            j = text.find("*/", i + 2)
            i = n if j < 0 else j + 2
        elif c in "{([":
            depth += 1
            expect = depth == 1
            i += 1
        elif c in "})]":
            depth -= 1
            i += 1
            if depth <= 0:
                return keys, True
        elif depth == 1 and c == ",":
            expect = True
            i += 1
        elif depth == 1 and expect and text.startswith("...", i):
            expect = False
            i += 3
        elif depth == 1 and expect and IDENT.match(text, i):
            m = IDENT.match(text, i)
            k = m.end()
            while k < n and text[k] in " \t":
                k += 1
            if m.group(0) in ("get", "set", "async", "static") and (IDENT.match(text, k) or text[k:k + 1] in ("*", "[")):
                i = k       # a modifier: the key is the next word
            else:
                keys.append(m.group(0))
                expect = False
                i = m.end()
        else:
            i += 1
    return keys, False


IMPORT_RE = re.compile(r"""(?:\bfrom|\bimport)\s*\(?\s*["'`]([./][^"'`\s]+)["'`]""")


def resolve_import(ix_files: set[str], importer: str, spec: str) -> str | None:
    spec = spec.split("?")[0].split("#")[0]
    base = spec.lstrip("/") if spec.startswith("/") else os.path.normpath(os.path.join(os.path.dirname(importer), spec)).replace("\\", "/")
    for cand in (base, *(base + e for e in CODE_EXT), *(base + "/index" + e for e in CODE_EXT), "public/" + base):
        if cand in ix_files:
            return cand
    return None


def reachable(ix: Index, starts: list[str], cap: int = 800) -> set[str]:
    """Files an entry script pulls in through relative static and dynamic imports (bounded)."""
    files, seen, todo = set(ix.files), set(), list(starts)
    while todo and len(seen) < cap:
        f = todo.pop()
        if f in seen:
            continue
        seen.add(f)
        text = ix.text(f)
        if not text:
            continue
        for m in IMPORT_RE.finditer(text):
            r = resolve_import(files, f, m.group(1))
            if r and r not in seen and r.lower().endswith(CODE_EXT):
                todo.append(r)
    return seen


# --------------------------------------------------------------------------- package.json, lockfile, bundler

LOCKFILES = [("package-lock.json", "npm"), ("npm-shrinkwrap.json", "npm"), ("pnpm-lock.yaml", "pnpm"),
             ("yarn.lock", "yarn"), ("bun.lockb", "bun"), ("bun.lock", "bun")]
BUNDLERS = [("vite", ("vite.config.*",)), ("webpack", ("webpack.config.*", "webpack.*.js")), ("parcel", (".parcelrc",)),
            ("rollup", ("rollup.config.*",)), ("esbuild", ("esbuild.config.*", "esbuild.mjs", "build.mjs"))]


def read_json(path: Path, limit: int = 30 << 20):
    try:
        if path.stat().st_size > limit:
            return None
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, json.JSONDecodeError):
        return None


def package_facts(root: Path, ix: Index) -> dict:
    pkg = read_json(root / "package.json")
    lock = next(({"found": True, "file": f, "kind": kind} for f, kind in LOCKFILES if (root / f).is_file()), {"found": False})
    if not isinstance(pkg, dict):
        return {"found": False, "lockfile": lock, "dependencies": {}, "devDependencies": {}, "deps": {}, "scripts": {}}
    deps, dev = pkg.get("dependencies") or {}, pkg.get("devDependencies") or {}
    locked = {}
    if lock.get("kind") == "npm":
        data = read_json(root / lock["file"]) or {}
        for name in {**deps, **dev}:
            v = ((data.get("packages") or {}).get("node_modules/" + name) or (data.get("dependencies") or {}).get(name) or {}).get("version")
            if v:
                locked[name] = v
    for name in {**deps, **dev}:
        if name not in locked and (name in KEY_DEPS or name.startswith("@pixi/")):
            inst = read_json(root / "node_modules" / name / "package.json", limit=1 << 20)
            if isinstance(inst, dict) and inst.get("version"):
                locked[name] = inst["version"]
    interesting = {}
    for name, declared in {**dev, **deps}.items():
        if name in KEY_DEPS or name.startswith("@pixi/"):
            interesting[name] = {"declared": declared, "resolved": locked.get(name), "dev": name not in deps}
    return {"found": True, "name": pkg.get("name"), "version": pkg.get("version"), "type": pkg.get("type"),
            "scripts": pkg.get("scripts") or {}, "dependencies": deps, "devDependencies": dev, "deps": interesting,
            "resolved": locked, "lockfile": lock}


def bundler_facts(root: Path, ix: Index, pkg: dict) -> dict:
    for kind, patterns in BUNDLERS:
        configs = [f for f in ix.find(*patterns) if "/" not in f]
        if configs:
            out = {"found": True, "kind": kind, "config": configs[0]}
            text = ix.text(configs[0]) or ""
            inputs = sorted(set(re.findall(r"""["'`]([\w./-]+\.html)["'`]""", text)))
            if inputs:
                out["inputs"] = inputs
            m = re.search(r"\bport\s*:\s*(\d{2,5})", text)
            if m:
                out["port"] = int(m.group(1))
            m = re.search(r"""\bbase\s*:\s*["'`]([^"'`]*)["'`]""", text)
            if m:
                out["base"] = m.group(1)
            return out
    for kind in ("vite", "webpack", "parcel", "rollup", "esbuild"):
        if kind in pkg.get("deps", {}) or kind in pkg.get("dependencies", {}) or kind in pkg.get("devDependencies", {}):
            return {"found": True, "kind": kind, "config": None}
    return {"found": False}


# --------------------------------------------------------------------------- engine detection

# (key, markers in script text, version patterns, version prefix)
TEXT_ENGINES = [
    ("threejs-vite", (r"__THREE_DEVTOOLS__", r"\bTHREE\.WebGLRenderer\b", r"Multiple instances of Three\.js"),
     (r"""revision:\s*["'](\d{2,3})["']""", r"""\bREVISION\s*=\s*["'](\d{2,3})["']""", r"""__THREE__\s*=\s*["'](\d{2,3})["']"""), "r"),
    ("phaser", (r"\bPhaser\.Game\b", r"\bPhaser v\d", r"phaser\.io", r"\bPhaser\.AUTO\b"),
     (r"Phaser v(\d+\.\d+\.\d+)", r"""Phaser[^;]{0,400}?VERSION:\s*["'](\d+\.\d+\.\d+)["']"""), ""),
    ("pixi", (r"\bPIXI\.Application\b", r"PixiJS \d", r"pixijs\.com", r"pixijs\.download"),
     (r"PixiJS (\d+\.\d+\.\d+)", r"""pixi\.js[@/ ]v?(\d+\.\d+\.\d+)"""), ""),
    ("babylon", (r"\bBABYLON\.Engine\b", r"Babylon\.js v\d", r"babylonjs\.com"),
     (r"Babylon\.js v(\d+\.\d+\.\d+)",), ""),
    ("playcanvas", (r"\bpc\.Application\b", r"\bpc\.createScript\b", r"__game-scripts\.js", r"Powered by PlayCanvas", r"playcanvas-stable"),
     (r"Powered by PlayCanvas (\d+\.\d+\.\d+)",), ""),
    ("unity-webgl", (r"\bcreateUnityInstance\b", r"\bUnityLoader\.instantiate\b", r"\.loader\.js[\"'`]"),
     (r"""unityVersion["']?\s*[:=]\s*["'](\d{4}\.\d+\.\d+\w*)["']""",), ""),
    ("godot-web", (r"\bGODOT_CONFIG\b", r"\bnew Engine\(\s*GODOT", r"Godot Engine v\d"),
     (r"Godot Engine v(\d+\.\d+(?:\.\d+)?)",), ""),
    ("construct", (r"c3runtime\.js", r"c2runtime\.js", r"\bC3\.Plugins\b", r"\bcr_createRuntime\b"), (), ""),
]
# a pinned CDN or import-map URL names the library and its version outright
CDN_ENGINES = [("threejs-vite", r"\bthree@(\d+\.\d+\.\d+)"), ("phaser", r"\bphaser@(\d+\.\d+\.\d+)"),
               ("pixi", r"\bpixi\.js@(\d+\.\d+\.\d+)"), ("babylon", r"\b(?:babylonjs|@babylonjs/core)@(\d+\.\d+\.\d+)"),
               ("playcanvas", r"\bplaycanvas@(\d+\.\d+\.\d+)")]
VITE_MARKERS = re.compile(r"__vite__mapDeps|__vitePreload|/@vite/client|modulepreload-polyfill")
CANVAS_2D = re.compile(r"""getContext\(\s*["'`]2d["'`]""")


def engines_in_text(texts: dict[str, str]) -> list[tuple[str, int, list[str], dict]]:
    """Engine signatures inside script or HTML text  ->  [(key, score, evidence, details)]."""
    hits = []
    for key, markers, versions, prefix in TEXT_ENGINES:
        for name, text in texts.items():
            marker = next((m.group(0) for pat in markers for m in [re.search(pat, text)] if m), None)
            if not marker:
                continue
            det = {}
            for pat in versions:
                m = re.search(pat, text)
                if m:
                    det["version"] = prefix + m.group(1)
                    break
            hits.append((key, 90, [f"`{marker}` in {name}"], det))
            break
    for key, pat in CDN_ENGINES:
        if any(h[0] == key for h in hits):
            continue
        for name, text in texts.items():
            m = re.search(pat, text)
            if m:
                hits.append((key, 85, [f"`{m.group(0)}` in {name}"], {"version": m.group(1)}))
                break
    return hits


def detect(ix: Index, pkg: dict, bundler: dict) -> list[tuple[str, int, list[str], dict]]:
    """-> [(engine_key, score, evidence, details)], best first."""
    hits: list[tuple[str, int, list[str], dict]] = []
    deps = pkg.get("deps", {})
    every = {**pkg.get("devDependencies", {}), **pkg.get("dependencies", {})}

    def add(key, score, ev, **det):
        hits.append((key, score, ev, {k: v for k, v in det.items() if v not in (None, "")}))

    def dep(name):
        d = deps.get(name)
        return None if not d else (f"dependency {name} {d['declared']}" + (f" (resolved {d['resolved']})" if d["resolved"] and d["resolved"] != d["declared"] else ""),
                                   d["resolved"] or d["declared"])

    if dep("three"):
        ev, ver = dep("three")
        vite = "vite" in deps or bundler.get("kind") == "vite"
        add("threejs-vite", 100, [ev, "vite: found" if vite else "vite: not found"], version=ver, vite=vite)
    if dep("phaser"):
        add("phaser", 100, [dep("phaser")[0]], version=dep("phaser")[1])
    pixi = dep("pixi.js") or next((dep(n) for n in deps if n.startswith("@pixi/")), None)
    if pixi:
        add("pixi", 100, [pixi[0]], version=pixi[1])
    babylon = dep("@babylonjs/core") or dep("babylonjs")
    if babylon:
        add("babylon", 100, [babylon[0]], version=babylon[1])
    if dep("playcanvas"):
        add("playcanvas", 100, [dep("playcanvas")[0]], version=dep("playcanvas")[1])
    if "c3runtime" in every:
        add("construct", 90, ["dependency c3runtime"])

    # exported builds, recognised by their files
    unity = ix.find("build/*.loader.js", "*/build/*.loader.js", "*unityloader.js")
    if unity and ix.has("*.wasm", "*.wasm.*", "*.unityweb", "*.data", "*.data.*"):
        add("unity-webgl", 95, unity[:1] + ix.find("*.wasm", "*.wasm.*", "*.unityweb")[:1])
    pck = ix.find("*.pck")
    if pck and ix.has("*.wasm"):
        add("godot-web", 95, pck[:1] + ix.find("*.wasm")[:1])
    elif ix.has("project.godot"):
        presets = ix.text("export_presets.cfg") or ""
        web = bool(re.search(r'platform\s*=\s*"(?:Web|HTML5)"', presets))
        add("godot-web", 90 if web else 60, ["project.godot", "export_presets.cfg: Web preset " + ("found" if web else "not found")])
    construct = ix.find("*c3runtime.js", "*c2runtime.js", "*c3main.js")
    if construct:
        add("construct", 95, construct[:2])
    playcanvas = ix.find("*__game-scripts.js", "*playcanvas-stable.min.js", "*playcanvas.min.js")
    if playcanvas:
        add("playcanvas", 90, playcanvas[:2])

    # libraries vendored as files, or named in HTML (CDN tags, import maps)
    have = {h[0] for h in hits}
    vendored = [f for f in ix.find("*three.module*.js", "*three.min.js", "*three.core*.js", "*phaser*.js", "*pixi*.js", "*babylon*.js")
                if not in_build(f)][:6]
    texts = {f: t for f in vendored + [f for f in ix.files if f.lower().endswith(".html") and not in_build(f)][:12]
             for t in [ix.text(f, limit=8 << 20)] if t}
    for key, score, ev, det in engines_in_text(texts):
        if key not in have:
            add(key, score - 5, ev, **det)
            have.add(key)

    if not hits:
        for f in ix.game_sources():
            text = ix.text(f) or ""
            m = CANVAS_2D.search(text)
            if m:
                add("canvas-2d", 60, [f"{f}:{line_of(text, m.start())} getContext(\"2d\")", "no engine library found"])
                break
    if not hits:
        add("unknown", 10, ["no known engine signature"])
    hits.sort(key=lambda h: -h[1])
    return hits


# --------------------------------------------------------------------------- debug hooks

HOOK_RE = re.compile(r"\b(?:window|globalThis|self)\.(__[A-Za-z_$][\w$]*)\s*=(?!=)\s*")
LIB_GLOBALS = re.compile(r"^__(?:THREE|REACT|VUE|PIXI|SENTRY|vite|zone|REDUX|NEXT|NUXT|webpack|core-js|APOLLO)", re.I)


def hook_facts(ix: Index) -> tuple[list[dict], list[dict]]:
    """`window.__x = ...` assignments  ->  (hooks in game code, names only set by tests, capture scripts or tools)."""
    game: dict[str, dict] = {}
    auto: dict[str, dict] = {}
    for f in ix.sources():
        text = ix.text(f)
        if not text or "__" not in text:
            continue
        side = not ix.is_game(f) or is_automation(text)
        for m in HOOK_RE.finditer(text):
            name = m.group(1)
            if LIB_GLOBALS.match(name):
                continue
            bucket = auto if side else game
            if name in bucket:
                bucket[name]["occurrences"] += 1
                continue
            h = {"name": "window." + name, "file": f, "line": line_of(text, m.start()), "occurrences": 1}
            if not side and text[m.end():m.end() + 1] == "{":
                keys, closed = object_keys(text, m.end())
                h["members"] = keys
                if not closed:
                    h["members_truncated"] = True
            bucket[name] = h
    hooks = sorted(game.values(), key=lambda h: (h["name"] != "window.__game", "members" not in h, h["file"], h["line"]))
    only_auto = [h for n, h in sorted(auto.items()) if n not in game]
    return hooks, only_auto


# --------------------------------------------------------------------------- analytics

API_RE = re.compile(r"""["'`](/api/[\w\-./]*[\w\-])""")
CALL_URL_RE = re.compile(r"""\b(fetch|sendBeacon)\s*\(\s*["'`](https?://[^"'`\s?#$]+)""")
VIA_RE = re.compile(r"\b(fetch|sendBeacon|XMLHttpRequest|axios)\b[^;\n]{0,60}$")
# name, call markers, host patterns, package names. Only SDK names and hosts are ever reported, never init arguments.
SDKS = [
    ("PostHog", (r"\bposthog\.init\s*\(",), (r"\b[\w.-]*posthog\.com\b",), ("posthog-js",)),
    ("Google Analytics", (r"\bgtag\s*\(\s*[\"']",), (r"\b[\w.-]*googletagmanager\.com\b", r"\b[\w.-]*google-analytics\.com\b"), ()),
    ("Amplitude", (r"\bamplitude\.(?:init|getInstance)\s*\(",), (r"\b[\w.-]*amplitude\.com\b",), ("@amplitude/analytics-browser", "amplitude-js")),
    ("Mixpanel", (r"\bmixpanel\.init\s*\(",), (r"\b[\w.-]*mixpanel\.com\b",), ("mixpanel-browser",)),
    ("Plausible", (), (r"\b[\w.-]*plausible\.io\b",), ("plausible-tracker",)),
    ("Segment", (), (r"\bcdn\.segment\.com\b", r"\bapi\.segment\.io\b"), ("@segment/analytics-next",)),
    ("GameAnalytics", (r"\bGameAnalytics\s*\(\s*[\"']",), (r"\b[\w.-]*gameanalytics\.com\b",), ("gameanalytics",)),
    ("Firebase Analytics", (r"\bgetAnalytics\s*\(", r"firebase/analytics"), (), ()),
    ("Sentry (error reporting)", (r"\bSentry\.init\s*\(",), (r"\b[\w.-]*sentry\.io\b",), ("@sentry/browser",)),
]


def analytics_in_text(name: str, text: str, endpoints: dict, sdks: dict):
    for m in API_RE.finditer(text):
        path = m.group(1)
        if path not in endpoints:
            via = VIA_RE.search(text[max(0, m.start() - 80):m.start()])
            endpoints[path] = {"path": path, "file": name, "line": line_of(text, m.start()), "via": via.group(1) if via else "string literal"}
    for m in CALL_URL_RE.finditer(text):
        u = urlsplit(m.group(2))
        key = u.netloc + u.path
        if key not in endpoints:
            endpoints[key] = {"host": u.netloc, "path": u.path or "/", "file": name, "line": line_of(text, m.start()), "via": m.group(1)}
    for sdk, calls, hosts, _ in SDKS:
        for pat in calls + hosts:
            for m in re.finditer(pat, text):
                entry = sdks.setdefault(sdk, {"name": sdk, "file": name, "line": line_of(text, m.start()), "hosts": []})
                host = m.group(0).lower()
                if pat in hosts and host not in entry["hosts"]:
                    entry["hosts"].append(host)


def analytics_facts(ix: Index, pkg: dict) -> dict:
    endpoints, sdks = {}, {}
    # the game's own code first, then a backend folder (a proxy that forwards events is worth knowing about)
    files = ix.game_sources() + [f for f in ix.sources() if f.lower().startswith(BACKEND_DIRS)]
    for f in files:
        text = ix.text(f)
        if not text or is_automation(text) or re.search(r"\.(test|spec)\.[a-z]+$", f.lower()):
            continue
        analytics_in_text(f, text, endpoints, sdks)
    every = {**pkg.get("devDependencies", {}), **pkg.get("dependencies", {})}
    for sdk, _, _, packages in SDKS:
        for p in packages:
            if p in every:
                sdks.setdefault(sdk, {"name": sdk, "file": "package.json", "line": None, "hosts": []})["package"] = p
    return {"found": bool(endpoints or sdks), "endpoints": list(endpoints.values()), "sdks": list(sdks.values())}


# --------------------------------------------------------------------------- saves

STORAGE_RE = re.compile(r"\b(localStorage|sessionStorage)\s*\??\.\s*(getItem|setItem|removeItem)\s*\(\s*([^,)\n]+)")
KEY_CONST_RE = re.compile(r"""\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(["'`])([^"'`\n]{1,120})\2""")
KEY_NAME_RE = re.compile(r"(save|storage|store|profile|persist)\w*(key|prefix|name)", re.I)
IDB_RE = re.compile(r"""\bindexedDB\s*\??\.\s*open\s*\(\s*(["'`])([^"'`\n]+)\1\s*(?:,\s*(\d+))?""")
VER_CONST_RE = re.compile(r"""\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(\d+(?:\.\d+)*|"[^"\n]{0,40}"|'[^'\n]{0,40}')""")
VER_ASSIGN_RE = re.compile(r"(?<![\w$])((?:[\w$]+\.)+(?:schema|schemaVersion|saveVersion|dataVersion|version))\s*=(?!=)\s*(\d+)\b")
VER_KEY_RE = re.compile(r"""(?<![\w$.])(schema|schemaVersion|saveVersion|dataVersion|version)\s*:\s*(\d+|"[\d.]{1,16}"|'[\d.]{1,16}')""")
VER_NAME_RE = re.compile(r"version|schema", re.I)


def save_facts(ix: Index) -> dict:
    local, session, idb, constants, versions = {}, {}, [], {}, []
    unresolved = 0
    for f in ix.game_sources():
        text = ix.text(f)
        if not text or is_automation(text):
            continue
        consts = None
        touches = False
        for m in STORAGE_RE.finditer(text):
            touches = True
            arg = m.group(3).strip()
            bucket = local if m.group(1) == "localStorage" else session
            lit = re.fullmatch(r"""(["'`])([^"'`$]+)\1""", arg)
            if lit:
                key, const = lit.group(2), None
            else:
                if consts is None:
                    consts = {c.group(1): c.group(3) for c in KEY_CONST_RE.finditer(text)}
                key, const = consts.get(arg), arg
                if key is None:
                    unresolved += 1
                    continue
            bucket.setdefault(key, {"key": key, "file": f, "line": line_of(text, m.start()), **({"constant": const} if const else {})})
        for m in KEY_CONST_RE.finditer(text):
            if KEY_NAME_RE.search(m.group(1)):
                touches = True
                constants.setdefault(m.group(3), {"constant": m.group(1), "value": m.group(3), "file": f, "line": line_of(text, m.start())})
        for m in IDB_RE.finditer(text):
            touches = True
            idb.append({"name": m.group(2), "version": int(m.group(3)) if m.group(3) else None, "file": f, "line": line_of(text, m.start())})
        if touches or re.search(r"save|profile|storage|persist", f.rsplit("/", 1)[-1], re.I):
            seen = {(v["name"], v["value"]) for v in versions}
            for rx in (VER_CONST_RE, VER_ASSIGN_RE, VER_KEY_RE):
                for m in rx.finditer(text):
                    if rx is VER_CONST_RE and not VER_NAME_RE.search(m.group(1)):
                        continue
                    item = (m.group(1), m.group(2).strip("\"'"))
                    if item not in seen:
                        seen.add(item)
                        versions.append({"name": item[0], "value": item[1], "file": f, "line": line_of(text, m.start())})
    constants = {v: c for v, c in constants.items() if v not in local and v not in session}
    return {"found": bool(local or session or idb or constants),
            "local_storage": list(local.values()), "session_storage": list(session.values()), "indexed_db": idb,
            "key_constants": list(constants.values()), "dynamic_keys": unresolved, "versions": versions[:12]}


# --------------------------------------------------------------------------- i18n, tests, assets, deploy

I18N_DIRS = ("i18n", "locales", "locale", "lang", "langs", "languages", "translations", "l10n")
LOCALE_RE = re.compile(r"^[a-z]{2}(?:[-_][A-Za-z]{2,4})?$")
LANGS_RE = re.compile(r"\b(?:SUPPORTED_)?(?:LANGS|LANGUAGES|LOCALES|languages|locales|langs)\s*=\s*\[([^\]]{0,400})\]")
I18N_LIBS = ("i18next", "vue-i18n", "react-intl", "react-i18next", "@lingui/core", "node-polyglot", "svelte-i18n")


def i18n_facts(ix: Index, pkg: dict) -> dict:
    langs, evidence = set(), []
    for f in ix.files:
        parts = f.split("/")
        if in_build(f) or is_side(f) or not any(p.lower() in I18N_DIRS for p in parts[:-1]):
            continue
        at = max(i for i, p in enumerate(parts[:-1]) if p.lower() in I18N_DIRS)
        folder = "/".join(parts[:at + 1])
        cand = parts[at + 1].rsplit(".", 1)[0] if at + 1 == len(parts) - 1 else parts[at + 1]
        if LOCALE_RE.match(cand) and (at + 1 < len(parts) - 1 or f.lower().endswith(CODE_EXT + (".json", ".yaml", ".yml", ".po"))):
            langs.add(cand)
            if folder not in evidence:
                evidence.append(folder)
        if f.lower().endswith(CODE_EXT):
            m = LANGS_RE.search(ix.text(f) or "")
            if m:
                listed = [c for c in re.findall(r"""["']([A-Za-z]{2}(?:[-_][A-Za-z]{2,4})?)["']""", m.group(1))]
                if listed:
                    langs.update(listed)
                    evidence.append(f"{f}:{line_of(ix.text(f), m.start())}")
    every = {**pkg.get("devDependencies", {}), **pkg.get("dependencies", {})}
    libs = [n for n in I18N_LIBS if n in every]
    return {"found": bool(langs or libs), "languages": sorted(langs), "evidence": evidence[:6], "libraries": libs}


TEST_FILE_RE = re.compile(r"\.(test|spec)\.(js|mjs|cjs|ts|tsx|jsx)$")
RUNNERS = [("node --test", r"\bnode\s+(?:--[\w-]+(?:=\S+)?\s+)*--test\b", ()), ("vitest", r"\bvitest\b", ("vitest",)),
           ("jest", r"\bjest\b", ("jest",)), ("playwright test", r"\bplaywright\s+test\b", ("@playwright/test",)),
           ("mocha", r"\bmocha\b", ("mocha",)), ("cypress", r"\bcypress\b", ("cypress",))]


def test_facts(ix: Index, pkg: dict) -> dict:
    scripts = pkg.get("scripts", {})
    every = {**pkg.get("devDependencies", {}), **pkg.get("dependencies", {})}
    runners = []
    for name, pat, packages in RUNNERS:
        where = [f"scripts.{k}" for k, v in scripts.items() if isinstance(v, str) and re.search(pat, v)]
        where += [f"dependency {p}" for p in packages if p in every]
        where += ix.find(f"{name.split()[0]}.config.*")[:1] if name not in ("node --test",) else []
        if where:
            runners.append({"name": name, "evidence": where[:4]})
    if "playwright" in every and not any(r["name"] == "playwright test" for r in runners):
        runners.append({"name": "playwright (library)", "evidence": ["dependency playwright"]})
    files = [f for f in ix.files if TEST_FILE_RE.search(f.lower()) and not in_build(f)]
    dirs: dict[str, int] = {}
    for f in files:
        d = f.rsplit("/", 1)[0] if "/" in f else "."
        dirs[d] = dirs.get(d, 0) + 1
    return {"found": bool(runners or files), "runners": runners, "files": len(files),
            "dirs": [{"dir": d, "files": n} for d, n in sorted(dirs.items(), key=lambda kv: -kv[1])[:5]]}


def asset_facts(ix: Index, exts: tuple[str, ...], largest: int = 5) -> dict:
    files = [(f, ix.size(f)) for f in ix.files if f.lower().endswith(exts) and ix.is_asset(f)]
    formats: dict[str, dict] = {}
    dirs: dict[str, int] = {}
    for f, size in files:
        fmt = formats.setdefault(f.rsplit(".", 1)[-1].lower(), {"count": 0, "bytes": 0})
        fmt["count"] += 1
        fmt["bytes"] += size
        d = f.rsplit("/", 1)[0] if "/" in f else "."
        dirs[d] = dirs.get(d, 0) + 1
    return {"found": bool(files), "count": len(files), "bytes": sum(s for _, s in files), "formats": formats,
            "dirs": [{"dir": d, "files": n} for d, n in sorted(dirs.items(), key=lambda kv: -kv[1])[:5]],
            "largest": [{"file": f, "bytes": s} for f, s in sorted(files, key=lambda fs: -fs[1])[:largest]]}


FONT_HOSTS = re.compile(r"\b(fonts\.googleapis\.com|fonts\.gstatic\.com|use\.typekit\.net|fonts\.bunny\.net|rsms\.me)\b")


def font_facts(ix: Index) -> dict:
    out = asset_facts(ix, FONT_EXT)
    hosts = []
    for f in ix.files:
        if f.lower().endswith((".html", ".css")) and ix.is_game(f):
            for m in FONT_HOSTS.finditer(ix.text(f) or ""):
                if m.group(1) not in hosts:
                    hosts.append(m.group(1))
    out["external_hosts"] = hosts
    out["found"] = out["found"] or bool(hosts)
    return out


def pwa_facts(ix: Index, pkg: dict) -> dict:
    sw = {"found": False}
    files = [f for f in ix.find("sw.js", "service-worker.js", "serviceworker.js", "*/sw.js", "*/service-worker.js", "*/serviceworker.js")
             if not in_build(f) and not is_side(f)]
    if files:
        sw = {"found": True, "file": files[0]}
    for f in ix.game_sources():
        text = ix.text(f) or ""
        m = re.search(r"serviceWorker\s*\??\.\s*register\s*\(", text)
        if m:
            sw = {**sw, "found": True, "registered_at": f"{f}:{line_of(text, m.start())}"}
            break
    every = {**pkg.get("devDependencies", {}), **pkg.get("dependencies", {})}
    if "vite-plugin-pwa" in every:
        sw = {**sw, "found": True, "plugin": "vite-plugin-pwa"}
    manifest = {"found": False}
    files = [f for f in ix.find("manifest.json", "manifest.webmanifest", "site.webmanifest", "public/manifest.json",
                                "public/manifest.webmanifest", "public/site.webmanifest") if not in_build(f)]
    if files:
        manifest = {"found": True, "file": files[0]}
    else:
        for f in ix.files:
            if f.lower().endswith(".html") and not in_build(f) and not is_side(f):
                m = re.search(r"""<link[^>]+rel=["']?manifest["']?[^>]*>""", ix.text(f) or "", re.I)
                if m:
                    manifest = {"found": True, "linked_from": f}
                    break
    return {"service_worker": sw, "manifest": manifest}


DEPLOY_FILES = [("vercel", ("vercel.json",)), ("netlify", ("netlify.toml", "_redirects", "public/_redirects")),
                ("cloudflare", ("wrangler.toml", "wrangler.json", "wrangler.jsonc")), ("firebase", ("firebase.json",)),
                ("docker", ("dockerfile",)), ("itch.io butler", (".itch.toml",))]


def deploy_facts(ix: Index, pkg: dict) -> dict:
    configs = []
    for kind, names in DEPLOY_FILES:
        found = [f for f in ix.find(*names)]
        if found:
            configs.append({"kind": kind, "file": found[0]})
    for f in ix.find(".github/workflows/*.yml", ".github/workflows/*.yaml"):
        text = ix.text(f) or ""
        if re.search(r"deploy-pages|upload-pages-artifact|gh-pages|peaceiris/actions-gh-pages", text):
            configs.append({"kind": "github-pages", "file": f})
        elif re.search(r"\b(vercel|netlify|wrangler|firebase deploy|butler push)\b", text):
            configs.append({"kind": "ci deploy", "file": f})
    scripts = [k for k, v in pkg.get("scripts", {}).items() if isinstance(v, str) and
               (re.search(r"deploy|publish|release", k) or re.search(r"\b(vercel|netlify|gh-pages|wrangler|butler)\b", v))]
    tools = sorted({m for k in scripts for m in re.findall(r"\b(vercel|netlify|gh-pages|wrangler|butler|firebase)\b", pkg["scripts"][k])})
    return {"found": bool(configs or scripts), "configs": configs, "scripts": scripts, "tools": tools}


# --------------------------------------------------------------------------- bundle, git, tuning tables


def bundle_facts(root: Path, top: int = 5, gzip_cap: int = 60 << 20) -> dict:
    for name in BUILD_DIRS:
        d = root / name
        if not d.is_dir():
            continue
        files = []
        for dirpath, dirnames, filenames in os.walk(d):
            dirnames[:] = [x for x in dirnames if x not in SKIP_DIRS]
            for f in filenames:
                p = Path(dirpath) / f
                try:
                    files.append((p.relative_to(root).as_posix(), p.stat().st_size))
                except OSError:
                    pass
            if len(files) > MAX_ENTRIES:
                break
        if not any(f.lower().endswith((".html", ".js")) for f, _ in files):
            continue
        js = sorted((fs for fs in files if fs[0].lower().endswith((".js", ".mjs"))), key=lambda fs: -fs[1])
        css = [fs for fs in files if fs[0].lower().endswith(".css")]
        gz: dict[str, int] = {}
        hooks: dict[str, str] = {}
        engine_texts: dict[str, str] = {}
        budget = gzip_cap
        for f, size in js:
            if size > budget:
                break
            budget -= size
            try:
                data = (root / f).read_bytes()
            except OSError:
                continue
            gz[f] = len(gzip.compress(data, compresslevel=6, mtime=0))
            text = data.decode("utf-8", errors="replace")
            for m in HOOK_RE.finditer(text):
                if not LIB_GLOBALS.match(m.group(1)):
                    hooks.setdefault("window." + m.group(1), f)
            engine_texts[f] = text
        return {"found": True, "dir": name, "files": len(files), "bytes": sum(s for _, s in files),
                "js_bytes": sum(s for _, s in js), "js_gzip_bytes": sum(gz.values()) if len(gz) == len(js) else None,
                "css_bytes": sum(s for _, s in css),
                "html": sorted(f for f, _ in files if f.lower().endswith(".html") and f.count("/") == 1),
                "largest": [{"file": f, "bytes": s, "gzip_bytes": gz.get(f)} for f, s in js[:top]],
                "hooks": [{"name": n, "file": f} for n, f in sorted(hooks.items())],
                "engine": [{"key": k, "evidence": ev, **det} for k, _, ev, det in engines_in_text(engine_texts)]}
    return {"found": False}


def git_facts(root: Path) -> dict:
    if not (root / ".git").exists():
        return {"found": False}

    def git(*args):
        try:
            p = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, timeout=10,
                               env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"})
        except (OSError, subprocess.TimeoutExpired):
            return None
        return p.stdout.strip() if p.returncode == 0 and p.stdout.strip() else None

    head = git("rev-parse", "--short", "HEAD")
    if not head:
        return {"found": False}
    return {"found": True, "branch": git("rev-parse", "--abbrev-ref", "HEAD"), "head": head,
            "last_tag": git("describe", "--tags", "--abbrev=0")}


TUNING_NAME_RE = re.compile(r"ramp|balance|tiers?\b|waves?\b|tuning|econom|constants?\b|config|levels?\b|stats\b|upgrades?\b|"
                            r"progression|difficulty|curves?\b|tables?\b|prices?\b|costs?\b|loot|drops?\b|spawns?\b|enem(?:y|ies)|(?:^|[-_.])data\b")
TUNING_STRONG_RE = re.compile(r"ramp|balance|tiers?\b|waves?\b|tuning|econom|^data$")
NUMBER_RE = re.compile(r"(?<![\w$.#])\d+(?:\.\d+)?(?![\w$])")


def tuning_facts(ix: Index, top: int = 8, floor: int = 25) -> list[dict]:
    """Files that look like tuning tables: a telling name and many numeric literals. Candidates, not a verdict."""
    out = []
    for f in ix.files:
        low = f.lower()
        stem = low.rsplit("/", 1)[-1].rsplit(".", 1)[0]
        if not low.endswith(CODE_EXT + (".json",)) or not ix.is_game(f) or "/" not in f:
            continue
        if not TUNING_NAME_RE.search(stem) or re.search(r"(view|ui|art|css)$|package|tsconfig|\.config$", stem) or in_dirs(f, I18N_DIRS):
            continue
        text = ix.text(f)
        if not text or is_automation(text):
            continue
        n = len(NUMBER_RE.findall(text))
        if n >= floor:
            out.append({"file": f, "numbers": n, "lines": text.count("\n") + 1})
    strong = lambda t: bool(TUNING_STRONG_RE.search(t["file"].rsplit("/", 1)[-1].rsplit(".", 1)[0].lower()))
    return sorted(out, key=lambda t: (not strong(t), -t["numbers"]))[:top]


# --------------------------------------------------------------------------- a project folder


def entry_facts(ix: Index, hooks: list[dict]) -> list[dict]:
    entries = []
    html = [f for f in ix.files if f.lower().endswith(".html") and (f.count("/") == 0 or f.lower().startswith("public/"))]
    for f in html:
        text = ix.text(f, limit=4 << 20) or ""
        scripts = re.findall(r"""<script\b[^>]*\bsrc=["']([^"']+)["']""", text, re.I)
        modules = re.findall(r"""<script\b(?=[^>]*\btype=["']module["'])[^>]*\bsrc=["']([^"']+)["']""", text, re.I)
        e = {"file": f, "bytes": ix.size(f), "scripts": scripts, "modules": modules}
        starts = [r for s in scripts if not re.match(r"(?:https?:)?//", s)
                  for r in [resolve_import(set(ix.files), f, s if s.startswith(("/", ".")) else "./" + s)] if r]
        if starts:
            reach = reachable(ix, starts)
            e["source_files"] = len(reach)
            e["hooks"] = [h["name"] for h in hooks if h["file"] in reach or h["file"] == f]
        else:
            e["hooks"] = [h["name"] for h in hooks if h["file"] == f]
        entries.append(e)
    return entries


def dev_server(pkg: dict, bundler: dict) -> dict:
    for name in ("dev", "start", "serve", "preview"):
        cmd = pkg.get("scripts", {}).get(name)
        if isinstance(cmd, str):
            m = re.search(r"(?:--port|-p)[ =](\d{2,5})", cmd)
            port, source = (int(m.group(1)), f"scripts.{name}") if m else (None, None)
            if port is None and bundler.get("port"):
                port, source = bundler["port"], bundler["config"]
            if port is None and bundler.get("kind") == "vite" and re.search(r"\bvite\b", cmd) and name != "preview":
                port, source = 5173, "vite default"
            return {"found": True, "script": name, "port": port, "port_source": source}
    return {"found": False}


def fingerprint_dir(root: Path) -> dict:
    root = root.resolve()
    ix = Index(root)
    pkg = package_facts(root, ix)
    bundler = bundler_facts(root, ix, pkg)
    hits = detect(ix, pkg, bundler)
    key, score, ev, det = hits[0]
    label = ENGINES[key] + (" + Vite" if key == "threejs-vite" and det.get("vite") else "")
    hooks, auto_hooks = hook_facts(ix)
    entries = entry_facts(ix, hooks)
    analytics = analytics_facts(ix, pkg)
    tests = test_facts(ix, pkg)
    audio = asset_facts(ix, AUDIO_EXT)
    bundle = bundle_facts(root)
    tuning = tuning_facts(ix)
    dev = dev_server(pkg, bundler)
    report = dict(
        kind="dir", name=pkg.get("name") or root.name, version=pkg.get("version"), path=str(root),
        engine=dict(key=key, label=label, confidence=score, evidence=ev, **det),
        other_engine_signals=[dict(key=h[0], evidence=h[2]) for h in hits[1:4]],
        package={k: pkg.get(k) for k in ("found", "name", "version", "type", "scripts", "deps", "dependencies", "devDependencies")},
        lockfile=pkg["lockfile"], bundler=bundler, dev_server=dev, entries=entries,
        hooks=hooks, hooks_outside_game_code=auto_hooks[:10],
        analytics=analytics, saves=save_facts(ix), i18n=i18n_facts(ix, pkg), tests=tests,
        audio=audio, fonts=font_facts(ix), pwa=pwa_facts(ix, pkg), deploy=deploy_facts(ix, pkg),
        bundle=bundle, git=git_facts(root), tuning=tuning,
        files_indexed=len(ix.files), index_truncated=ix.truncated,
    )
    report["routes"] = dir_routes(report)
    return report


def dir_routes(r: dict) -> list[dict]:
    routes = []
    scripts = r["package"].get("scripts") or {}
    dev = r["dev_server"]
    game = next((h for h in r["hooks"] if h["name"] == "window.__game"), None) or (r["hooks"][0] if r["hooks"] else None)
    entry = next((e for e in r["entries"] if game and game["name"] in e.get("hooks", [])), None) or \
        next((e for e in r["entries"] if e["file"] == "index.html"), None) or (r["entries"][0] if r["entries"] else None)
    if entry:
        page = "" if entry["file"] == "index.html" else entry["file"].removeprefix("public/")
        url = f"http://127.0.0.1:{dev['port']}/{page}" if dev.get("port") else f"http://127.0.0.1:<port>/{page}"
        flags = f" --ready 'window.{game['name'].split('.', 1)[1]}'" if game and game["name"] in entry.get("hooks", []) else ""
        why = (f"`npm run {dev['script']}` first" if dev.get("found") else "serve the folder first") + \
            (f"; port from {dev['port_source']}" if dev.get("port") else "; port not found, read it from the server's output")
        routes.append({"do": f"wise qa {url}{flags}", "why": f"muted phone-sized browser, taps, console errors, overflow ({why})"})
    else:
        routes.append({"do": "wise qa <url>", "why": "no HTML entry point found in this folder; point it at the running game"})
    if game:
        members = f": {', '.join(game['members'][:8])}" if game.get("members") else ""
        routes.append({"do": f"read {game['file']}:{game['line']}", "why": f"debug hook {game['name']}{members}; use it in QA to "
                       "speed time or set up state, never to win"})
    if r["tuning"]:
        routes.append({"do": "read " + ", ".join(t["file"] for t in r["tuning"][:4]),
                       "why": "tuning tables seem to live here (telling file name + many numeric literals)"})
    if r["tests"]["found"] and "test" in scripts:
        routes.append({"do": "npm test", "why": f"{r['tests']['files']} test files" +
                       (f", {', '.join(x['name'] for x in r['tests']['runners'])}" if r["tests"]["runners"] else "")})
    if r["audio"]["found"]:
        d = r["audio"]["dirs"][0]["dir"]
        fmt = max(r["audio"]["formats"].items(), key=lambda kv: kv[1]["bytes"])[0]
        routes.append({"do": f"wise music-enhance {d}/*.{fmt} --check", "why": "loudness and true peak per file, measured, never played"})
    if not r["bundle"]["found"] and "build" in scripts:
        routes.append({"do": "npm run build, then wise scan again", "why": "no build output here yet, so bundle sizes are not measured"})
    if r["engine"]["key"] == "unknown":
        routes.append({"do": "point wise scan at the folder that holds the project file (package.json, project.godot, *.uproject, ProjectSettings/, Cargo.toml, CMakeLists.txt ...)",
                       "why": "no engine or build marker was found at the top of this folder"})
    return routes


# --------------------------------------------------------------------------- a URL


class Fetched(NamedTuple):
    url: str                 # after redirects
    status: int              # 0 when the request never got an answer
    headers: dict            # lower-cased names
    body: bytes              # decoded (gunzipped) bytes, possibly cut at the cap
    wire: int | None         # bytes on the wire, when known
    error: str | None = None


def http_fetch(url: str, method: str = "GET", max_bytes: int = MAX_URL_BYTES, timeout: float = 15.0) -> Fetched:
    """One request with urllib. The scanner takes any callable with this signature, so tests inject their own."""
    if urlsplit(url).scheme not in ("http", "https"):
        return Fetched(url, 0, {}, b"", None, "only http and https are fetched")
    req = urllib.request.Request(url, method=method, headers={"User-Agent": UA, "Accept": "*/*", "Accept-Encoding": "gzip"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            headers = {k.lower(): v for k, v in resp.headers.items()}
            raw = b"" if method == "HEAD" else resp.read(max_bytes + 1)
            status, final = resp.status, resp.geturl()
    except urllib.error.HTTPError as e:
        return Fetched(url, e.code, {k.lower(): v for k, v in (e.headers or {}).items()}, b"", None, f"HTTP {e.code}")
    except (urllib.error.URLError, OSError, ValueError) as e:
        return Fetched(url, 0, {}, b"", None, str(getattr(e, "reason", e)))
    wire = len(raw) if method != "HEAD" else (int(headers["content-length"]) if headers.get("content-length", "").isdigit() else None)
    body = raw
    if "gzip" in headers.get("content-encoding", "").lower() and raw:
        try:
            body = zlib.decompressobj(16 + zlib.MAX_WBITS).decompress(raw, max_bytes)
        except zlib.error:
            pass
    return Fetched(final, status, headers, body, wire)


class _Page(HTMLParser):
    """Scripts, styles, preloads and inline code of one HTML page."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.assets: list[dict] = []
        self.inline: list[str] = []
        self.base = None
        self.manifest = None
        self.viewport = None
        self.title = None
        self._in = None

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "script":
            if a.get("src"):
                self.assets.append({"ref": a["src"], "kind": "module script" if a.get("type") == "module" else "script"})
            elif a.get("type", "") in ("", "module", "text/javascript", "importmap"):
                self._in = "script"
        elif tag == "link" and a.get("href"):
            rel = a.get("rel", "").lower().split()
            if "stylesheet" in rel:
                self.assets.append({"ref": a["href"], "kind": "style"})
            elif "modulepreload" in rel:
                self.assets.append({"ref": a["href"], "kind": "modulepreload"})
            elif "preload" in rel:
                self.assets.append({"ref": a["href"], "kind": "preload " + (a.get("as") or "?")})
            elif "manifest" in rel:
                self.manifest = a["href"]
        elif tag == "base" and a.get("href"):
            self.base = a["href"]
        elif tag == "meta" and a.get("name", "").lower() == "viewport":
            self.viewport = a.get("content")
        elif tag == "title":
            self._in = "title"

    def handle_endtag(self, tag):
        if tag in ("script", "title"):
            self._in = None

    def handle_data(self, data):
        if self._in == "script" and data.strip():
            self.inline.append(data)
        elif self._in == "title" and self.title is None:
            self.title = data.strip()


# bundles import .js chunks; a dev server also serves .ts/.tsx/.jsx modules under their source names
JS_IMPORT_RE = re.compile(r"""(?:\bfrom|\bimport)\s*\(?\s*["'`]((?:\.{0,2}/)[^"'`\s]+?\.(?:m?js|tsx?|jsx)(?:\?[^"'`\s]*)?)["'`]""")
MAPDEPS_RE = re.compile(r"__vite__mapDeps[^\[]{0,200}\[([^\]]{0,20000})\]")
HASHED_RE = re.compile(r"[-.][A-Za-z0-9_-]{8,}\.(?:m?js|css|woff2?|png|jpe?g|webp|mp3|ogg)$")


def _long_cache(cc: str | None) -> bool:
    if not cc:
        return False
    m = re.search(r"max-age=(\d+)", cc)
    return "immutable" in cc or bool(m and int(m.group(1)) >= 30 * 86400)


def fingerprint_url(url: str, fetch: Callable[..., Fetched] | None = None,
                    max_requests: int = MAX_URL_REQUESTS, max_bytes: int = MAX_URL_BYTES) -> dict:
    fetch = fetch or http_fetch
    used = {"requests": 1, "bytes": 0}
    page = fetch(url, "GET", max_bytes)
    if page.error or page.status >= 400 or page.status == 0:
        raise ScanError(f"could not fetch {url}: {page.error or 'HTTP ' + str(page.status)}")
    used["bytes"] += page.wire or len(page.body)
    html = page.body.decode("utf-8", errors="replace")
    doc = _Page()
    doc.feed(html)
    base = urljoin(page.url, doc.base) if doc.base else page.url
    origin = "{0.scheme}://{0.netloc}".format(urlsplit(page.url))

    def show(u: str) -> str:
        return u[len(origin):] if u.startswith(origin + "/") else u

    queue = [{"url": urljoin(base, a["ref"]), "kind": a["kind"], "via": "html"} for a in doc.assets]
    seen, assets, texts, skipped = set(), [], {}, 0
    texts["inline script"] = "\n".join(doc.inline)
    texts["html"] = html
    while queue:
        item = queue.pop(0)
        u = item["url"].split("#")[0]
        if u in seen or urlsplit(u).scheme not in ("http", "https"):
            continue
        seen.add(u)
        if used["requests"] >= max_requests or used["bytes"] >= max_bytes:
            skipped += 1
            continue
        is_js = item["kind"] in ("script", "module script", "modulepreload", "preload script")
        want_body = is_js or item["kind"] == "style"
        used["requests"] += 1
        got = fetch(u, "GET" if want_body else "HEAD", max(1, max_bytes - used["bytes"]))
        used["bytes"] += (got.wire or len(got.body)) if want_body else 0
        path = urlsplit(u).path
        rec = {"url": u, "path": show(u), "kind": item["kind"], "via": item["via"], "status": got.status,
               "bytes": len(got.body) if want_body and not got.error else None, "transfer_bytes": got.wire,
               "content_encoding": got.headers.get("content-encoding"), "cache_control": got.headers.get("cache-control"),
               "hashed_name": bool(HASHED_RE.search(path))}
        if got.error:
            rec["error"] = got.error
        assets.append(rec)
        if not is_js or got.error or not got.body:
            continue
        text = got.body.decode("utf-8", errors="replace")
        texts[show(u)] = text
        name = path.rsplit("/", 1)[-1]
        refs = [m.group(1) for m in JS_IMPORT_RE.finditer(text)]
        for m in MAPDEPS_RE.finditer(text):     # Vite's preload list: the chunks and styles a dynamic import needs
            refs += re.findall(r"""["']([^"']+\.(?:m?js|css))["']""", m.group(1))
        for ref in dict.fromkeys(refs):
            target = urljoin(u, ref) if ref.startswith((".", "/")) else urljoin(base, ref)
            if target.split("#")[0] not in seen:
                queue.append({"url": target, "kind": "style" if ref.endswith(".css") else "script", "via": f"import in {name}"})

    scripts = {k: v for k, v in texts.items() if k != "html"}
    hits = engines_in_text(scripts) or engines_in_text({"html": html})
    vite = next((n for n, t in texts.items() if VITE_MARKERS.search(t)), None)
    if hits:
        key, score, ev, det = hits[0]
    else:
        m2d = next(((n, m) for n, t in scripts.items() for m in [CANVAS_2D.search(t)] if m), None)
        key, score, ev, det = ("canvas-2d", 60, [f"getContext(\"2d\") in {m2d[0]}", "no engine library found in the fetched scripts"], {}) \
            if m2d else ("unknown", 10, ["no known engine signature in the fetched scripts"], {})
    if key == "threejs-vite":
        det = {**det, "vite": bool(vite)}
        ev = ev + [f"vite markers: found in {vite}" if vite else "vite markers: not found"]
    label = ENGINES[key] + (" + Vite" if key == "threejs-vite" and vite else "")

    hooks, lib_globals = {}, {}
    endpoints, sdks = {}, {}
    sw = None
    for name, text in scripts.items():
        for m in HOOK_RE.finditer(text):
            (lib_globals if LIB_GLOBALS.match(m.group(1)) else hooks).setdefault("window." + m.group(1), name)
        analytics_in_text(name, text, endpoints, sdks)
        if sw is None and re.search(r"serviceWorker\s*\??\.\s*register\s*\(", text):
            sw = name
    for e in list(endpoints.values()) + list(sdks.values()):
        e.pop("line", None)      # a line number in a minified bundle says nothing

    hashed = [a for a in assets if a["hashed_name"] and not a.get("error")]
    encodings: dict[str, int] = {}
    for a in assets:
        if not a.get("error"):
            enc = a["content_encoding"] or "none"
            encodings[enc] = encodings.get(enc, 0) + 1
    js = [a for a in assets if a["bytes"] is not None and a["kind"] != "style"]
    report = dict(
        kind="url", url=page.url, requested_url=url, title=doc.title, status=page.status,
        engine=dict(key=key, label=label, confidence=score, evidence=ev, **det),
        other_engine_signals=[dict(key=h[0], evidence=h[2]) for h in hits[1:4]],
        html=dict(bytes=len(page.body), transfer_bytes=page.wire, cache_control=page.headers.get("cache-control"),
                  content_encoding=page.headers.get("content-encoding"), content_type=page.headers.get("content-type"),
                  viewport=doc.viewport, inline_scripts=len(doc.inline), manifest=doc.manifest),
        assets=assets,
        totals=dict(requests=used["requests"], transfer_bytes=(page.wire or len(page.body)) + sum(a["transfer_bytes"] or 0 for a in assets),
                    js_bytes=sum(a["bytes"] for a in js), js_files=len(js),
                    skipped=skipped, truncated=bool(skipped), limits=dict(requests=max_requests, bytes=max_bytes)),
        headers=dict(html_cache_control=page.headers.get("cache-control"), html_content_encoding=page.headers.get("content-encoding"),
                     hashed_assets=len(hashed), hashed_assets_long_cache=sum(_long_cache(a["cache_control"]) for a in hashed),
                     asset_encodings=encodings),
        hooks=[{"name": n, "file": f} for n, f in sorted(hooks.items(), key=lambda kv: (kv[0] != "window.__game", kv[0]))],
        library_globals=sorted(lib_globals),
        analytics={"found": bool(endpoints or sdks), "endpoints": list(endpoints.values()), "sdks": list(sdks.values())},
        pwa={"service_worker": {"found": bool(sw), **({"registered_in": sw} if sw else {})},
             "manifest": {"found": bool(doc.manifest), **({"href": doc.manifest} if doc.manifest else {})}},
    )
    routes = []
    game = next((h for h in report["hooks"] if h["name"] == "window.__game"), None)
    routes.append({"do": f"wise qa {page.url}" + (" --ready 'window.__game'" if game else ""),
                   "why": "muted phone-sized browser, taps, console errors, overflow"})
    if report["hooks"]:
        routes.append({"do": "use " + ", ".join(h["name"] for h in report["hooks"][:4]) + " from the page",
                       "why": "debug hooks ship in this build; speed time or set up state with them, never win with them"})
    if skipped:
        routes.append({"do": "scan the project folder for the full picture", "why": f"{skipped} asset(s) were not fetched (limit reached)"})
    report["routes"] = routes
    return report


# --------------------------------------------------------------------------- entry points


def fingerprint(target: str, sheet: str | None = None, scene: float | None = None) -> dict:
    """Facts about a game project folder, a web game's URL, a video file or a folder of videos.

    Raises ScanError when the target can't be read."""
    from wisecraft import clip, engines
    if re.match(r"https?://", target, re.I):
        return fingerprint_url(target)
    p = Path(target).expanduser()
    scene = clip.SCENE if scene is None else scene
    if p.is_file():
        if clip.is_video(p):
            return _clip(lambda: clip.fingerprint(p, sheet, scene))
        if p.suffix.lower() in AUDIO_EXT:
            raise ScanError(f"{target} is an audio file: measure or fix it with `wise music-enhance {p.name} --check`")
        raise ScanError(f"{target} is a file; pass the project folder, the URL of the running game, or a video (mp4, mov, webm, mkv)")
    if not p.is_dir():
        raise ScanError(f"no such folder or file: {target} (pass a project folder, an http(s) URL, or a video)")
    if engines.looks_native(p):
        r = engines.fingerprint(p)
        if r:
            return r
    low = {c.name.lower() for c in p.iterdir()}
    webby = "package.json" in low or any(n.endswith((".html", ".js", ".ts")) for n in low)
    if not webby and clip.videos_in(p):
        return _clip(lambda: clip.fingerprint_folder(p, sheet, scene))
    return fingerprint_dir(p)


def _clip(work):
    from wisecraft import clip
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise ScanError("scanning a video needs ffmpeg and ffprobe on PATH: brew install ffmpeg / apt install ffmpeg / winget install ffmpeg")
    try:
        return work()
    except clip.ClipError as e:
        raise ScanError(str(e)) from None


NOT_FOUND = "not found"


def _where(d: dict) -> str:
    return f"{d['file']}:{d['line']}" if d.get("line") else str(d.get("file", ""))


def format_dir(r: dict) -> str:
    e, pk = r["engine"], r["package"]
    lines = [f"{r['name']}" + (f" {r['version']}" if r.get("version") else "") + "  (project folder)",
             f"  path:       {r['path']}",
             f"  engine:     {e['label']}  [{e['key']}, {e['confidence']}%]" + (f"  version {e['version']}" if e.get("version") else ""),
             f"              evidence: {'; '.join(map(str, e['evidence']))}"]
    if r["other_engine_signals"]:
        lines.append("  also:       " + "; ".join(f"{o['key']} ({o['evidence'][0]})" for o in r["other_engine_signals"]))
    if pk["found"]:
        deps = ", ".join(f"{n} {d['declared']}" + (f" (resolved {d['resolved']})" if d["resolved"] and d["resolved"] != d["declared"] else "")
                         for n, d in pk["deps"].items())
        lines.append(f"  stack:      {deps or 'none of the known libraries'}  "
                     f"[{len(pk['dependencies'])} dependencies, {len(pk['devDependencies'])} dev]")
        lock = r["lockfile"]
        lines.append(f"  package:    package.json found; lockfile: {lock['file'] + ' (' + lock['kind'] + ')' if lock['found'] else NOT_FOUND}")
        for k, v in list(pk["scripts"].items())[:12]:
            lines.append(f"    {k}: {v}")
    else:
        lines.append(f"  package:    package.json {NOT_FOUND}")
    b = r["bundler"]
    lines.append("  bundler:    " + (f"{b['kind']}" + (f" ({b['config']})" if b.get("config") else " (dependency only, no config file)") +
                                     (f", inputs: {', '.join(b['inputs'])}" if b.get("inputs") else "") if b["found"] else NOT_FOUND))
    if r["entries"]:
        lines.append("  entries:    " + "\n              ".join(
            f"{x['file']} ({human(x['bytes'])})" + (f" -> {', '.join(x['modules'] or x['scripts'][:3])}" if x["scripts"] else " (no script src)") +
            (f"  reaches {', '.join(x['hooks'])}" if x.get("hooks") else "") for x in r["entries"][:8]))
    else:
        lines.append(f"  entries:    HTML entry points {NOT_FOUND}")
    if r["hooks"]:
        lines.append("  hooks:      " + "\n              ".join(
            f"{h['name']}  {_where(h)}" + (f"  members: {', '.join(h['members'][:14])}" + (" ..." if len(h["members"]) > 14 or h.get("members_truncated") else "")
                                           if h.get("members") else "") for h in r["hooks"][:8]))
    else:
        lines.append(f"  hooks:      window.__* assignments {NOT_FOUND} in game code")
    if r["hooks_outside_game_code"]:
        lines.append("              only outside game code (tests, capture scripts, tools): " + ", ".join(f"{h['name']} ({_where(h)})" for h in r["hooks_outside_game_code"][:5]))
    a = r["analytics"]
    lines.append("  analytics:  endpoints: " + ("; ".join(f"{x.get('host', '')}{x['path']} ({_where(x)}, {x['via']})" for x in a["endpoints"][:6]) or NOT_FOUND))
    lines.append("              SDKs: " + ("; ".join(f"{s['name']}" + (f" [{', '.join(s['hosts'])}]" if s["hosts"] else "") + f" ({_where(s)})" for s in a["sdks"]) or NOT_FOUND))
    s = r["saves"]
    if s["found"]:
        if s["local_storage"]:
            lines.append("  saves:      localStorage: " + "; ".join(f"{k['key']!r} ({_where(k)})" for k in s["local_storage"][:8]))
        if s["key_constants"]:
            lines.append("              key constants: " + "; ".join(f"{k['constant']} = {k['value']!r} ({_where(k)})" for k in s["key_constants"][:6]))
        if s["session_storage"]:
            lines.append("              sessionStorage: " + "; ".join(f"{k['key']!r}" for k in s["session_storage"][:8]))
        if s["indexed_db"]:
            lines.append("              IndexedDB: " + "; ".join(f"{d['name']!r} v{d['version']} ({_where(d)})" for d in s["indexed_db"][:4]))
        if s["dynamic_keys"]:
            lines.append(f"              {s['dynamic_keys']} storage call(s) build their key at run time (not resolved)")
        lines.append("              version/schema: " + ("; ".join(f"{v['name']} = {v['value']} ({_where(v)})" for v in s["versions"][:6]) or NOT_FOUND))
    else:
        lines.append(f"  saves:      localStorage / IndexedDB use {NOT_FOUND}")
    i = r["i18n"]
    lines.append("  i18n:       " + (f"{', '.join(i['languages']) or 'languages not listed'}" + (f"  ({', '.join(i['evidence'][:3])})" if i["evidence"] else "") +
                                     (f"  libraries: {', '.join(i['libraries'])}" if i["libraries"] else "") if i["found"] else NOT_FOUND))
    t = r["tests"]
    lines.append("  tests:      " + (f"{', '.join(x['name'] for x in t['runners']) or 'runner ' + NOT_FOUND}; {t['files']} test file(s)" +
                                     (f" in {', '.join(d['dir'] for d in t['dirs'][:3])}" if t["dirs"] else "") if t["found"] else NOT_FOUND))
    for label, key in (("audio", "audio"), ("fonts", "fonts")):
        x = r[key]
        if x["count"]:
            fm = ", ".join(f"{k} {v['count']} / {human(v['bytes'])}" for k, v in sorted(x["formats"].items(), key=lambda kv: -kv[1]["bytes"]))
            lines.append(f"  {label + ':':<11} {x['count']} file(s), {human(x['bytes'])}  ({fm})  in {', '.join(d['dir'] for d in x['dirs'][:3])}")
            lines.append("              largest: " + ", ".join(f"{f['file'].rsplit('/', 1)[-1]} {human(f['bytes'])}" for f in x["largest"]))
        else:
            lines.append(f"  {label + ':':<11} files {NOT_FOUND}")
        if key == "fonts" and x["external_hosts"]:
            lines.append("              external: " + ", ".join(x["external_hosts"]))
    p = r["pwa"]
    sw, mf = p["service_worker"], p["manifest"]
    lines.append("  pwa:        service worker: " + ((sw.get("file") or sw.get("registered_at") or sw.get("plugin")) if sw["found"] else NOT_FOUND) +
                 "; manifest: " + ((mf.get("file") or "linked from " + mf.get("linked_from", "?")) if mf["found"] else NOT_FOUND))
    d = r["deploy"]
    lines.append("  deploy:     " + ("; ".join([f"{c['kind']} ({c['file']})" for c in d["configs"]] +
                                               ([f"scripts: {', '.join(d['scripts'])}" + (f" [{', '.join(d['tools'])}]" if d["tools"] else "")] if d["scripts"] else []))
                                     if d["found"] else NOT_FOUND))
    bd = r["bundle"]
    if bd["found"]:
        gz = f", {human(bd['js_gzip_bytes'])} gzip" if bd.get("js_gzip_bytes") is not None else ""
        lines.append(f"  bundle:     {bd['dir']}/  {human(bd['bytes'])} total in {bd['files']} files; JS {human(bd['js_bytes'])}{gz}; CSS {human(bd['css_bytes'])}")
        lines.append("              largest: " + ", ".join(f"{c['file'].rsplit('/', 1)[-1]} {human(c['bytes'])}" +
                                                             (f" ({human(c['gzip_bytes'])} gzip)" if c.get("gzip_bytes") is not None else "") for c in bd["largest"]))
        if bd["hooks"]:
            lines.append("              hooks in the build: " + ", ".join(h["name"] for h in bd["hooks"][:6]))
        for en in bd["engine"][:1]:
            lines.append(f"              engine in the build: {en['key']}" + (f" {en['version']}" if en.get("version") else "") + f" ({en['evidence'][0]})")
    else:
        lines.append(f"  bundle:     build output {NOT_FOUND} (looked for {', '.join(x + '/' for x in BUILD_DIRS)})")
    g = r["git"]
    lines.append("  git:        " + (f"branch {g['branch'] or NOT_FOUND}, head {g['head']}, last tag {g['last_tag'] or NOT_FOUND}" if g["found"] else NOT_FOUND))
    lines.append("  tuning:     " + (", ".join(f"{t['file']} ({t['numbers']} numbers)" for t in r["tuning"]) or f"candidates {NOT_FOUND}"))
    lines.append("  routes:")
    for n, rt in enumerate(r["routes"], 1):
        lines.append(f"    {n}. {rt['do']}  ({rt['why']})")
    if r.get("index_truncated"):
        lines.append("  note:       file index truncated (huge folder); pass a subfolder for detail")
    return "\n".join(lines)


def format_url(r: dict) -> str:
    e, h, t = r["engine"], r["html"], r["totals"]
    lines = [f"{r['title'] or '(no title)'}  (URL)",
             f"  url:        {r['url']}  [HTTP {r['status']}]",
             f"  engine:     {e['label']}  [{e['key']}, {e['confidence']}%]" + (f"  version {e['version']}" if e.get("version") else "  version " + NOT_FOUND),
             f"              evidence: {'; '.join(map(str, e['evidence']))}",
             f"  html:       {human(h['bytes'])}; cache-control: {h['cache_control'] or NOT_FOUND}; content-encoding: {h['content_encoding'] or NOT_FOUND}; "
             f"viewport meta: {'found' if h['viewport'] else NOT_FOUND}; {h['inline_scripts']} inline script(s)",
             f"  transfer:   {human(t['transfer_bytes'])} in {t['requests']} request(s); JS {human(t['js_bytes'])} decoded in {t['js_files']} file(s)" +
             (f"; {t['skipped']} asset(s) NOT fetched (limit {t['limits']['requests']} requests / {human(t['limits']['bytes'])})" if t["skipped"] else "")]
    hd = r["headers"]
    lines.append(f"  caching:    hashed assets with a long or immutable cache: {hd['hashed_assets_long_cache']} of {hd['hashed_assets']}; "
                 f"asset encodings: {', '.join(f'{k} x{v}' for k, v in hd['asset_encodings'].items()) or NOT_FOUND}")
    lines.append("  assets:")
    for a in sorted(r["assets"], key=lambda a: -(a["transfer_bytes"] or 0))[:14]:
        size = a.get("error") or (human(a["bytes"]) if a["bytes"] is not None else human(a["transfer_bytes"]))
        lines.append(f"    {a['path']}  {size}  [{a['kind']}, {a['via']}]" + (f"  cache-control: {a['cache_control']}" if a["cache_control"] else ""))
    if len(r["assets"]) > 14:
        lines.append(f"    ... and {len(r['assets']) - 14} more (see --json)")
    lines.append("  hooks:      " + (", ".join(f"{x['name']} ({x['file']})" for x in r["hooks"][:8]) or f"window.__* assignments {NOT_FOUND} in the fetched scripts"))
    a = r["analytics"]
    lines.append("  analytics:  endpoints: " + ("; ".join(f"{x.get('host', '')}{x['path']} ({x['file']})" for x in a["endpoints"][:6]) or NOT_FOUND))
    lines.append("              SDKs: " + ("; ".join(s["name"] + (f" [{', '.join(s['hosts'])}]" if s["hosts"] else "") for s in a["sdks"]) or NOT_FOUND))
    p = r["pwa"]
    lines.append("  pwa:        service worker: " + (p["service_worker"].get("registered_in", "") if p["service_worker"]["found"] else NOT_FOUND) +
                 "; manifest: " + (p["manifest"].get("href", "") if p["manifest"]["found"] else NOT_FOUND))
    lines.append("  routes:")
    for n, rt in enumerate(r["routes"], 1):
        lines.append(f"    {n}. {rt['do']}  ({rt['why']})")
    return "\n".join(lines)


def format_report(r: dict) -> str:
    from wisecraft import clip, engines
    return {"url": format_url, "dir": format_dir, "project": engines.format_project, "video": clip.format_video,
            "videos": clip.format_folder}[r["kind"]](r)


def main(a):
    try:
        r = fingerprint(a.target, a.sheet, a.scene)
    except ScanError as e:
        # 1: something that should be readable was not (a URL, a video file); 2: a wrong argument
        p = Path(a.target).expanduser()
        unreadable = re.match(r"https?://", a.target, re.I) or (p.is_file() and p.suffix.lower() in (".mp4", ".mov", ".webm", ".mkv", ".m4v", ".avi"))
        die(str(e), 1 if unreadable else 2)
    print(json.dumps(r, indent=2) if a.json else format_report(r))


def register(sub):
    import argparse
    p = sub.add_parser("scan", help="fingerprint any game project, a web game's URL, or any video clip: engine, versions, entries, targets, assets",
                       description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("target", help="a project folder, the http(s) URL of a running or deployed web game, a video file, or a folder of videos")
    p.add_argument("--json", action="store_true", help="print the report as JSON")
    p.add_argument("--sheet", nargs="?", const="", metavar="PNG", help="for a video: also write a contact sheet (default <name>.sheet.png next to it; a folder for several)")
    p.add_argument("--scene", type=float, metavar="0..1", help="for a video: how different two frames must be to count as a cut (default 0.3)")
    p.set_defaults(func=main)
