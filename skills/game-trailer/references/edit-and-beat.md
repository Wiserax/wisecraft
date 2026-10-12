# Edit and beat

The edit is a JSON file, `edl.json`, that `wise video compile` renders into the finished video. Writing the
edit as data makes a recut a one-line change and a reshoot a re-render. `wise video --help` lists every key;
this page covers the ones a trailer needs, and how compile actually behaves.

## The keys that matter
Top level:

| Key | Use | Note |
|---|---|---|
| `size` | `[1080, 1920]` vertical, `[1920, 1080]` 16:9, `[1080, 1080]` square | text scales with the short side |
| `fps` | 30 or 60 | match the takes' output rate |
| `bpm` | the music's tempo | lets segments use `beats` |
| `transition` | `{"type": "cut"}` | **the default is a 0.3 s fade on every join**; any ffmpeg xfade name works |
| `fade_out` | `0` | the default 0.8 fades picture *and* sound together; 0 holds the end card |
| `clip_volume` | `0` | frame-stepped takes are silent; 0 keeps compile from mixing in anything else |
| `music` | `{"path", "volume", "start", "fade_in"}` | `start` skips into the track (align the first beat) |
| `sfx` | `[{"path", "at", "volume"}]` | one-shot sounds at times on the final timeline |
| `theme` | `{"accent", "text", "chip"}` | title and card colours |
| `watermark` | `{"path", "height", "corner", "opacity"}` | hidden on cards; `"watermark": false` on a segment hides it there |
| `beat_lock` | `true` with fades | lengthens each segment by its transition so fades don't pull cuts early |

Per segment: `clip`, `in` (seconds into the take), `beats` or `dur` (output seconds), `speed` (0.5 reads
half as much of the take), `fill` (`crop`, `pad` or `blur` for a take whose shape differs from the frame),
`zoom`, `crop` (`[x, y, w, h]` in take pixels, before scaling), `hook` (big centred line, `\n` for two),
`title` (+ `credit`), `transition` (the join *into* this segment), `volume`. A `card` segment
(`{"title", "sub", "logo", "bg"}`) is a full-frame title card with a slow push-in.

`assets/edl.vertical.template.json` is a complete 30 s vertical edit with these set. Compiled after
snapping, its 14 segments rendered exactly 157 119 78 40 39 158 157 158 78 158 78 237 157 236 frames
(1,850, 30.83 s at 60 fps) in about 21 s on a laptop.

## Beat math
One beat lasts `60 / BPM` seconds. In frames:

| BPM | Beat (s) | Frames at 30 fps | Frames at 60 fps |
|---|---|---|---|
| 90 | 0.6667 | 20.000 | 40.000 |
| 91.44 | 0.6562 | 19.685 | 39.370 |
| 100 | 0.6000 | 18.000 | 36.000 |
| 110 | 0.5455 | 16.364 | 32.727 |
| 120 | 0.5000 | 15.000 | 30.000 |
| 128 | 0.4688 | 14.062 | 28.125 |
| 140 | 0.4286 | 12.857 | 25.714 |
| 150 | 0.4000 | 12.000 | 24.000 |

Only some tempos give whole frames. `wise video beats music.mp3` prints the tempo and the first beat; set
`music.start` to the first beat (or to a later downbeat, one bar in) so beat 1 of the music is frame 0 of the
trailer.

## Why cuts drift, and the fix
Compile renders each segment on its own and cuts it to whole frames: a segment of `d` seconds becomes about
`ceil(d × fps)` frames. When a beat is 19.685 frames, every 1-beat segment becomes 20 frames and every cut
lands a third of a frame later than the one before. Measured on a 30 fps test edit of eight 1-beat shots at
91.44 BPM: every segment rendered 20 frames, and the eighth cut landed 84 ms late. An earlier trailer's last
cut was 81 ms off the same way. That is enough to see a slam land off the drum.

**The fix: snap the running total, not each segment.** For cut k, the ideal time is the sum of the beat
lengths so far; round that to the nearest frame, and give the segment whatever frames reach it. Segments
then alternate between 19 and 20 frames and no error accumulates.

```bash
python3 scripts/snap_edl.py edl.json            # writes edl.snapped.json, prints the table
wise video compile edl.snapped.json out.mp4
```

Its output on the vertical template (60 fps, 91.44 BPM), raw = what compile would do without snapping:
```
  cut  ideal s frames   raw ms snapped ms
    1    2.625    157     +8.7       -8.0
    2    4.593    119    +23.5       +6.8
    3    5.906     78    +27.8       -5.5
    ...
   12   24.278    237   +105.1       +5.1
   13   26.903    157   +113.8       -2.9
   14   30.840    236   +126.8       -6.6
  worst snapped error 8.1 ms (half a frame is 8.3 ms)
```
And on the 30 fps test edit, where the compiled segments were then counted with ffprobe:

| Cut | Ideal (s) | Raw frames | Raw error | Snapped frames | Snapped error |
|---|---|---|---|---|---|
| 1 | 0.656 | 20 | +10.5 ms | 20 | +10.5 ms |
| 2 | 1.312 | 20 | +21.0 ms | 19 | -12.3 ms |
| 3 | 1.969 | 20 | +31.5 ms | 20 | -1.8 ms |
| 4 | 2.625 | 20 | +42.0 ms | 20 | +8.7 ms |
| 5 | 3.281 | 20 | +52.5 ms | 19 | -14.2 ms |
| 8 | 5.249 | 20 | +84.0 ms | 19 | -16.0 ms |

The script writes each `dur` as frames ÷ fps less 0.4 ms. Compile cuts at millisecond precision, and an
exact frames ÷ fps can round up past the frame boundary and gain a frame; the margin gives the intended count
(checked for 1 to 45 frames at 30 and 60 fps) and keeps the total length right, so the end card is not
trimmed.

- **Hard cuts are exact.** With fades, set `beat_lock: true` and keep every transition a whole number of
  frames (0.3 s is 9 frames at 30 fps, 18 at 60); the script warns otherwise.
- **Snap after every recut.** Changing one segment's beats moves every cut after it.

## Rhythm
- **Mix lengths:** 1-beat stabs for kills, 2 for actions, 4 for arrivals and reveals, 6 to 8 for the finale
  and the end card. A trailer of 2-beat shots is a metronome.
- **Accelerate into the peak:** 4, 2, 2, 1, 1, then the 8-beat finale. The ear expects it.
- **Cut on the impact, not before it.** The slam frame is the first frame of the next shot or the beat
  inside a shot; pick the in-point so the impact sits on a beat.
- **J-cuts and L-cuts with SFX.** `sfx.at` is on the final timeline, so a sound can lead its picture: the
  titan's roar starts 0.3 s before the titan shot (a J-cut), and the celebration sting rings on over the end
  card (an L-cut).
- **No white flash on impacts.** It hides the very frames it should sell. Shake and a held frame read better.

## Titles and safe zones
- **One line, a few words, naming what is on screen,** on screen at least 0.6 s, large enough to read on a
  phone held at arm's length.
- **`hook`** is centred, big, with a shadow. It starts fading in 0.15 s after the cut (a 0.3 s fade) and is
  gone 0.1 s before the next cut (`hook_in`, `hook_out` and `hook_size` move it). The centre of the frame is safe on every platform: use it for words in a vertical social cut.
- **`title`** is a chip at the bottom left, 64 px from the left and 70-154 px above the bottom edge of a
  1080-wide frame (it scales with the short side). It slides in 0.2 s after the cut and is gone 0.1 s
  before the next, with 0.25 s fades, so it is fully readable from 0.45 s to 0.35 s before the cut. A titled
  segment needs 0.9 s at the very least and 1.4 s to hold the title fully for 0.6 s (2 beats at up to about
  85 BPM, 3 beats up to about 128).
- **Vertical platform overlays (approximate; re-check each platform's current guide):** on 1080×1920 the
  top ~220 px (status bar, tabs), the bottom ~420 px (caption, sound, buttons) and the right ~140 px (like,
  comment, share) are covered. The `title` chip sits inside the bottom zone, so keep `title` for 16:9 and
  store cuts and use `hook` on vertical social cuts. The watermark's default corner (bottom right) is
  covered there too; leave it off (the end card carries the logo) or use `"corner": "tr"` below the top band.
- **16:9:** the classic title-safe area is the central 90% (96 px in from each side, 54 px from top and
  bottom at 1920×1080). The `title` chip starts 64 px from the left: fine for web and store pages, a little
  wide of strict broadcast title-safe.

## The 16:9 version: reframe, don't crop
A 16:9 cut is a second edit, not a crop of the vertical one. Cropping a 9:16 frame to 16:9 keeps a third of
its height and loses the subject.

```json
{
  "size": [1920, 1080], "fps": 60, "bpm": 91.44,
  "transition": {"type": "cut"}, "fade_out": 0, "clip_volume": 0,
  "music": {"path": "music/track.mp3", "volume": 0.8, "start": 0.0},
  "sfx": [{"path": "sfx/slam.wav", "at": 18.4, "volume": 0.9}],
  "segments": [
    {"clip": "takes-16x9/01-hook.mp4", "in": 0.5, "beats": 4, "speed": 0.5, "hook": "8,000 ENEMIES. ONE FORT."},
    {"clip": "takes/02-tap.mp4", "in": 0.2, "beats": 3, "fill": "blur", "title": "TAP. UPGRADE."},
    {"clip": "takes-16x9/03-payoff.mp4", "in": 0.0, "beats": 2},
    {"clip": "takes-16x9/10-titan-approach.mp4", "in": 0.2, "beats": 4, "speed": 0.25, "title": "A TITAN APPROACHES"},
    {"card": {"title": "PLAY FREE", "sub": "in your browser", "logo": "art/logo.png"}, "beats": 6}
  ]
}
```
- **Battle shots:** recaptured natively wide (640×360 CSS at scale 3), with the same staging and timings.
- **UI shots:** the vertical take with `"fill": "blur"`: the phone-shaped picture sits centred over a
  blurred, darkened cover of itself, which reads as a phone panel. Or `pad` for plain black sides.
- **Titles:** `title` chips work here. Put each inside the picture it describes, and title only the first
  shot of a group.
- Snap it and check it like the vertical: `snap_edl.py`, compile, `wise video check`.

## Before compiling the final
1. `python3 scripts/snap_edl.py edl.json` and read the worst error.
2. `wise video compile edl.snapped.json out.mp4 --preview` for a fast half-size look (it also drops to
   30 fps, so cut timing in the preview is approximate).
3. `wise video contact out.mp4 sheet.png --every 0.5`: read every cut.
4. The full compile, then the sound (`references/sound.md`) and the checks in the SKILL.
