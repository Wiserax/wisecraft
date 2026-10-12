# Performance checks: frame time you can trust

Target: 60 fps at the stress count *and* in real late-stage play, with an adaptive quality guard that
recovers. Measure first; the cause is rarely the one in the complaint. "A slideshow from stage 7" turned out
to be a quality guard that never stepped back up, not an overload.

## 0. Is this machine fit to measure?
Check before every frame-time run and write it in the report.
- **On mains power, low-power mode off.** A laptop on battery in low-power mode caps the browser at 30 fps.
  It happened mid-task: 60/60/60 at the three stress counts, then a flat 30 twenty minutes later, on the live
  build as well. The giveaway is the flatness.
- **Measure the live build side by side:** same machine, same minutes, same script.
- **Nothing heavy alongside.** Parallel captures make noisy numbers, most of all at 4x CPU throttle.
- If you can't get a clean machine, report "60 fps not confirmed on the final commit" with the last good
  measurement, its commit and its time. Don't report 30 as a regression and don't report 60 from memory.

## 1. Two tests, always both
1. **Capacity:** spawn 2,000 / 5,000 / 8,000 enemies with the walls held; measure fps and p95 frame time.
   Target 60 fps, p95 ≤ 16.8 ms on a desktop-class machine.
2. **Real late-stage play:** a realistic save at the late stages, walls **not** held, real buys, boss and
   giants on screen. Desktop retina (1440x900 @2x), phone 390x844 @3x, and Chrome with 4x CPU throttle.
   Capacity misses sustained slow patches, the guard's state and effect bursts.

For real play use a bot that buys every upgrade it can afford (`wise qa --persona spender`, or a journey),
give the walls a health floor only so a loss can't end the run, run in real time and record every frame in
fixed windows (a mid wave and the boss of each late stage). Headless WebKit is noisy: single 30-34 ms frames
come and go between runs, so report a range from several runs.

`wise qa ... --max-p95 20` turns the p95 into a gate for a quick check; the windows above are the real test.

## 2. Budgets that worked (three.js, an instanced crowd)
- About 300k triangles a frame at peak (low-poly corpses, LOD or impostors for far giants), 60-70 draw
  calls, a shadow budget (only hero objects cast).
- No per-frame allocations in hot paths; no forced layout per frame (reading DOM sizes in the render loop).
- The crowd collision solver dominates the sim at thousands of bodies; one pass instead of two is a valid
  degradation step.

Where the profile found time on the source game:
- 400 corpses on the detailed mesh were more triangles than the living horde (460k → 300k a frame).
- A model read `canvas.clientHeight` every frame: a forced layout worth 2.4% of a boss wave's frame.
- The big sun shadow map was redrawn every frame; every third frame is enough for scenery.

**Prove the sim is unchanged** after optimising it: hash the old and new sim state over a few thousand steps
with the same seed. Identical hashes mean every balance table still stands; otherwise re-run the bots (the
**game-balance** skill).

## 3. Report
Start with what changed for the player ("stage 7 stays smooth; a slow moment clears within 25 s"). Then one
table: scene x device profile → fps, p95, frames over 33 ms, guard level, before and after. Then the machine
state (power, what else ran) and what was not measured. "No real phone and no real Safari" is the usual open
item; say it every time it is true.

## Done means
- 60 fps and p95 ≤ 16.8 ms at 2,000 / 5,000 / 8,000, measured on mains power.
- The late-stage windows hold 60 fps on the desktop and phone profiles; the 4x CPU profile is reported.
- The guard steps down under load and is back at full quality after the load ends, shown in a capture.
- Cold boot never ends on an endless splash.
- The browser gate is clean in all three runs.
