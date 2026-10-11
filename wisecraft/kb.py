# Ported from Universal Modder (https://github.com/rehan-remade/universal-modder), um/kb.py.
# Copyright (c) 2026 Rehan and universal-modder contributors. MIT License; see LICENSE and NOTICE.
"""The knowledge base: field notes on how web games were actually built, tuned and shipped, written by agents for agents.

    wise kb search "boss slam hit stop"            # prior art before you start (local repo, or synced from GitHub)
    wise kb search wave pacing --route data-tuning # filter by game / engine / route
    wise kb show techniques/player-model-bots.md
    wise kb new --game "Horde tower defense (mobile web)" --title "A boss that slams the wall" --from-scan ./my-game
    wise kb add --kind technique --title "Measure the mix without playing it"    # `add` is the same as `new`
    wise kb check knowledge/games/horde-tower-defense-mobile-web/a-boss-that-slams-the-wall.md   # validate before a PR
    wise kb index                                  # regenerate knowledge/INDEX.md + index.json
    wise kb sync                                   # refresh the cached copy from GitHub
    wise kb pr knowledge/techniques/measure-the-mix-without-playing-it.md --yes   # branch, commit, push to your fork, open a PR

Every note is Markdown with YAML front matter (knowledge/TEMPLATE.md). `check` enforces the schema, the
required sections, no secrets, no private preview or deploy URLs, no names from the denylist (.wise-denylist,
see `wise publish check --help`), no huge files. The base is public: describe the game neutrally ("a horde
tower defense for mobile web"), never by a company or unreleased product name. Contributions go through pull
requests: that's how one agent's hard-won gotchas reach the next one. Ask your human before `wise kb pr --yes`.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from wisecraft.common import ROOT, data_dir, die

REPO = os.environ.get("WISE_KB_REPO", "Wiserax/wisecraft")
BRANCH = os.environ.get("WISE_KB_BRANCH", "main")
AGENT = "wisecraft"    # User-Agent for the GitHub API and raw files
ROUTES = ["design", "data-tuning", "engine-code", "ui", "audio", "performance", "tooling", "release", "process", "other"]
STATUSES = ["idea", "in-progress", "working", "released", "abandoned"]
PLATFORMS = ["web-mobile", "web-desktop", "pwa", "webview", "other"]
# engine is free text; these are the keys `wise scan` prints, so notes that use them group together
ENGINES = ["threejs-vite", "phaser", "pixi", "babylon", "playcanvas", "unity-webgl", "godot-web", "construct", "canvas-2d"]
GAME_KEYS = ["kind", "title", "game", "engine", "route", "status", "date", "agents"]
TECH_KEYS = ["kind", "title", "tags", "date", "agents"]
LIST_KEYS = ["games_also", "tools", "agents", "humans", "links", "tags"]
GAME_SECTIONS = ["setup", "route", "verification", "gotchas"]
TEMPLATE_TITLE = "A boss that walks in and slams the wall in a horde tower defense"
MAX_BLOCK_WARN, MAX_BLOCK_FAIL = 60, 150
MAX_NOTE_KB, MAX_MEDIA_MB = 120, 1.5
# Notes and the index are UTF-8 with \n line ends on every OS. Without this, Windows reads and writes them in its
# ANSI code page with \r\n: the index's "·" separators come out as invalid UTF-8 and `wise kb check --index` fails.
TEXT = {"encoding": "utf-8", "newline": "\n"}


# --------------------------------------------------------------------------- where the notes are

def local_root() -> Path | None:
    """knowledge/ of the repo this package runs from (clone, plugin, editable install), or of the cwd's repo."""
    here = ROOT / "knowledge"
    if (here / "TEMPLATE.md").exists():
        return here
    for d in [Path.cwd(), *Path.cwd().parents]:
        if (d / "knowledge" / "TEMPLATE.md").exists():
            return d / "knowledge"
    return None


def cache_root() -> Path:
    return data_dir() / "kb" / REPO.replace("/", "__") / "knowledge"


def sync(quiet: bool = False) -> Path:
    """Mirror knowledge/ from GitHub into the cache (git tree API + raw files; no auth needed)."""
    api = f"https://api.github.com/repos/{REPO}/git/trees/{BRANCH}?recursive=1"
    req = urllib.request.Request(api, headers={"User-Agent": AGENT, "Accept": "application/vnd.github+json"})
    tree = json.load(urllib.request.urlopen(req, timeout=60))
    paths = [t["path"] for t in tree.get("tree", []) if t["type"] == "blob" and t["path"].startswith("knowledge/")
             and t["path"].endswith((".md", ".json"))]
    root = cache_root()
    tmp = root.with_name("knowledge.tmp")
    shutil.rmtree(tmp, ignore_errors=True)
    for p in paths:
        dst = tmp / p[len("knowledge/"):]
        dst.parent.mkdir(parents=True, exist_ok=True)
        url = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{p}"
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": AGENT}), timeout=60) as r:
            dst.write_bytes(r.read())
    tmp.mkdir(parents=True, exist_ok=True)   # a repo with no notes yet still syncs to an empty folder
    shutil.rmtree(root, ignore_errors=True)
    tmp.rename(root)
    (root / ".synced").write_text(str(time.time()), **TEXT)
    if not quiet:
        print(f"synced {len(paths)} files from github.com/{REPO} -> {root}")
    return root


def resolve_root(explicit: str | None = None, remote: bool = False) -> Path:
    if explicit:
        return Path(explicit)
    if os.environ.get("WISE_KB"):
        return Path(os.environ["WISE_KB"])
    loc = None if remote else local_root()
    if loc:
        return loc
    root = cache_root()
    stamp = root / ".synced"
    stale = not stamp.exists() or time.time() - float(stamp.read_text(encoding="utf-8") or 0) > 86400
    if stale:
        try:
            return sync(quiet=True)
        except OSError as e:
            if not root.exists():
                die(f"no local knowledge/ and GitHub sync failed ({e}); clone https://github.com/{REPO}")
    return root


# --------------------------------------------------------------------------- notes

def parse(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.S)
    if not m:
        return {}, text
    import yaml
    try:
        meta = yaml.safe_load(m.group(1)) or {}
    except (yaml.YAMLError, ValueError) as e:  # ValueError: a date YAML can't build, e.g. 2026-09-31
        return {"_yaml_error": str(e)}, m.group(2)
    return (meta if isinstance(meta, dict) else {}), m.group(2)


def notes(root: Path) -> list[tuple[Path, dict, str]]:
    out = []
    for p in sorted(root.rglob("*.md")):
        rel = p.relative_to(root).as_posix()
        if rel in ("README.md", "INDEX.md", "TEMPLATE.md"):
            continue
        meta, body = parse(p)
        out.append((p, meta, body))
    return out


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:60] or "note"


def strs(v) -> list[str]:
    """A list field as text, whatever YAML made of it: an unquoted `[Vite 7: dev server]` is a dict,
    `[2048]` an int, a bare `tools: Playwright` a string."""
    if v is None or v == "":
        return []
    return [str(x) for x in (v if isinstance(v, list) else [v])]


# --------------------------------------------------------------------------- search

def _term(t: str) -> re.Pattern:
    """A search term that must start a word: "rust" finds "Rust" and "rusty", not "trust" or "frustum".
    A term that starts with punctuation (".glb", ".io") still matches anywhere, so it finds "boss.glb"."""
    return re.compile((r"(?<![a-z0-9])" if t[:1].isalnum() else "") + re.escape(t))


def search(root: Path, terms: list[str], game=None, engine=None, route=None, limit=10) -> list[dict]:
    terms = [_term(t.lower()) for t in terms if t.strip()]
    res = []
    for p, meta, body in notes(root):
        if game and slug(game) not in slug(str(meta.get("game", ""))) + " " + " ".join(slug(g) for g in strs(meta.get("games_also"))):
            continue
        if engine and str(meta.get("engine", "")).lower() != engine.lower():
            continue
        if route and str(meta.get("route", "")).lower() != route.lower():
            continue
        fields = {
            5: str(meta.get("title", "")),
            4: " ".join([str(meta.get("game", ""))] + strs(meta.get("games_also"))),
            3: " ".join(str(x) for x in [meta.get("engine", ""), meta.get("route", ""), *strs(meta.get("tags")), *strs(meta.get("tools"))]),
        }
        low = body.lower()
        score = 0
        for t in terms:
            score += sum(w for w, f in fields.items() if t.search(f.lower()))
            score += min(5, len(t.findall(low)))
        if terms and score == 0:
            continue
        hits = [ln.strip() for ln in body.splitlines() if ln.strip() and any(t.search(ln.lower()) for t in terms)][:3]
        res.append(dict(score=score, path=p.relative_to(root).as_posix(), title=meta.get("title"), game=meta.get("game"),
                        engine=meta.get("engine"), route=meta.get("route"), status=meta.get("status"), hits=hits))
    res.sort(key=lambda r: -r["score"])
    return res[:limit]


# --------------------------------------------------------------------------- check

def engine_keys() -> list[str]:
    """The engine keys `wise scan` knows right now; the list above when scan cannot be imported."""
    try:
        from wisecraft.scan import ENGINES as known
        return [k for k in known if k != "unknown"] or ENGINES
    except Exception:
        return ENGINES


def deny_terms(path: Path, root: Path | None = None, deny: str | None = None) -> list[str]:
    """Names a public note must not contain: --deny FILE, else the .wise-denylist of the repo that holds the note
    (the folder above knowledge/, or the nearest folder above the note that has one), else $WISE_DENY."""
    from wisecraft.publish import DENY_FILE, load_denylist
    if deny:
        return load_denylist(None, deny)[0]
    for d in ([root.resolve().parent] if root else []) + list(path.resolve().parents):
        if (d / DENY_FILE).is_file():
            return load_denylist(d)[0]
    return load_denylist(None)[0]


def check_note(path: Path, root: Path | None = None, deny: str | None = None) -> tuple[list[str], list[str]]:
    from wisecraft.publish import PRIVATE_URL_PATTERNS, SECRET_PATTERNS, USER_PATH, deny_hits, match_lines, where
    fails, warns = [], []
    text = path.read_text(encoding="utf-8", errors="replace")
    meta, body = parse(path)
    if not meta:
        return [f"{path}: no YAML front matter (start the file with --- ... --- ; see knowledge/TEMPLATE.md)"], []
    if "_yaml_error" in meta:
        return [f"{path}: front matter is not valid YAML: {meta['_yaml_error']}"], []
    kind = meta.get("kind", "game")
    for k in GAME_KEYS if kind == "game" else TECH_KEYS:
        if meta.get(k) in (None, "", []):
            fails.append(f"missing front-matter key: {k}")
    if kind not in ("game", "technique"):
        fails.append(f"kind must be game or technique, not {kind!r}")
    if kind == "game":
        if meta.get("route") and meta["route"] not in ROUTES:
            fails.append(f"route {meta['route']!r} not one of: {', '.join(ROUTES)}")
        if meta.get("platform") and meta["platform"] not in PLATFORMS:
            warns.append(f"platform {meta['platform']!r} not one of: {', '.join(PLATFORMS)}")
        keys = engine_keys()
        if meta.get("engine") and meta["engine"] not in keys and meta["engine"] != "unknown":
            warns.append(f"engine {meta['engine']!r} isn't one of wise scan's keys ({', '.join(keys)}, unknown); fine if none fits")
        heads = [h.lower() for h in re.findall(r"^##\s+(.+)$", body, re.M)]
        for s in GAME_SECTIONS:
            if not any(h.startswith(s) for h in heads):
                fails.append(f"missing section: ## {s.capitalize()}...")
        if "gotchas" in " ".join(heads) and not re.search(r"^##\s+Gotchas.*?\n(?:.*\n)*?\s*1\.", body, re.M | re.I):
            warns.append("Gotchas section has no numbered items")
    if meta.get("status") and meta["status"] not in STATUSES:
        fails.append(f"status {meta['status']!r} not one of: {', '.join(STATUSES)}")
    d = meta.get("date")
    if d and not isinstance(d, dt.date) and not re.match(r"^\d{4}-\d{2}-\d{2}$", str(d)):
        fails.append(f"date must be YYYY-MM-DD, got {d!r}")
    for k in LIST_KEYS:
        v = meta.get(k)
        if v is not None and not isinstance(v, list):
            fails.append(f'{k} must be a list, e.g. {k}: ["a", "b"]')
        # YAML reads an unquoted `Vite 7: dev server` as a dict, `2048` as an int, and splits `node (20, 22)` in two
        for x in v if isinstance(v, list) else []:
            if not isinstance(x, str):
                fails.append(f"{k}: item {x!r} is YAML {type(x).__name__}, not text; quote it, e.g. [\"Vite 7: dev server\"]")
            elif any(x.count(a) != x.count(b) for a, b in ("()", "[]", "{}")):
                fails.append(f"{k}: item {x!r} has unbalanced brackets (split on a comma?); quote items that contain commas")
    if TEMPLATE_TITLE == meta.get("title") and "TEMPLATE" not in path.name:
        fails.append("title is still the template's example title")
    left = [ph for ph in ("FILL IN", "Two to four sentences:", "Numbered; each one symptom", "What you saw. **Cause:** what it really was")
            if ph in text]
    if left and "TEMPLATE" not in path.name:
        fails.append(f"unfilled template text: {', '.join(repr(x) for x in left)}")
    for label, rx in SECRET_PATTERNS:
        if rx.search(text):
            fails.append(f"{label} in the note - remove it")
    # the base is public: a preview or deploy host tells the world where an unreleased build lives
    for label, rx in PRIVATE_URL_PATTERNS:
        lines = match_lines(text, rx)
        if lines:
            fails.append(f"private {label} on line {where(lines)}: write https://<name>.<host> or link the public page")
    for term, lines in deny_hits(text, deny_terms(path, root, deny)).items():
        fails.append(f"denylisted name {term!r} on line {where(lines)}: describe the game neutrally")
    blocks = re.findall(r"```[^\n]*\n(.*?)```", body, re.S)
    for b in blocks:
        n = b.count("\n")
        if n > MAX_BLOCK_FAIL:
            fails.append(f"a {n}-line code block: link to your repo instead of pasting code (limit {MAX_BLOCK_FAIL})")
        elif n > MAX_BLOCK_WARN:
            warns.append(f"a {n}-line code block: keep snippets short (under {MAX_BLOCK_WARN} lines)")
    if USER_PATH.search(text):
        warns.append("absolute user path (use <you>, %USERPROFILE% or ~ instead)")
    if len(text.encode()) > MAX_NOTE_KB * 1024:
        warns.append(f"note is {len(text.encode()) // 1024} KB; split it or trim (limit {MAX_NOTE_KB} KB)")
    for m in re.finditer(r"!\[[^\]]*\]\(([^)\s]+)\)", body):
        src = m.group(1)
        if src.startswith("http"):
            continue
        img = (path.parent / src).resolve()
        if not img.exists():
            fails.append(f"image not found: {src}")
        elif img.stat().st_size > MAX_MEDIA_MB * 2**20:
            fails.append(f"image {src} is {img.stat().st_size / 2**20:.1f} MB (limit {MAX_MEDIA_MB} MB; link videos instead)")
    return fails, warns


# --------------------------------------------------------------------------- index

def build_index(root: Path) -> tuple[str, list[dict]]:
    rows = []
    for p, meta, _ in notes(root):
        rows.append(dict(path=p.relative_to(root).as_posix(), **{k: (v.isoformat() if isinstance(v, dt.date) else v) for k, v in meta.items()}))
    games = sorted([r for r in rows if r.get("kind", "game") == "game"], key=lambda r: (str(r.get("game", "")).lower(), str(r.get("date", ""))))
    techs = sorted([r for r in rows if r.get("kind") == "technique"], key=lambda r: str(r.get("title", "")).lower())
    esc = lambda s: str(s or "").replace("|", "\\|")
    lines = ["# Knowledge base index", "",
             "_Generated by `wise kb index` from the notes' front matter; don't edit by hand. Machine-readable: `index.json`._", "",
             f"## Games ({len(games)} notes)", "",
             "| Game | Note | Engine | Route | Status | Agents | Date |", "|---|---|---|---|---|---|---|"]
    for r in games:
        also = strs(r.get("games_also"))
        g = esc(r.get("game")) + (" + " + ", ".join(esc(x) for x in also) if also else "")
        lines.append(f"| {g} | [{esc(r.get('title'))}]({r['path']}) | {esc(r.get('engine'))} | {esc(r.get('route'))} | "
                     f"{esc(r.get('status'))} | {esc(', '.join(strs(r.get('agents'))))} | {esc(r.get('date'))} |")
    lines += ["", f"## Techniques ({len(techs)} notes)", ""]
    for r in techs:
        lines.append(f"- [{esc(r.get('title'))}]({r['path']}) · {esc(', '.join(strs(r.get('tags'))))}")
    lines += ["", "## Playbooks", "",
              "The workflows these notes feed (design, balance, UI, audio, performance, QA, release, trailer) live with the "
              "skills: [skills/](../skills/).", ""]
    return "\n".join(lines), rows


def index_files(root: Path) -> dict[Path, str]:
    """The two generated files and what they should hold right now."""
    idx, rows = build_index(root)
    return {root / "INDEX.md": idx, root / "index.json": json.dumps(rows, indent=1, default=str) + "\n"}


def write_index(root: Path) -> int:
    files = index_files(root)
    for p, text in files.items():
        p.write_text(text, **TEXT)
    return len(json.loads(files[root / "index.json"]))


# --------------------------------------------------------------------------- new / pr

def scan_facts(target: str) -> dict:
    """What `wise scan` knows about a game folder or URL. {} when scan is missing or fails: the note is still made."""
    try:
        from wisecraft.scan import fingerprint
        s = fingerprint(target)
    except (Exception, SystemExit) as e:    # SystemExit: scan's own die() on a folder it cannot read
        print(f"wise: --from-scan found nothing to pre-fill ({type(e).__name__}: {e})", file=sys.stderr)
        return {}
    return s if isinstance(s, dict) else {}


def new_note(root: Path, game: str | None, title: str, kind: str = "game", from_scan: str | None = None,
             engine: str | None = None, route: str | None = None, agent: str | None = None, out: str | None = None) -> Path:
    import yaml
    meta, body = parse(root / "TEMPLATE.md")
    meta = {k: v for k, v in meta.items()}
    meta.update(kind=kind, title=title, date=dt.date.today().isoformat(), agents=[agent or os.environ.get("WISE_AGENT", "FILL IN: agent (model)")],
                humans=[], links=[], tags=[], status="in-progress")
    if kind == "game":
        meta.update(game=game or "FILL IN", games_also=[], engine=engine or "unknown", route=route or "other", tools=[],
                    game_version="FILL IN: exact build and stack versions", platform="web-mobile")
        if from_scan:
            s = scan_facts(from_scan)
            eng = s.get("engine")
            key = (eng.get("key") or eng.get("name")) if isinstance(eng, dict) else eng
            versions = s.get("versions") if isinstance(s.get("versions"), dict) else {}
            if not versions and isinstance(eng, dict) and eng.get("version"):    # scan may report the version on the engine itself
                versions = {key: eng["version"]}
            stack = ", ".join(f"{k} {v}" for k, v in versions.items() if v)
            build = str(s.get("version") or "").strip()
            # still FILL IN: package.json's version and a declared range are hints, the note needs the build that worked
            meta.update(game=game or s.get("name") or "FILL IN", engine=engine or (str(key) if key else "unknown"),
                        game_version="FILL IN: " + (f"confirm build {build}" if build else "game build") + (f" ({stack})" if stack else ""))
    else:
        for k in ("game", "games_also", "game_version", "platform", "engine", "route", "tools"):
            meta.pop(k, None)
    body = re.sub(r"^# .*$", f"# {title}", body, count=1, flags=re.M)
    if kind == "technique":
        body = (f"# {title}\n\n> What this technique is for, in two sentences.\n\n## When to use it\n\n## How\n\n"
                "## Gotchas\n1. **Symptom.** ... **Cause:** ... **Fix:** ...\n\n## Seen in\nLinks to game notes that used it.\n")
    front = yaml.safe_dump(meta, sort_keys=False, allow_unicode=True, width=120)
    base = root / ("games" / Path(slug(meta.get("game", "misc"))) if kind == "game" else Path("techniques"))
    path = Path(out) if out else base / f"{slug(title)}.md"
    if path.exists():
        die(f"{path} exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{front}---\n{body}", **TEXT)
    return path


def pr_head(branch: str, fork_url: str | None) -> str:
    """The --head for `gh pr create`. gh looks a bare branch name up in the base repo, so a PR from a fork needs
    "<fork owner>:<branch>" (else: "Head ref must be a branch"). fork_url: the fork remote's URL, None when pushing
    to the repo itself."""
    m = re.search(r"github\.com[:/]+([^/]+)/", fork_url or "")
    return f"{m.group(1)}:{branch}" if m else branch


def open_pr(path: Path, yes: bool):
    """Branch + commit the note (and its media + regenerated index) + push to your fork + gh pr create."""
    root = local_root()
    if not root:
        die("run this inside a clone of the repo (or your fork)")
    repo = root.parent
    meta, _ = parse(path)
    fails, _ = check_note(path, root)
    if fails:
        die("fix these first:\n  " + "\n  ".join(fails))
    branch = f"kb/{slug(meta.get('game', '') or 'technique')}-{slug(meta.get('title', 'note'))}"[:80]
    title = f"kb: {meta.get('title')}" + (f" ({meta.get('game')})" if meta.get("game") else "")
    body = (f"Field note: **{meta.get('title')}**\n\n- game: {meta.get('game', '-')}\n- engine / route: {meta.get('engine', '-')} / "
            f"{meta.get('route', '-')}\n- status: {meta.get('status')}\n- agents: {', '.join(meta.get('agents') or [])}\n\n"
            "Checked with `wise kb check`; index regenerated with `wise kb index`.\n\n"
            "- [x] no secrets, private URLs, company or unreleased product names\n- [x] versions and verification written down\n")
    media = [p for p in path.parent.glob("media/*")] if (path.parent / "media").exists() else []
    can_push = False
    if shutil.which("gh"):
        r = subprocess.run(["gh", "api", f"repos/{REPO}", "--jq", ".permissions.push"], capture_output=True, text=True)
        can_push = r.stdout.strip() == "true"
    remote = "origin" if can_push else "fork"
    cmds = [["git", "checkout", "-b", branch], ["wise", "kb", "index"],
            ["git", "add", str(path), str(root / "INDEX.md"), str(root / "index.json"), *map(str, media)],
            ["git", "commit", "-m", title]]
    if not can_push:
        cmds.append(["gh", "repo", "fork", "--remote", "--remote-name", "fork"])
    cmds += [["git", "push", "-u", remote, branch],
             ["gh", "pr", "create", "--repo", REPO, "--head", branch, "--title", title, "--body", body]]
    if not yes:
        print("dry run (add --yes after your human agrees):")
        for c in cmds:
            print("  " + " ".join(c if len(" ".join(c)) < 200 else c[:6] + ["..."]))
        return
    if not shutil.which("gh"):
        die("needs the GitHub CLI (gh) logged in; or push a branch and open the PR on github.com")
    write_index(root)
    for c in cmds:
        if c[:3] == ["wise", "kb", "index"]:
            continue
        if c[:3] == ["gh", "repo", "fork"] and subprocess.run(["git", "remote", "get-url", "fork"], cwd=repo, capture_output=True).returncode == 0:
            continue
        if c[:3] == ["gh", "pr", "create"] and remote == "fork":
            url = subprocess.run(["git", "remote", "get-url", "fork"], cwd=repo, capture_output=True, text=True).stdout.strip()
            c[c.index("--head") + 1] = pr_head(branch, url)
        r = subprocess.run(c, cwd=repo, capture_output=True, text=True)
        if r.returncode:
            die(f"{' '.join(c[:4])} failed: {(r.stderr or r.stdout).strip()[-800:]}")
        if c[:3] == ["gh", "pr", "create"]:
            print(r.stdout.strip())


# --------------------------------------------------------------------------- CLI

def main(a):
    c = a.cmd
    if c == "sync":
        sync()
        return
    if c == "search":
        root = resolve_root(a.root, a.remote)
        res = search(root, a.terms, a.game, a.engine, a.route, a.limit)
        if a.json:
            print(json.dumps(res, indent=1))
            return
        if not res:
            print(f"nothing in {root} matches; you may be first - write it up afterwards (`wise kb new`)")
        for r in res:
            facts = " | ".join(str(x) for x in (r["game"], r["engine"], r["route"], r["status"]) if x) or "technique"
            print(f"{r['path']}\n   {r['title']}  [{facts}]")
            for h in r["hits"]:
                print(f"     | {h.lstrip('> ')[:160]}")
        return
    if c == "show":
        root = resolve_root(a.root, a.remote)
        p = root / a.note
        if not p.exists():
            cands = [x for x in root.rglob("*.md") if a.note in x.as_posix()]
            if not cands:
                die(f"no note {a.note!r} in {root}")
            p = cands[0]
        print(p.read_text(encoding="utf-8"))
        return
    if c in ("new", "add"):
        root = Path(a.root) if a.root else local_root()
        if not root:
            die("run inside a clone of the repo (knowledge/ is written there), or pass --root")
        p = new_note(root, a.game, a.title, a.kind, a.from_scan, a.engine, a.route, a.agent, a.out)
        print(p)
        print("next: fill it in (Gotchas matter most), `wise kb check " + str(p) + "`, `wise kb index`, then a PR (`wise kb pr ...`)")
        return
    if c == "check":
        root = Path(a.root) if a.root else local_root()
        paths = [Path(x) for x in a.paths] or ([p for p, _, _ in notes(root)] if root else [])
        bad = 0
        for p in paths:
            fails, warns = check_note(p, root, a.deny)
            for f in fails:
                print(f"FAIL {p}: {f}")
            for w in warns:
                print(f"WARN {p}: {w}")
            bad += bool(fails)
        if root and a.index and not a.paths:
            for f, want in index_files(root).items():
                if not f.exists() or f.read_text(encoding="utf-8") != want:
                    print(f"FAIL knowledge/{f.name} is out of date: run `wise kb index`")
                    bad += 1
        print(f"{'FAIL' if bad else 'PASS'}: {len(paths)} notes checked")
        raise SystemExit(1 if bad else 0)
    if c == "index":
        root = Path(a.root) if a.root else local_root()
        if not root:
            die("no local knowledge/ folder")
        print(f"{root / 'INDEX.md'}: {write_index(root)} notes")
        return
    if c == "pr":
        open_pr(Path(a.note), a.yes)


def register(sub):
    import argparse
    p = sub.add_parser("kb", help="knowledge base of how web games were built and shipped: search, write, check, PR",
                       description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    cs = p.add_subparsers(dest="cmd", metavar="<cmd>")
    q = cs.add_parser("search", help="find prior notes (local clone, else the GitHub copy)")
    q.add_argument("terms", nargs="*")
    q.add_argument("--game")
    q.add_argument("--engine")
    q.add_argument("--route", choices=ROUTES)
    q.add_argument("--limit", type=int, default=10)
    q.add_argument("--json", action="store_true")
    q.add_argument("--remote", action="store_true", help="search the synced GitHub copy even inside a clone")
    q.add_argument("--root")
    q.set_defaults(func=main)
    q = cs.add_parser("show", help="print a note")
    q.add_argument("note")
    q.add_argument("--remote", action="store_true")
    q.add_argument("--root")
    q.set_defaults(func=main)
    q = cs.add_parser("new", aliases=["add"], help="scaffold a note from the template (`add` is the same)")
    q.add_argument("--title", required=True)
    q.add_argument("--game", help='a neutral description, e.g. "Horde tower defense (mobile web)"')
    q.add_argument("--kind", default="game", choices=["game", "technique"])
    q.add_argument("--from-scan", metavar="DIR_OR_URL", help="pre-fill engine / stack versions / name from `wise scan <dir or URL>`")
    q.add_argument("--engine", help=f"wise scan's key ({', '.join(ENGINES)}) or free text")
    q.add_argument("--route", choices=ROUTES)
    q.add_argument("--agent", help='e.g. "Codex (gpt-6)"; default $WISE_AGENT')
    q.add_argument("--out")
    q.add_argument("--root")
    q.set_defaults(func=main)
    q = cs.add_parser("check", help="validate notes (all, or the given paths)")
    q.add_argument("paths", nargs="*")
    q.add_argument("--index", action="store_true", help="also fail if INDEX.md or index.json is stale")
    q.add_argument("--deny", metavar="FILE", help="denylist of names (default: the repo's .wise-denylist, else $WISE_DENY)")
    q.add_argument("--root")
    q.set_defaults(func=main)
    q = cs.add_parser("index", help="regenerate knowledge/INDEX.md and index.json")
    q.add_argument("--root")
    q.set_defaults(func=main)
    cs.add_parser("sync", help="refresh the cached GitHub copy").set_defaults(func=main)
    q = cs.add_parser("pr", help="open a pull request with a note (dry run unless --yes)")
    q.add_argument("note")
    q.add_argument("--yes", action="store_true", help="really branch, push and open the PR")
    q.set_defaults(func=main)
