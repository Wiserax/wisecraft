---
name: game-economy
description: Tune the economy and difficulty of a web game with simulated players, then prove the result in a real browser. Covers player-model bots A-D (passive, tutorial follower, producer-like heavy tapper, efficient), the difficulty index across bots, rising-sine stages and chapters, boss tiers, premium-currency budgets and sinks, gifts only after a fall, what to do when the sim and the browser disagree, and how to re-measure when a bug fix shifts balance. Use when the user says "too easy", "too hard", "boring first minutes", "make it 60-70% as hard as the old version", "too many coins", "bosses fall too fast", "rebalance chapter 2", or asks for stages, waves, bosses, currencies or a monetization sink.
---

# Game economy and difficulty

Balance is measured, not felt by the agent. Model the players as bots, set a target per bot, change the
tables, and report the same table before and after. Then prove the first session in a real browser, because
the sim and the browser disagree exactly there.

The numbers below come from a horde tower-defense mobile web game (Vite + three.js, 8,000 enemies on screen
at 60 fps). Treat them as a starting point for a similar game, not as constants.

## 0. Before you tune
- `wise kb search "balance"` and the game's name: someone may have left the bot design and its traps.
- Find the tables (`ramp.js`, `first-siege.js`, `boss-tiers.js`). Every number lives in a named constant or
  table, so the balance owner changes data and not code.
- **A tuning agent must not edit UI files.** Give it data files and the sim, so its branch merges cleanly
  under the UI owner's.

## 1. Player models (simulate them all, 6+ seeds each)
| Model | Behaviour | Typical target |
|---|---|---|
| A passive | taps only, buys nothing | falls at the mid-stage mini-boss; the retry (with the gift) is winnable |
| B tutorial follower | buys what the tutorial points at, ~1 buy / 10 s | wins the first stage with walls ending 20–50% |
| C producer-like / heavy tapper | taps ~2/s, buys the first affordable Attack card every ~5 s | wins, but dips below 75% walls at each boss; boss lasts 25–35 s |
| D efficient | balanced attack + defence, buys every chance | wins comfortably (≥ 70%) |
| novice / average / casual-human | campaign bots for chapters | casual human ≤ 4–6 tries per stage, novice falls a few times per chapter |

Model C exists because the producer plays like that, and the producer is the first real player.

**Difficulty index:** tries to clear stages 1–10 per bot, each stage capped at 5. Compare against a reference
version (100%). When the producer says "60–70%", compute it this way and report all three campaign bots.
The weakest bot hits the cap first, so a change that hits strong builds harder (boss tap multiplier, armour
phases, threat scaled to fort power) moves strong players without walling weak ones.

## 2. Curve shape
- **Inside a stage (≈ 3 min, 10 waves):** a rising sine. Pushes on odd waves, breathers on even waves; a
  mid-stage mini-boss (wave 5), a boss wave at the end (horde ×2, a big boss). Something new to watch or buy
  at least every 5 s. Plot alive count *and* wall damage per 5 s: if wall damage is zero for the first
  minute, the opening is boring.
- **Across a chapter:** a sawtooth rising to stage 10, the hardest stage. Boss and titan stages are local
  peaks with a breather after. A finale easier than stage 5 is a bug.
- **First siege:** HP-gated (a basic enemy needs about 3 hits from the starting weapon) so the first upgrade
  is felt; the first card is affordable within about 5 s; no upgrades means you lose.
- **Tune count and pressure shape, not just HP.** Players feel "a thousand of them keep coming", not a
  bigger number. Count × HP is the pressure. A low-damage start can't handle 30% more bodies *and* 3-hit HP;
  pick fewer, tougher bodies there.

## 3. Bosses
- **Tiers:** `{ scale, tier: "mini"|"boss", hpMul }` on one spawn API. The model, hit area, HP bar and
  presence follow scale. ×2 bosses need camera pull-back and must not hide the base (dither where they
  overlap it).
- **Spawn at the field edge and walk in.** Large bodies need collision that can't wedge (squeeze past
  scenery), and attack reach that scales with radius. Test: a scale-2 boss reaches the wall from every
  angle and deals damage.
- **Taps vs bosses:** ×0.35 on bosses, ×0.5 on minis (or an armour phase at 50% HP), otherwise heavy tappers
  delete them.
- **Mini-boss pay:** less than a boss (no premium currency); its drop is about 1.5 upgrades.

## 4. Economy
- **Premium currency budget per chapter,** e.g. Chapter 1 ≈ 20–100 gems in total. Count every source (ranks,
  camo goals, events, drops) and check after every balance change.
- **Battle gold must feel tight:** "too generous in coins" is a real complaint. Upgrades should be choices,
  not a queue.
- **Sinks:** gacha towers (the Vault: free first open, 1 free per day, a paid open around 60 gems, a cap on
  power), cosmetics, and later pick-1-of-3 pacts.
- **Crowd answers** (pierce, splash) are essential, so price them as deliberate buys. Cap pierce at L5 with
  a top-tier L5 price, and keep full damage per pierced body.

## 5. Rescues
- **Gifts and blessings only after a fall.** Free help for a player who never died makes the game boring. A
  blessing helps (×1.5 damage, ×1.75 walls), it doesn't auto-win.
- A gift follows the stage being played; it never pops over a win screen.

## 6. Sim ↔ browser
- After any early-game change, run 3+ real-browser first sieges with the playtest bot (the **browser-qa**
  skill). If the sim says won and the browser says lost, find the behaviour difference (what the bot buys,
  taps, events active) before tuning more.
- Report per-wave tables: alive mean and peak, gold earned and spent, buys, walls at wave end, boss time
  under fire.
- Browser results that depend on real time also depend on the machine's frame rate. Read
  `references/sim-vs-browser.md` before trusting a browser loss.

## 7. When a bug fix shifts balance
A fix that makes the game behave as designed changes the pressure, even with no number touched. Measure with
the bots before and after, on the same seeds, and report both tables with the fix.
- **The case:** a double-size boss never reached the wall (collision held it about 7 m out; its reach was
  6.5 m). Once fixed, its strikes were new wall damage on the boss wave, and the fast-tapping player (model
  C) started losing.
- **What settled it:** three runs on 8 seeds each: the live build, the fix, and the fix with the boss unable
  to strike. That split "the boss now hits" from "the fight changed around it". The first slam strength
  (3.2 strikes per slam) took about 25% of the walls and model C lost 2 sieges in 8; at 1 strike per slam
  nobody lost.
- **Rule:** the engine owner ships the fix at the weakest setting that proves it and hands the levers (boss
  `hpMul`, the adds on that wave) to the balance owner. Don't retune HP or gold inside a bug-fix branch.

## 8. Report
Start with what changed for the player ("the first stage is busy from second 5; bosses stand 25 s"). Then
the table per bot before → after, the difficulty index, the premium budget, the browser runs, and what is
still open (which bot misses its target and which lever would move it).

## References
- `references/sim-vs-browser.md`: why the sim and the browser disagreed about the first siege, how it was
  settled, and how to make bot runs comparable. Read it when the two disagree or a browser bot result looks
  random.
- `references/lessons.md`: the lessons that cost a day each, with numbers. Read it before stretching wave
  length, adding a checkpoint, or paying progression in soft currency.
