---
kind: game
title: "The first stage as a rising sine: odd waves push, even waves let the player spend"
game: "Horde tower defense (mobile web)"
games_also: []
game_version: "2.3.2 (table as of 2.3.5), Vite 7 + three.js 0.180"
platform: web-mobile
engine: threejs-vite
route: design
tools: ["node --test", "Playwright", "Vite", "three.js"]
status: released
agents: ["Claude Code (Opus 5.5)"]
humans: []
date: 2026-10-10
links: []
tags: [first-session, pacing, wave-design, sine, mini-boss, boss, scripted-waves, economy, player-models, onboarding]
---

# The first stage as a rising sine: odd waves push, even waves let the player spend

> The first three minutes were called boring and monotonous: an even trickle of walkers whose count rose in a
> straight line, and walls that stayed at 100 %. The stage is now one data table, ten waves on a rising sine.
> Pushes arrive as packs from one to three sides; breathers bring a reason to spend; wave 5 has a mini-boss
> and wave 10 a boss at twice the size. The longest stretch with nothing new went from 17-24 s to 6-8 s.
> Checked with four player-model bots headless (6 seeds each) and in a real browser.

## Setup
- A horde tower-defense mobile web game (Vite 7 + three.js 0.180, 8,000 enemies on screen at 60 fps,
  portrait 390×844).
- A stage is 10 waves of 18.4 s. Before this change every stage, the first included, came from the same
  generator: a body count per wave, arriving evenly.
- The script lives in `src/game/first-siege.js` as `FIRST_SIEGE.waves`: pure data, one entry per wave. The
  run calls it at three points: wave start (plan), step (spawn what is due) and kill (wave gold, mini-boss pay).
  It is on for the first stage of the first chapter only.

## Route and why
**Design as a hand-written table for one stage, generator for the rest.** The first session decides whether a
player stays, and a generator tuned for every stage cannot also place a beat every few seconds. A table is
cheap to read, diff and test, and it leaves every other stage unchanged. The engine side (boss tiers by
scale, a gold-carrying walker, boss-wave cues) was built behind an agreed spawn API so the table could be
tuned in parallel.

## How the game works (what we had to learn)
- **Pressure is count × health, and the start is limited by shots.** The starting gun fires 1.65 shots a
  second. With walkers that take three hits, 30 % more bodies made every bot lose. The opening therefore has
  fewer, tougher bodies; they live longer, so the field still looks fuller.
- **An even stream reads as nothing happening.** The same bodies arriving as a pack from the side, or as a
  runner squad, are a beat.
- **A breather needs a job.** A quiet wave with nothing to do is the boring stretch again. Here it carries
  gold: two gold-carrying walkers, and the mini-boss's drop.
- **Income should follow pressure.** Each wave has a gold multiplier for bodies born in it.
- **Starting gold hides the loop.** The stage opened on 60 gold; the player bought before killing anything.

## Build steps
The table that shipped (bodies and time are multipliers on the old wave):

| Wave | Bodies | What happens | Beat |
|---|---|---|---|
| 1 | ×1, gold ×2.2 | two small packs, the first close enough to kill within 3 s | arrival |
| 2 | ×2.6, tougher ×1.3 | a 15-strong pack 20 m out at 2 s, then two packs 80° apart | first rush |
| 3 | ×2 | a small giant under fire, a runner squad with a pack behind it at 10 s | runners |
| 4 | ×0.35 | spread walkers, two gold carriers at 3 s and 13 s | spend |
| 5 | ×1.45 | packs from two sides; the mini-boss (scale 0.7) strides in and stomps 13 m out | mini-boss |
| 6 | ×0.6 | walkers only | breather |
| 7 | ×1.15 | packs from three directions 60° apart, plus runners | flank |
| 8 | ×1.2 | two brutes with an escort on two sides | brutes |
| 9 | ×0.4 | war drums and a reddening sky; a rising stream from 10 s | calm, then build |
| 10 | ×1.25, time ×2.5 | a 46 s wave; the boss at scale 2 and ×3.8 health; packs through to 40 s | boss |

Around the table:
1. Open on 6 gold, with ×2.2 kill gold in wave 1, so the first card is bought from the first kills.
2. Group fields: when it arrives, over how long, what share of the wave, kind, how many sides and how far
   apart, and a beat name the presentation can cue. Leftover bodies come in small clumps every 4.5 s.
3. Random pack bearings stay within ±50° of straight down the screen, because a phone shows about 16 m either
   side of the fort.
4. The mini-boss pays 3 walker kills of gold and no premium gem; a boss pays 10 and a gem.
5. The rescue gift is offered after a fall from 1.25 minutes of battle (was 2), so a fall at the mini-boss
   brings it.

## Verification
Targets were written per player model before tuning; results after the first round (headless 6 seeds;
browser runs A×2, B×3, C×3, D×2 agree):

| Model | Target | Headless | Browser |
|---|---|---|---|
| A passive (taps, buys nothing) | falls at waves 5-6; the retry is winnable | falls in wave 6 at 1:32, 6 of 6; blessed retry won at 90-94 % | falls in wave 6; retry won |
| B tutorial follower | wins; 40-70 % walls at wave 5; ends 25-60 % | wins 6 of 6; 56-71 % at the mini-boss; ends 17-46 % | ends 26 / 31 / 36 % |
| C heavy tapper | wins; dips under 75 % at both bosses | 74 % and about 50 % | 74 %; 42 / 50 / 50 % |
| D efficient | wins at 70 % or more | 82-84 % | 82 %, 82 % |

- Follower's alive count per wave, old → new: wave 4 mean 11.2 → 4.4 (the breather), wave 5 mean 17.6 → 36.5
  with a peak of 55 (the mini-boss). Wall damage in the first four waves stayed at zero in that round; a later
  round made waves 2 and 3 pushes that touch the walls.
- The table above is the third round. Its headless results (6 seeds): the heavy tapper wins at 17-36 %, the
  follower at 16-47 %, the efficient model at 89 %, and the passive model falls in wave 5 and wins its retry.
- Chapter-level numbers did not move in the first round: 29 tries and 107 gems for the casual-human bot.
- `node --test`: 479 passing at the time; 60 fps at 8,000 enemies; browser regression clean.
- **Not verified:** a real new player. Every number here is a bot.

## Gotchas
1. **"Boring for three minutes."** **Cause:** a linear ramp delivered as an even trickle; alive count rose flat
   from 0 to 25 and the walls never dropped. **Fix:** a sine on a rising line, with named beats.
2. **A plot of alive count looked fine and the stage was still dull.** **Cause:** wall damage was zero for the
   first minute. **Fix:** plot alive count and wall damage per wave, and the longest gap between beats.
3. **More bodies made everyone lose.** **Cause:** the opening is shot-limited (see above). **Fix:** fewer,
   tougher bodies at the start; count rises later, when the fort has more guns.
4. **Sixty starting gold removed the first decision.** **Fix:** 6 gold, and richer kills in wave 1.
5. **The passive player fell too late to be rescued.** Before, it fell in waves 7-8 and the rescue gift came
   in 1 of 3 seeds. **Fix:** the mini-boss is the wall for a player who buys nothing, and the gift's threshold
   sits just before it.
6. **The mini-boss's drop was worth about two upgrades when the design said 1.5**, and it counted toward boss
   goals. The drop file belonged to another worker. **Fix:** it was reported, then cut in the next round.
7. **A boss twice the size hid the fort.** **Fix (engine side):** the model stands off from its simulated
   body, is dithered where it covers the fort, and the camera pulls back while it lives.

## Open questions
- The table is tuned to one starting loadout. A returning player replaying the stage with meta upgrades was
  not measured.
- Later stages still use the generator; whether they need the same treatment is undecided.
