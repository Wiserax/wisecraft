#!/usr/bin/env python3
"""Read a faucet/sink ledger (assets/economy-model.template.csv) and print the balance per period and currency.

    python3 economy_ledger.py ledger.csv
    python3 economy_ledger.py ledger.csv --soft coins --budget gems=40-90 --save-limit 0.3 --dead-sink 0.02
    python3 economy_ledger.py ledger.csv --json

The CSV has one row per flow: period,currency,flow,source,amount[,note]. flow is "faucet" (the player gets it)
or "sink" (the player spends it). Periods are kept in the order they first appear (D1..D7, ch1..ch10, anything).
The ledger describes one kind of player (say, an engaged player who plays 3 sessions a day); write one per kind.

For every currency it prints faucet, sink, net and the running balance per period, and flags:
  - saving: a period whose net keeps more than --save-limit of what came in (default 0.3). For a soft currency,
    several in a row mean the sinks stopped keeping up (inflation: prices stop meaning anything). With --soft,
    saving and growing are checked only for the listed currencies: saving up a hard currency for a pull is normal;
  - growing: the balance rose in each of the last 3 periods or more and is now more than the last period's
    spending (a small buffer is healthy; a hoard the sinks can't absorb is not);
  - debt: the running balance went below zero (the plan spends money the player does not have);
  - dead sink: a sink that takes less than --dead-sink of that currency's spending (default 0.02);
  - budget: --budget CUR=MIN-MAX checks the total faucet of a currency per period (a premium budget).
Exit 0 with no flags, 1 with flags, 2 on a usage error. Standard library only.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys


def load(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    need = {"period", "currency", "flow", "source", "amount"}
    if not rows or not need <= set(rows[0]):
        raise ValueError(f"the header must have {', '.join(sorted(need))}")
    for i, r in enumerate(rows, 2):
        if r["flow"] not in ("faucet", "sink"):
            raise ValueError(f"line {i}: flow must be faucet or sink, not {r['flow']!r}")
        r["amount"] = float(r["amount"])
    return rows


def ledger(rows: list[dict], save_limit: float, dead: float, budgets: dict, soft: list[str] | None = None) -> dict:
    periods = list(dict.fromkeys(r["period"] for r in rows))
    out = {"periods": periods, "currencies": {}, "flags": []}
    for cur in dict.fromkeys(r["currency"] for r in rows):
        rs = [r for r in rows if r["currency"] == cur]
        table, bal, rising = [], 0.0, 0
        watch = not soft or cur in soft     # saving and growing are soft-currency flags; saving up gems is normal
        for p in periods:
            fa = sum(r["amount"] for r in rs if r["period"] == p and r["flow"] == "faucet")
            si = sum(r["amount"] for r in rs if r["period"] == p and r["flow"] == "sink")
            net = fa - si
            bal += net
            kept = net / fa if fa else 0.0
            table.append({"period": p, "faucet": fa, "sink": si, "net": net, "balance": bal, "kept": round(kept, 3)})
            if watch and fa and kept > save_limit:
                out["flags"].append({"currency": cur, "period": p, "flag": "saving", "why": f"keeps {100 * kept:.0f}% of what came in (limit {100 * save_limit:.0f}%)"})
            if bal < 0:
                out["flags"].append({"currency": cur, "period": p, "flag": "debt", "why": f"balance {bal:,.0f}: the plan spends more than the player has"})
            rising = rising + 1 if net > 0 else 0
            if cur in budgets:
                lo, hi = budgets[cur]
                if not lo <= fa <= hi:
                    out["flags"].append({"currency": cur, "period": p, "flag": "budget", "why": f"faucet {fa:,.0f} outside {lo:,.0f}-{hi:,.0f}"})
        last_sink = table[-1]["sink"] if table else 0.0
        if watch and rising >= 3 and bal > last_sink:
            out["flags"].append({"currency": cur, "period": periods[-1], "flag": "growing",
                                 "why": f"the balance rose in each of the last {rising} periods and holds {bal:,.0f}, more than a period's spending ({last_sink:,.0f})"})
        spend = sum(r["amount"] for r in rs if r["flow"] == "sink")
        sources = {}
        for r in rs:
            key = (r["flow"], r["source"])
            sources[key] = sources.get(key, 0.0) + r["amount"]
        for (flow, src), amt in sources.items():
            if flow == "sink" and spend and amt / spend < dead:
                out["flags"].append({"currency": cur, "period": "all", "flag": "dead sink", "why": f"{src} takes {100 * amt / spend:.1f}% of the spending"})
        out["currencies"][cur] = {"table": table, "sources": [{"flow": f, "source": s, "total": a} for (f, s), a in sources.items()]}
    out["ok"] = not out["flags"]
    return out


def show(r: dict) -> str:
    L = []
    for cur, c in r["currencies"].items():
        L += [f"{cur}", f"  {'period':<8}{'faucet':>10}{'sink':>10}{'net':>10}{'balance':>10}{'kept':>7}"]
        L += [f"  {t['period']:<8}{t['faucet']:>10,.0f}{t['sink']:>10,.0f}{t['net']:>10,.0f}{t['balance']:>10,.0f}{100 * t['kept']:>6.0f}%" for t in c["table"]]
        fa = sum(s["total"] for s in c["sources"] if s["flow"] == "faucet") or 1
        si = sum(s["total"] for s in c["sources"] if s["flow"] == "sink") or 1
        L.append("  sources: " + ", ".join(f"{s['source']} {100 * s['total'] / (fa if s['flow'] == 'faucet' else si):.0f}%"
                                           for s in c["sources"] if s["flow"] == "faucet"))
        L.append("  sinks:   " + ", ".join(f"{s['source']} {100 * s['total'] / si:.0f}%" for s in c["sources"] if s["flow"] == "sink"))
        L.append("")
    L.append("flags:" if r["flags"] else "flags: none")
    L += [f"  {f['currency']} {f['period']}: {f['flag']}: {f['why']}" for f in r["flags"]]
    return "\n".join(L)


def parse_budgets(items: list[str]) -> dict:
    out = {}
    for s in items or []:
        cur, rng = s.split("=", 1)
        lo, hi = rng.split("-", 1)
        out[cur] = (float(lo), float(hi))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ledger")
    ap.add_argument("--save-limit", type=float, default=0.3)
    ap.add_argument("--dead-sink", type=float, default=0.02)
    ap.add_argument("--budget", action="append", metavar="CUR=MIN-MAX")
    ap.add_argument("--soft", action="append", metavar="CUR", help="the soft currencies: saving and growing are checked only for these (default: all)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    try:
        r = ledger(load(a.ledger), a.save_limit, a.dead_sink, parse_budgets(a.budget), a.soft)
    except (OSError, ValueError) as e:
        print(f"economy_ledger: {e}", file=sys.stderr)
        sys.exit(2)
    print(json.dumps(r, indent=2) if a.json else show(r))
    sys.exit(0 if r["ok"] else 1)


if __name__ == "__main__":
    main()
