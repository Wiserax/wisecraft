# Ported from Universal Modder (https://github.com/rehan-remade/universal-modder), um/common.py.
# Copyright (c) 2026 Rehan and universal-modder contributors. MIT License; see LICENSE and NOTICE.
"""Small helpers shared by the subcommands: subprocess, output, sizes, the per-user data folder."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # the repo or plugin root (knowledge/, skills/ live here in a clone)
JS = Path(__file__).resolve().parent / "js"  # node scripts the CLI drives (Playwright harness, board renderer)


def is_windows() -> bool:
    return os.name == "nt"


def is_mac() -> bool:
    return sys.platform == "darwin"


def data_dir() -> Path:
    """Per-user state: the cached knowledge base, QA output defaults. Override with WZ_HOME."""
    d = Path(os.environ.get("WZ_HOME", Path.home() / ".wizerax"))
    d.mkdir(parents=True, exist_ok=True)
    return d


def run(cmd: list[str], check: bool = True, capture: bool = True, timeout: float | None = None, **kw) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(cmd, check=check, capture_output=capture, text=True, timeout=timeout, **kw)
    except FileNotFoundError:
        die(f"not found: {cmd[0]}")
    except subprocess.CalledProcessError as e:
        die(f"{' '.join(map(str, cmd[:3]))}... failed ({e.returncode}):\n{(e.stderr or e.stdout or '').strip()[-2000:]}")


def die(msg: str, code: int = 1):
    print(f"wz: {msg}", file=sys.stderr)
    sys.exit(code)


def emit(obj, as_json: bool = False):
    if as_json or not isinstance(obj, str):
        print(json.dumps(obj, indent=2, default=str))
    else:
        print(obj)


def parse_size(s: str) -> tuple[int, int]:
    """'390x844' -> (390, 844); '128' -> (128, 128)."""
    if "x" in s.lower():
        w, h = s.lower().split("x", 1)
        return int(w), int(h)
    return int(s), int(s)


def need(module: str, pip_name: str | None = None):
    try:
        return __import__(module)
    except ImportError:
        die(f"this command needs {pip_name or module}: `pip install {pip_name or module}` (or run through bin/wz, which uses uv)")


def need_tool(name: str, hint: str = "") -> str:
    """Path of an external program (ffmpeg, ffprobe, node), or exit with how to get it."""
    found = shutil.which(name)
    if not found:
        die(f"{name} not found on PATH{': ' + hint if hint else ''}")
    return found
