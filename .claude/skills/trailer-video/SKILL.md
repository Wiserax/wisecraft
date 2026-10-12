---
name: trailer-video
description: Shoot and cut a 25-32 second trailer of a web game from scripted captures of the real build. Covers the structure (hook in 3 s, the loop by 8 s, one idea per shot, a hero finale and end card), deterministic capture with one simulation step per captured frame (60 fps normal, 120-240 fps for slow motion), camera and staging, a beat-locked EDL for `wise video compile`, captions inside the vertical safe box, a 16:9 reframe, the game's own SFX levelled to -14 LUFS with `wise music-enhance`, a duplicate-frame stutter check and a ten-point review scorecard. Use when the user says "make a trailer", "cut a clip for TikTok", "showcase video", "the animation is not smooth", "reshoot the boss", "make a 16:9 version", or wants a video of a feature.
---

# Trailer video

A game isn't finished until you can show it in 30 seconds. The toolchain is scripted takes against the real
build (capture), `wise video contact` (look), `wise video compile` (edit), `wise scan` and `wise music-enhance`
(check and level). All of it runs muted: the agent can't watch motion or hear sound, so it checks frames and numbers
and says so.

## 1. Structure (25–32 s vertical)
1. **Hook, 0–3 s:** the most spectacular in-game moment (a giant boss's glare and stomp) plus one caption
   that works without sound ("8,000 ENEMIES. ONE FORT.").
2. **The loop by about 8 s:** a finger taps an upgrade → guns fire faster → the horde melts. Show what the
   player *does*.
3. **Escalation,** one idea per shot: horde → giants or mini-bosses → gacha reveal → new towers → crowd
   answer (pierce) → skill (blade) → titan slam.
4. **Hero finale:** the big boss's death up close (collapse + slow motion) → the chapter-clear celebration →
   logo + PLAY FREE end card, held while the music fades. Never end on a cluttered wide shot.

## 2. Capture
- **Scripted takes against the real build** (`takes/*.mjs`) with debug hooks to stage moments; parallel
  shooters on separate ports. Shoot on a frozen build in its own worktree, so a merge can't change a shot
  between takes.
- **Smooth motion:** one simulation step per captured frame; 60 fps for normal speed, 120–240 fps for half
  or quarter-speed slow motion. Real-time capture lags under load and gives accidental slow motion. The
  game must also show a new state on every slowed frame: a cut the producer called "not smooth at all"
  repeated states during in-game slow motion.
- **Check with a duplicate-frame scan:** `bash scripts/repeated-frames.sh <video>`. Only the logo hold may repeat.
- **Lower camera angles and fewer enemies in close shots;** eased push-ins and dollies instead of static
  frames. A 6,000-enemy wide shot reads as one mass.
- **Staged, not played, and say so.** Health pinned, moves forced onto the beat through the game's own
  clocks, rolls forced for a reveal. Change no game code for a take.

`references/capture.md` has the deterministic capture method and its traps (fake clock, CSS animations,
resolution, colour range).

## 3. Look before you cut
```bash
wise video probe take.mp4
wise video first-frame take.mp4                              # where gameplay starts
wise video contact take.mp4 sheet.png --every 1.5 --cols 6   # a timestamped grid; read it, pick in/out points
wise video beats music.mp3                                   # tempo and first beat
```
Pick the peak frames: the glare, the slam, the reveal. Write in/out times into the EDL.

## 4. Edit with an EDL
`wise video compile edl.json out.mp4`. The full format is in `wise video --help`.
```json
{
  "size": [1080, 1920], "fps": 60, "bpm": 91.44,
  "music": {"path": "music.mp3", "volume": 0.6},
  "segments": [
    {"clip": "takes/boss-hero.mp4", "in": 2.0, "beats": 4, "hook": "8,000 ENEMIES. ONE FORT."},
    {"clip": "takes/upgrade.mp4", "in": 0.6, "beats": 3, "title": "TAP. UPGRADE."},
    {"clip": "takes/titan.mp4", "in": 5.9, "beats": 4, "speed": 0.25, "title": "A TITAN APPROACHES"},
    {"card": {"title": "PLAY FREE", "sub": "in your browser"}, "beats": 4}
  ]
}
```
- **A beat-locked EDL** (`edl.json`: clip, in, beats, speed, title) on the music's BPM grid; cuts within
  about 16 ms of the beat. Vary shot lengths (not every shot 2 beats).
- **Hard cuts drift.** Segments render to whole frames. At 91.44 BPM a beat is 19.69 frames at 30 fps, so
  each cut gained or lost a fraction and the last one landed 81 ms early. Snap every duration to whole
  frames against the running total, and compile the snapped copy.
- **Captions in the safe box.** Titles inside vertical safe zones (clear of TikTok and Reels UI), on screen
  at least 0.6 s. One line that names what is on screen.
- **A 16:9 version by reframing** (battle shots recomposed; UI shots as a phone panel + close-up), not by
  cropping. Check each title still sits inside the picture it describes.
- **No white flash on impacts.** It hid the frames it was meant to sell.
- **The picture doesn't fade with the music.** The end card holds on the logo to the last frame.

## 5. Sound
- The game's own SFX mixed under the music (roars, slams, coins, kill crunches, celebration sting), ducking
  the music 3–10 dB on impacts. Integrated -14 LUFS for social, true peak ≤ -1 dBTP:
  `wise music-enhance out.mp4 --for trailer` sets it and copies the picture untouched.
- Earlier cuts carried a music bed only (-17.8 LUFS). The SFX layer is what sells impacts.
- The agent can't listen. Say so, and give the human the file plus a waveform chart. Never play it aloud.

## 6. Check the finished file
```bash
wise scan out.mp4                             # duration, fps, cuts and shot length, loudness, first real frame
bash scripts/repeated-frames.sh out.mp4        # near-duplicates: only the end-card hold
wise music-enhance out.mp4 --for trailer       # -> out.enhanced.mp4 at -14 LUFS, true peak <= -1 dBTP
wise music-enhance out.enhanced.mp4 --check    # the gate: exit 1 when it is off the target
wise video contact out.mp4 final-sheet.png --every 1
```
Read the final sheet: three frames around each cut, no near-black or single-frame flash, titles inside the
box. Then score it.

## 7. Review scorecard (score each out of 10)
Hook · clarity of the loop · one idea per shot · escalation and arc · pacing and rhythm · VFX polish ·
motion smoothness · sound design and sync · platform fit · brand and call to action. Below 7 on clarity or
finale: recut before sharing.

`references/scorecard.md` says what each line means and what to fix when it scores low.

## Rules
- **Never publish the video.** Open it locally for the producer; posting is their call.
- **Never play audio aloud.** Measure.
- **Only the game's own footage and licensed music.** Credit the track.
- **If the effects look cheap in the trailer, fix the game, not the edit.** The VFX upgrade done for a
  trailer shipped to players first (the **game-feel-audio** skill).

## References
- `references/capture.md`: deterministic capture step by step, with the traps. Read it before writing a take.
- `references/scorecard.md`: the ten lines of the scorecard and the usual fixes. Read it before sharing a cut.
- `scripts/repeated-frames.sh`: counts near-duplicate frames with ffmpeg (the stutter check for slow motion).
