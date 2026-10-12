# Deterministic capture

The goal: every captured frame shows a new game state, at full resolution, the same on every run.

## The method
1. **Serve a frozen build** on its own port. One browser context per take, muted, a fresh profile.
2. **Install a fake clock and pause it.** An installed clock still flows with real time unless paused.
3. **Per frame:** run the take's staging code in the page, advance the clock by `1 / FPS` seconds, step the
   simulation once, take one screenshot.
4. **Encode** the screenshots at the capture rate. For slow motion, capture at 120 or 240 fps and play at
   0.5× or 0.25× in the edit: one sim step per captured frame at every speed.
5. **Scan** the clip with `scripts/repeated-frames.sh`.

A take is a small script (`takes/<name>.mjs`) that stages a moment with the debug hooks and names its
length in game time. A shot list script runs them all, so a reshoot after a fix is one command.

## Traps
| # | Symptom | Cause | Fix |
|---|---|---|---|
| 1 | The trailer looks about 360p | a screencast delivers frames in CSS pixels, not device pixels; and the renderer capped its pixel ratio | one screenshot per frame at device scale 3; lift the renderer's cap for capture only |
| 2 | Takes are accidental slow motion, and differ per run | real-time capture lags under load | fake clock, paused, one step per frame |
| 3 | A "15 s" take holds about 4 s of game | the take looped on the wall clock | count game time in every take |
| 4 | UI animations stutter or race | CSS animations and native smooth scrolling run on real time under a paused clock | step CSS animations one frame per capture; scroll by setting `scrollTop` per frame |
| 5 | Slow motion stutters: the same state for several frames | the game slowed time but still stepped the sim at the normal rate | step the sim in finer slices during slow motion, in the game itself (9 of 24 slowed frames were new before, 23 of 24 after) |
| 6 | Contrast shifts after upload | JPEG frames are full-range BT.601 and were encoded untagged | convert to video-range BT.709 and tag the stream |
| 7 | The camera fights the take | the game's adaptive framing rewrites the zoom every frame | boot with a flag that pins the classic framing |
| 8 | A purchase in a take resets the walls | the real buy path does more than the visual | pin the staged values per frame, after the call |
| 9 | Toasts and level-up popups cover the shot | a fresh profile ranks up on any fight | stage a profile with headroom; hide what the shot isn't about |
| 10 | The last cut is early by a few frames | beat lengths are not whole frames | snap segment durations to frames (see the SKILL) |
| 11 | 16:9 has near-still frames | quarter-speed shots and UI panels shot at too low a rate | capture those at 240 fps; re-run `scripts/repeated-frames.sh` on the 16:9 file too |

## Staging rules
- Use the game's own spawn, buy and skill functions, then place and pin. The flash, the sound event and the
  purchase are then the real ones.
- Pin health (boss, wall) so a beat lands where the edit needs it.
- Hide the HUD in beauty shots, except the element the shot is about.
- For a reveal, force the roll and say so in the notes.
- Shoot 16:9 gameplay natively wide. UI is portrait by design: lay it out as framed phone panels that arrive
  on the beat.
- Write a NOTES file beside the output: what was staged, what was real, known weak spots.

## Cost
A 30 s trailer at 60 fps is 1,800 screenshots per aspect, more with slow-motion shots. Run takes as parallel
shooters on separate ports, and don't measure fps on the same machine meanwhile.
