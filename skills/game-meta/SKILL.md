---
name: game-meta
description: Design and tune a game's meta and monetization from real data. Covers loot boxes, chests and drop tables (rarity tiers, expected value, soft and hard pity, the 50/50 featured guarantee, duplicates), gacha odds disclosure, the shop, starter packs and offers, the season pass, subscriptions and rewarded ads, soft, hard and event currencies with a faucet and sink ledger, price ladders, premium budgets, progression and the difficulty curve across sessions, rescue gifts only after a fall, retention loops, and ethical guardrails (odds laws, no dark patterns, minors). Ships a drop-table calculator and an economy ledger checker. Use when the user says "design the loot boxes", "add a gacha", "is this gacha fair", "add a pity system", "too many coins", "nothing to spend coins on", "add a season pass", "price the starter pack", "players quit on day 2", "the gift shows up for players who win", or asks about currencies, sinks, offers, monetization or retention.
---

# Game meta: the loop around the game

Balance decides whether a fight is fair. The meta decides why a player comes back tomorrow, what they work
toward, and what they pay for. It is mostly arithmetic: a ledger of what comes in and goes out, drop tables
with known odds, prices measured against income, and a curve across days. Compute it, then prove it with bots
and a real browser, then read what real players did.

## 0. Real data first
Before designing anything, read what exists:
- **Retention** D1 / D7 / D30 by install cohort, split by what happened in session 1 (cleared or not, fell or
  not, got the gift or not).
- **The funnel:** boot → first fight → first clear → hub → second session → chapter 1 clear.
- **The real ledger:** faucet, sink and balance per currency by day since install (median and p90), per
  segment.
- **Money:** payer conversion, ARPDAU, ARPPU, revenue by item and by offer trigger, store-open → purchase,
  refund rate.
- **The gacha:** observed odds against the disclosed ones, how often pity is reached, duplicate share.

If the game logs none of this, instrumenting it is the first task (`references/tuning-from-data.md` has the
events). Where no data exists yet, the ledger and the bots fill the gap, and the report says so.

Also read `knowledge/INDEX.md` for notes on rewards, gifts and pricing in this kind of game.

## 1. The workflow
1. **Read** the data above and the game's tables (prices, rewards, drop tables, pass tiers). Every number
   lives in a named table, so the meta owner changes data and not code.
2. **Model** the economy as a ledger per kind of player (light, engaged, heavy) in
   `assets/economy-model.template.csv`, and every random reward as a drop table in
   `assets/drop-table.template.json`.
3. **Check** with the scripts (standard library Python, no install):
   ```bash
   python3 scripts/economy_ledger.py economy.csv --soft coins --budget gems=40-90   # inflation, debt, dead sinks, budget
   python3 scripts/drop_table.py drop-table.json                                    # odds, value per pull, pity, disclosure check
   ```
4. **Tune** the tables. One lever at a time; write down the expected effect before running.
5. **Prove** it: the player-model bots of the **game-balance** skill with each kind of player's spending (the
   difficulty index must not move unless that was the point), and a real-browser pass of the **game-qa** skill
   over the shop, the gacha, the pass and the reward screens (double taps, reloads mid-grant, a spender
   profile built from debug grants).
6. **Report** what changes for the player first, then the numbers before → after, and what real data will
   confirm or refute it after release.

## 2. Rules that held up in a shipped game
From a horde tower defense for phones, where each cost about a day to learn:
- **Progression pays premium currency, not soft.** Soft currency buys power, so a rank reward of coins makes
  the next stages easier than planned and pulls the chapter forward.
- **Count the premium budget per chapter from every source** (ranks, goals, clears, events, drops, the free
  daily pull, the pass). Chapter 1 was budgeted at 20-100 gems; a rebalance that moved rewards measured
  90-102 at the clear. Recount after every change.
- **Battle gold must feel tight.** "Too generous in coins" was real feedback; battle gold went to ×0.62.
  Upgrades are choices, not a queue.
- **The vault (gacha):** a free first open, one free open a day, a paid open around 60 gems, and a cap on the
  power it can give, so spenders are stronger without skipping the curve.
- **Price an essential upgrade in tries, not gold.** Run the same bot with and without it. The crowd answer
  (pierce) was worth 6.5 tries (23 % of the chapter) on the generic price curve; its last level got its own
  price, 12,000 next to the dearest late buys, and is now worth 5 tries (12 %).
- **A mini-boss inherits a boss's pay** if it reuses the boss role. Set its pay on purpose: less than a boss,
  no premium currency.
- **Gifts and blessings only after a fall, never over a win screen.** A gift for players who never fell makes
  the game boring; a blessing helps (×1.5 damage, ×1.75 walls), it doesn't win.
- **Pay rewards the instant the run ends,** idempotent on the run id; the celebration only presents them. A
  reload or a double tap must never pay twice or lose the grant.
- **Checkpoints must not keep the whole build,** and **"push on" must be measured** with the bots before it
  ships: if they can't win it, the button is a way to lose.
- **Longer waves pay more per stage,** so the chapter gets shorter. Hold gold per stage when stretching time.

The notes behind these:
[rescue gifts only after a fall](../../knowledge/games/horde-tower-defense-mobile-web/rescue-gifts-only-after-a-fall-and-never-over-a-win-screen.md),
[pay rewards the instant the run ends](../../knowledge/games/horde-tower-defense-mobile-web/pay-rewards-the-instant-the-run-ends-the-celebration-only-pr.md),
[the top level of a crowd-answer upgrade needs its own price](../../knowledge/games/horde-tower-defense-mobile-web/the-top-level-of-a-crowd-answer-upgrade-needs-its-own-price.md).

## 3. Drop tables and gacha, in short
- Roll the tier, then the item. Integer weights over a round sum (10,000).
- Without pity the tail is brutal: at 0.6 % a pull, the mean is 167 pulls and one player in a hundred needs
  766. **Add soft and hard pity:** the template (soft from pull 60 at +6 % a pull, hard at 75) gives a mean of
  53.1 pulls, a consolidated rate of 1.882 % and a 99th percentile of 69.
- **The 50/50 with a guarantee** gives the featured item in 79.7 pulls on average, 150 at worst; without the
  guarantee the 99th percentile is 390 pulls. Ship the guarantee.
- **Value per pull with pity** between about 70 % and 100 % of the price (template: 52.71 of 60 gems).
- **Duplicates convert** to shards, and a spark buys the featured item at about the cost of luck.
- **Disclose** base and consolidated odds, the pity rule and what duplicates become, before purchase.
  `drop_table.py` fails when the disclosure disagrees with the weights: run it in the game's tests.

Formulas, tables and the disclosure format: `references/drop-tables-and-gacha.md`.

## 4. Currencies, shop and pass, in short
- One job per currency: run gold for choices inside a run, soft for power, premium for time, choice,
  cosmetics and the gacha, event currency that converts when it expires.
- Prices follow a ladder (`base × r^(L-1)`); plot time-to-afford against income, and step off the curve when
  an item's value doesn't follow it.
- Inflation starts when the main sink caps out. The template ledger shows it: from day 5 the player keeps
  40-62 % of the coins earned and holds 13,400 by day 7; a star-up sink from day 4 brings it to 7-13 % and
  3,500.
- A starter pack at 3-6× the pouch value after the first chapter clear; offers on real triggers with
  cooldowns, never during a fight or over a win; a pass an engaged player finishes in its last week.

Details: `references/currencies-and-sinks.md`, `references/shop-offers-and-pass.md`.

## 5. Progression and retention, in short
- Across a chapter, a rising sawtooth to stage 10; boss stages are local peaks; a finale easier than stage 5
  is a bug. Walls are measured in tries (the difficulty index of the **game-balance** skill); two caps in a
  row is a wall where players quit.
- Every soft gate has a free answer within one or two sessions: an upgrade, a vault tower, the rescue gift.
- Always a next goal: minutes (an upgrade), a session (a tier, a chest), days (a chapter, a tower).
- Loops: run, session, daily (about 10 minutes covers the dailies), weekly, season, long. Streaks advance on
  days played and never punish a missed day.
- "Players quit on day 2": split D1 retention by session-1 outcome, then find the funnel step.

Details: `references/progression-and-retention.md`.

## 6. Guardrails
- **Spending money needs a yes.** The agent never completes a real purchase, ad view or subscription; it
  tests spenders with debug grants, store sandboxes and test ads. It never turns on a paid service or changes
  live prices, offers or odds without the producer's yes.
- **Odds are disclosed** wherever paid randomness exists, matching the code.
- **No dark patterns:** no resetting timers, confirm-shaming, hidden real-money prices, paywalls as the only
  way past a wall, offers right after a near-miss. If asked for one, explain the risk and offer the honest
  version.
- **Minors:** stricter defaults, spend caps, consent where required.
- **Not legal advice:** check the current rules for every market and say which were checked.

Details and the country-by-country summary: `references/ethics-and-rules.md`.

## 7. Report
Start with the player's experience ("a free player gets the featured tower in about 80 pulls, never more than
150; coins stay meaningful through day 7"). Then:
- the ledger flags before → after, with the command that produced them;
- the drop-table numbers (odds, mean and p99 pulls, value per pull) and the disclosure check;
- the bots' difficulty index and premium budget per chapter, before → after;
- the browser pass over the money flows;
- which numbers are real data, which are sims, which are design assumptions, and which events will confirm
  them after release.

## References
- `references/drop-tables-and-gacha.md`: tiers, pity math, the 50/50, value per pull, duplicates, the
  disclosure table. Read it before touching any random reward.
- `references/currencies-and-sinks.md`: currency jobs, the daily budget, price ladders, exchange rates, the
  value of time, inflation, the worked ledger.
- `references/shop-offers-and-pass.md`: shop layout, price points, the starter pack, offer triggers, the
  season pass sized from play, subscriptions, rewarded ads.
- `references/progression-and-retention.md`: the curve across sessions, rescue gifts, instant rewards,
  retention loops, the first week, rough metric ranges.
- `references/ethics-and-rules.md`: odds disclosure by market, dark patterns and their honest versions,
  minors, refunds, what the agent never does.
- `references/tuning-from-data.md`: the events to log, the tables to read, checking odds in production, A/B
  test sizes and guardrails, changing a live price.
- `assets/drop-table.template.json`, `assets/economy-model.template.csv`: the templates.
- `scripts/drop_table.py`, `scripts/economy_ledger.py`: the calculators (Python 3.9+, standard library only).
