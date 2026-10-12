# Ported from Universal Modder (https://github.com/rehan-remade/universal-modder), um/cli.py.
# Copyright (c) 2026 Rehan and universal-modder contributors. MIT License; see LICENSE and NOTICE.
"""`wise` command line: one entry point for every tool, so skills can say `wise <group> <cmd>`."""
from __future__ import annotations

import argparse
import importlib
import sys

from wisecraft import __doc__ as DOC, __version__

GROUPS = ["scan", "qa", "board", "music-enhance", "video"]


def main(argv=None):
    # notes and game titles are UTF-8; a cp1252 console must not crash on them
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass
    ap = argparse.ArgumentParser(prog="wise", description=DOC, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", action="version", version=f"wisecraft {__version__}")
    sub = ap.add_subparsers(dest="group", metavar="<group>")
    for g in GROUPS:
        importlib.import_module(f"wisecraft.{g.replace('-', '_')}").register(sub)
    args = ap.parse_args(argv)
    if not getattr(args, "func", None):
        # a group without a command: show that group's help
        if args.group:
            ap.parse_args([args.group, "--help"])
        ap.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
