# Review scorecard

Score each line out of 10 from the contact sheets, `wise video check` and the loudness numbers, never from
memory of the plan. Below 7 on **clarity of the loop** or on the **finale**: recut before showing anyone.
Give the producer the scores with the file.

| # | Line | A 9 looks like | Measured by | Usual fix when low |
|---|---|---|---|---|
| 1 | Hook | the most spectacular moment in the first 3 s, with one line that works muted | the sheet's first 3 s | open on the boss, not on a logo or a menu |
| 2 | Clarity of the loop | by about 8 s a viewer knows what the player does: tap, stronger, the horde melts | the sheet up to 8 s | show the finger and the upgrade; cut one spectacle shot to make room |
| 3 | One idea per shot | each shot can be named in three words | the shot list against the sheet | split a shot that shows two features; drop the weaker |
| 4 | Escalation and arc | each shot bigger than the last, ending on the biggest | the sheet, in order | reorder: horde, giants, reveal, towers, crowd answer, skill, titan |
| 5 | Pacing and rhythm | every cut within half a frame of the beat; shot lengths vary | `snap_edl.py` worst error; cut count from `wise video check` | snap the EDL; mix 1, 2, 4 and 8-beat shots |
| 6 | Effect polish | explosions and lightning hold up in a still frame | the close shots on the sheet | fix the effect in the game (the **game-feel-audio** skill), then reshoot |
| 7 | Motion smoothness | no near-duplicate frames outside the end-card hold | `wise video check` near-duplicates | take fps = output fps ÷ speed; in-game slow motion off for takes |
| 8 | Sound design and sync | the game's SFX on the impacts, music ducked 3-10 dB there, -14 LUFS, ≤ -1 dBTP | `wise music-enhance --check`, the ducking measurement | add the game's SFX; duck the music; re-level |
| 9 | Platform fit | the right aspect per destination; words inside the safe area for at least 0.6 s | the sheet against the safe zones | `hook` instead of `title` on vertical; shorten to one line |
| 10 | Brand and call to action | logo + PLAY FREE held to the last frame while the sound fades | the last second of the sheet | `"fade_out": 0` in the EDL; fade the sound with `--fade-out` |

## Weak spots that came back from real reviews
- A creature shot small and from above reads as nothing. Reshoot close, facing the camera, filling about 45%
  of the frame height.
- The hero's hit landed outside the vertical frame. Pull the camera back over the wind-up so the impact is in
  frame on the beat.
- In 16:9 the titan was seen from behind. Re-angle to its front; keep the timings.
- Titles sat on the edge of the phone panel in 16:9. Put each title inside the close-up it describes, and
  title only the first shot of a group.
- The finale's fireworks were small in frame. A hero finale needs a close shot.
- "Not smooth at all": the game's own slow motion repeated states. Fixed in the game by stepping finer while
  slowed (9 of 24 new frames, then 23 of 24), and by turning it off for takes.
- A white flash on every impact hid the frames it was meant to sell. Removed.
- The picture faded to black with the music. The end card now holds; only the sound fades.

## What to tell the producer
- The file paths (vertical, 16:9, cutdowns), length and frame rate of each.
- The scorecard, line by line, and what would raise the lowest line.
- Measured: near-duplicate frames, integrated loudness and true peak, the worst cut-to-beat error, the dip
  of the music under the main impacts.
- What was staged (pinned health, forced rolls) and the music credit.
- "Nobody has watched it in motion or heard it; checked from frames, sheets and numbers."
- That it has not been posted anywhere, and where the files are.
