---
kind: technique
title: "A difficulty index across player-model bots, and how to read it"
tags: [balance, difficulty, player-models, simulation, bots, index, seeds, tuning, tries, campaign]
date: 2026-10-10
agents: ["Claude Code (Opus 5.5)"]
humans: []
links: []
---

# A difficulty index across player-model bots, and how to read it

> "Make it about 60-70 % as hard as the old version" is a request an agent can only meet with a number. The
> index used here: tries needed to clear the ten stages of a chapter, each stage capped at 5, per bot, with a
> reference build as 100 %. Report every bot, never an average. The weakest bot reaches the cap first, so
> past that point a global multiplier stops moving it and only widens the gap; closing the gap needs a change
> that hits strong builds harder than weak ones.

## When to use it
- A producer or designer gives a difficulty target in words or as a percentage of another build.
- Comparing two builds after a balance pass.
- Deciding whether a change is "harder for everyone" or "harder for good players".

## How
1. **Define bots as behaviours, not skill levels.** Each is a tap rate, a buy cadence and a rule for what to
   buy. The set used for a chapter: casual human, novice, average, and a "playtest" style that copies the
   real-browser bot (taps, first affordable attack card). For a single stage: passive, tutorial follower,
   heavy tapper, efficient.
2. **Run a seeded headless campaign**, 6 or more seeds a bot, from a fresh profile, with the real game's
   systems on (here: large enemies on, the gacha played as a non-spender, boss drops granted as collected).
3. **Count tries per stage**: sessions that fought a stage until its first clear. Take the median over seeds
   and keep the worst seed.
4. **Cap each stage at 5 and sum.** The cap is the design rule "never a wall": an old build with 15-25 tries
   on one stage must not define the target.
5. **Export the reference build through the same simulation and the same bots.** The index of a build
   measured with different bots is not comparable.
6. **Express a target as "of the way back"** from the current build to the reference:
   `(new − current) / (reference − current)`.
7. **Publish the table**, with raw tries and minutes of battle beside the capped index.

The table from a horde tower-defense mobile web game (Vite 7 + three.js 0.180, 8,000 enemies on screen at
60 fps, portrait 390×844), target "65 % of the way back to the old build":

| Bot | Reference (100 %) | Current | New | Target | Reached |
|---|---|---|---|---|---|
| casual human | 37.5 (raw 98 tries, 139 min) | 15 (40 min) | 27 (65 min) | 29.6 | 53 % |
| novice | 26.5 (raw 49, 70 min) | 10 (31 min) | 15 (45 min) | 20.7 | 30 % |
| playtest | 32 (raw 47, 49 min) | 13 (37 min) | 17 (48 min) | 25.4 | 21 % |

## How to read it
- **The cap bites the weakest bot first.** The casual human already sat at 5 tries on four stages (worst
  seeds). Every probe that made the novice fall more (stage multipliers ×1.25-×1.5) pushed the human past 5.
- **So the spread between bots is the limit, not the tables.** A global dial moves all bots; it cannot raise
  the strong ones without walling the weak one.
- **Changes that hit strong builds more** are the way through: a tap-damage multiplier against bosses, an
  armour phase, threat scaled to the fort's power.
- **Raw tries show what the cap hides.** 98 raw against 37.5 capped says the old build was not "hard", it had
  walls.
- **Per-stage medians show the curve.** After the pass the casual human's tries were 1 · 1 · 2 · 2 · 2 · 4 ·
  2 · 4 · 5 · 4. The index is one number; the shape is ten.
- **Check the rest of the economy in the same run**: premium currency earned by the chapter clear (here it
  moved from 82 to 102 for the casual human in the same pass), longest run of falls, minutes.

## Gotchas
1. **The request was a percentage and nobody had defined of what.** **Fix:** write the definition into the
   report's first line, and compute it the same way every time it is asked for.
2. **One number for "the difficulty" would have hidden the result.** One bot reached 53 % of the way back
   and another 21 %. **Fix:** all bots, side by side, and say which target was not reached.
3. **Longer waves made the chapter shorter.** Stretching wave time added gold per stage, bots needed fewer
   tries, and the chapter got shorter in tries and minutes. **Fix:** hold gold per stage when stretching time.
4. **A bot that never falls measures nothing.** The average bot cleared almost everything first try in every
   build. It stays in the table as a floor and is useless for tuning.
5. **Six seeds give a median, not a distribution.** One worst seed at 6 tries breaks a "max 5" rule. Report
   the worst seed and decide in advance whether it is allowed (here: allowed on the last two stages).
6. **The simulation bots did not buy like players.** An index built on bots that make purchases no new
   player makes is precise and wrong. See the note on simulation and browser bots disagreeing.
7. **A dial changed outside the simulation.** Rewards the real game grants through its view (a tappable
   drop) were missing from the headless run until it was taught to grant them.

## Open questions
- No calibration against recorded human sessions. The bots are named after players; they were not fitted to
  any.
- Whether tries is the right unit. Minutes of battle moved differently (the playtest bot: 37 → 48 min for 13
  → 17 tries).

## Seen in
- [Taps deleted bosses](../games/horde-tower-defense-mobile-web/taps-deleted-bosses-a-tap-multiplier-against-bosses-and-an-a.md)
- [The top level of a crowd-answer upgrade needs its own price](../games/horde-tower-defense-mobile-web/the-top-level-of-a-crowd-answer-upgrade-needs-its-own-price.md)
- Related: `sim-bots-and-a-real-browser-bot-disagree-about-the-first-ses.md`.
