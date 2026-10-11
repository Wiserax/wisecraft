---
kind: game
title: "The top level of a crowd-answer upgrade needs its own price (pierce L5)"
game: "Horde tower defense (mobile web)"
games_also: []
game_version: "2.3.0, Vite 7 + three.js 0.180"
platform: web-mobile
engine: threejs-vite
route: data-tuning
tools: ["node --test", "Vite"]
status: released
agents: ["Claude Code (Opus 5.5)"]
humans: []
date: 2026-10-10
links: []
tags: [economy, pricing, pierce, upgrade-curve, crowd-control, ablation, player-models, battle-gold]
---

# The top level of a crowd-answer upgrade needs its own price (pierce L5)

> Pierce lets a bolt fly on through its target and hit the next enemies in line. It was added as the answer
> to a packed horde and priced on the usual geometric curve, 150 to 1,756 battle gold over five levels. It
> turned out cheap and essential: one bot's run without it cost 6.5 more tries, 23 % of the chapter. The fix
> gave the last level a price off the curve, 12,000, next to the most expensive late buys. Pierce is still
> the main answer to crowds and is now worth 12 % of the chapter. Measured by simulating with and without it.

## Setup
- A horde tower-defense mobile web game (Vite 7 + three.js 0.180, 8,000 enemies on screen at 60 fps,
  portrait 390×844).
- Battle gold is earned and spent inside one run. Upgrades are cards with levels; prices normally grow by a
  fixed ratio per level.
- Pierce: battle-only, unlocks at the fifth stage, 5 levels. A bolt flies up to 12 m past its target and hits
  the next `level` enemies within 0.5 m of its path, nearest first. No randomness.
- The oracle is a headless campaign simulation: bots with different play styles, 6 seeds each.

## Route and why
**Data tuning: a price list, not a formula.** The upgrade entry in `src/game/data.js` gained an explicit
`prices` array that overrides the curve. The first version had balanced pierce the other way, with a damage
penalty (pierced enemies took 85 % damage). The feedback on that build was "cheap and essential" and that
level 5 "must be a big price", with full damage, so the penalty went and the price came.

## How the game works (what we had to learn)
- **A crowd answer is not a damage upgrade.** Its value grows with density, so it is worth little in early
  stages and a great deal in late ones. A price curve tuned on early income is wrong by an order of magnitude
  at the end.
- **The last level is the one that ends the problem.** Level 5 hits six bodies a bolt. With late-stage income
  a few thousand battle gold a session, 1,756 was bought without a thought.
- **An ablation run measures what an upgrade is worth.** Run the same bot and seeds with the upgrade removed
  (`NO_PIERCE=1`) and compare tries and minutes for the chapter.

## Build steps
1. Measure the share: with and without, same bot, same seeds.
2. Find the price band of the deliberate late buys. Here the dearest tower levels cost 11,000-17,000.
3. Keep levels 1-4 on a doubling curve so the upgrade is still reachable; put level 5 in that band.
4. Give the buyer full value: pierced bodies take full damage.
5. Re-run the ablation and the chapter index.

| | Before | After |
|---|---|---|
| Prices L1-L5, battle gold | 150 · 278 · 513 · 949 · 1,756 | 300 · 600 · 1,200 · 2,400 · 12,000 |
| Damage to pierced bodies | 85 % | 100 % |
| Step from L4 to L5 | ×1.85 | ×5 |

## Verification
Casual-human bot, first chapter, 6 seeds:

| Build | With pierce | Without | Pierce's share |
|---|---|---|---|
| before | 14.5 tries, 40.5 min | 21 tries, 52.4 min | 6.5 tries, 11.9 min (23 % of the chapter) |
| after | 27 tries, 64.9 min | 32 tries, 73.7 min | 5 tries, 8.8 min (12 %) |

- Without pierce, the last four stages sit at the 5-try cap, so it remains the main answer to crowds.
- The "after" build also changed stage health, gold and bosses in the same round, so the two rows are not a
  clean A/B of the price alone. The share within each row is the comparable figure.
- The economy tests were updated for the new numbers (`node --test`).
- **Not verified:** how many real players reach level 5, and when.

## Gotchas
1. **An essential upgrade was the cheapest thing on the panel.** **Cause:** it inherited the generic price
   curve. **Fix:** an explicit price list for upgrades whose value does not follow the curve.
2. **The first balancing lever was a damage penalty (85 %).** It left the pricing problem alone: the upgrade
   was still bought without a thought. **Fix:** full damage, real price.
3. **Raising every level's price would have moved the unlock moment.** Level 1 is the "now I have an answer"
   beat on the stage where it unlocks. **Fix:** double the early levels only; put the wall at the top.
4. **A price is only "big" against income.** 12,000 was chosen against the dearest late tower levels and a
   late session's income of about 4,000-5,000 battle gold, not as a round number. When income is retuned,
   this price has to be looked at again; the same round cut battle gold to ×0.62.
5. **The card order mattered too.** Once unlocked, the pierce card was pinned first in its tab, so players
   find it. A deliberate buy has to be visible to be deliberate.
6. **The upgrade's worth was unknown until it was removed.** The 23 % figure came from the ablation run, not
   from the design. Do this for every upgrade described as "the answer to X".

## Open questions
- Whether one level at ×5 feels like a goal or like a paywall to players. Bots do not report frustration.
- Splash damage (the mortar) is the other crowd answer and was not put through the same ablation.
