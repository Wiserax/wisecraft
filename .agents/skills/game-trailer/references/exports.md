# Exports and delivery specs

One master per aspect, each its own edit and its own check. Lengths and limits below are typical at the
time of writing; platforms change them. **Re-check each platform's current spec before a paid campaign or a
store submission.**

## Per destination
| Destination | Aspect | Size | Length (typical) | Note |
|---|---|---|---|---|
| TikTok, Instagram Reels, YouTube Shorts | 9:16 | 1080×1920 | 15 s and 30 s cuts; 21-34 s often recommended for ads | the master; words inside the safe area |
| YouTube, press kit, website | 16:9 | 1920×1080 | 30-60 s | reframed, not cropped |
| Google Play store listing | 16:9 | 1920×1080 | 30 s - 2 min | given as a YouTube link; landscape |
| Apple App Store app preview | device-specific (portrait or landscape) | per device class, e.g. 886×1920 portrait for recent large iPhones | 15-30 s | strict sizes and frame rate (30 fps max); screen capture of the app only; check Apple's current table |
| Feed posts, some ad placements | 1:1 | 1080×1080 | 15-30 s | only on request; a third edit |

## The encode
`wise video compile` writes H.264 (libx264, CRF 18, preset slow), yuv420p, AAC 192 kb/s, `+faststart`, at the
EDL's size and fps. `wise music-enhance` then rewrites only the audio (AAC 48 kHz). What is left is the colour
tag: compile's output reports `color_range`, `color_space`, `color_primaries` and `color_transfer` as
unknown, and an untagged file can shift contrast on some players and upload transcoders.

Tag the final file losslessly (the picture is not re-encoded):
```bash
ffmpeg -i out.mix.enhanced.mp4 -c copy \
  -bsf:v h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1:video_full_range_flag=0 \
  -movflags +faststart trailer-9x16.mp4
```
Then `ffprobe -show_streams trailer-9x16.mp4` should show `profile=High`, `pix_fmt=yuv420p`,
`color_range=tv`, `color_space=bt709`, `color_primaries=bt709`, `color_transfer=bt709`, and
`sample_rate=48000` for the audio. Tested on the vertical template's full chain.

| Property | Value |
|---|---|
| Video codec | H.264 High, yuv420p |
| Colour | BT.709, video (limited) range, tagged |
| Frame rate | 30 or 60, constant; the same as the takes' output rate |
| Audio | AAC, 48 kHz, stereo |
| Container | MP4 with `+faststart` (plays before it has fully downloaded) |
| Loudness | -14 LUFS integrated, ≤ -1 dBTP (social); see `sound.md` for others |

## Reframe, don't crop
- **9:16 to 16:9 by cropping keeps a third of the height** and cuts the subject in half. Make the 16:9 its own
  edit from wide takes (`edit-and-beat.md`).
- **UI shots in 16:9:** the portrait take with `"fill": "blur"` (a phone panel over a blurred cover) or a
  framed phone panel beside a close-up.
- **Square from vertical** is closer: `"fill": "crop"` keeps the middle 1080×1080 of a 1080×1920 take, so
  the subject must sit in the middle band. Check each shot on the contact sheet.

## Cutdowns
- **15 s:** the hook (3 s), the loop (4 s), the single biggest escalation shot, the finale (3 s) and a 2 s
  end card. Re-snap and re-check; a cutdown is a new edit, not a trim.
- **6 s bumper:** the hook and the end card only.

## File names and the hand-off folder
```
trailer/
  trailer-9x16.mp4        the vertical master
  trailer-16x9.mp4        the reframed 16:9
  trailer-9x16-15s.mp4    cutdowns, if asked
  final-sheet.png         contact sheet of the master
  NOTES.md                staged vs real, music licence, measurements, scorecard, weak spots
```
Open the files locally for the producer. Never upload, post or publish them.
