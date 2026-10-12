#!/usr/bin/env python3
"""Wave, HP, DPS and price curves on one table, before any bot runs: a quick check that the numbers have a shape.

    python3 curves.py ../assets/curves.template.json          # the table
    python3 curves.py my-stage.json --json                     # the same rows as JSON

For every wave: how many enemies come, their HP, the HP that arrives per second (the pressure), the gold the
player has earned so far, the upgrade level that gold buys when every coin goes into damage, the player's DPS at
that level, and the ratio DPS / pressure. Below 1.0 the horde piles up during that wave; well above 1.5 nothing
threatens. A designed stage moves around 1.0: pushes under it, breathers over it, a boss wave as the low point.
This is arithmetic, not a simulation. It says nothing about taps, targeting, walls or what a real player buys;
the bots (bots.mjs) and a browser run (the game-qa skill) are the evidence. Python 3.10+, standard library only.
"""
from __future__ import annotations

import argparse
import json
import math
import sys


def rows(c: dict) -> list[dict]:
    waves, secs = c["waves"], c["wave_seconds"]
    e, n, p, u = c["enemy"], c["count"], c["player"], c["upgrades"]
    bosses = {int(k): v for k, v in c.get("boss_waves", {}).items()}
    gold, level, spent, out = p.get("start_gold", 0), 0, 0, []
    for w in range(1, waves + 1):
        hp = e["hp"] * e["hp_growth"] ** (w - 1)
        count = n["base"] * n["growth"] ** (w - 1)
        sine = n.get("sine")
        if sine:                                   # a rising sine: odd waves push, even waves let the player spend
            count *= 1 + sine["amp"] * math.sin(math.pi * (w - 0.5))
        count = max(1, round(count))
        total_hp = count * hp
        boss = bosses.get(w)
        if boss:
            total_hp += boss["count"] * hp * boss["hp_mul"]
        # spend before the wave: every affordable level, cheapest first
        while gold - spent >= (price := u["base_price"] * u["ratio"] ** level):
            spent += price
            level += 1
        dps = p["dps"] * u["dps_gain"] ** level
        pressure = total_hp / secs
        out.append(dict(wave=w, count=count, hp=round(hp, 2), boss=bool(boss), total_hp=round(total_hp, 1), pressure=round(pressure, 2),
                        gold=round(gold), level=level, next_price=round(u["base_price"] * u["ratio"] ** level), dps=round(dps, 2),
                        ratio=round(dps / pressure, 2)))
        gold += (count + (boss["count"] if boss else 0)) * p["gold_per_kill"] + (boss.get("gold", 0) if boss else 0)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config", help="a curves JSON (start from assets/curves.template.json)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        with open(a.config, encoding="utf-8") as f:
            c = json.load(f)
        table = rows(c)
    except (OSError, ValueError, KeyError) as err:
        print(f"curves: {err}", file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps(table, indent=2))
        return 0
    print(f"{'wave':>4} {'count':>5} {'hp':>7} {'boss':>4} {'HP/s in':>8} {'gold':>6} {'lvl':>3} {'next':>6} {'DPS':>7} {'DPS/in':>6}")
    for r in table:
        flag = "  <- piles up" if r["ratio"] < 1 else ("  <- nothing threatens" if r["ratio"] > 1.5 else "")
        print(f"{r['wave']:>4} {r['count']:>5} {r['hp']:>7} {'yes' if r['boss'] else '':>4} {r['pressure']:>8} {r['gold']:>6} "
              f"{r['level']:>3} {r['next_price']:>6} {r['dps']:>7} {r['ratio']:>6}{flag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
