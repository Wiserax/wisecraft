---
name: game-balance
description: Tune the numbers of a game (waves, enemy HP and count, DPS, upgrade prices, boss tiers, stage and chapter curves) and prove the result with player-model bots on fixed seeds and a real-browser run. Covers reading real analytics first, bots as habits (passive, casual, heavy tapper, attentive, spender), a difficulty index across bots ("make it 60-70% as hard as the old build"), rising-sine stages and sawtooth chapters, pressure vs DPS curves, geometric price ladders, boss tap multipliers and armour phases, what to do when the sim and the browser disagree, and re-measuring after a bug fix shifts balance. Use when the user says "too easy", "too hard", "boring first minutes", "bosses die too fast", "rebalance chapter 2", "tune the waves", "the upgrade is too cheap", "how hard is it compared to the old version", or asks for wave, HP, damage or price tables.
---

# Game balance: the numbers, measured

Balance is measured, not felt by the agent. Read what real players did, model the players as bots, set a
target per bot, change the tables, and report the same table before and after on the same seeds. Then prove
the first session in a real browser, because the simulation and the browser disagree exactly there.

The worked numbers come from a horde tower defense for phones (Vite + three.js, 8,000 enemies on screen at
60 fps). Treat them as a starting point for a similar game, not as constants. Economy design (currencies,
loot, shop, pass, retention) lives in the **game-meta** skill; this one owns the numbers inside a run.

## 0. Real data first
Before a single bot runs, read what exists:
- **Analytics:** where real players fall (stage, wave, seconds in), retries per stage, session length, quits
  right after a loss, what they buy first. A funnel of "reached wave N" by stage is the most useful single
  chart. Bots fill the gaps where no real data exists yet (a new stage, an unreleased build).
- **Real saves and the live build:** a real mid-game save beats a fixture; the live build is the reference.
- **The producer's words**, turned into a number: "60-70% as hard as the old version" means the difficulty
  index below, defined in the first line of the report.
- `knowledge/INDEX.md`: earlier notes on balance and on this kind of game.

Then find the tables. Every number lives in a named constant or a data file (`ramp.js`, `waves.json`,
`boss-tiers.js`), so the balance owner changes data and not code. **A tuning agent edits data files and the
sim, never UI files**, so its branch merges cleanly.

## 1. Player models: habits, not skill levels
A bot is a tap rate, a buy cadence and a rule for what to buy. Simulate them all on 6-8 seeds each.

| Model | Habit | Typical target |
|---|---|---|
| passive | taps nothing, buys nothing | falls at the mid-stage mini-boss; the retry (with a rescue gift) is winnable |
| casual / tutorial follower | buys what the tutorial points at, about 1 buy every 10 s | clears the first stage with walls ending 20-50% |
| heavy tapper (producer-like) | taps about 2/s at the nearest enemy, buys the first affordable attack card every ~5 s | clears, but dips below 75% walls at each boss; a boss lasts 25-35 s |
| attentive / efficient | balanced attack and defence, buys every chance | clears comfortably (70%+ walls) |
| browser-style | copies the real-browser bot: first affordable attack card, never opens defence | must match the browser result; see section 6 |

The heavy tapper exists because the producer plays like that, and the producer is the first real player.
`scripts/bots.mjs` runs these habits against any sim that exports `createSim({ seed })` with `step`, `tap`
and `state` (two functions marked ADAPT cover buying):
```bash
node scripts/bots.mjs path/to/sim.js --seeds 8 --seconds 240
```
On the sample game (`examples/horde-demo`) it prints, for every model, 8 of 8 cleared with walls at 100% and
no wall hit at all. Even the passive player wins untouched: that is "too easy", measured.

## 2. The difficulty index
"Make it 60-70% as hard" can only be met with a number:
- **Tries to clear stages 1-10 per bot**, median over seeds, each stage capped at 5, summed. The cap is the
  design rule "never a wall".
- **A reference build is 100%**, measured through the same sim and the same bots.
- **A target is "of the way back"**: `(new - current) / (reference - current)`.
- **Report every bot, never an average,** with raw tries and minutes beside the capped index.

The weakest bot hits the cap first, so a global multiplier stops moving it and only widens the gap. To make
strong players work harder without walling weak ones, use changes that scale with the player's power: a tap
multiplier against bosses, an armour phase at half health, threat scaled to fort power. The full method, a
real table and how to read it: `knowledge/techniques/a-difficulty-index-across-player-model-bots-and-how-to-read.md`.

## 3. Curve shape
- **Inside a stage (about 3 min, 10 waves): a rising sine.** Odd waves push, even waves let the player spend;
  a mini-boss at wave 5 and a boss wave at the end (horde x2, a big boss). Something new to watch or buy at
  least every 5 s. Plot alive count *and* wall damage per 5 s: zero wall damage for the first minute means a
  boring opening.
- **Across a chapter: a sawtooth** rising to stage 10, the hardest. Boss stages are local peaks with a
  breather after. A finale easier than stage 5 is a bug.
- **The first fight:** a basic enemy needs about 3 hits from the starting weapon, so the first upgrade is
  felt; the first card is affordable within about 5 s; with no upgrades the player loses.
- **Tune count and pressure shape, not just HP.** Count x HP is the pressure, but players feel "a thousand of
  them keep coming", not a bigger number. A low-damage start can't take 30% more bodies *and* 3-hit HP: pick
  fewer, tougher bodies there.

`references/curves.md` has the formulas (pressure, DPS, time to kill, geometric ladders, the sine) and
`scripts/curves.py` prints a stage's wave table from one JSON before any bot runs:
```bash
python3 scripts/curves.py assets/curves.template.json     # DPS / incoming HP per wave; < 1 piles up
```

## 4. Bosses
- **Tiers on one spawn API:** `{ scale, tier: "mini" | "boss", hpMul }`. Model, hit area, HP bar and
  presence follow scale.
- **Taps vs bosses:** x0.35 on bosses, x0.5 on minis (or an armour phase at 50% HP), otherwise heavy tappers
  delete them in seconds. The case: a fast tapper killed the mini-boss in about 7 s and the boss in about 10 s
  while a tutorial follower needed 16-19 s and 24-34 s; health alone could not close that gap.
- **Time under fire is the target,** per model: a boss that stands 25-35 s for the heavy tapper.
- **A large boss must reach the wall:** attack reach scales with body radius, and a scale-2 boss is tested
  against the wall from every angle. If it never strikes, the balance was measured on a broken fight.
- **Mini-boss pay:** less than a boss; its drop is about 1.5 upgrades.

## 5. Prices inside a run
- **Battle gold must feel tight.** "Too generous in coins" is a real complaint; upgrades should be choices,
  not a queue.
- **A geometric ladder** `price(n) = base x r^n` with r around 1.3-1.6 for power upgrades. Check it against
  income: when r outruns gold per wave, late waves fall behind (the template table shows DPS / incoming HP at
  0.27 on the final boss wave).
- **Crowd answers (pierce, splash) are essential, so price them as deliberate buys.** Cap pierce at L5 with
  its own top price, keep full damage per pierced body, and price the top level by what it is worth in tries
  (pierce L5 was worth about 5 tries, 9 minutes of a chapter).
- **Longer waves add gold per stage,** so bots need fewer tries and the chapter gets *shorter*. Hold gold per
  stage when you stretch time.

## 6. Sim and browser
- After any early-game change, run 3+ real-browser first fights with the **game-qa** skill
  (`wise qa ... --persona tapper`, or a custom journey) and report walls left at the clear.
- If the sim says won and the browser says lost, find the behaviour difference (what the bot buys, what it
  taps, which events are on) before tuning more. Then add a sim style that buys like the browser bot.
- Browser results that depend on real time also depend on the machine's frame rate: a laptop on battery in
  low-power mode caps the browser at 30 fps. Run the live build side by side before blaming the change.
- `references/sim-vs-browser.md` is the worked case and the checklist.

## 7. When a bug fix shifts balance
A fix that makes the game behave as designed changes the pressure with no number touched. Measure before and
after on the same seeds and report both tables with the fix.
- **The case:** a double-size boss never reached the wall. Once fixed, its strikes were new wall damage and
  the heavy tapper started losing. Three runs on 8 seeds (live, the fix, the fix with the boss unable to
  strike) split "the boss now hits" from "the fight changed around it": 3.2 strikes per slam took about 25%
  of the walls and lost 2 sieges in 8; at 1 strike per slam nobody lost.
- **Rule:** the engine owner ships the fix at the weakest setting that proves it and hands the levers (boss
  `hpMul`, the adds on that wave) to the balance owner. No HP or gold retuning inside a bug-fix branch.

## 8. Report
Start with what changed for the player ("the first stage is busy from second 5; bosses stand 25 s"). Then:
the table per bot before and after (cleared, lost, walls left as min-max, first wall hit, fall time), the
difficulty index with its definition, the browser runs, which numbers are sim and which are browser, and what
is still open (which bot misses its target and which lever would move it).

## Rules
- **Real data first;** bots and fixtures fill gaps. Say which numbers came from where.
- **Same seeds before and after,** 6+ per model; report the range, not only the mean.
- **Data, not code:** the balance owner changes tables; UI files are someone else's.
- **Spending real money needs a person's yes.** Spender bots buy with in-game currency or debug grants only.

## References
- `references/curves.md`: formulas and a worked stage table. Read it before writing a wave or price table.
- `references/sim-vs-browser.md`: why the sim and the browser disagreed about the first fight, the checklist,
  and making bot runs comparable. Read it when the two disagree or a browser result looks random.
- `references/lessons.md`: one full balance pass with numbers, and the lessons that cost a day each.
- `scripts/bots.mjs`: the player-model runner. `scripts/curves.py` + `assets/curves.template.json`: the
  wave, HP, DPS and price table.
- Notes: `knowledge/techniques/a-difficulty-index-across-player-model-bots-and-how-to-read.md`,
  `knowledge/techniques/sim-bots-and-a-real-browser-bot-disagree-about-the-first-ses.md`, and in
  `knowledge/games/horde-tower-defense-mobile-web/`: the rising-sine first stage, taps that deleted bosses,
  the pierce L5 price, and the bug fix that changed the balance.
