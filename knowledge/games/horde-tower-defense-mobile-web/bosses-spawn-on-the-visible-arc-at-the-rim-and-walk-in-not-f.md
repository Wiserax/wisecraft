---
kind: game
title: "Bosses spawn on the visible arc at the rim and walk in, not from under the HUD"
game: "Horde tower defense (mobile web)"
games_also: []
game_version: "2.3.5 (found on live 2.3.4, released in build 2.3.6), Vite 7 + three.js 0.180"
platform: web-mobile
engine: threejs-vite
route: design
tools: ["node --test", "Playwright", "Vite", "three.js"]
status: released
agents: ["Claude Code (Opus 5.5)"]
humans: []
date: 2026-10-11
links: []
tags: [boss, spawn, bearing, hud, portrait, camera, entrance, stomp, pacing, determinism, spawn-stream]
---

# Bosses spawn on the visible arc at the rim and walk in, not from under the HUD

> Players saw bosses "appear right next to the base". Two causes. Stage bosses took a random bearing around
> the fort, and the bearings toward the camera lie under the bottom dock in portrait, so a boss stepped out
> from under the UI a few metres from the wall. And the first stage's scripted bosses were placed 13 m and
> 15 m out on purpose, to land their entrance stomp. Every boss now starts on the spawn ring inside the arc the
> player can see and walks in; a scripted boss strides in fast and stomps when it reaches its script distance.

## Setup
- A horde tower-defense mobile web game (Vite 7 + three.js 0.180, 8,000 enemies on screen at 60 fps,
  portrait 390×844).
- The battle camera is orthographic, fixed, looking down at the fort from one corner. In portrait a phone
  shows about 16 m of ground either side of the fort and about 35 m below it; the upgrade dock covers the
  ground toward the camera.
- The horde spawns on a ring 27-35 m from the fort (19-25 m in the very first wave).

## Route and why
**Design, written as data.** The rule ("you see it coming") is one table, `ENTRY` in `src/game/boss-tiers.js`,
and one function that maps a random draw to a bearing. Our reasoning against the alternatives: pulling the
camera back far enough to show the whole ring makes walkers too small on a phone, and moving the dock is a UI
redesign for a spawn problem.

## How the game works (what we had to learn)
- **Which bearings are visible is a property of the camera and the HUD, not of the map.** "Up the screen" is
  one world bearing (the direction straight away from the camera). The table stores it as `up` with a
  half-width `arc` of ±55°.
- **A boss's own walking pace is slow.** 0.68 m/s: from the rim to a stomp point 13 m out is 17 m, which
  would take 25 s of a wave that lasts 18.4 s. A walk-in needs its own speed.
- **The entrance stomp is balance, not decoration.** It deals a flat amount of wall damage at a scripted
  distance and time; the first stage's wall curve was tuned around it.
- **Spawns come from a seeded stream.** The same seed must give the same spawns whatever the combat rolls,
  or the balance simulations stop being comparable across builds.
- **Other large enemies were left alone.** The titan already starts 24 m out at the screen's left rim; giants
  are untouched. Only stage bosses and mini-bosses changed.

## Build steps
1. `ENTRY = { up, arc: ±55°, from: 30 m, stride: 2.4 m/s }`.
2. `entryBearing(u)`: map the spawn stream's **existing** draw `u` in [0, 1) to a bearing inside the arc. No
   extra random call, so every later spawn of the seed is unchanged.
3. Every stage boss and mini-boss starts on the horde's ring (27-35 m) at that bearing.
4. Scripted bosses of the first stage start `from` 30 m out at 0 s of their wave, on fixed bearings up the
   screen, and stride in at `stride` whatever speed modifier the horde has.
5. When a scripted boss reaches its script distance it stomps (the same flat wall damage as before), then
   walks on at its own pace. Until then its record carries an `arrive` flag, which is saved and restored with
   the run, so a reload mid walk-in does not skip or repeat the stomp.

Timing before and after, first stage:

| Boss | Before | After |
|---|---|---|
| mini-boss (wave 5) | placed 13 m out at 3 s, stomps on landing | starts 30 m out at 0 s, stomps 7.4 s into the wave |
| ×2 boss (wave 10) | placed 15 m out at 5 s, stomps on landing | starts 30 m out at 0 s, stomps 6.2 s into the wave |

## Verification
- `tests/boss-reach.test.js` (`node --test`): every stage boss starts at least 27 m out and inside the arc;
  the first stage's two bosses start more than 28 m out and stomp at their script distance.
- Player models before and after (8 seeds, headless): with the walk-in alone, the heavy-tapper model ends the
  first stage with 36-44 % of its walls against 31-40 % on the live build, so the walk-in itself did not make
  the stage harder.
- Main browser regression clean in Chromium, WebKit and Chromium at 320×568.
- **Not verified:** how the entrance reads on a real phone; landscape (the arc is written for portrait).

## Gotchas
1. **Bosses appeared a few metres from the wall.** **Cause:** a uniform bearing around the fort; the bearings
   toward the camera are under the dock. **Fix:** spawn inside the visible arc only.
2. **The scripted bosses also appeared close.** **Cause:** they were placed at their stomp distance so the
   stomp would land on a known beat. **Fix:** start at the rim, stride in, stomp on arrival.
3. **The stomp moved by several seconds.** Arrival is now 7.4 s and 6.2 s into the wave, not 3 s and 5 s.
   Anything timed to the stomp (music cue, wave-open ring, a balance script) must read the arrival event, not
   a clock.
4. **A walk-in at the boss's own pace never arrives.** See the 25 s figure above. **Fix:** a separate stride
   until the stomp, then its own pace.
5. **An extra random draw for the bearing would have shifted every later spawn of the seed.** **Fix:** reuse
   the draw the spawn already makes. The project keeps a spawn-stream test (same seed, same spawns over 60 s)
   for this class of change.
6. **A bot could not tap what it could not see.** While the ×2 boss stood under the dock, the browser bot's
   taps on the boss found no on-screen point and went to the crowd. Once the boss was visible, the bot's
   behaviour changed and so did its result. Count this as a balance change (see the related note).

## Open questions
- The arc is hard-coded for the portrait camera. A zoom button shipped in the same release; whether a wide
  zoom should widen the arc is undecided.
- Giants were not changed; whether they have the same problem was not checked.
