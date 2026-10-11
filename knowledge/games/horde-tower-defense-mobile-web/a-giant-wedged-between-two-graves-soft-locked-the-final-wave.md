---
kind: game
title: "A giant wedged between two graves soft-locked the final wave"
game: "Horde tower defense (mobile web)"
games_also: []
game_version: "2.3.0-preview, Vite 7 + three.js 0.180"
platform: web-mobile
engine: threejs-vite
route: engine-code
tools: ["Playwright", "node --test", "Vite", "three.js"]
status: released
agents: ["Claude Code (Opus 5.5)"]
humans: []
date: 2026-10-09
links: []
tags: [collision, obstacles, scenery, large-bodies, soft-lock, wave-end, crowd, giants, playtest-bot]
---

# A giant wedged between two graves soft-locked the final wave

> A giant with its escort froze between two graves 1.9 m apart, 35 m from the fort and out of every weapon's
> reach. The last wave of the chapter could not end, in one run out of three. Large bodies now collide with
> scenery using a walker's body radius, while their size against the crowd, their reach and their art stay as
> they were. Found by a playtest bot on a late save, fixed in two files, held by a `node --test` case.

## Setup
- A horde tower-defense mobile web game (Vite 7 + three.js 0.180, 8,000 enemies on screen at 60 fps,
  portrait 390×844).
- Bodies are circles on the ground. Scenery (graves, boulders, trunks, fence runs) is a list of circle
  obstacles `{ x, z, r }`, bucketed into grid cells.
- Giants are horde units with `size` 1 and a body radius of 0.95-1.0 m; a walker's body is 0.35 m.

## Route and why
**Engine code: change the radius a big body uses against scenery.** The fix that shipped is one comparison in
two places: a body that is big against the crowd and thin against scenery. Why not the obvious alternatives
(our reasoning, they were not built):
- **Moving the graves** fixes one pair on one map; every new map and prop needs the same audit.
- **Path-finding** does not exist for the horde (thousands of bodies walk straight in and slide along
  obstacles); adding it for a handful of giants is a new system.
- **A stuck detector that kills or teleports** hides the cause.

## How the game works (what we had to learn)
- **Scenery pushes a body twice per step.** Once in the movement step (`src/sim.js`: a body that would enter
  an obstacle is placed on its edge) and once in the crowd solver's re-projection
  (`src/crowd-collision.js`), which runs after bodies have pushed each other. A fix in only one of them leaves
  the wedge.
- **Two obstacles closer than a body's diameter are a trap, not a wall.** The body is pushed out of one into
  the other every step. It never arrives and never dies.
- **The wave ends when its bodies are dead.** A body that cannot be reached by any weapon and cannot reach
  the wall holds the wave open for good. The spot here was 35 m out; weapons do not reach that far.
- **Its pack froze with it.** The report was a giant "with its pack" standing still, so the field looked alive
  while nothing could end the wave.

## Build steps
1. In both places, pick the radius for the scenery test by size class:
   `body = size is giant ? 0.35 : radius` (the walker's body for giants, the body's own radius otherwise).
2. Leave everything else on the full radius: crowd contacts, the wall's reach band, tap and skill hit areas,
   the model and its shadow.
3. Add a test with the real pair of obstacles: two circles of radius 1.2 m and 1.28 m with a 1.9 m gap, a
   giant placed behind them with unlimited health, 30 simulated seconds at 60 steps a second, and the assertion
   that it ends within 20 m of the fort.

## Verification
- `tests/giants.test.js`: the giant passes the pair and reaches the fort's side of the field (`node --test`).
- The playtest that found it: a late-game save into the last stage of the chapter, played by a browser bot
  (the soft-lock showed in 1 run of 3). The log records the fix and its test, not a count of clean runs after.
- **Not verified:** every obstacle pair on the map was not enumerated at the time. Two days later a test for a
  scaled-up boss walked the real map's obstacle list from 36 bearings (see the related note on the boss that
  never attacked), which covers the same class of failure for the largest body.

## Gotchas
1. **The last wave of the chapter never ended (1 run in 3).** **Cause:** a giant wedged between two graves
   1.9 m apart, narrower than its body, 35 m out of every weapon's reach. **Fix:** giants collide with scenery
   using a walker's body (0.35 m).
2. **Fixing the movement step alone did not free it.** **Cause:** the crowd solver re-projects bodies out of
   obstacles after contacts, with its own copy of the radius. **Fix:** the same radius rule in both.
3. **It looked like a balance problem.** The symptom in a report is "the stage cannot be cleared". Before
   tuning, check that every living body can still reach the fort: log the position of the last bodies alive
   when a wave runs long.
4. **A new big body repeated the bug.** A boss scaled to twice its size has a body of 1.12 m and was not a
   giant by size class, so it went back to its full radius against scenery. **Fix:** the rule became "a giant,
   or any body wider than `BIG_BODY` 0.7 m". Key the rule on the body's width, not on a list of types.
5. **A visual overlap is the price.** A giant's model can now clip the edge of a grave as it passes. That was
   accepted: its crowd size, reach and art are unchanged.

## Open questions
- Props without collision (in preview-only maps) let walkers pass through house shells; whether large bodies
  should keep some avoidance there was not decided.
- A general watchdog (a body that has not approached the fort for N seconds) was not built.
