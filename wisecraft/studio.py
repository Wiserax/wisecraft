"""A live studio panel for a side pane: every agent at work, and a feed of what they make, to review.

    wise studio                       # serve http://127.0.0.1:5480 until Ctrl-C
    wise studio --open                # also open it in Orca's browser pane (orca tab create --url ...)
    wise studio --port 5490 --hours 4 # another port, a shorter window
    wise studio --print-config        # the config file, the watched folders and the reviews file, then stop

The page is made for a narrow pane (360-480 px), dark, and refreshes every 3 s while it is visible.
- Agents: Claude Code lead sessions and their subagents (~/.claude*/projects), background task transcripts
  (<tmp>/claude-<uid>/*/*/tasks/*.output), Orca terminals (`orca terminal list`) and Codex sessions
  (~/.codex/sessions). Each shows its state, what it is doing now (its last tool call), time, tokens and API $.
- Feed: images, videos and 3D models (.glb, .fbx) created or changed in the watched folders in the last
  --hours, newest first, with the project and, when a transcript names the file, the agent. Tap for a lightbox;
  a .glb opens in a 3D viewer. 👍 / 👎 and a note append a line to reviews.jsonl for agents to read.
- Mailbox: recent Orca orchestration messages, loaded when opened.

Config, optional JSON at ~/.config/wisecraft/studio.json (or --config FILE):
  {"base": "~/Documents/Codex", "roots": ["*/outputs", "*/shots", "*/qa", "*/art-shots"], "hours": 8,
   "reviews": "~/.config/wisecraft/reviews.jsonl"}
Roots are globs under base, or absolute; every matched folder is watched with its subfolders.

Safety: it binds 127.0.0.1 only, serves files only from inside the watched folders (real paths, no traversal),
hides tokens and keys in what it shows, and writes nothing but reviews.jsonl and thumbnails in
~/.cache/wisecraft/studio. Scans are cached by mtime and run only while a page is polling.
Exit 0 on Ctrl-C (or when a studio already answers on the port), 2 on usage errors or a port in use.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import types
import urllib.parse
import urllib.request
from collections import OrderedDict
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAGE = HERE / "studio.html"
CONFIG = Path("~/.config/wisecraft/studio.json").expanduser()
DEFAULTS = {
    "base": "~/Documents/Codex",
    "roots": ["*/outputs", "*/shots", "*/qa", "*/art-shots"],
    "hours": 8,
    "reviews": "~/.config/wisecraft/reviews.jsonl",
    "claude_dirs": ["~/.claude", "~/.claude-work"],
    "codex_dir": "~/.codex",
}
IMAGE = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
VIDEO = {".webm", ".mp4"}
MODEL = {".glb", ".fbx"}
MEDIA = IMAGE | VIDEO | MODEL
MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".gif": "image/gif",
        ".webm": "video/webm", ".mp4": "video/mp4", ".glb": "model/gltf-binary", ".fbx": "application/octet-stream"}
SKIP_DIRS = {"node_modules", "__pycache__", ".git", ".venv", "venv", ".cache", "build", "dist"}  # build copies, not new work
RUNNING_IF_WRITTEN_WITHIN = 180
BULK = (60, 3.0)  # this many files in one project within +-3 s is a checkout or a batch export: one card


def kind_of(path) -> str:
    ext = os.path.splitext(str(path))[1].lower()
    return "image" if ext in IMAGE else "video" if ext in VIDEO else "model" if ext in MODEL else ""


# --------------------------------------------------------------------------- the progress skill's parser

def load_progress_agents():
    """skills/progress/scripts/agents.py, the one transcript parser (a wheel carries a copy beside this file)."""
    for p in (HERE.parent / "skills" / "progress" / "scripts" / "agents.py", HERE / "_progress_agents.py"):
        if p.is_file():
            # compiled by hand: no __pycache__ appears inside skills/, whose copies must match it byte for byte
            mod = types.ModuleType("wisecraft_progress_agents")
            mod.__file__ = str(p)
            exec(compile(p.read_text(encoding="utf-8"), str(p), "exec"), mod.__dict__)
            return mod
    raise ImportError("skills/progress/scripts/agents.py not found")


AG = load_progress_agents()


# --------------------------------------------------------------------------- secrets never leave

_SECRETS = [
    (re.compile(r"(?i)\b([\w.-]*(?:api[_-]?key|access[_-]?key|token|secret|passw(?:or)?d|credential|cookie|session[_-]?id)[\w.-]*)"
                r"(\s*[:=]\s*)(\"[^\"]*\"|'[^']*'|\S+)"), r"\1\2***"),
    (re.compile(r"(?i)\b(authorization|bearer|x-api-key)(\s*[:=]?\s*)(bearer\s+)?(\"[^\"]*\"|'[^']*'|\S+)"), r"\1\2***"),
    (re.compile(r"\b(?:sk|pk|rk)-[A-Za-z0-9_-]{12,}"), "***"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{16,}"), "***"),
    (re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"), "***"),
    (re.compile(r"\bAKIA[0-9A-Z]{12,}"), "***"),
    (re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]*"), "***"),
    (re.compile(r"(?=[A-Za-z0-9+_=]*\d)(?=[A-Za-z0-9+_=]*[A-Za-z])\b[A-Za-z0-9+_=]{32,}"), "***"),
]


def redact(text: str, limit: int = 200) -> str:
    """Text safe to show: no keys, tokens, passwords, nothing that reads ~/.config or the environment."""
    if not text:
        return ""
    text = str(text)
    if re.search(r"(^|[\s'\"=])(~|\$HOME|/Users/[^/\s]+|/home/[^/\s]+)/\.config/|\.(env|netrc|npmrc|pypirc)\b|\bprintenv\b|(^|[;&|]\s*)env\s*($|\|)",
                 text):
        return "(hidden: reads private settings)"
    for rx, sub in _SECRETS:
        text = rx.sub(sub, text)
    text = " ".join(text.split()) if "\n" not in text else text
    return text if len(text) <= limit else text[: limit - 1] + "…"


# --------------------------------------------------------------------------- config and the path guard

def load_config(path=None) -> dict:
    cfg = dict(DEFAULTS)
    p = Path(path).expanduser() if path else CONFIG
    if p.is_file():
        try:
            user = json.loads(p.read_text(encoding="utf-8"))
        except ValueError as e:
            raise SystemExit(f"studio config {p} is not valid JSON: {e}")
        cfg.update({k: v for k, v in user.items() if k in DEFAULTS})
    elif path:
        raise SystemExit(f"studio config not found: {p}")
    cfg["_file"] = str(p)
    return cfg


def expand_roots(cfg) -> list[str]:
    """Real paths of the watched folders, longest first; folders inside another root are dropped."""
    base = Path(cfg["base"]).expanduser()
    found = set()
    for pattern in cfg["roots"]:
        pat = os.path.expanduser(pattern)
        pat = pat if os.path.isabs(pat) else str(base / pat)
        pat = pat[:-3] if pat.endswith("/**") else pat
        for m in glob.glob(pat):
            if os.path.isdir(m):
                found.add(os.path.realpath(m))
    roots = sorted(found)
    return [r for r in roots if not any(r != o and r.startswith(o + os.sep) for o in roots)]


def guard(raw, roots) -> Path | None:
    """The real path of a media file inside one of the roots, or None. Every served or reviewed path goes through it."""
    if not raw or not isinstance(raw, str) or "\x00" in raw:
        return None
    p = os.path.expanduser(raw)
    if not os.path.isabs(p):
        return None
    real = os.path.realpath(p)
    if os.path.splitext(real)[1].lower() not in MEDIA:
        return None
    for r in roots:
        r = os.path.realpath(r)
        if real.startswith(r.rstrip(os.sep) + os.sep) and os.path.isfile(real):
            return Path(real)
    return None


def project_of(path: str, base: str) -> str:
    """The first folder under base (a worktree), or the root's parent folder's name."""
    rel = os.path.relpath(path, base)
    if not rel.startswith(".."):
        return rel.split(os.sep, 1)[0]
    return Path(path).parent.parent.name


# --------------------------------------------------------------------------- transcripts, read incrementally

MEDIA_RE = re.compile(r"(?<![\w@%+~./-])[\w@%+~./-]{0,240}[\w-]\.(?:png|jpe?g|webp|gif|webm|mp4|glb|fbx)\b", re.I)
MEDIA_HINT = re.compile(r"\.(?:png|jpe?g|webp|gif|webm|mp4|glb|fbx)\b", re.I)
DIR_RE = re.compile(r"(?<![\w@.~/-])(?:~|\.{1,2})?/?(?:[\w@.-]{1,80}/){1,12}[\w@.-]{1,80}/?")


def walk_strings(x, out, depth=0):
    """Every string inside a tool call or result, skipping inline images and anything huge."""
    if depth > 6 or len(out) > 200:
        return out
    if isinstance(x, str):
        if len(x) <= 100000:
            out.append(x)
    elif isinstance(x, dict):
        if x.get("type") in ("image", "document") or "base64" in str(x.get("type", "")):
            return out
        for v in x.values():
            walk_strings(v, out, depth + 1)
    elif isinstance(x, list):
        for v in x:
            walk_strings(v, out, depth + 1)
    return out


class Mentions:
    """Which agent named which media file (or its folder) in a tool call or a tool result, and when."""

    def __init__(self, cap=60000):
        self.keys = OrderedDict()
        self.cap = cap

    def _put(self, key, entry):
        lst = self.keys.pop(key, [])
        lst.append(entry)
        self.keys[key] = lst[-4:]
        while len(self.keys) > self.cap:
            self.keys.popitem(last=False)

    @staticmethod
    def keys_for(token: str, cwd: str | None):
        tok = token.strip("'\"`()[],;:")
        if tok.startswith("~"):
            tok = os.path.expanduser(tok)
        elif not tok.startswith("/") and cwd:
            tok = os.path.normpath(os.path.join(cwd, tok))
        parts = [p for p in tok.split("/") if p]
        keys = []
        if tok.startswith("/"):
            keys.append("abs:" + os.path.normpath(tok))
        if len(parts) >= 2:
            keys.append("tail:" + "/".join(parts[-2:]))
        if parts:
            keys.append("base:" + parts[-1])
        return keys

    def add_text(self, text: str, agent: str, t: float, prio: int, cwd: str | None, dirs: bool = False):
        if not text or len(text) > 100000:
            return
        for tok in (MEDIA_RE.findall(text)[:200] if MEDIA_HINT.search(text) else ()):
            for k in self.keys_for(tok, cwd):
                self._put(k, (t, prio, agent))
        if dirs:
            for tok in DIR_RE.findall(text)[:40]:
                if not MEDIA_RE.fullmatch(tok):
                    parts = [p for p in os.path.normpath(os.path.join(cwd or "/", tok.rstrip("/"))).split("/") if p]
                    if len(parts) >= 2:
                        self._put("dir:" + "/".join(parts[-2:]), (t, 1, agent))

    def who(self, path: str, mtime: float):
        """(agent key, sure) for a file, from the latest naming before it was written (+2 min), tool calls first."""
        parts = [p for p in path.split("/") if p]
        base = parts[-1]
        exact = ["abs:" + path, "tail:" + "/".join(parts[-2:])]
        if len(base) >= 10 or re.search(r"\d", base):
            exact.append("base:" + base)
        for keys, sure, span in ((exact, True, 6 * 3600), (["dir:" + "/".join(parts[-3:-1]), "dir:" + "/".join(parts[-4:-2])], False, 1200)):
            best = None
            for k in keys:
                for t, prio, agent in self.keys.get(k, ()):
                    # the lead often names a file its worker wrote; a worker's own call ranks first
                    rank = (prio, not agent.startswith("lead:"), t)
                    if mtime - span <= t <= mtime + 120 and (best is None or rank > best[0]):
                        best = (rank, agent)
            if best:
                return best[1], sure
        return None, False


class Tail:
    """One JSONL transcript, read from where the last read stopped. A big file is first entered near the start of
    the time window (a bisection on the timestamps), lines over MAX_LINE are skipped, and keep() filters raw lines
    before they are parsed, so a 400 MB lead transcript costs a few hundred ms once, then only its new bytes."""

    MAX_LINE = 512 * 1024
    BISECT_OVER = 8 << 20

    def __init__(self, path: str, since: float):
        self.path, self.since = path, since
        self.offset, self.rest, self.size, self.mtime = 0, b"", -1, 0.0

    def keep(self, line: bytes) -> bool:
        return True

    @staticmethod
    def _ts_after(f, off):
        f.seek(off)
        if off:
            f.readline()
        for _ in range(64):
            line = f.readline()
            if not line:
                return None
            m = re.search(rb'"timestamp":"([^"]{10,40})"', line)
            if m:
                try:
                    return AG.ts(m.group(1).decode())
                except ValueError:
                    continue
        return None

    def _start(self, f, size):
        lo, hi = 0, size
        while hi - lo > (1 << 20):
            mid = (lo + hi) // 2
            t = self._ts_after(f, mid)
            if t is not None and t < self.since:
                lo = mid
            else:
                hi = mid
        if lo:
            f.seek(lo)
            f.readline()
            return f.tell()
        return 0

    def new_lines(self, st):
        if st.st_size == self.size and st.st_mtime == self.mtime:
            return []
        if st.st_size < self.offset:
            self.offset, self.rest = 0, b""
            self.reset()
        self.size, self.mtime = st.st_size, st.st_mtime
        out = []
        with open(self.path, "rb") as f:
            if self.offset == 0 and st.st_size > self.BISECT_OVER:
                self.offset = self._start(f, st.st_size)
            f.seek(self.offset)
            while True:
                chunk = f.read(4 << 20)
                if not chunk:
                    break
                self.offset += len(chunk)
                lines = (self.rest + chunk).split(b"\n")
                self.rest = lines.pop()
                if len(self.rest) > self.MAX_LINE:
                    self.rest = b"\0"  # a giant line: drop it as it streams past
                for line in lines:
                    if not line or line[:1] == b"\0" or len(line) > self.MAX_LINE or not self.keep(line):
                        continue
                    try:
                        out.append(json.loads(line))
                    except ValueError:
                        continue
        return out

    def reset(self):
        pass


class ClaudeTail(Tail):
    def __init__(self, path, since, key, mentions):
        super().__init__(path, since)
        self.key, self.mentions = key, mentions
        self.tally = AG.Tally(since)

    def reset(self):
        self.tally = AG.Tally(self.since)

    def keep(self, line):
        # the lines the tally and the mentions use; attachments, hooks and request blobs are never parsed
        return b'"assistant"' in line or b'"ai-title"' in line or b'"tool_result"' in line

    def read(self, st):
        for d in self.new_lines(st):
            self.tally.feed(d)
            if not isinstance(d, dict) or not d.get("timestamp"):
                continue
            m = d.get("message")
            if not isinstance(m, dict) or not isinstance(m.get("content"), list):
                continue
            try:
                t = AG.ts(d["timestamp"])
            except ValueError:
                continue
            if t < self.since:
                continue
            cwd = d.get("cwd")
            for c in m["content"]:
                if not isinstance(c, dict):
                    continue
                if c.get("type") == "tool_use":
                    for s in walk_strings(c.get("input"), []):
                        self.mentions.add_text(s, self.key, t, 2, cwd, dirs=c.get("name") == "Bash")
                elif c.get("type") == "tool_result":
                    for s in walk_strings(c.get("content"), []):
                        self.mentions.add_text(s, self.key, t, 1, cwd)
        return self.tally.result()


def codex_doing(name, args) -> str:
    """A Codex tool call in a few words: the shell command it runs, else the first line of its code."""
    if name == "wait":
        return "waiting for a running cell"
    if isinstance(args, dict):
        cmd = args.get("cmd") or args.get("command") or args.get("code") or ""
        cmd = " ".join(map(str, cmd)) if isinstance(cmd, list) else str(cmd)
    else:
        cmd = str(args or "")
    m = re.search(r"""cmd:\s*["'`]([^"'`]{1,200})""", cmd)
    if m:
        return m.group(1).replace("\\n", " ; ")
    m = re.search(r"tools\.(\w+)", cmd)
    lines = [ln.strip() for ln in cmd.splitlines() if ln.strip() and not ln.strip().startswith("//")]
    return (m.group(1).replace("_", " ") if m else "") or (lines[0] if lines else name)


class CodexTail(Tail):
    MAX_LINE = 16 << 20  # a prompt with a pasted image is one multi-MB line, and it holds the task's title

    def __init__(self, path, since, key, mentions):
        super().__init__(path, since)
        self.key, self.mentions = key, mentions
        self.reset()
        try:  # the first line names the folder, even when the window starts later in the file
            with open(path, "rb") as f:
                first = json.loads(f.readline(4 << 20) or b"{}")
            self.cwd = ((first.get("payload") or {}).get("cwd")) or None
        except (OSError, ValueError, AttributeError):
            pass

    def reset(self):
        self.cwd = self.title = self.doing = self.said = None
        self.tokens, self.first, self.last, self.done = 0, None, None, False

    def read(self, st):
        for d in self.new_lines(st):
            if not isinstance(d, dict):
                continue
            p = d.get("payload") if isinstance(d.get("payload"), dict) else {}
            kind, sub = d.get("type"), p.get("type")
            if kind == "session_meta":
                self.cwd = p.get("cwd") or self.cwd
            try:
                t = AG.ts(d["timestamp"]) if d.get("timestamp") else None
            except ValueError:
                t = None
            if t is None or t < self.since:
                continue
            self.first, self.last = self.first or t, t
            if sub == "token_count":
                total = ((p.get("info") or {}).get("total_token_usage") or {}).get("total_tokens")
                self.tokens = total or self.tokens
            elif sub == "task_started":
                self.done = False
            elif sub == "task_complete":
                self.done = True
                self.said = p.get("last_agent_message") or self.said
            elif kind == "response_item" and sub in ("function_call", "custom_tool_call", "local_shell_call"):
                args = p.get("arguments") or p.get("input") or p.get("action") or ""
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except ValueError:
                        pass
                self.doing = codex_doing(p.get("name") or "tool", args)
                for s in walk_strings(args, []):
                    self.mentions.add_text(s, self.key, t, 2, self.cwd, dirs=True)
            elif kind == "response_item" and sub in ("function_call_output", "custom_tool_call_output"):
                for s in walk_strings(p.get("output"), []):
                    self.mentions.add_text(s, self.key, t, 1, self.cwd)
            elif kind == "response_item" and sub == "message" and p.get("role") == "user" and not self.title:
                for c in p.get("content") or []:
                    text = (c or {}).get("text") or ""
                    if text.strip() and not text.lstrip().startswith(("<", "#")):
                        self.title = text.strip().splitlines()[0]
                        break
        return self


# --------------------------------------------------------------------------- the scanners

def _cached(ttl):
    """Recompute at most once per ttl seconds; callers in between get the last result."""
    def wrap(fn):
        def inner(self, *a, **kw):
            now = time.time()
            slot = self._cache.setdefault(fn.__name__, [0.0, None])
            with self._lock:
                if now - slot[0] >= ttl or slot[1] is None:
                    slot[1], slot[0] = fn(self, *a, **kw), time.time()
                return slot[1]
        return inner
    return wrap


def orca(*args, timeout=6):
    exe = shutil.which("orca")
    if not exe:
        return None
    try:
        r = subprocess.run([exe, *args], capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if r.returncode != 0:
        return None
    if "--json" in args:
        try:
            return json.loads(r.stdout).get("result")
        except (ValueError, AttributeError):
            return None
    return r.stdout


class Agents:
    def __init__(self, cfg, mentions):
        self.cfg, self.mentions = cfg, mentions
        self.hours = float(cfg["hours"])
        self.tails: dict[str, Tail] = {}
        self.meta: dict[str, str] = {}
        self.labels: dict[str, dict] = {}
        self._lock, self._cache = threading.RLock(), {}

    def since(self):
        return time.time() - self.hours * 3600

    def _tail(self, cls, path, key):
        t = self.tails.get(path)
        if t is None:
            t = self.tails[path] = cls(path, self.since(), key, self.mentions)
        return t

    def _desc(self, meta_path):
        if meta_path not in self.meta:
            try:
                self.meta[meta_path] = json.loads(Path(meta_path).read_text()).get("description", "")
            except (OSError, ValueError):
                self.meta[meta_path] = ""
        return self.meta[meta_path]

    @staticmethod
    def _scandir(d):
        try:
            return list(os.scandir(d))
        except OSError:
            return []

    def _row(self, path, st, key, desc, lead):
        r = self._tail(ClaudeTail, path, key).read(st)
        if not r["first"]:
            return None
        age = time.time() - st.st_mtime
        if age < RUNNING_IF_WRITTEN_WITHIN:
            state = "running"
        elif lead:
            state = "idle"
        else:
            state = "done" if r["stop"] == "end_turn" else "stopped"
        row = {"id": key, "desc": redact(desc or r["title"] or "", 90), "state": state, "doing": redact(r["doing"], 110),
               "minutes": round((r["last"] - r["first"]) / 60), "tokens": r["tokens"], "cost": round(r["cost"], 2),
               "last": r["last"], "model": (r["model"] or "").replace("claude-", "")}
        self.labels[key] = {"agent": row["desc"] or "lead", "session": None}
        return row, r

    @_cached(3)
    def claude(self):
        cut = self.since()
        sessions = {}
        known = set()
        pdirs = []
        for cdir in self.cfg["claude_dirs"]:
            real = os.path.realpath(os.path.expanduser(os.path.join(cdir, "projects")))
            if os.path.isdir(real) and real not in [r for r, _ in pdirs]:
                pdirs.append((real, Path(cdir).name.lstrip(".")))  # accounts that share one projects folder count once
        for pdir, account in pdirs:
            for proj in self._scandir(pdir):
                if not proj.is_dir():
                    continue
                for e in self._scandir(proj.path):
                    if not (e.name.endswith(".jsonl") and e.is_file()):
                        continue
                    sid = e.name[:-6]
                    sdir = os.path.join(proj.path, sid)
                    subs = []
                    sub_dir = os.path.join(sdir, "subagents")
                    for s in self._scandir(sub_dir):
                        if s.name.startswith("agent-") and s.name.endswith(".jsonl"):
                            subs.append(s)
                    st = e.stat()
                    sub_stats = [(s, s.stat()) for s in subs]
                    if st.st_mtime < cut and not any(ss.st_mtime >= cut for _, ss in sub_stats):
                        continue
                    sess = {"id": sid[:8], "account": account, "project": proj.name, "title": "", "cwd": "",
                            "lead": None, "agents": []}
                    if st.st_mtime >= cut:
                        got = self._row(e.path, st, "lead:" + sid, "", True)
                        if got:
                            row, r = got
                            sess["lead"], sess["title"], sess["cwd"] = row, redact(r["title"] or "", 80), r["cwd"] or ""
                            row["desc"] = "lead"
                    known.add(os.path.realpath(e.path))
                    for s, ss in sub_stats:
                        known.add(os.path.realpath(s.path))
                        if ss.st_mtime < cut:
                            continue
                        aid = s.name[6:-6]
                        got = self._row(s.path, ss, aid, self._desc(s.path[:-6] + ".meta.json"), False)
                        if got:
                            sess["agents"].append(got[0])
                            sess["cwd"] = sess["cwd"] or got[1]["cwd"] or ""
                    if sess["lead"] or sess["agents"]:
                        sessions[sid] = sess
        self._tasks(sessions, known, cut)
        out = []
        for sid, sess in sessions.items():
            title = sess["title"] or (sess["agents"][0]["desc"] if sess["agents"] else sid[:8])
            for a in ([sess["lead"]] if sess["lead"] else []) + sess["agents"]:
                self.labels[a["id"]] = {"agent": a["desc"], "session": title}
            rows = ([sess["lead"]] if sess["lead"] else []) + sess["agents"]
            sess["title"] = title
            sess["project"] = Path(sess["cwd"]).name if sess["cwd"] else sess["project"].rsplit("-", 1)[-1]
            sess["last"] = max(r["last"] for r in rows)
            sess["running"] = sum(r["state"] == "running" for r in rows)
            sess["cost"] = round(sum(r["cost"] for r in rows), 2)
            sess["tokens"] = sum(r["tokens"] for r in rows)
            sess["agents"].sort(key=lambda r: (r["state"] != "running", -r["last"]))
            out.append(sess)
        out.sort(key=lambda s: (s["running"] == 0, -s["last"]))
        return out

    def _tasks(self, sessions, known, cut):
        """Background task outputs that are JSONL transcripts and not a subagent file already counted."""
        if not hasattr(os, "getuid"):
            return
        roots = {os.path.realpath(f"/tmp/claude-{os.getuid()}"), os.path.join(tempfile.gettempdir(), f"claude-{os.getuid()}")}
        seen = set()
        for root in roots:
            for f in glob.glob(os.path.join(root, "*", "*", "tasks", "*.output")):
                real = os.path.realpath(f)
                if real in known or real in seen:
                    continue
                seen.add(real)
                try:
                    st = os.stat(real)
                    if st.st_mtime < cut or st.st_size == 0:
                        continue
                    with open(real, "rb") as fh:
                        if fh.read(1) != b"{":
                            continue
                except OSError:
                    continue
                sid = Path(f).parent.parent.name
                got = self._row(real, st, "task-" + Path(f).stem, "background task " + Path(f).stem[:8], False)
                if not got:
                    continue
                sess = sessions.setdefault(sid, {"id": sid[:8], "account": "claude", "project": Path(f).parent.parent.parent.name,
                                                 "title": "", "cwd": got[1]["cwd"] or "", "lead": None, "agents": []})
                sess["agents"].append(got[0])

    @_cached(4)
    def codex(self):
        cut = self.since()
        root = Path(self.cfg["codex_dir"]).expanduser() / "sessions"
        out = []
        days = {datetime.fromtimestamp(t).strftime("%Y/%m/%d") for t in (time.time(), cut)}
        for day in sorted(days):
            for e in self._scandir(root / day):
                if not e.name.endswith(".jsonl"):
                    continue
                st = e.stat()
                if st.st_mtime < cut:
                    continue
                key = "codex-" + e.name[-14:-6]
                t = self._tail(CodexTail, e.path, key).read(st)
                if not t.first:
                    continue
                age = time.time() - st.st_mtime
                state = "done" if t.done else "running" if age < RUNNING_IF_WRITTEN_WITHIN else "stopped"
                desc = redact(t.title or "Codex", 90)
                row = {"id": key, "desc": desc, "state": state, "doing": redact(t.said if t.done and t.said else t.doing or "", 110),
                       "minutes": round((t.last - t.first) / 60), "tokens": t.tokens, "cost": None, "last": t.last,
                       "project": Path(t.cwd).name if t.cwd else "", "model": "codex"}
                self.labels[key] = {"agent": desc, "session": "Codex"}
                out.append(row)
        out.sort(key=lambda r: (r["state"] != "running", -r["last"]))
        return out

    @_cached(30)
    def terminals(self):
        res = orca("terminal", "list", "--json", timeout=8)
        if not res:
            return None
        out = []
        for t in res.get("terminals") or []:
            title = t.get("title") or ""
            glyph = title[:1] if title[:1] in "◐◑◒◓✳⠂⠐" else ""
            busy = glyph in "◐◑◒◓⠂⠐" and glyph != ""
            out.append({"handle": t.get("handle"), "title": redact(title.lstrip("◐◑◒◓✳⠂⠐ ").strip(), 80), "busy": busy,
                        "idle": glyph == "✳", "path": t.get("worktreePath") or "", "worktree": Path(t.get("worktreePath") or "").name,
                        "agent": t.get("agentIdentity") or "", "last": (t.get("lastOutputAt") or 0) / 1000,
                        "connected": bool(t.get("connected"))})
        out.sort(key=lambda t: (not t["busy"], -t["last"]))
        return out

    @_cached(60)
    def mailbox(self):
        res = orca("orchestration", "inbox", "--limit", "25", "--json", timeout=8)
        if res is None:
            return None
        names = {t["handle"]: t["title"] for t in (self.terminals() or [])}
        out = []
        for m in res.get("messages") or []:
            out.append({"subject": redact(m.get("subject") or "", 120), "body": redact(m.get("body") or "", 600),
                        "type": m.get("type") or "", "time": m.get("created_at") or "",
                        "from": names.get(m.get("from_handle"), (m.get("from_handle") or "")[:13]),
                        "to": names.get(m.get("to_handle"), (m.get("to_handle") or "")[:16])})
        return out

    def state(self):
        sessions = self.claude()
        codex = self.codex()
        terms = self.terminals()
        used = set()
        for s in sessions:
            for t in terms or []:
                if t["handle"] in used:
                    continue
                if t["title"] and t["title"] == s["title"] and (not s["cwd"] or t["path"] == s["cwd"]):
                    s["terminal"] = {"handle": t["handle"], "busy": t["busy"]}
                    used.add(t["handle"])
                    break
        others = [t for t in (terms or []) if t["handle"] not in used]
        return {"sessions": sessions, "codex": codex, "terminals": others, "orca": terms is not None,
                "running": sum(s["running"] for s in sessions) + sum(c["state"] == "running" for c in codex),
                "cost": round(sum(s["cost"] for s in sessions), 2)}


def term_preview(handle: str):
    if not re.fullmatch(r"term_[0-9a-f-]{8,64}", handle or ""):
        return None
    out = orca("terminal", "read", "--terminal", handle, "--screen", "--json", timeout=8)
    lines = []
    if isinstance(out, dict):
        text = out.get("output") or out.get("text") or out.get("screen") or ""
        if isinstance(text, list):
            text = "\n".join(map(str, text))
        lines = [ln.rstrip() for ln in str(text).splitlines() if ln.strip()]
    return [redact(ln, 160) for ln in lines[-12:]]


class Feed:
    """Recent media files in the watched folders, kept current without walking them again:
    - every pass (5 s), folders with a change in the last 15 min are relisted (in-place overwrites show up);
    - every third pass, folders changed inside the window and the top two levels of each root are stat'ed, and the
      ones whose mtime moved are relisted (new files and new subfolders);
    - each pass also relists 1/120 of all folders, so an overwrite in a cold folder shows up within ~10 min."""

    def __init__(self, cfg, mentions, labels):
        self.cfg, self.mentions, self.labels = cfg, mentions, labels
        self.base = os.path.realpath(os.path.expanduser(cfg["base"]))
        self.hours = float(cfg["hours"])
        self.roots: list[str] = []
        self.dirs: dict[str, float] = {}  # folder -> its mtime when last listed
        self.depth: dict[str, int] = {}
        self.entries: dict[str, dict] = {}  # folder -> {name: (mtime, size)} of its recent media files
        self.hot: dict[str, float] = {}  # folder -> relisted every pass until then
        self.rot = self.passes = 0
        self.roots_at = 0.0
        self.ready = False
        self.dirty = True
        self.built_at = 0.0
        self._lock, self._cache = threading.RLock(), {}
        self.version = ""
        self._last = None

    def cut(self):
        return time.time() - self.hours * 3600

    def _list(self, d, cut, now):
        """Relist one folder; returns its new subfolders."""
        try:
            m = os.stat(d).st_mtime
            it = list(os.scandir(d))
        except OSError:
            self._forget(d)
            return []
        self.dirs[d] = m
        new_dirs, recent = [], {}
        depth = self.depth.get(d, 0)
        for e in it:
            name = e.name
            if name[:1] == ".":
                continue
            try:
                if e.is_dir(follow_symlinks=False):
                    if name not in SKIP_DIRS and e.path not in self.dirs and depth < 12:
                        self.depth[e.path] = depth + 1
                        new_dirs.append(e.path)
                    continue
                if os.path.splitext(name)[1].lower() not in MEDIA:
                    continue
                st = e.stat()
            except OSError:
                continue
            if st.st_mtime >= cut:
                recent[name] = (st.st_mtime, st.st_size)
        if recent:
            if now - max(v[0] for v in recent.values()) < 900:
                self.hot[d] = now + 900
        if recent != self.entries.get(d, {}):
            self.dirty = True
            if recent:
                self.entries[d] = recent
            else:
                self.entries.pop(d, None)
        return new_dirs

    def _forget(self, d):
        for x in [x for x in self.dirs if x == d or x.startswith(d + os.sep)]:
            self.dirs.pop(x, None)
            self.depth.pop(x, None)
            self.hot.pop(x, None)
            if self.entries.pop(x, None):
                self.dirty = True

    def _walk(self, start, cut, now):
        todo = [start]
        while todo:
            todo.extend(self._list(todo.pop(), cut, now))

    def scan(self):
        with self._lock:
            now = time.time()
            cut = self.cut()
            self.passes += 1
            if now - self.roots_at > 60:
                self.roots_at = now
                roots = expand_roots(self.cfg)
                for r in self.roots:
                    if r not in roots:
                        self._forget(r)
                for r in roots:
                    if r not in self.dirs:
                        self.depth[r] = 0
                        self._walk(r, cut, now)
                self.roots = roots
            done = set()
            for d in [d for d, until in self.hot.items() if until >= now]:
                self._walk_new(d, cut, now, done)
            for d in [d for d, until in self.hot.items() if until < now]:
                self.hot.pop(d)
            if self.passes % 3 == 1:
                for d, seen in list(self.dirs.items()):
                    if d in done or (seen < cut and self.depth.get(d, 0) > 2):
                        continue
                    try:
                        m = os.stat(d).st_mtime
                    except OSError:
                        self._forget(d)
                        continue
                    if m != seen:
                        self.hot[d] = now + 900
                        self._walk_new(d, cut, now, done)
            dirs = list(self.dirs)
            n = max(1, len(dirs) // 120)
            start = self.rot % max(1, len(dirs))
            for d in dirs[start:start + n]:
                if d not in done:
                    self._walk_new(d, cut, now, done)
            self.rot = start + n
            for d, ent in list(self.entries.items()):
                if any(m < cut for m, _ in ent.values()):
                    self.entries[d] = {k: v for k, v in ent.items() if v[0] >= cut}
                    self.dirty = True
            self.ready = True

    def _walk_new(self, d, cut, now, done):
        done.add(d)
        for nd in self._list(d, cut, now):
            self._walk(nd, cut, now)

    @_cached(5)
    def items(self):
        self.scan()
        if self._last and not self.dirty and time.time() - self.built_at < 30:
            return self._last
        self.dirty, self.built_at = False, time.time()
        files = sorted(((os.path.join(d, n), v) for d, ent in self.entries.items() for n, v in ent.items()),
                       key=lambda kv: kv[1][0])
        by_project: dict[str, list] = {}
        for path, (m, size) in files:
            by_project.setdefault(project_of(path, self.base), []).append((path, m, size))
        cards = []
        n, window = BULK
        for project, lst in by_project.items():
            times = [m for _, m, _ in lst]
            bulk = [False] * len(lst)
            lo = hi = 0
            for i, t in enumerate(times):
                while times[lo] < t - window:
                    lo += 1
                while hi < len(times) and times[hi] <= t + window:
                    hi += 1
                bulk[i] = hi - lo >= n
            group = None
            for (path, m, size), b in zip(lst, bulk):
                if b:
                    if group and m - group["time"] <= window * 2:
                        group["count"] += 1
                        group["time"] = m
                        if kind_of(path) == "image":
                            group["path"] = path
                        continue
                    group = {"batch": True, "count": 1, "time": m, "path": path, "project": project,
                             "folder": os.path.relpath(os.path.dirname(path), self.base)}
                    cards.append(group)
                    continue
                group = None
                cards.append({"path": path, "time": m, "size": size, "project": project})
        cards.sort(key=lambda c: -c["time"])
        cards = cards[:6000]
        for c in cards:
            c["kind"] = kind_of(c["path"])
            c["name"] = os.path.basename(c["path"])
            c["rel"] = os.path.relpath(c["path"], self.base) if c["path"].startswith(self.base + os.sep) else c["path"]
            c["thumb"] = thumb_source(c["path"]) is not None or c["kind"] in ("image", "video")
            if c.get("batch"):
                c["kind"] = "batch"
                continue
            agent, sure = self.mentions.who(c["path"], c["time"])
            if agent:
                lab = self.labels.get(agent) or {}
                c["agent"] = lab.get("agent") or agent[:8]
                c["session"] = lab.get("session") or ""
                c["sure"] = sure
        self.version = hashlib.sha1(json.dumps([(c["path"], c["time"], c.get("count"), c.get("agent")) for c in cards])
                                    .encode()).hexdigest()[:12]
        self._last = {"version": self.version, "items": cards, "ready": self.ready, "roots": len(self.roots),
                      "folders": len(self.dirs)}
        return self._last


# --------------------------------------------------------------------------- thumbnails and reviews

THUMBS = Path(os.environ.get("WISE_STUDIO_CACHE", "~/.cache/wisecraft/studio")).expanduser()


def thumb_source(path: str):
    """The picture a card shows: the file itself, or for a model or a video an image beside it with the same stem."""
    ext = os.path.splitext(path)[1].lower()
    if ext in IMAGE:
        return path
    stem = os.path.splitext(path)[0]
    for e in (".png", ".jpg", ".jpeg", ".webp"):
        if os.path.isfile(stem + e):
            return stem + e
    return None


def make_thumb(path: Path, width=360) -> bytes | None:
    st = path.stat()
    key = hashlib.sha1(f"{path}|{st.st_mtime}|{st.st_size}|{width}".encode()).hexdigest()
    out = THUMBS / key[:2] / (key + ".jpg")
    if out.is_file():
        return out.read_bytes()
    src = thumb_source(str(path))
    data = None
    if src:
        try:
            from PIL import Image
            with Image.open(src) as im:
                im.seek(0)
                im.draft("RGB", (width * 2, width * 4))
                im = im.convert("RGBA")
                im.thumbnail((width, width * 3))
                bg = Image.new("RGB", im.size, (17, 19, 24))
                bg.paste(im, mask=im.split()[3])
                buf = io.BytesIO()
                bg.save(buf, "JPEG", quality=78)
                data = buf.getvalue()
        except Exception:
            data = None
    elif kind_of(path) == "video" and shutil.which("ffmpeg"):
        try:
            r = subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-ss", "0.5", "-i", str(path), "-frames:v", "1", "-an",
                                "-vf", f"scale={width}:-2", "-f", "image2", "-c:v", "mjpeg", "-q:v", "6", "-"],
                               capture_output=True, timeout=15)
            data = r.stdout if r.returncode == 0 and r.stdout else None
        except (OSError, subprocess.TimeoutExpired):
            data = None
    if data:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
    return data


class Reviews:
    def __init__(self, path):
        self.path = Path(path).expanduser()
        self._lock = threading.Lock()
        self._mt, self._last = None, {}

    def add(self, path: str, verdict: str, note: str, project: str):
        row = {"time": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"), "path": path,
               "verdict": verdict, "note": note, "project": project}
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return row

    def stamp(self):
        try:
            return int(self.path.stat().st_mtime * 1000) % 100000000
        except OSError:
            return 0

    def latest(self):
        try:
            mt = self.path.stat().st_mtime
        except OSError:
            return {}
        if mt != self._mt:
            last = {}
            for line in self.path.read_text(encoding="utf-8", errors="replace").splitlines():
                try:
                    r = json.loads(line)
                    last[r["path"]] = {"verdict": r.get("verdict"), "note": r.get("note", ""), "time": r.get("time")}
                except (ValueError, KeyError, TypeError):
                    continue
            self._mt, self._last = mt, last
        return self._last


# --------------------------------------------------------------------------- the server

class Studio:
    def __init__(self, cfg, port):
        self.cfg, self.port = cfg, port
        self.mentions = Mentions()
        self.agents = Agents(cfg, self.mentions)
        self.feed = Feed(cfg, self.mentions, self.agents.labels)
        self.reviews = Reviews(cfg["reviews"])

    def warm(self):
        try:
            self.agents.claude()
            self.agents.codex()
            self.feed.items()
        except Exception as e:  # a bad transcript must not stop the server
            print(f"studio: warm-up: {e}", file=sys.stderr)


class Handler(BaseHTTPRequestHandler):
    studio: Studio = None
    server_version = "wisecraft-studio"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        pass

    def _host_ok(self):
        host = (self.headers.get("Host") or "").split(":")[0]
        origin = self.headers.get("Origin")
        if host not in ("127.0.0.1", "localhost"):
            return False
        if origin and urllib.parse.urlparse(origin).hostname not in ("127.0.0.1", "localhost"):
            return False
        return True

    def _send(self, code, body: bytes, ctype="application/json", extra=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj, ensure_ascii=False).encode(), extra={"Cache-Control": "no-store"})

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        if not self._host_ok():
            return self._send(403, b'{"error":"forbidden host"}')
        u = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(u.query)
        one = lambda k: (q.get(k) or [""])[0]
        s = self.studio
        try:
            if u.path in ("/", "/index.html"):
                return self._send(200, PAGE.read_bytes(), "text/html; charset=utf-8", {"Cache-Control": "no-store"})
            if u.path == "/api/ping":
                return self._json({"studio": "wisecraft", "pid": os.getpid()})
            if u.path == "/api/state":
                st = s.agents.state()
                st["feed"] = f"{s.feed.version}-{s.reviews.stamp()}"
                st["now"] = time.time()
                return self._json(st)
            if u.path == "/api/feed":
                f = s.feed.items()
                rev = s.reviews.latest()
                version = f"{f['version']}-{s.reviews.stamp()}"
                if one("v") and one("v") == version:
                    return self._json({"version": version, "same": True})
                kind, project = one("kind"), one("project")
                try:
                    limit = max(1, min(int(one("limit") or 40), 6000))
                except ValueError:
                    limit = 40
                projects: dict[str, int] = {}
                picked = []
                for c in f["items"]:
                    projects[c["project"]] = projects.get(c["project"], 0) + 1
                    if project and c["project"] != project:
                        continue
                    if kind and kind != "all" and c["kind"] != kind and not (kind == "image" and c["kind"] == "batch"):
                        continue
                    picked.append(c)
                return self._json({"version": version, "total": len(picked), "all": len(f["items"]), "projects": projects,
                                   "ready": f["ready"], "folders": f["folders"],
                                   "items": [dict(c, review=rev.get(c["path"])) for c in picked[:limit]]})
            if u.path == "/api/reviews":
                return self._json(s.reviews.latest())
            if u.path == "/api/mailbox":
                m = s.agents.mailbox()
                return self._json({"messages": m, "available": m is not None})
            if u.path == "/api/term":
                lines = term_preview(one("h"))
                return self._json({"lines": lines}) if lines is not None else self._json({"error": "bad handle"}, 400)
            if u.path in ("/file", "/thumb"):
                p = guard(one("p"), s.feed.roots or expand_roots(s.cfg))
                if not p:
                    return self._send(404, b'{"error":"not in a watched folder"}')
                if u.path == "/thumb":
                    data = make_thumb(p)
                    if not data:
                        return self._send(404, b'{"error":"no thumbnail"}')
                    return self._send(200, data, "image/jpeg", {"Cache-Control": "private, max-age=86400"})
                return self._file(p)
            return self._send(404, b'{"error":"not found"}')
        except (BrokenPipeError, ConnectionResetError):
            return None

    def _file(self, p: Path):
        size = p.stat().st_size
        ctype = MIME.get(p.suffix.lower(), "application/octet-stream")
        rng = re.fullmatch(r"bytes=(\d*)-(\d*)", self.headers.get("Range") or "")
        start, end = 0, size - 1
        if rng and (rng.group(1) or rng.group(2)):
            if rng.group(1):
                start = int(rng.group(1))
                end = min(int(rng.group(2)), size - 1) if rng.group(2) else size - 1
            else:
                start = max(0, size - int(rng.group(2)))
            if start > end or start >= size:
                return self._send(416, b"", ctype, {"Content-Range": f"bytes */{size}"})
        length = end - start + 1
        self.send_response(206 if rng and (rng.group(1) or rng.group(2)) else 200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(length))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Cache-Control", "private, max-age=60")
        self.send_header("X-Content-Type-Options", "nosniff")
        if rng and (rng.group(1) or rng.group(2)):
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.end_headers()
        if self.command == "HEAD":
            return
        with p.open("rb") as f:
            f.seek(start)
            left = length
            while left > 0:
                chunk = f.read(min(1 << 20, left))
                if not chunk:
                    break
                self.wfile.write(chunk)
                left -= len(chunk)

    def do_POST(self):
        if not self._host_ok():
            return self._send(403, b'{"error":"forbidden host"}')
        if urllib.parse.urlparse(self.path).path != "/api/review":
            return self._send(404, b'{"error":"not found"}')
        if "application/json" not in (self.headers.get("Content-Type") or ""):
            return self._send(415, b'{"error":"json only"}')
        n = int(self.headers.get("Content-Length") or 0)
        if n <= 0 or n > 8192:
            return self._send(413, b'{"error":"too large"}')
        try:
            body = json.loads(self.rfile.read(n))
        except ValueError:
            return self._send(400, b'{"error":"bad json"}')
        s = self.studio
        p = guard(body.get("path"), s.feed.roots or expand_roots(s.cfg))
        verdict = body.get("verdict")
        if not p or verdict not in ("up", "down", "note"):
            return self._send(400, b'{"error":"path must be a watched file; verdict up, down or note"}')
        note = " ".join(str(body.get("note") or "").split())[:500]
        row = s.reviews.add(str(p), verdict, note, project_of(str(p), s.feed.base))
        return self._json(row)


def already_running(port) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/ping", timeout=1.5) as r:
            return json.loads(r.read()).get("studio") == "wisecraft"
    except (OSError, ValueError):
        return False


def open_in_orca(url):
    exe = shutil.which("orca")
    if not exe:
        print(f"open {url} in a browser pane (no `orca` on PATH)")
        return
    cmd = [exe, "tab", "create", "--url", url]
    if os.environ.get("ORCA_WORKTREE_ID"):  # the pane of the terminal that ran this, not whichever worktree is in front
        cmd += ["--worktree", "id:" + os.environ["ORCA_WORKTREE_ID"]]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    print(f"opened in Orca's browser pane: {url}" if r.returncode == 0 else f"orca tab create failed; open {url} yourself")


def main(a):
    cfg = load_config(a.config)
    if a.hours:
        cfg["hours"] = a.hours
    if a.print_config:
        roots = expand_roots(cfg)
        print(f"config:  {cfg['_file']}{'' if Path(cfg['_file']).is_file() else ' (not there; defaults)'}")
        print(f"base:    {cfg['base']}")
        print(f"roots:   {', '.join(cfg['roots'])}  ->  {len(roots)} folder(s)")
        for r in roots[:40]:
            print(f"  {r}")
        print(f"reviews: {Path(cfg['reviews']).expanduser()}")
        print(f"hours:   {cfg['hours']}")
        return
    url = f"http://127.0.0.1:{a.port}"
    if already_running(a.port):
        print(f"a studio already runs at {url}")
        if a.open:
            open_in_orca(url)
        return
    studio = Studio(cfg, a.port)
    Handler.studio = studio
    try:
        httpd = ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    except OSError as e:
        print(f"port {a.port} is in use ({e.strerror}); pass --port", file=sys.stderr)
        sys.exit(2)
    httpd.daemon_threads = True
    threading.Thread(target=studio.warm, daemon=True).start()
    print(f"wisecraft studio: {url}  (pid {os.getpid()}, last {cfg['hours']} h, Ctrl-C to stop)", flush=True)
    if a.open:
        threading.Timer(0.3, open_in_orca, args=(url,)).start()
    try:
        httpd.serve_forever(poll_interval=1.0)
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


def register(sub):
    p = sub.add_parser("studio", help="a live side panel: every agent at work and a feed of their screenshots, videos and models",
                       description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--port", type=int, default=5480, help="port on 127.0.0.1 (default 5480)")
    p.add_argument("--open", action="store_true", help="also open it in Orca's browser pane (orca tab create)")
    p.add_argument("--hours", type=float, help="show the last N hours (default 8, or the config's)")
    p.add_argument("--config", metavar="FILE", help="studio config JSON (default ~/.config/wisecraft/studio.json)")
    p.add_argument("--print-config", action="store_true", help="print the config, the watched folders and the reviews file")
    p.set_defaults(func=main)
