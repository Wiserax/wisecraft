#!/usr/bin/env python3
"""Token, cost and time per Claude Code subagent, read from the session transcripts.

Usage:
  agents.py [--hours 8] [--json] <session dir or project dir> ...

A session dir is ~/.claude/projects/<project>/<session-id> (it holds subagents/).
A project dir is ~/.claude/projects/<project>; its most recently active session is used.
Cost is the API list-price equivalent (a subscription pays a flat fee); edit PRICES if yours differ.
"""
import json
import sys
import time
from datetime import datetime
from pathlib import Path

# $ per million tokens: input, output, cache read, cache write (5 min), cache write (1 h)
PRICES = {
    "opus": (5.0, 25.0, 0.50, 6.25, 10.0),
    "sonnet": (3.0, 15.0, 0.30, 3.75, 6.0),
    "haiku": (1.0, 5.0, 0.10, 1.25, 2.0),
}
RUNNING_IF_WRITTEN_WITHIN = 180  # seconds


def price_for(model):
    for key, p in PRICES.items():
        if key in (model or ""):
            return p
    return PRICES["opus"]


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def read_transcript(path, since=0):
    seen, tokens, cost = set(), 0, 0.0
    first = last = None
    model, stop, last_tool = None, None, False
    for line in path.open(errors="replace"):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("timestamp"):
            t = ts(d["timestamp"])
            if t < since:
                continue
            first = first or t
            last = t
        elif first is None:
            continue
        m = d.get("message")
        if d.get("type") != "assistant" or not isinstance(m, dict):
            continue
        content = m.get("content") if isinstance(m.get("content"), list) else []
        if any(c.get("type") == "tool_use" for c in content):
            last_tool = True
        if m.get("stop_reason"):
            stop = m["stop_reason"]
            last_tool = stop == "tool_use"
        u, rid = m.get("usage"), d.get("requestId")
        if not u or rid in seen:
            continue
        seen.add(rid)
        model = m.get("model") or model
        pin, pout, pread, pw5, pw1h = price_for(model)
        cc = u.get("cache_creation") or {}
        w1h = cc.get("ephemeral_1h_input_tokens", 0)
        w5 = u.get("cache_creation_input_tokens", 0) - w1h
        parts = (u.get("input_tokens", 0), u.get("output_tokens", 0), u.get("cache_read_input_tokens", 0), w5, w1h)
        tokens += sum(parts)
        cost += sum(n * p for n, p in zip(parts, (pin, pout, pread, pw5, pw1h))) / 1e6
    return {"tokens": tokens, "cost": cost, "first": first, "last": last, "model": model, "stop": stop, "last_tool": last_tool}


def session_dirs(arg):
    p = Path(arg).expanduser()
    if (p / "subagents").is_dir() or p.with_suffix(".jsonl").exists():
        return [p]
    sessions = [d for d in p.iterdir() if d.is_dir() and (d / "subagents").is_dir()]
    return sorted(sessions, key=lambda d: d.stat().st_mtime)[-1:]


def main(argv):
    hours, as_json, args = 8.0, False, []
    it = iter(argv)
    for a in it:
        if a == "--hours":
            hours = float(next(it))
        elif a == "--json":
            as_json = True
        else:
            args.append(a)
    now, rows = time.time(), []
    for arg in args:
        for sess in session_dirs(arg):
            main_log = sess.with_suffix(".jsonl")
            files = [("main", main_log, "lead session")] if main_log.exists() else []
            for f in sorted((sess / "subagents").glob("agent-*.jsonl")):
                meta = f.with_name(f.name.replace(".jsonl", ".meta.json"))
                desc = json.loads(meta.read_text()).get("description", "") if meta.exists() else ""
                files.append((f.stem.replace("agent-", ""), f, desc))
            for aid, f, desc in files:
                if now - f.stat().st_mtime > hours * 3600:
                    continue
                r = read_transcript(f, now - hours * 3600)
                if not r["first"]:
                    continue
                fresh = now - f.stat().st_mtime < RUNNING_IF_WRITTEN_WITHIN
                state = "running" if fresh else "done" if r["stop"] == "end_turn" else "stopped"
                rows.append({"session": sess.name[:8], "id": aid, "desc": desc, "state": state,
                             "minutes": round((r["last"] - r["first"]) / 60), "tokens": r["tokens"],
                             "cost": round(r["cost"], 2), "model": r["model"]})
    if as_json:
        print(json.dumps(rows, indent=1))
        return
    for r in rows:
        print(f"{r['session']}  {r['state']:7}  {r['minutes']:4}m  {r['tokens'] / 1e6:6.2f}M tok  ${r['cost']:7.2f}  {r['desc']}")
    if rows:
        print(f"total: {sum(r['tokens'] for r in rows) / 1e6:.1f}M tokens, ${sum(r['cost'] for r in rows):.2f} API-equivalent")


if __name__ == "__main__":
    main(sys.argv[1:])
