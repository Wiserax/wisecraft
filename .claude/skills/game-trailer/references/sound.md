# Sound: music, the game's SFX, ducking, loudness

The agent can't hear and must never play anything aloud. Every decision here is a number from a meter, and
the hand-off says that nobody has listened.

## Music
- **Licensed, and the licence written down.** The game's own soundtrack is best; otherwise a track whose
  licence covers advertising on the platforms the trailer will run on. Record title, artist, licence and
  where it is kept in the NOTES, and credit the track where the licence asks for it. Buying a track or a
  licence is a spend: ask first.
- **Tempo first.** `wise video beats music.mp3` prints `bpm`, `first_beat` and `duration`. The tempo sets
  the shot lengths; 100 to 130 BPM suits most action trailers. The reading is an estimate from onsets: check
  it against a count of the contact sheet's beat marks or the track's published tempo when a cut feels off.
- **Structure.** The trailer's arc follows the track's: the hook on a hit, the escalation over a build, the
  finale on the drop, the end card over the tail. Use `music.start` to begin at a strong bar.

## The game's own SFX
Frame-stepped takes are silent: the page is captured as screenshots. The game's sounds come back through
the EDL's `sfx` list, placed on the final timeline.
- **Take the files from the game's assets** (they are licensed for the game; check they may be used in
  marketing). Roars, slams, coin bursts, kill crunches, the reveal shimmer, the celebration sting.
- **Place them on impacts:** `{"path": "sfx/slam.wav", "at": 18.4, "volume": 0.9}`, where `at` is the frame
  of the impact in the final cut (read it from the contact sheet of the compiled video).
- **Lead with sound** where it helps: a roar that starts 0.3 s before its shot pulls the eye to the cut.
- A music bed alone doesn't sell an impact. One earlier cut carried only music and sat at -17.8 LUFS; the
  SFX layer is what made the slams land.

## Ducking: music down 3-10 dB under impacts
Compile mixes music and SFX without ducking. Duck in two passes:

1. **Compile without music.** A copy of the snapped EDL with the `music` key removed renders the picture
   with the SFX only: `out.sfx.mp4`.
2. **Duck the music against the SFX and mix** (picture copied, not re-encoded). `D` is the video's duration
   and `-ss` the music start:
   ```bash
   D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 out.sfx.mp4)
   ffmpeg -i out.sfx.mp4 -ss 0 -i music/track.mp3 -filter_complex \
     "[0:a]asplit=2[key][fx];[1:a]atrim=0:${D},asetpts=PTS-STARTPTS,volume=0.8[mus];\
   [mus][key]sidechaincompress=threshold=0.05:ratio=2:attack=5:release=300[duck];\
   [duck][fx]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]" \
     -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -movflags +faststart out.mix.mp4
   ```
   On a test with a noise slam as the key and a steady tone as the music, ratio 2 dipped the music 7-9 dB
   on the slams and 0 dB between them; ratio 3 dipped 8-11 dB. Start at 2 and measure.
3. **Measure the dip, don't guess it.** Render the ducked music alone (the same graph ending at `[duck]`,
   mapped to `duck.wav`), then read momentary loudness of the music before and after ducking:
   ```bash
   ffmpeg -i duck.wav -af "ebur128=metadata=1,ametadata=print:key=lavfi.r128.M:file=duck-M.txt" -f null -
   ```
   Compare the values at the impact times with the unducked music read the same way. Aim for 3-10 dB at
   impacts and 0 dB between them; raise `threshold` if the music dips between impacts, raise `ratio` for a
   deeper dip.

## Loudness: level the finished file
```bash
wise music-enhance out.mix.mp4 --for trailer --fade-out 1.5   # -> out.mix.enhanced.mp4
wise music-enhance out.mix.enhanced.mp4 --check               # exit 1 off target
```
- `--for trailer` targets -14 LUFS integrated with a -1 dBTP true-peak ceiling. It applies one clean gain
  change when the peaks allow it, and ffmpeg's loudnorm limiter otherwise. The picture is copied bit for bit.
- `--fade-out 1.5` fades the sound over the last 1.5 s while the picture holds on the end card (compile ran
  with `"fade_out": 0`). Tested: a 30.8 s trailer faded from 29.33 s, levelled to -14.0 LUFS, picture copied.
- `wise video check out.mix.enhanced.mp4` reports the same loudness and true peak alongside the picture
  facts.

## Targets
| Where | Integrated loudness | True peak | Note |
|---|---|---|---|
| Social video (TikTok, Reels, Shorts, YouTube) | -14 LUFS | ≤ -1 dBTP | YouTube normalises playback to about -14; louder only gets turned down |
| Store pages and app previews | -14 to -16 LUFS | ≤ -1 dBTP | no single published target; check the store's current guide |
| Broadcast (EBU R128) | -23 LUFS | ≤ -1 dBTP | US broadcast (ATSC A/85) is -24 LKFS |

`wise music-enhance --target -23 out.mp4` sets any other target. Re-check platform targets before a paid
campaign; they change.

## In the hand-off
- Integrated loudness, true peak and loudness range of the delivered file, from the meter.
- The dip at the main impacts, measured.
- The music credit.
- "Nobody has heard this mix; levels are measured, not listened to."
