---
name: game-trailer
description: Cut a 15-60 second trailer from the real game, not from mockups. Covers the brief and shot list, a capture plan, deterministic frame-exact capture in a browser (one simulation step per captured frame, 120-240 fps takes for smooth slow motion), contact sheets to pick moments, a beat-locked EDL compiled with `wise video compile` and snapped to whole frames, titles inside platform safe zones, the game's own SFX over licensed music with ducking, loudness set to -14 LUFS / -1 dBTP with `wise music-enhance`, vertical 9:16 and 16:9 (and square) exports, a stutter and loudness check with `wise video check`, and a ten-line review scorecard. Use when the user says "make a trailer", "cut a clip for TikTok", "Reels", "Shorts", "store video", "app preview", "showcase video", "a video of the new boss", "the slow motion stutters", "the animation is not smooth", "reshoot the boss", "make a 16:9 version", "add music", "the trailer is too quiet", or wants any video of a feature.
---

# Game trailer

A game is not finished until it can be shown in 30 seconds. This skill makes that video from the real build:
scripted takes captured frame by frame, cut on the beat from an edit list, mixed to a measured loudness and
exported in every shape the producer needs. The agent can't watch motion or hear sound. It checks frames,
sheets and numbers, and says so in every hand-off.

The toolchain:

| Step | Tool |
|---|---|
| Capture | a take script per shot (Playwright, fake clock), encoded with ffmpeg |
| Look | `wise video contact`, `wise video probe`, `wise video first-frame` |
| Tempo | `wise video beats music.mp3` |
| Edit | `edl.json` → `scripts/snap_edl.py` → `wise video compile` |
| Level | `wise music-enhance out.mp4 --for trailer` |
| Check | `wise video check out.mp4 --sheet`, the scorecard |

The lessons here come from several trailers of a horde tower defense for phones (Vite + three.js, 8,000
enemies on screen). The numbers are a starting point for another game, not constants.

## 1. Brief and shot list
Write down, before any capture:
- **Where it runs and how long.** A 30 s vertical for social is the default. Add a 16:9 for YouTube, a
  store page or press, and a 15 s cutdown if asked. `references/exports.md` has the specs.
- **The one sentence it sells.** "8,000 enemies, one fort, your taps." Every shot serves it.
- **The structure (25-32 s vertical):**
  1. **Hook, 0-3 s:** the most spectacular in-game moment plus one line that works with the sound off.
     Never open on a logo or a menu.
  2. **The loop by about 8 s:** what the player *does*. A finger taps an upgrade, the guns fire faster, the
     horde melts.
  3. **Escalation, one idea per shot:** each shot bigger than the last (horde, giants, a reveal, new towers,
     a crowd answer, a skill, the titan).
  4. **Hero finale:** the biggest moment up close (a boss's death in slow motion), the celebration, then the
     end card (logo + PLAY FREE) held to the last frame while the music fades.
- **The shot list** from `assets/shot-list.template.md`: per shot the moment, the camera, the speed, the
  beats, the caption. One idea per shot; each shot nameable in three words.

## 2. Capture plan
For every shot, decide the capture rate from the slowest speed it plays at in the edit:

**take fps = output fps ÷ slowest speed**

| Output | Normal | Half speed | Quarter speed |
|---|---|---|---|
| 30 fps | 30 | 60 | 120 |
| 60 fps | 60 | 120 | 240 |

Then the staging (debug hooks: spawn, pin health, force a roll), the camera move (an eased push-in beats a
static frame), and the aspect. Shoot 16:9 gameplay natively wide; never crop a vertical into a 16:9.
`references/capture-plan.md` has the worked 30 s plan, the easing curves and the staging rules.

## 3. Capture: one simulation step per captured frame
- **Never record in real time.** Real-time capture lags under load and gives accidental, uneven slow motion,
  and a screencast delivers CSS pixels (a "1080p" trailer that looks 360p).
- **The method:** a fake clock, installed and *paused*. Per frame: stage, advance the clock by 1/fps, step
  the simulation once, render, take one screenshot at device scale 3 (360×640 CSS = 1080×1920). Encode the
  frames at the take rate, converted to video-range BT.709 and tagged.
- **Turn the game's own slow motion and hit-stops off for takes.** Slow motion comes from the capture rate;
  the edit decides where it starts and ends. In-game slow motion that still steps the simulation at the
  normal rate repeats states: one death beat showed a new state on 9 of 24 slowed frames, and 23 of 24 once
  the game stepped in finer slices.
- **Shoot a frozen build** in its own checkout, so a merge can't change a shot between takes.
- **Staged, not played, and say so.** Health pinned, rolls forced, moves placed on the beat. Use the game's
  own spawn, buy and skill functions, so flashes and sound events are the real ones. Change no game code for
  a take.

`references/capture.md` has the take skeleton, the encode command and the traps table.

## 4. Look before you cut
```bash
wise video probe takes/boss.mp4
wise video first-frame takes/boss.mp4                          # where the picture starts
wise video contact takes/boss.mp4 sheets/boss.png --every 0.5  # a timestamped grid; read it, pick in/out
wise video beats music/track.mp3                               # tempo and first beat
```
Pick the peak frames from the sheet: the glare, the slam, the reveal. Write the in-points into the EDL.

## 5. Edit: a beat-locked EDL
`wise video compile edl.json out.mp4` renders the whole edit from JSON. `assets/edl.vertical.template.json`
is a ready starting point; `wise video --help` has every key.
- **Set `"transition": {"type": "cut"}` at the top.** Without it every join is a 0.3 s cross-fade.
- **Lengths in beats** (`"bpm"` + `"beats"` per segment). Mix 1, 2 and 4-beat shots; not every shot 2 beats.
- **Snap to whole frames before compiling.** Compile renders each segment to whole frames, and a beat is
  rarely whole (91.44 BPM at 30 fps is 19.685 frames). Measured: eight 1-beat cuts each rendered 20 frames
  and the last landed 84 ms late. `python3 scripts/snap_edl.py edl.json` writes `edl.snapped.json` with every
  cut on the nearest frame (worst 16 ms at 30 fps); compile that copy.
- **`"fade_out": 0`.** Compile's default fades picture and sound together over the last 0.8 s. The picture
  must hold on the end card; fade the sound alone in step 7.
- **No white flash on impacts.** It hides the frames it is meant to sell.

`references/edit-and-beat.md` has the beat math, a full EDL, the 16:9 reframe and the J-cut.

## 6. Titles
- One line, naming what is on screen ("A TITAN APPROACHES"), on screen at least 0.6 s, readable on a phone.
- **Where compile puts them:** `"hook"` is a big centred line (safe on every platform); `"title"` is a chip
  bottom-left, 70-154 px above the bottom edge of a 1080-wide frame. In a vertical social cut that chip sits
  under the platform's caption and button overlay. Use `hook` for vertical social cuts, `title` for 16:9 and
  store cuts.
- A `title` slides in 0.2 s after the cut and leaves 0.1 s before the next, with 0.25 s fades: a titled shot
  needs 1.4 s to hold the words fully for 0.6 s (3 beats at up to about 128 BPM).
- Platform overlays cover roughly the top 220 px, the bottom 420 px and the right 140 px of a 1080×1920
  frame. Keep every word and the key action out of them.

## 7. Sound: the game's own SFX over licensed music, measured
- **Licensed music only;** credit the track in the NOTES. Pick the tempo before the cut.
- **Frame-stepped takes have no audio.** The game's SFX go in through the EDL's `"sfx"` list (`path`, `at`,
  `volume`), placed on the impacts of the final timeline: roars, slams, coins, kill crunches, the
  celebration sting. A music bed alone (one cut sat at -17.8 LUFS with no SFX) doesn't sell an impact.
- **Duck the music 3-10 dB on impacts.** Compile mixes without ducking; `references/sound.md` has the tested
  sidechain recipe (7-9 dB dips on a slam, 0 dB between).
- **Level and fade the finished file:**
  ```bash
  wise music-enhance out.mp4 --for trailer --fade-out 1.5   # -> out.enhanced.mp4: -14 LUFS, true peak <= -1 dBTP
  wise music-enhance out.enhanced.mp4 --check               # the gate: exit 1 off target
  ```
  The picture is copied untouched; only the audio is rewritten.
- **Never play audio aloud.** No speakers, no unmuted browser. Hand the file to the human and say that
  nobody has heard it.

## 8. Exports
- **Vertical 1080×1920** for TikTok, Reels and Shorts: the master.
- **16:9 1920×1080** for YouTube, a store page or press: *reframed*, not cropped. Battle shots recaptured
  wide; UI shots as a phone panel beside a close-up. Check every title still sits inside the picture it
  describes.
- **Square 1080×1080** only on request.
- H.264 High, yuv420p, BT.709 tagged, AAC 48 kHz, `+faststart`. Compile leaves the colour untagged; tag the
  final file losslessly (`references/exports.md` has the one-line command).

## 9. Check the finished files
```bash
wise video check out.enhanced.mp4 --sheet final.png   # length, fps, cuts and shot length, loudness, first frame, near-duplicates
wise video contact out.enhanced.mp4 final-1s.png --every 1
```
- **Near-duplicate frames:** only the end-card hold may repeat. Repeats inside a slowed shot mean the take
  rate was too low or the game slowed its own time.
- **Cuts:** the count matches the EDL; the first real frame is at 0.
- **Loudness:** -14 LUFS ± 1, true peak ≤ -1 dBTP.
- **The sheet:** no near-black or single-frame flash, titles inside the safe area, the finale close.
- **Score it** with `references/scorecard.md`. Below 7 on the loop's clarity or on the finale: recut before
  showing anyone.

## 10. Deliver locally
- **Never publish or post the video.** Open it in the system viewer for the producer; posting is their call.
- Hand over: the file paths (vertical, 16:9, any cutdown), length, frame rate, loudness and true peak, the
  near-duplicate count, the worst cut-to-beat error, the scorecard, and a NOTES file beside the files: what
  was staged, what was real, the music and its licence, known weak spots.
- Say it plainly: "Nobody has watched it in motion or heard it; checked from frames, sheets and numbers."

## Rules
- **Only the game's own footage and licensed music.** No stock gameplay, no footage of other games, no real
  person's voice or likeness without consent.
- **If the effects look cheap in the trailer, fix the game, not the edit.** The effect upgrade made for one
  trailer shipped to players first (the **game-feel-audio** skill).
- **Spend nothing without a yes:** no paid music, paid generation or paid render services unless the
  producer says so.
- **Real numbers only** in the hand-off: every figure from a command that ran on the delivered file.

## References
- `references/capture-plan.md`: a worked 30 s shot plan, capture rates per shot, staging with debug hooks,
  camera easing, framing per aspect. Read it before writing any take.
- `references/capture.md`: the frame-exact capture method, a Playwright take skeleton, the encode command
  and the traps. Read it before running a take.
- `references/edit-and-beat.md`: the EDL, beat math, frame snapping, shot-length rhythm, titles and safe
  zones, the 16:9 reframe. Read it before compiling.
- `references/sound.md`: music choice and licence, SFX placement, sidechain ducking, loudness targets. Read
  it before the mix.
- `references/exports.md`: delivery specs per platform and the final encode. Read it before exporting.
- `references/scorecard.md`: the ten-line review and the usual fixes. Read it before showing a cut.
- `assets/shot-list.template.md`, `assets/edl.vertical.template.json`: ready to fill.
- `scripts/snap_edl.py`: snaps beat lengths to whole frames and prints the per-cut error (standard library).
