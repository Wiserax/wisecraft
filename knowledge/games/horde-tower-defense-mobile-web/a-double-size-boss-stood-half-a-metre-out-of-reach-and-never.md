---
kind: game
title: "A double-size boss stood half a metre out of reach and never hit the wall"
game: "Horde tower defense (mobile web)"
games_also: []
game_version: "2.3.5 (found on live 2.3.4, released in build 2.3.6), Vite 7 + three.js 0.180"
platform: web-mobile
engine: threejs-vite
route: engine-code
tools: ["node --test", "Playwright", "Vite", "three.js"]
status: released
agents: ["Claude Code (Opus 5.5)"]
humans: []
date: 2026-10-11
links: []
tags: [boss, scale, attack-reach, wall-clamp, body-radius, collision, obstacles, node-test, bearings, slam]
---

# A double-size boss stood half a metre out of reach and never hit the wall

> The first stage ends with a boss at twice the normal size. It walked to the fort, stopped, and never struck:
> for three releases its wall damage was zero. Its body radius had doubled, the wall clamp holds a body at the
> wall edge plus its own radius, and the attack reach was a fixed 6.5 m from the fort's centre. Reach now
> starts at the body's own edge and spans one row of the crowd. A `node --test` case walks a scale-2 boss in
> from 36 bearings across the real map's obstacles and requires it to reach, damage and slam.

## Setup
- A horde tower-defense mobile web game (Vite 7 + three.js 0.180, 8,000 enemies on screen at 60 fps,
  portrait 390×844).
- One spawn call makes every stage boss: `run.spawnBoss({ scale, tier, hpMul })` (`src/game/boss-tiers.js`).
  The model, body radius, tap area, health bar and presence follow `scale`, which is clamped to 0.4-2.
- The simulation is `src/sim.js`; scenery collision is shared with `src/crowd-collision.js`.

## Route and why
**Engine code, with a geometry test as the oracle.** The report was "the big one collided with something and
stayed near the base; it should hit it". Two causes fit that sentence (wedged on scenery, or standing out of
reach), so the test had to tell them apart: place a boss alone on the real map and record whether it ever
enters the attacking state, from every direction.

## How the game works (what we had to learn)
- **Attacking is a distance test.** A body attacks when its centre is inside a reach radius around the fort.
  For ordinary bodies that radius was a constant of about 6.5 m (a little more for tall bodies).
- **The wall clamp is edge-based.** A body cannot come closer than the wall's radius plus its own radius.
- **Scale doubled the radius and nothing else.**

  | Body | Radius | Held by the clamp at | Reach |
  |---|---|---|---|
  | stage boss, scale 1 | 0.56 m | inside its reach | about 6.5 m |
  | stage boss, scale 2 | 1.12 m | 7.07 m (7.56 m behind a row of walkers) | 6.5 m: never attacks |

- **Giants already had the right rule.** A giant's body is wider than the reach band, so giants strike from
  their own edge. The scaled boss was not a giant by size class and missed it.
- **The model is not where the body is.** For looks, a scaled-up boss's model stands further out than its
  simulated body (2.6 m per unit of scale above 1, eased in near the fort) so it does not stand inside the
  walls. A screenshot cannot tell you where the body is; read the simulation.

## Build steps
1. One threshold for "a big body": `BIG_BODY` 0.7 m (today's stage boss is 0.56 m, so nothing existing changes).
2. Against scenery, a big body uses a walker's radius (0.35 m), the rule giants already had, in both the
   movement step and the crowd re-projection.
3. Reach for a big body = base reach + (its radius − 0.3) + `BIG_REACH` 0.7 m. The 0.7 m is one row of the
   crowd standing between it and the wall. At scale 2 that is about 8.0 m against a stand-off of 7.56 m.
4. Give the attack a shape the player can read. A boss of scale ≥ `WALL_SLAM.from` 1.3 at the wall rears up
   for 1.2 s and slams every 3.2 s. The wind-up and the blow are events that name the boss, so the right
   model plays them and the damage lands with the visible blow.
5. Set what a slam is worth last, with player models (see Gotchas, 4).

## Verification
`tests/boss-reach.test.js`, run with `node --test`:
- The real map's obstacle list is built in Node (more than 60 circles, radii from 0.4 m to over 1.2 m).
- A scale-2 boss with unlimited health starts 31 m out on each of 36 bearings (every 10°), alone, and the run
  steps at 60 Hz for 45 s. Assertions per bearing: it enters the attacking state, the wall loses health, and
  at least one slam is announced. A failure prints the bearing and how far out it stands.
- Slams are announced (a wind-up, then a blow) and the blow carries the damage.
- A default-size boss gets no slam cycle, so every other stage plays as before.

Also run: the full suite (516 tests), the main browser regression in Chromium, WebKit and Chromium at 320×568.

**Not verified:** a boss between scale 1.3 and 2 on the real map (the test uses 2); a scaled boss inside a
dense late-stage crowd; a real phone.

## Gotchas
1. **The boss walked in, stopped and did nothing.** **Cause:** the clamp held its body at 7.07 m (wall edge
   plus a 1.12 m radius) while the attack reach was 6.5 m, so `attacking` never became true. **Fix:** reach
   from the body's own edge plus one crowd row.
2. **It passed every earlier check.** The scaled boss was staged with a debug hook, tapped, killed and
   screenshotted when the feature was built; none of those checks asked whether the wall lost health. Its
   scripted landing stomp did damage the walls, which hid that its strikes never did, and the stage was tuned
   in that state. **Fix:** an assertion on the outcome (wall health went down from a strike), not on the
   animation.
3. **"Collided with something" was half right.** A 1.12 m body can also wedge on scenery, as a giant had two
   days earlier. The size-class rule did not cover a scaled boss. **Fix:** key the scenery rule on width
   (`BIG_BODY`), then test from every bearing on the real obstacle list, not on an empty field.
4. **The first slam was too strong.** A slam worth 3.2 ordinary strikes (one strike for every second it
   stands there) took about 25 % of the first stage's walls through the damage ramp, and the heavy-tapper
   player model lost 2 sieges in 8. **Fix:** a slam is worth 1 strike: about 1.5 % of the walls a slam, about
   10 % over the boss's life.
5. **The scenery module needs a canvas in Node.** The map's obstacles are built together with its art.
   **Fix:** a no-op stand-in for `document` during the import, removed afterwards, and export the obstacle list
   from the test for other tests to reuse.
6. **Any constant measured from the centre breaks when a body scales.** Reach, tap radius, stomp distance,
   camera framing and health-bar width each needed the same question: is this measured from the centre or from
   the edge?

## Open questions
- The balance effect of a boss that now strikes is its own note (the heavy-tapper model lost margin).
- `BIG_REACH` is one crowd row. Behind two rows a scale-2 boss may again stand outside its reach; not tested.
