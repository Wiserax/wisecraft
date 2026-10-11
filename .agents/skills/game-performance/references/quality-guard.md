# The adaptive quality guard

A guard lowers quality when the device can't keep up. The hard part is coming back.

## Why it exists
With long waves, a fort that holds without killing fast enough piles up about 5,000 enemies. At 4× CPU
throttle that fell to 14 fps. The profile: simulation 55.6 ms a frame (the crowd contact solver about 45% of
a step), drawing 3.8 ms. So the sim side needs levels too, not just the renderer.

## Levels
Frames over ~22 ms for 2 s step down the costlier side.

| Side | Level 1 | Level 2 | Level 3 |
|---|---|---|---|
| Simulation | 30 Hz steps, at most 2 a frame | at most 1 step a frame | one crowd-contact pass instead of two |
| Drawing | pixel ratio 1.25 | pixel ratio 1.0, sun shadows off | |

No enemy count, HP, damage or table changes. A device that holds 60 fps never leaves level 0. Returning to
the hub resets the guard.

Result of the first version: the lowest 20 s window at 4× CPU went from 14 fps to 37 fps at 5,377 alive.

## The 60 Hz trap
The first version stepped back up after 5 s of frames under 13 ms. On a 60 Hz screen a frame is never
shorter than 16.7 ms: vsync holds it there however little work the page does. So the restore condition could
not be met.

One slow patch (a pile-up, a busy device, a background tab) and the fight stayed at pixel ratio 1.0, no
shadows, 30 Hz steps and one step a frame until it ended. One step a frame below 30 fps is slow motion. The
producer saw "a slideshow from stage 7". On the test machine the build held 60 fps in every late-stage
window, with a frame costing about 3 ms of work; the guard alone was the bug.

**The live test that showed it:** slow the CPU 6× for 25 s, then return to full speed. The old build never
came back. The fixed one was at full quality 25 s later.

## The recovery rule that worked
- **"Fast" means the frame holds the refresh with headroom for the level above,** not "shorter than vsync
  allows". Two thresholds: the frame interval (about 18.4 ms at 60 Hz) and the main-thread work inside it
  (about 10 ms). Measure work, not just the interval.
- **Back off when a restore relapses.** A level lowered again within 12 s of its restore waits twice as long
  next time (5 s up to 80 s). Otherwise the guard flaps.
- **Find the limiting side.** A frame whose main thread is mostly idle is GPU-bound: lower the drawing
  first.
- **Clamp hitches** to 100 ms, so one long frame (a tab switch) doesn't count as two seconds of bad frames.

## Test it
- Unit test the pure rule: feed frame times, assert levels and restore times, including 16.7 ms frames
  forever (must restore) and a relapse (must back off).
- The live test above, as a capture with the guard state on screen.
- Expose the state (`__game.guard`) and print it in every perf table. A table that says 60 fps while the
  guard sits at pixel ratio 1.0 is a different result.
- Screenshot check: at level 0 the picture must not change. Before/after battle shots differed no more than
  two loads of the same build (0.49% vs 0.45% of pixels).
