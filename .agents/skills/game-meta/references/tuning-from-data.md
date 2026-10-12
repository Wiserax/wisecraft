# Tuning the meta from real data

Real data first. Read what real players did before modelling what they might do; the ledger and the bots fill
the gaps where no data exists yet (before launch, a new feature, a segment too small to read). A number in a
report says where it came from: telemetry, a sim, a browser run, or a guess.

## 1. The events to log
If the game logs none of these, instrumenting them is the first meta task. Every event carries the player id,
session id, release, days since install and a timestamp.

| Event | Fields | Answers |
|---|---|---|
| `economy_flow` | currency, amount, direction (source or sink), source id, balance after, stage, run id | the real ledger: faucets, sinks, balances by day |
| `stage_result` | stage, outcome, try number, duration, walls left, gift offered, blessed | the real curve: tries per stage, where players fall |
| `store_open` | entry point (hub button, offer, wall) | which doors lead to the shop |
| `offer_shown` / `offer_result` | offer id, trigger, price, bought or dismissed | offer conversion per trigger |
| `purchase` | sku, local price, currency code, store transaction id, first purchase | revenue, conversion, ARPPU |
| `gacha_pull` | banner, pity counter before the pull, tier, item, featured, duplicate, cost | observed odds, pity reach, duplicate load |
| `gift_offered` / `gift_opened` | kind, stage, falls before it | whether rescues reach stuck players |

Automated QA runs send their analytics like any player (the **game-qa** skill); tag them so they can be
filtered out, never block them by default.

## 2. The tables to read first
- **Retention:** D1, D7, D30 by install cohort, split by what happened in session 1.
- **The funnel:** boot → first fight → first clear → hub → second session → chapter 1 clear.
- **The real ledger:** median and 90th-percentile faucet, sink and balance per currency by day since install,
  per segment. Put the medians into the CSV of `economy_ledger.py` in place of the planned numbers, and run it
  again.
- **The real curve:** tries per stage (median and p90) by segment; the stages where most sessions end.
- **Money:** payer conversion, ARPDAU, ARPPU, revenue by sku and by offer trigger, refund rate.
- **Segments:** by spend (non-payer, small, medium, large; set the cut-offs from the game's own distribution)
  and by engagement (days played in the first week). An average across segments describes nobody.

## 3. Checking the odds in production
Pity makes pulls depend on each other, so check the base rate on the pulls that the pity rule can't touch:
pulls with a counter below the soft start.
- Template numbers: 80,000 such pulls at 0.6 % should give 480 legendaries, standard deviation
  √(n·p·(1−p)) = 21.8. An observed 430 is 2.3 standard deviations low: look for a bug (a reroll, a wrong
  weight in one build) before anyone calls it bad luck.
- The consolidated rate over all pulls should approach 1 / mean pulls (1.882 % in the template). Over 100,000
  pulls that is about 1,882.
- If the observed and disclosed numbers differ, the disclosure is wrong, which is a compliance problem
  (`ethics-and-rules.md`), not a tuning detail.

## 4. A/B tests
- **Sample size per arm** (80 % power, 5 % two-sided), the quick rule: n ≈ 16 · p · (1 − p) / δ², with p the
  baseline rate and δ the absolute change to detect.
  - payer conversion 2 %, detect +0.5 points: n ≈ 12,544 players per arm;
  - D1 retention 35 %, detect 2 points: n ≈ 9,100 per arm;
  - D1 retention 40 %, detect 3 points: n ≈ 4,267 per arm.
- **Revenue is heavy-tailed:** one large spender moves the mean. Test conversion and ARPPU separately, or cap
  each player's spend in the analysis, and run for whole weeks (weekday and weekend players differ).
- **Guardrails** for every economy test: D1 and D7 retention, session length, refund rate, the share of
  players stuck at a wall, and the difficulty index from the bots. A test that lifts revenue and drops D7 has
  failed.
- **New players only** for price and offer tests, where possible: existing players have seen the old price.

## 5. Changing a live price or drop table
- Prepare the change, its numbers (`drop_table.py`, `economy_ledger.py`), and the test plan; the producer
  decides. Live prices and live odds never change without that yes.
- **Raising a price** players have seen reads as a betrayal. Prefer a new pack, a new offer, or a new tier;
  if a price must rise, change it for new players or at a season boundary, with notice.
- **Lowering a price** is safe; consider a goodwill grant for recent buyers of the old price.
- **Changing odds** means changing the disclosure in the same release, and running the disclosure check in the
  tests.
- **Rebalancing rewards** changes the premium budget: recount every source (the budget per chapter) after the
  change, and re-run the bots, because premium buys power.

## 6. When there is no data yet
Before launch, or for a new feature:
1. Write the ledger for three kinds of player (light, engaged, heavy) from the design.
2. Run `economy_ledger.py` and fix the flags.
3. Run the player-model bots (the **game-balance** skill) with the spending of each kind of player, and check
   the curve and the walls.
4. Prove the purchase and reward flows in a real browser: double taps, reloads mid-grant, the spender profile
   with debug grants (the **game-qa** skill).
5. Name every number as a design assumption in the report, and list the events that will replace it with real
   data after launch.
