#!/usr/bin/env python3
"""Read a drop table (assets/drop-table.template.json) and print what a player gets, exactly.

    python3 drop_table.py drop-table.json            # odds, value per pull, pulls to the featured item, checks
    python3 drop_table.py drop-table.json --json     # the same as one JSON object
    python3 drop_table.py drop-table.json --pulls 10 50 100

What it computes, without simulation:
  - the base probability of every tier and item (weight / sum of weights);
  - the per-pull rate of the pity tier at each pull since the last drop (base, then the soft-pity ramp, then
    hard pity), the distribution of pulls to that tier, its mean and the consolidated rate (1 / mean);
  - the effective rate of the other tiers (they share what the pity tier leaves, by weight);
  - expected value per pull and per price unit, with and without pity;
  - pulls to the featured item (with the 50/50 and its guarantee): mean, p50, p90, p99, worst case;
  - P(at least one pity-tier drop within n pulls), with pity and without (1 - (1 - p)^n);
  - checks: positive integer weights, the disclosed percentages against the computed ones.
Exit 0 when every check passes, 1 when one fails, 2 on a usage error. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import sys


def ramp(base: float, pity: dict | None) -> list[float]:
    """Probability of the pity tier on pull k (k = 1..hard) since the last drop of it."""
    if not pity:
        return []
    soft, step, hard = int(pity["soft_start"]), float(pity["soft_step"]), int(pity["hard"])
    rates = []
    for k in range(1, hard + 1):
        p = base if k < soft else base + step * (k - soft + 1)
        rates.append(1.0 if k >= hard else min(1.0, p))
    return rates


def first_hit(rates: list[float]) -> list[float]:
    """P(first drop on pull k), k = 1..len(rates)."""
    out, alive = [], 1.0
    for p in rates:
        out.append(alive * p)
        alive *= 1 - p
    return out


def convolve(a: list[float], b: list[float]) -> list[float]:
    out = [0.0] * (len(a) + len(b))
    for i, x in enumerate(a):
        if x:
            for j, y in enumerate(b):
                out[i + j + 1] += x * y          # index i means i+1 pulls, so the sum is (i+1)+(j+1) pulls
    return out


def featured_dist(t: list[float], rate: float, guarantee: bool, max_drops: int = 60) -> list[float]:
    """P(featured first arrives on pull k): mix of 1, 2, ... pity-tier drops."""
    total, chain, miss = [0.0] * len(t), t[:], 1.0
    for n in range(1, max_drops + 1):
        p_this = 1.0 if (guarantee and n == 2) else rate
        w = miss * p_this
        if len(total) < len(chain):
            total += [0.0] * (len(chain) - len(total))
        for k, x in enumerate(chain):
            total[k] += w * x
        miss *= 1 - p_this
        if miss < 1e-12:
            break
        chain = convolve(chain, t)
    return total


def pct(dist: list[float], q: float) -> int:
    acc = 0.0
    for k, x in enumerate(dist, 1):
        acc += x
        if acc >= q - 1e-12:
            return k
    return len(dist)


def analyse(d: dict, pulls: list[int]) -> dict:
    tiers, checks = d["tiers"], []
    for t in tiers:
        ok = isinstance(t["weight"], int) and t["weight"] > 0 and all(isinstance(i["weight"], int) and i["weight"] > 0 for i in t.get("items", []))
        checks.append({"check": f"{t['id']}: positive integer weights", "ok": ok})
    total = sum(t["weight"] for t in tiers)
    base = {t["id"]: t["weight"] / total for t in tiers}
    pity, feat = d.get("pity"), d.get("featured")
    out = {"name": d.get("name"), "price": d.get("price"), "value_unit": d.get("value_unit"), "weight_sum": total, "tiers": []}
    eff = dict(base)
    if pity:
        pt = pity["tier"]
        t = first_hit(ramp(base[pt], pity))
        mean = sum(k * x for k, x in enumerate(t, 1))
        eff[pt] = 1 / mean
        rest = sum(base[k] for k in base if k != pt)
        for k in base:
            if k != pt:
                eff[k] = (1 - eff[pt]) * base[k] / rest
        out["pity"] = {"tier": pt, "mean_pulls": round(mean, 2), "consolidated_percent": round(100 * eff[pt], 3),
                       "p50": pct(t, .5), "p90": pct(t, .9), "p99": pct(t, .99), "hard": int(pity["hard"]),
                       "share_hit_by_hard_pity": round(t[-1], 4)}
        if feat:
            f = featured_dist(t, float(feat["rate"]), bool(feat.get("guarantee_after_loss")))
            fm = sum(k * x for k, x in enumerate(f, 1))
            out["featured"] = {"item": feat["item"], "mean_pulls": round(fm, 2), "p50": pct(f, .5), "p90": pct(f, .9), "p99": pct(f, .99),
                               "worst_case": int(pity["hard"]) * (2 if feat.get("guarantee_after_loss") else 0) or None,
                               "cost_mean": round(fm * d["price"], 1) if d.get("price") else None}
        cum, acc = [], 0.0
        for x in t:
            acc += x
            cum.append(acc)
        out["at_least_one"] = [{"pulls": n, "with_pity": round(cum[min(n, len(cum)) - 1], 4),
                                "without_pity": round(1 - (1 - base[pt]) ** n, 4)} for n in pulls]
    ev_base = ev_eff = 0.0
    for t in tiers:
        iw = sum(i["weight"] for i in t.get("items", [])) or 1
        items = [{"id": i["id"], "base_percent": round(100 * base[t["id"]] * i["weight"] / iw, 4)} for i in t.get("items", [])]
        out["tiers"].append({"id": t["id"], "value": t["value"], "base_percent": round(100 * base[t["id"]], 3),
                             "effective_percent": round(100 * eff[t["id"]], 3), "items": items})
        ev_base += base[t["id"]] * t["value"]
        ev_eff += eff[t["id"]] * t["value"]
    out["ev_per_pull"] = {"base": round(ev_base, 2), "with_pity": round(ev_eff, 2)}
    if d.get("price"):
        out["ev_per_pull"]["return_with_pity"] = round(ev_eff / d["price"], 3)
    dup = d.get("duplicates")
    if dup:
        out["shards_per_pull_if_all_duplicates"] = round(sum(eff[k] * v for k, v in dup["per_tier"].items()), 2)
        if dup.get("spark_cost"):
            out["pulls_to_spark"] = round(dup["spark_cost"] / out["shards_per_pull_if_all_duplicates"], 1)
    disc = d.get("disclosure") or {}
    for k, v in (disc.get("base_percent") or {}).items():
        got = 100 * base.get(k, 0)
        checks.append({"check": f"disclosed base {k} {v}% vs {got:.3f}%", "ok": abs(got - v) < 0.005 + 1e-9})
    for k, v in (disc.get("consolidated_percent") or {}).items():
        got = 100 * eff.get(k, 0)
        checks.append({"check": f"disclosed consolidated {k} {v}% vs {got:.3f}%", "ok": abs(got - v) < 0.005 + 1e-9})
    out["checks"] = checks
    out["ok"] = all(c["ok"] for c in checks)
    return out


def show(r: dict) -> str:
    L = [f"{r['name']}  (price {r['price']} {r['value_unit']} a pull, weights sum {r['weight_sum']})", "",
         f"  {'tier':<12}{'value':>8}{'base %':>10}{'with pity %':>13}"]
    for t in r["tiers"]:
        L.append(f"  {t['id']:<12}{t['value']:>8}{t['base_percent']:>10.3f}{t['effective_percent']:>13.3f}")
        L += [f"      {i['id']:<22}{i['base_percent']:>8.4f} %" for i in t["items"]]
    ev = r["ev_per_pull"]
    L += ["", f"  value per pull: {ev['base']} {r['value_unit']} at base rates, {ev['with_pity']} with pity"
          + (f" ({100 * ev['return_with_pity']:.1f}% of the price)" if "return_with_pity" in ev else "")]
    if "pity" in r:
        p = r["pity"]
        L.append(f"  {p['tier']}: mean {p['mean_pulls']} pulls (consolidated {p['consolidated_percent']}%), p50 {p['p50']}, p90 {p['p90']}, "
                 f"p99 {p['p99']}, hard pity {p['hard']} ({100 * p['share_hit_by_hard_pity']:.2f}% of drops wait for it)")
    if "featured" in r:
        f = r["featured"]
        L.append(f"  featured {f['item']}: mean {f['mean_pulls']} pulls, p50 {f['p50']}, p90 {f['p90']}, p99 {f['p99']}, worst {f['worst_case']}"
                 + (f"; mean cost {f['cost_mean']} {r['value_unit']}" if f["cost_mean"] else ""))
    for a in r.get("at_least_one", []):
        L.append(f"  P(at least one {r['pity']['tier']} in {a['pulls']:>3} pulls): {100 * a['with_pity']:5.1f}% with pity, {100 * a['without_pity']:5.1f}% without")
    if "shards_per_pull_if_all_duplicates" in r:
        L.append(f"  duplicates: {r['shards_per_pull_if_all_duplicates']} shards a pull when everything is a duplicate"
                 + (f"; the spark takes {r['pulls_to_spark']} pulls" if "pulls_to_spark" in r else ""))
    L += ["", "  checks:"] + [f"    {'ok  ' if c['ok'] else 'FAIL'} {c['check']}" for c in r["checks"]]
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("table")
    ap.add_argument("--pulls", type=int, nargs="+", default=[10, 30, 50, 70])
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    try:
        d = json.load(open(a.table, encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(f"drop_table: cannot read {a.table}: {e}", file=sys.stderr)
        sys.exit(2)
    r = analyse(d, a.pulls)
    print(json.dumps(r, indent=2) if a.json else show(r))
    sys.exit(0 if r["ok"] else 1)


if __name__ == "__main__":
    main()
