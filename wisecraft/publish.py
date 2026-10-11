# Ported from Universal Modder (https://github.com/rehan-remade/universal-modder), um/publish.py.
# Copyright (c) 2026 Rehan and universal-modder contributors. MIT License; see LICENSE and NOTICE.
"""Check a folder before it goes public: no keys, no .env, no private deploy URLs, no names you must not leak.

    wise publish check .                              # the repo you are about to push or open-source
    wise publish check ./site --max-mb 2              # a build you are about to upload
    wise publish check . --deny ~/private/names.txt   # names that must not appear (clients, unreleased titles)

FAIL  leaked keys and tokens (Anthropic, OpenAI, GitHub, AWS, Google, Stripe live, Slack, Vercel, PostHog
      personal, fal, private key blocks), .env files, private preview or deploy URLs
      (https://<name>.vercel.app, *.netlify.app, *.pages.dev, *.ngrok*), any term from the denylist
      (in a text file or in a file path)
WARN  files over --max-mb (default 5), absolute user paths (/Users/<name>/, C:\\Users\\<name>\\), no README,
      no LICENSE

Denylist: one term per line, "#" starts a comment. It is read from --deny FILE, else from
<dir>/.wise-denylist, else from $WISE_DENY (comma-separated). Matching ignores case and finds the term anywhere
in a line, so "foocorp" also catches "FooCorp-internal". The report names the file, the line and the term,
never the line's text. The denylist file itself and .git/ .venv/ node_modules/ dist/ are not read.

Not flagged on purpose: PostHog project keys (phc_...) are public by design, and loopback URLs
(http://127.0.0.1:5173, localhost) are normal in command examples. .env.example is read like any text file.
Exit status is 1 on any FAIL. It is a lint, not a guarantee: read the diff before you push.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

from wisecraft.common import die

SECRET_PATTERNS = [
    ("fal key", re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}:[0-9a-f]{32}\b")),
    ("FAL_KEY assignment", re.compile(r"FAL_KEY\s*[=:]\s*['\"]?[A-Za-z0-9:_\-]{20,}")),
    ("Anthropic key", re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}")),
    # project, service-account and admin keys carry - and _ in their body; legacy keys are plain alphanumerics
    ("OpenAI key", re.compile(r"\bsk-(?:(?:proj|svcacct|admin)-[A-Za-z0-9_\-]{32,}|[A-Za-z0-9]{32,})")),
    # classic tokens (ghp_, gho_, ...) and fine-grained personal access tokens (github_pat_)
    ("GitHub token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{60,})")),
    ("AWS key id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("private key", re.compile(r"-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY(?: BLOCK)?-----")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}")),
    # secret (sk_) and restricted (rk_) live keys; test keys and publishable pk_ keys are not secrets
    ("Stripe live key", re.compile(r"\b[sr]k_live_[A-Za-z0-9]{16,}")),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9\-]{10,}")),
    # prefixed tokens (personal, integration, app, refresh, gateway) and Blob read-write tokens
    ("Vercel token", re.compile(r"\b(?:vc[paikr]_[A-Za-z0-9_\-]{24,}|vercel_blob_rw_[A-Za-z0-9_]{20,})")),
    # older Vercel tokens are 24 plain characters, so only the assignment gives them away
    ("Vercel token assignment", re.compile(r"VERCEL_(?:[A-Z]+_)*TOKEN\s*[=:]\s*['\"]?[A-Za-z0-9_\-]{20,}")),
    # phx_ is a personal API key (full account access); phc_ project keys ship in every client and are not flagged
    ("PostHog personal API key", re.compile(r"\bphx_[A-Za-z0-9]{30,}")),
]
_HOST = r"(?:https?://)?(?<![A-Za-z0-9.\-<*{$])[A-Za-z0-9][A-Za-z0-9.\-]*"
PRIVATE_URL_PATTERNS = [
    ("Vercel deploy URL", re.compile(_HOST + r"\.vercel\.app\b", re.I)),
    ("Netlify deploy URL", re.compile(_HOST + r"\.netlify\.app\b", re.I)),
    ("Cloudflare Pages URL", re.compile(_HOST + r"\.pages\.dev\b", re.I)),
    ("ngrok tunnel URL", re.compile(_HOST + r"\.ngrok(?:-free)?\.(?:io|app|dev|pizza)\b", re.I)),
]
USER_PATH = re.compile(r"[A-Z]:\\Users\\(?!<)[^\\\s`\"']+|/home/(?!<)[a-z_][a-z0-9_-]*/|/Users/(?!<)[A-Za-z]+/")
DENY_FILE = ".wise-denylist"
MIN_TERM = 3    # a shorter term would match half the lines of any repo
SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "dist", "__pycache__", ".pytest_cache", ".vs", ".idea"}
BINARY_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif", ".ico", ".bmp", ".psd", ".mp3", ".ogg", ".wav", ".m4a", ".aac",
              ".flac", ".mp4", ".webm", ".mov", ".mkv", ".glb", ".bin", ".ktx2", ".basis", ".wasm", ".ttf", ".otf", ".woff", ".woff2",
              ".zip", ".gz", ".br", ".7z", ".pdf", ".blend", ".fbx", ".pyc", ".so", ".dylib", ".dll", ".exe"}
ENV_TEMPLATES = (".example", ".sample", ".template", ".dist")
MAX_TEXT_MB = 4   # larger files are not read as text (a bundle that size belongs in dist/, which is skipped)


def load_denylist(root: Path | None = None, deny: str | None = None) -> tuple[list[str], Path | None]:
    """The terms that must not appear, lowercased, and the file they came from (None for $WISE_DENY or no list).
    Order: --deny FILE, else <root>/.wise-denylist, else $WISE_DENY (comma-separated)."""
    src = None
    if deny:
        src = Path(deny).expanduser()
        if not src.is_file():
            die(f"no denylist file: {src}")
    elif root and (root / DENY_FILE).is_file():
        src = root / DENY_FILE
    raw = src.read_text(encoding="utf-8", errors="replace").splitlines() if src else os.environ.get("WISE_DENY", "").split(",")
    terms = []
    for line in raw:
        t = line.split("#", 1)[0].strip().lower()
        if t and t not in terms:
            terms.append(t)
    return terms, src


def match_lines(text: str, rx: re.Pattern) -> list[int]:
    """1-based numbers of the lines where rx matches."""
    return sorted({text.count("\n", 0, m.start()) + 1 for m in rx.finditer(text)})


def deny_hits(text: str, terms: list[str]) -> dict[str, list[int]]:
    """{term: [line numbers]} for every denylist term found in text (case-insensitive, anywhere in a line)."""
    low = text.lower()
    found = [t for t in terms if len(t) >= MIN_TERM and t in low]
    if not found:
        return {}
    out: dict[str, list[int]] = {}
    for n, line in enumerate(low.split("\n"), 1):
        for t in found:
            if t in line:
                out.setdefault(t, []).append(n)
    return out


def where(lines: list[int], limit: int = 8) -> str:
    """'12' or '12,40,57' (the first few, then how many more)."""
    return ",".join(map(str, lines[:limit])) + (f",+{len(lines) - limit} more" if len(lines) > limit else "")


def is_text(f: Path) -> bool:
    if f.suffix.lower() in BINARY_EXT:
        return False
    try:
        if f.stat().st_size > MAX_TEXT_MB << 20:
            return False
        with open(f, "rb") as fh:
            return b"\0" not in fh.read(4096)
    except OSError:
        return False


def is_env_file(name: str) -> bool:
    n = name.lower()
    if n.endswith(ENV_TEMPLATES):
        return False
    return n == ".env" or n.startswith(".env.") or n.endswith(".env")


def walk(root: Path) -> list[Path]:
    """Every file under root, without descending into SKIP_DIRS (node_modules can hold 100k files)."""
    out = []
    for d, dirs, names in os.walk(root):
        dirs[:] = sorted(x for x in dirs if x not in SKIP_DIRS)
        out += [Path(d) / n for n in sorted(names)]
    return out


def check(folder: str, deny: str | None = None, max_mb: float = 5.0) -> int:
    root = Path(folder)
    if not root.is_dir():
        die(f"not a folder: {root}")
    terms, deny_path = load_denylist(root, deny)
    fails, warns = [], []
    short = [t for t in terms if len(t) < MIN_TERM]
    if short:
        warns.append(f"denylist terms under {MIN_TERM} characters are ignored: {', '.join(repr(t) for t in short)}")
    deny_real = deny_path.resolve() if deny_path else None
    files = walk(root)
    for f in files:
        rel = f.relative_to(root).as_posix()        # same report on every OS (Windows would print src\main.js)
        if f.name == DENY_FILE or (deny_real and f.resolve() == deny_real):
            continue
        for t in terms:
            if len(t) >= MIN_TERM and t in rel.lower():
                fails.append(f"denylisted name {t!r} in the path {rel}")
        if is_env_file(f.name):
            fails.append(f"env file (secrets?): {rel}")
        try:
            size = f.stat().st_size
        except OSError:
            continue
        if size > max_mb * 2**20:
            warns.append(f"large file ({size / 2**20:.1f} MB, limit {max_mb:g}): {rel} - host big media elsewhere or compress it")
        if not is_text(f):
            continue
        try:
            txt = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for label, rx in SECRET_PATTERNS:
            lines = match_lines(txt, rx)
            if lines:
                fails.append(f"{label} in {rel}:{where(lines)}")
        for label, rx in PRIVATE_URL_PATTERNS:
            lines = match_lines(txt, rx)
            if lines:
                fails.append(f"private {label} in {rel}:{where(lines)}")
        for t, lines in deny_hits(txt, terms).items():
            fails.append(f"denylisted name {t!r} in {rel}:{where(lines)}")
        lines = match_lines(txt, USER_PATH)
        if lines:
            warns.append(f"absolute user path in {rel}:{where(lines)}")
    top = {p.name.lower() for p in root.iterdir() if p.is_file()}
    if not any(n.startswith("readme") for n in top):
        warns.append("no README (what it is, how to run it, credits)")
    if not any(n.startswith(("license", "licence", "copying", "unlicense")) for n in top):
        warns.append("no LICENSE (without one nobody may reuse the code)")
    for x in fails:
        print("FAIL ", x)
    for x in warns:
        print("WARN ", x)
    print(f"{'FAIL' if fails else 'WARN' if warns else 'PASS'}: {len(files)} files, {len(fails)} failures, {len(warns)} warnings")
    return 1 if fails else 0


def main(a):
    raise SystemExit(check(a.dir, a.deny, a.max_mb))


def register(sub):
    import argparse
    p = sub.add_parser("publish", help="lint a folder before it goes public (keys, .env, private URLs, denylisted names)",
                       description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    cs = p.add_subparsers(dest="cmd", metavar="<cmd>")
    q = cs.add_parser("check", help="check a folder", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    q.add_argument("dir")
    q.add_argument("--deny", metavar="FILE", help="denylist file: one term per line, # comments (default: <dir>/.wise-denylist, else $WISE_DENY)")
    q.add_argument("--max-mb", type=float, default=5.0, help="warn about files larger than this (default 5)")
    q.set_defaults(func=main)
