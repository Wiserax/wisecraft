#!/usr/bin/env python3
"""With vs without Wisecraft: run a headless agent on three small tasks and score the result with scripts.

    python3 benchmarks/run.py --dry-run                      # print the commands, run nothing
    python3 benchmarks/run.py --trials 3                     # 3 tasks x 2 arms x 3 trials = 18 agent runs
    python3 benchmarks/run.py --tasks boss-walks-in --trials 1 --arms with
    python3 benchmarks/run.py --report ~/.wisecraft/bench/<stamp>      # re-score and summarise a finished run

Each trial gets a fresh copy of examples/horde-demo in its own git repo. The "with" arm loads this plugin
(`--plugin-dir`); the "without" arm runs the same agent with skills disabled. Both get the same prompt, model and
turn limit. Afterwards benchmarks/score.mjs checks the folder (it calls the sim and reads files; it never reads
what the agent said). Results land in ~/.wisecraft/bench/<stamp>/results.json: per trial the checks, wall-clock
seconds, tokens and cost as reported by the agent CLI, and per arm the mean and standard deviation.

This spends real tokens (18 agent sessions by default). Nothing is charted until it has run: the README shows
"coming soon" while benchmarks/results.json does not exist.
"""
import argparse
import json
import os
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "benchmarks"
SPEC = json.loads((BENCH / "tasks.json").read_text())
SKIP = {"node_modules", "dist", ".git"}
# What a trial may do without asking: edit files, and run the project's own tools. Nothing else is approved, so a
# headless run cannot wander outside its copy of the game.
TOOLS = ["Read", "Edit", "Write", "Glob", "Grep", "Bash(npm test:*)", "Bash(npm run:*)", "Bash(node:*)", "Bash(wise:*)", "Bash(git:*)", "Bash(ls:*)"]


def agent_cmd(prompt: str, arm: str, a) -> list:
    cmd = [a.agent, "-p", prompt, "--output-format", "json", "--permission-mode", "acceptEdits", "--max-turns", str(a.max_turns),
           "--setting-sources", "project", "--no-session-persistence", "--allowedTools", *TOOLS]
    if a.model:
        cmd += ["--model", a.model]
    if a.max_usd:
        cmd += ["--max-budget-usd", str(a.max_usd)]
    cmd += ["--plugin-dir", str(ROOT)] if arm == "with" else ["--disable-slash-commands"]
    return cmd


def fresh_copy(dst: Path, modules: Path | None):
    shutil.copytree(ROOT / SPEC["game"], dst, ignore=lambda d, names: [n for n in names if n in SKIP])
    if modules and modules.exists():
        os.symlink(modules, dst / "node_modules")
    env = {**os.environ, "GIT_AUTHOR_NAME": "bench", "GIT_AUTHOR_EMAIL": "bench@example.com", "GIT_COMMITTER_NAME": "bench", "GIT_COMMITTER_EMAIL": "bench@example.com"}
    for args in (["init", "-q"], ["add", "-A"], ["commit", "-q", "-m", "the sample game, untouched"]):
        subprocess.run(["git", *args], cwd=dst, env=env, check=False, capture_output=True)


def score(game: Path, task: str, build: bool) -> dict:
    env = {**os.environ, "WISE": str(ROOT / "bin" / "wise")}
    r = subprocess.run(["node", str(BENCH / "score.mjs"), str(game), task, *(["--build"] if build else [])], capture_output=True, text=True, env=env)
    try:
        return json.loads(r.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError):
        return {"task": task, "checks": {}, "passed": 0, "total": 0, "error": (r.stderr or r.stdout)[-400:]}


def usage(raw: str) -> dict:
    """Tokens, cost and turns from the agent CLI's JSON result (fields it does not report stay None)."""
    try:
        j = json.loads(raw)
    except json.JSONDecodeError:
        return {"tokens": None, "cost_usd": None, "turns": None, "agent_ms": None}
    u = j.get("usage") or {}
    tokens = sum(v for k, v in u.items() if isinstance(v, int) and k in ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
    return {"tokens": tokens or None, "output_tokens": u.get("output_tokens"), "cost_usd": j.get("total_cost_usd"), "turns": j.get("num_turns"), "agent_ms": j.get("duration_ms")}


def stats(xs):
    xs = [x for x in xs if x is not None]
    if not xs:
        return None
    return {"mean": round(statistics.mean(xs), 3), "sd": round(statistics.stdev(xs), 3) if len(xs) > 1 else 0.0, "n": len(xs)}


def summarise(trials: list) -> dict:
    out = {}
    for arm in sorted({t["arm"] for t in trials}):
        rows = [t for t in trials if t["arm"] == arm]
        out[arm] = {"pass_rate": stats([t["score"]["passed"] / t["score"]["total"] for t in rows if t["score"].get("total")]),
                    "minutes": stats([t["seconds"] / 60 for t in rows if t.get("seconds")]),
                    "tokens": stats([t["usage"].get("tokens") for t in rows]),
                    "by_task": {task: stats([t["score"]["passed"] / t["score"]["total"] for t in rows if t["task"] == task and t["score"].get("total")])
                                for task in sorted({t["task"] for t in rows})}}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--trials", type=int, default=3)
    ap.add_argument("--tasks", nargs="*", help="task ids (default: all)")
    ap.add_argument("--arms", nargs="*", default=["without", "with"], choices=["with", "without"])
    ap.add_argument("--agent", default="claude", help="the headless agent CLI (default: claude)")
    ap.add_argument("--model", help="model for both arms (default: the CLI's default)")
    ap.add_argument("--max-turns", type=int, default=60)
    ap.add_argument("--timeout", type=int, default=1500, help="seconds per trial")
    ap.add_argument("--max-usd", type=float, default=4.0, help="spending cap per trial, passed to the agent CLI (0 = none)")
    ap.add_argument("--build", action="store_true", help="also run `npm run build` in the release task (needs --modules)")
    ap.add_argument("--modules", help="a node_modules folder (vite + three) to link into every copy")
    ap.add_argument("--out", help="run folder (default: ~/.wisecraft/bench/<stamp>, outside the repo)")
    ap.add_argument("--report", help="re-score a finished run folder and print its summary")
    ap.add_argument("--merge", nargs="+", help="run folders to merge into benchmarks/results.json (what the README chart reads)")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    tasks = [t for t in SPEC["tasks"] if not a.tasks or t["id"] in a.tasks]

    if a.merge:
        trials = []
        for d in a.merge:
            for t in json.loads((Path(d) / "results.json").read_text())["trials"]:
                trials.append({**t, "dir": str(Path(d).name + "/" + t["dir"])})
        meta = {"agent": a.agent, "model": a.model or "the CLI's default", "max_turns": a.max_turns, "date": time.strftime("%Y-%m-%d"),
                "trials_per_cell": max((t["trial"] for t in trials), default=0), "runs": len(trials)}
        result = {"meta": meta, "summary": summarise(trials), "trials": trials}
        (BENCH / "results.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result["summary"], indent=2))
        return 0
    if a.report:
        run = Path(a.report)
        trials = json.loads((run / "results.json").read_text())["trials"]
        for t in trials:
            t["score"] = score(run / t["dir"] / "game", t["task"], a.build)
        result = {"trials": trials, "summary": summarise(trials)}
        (run / "results.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result["summary"], indent=2))
        return 0

    # Outside the repo on purpose: a copy inside it would inherit this repo's AGENTS.md and skills in both arms.
    run = Path(a.out) if a.out else Path.home() / ".wisecraft" / "bench" / time.strftime("%Y%m%d-%H%M%S")
    plan = [(t, arm, n) for n in range(1, a.trials + 1) for t in tasks for arm in a.arms]
    print(f"{len(plan)} agent runs -> {run}")
    if a.dry_run:
        for t, arm, n in plan:
            print(f"[{t['id']} / {arm} / {n}] " + " ".join(agent_cmd("<prompt>", arm, a)))
        return 0
    trials = []
    for t, arm, n in plan:
        name = f"{t['id']}-{arm}-{n}"
        game = run / name / "game"
        game.parent.mkdir(parents=True, exist_ok=True)
        fresh_copy(game, Path(a.modules) if a.modules else None)
        t0 = time.time()
        try:
            r = subprocess.run(agent_cmd(t["prompt"], arm, a), cwd=game, capture_output=True, text=True, timeout=a.timeout)
            raw, err = r.stdout, r.stderr[-2000:]
        except subprocess.TimeoutExpired as e:
            raw, err = (e.stdout or b"").decode("utf-8", "replace") if isinstance(e.stdout, bytes) else (e.stdout or ""), "timeout"
        seconds = round(time.time() - t0, 1)
        (game.parent / "agent.json").write_text(raw or "")
        row = {"task": t["id"], "arm": arm, "trial": n, "dir": name, "seconds": seconds, "usage": usage(raw or ""), "score": score(game, t["id"], a.build), "error": err if err == "timeout" else None}
        trials.append(row)
        print(f"[{name}] {row['score'].get('passed')}/{row['score'].get('total')} checks, {seconds / 60:.1f} min, tokens {row['usage'].get('tokens')}")
        (run / "results.json").write_text(json.dumps({"trials": trials, "summary": summarise(trials)}, indent=2) + "\n")
    print(json.dumps(summarise(trials), indent=2))
    print(f"copy {run / 'results.json'} to benchmarks/results.json to publish it (see benchmarks/README.md)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
