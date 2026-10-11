#!/usr/bin/env python3
"""Copy skills/ to the places agents look for skills in a clone: .agents/skills and .claude/skills.

    python3 scripts/sync_skills.py          # copy, and drop files that no longer exist in skills/
    python3 scripts/sync_skills.py --check  # exit 1 when a copy differs (what the test runs)

They are real copies, not symlinks, so Windows clones work. Edit skills/ only.
"""
import filecmp
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "skills"
COPIES = [ROOT / ".agents" / "skills", ROOT / ".claude" / "skills"]
SKIP = {".DS_Store", "__pycache__"}


def tree(d: Path) -> dict:
    return {p.relative_to(d).as_posix(): p for p in sorted(d.rglob("*")) if p.is_file() and not (set(p.parts) & SKIP)}


def diff(copy: Path) -> list:
    src, dst = tree(SRC), tree(copy) if copy.exists() else {}
    out = [f"missing  {k}" for k in src if k not in dst]
    out += [f"stale    {k}" for k in dst if k not in src]
    out += [f"differs  {k}" for k in src if k in dst and not filecmp.cmp(src[k], dst[k], shallow=False)]
    return out


def sync(copy: Path) -> int:
    src, dst = tree(SRC), tree(copy) if copy.exists() else {}
    n = 0
    for k, p in dst.items():
        if k not in src:
            p.unlink()
            n += 1
    for k, p in src.items():
        to = copy / k
        if k not in dst or not filecmp.cmp(p, to, shallow=False):
            to.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, to)
            n += 1
    for d in sorted((x for x in copy.rglob("*") if x.is_dir()), reverse=True):
        if not any(d.iterdir()):
            d.rmdir()
    return n


def main() -> int:
    if "--check" in sys.argv[1:]:
        bad = {c: diff(c) for c in COPIES}
        for c, lines in bad.items():
            for line in lines:
                print(f"{c.relative_to(ROOT)}: {line}")
        if any(bad.values()):
            print("run: python3 scripts/sync_skills.py")
            return 1
        print("skill copies match skills/")
        return 0
    for c in COPIES:
        print(f"{c.relative_to(ROOT)}: {sync(c)} file(s) updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
