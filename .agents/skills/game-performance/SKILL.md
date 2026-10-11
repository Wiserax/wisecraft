---
name: game-performance
description: Find and fix lag in a web game and prove the fix with numbers. Covers the capacity test (2,000 / 5,000 / 8,000 enemies) plus real late-stage play, frame and draw budgets for three.js crowds, an adaptive quality guard that steps back up (the 60 Hz trap), load time on a throttled phone profile, a boot that retries a failed chunk instead of hanging, and why a laptop on battery in low-power mode invalidates every fps gate. Use when the user says "it lags", "slideshow from stage 7", "fps drops with the boss", "slow on my phone", "takes ages to load", "stuck on the splash", or before any release that changes rendering, simulation or assets.
---

# Game performance

Target: 60 fps at the stress count *and* in real late-stage play, with adaptive quality that recovers.
Measure first; the cause is rarely the one in the complaint. "Slideshow from stage 7" turned out to be a
quality guard that never stepped back up, not an overload.

## 0. Is this machine fit to measure?
Check before every fps run, and write it in the report.
- **On mains power, low-power mode off.** A laptop on battery in low-power mode caps the browser at 30 fps.
  Every build then reads a flat 30, and the gate fails for a reason that has nothing to do with the change.
  It happened mid-task here: 60/60/60 at the three stress counts, then a flat 30 twenty minutes later, on
  the live build as well.
- **Measure the live build side by side.** Same machine, same minutes, same script. If live reads 30 too,
  the machine changed, not the game. Do this before blaming the change.
- **Nothing heavy alongside.** A machine busy with parallel captures gives noisy numbers, most of all at 4×
  CPU throttle. Note it next to the table.
- If you can't get a clean machine, report "60 fps not confirmed on the final commit", with the last good
  measurement, its commit and its time. Don't report 30 as a regression and don't report 60 from memory.

## 1. Two tests, always both
1. **Capacity:** spawn 2,000 / 5,000 / 8,000 enemies with the walls held and measure fps and p95 frame
   time. Target 60 fps, p95 ≤ 16.8 ms on a desktop-class machine.
2. **Real late-stage play:** load a realistic save at the late stages (e.g. 7–9), walls **not** held, real
   buys, boss + giants + titan on screen. Test at desktop retina (1440×900 @2x), phone 390×844 @3x, and
   Chrome with 4× CPU throttle. Capacity tests miss what real play does: sustained slow patches, guard state
   and VFX bursts.

For the real-play test, use a bot that buys every upgrade it can afford, give the walls a health floor only
(so a lost fight can't end the run), run in real time and record every frame in fixed windows (a mid wave
and the boss of each late stage). WebKit headless is noisy: single missed refreshes of 30–34 ms come and go
between runs, so report it as a range from several runs.

## 2. Budgets that worked (three.js, instanced crowd)
- ~300k triangles per frame at peak (low-poly corpses, LOD or impostors for far giants), ~60–70 draw calls,
  a shadow budget (only hero objects cast).
- No per-frame allocations in hot paths; write instance matrices directly; no forced layout per frame
  (reading DOM sizes inside the render loop).
- The crowd collision solver dominates the sim at thousands of bodies; one pass instead of two is a valid
  degradation step.

What the profile found on the source game, as examples of where to look:
- 400 corpses on the detailed mesh were more triangles than the living horde (460k → 300k a frame with a
  crowd-level corpse mesh).
- A model read `canvas.clientHeight` every frame: a forced layout worth 2.4% of a boss wave's frame.
- The big sun shadow map was redrawn every frame; every third frame is enough for scenery.

**Prove the sim is unchanged.** Balance sims depend on the simulation. After optimising it, hash the state
of the old and the new sim over a few thousand steps with the same seed. Identical hashes mean every balance
table still stands; otherwise re-run the bots (the **game-economy** skill).

## 3. Adaptive quality guard
- When frames stay above ~22 ms for 2 s, step down whichever side costs more:
  - **sim:** 30 Hz steps → 1 step per frame → 1 collision pass;
  - **draw:** pixel ratio 1.25 → 1.0, shadows off.
- **It must recover:** step back up after sustained good frames using a threshold that a 60 Hz vsync can
  actually meet (frames ~16.7 ms, so "under 13 ms" never happens). Our first guard never recovered, and
  stage 7 stayed a slideshow for the rest of the siege.
- Expose its state (`__game.guard`) and include it in perf reports.

`references/quality-guard.md` has the recovery rule that worked and the test that proves it.

## 4. Load time
- Measure cold and warm loads on Fast 4G + 4× CPU: bytes, time to splash, hub, first siege, first sound
  after the first tap.
- Stage audio loading (UI first, battle later, idle prefetch), immutable cache headers for hashed assets,
  one-day cache for audio and art, and no orphan assets in the deploy.
- **Boot must never hang:** retry a failed chunk under a fresh URL, reload once, then show a Retry screen.
  Prove it with 60+ cold boots.

`references/load-and-boot.md` has the numbers and the fault matrix.

## 5. Report
Start with what changed for the player ("stage 7 stays smooth; a slow moment clears within 25 s"). Then one
table: scene × device profile → fps, p95, frames over 33 ms, guard level, before and after. Then the machine
state (power, what else ran), and what was not measured. "No real phone and no real Safari" is the usual
open item; say it every time it is true.

## Done means
- 60 fps and p95 ≤ 16.8 ms at 2,000 / 5,000 / 8,000, measured on mains power.
- The real late-stage windows hold 60 fps on the desktop and phone profiles; the 4× CPU profile is reported.
- The guard steps down under load and is back at full quality after the load ends, shown in a capture.
- Cold boot never ends on an endless splash.
- Tests still pass and the browser gate is clean (`wise qa`, the **browser-qa** skill).

## References
- `references/quality-guard.md`: the guard's levels, the 60 Hz trap in detail, the recovery rule and how to
  test it. Read it before writing or touching a guard.
- `references/load-and-boot.md`: staged audio, cache headers, the boot fault matrix and measured gains. Read
  it for "slow to load" or "stuck on the splash".
