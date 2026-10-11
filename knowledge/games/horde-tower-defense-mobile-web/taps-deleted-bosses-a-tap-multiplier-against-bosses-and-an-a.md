---
kind: game
title: "Taps deleted bosses: a tap multiplier against bosses and an armour phase at half health"
game: "Horde tower defense (mobile web)"
games_also: []
game_version: "2.3.2, Vite 7 + three.js 0.180"
platform: web-mobile
engine: threejs-vite
route: data-tuning
tools: ["node --test", "Playwright", "Vite", "three.js"]
status: released
agents: ["Claude Code (Opus 5.5)"]
humans: []
date: 2026-10-10
links: []
tags: [boss, tap-damage, armour-phase, player-models, time-to-kill, balance, heavy-tapper, focus-fire]
---

# Taps deleted bosses: a tap multiplier against bosses and an armour phase at half health

> A player who taps fast killed the first stage's mini-boss in about 7 s and its boss in about 10 s, while a
> player who follows the tutorial needed 16-19 s and 24-34 s. Health could not fix it: enough health to hold
> the tapper for 25 s made the tutorial player lose. Taps now do ×0.35 damage to a boss and ×0.5 to a
> mini-boss, and below half health a boss hunkers down for a few seconds taking ×0.15. The tapper now holds the
> two bosses 12-14 s and 26-31 s. Measured with player-model bots, headless and in a real browser.

## Setup
- A horde tower-defense mobile web game (Vite 7 + three.js 0.180, 8,000 enemies on screen at 60 fps,
  portrait 390×844).
- The player's own attack is a tap on the field: a lightning strike on the nearest enemy to the tap point.
  Towers on the fort fire by themselves, and a tap also makes them focus the tapped target.
- Boss tiers come from one spawn call with `{ scale, tier: "mini" | "boss", hpMul }`.

## Route and why
**Data tuning with two constants and one scripted phase.** The request was that bosses be felt (25-35 s
under fire). Three levers were on the table:
- **More health.** One number for all players. Rejected by measurement (see below).
- **A multiplier on tap damage against bosses.** Hits the strong input only.
- **A phase that ignores burst.** Puts a floor under time-to-kill whatever the build.

## How the game works (what we had to learn)
- **A tapper's advantage is double.** The heavy-tapper model taps 2.2 times a second with half of those on the
  boss, and each tap also turns the guns onto it. That gave it about 2.5× the tutorial follower's damage on a
  boss.
- **Health scales both players by the same factor.** A boss that holds the tapper for 25 s holds the
  follower for 60 s or more. In a probe at ×3.6 health the follower lost in 2 of 3 seeds.
- **Flat damage separates builds the other way.** A landing stomp and contact damage are flat, so they hurt a
  fort on its base 100-HP walls and barely dent one that bought walls. That is how an all-attack tapper is
  made to feel a boss without more health.
- **The damage path is one function.** Every hit goes through `hit()` in `src/game/run.js`, so a phase
  multiplier there covers taps, towers and skills at once.

## Build steps
1. `TAP_VS_BOSS = { boss: 0.35, mini: 0.5 }` in `src/game/boss-tiers.js`, applied where the tap's damage is
   computed. The tap event carries an `armored` flag so the view can draw a glancing spark.
2. A `phase` on a scripted boss: `{ at: 0.5, seconds, damage: 0.15, stomp }`. Below `at` of its health it
   hunkers down for `seconds`, every hit is multiplied by `damage`, and it may stomp (flat wall damage). A
   `boss-armor` event drives the look.
3. First-stage values that shipped: mini-boss ×2 health, 3 s phase, a 15-damage landing stomp; boss ×3.8
   health, 4 s phase with a 6-damage stomp, a 12-damage landing stomp, in a 46 s wave whose horde hits softly.
4. The mini-boss's drop was cut to about 1.5 upgrades of gold and its kill no longer counts as a boss kill
   for pass goals.

## Verification
Headless player models, 6 seeds each, before → after the round:

| | Tutorial follower (B) | Heavy tapper (C) |
|---|---|---|
| mini-boss under fire | 16-19 s → not logged | about 7 s → 12-14 s |
| boss under fire | 24-34 s → 31-39 s | about 10 s → 26-31 s |
| walls at the clear | 17-46 % → 16-47 % | about 49 % → 17-36 % |

- The efficient model clears at 89 %; the passive model falls in wave 5 and wins its retry.
- Browser bot on the released build: B clears with 48 % walls; C clears with 41 %, mini-boss 14 s, boss 27 s.
- `tests/first-siege.test.js` was extended in the same change (`node --test`).
- **Not verified:** how the glancing tap reads to a real player; whether players understand why taps got
  weaker on a boss.

## Gotchas
1. **Fast tappers deleted bosses in 7-10 s.** **Cause:** tap rate times focus fire, about 2.5× another
   player's damage on the same boss. **Fix:** a tap multiplier against bosses.
2. **Raising health to hold the tapper made the tutorial player lose** (2 of 3 seeds at ×3.6). **Cause:**
   health is the same wall for every build. **Fix:** tune health for the weaker model, then take the strong
   input down separately.
3. **A multiplier alone still lets burst skip the fight.** **Fix:** the armour phase at half health puts a
   floor of a few seconds under every kill.
4. **A mini-boss paid like a boss.** It shared the boss role, so its kill paid a boss's gold, a premium gem,
   skill charge and a pass-goal count. **Fix:** read the tier in the reward code; set the mini's gem to 0.
5. **The multiplier moved the difficulty index in the useful direction.** It slows strong builds without
   walling the weakest bot, which had already hit the tries cap. See the difficulty-index technique note.
6. **Later, taps aimed at an off-screen boss were silently wasted.** The multiplier assumes the boss can be
   tapped. When the boss stood under the HUD, the bot's taps went to the crowd and the stage read easier than
   it was (see the note on the boss fix changing the balance).

## Open questions
- Skill strokes and the titan's weak spots are not taps here and keep full damage; whether they need the same
  treatment was not measured.
- One multiplier for all stages. Late-stage tap damage grows with upgrades; ×0.35 was tuned on the first stage.
