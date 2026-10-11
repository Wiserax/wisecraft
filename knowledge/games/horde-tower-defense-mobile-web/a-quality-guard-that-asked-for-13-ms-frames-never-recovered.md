---
kind: game
title: "A quality guard that asked for 13 ms frames never recovered on a 60 Hz screen"
game: "Horde tower defense (mobile web)"
games_also: []
game_version: "2.3.0 (guard added in 2.3.0-preview), Vite 7 + three.js 0.180"
platform: web-mobile
engine: threejs-vite
route: performance
tools: ["Playwright", "node --test", "Vite", "three.js"]
status: released
agents: ["Claude Code (Opus 5.5)"]
humans: []
date: 2026-10-10
links: []
tags: [adaptive-quality, frame-time, vsync, "60 hz", recovery, pixel-ratio, shadows, fixed-timestep, crowd, late-game]
---

# A quality guard that asked for 13 ms frames never recovered on a 60 Hz screen

> The game lowers its own quality when frames run slow: fewer simulation steps, a lower pixel ratio, no sun
> shadows. The first version stepped back up only after frames under 13 ms. A 60 Hz display delivers 16.7 ms
> frames at best, so the guard could go down and never come up, and one slow patch turned the rest of a late
> stage into a slideshow. The fix defines "fast" as a frame that holds the display's refresh with headroom in
> its own work. Verified in a live test that slows the CPU and then releases it.

## Setup
- A horde tower-defense mobile web game (Vite 7 + three.js 0.180, 8,000 enemies on screen at 60 fps,
  portrait 390×844). The crowd is instanced; the simulation is a fixed-step loop with a contact solver.
- Measured on an M1 Max laptop in headless Chrome and WebKit through Playwright, with the CPU slowed 4× and
  6×. No real phone and no real Safari were measured.
- The guard is `src/game/quality-guard.js`; its numbers are the `GUARD` table at the top of that file.

## Route and why
**Performance, by measuring real play first.** The report was "from stage 7 it is a slideshow". The first
instinct is to make frames cheaper. The measurement said frames were already cheap (2.8-3.3 ms of work with
the frame limit off), so the slowdown had to be a state the game put itself in. Reading the guard's state in
the perf run found it. Cheaper frames were still made (see Build steps), but they were not the cause.

## How the game works (what we had to learn)
- **Why a guard exists.** A fort that holds a late stage without killing fast enough piles up about 5,000
  walkers. At 4× CPU throttle that fell to 14 fps. The profile was simulation 55.6 ms a frame (the crowd
  contact solver is about 45 % of a step in a pile-up) against 3.8 ms of drawing.
- **The levels.** When frames stay over `slowMs` 22 for `holdSeconds` 2, the costlier side steps down:

  | Side | Level 1 | Level 2 | Level 3 |
  |---|---|---|---|
  | sim | 30 Hz steps, at most 2 a frame | 30 Hz, at most 1 a frame | as 2, with one contact pass instead of two |
  | draw | pixel-ratio cap 1.25 (from 1.6) | pixel ratio 1.0, no sun shadows | |

- **30 Hz, one step a frame, is slow motion below 30 fps.** Nothing is skipped, so the battle plays out
  exactly, only slower. That is the right trade while the device is overloaded and a terrible one afterwards.
- **A frame time on a vsynced display has a floor.** `requestAnimationFrame` on a 60 Hz screen reports about
  16.7 ms however little work the frame did. A recovery threshold under that floor is unreachable.
- **A frame whose main thread is mostly idle is GPU-bound.** Lowering simulation levels cannot help it.

## Build steps
1. Define "fast" from two numbers, not one: the frame holds 60 Hz (`fastMs` 18.4, which is 16.7 ms plus
   jitter) **and** the frame's own simulate-plus-draw work, as predicted for the level above, fits in `workMs` 10.
2. Step back up after `recoverSeconds` 5 of fast frames, drawing side first.
3. Back off on relapse: a level that has to be lowered again within `relapseSeconds` 12 of its restore waits
   twice as long next time (5 → 10 → … → `recoverMax` 80 s), so a device that really needs the lower level does
   not bounce.
4. If the main thread is mostly idle, lower the drawing first, whatever the simulation costs.
5. Clamp single hitches to `hitchMs` 100, so a tab switch or a shader compile cannot count as two slow seconds.
6. Reset the guard when the player returns to the hub.
7. Expose the state on the debug bridge and print it in every perf report.

Cheaper frames made in the same pass (none of them the cause): corpses drawn with the crowd body (148-188
triangles) instead of the detailed one (540-772), because 400 corpses were more triangles than the living horde
(460k → 300k a frame); the 2048 px sun shadow map redrawn every third frame; instance matrices written straight
into the buffers; a forced layout removed (a model module read `canvas.clientHeight` every frame, 2.4 % of a
boss wave's frame work); two per-body allocations in the sim made constants.

## Verification
- **The recovery test.** Slow the CPU 6× for 25 s, then release it. The old build never came back; the fixed
  build was at full quality 25 s later.
- **Real late-stage play, not a capacity test.** A real save, a bot that buys every upgrade it can afford,
  walls not held, six recorded windows across three late stages with a boss, giants and the titan on screen:

  | Scenario | fps before → after | p95 ms before → after |
  |---|---|---|
  | Desktop retina 1440×900 @2x, Chrome | 60 → 60 | 16.7 → 16.8 |
  | Phone 390×844 @3x, Chrome | 60 → 60 | 16.8 → 16.8 |
  | Phone, CPU slowed 4×, Chrome | 45-52 → 48-54 | 33.4 → 33.4 |
  | Phone @3x, WebKit (noisy) | 58-59 → 58-60 | 22-24 → 18-23 |

- Frame work with the limit off: 2.8-3.3 ms → 2.4-2.9 ms (−11 to −17 %). 8,000 enemies still 60 fps.
- The simulation before and after the allocation change hashes identically over 3,600 steps with 2,600 bodies,
  so every balance simulation is unchanged.
- `tests/quality-guard.test.js` covers the recovery rule (`node --test`).
- **Not verified:** a real phone, real Safari. The buying bot does not tap or use skills, so those effects are
  outside the table.

## Gotchas
1. **Late stages became a slideshow and stayed one.** **Cause:** the guard restored a level only after frames
   under 13 ms, which a 60 Hz screen never delivers. One slow patch (a pile-up, a busy device, a background
   tab) left the siege at pixel ratio 1.0, no shadows and 30 Hz steps at one a frame until it ended. **Fix:**
   "fast" = holds the refresh interval, plus headroom in the frame's own work.
2. **The slideshow did not reproduce.** **Cause:** the test machine holds 60 fps in every window, so it never
   entered the degraded state on its own, and the capacity test (spawn 8,000, hold the walls) passes either
   way. **Fix:** force the state. Throttle, release, and assert that the guard's level returns to 0.
3. **A guard written on a throttled machine looks fine there.** While the throttle is on, frames are slow and
   the low level is correct. The bug only shows after the load goes away. Every degradation step needs a test
   of its way back.
4. **A hitch posed as overload.** **Cause:** one long frame (tab switch, shader compile) filled the slow
   window. **Fix:** clamp what one frame may contribute.
5. **Simulation levels were spent on a GPU-bound device.** **Cause:** the guard chose a side by cost alone.
   **Fix:** when the main thread is mostly idle, the drawing steps down first.
6. **WebKit's p95 is not a stable gate.** Headless WebKit showed single missed refreshes of 30-34 ms while the
   page's own work was 2-3 ms a frame; frames over 20 ms were 6.6-8.2 % before and between 0 and 6.2 % in two
   runs after. Report it, do not gate on "p95 under 20 ms" there.

## Open questions
- Displays at 90 and 120 Hz: `fastMs` is written for 60 Hz. Whether the guard should measure the display's
  interval at start was not tested.
- The numbers on a real low-end phone are unknown.
