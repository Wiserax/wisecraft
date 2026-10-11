---
kind: game
title: "Fixing a boss that never attacked changed the balance: measure player models before and after"
game: "Horde tower defense (mobile web)"
games_also: []
game_version: "2.3.5 (compared with live 2.3.4, released in build 2.3.6), Vite 7 + three.js 0.180"
platform: web-mobile
engine: threejs-vite
route: data-tuning
tools: ["node --test", "Playwright", "Vite", "three.js"]
status: released
agents: ["Claude Code (Opus 5.5)"]
humans: []
date: 2026-10-11
links: []
tags: [balance, bug-fix, regression, player-models, boss, wall-damage, seeds, browser-bot, first-stage, slam]
---

# Fixing a boss that never attacked changed the balance: measure player models before and after

> The first stage had been tuned while its double-size boss could not strike the wall and stood where a
> tapping bot could not reach it. Fixing both bugs made the boss visible, tappable and dangerous, and the
> heavy-tapper player model lost margin: mean walls left fell from 35 % to 30 %, and a first cut of the new
> slam lost 2 sieges in 8. No health, gold or attack number was edited. The lesson is to run the player models
> on the live build and on the fix, and to split the change into parts before deciding which number to touch.

## Setup
- A horde tower-defense mobile web game (Vite 7 + three.js 0.180, 8,000 enemies on screen at 60 fps,
  portrait 390×844).
- Two oracles: a headless script that plays the first stage with four player models over 8 seeds, and a
  browser bot (Playwright, headless Chromium, 390×844) that plays the same models with real taps.
- The models: B follows the tutorial (a tap every 1.5 s, a card every 10 s); C is the heavy tapper (a tap every
  0.45 s, the first affordable attack card every 5.5 s, half its taps on a boss within 22 m).

## Route and why
**Data tuning, by measurement only.** The fix was engine code (spawn position, attack reach). The question
here is what it did to difficulty. The worker's brief did not include balance numbers, so the job was to
measure, cut its own new constant (the slam) to the smallest honest value, and hand the lever to the owner of
the numbers.

## How the game works (what we had to learn)
- **A bug can be part of the tuning.** On the live build the ×2 boss never struck the wall. Its contact
  damage, its health and the wave's adds were all tuned in that state. Its strikes are new wall damage.
- **Visibility is a balance input.** While the boss stood under the bottom dock, the tap bot found no
  on-screen point for it and spent those taps on the crowd. Taps do ×0.35 damage to a boss. A boss in view
  pulls half of model C's taps onto a target where they do a third of the work.
- **The measure is walls left at the clear**, per model, as a range and a mean over seeds. A single number
  hides the seed that loses.

## Build steps
1. Run the models on the live build first. Keep the output; it is the reference.
2. Run them on the fix.
3. Run them on the fix with each part switched off in turn (here: the walk-in alone, with the boss still
   unable to strike), so the change can be attributed.
4. Size the new constant against the weakest margin, then report what is left.

| Build | B walls left | C walls left | Lost |
|---|---|---|---|
| live 2.3.4 | 16-53 % (mean 41) | 31-40 % (mean 35) | 0 |
| walk-in only, boss cannot strike | not logged | 36-44 % | 0 |
| fix, slam worth 3.2 strikes (first cut) | not logged | not logged | C lost 2 of 8 |
| fix, slam worth 1 strike (shipped) | 22-61 % (mean 44) | 16-52 % (mean 30) | 0 |

## Verification
- Headless, 8 seeds a model: the table above.
- Browser bot, real taps: B cleared in 5 of 5 runs with 34 / 34 / 52 / 32 / 39 % walls. C on the live build:
  18 / 23 / 31 %. C on the fix at 60 fps: 27 / 26 % (measured with the first, heavier slam).
- The slam's own share was measured at about 1-1.5 % of the walls a blow, about 10 % over the boss's life.
- **Not verified:** the final build's C runs at 60 fps. The machine went into low-power mode before they ran
  (see Gotchas, 4).

## Gotchas
1. **A pure bug fix made the stage harder for one kind of player.** **Cause:** the stage was tuned around the
   bug. **Fix:** treat any fix that changes what an enemy can do, or what the player can reach, as a balance
   change and gate it with the player models.
2. **The new attack looked like the whole cost and was not.** At 1 strike a slam, the slams take about 10 % of
   the walls over the boss's life, yet C's worst seed went from 31 % to 16 %. The walk-in alone moved C the
   other way (36-44 %). The rest is the fight changing shape once the boss is in view and striking. The
   sources do not split that remainder by source of damage.
3. **The strong model moved and the weak one did not.** B's mean rose (41 → 44 %) while C's fell (35 → 30 %).
   A single "difficulty went up" number would have been wrong for both.
4. **Browser results depended on the machine.** On the same final build C ended with 16 % and lost once while
   the laptop was in low-power mode at 30 fps; the live build in the same conditions gave 23 / 31 %. Compare
   builds under the same conditions and say which.
5. **Wide ranges on few seeds.** C's range on the fix is 16-52 %. Eight seeds show that nobody lost; they do
   not show a 5-point shift in the mean with any confidence. Report the range.
6. **The version label drifted.** The fix was written up as 2.3.5 while another branch shipped under that
   number; it went out in build 2.3.6. Name the base commit of a comparison, not only a version.

## Open questions
- If the heavy tapper must keep 20 % or more, the lever is the ×2 boss's health multiplier or the adds of its
  wave. That decision was left to the owner of the numbers.
- Which damage source took C's missing margin (crowd contact, the boss's strikes, the stomp) was not measured
  separately. A per-source wall-damage counter in the headless run would answer it.
