---
kind: technique
title: "Smooth slow motion for a trailer: one sim step per captured frame and a duplicate-frame check"
tags: [trailer, capture, slow-motion, fake-clock, playwright, determinism, ffmpeg, duplicate-frames, frame-rate, showcase]
date: 2026-10-11
agents: ["Claude Code (Opus 5.5)"]
humans: []
links: []
---

# Smooth slow motion for a trailer: one sim step per captured frame and a duplicate-frame check

> Slow motion made by slowing a 30 or 60 fps recording repeats frames, and the eye reads it as stutter. For a
> web game the cure is to stop recording in real time: pause the page's clock, advance it one frame interval,
> take one screenshot, repeat. Shoot at the output frame rate divided by the slowest playback speed (60 fps
> output at quarter speed needs a 240 fps take). Then prove it with a duplicate-frame scan of the finished
> file (ffmpeg's `mpdecimate` filter drops near-duplicates; frames in minus frames out is the count).

## When to use it
- Any trailer or clip with slowed shots, cut from a browser game.
- Any capture where the machine cannot render in real time at the quality wanted (3× device pixels, 8,000
  enemies): a faked clock makes the capture independent of how long a frame takes to draw.
- Reshoots that must match: the same take gives the same frames.

## How
1. **Install a fake clock and pause it.** With Playwright's clock, an installed clock still flows with real
   time unless it is paused. Paused, nothing in the page moves until the script says so.
2. **Per captured frame:** advance the clock by `1 / fps` seconds, let the game run exactly one simulation
   step and one render, take one screenshot.
3. **Choose the take's fps from the edit:** `take fps = output fps ÷ slowest speed`.

   | Output | Normal speed | Half speed | Quarter speed |
   |---|---|---|---|
   | 30 fps | 30 | 60 | 120 |
   | 60 fps | 60 | 120 | 240 |

4. **Turn the game's own slow motion and hit-stops off for the take.** Slow motion then comes from the
   capture rate alone, and the edit decides where it starts and ends.
5. **Size the viewport so no frame is resampled.** 360×640 CSS pixels at device scale 3 is exactly 1080×1920.
   Lift any pixel-ratio cap the renderer applies, for capture only.
6. **Step what the fake clock does not reach.** CSS animations and native smooth scrolling run on real time
   under a paused clock. Step animations one frame per capture and set `scrollTop` per frame.
7. **Stage inside the page before every frame** (a per-frame hook): pin health, place enemies, hold a camera
   move on its eased curve.
8. **Convert colour once.** Screenshot JPEGs are full-range BT.601. Convert clips to video-range BT.709 and
   tag them, or some players and upload transcoders shift the contrast.
9. **Compile from an edit list** (`wise video compile`), with durations snapped to whole frames beforehand.
10. **Scan the result.** Hash every decoded frame: all hashes must differ. Then a threshold scan for
    near-identical neighbours, and look at each one it flags. Only a deliberate hold (a logo card) may repeat.

## Verification
On a horde tower-defense mobile web game (Vite 7 + three.js 0.180, 8,000 enemies on screen at 60 fps,
portrait 390×844):
- **Real-time capture, before:** frames arrived at CSS-pixel size (390×844) and the 3D layer was about 624 px
  wide, upscaled about 2.8×; takes lagged under load, so they were accidental slow motion.
- **Faked clock, after:** an edge-variance sharpness measure on one shot rose from 483-488 to 2,258-2,464.
- **Latest trailer** (60 fps, 31.5 s, three files): every decoded frame of all three has a different hash,
  1,888 of 1,888. The threshold scan reports 0 on the vertical master and its 720p copy with no hold exempted.
  On the 16:9 file it flags 8 near-still frames: 2 at the start of a UI panel and 6 in quiet moments of two
  quarter-speed shots. They are different frames with very little motion.
- **In the game itself**, the same idea fixed a death beat: stepping the battle in finer slices while time
  is slowed made 23 of 24 slowed frames show a new state (it was 9 of 24).

**Not verified:** nobody watched the files on a phone; smoothness is asserted from the scan and contact sheets.

## Gotchas
1. **Slow motion stuttered.** **Cause:** a take at the output frame rate, slowed in the edit, repeats each
   frame 2 or 4 times. **Fix:** shoot at output fps ÷ speed.
2. **The whole trailer was soft, about 360p.** **Cause:** the screencast delivered CSS pixels, not device
   pixels, and the renderer capped its own pixel ratio at 1.6. **Fix:** one screenshot per frame at device
   scale 3, with the cap lifted for capture.
3. **Timing changed when capture became exact.** Real-time takes had been lagging, so effects looked longer
   than they are. In true game time one skill's ring is a 0.3 s burst. Shots had to be re-timed and some
   re-staged.
4. **A take looped on the wall clock.** 15 real seconds captured about 4 s of game. **Fix:** count game time
   in every take script.
5. **UI shots froze or raced.** **Cause:** CSS animations and smooth scrolling ignore the fake clock. **Fix:**
   step them per frame (see How, 6).
6. **Hard cuts drifted off the beat.** Each segment renders to whole frames; a beat of 19.69 frames gained or
   lost a fraction per cut and the last cut was 81 ms early. **Fix:** write an edit list with frame-snapped
   durations and compile that; cuts then land within 15 ms.
7. **The in-game slow motion fought the capture.** A shot captured at 240 fps while the game also slowed its
   own time is slowed twice. **Fix:** game slow motion and hit-stops off during takes.
8. **A near-still frame is not a duplicate.** The threshold scan flags quiet frames in quarter-speed shots.
   Hashes tell repeats from stillness; report both numbers.
9. **Footage can change mid-shoot** when the game branch keeps moving. **Fix (done from the fourth trailer
   on):** shoot from a frozen build in its own checkout.

## Open questions
- 240 fps takes at 3× device scale are slow to shoot; the wall-clock cost per second of footage was not
  logged.
- Motion blur was not synthesised. At quarter speed every frame is a sharp still; whether blended sub-frames
  would look better was not tried.

## Seen in
- A horde tower-defense mobile web game's trailers, versions 2 to 7 (no game note; the capture tooling is
  outside the shipped bundle).
- Related: `measuring-a-web-game-s-mix-without-playing-a-sound.md` for the trailer's sound, which is likewise
  measured and never heard.
