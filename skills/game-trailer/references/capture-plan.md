# Capture plan

Plan every shot before the first take: what moment, how it is staged, how the camera moves, at what speed
it plays and therefore at what rate it is captured. A plan on paper turns a reshoot into one command and keeps
the edit on the beat.

## The shot list template
`assets/shot-list.template.md` is ready to copy. One row per shot:

| Column | What to write |
|---|---|
| # | the order in the cut |
| Beats | its length on the music's grid (1, 2, 4 or 8) |
| Moment | three words: "titan slam, close" |
| Staging | the debug calls: spawn, pin, force |
| Camera | static, push-in, pull-back, dolly, orbit; from and to |
| Speed | 1, 0.5 or 0.25 in the edit |
| Take fps | output fps ÷ speed |
| Game time | output seconds × speed (what the take must contain), plus handles |
| Words | the hook or title, if any |
| Aspect | vertical, 16:9 or both (16:9 is a separate take, not a crop) |

## A worked 28.5 s plan
60 fps output, a 120 BPM track (one beat = 0.5 s, exactly 30 frames at 60 fps, so this plan needs no
snapping; most tracks are not this kind). Shot lengths mix 1, 2, 3, 4 and 8 beats.

| # | Starts (s) | Beats | Moment | Speed | Take fps | Game time (s) | Output frames |
|---|---|---|---|---|---|---|---|
| 1 | 0.0 | 4 | Hook: titan glare and stomp, low angle | 0.5 | 120 | 1.00 | 120 |
| 2 | 2.0 | 3 | Loop: a finger taps the Attack card | 1 | 60 | 1.50 | 90 |
| 3 | 3.5 | 2 | Guns fire faster, the front rank melts | 1 | 60 | 1.00 | 60 |
| 4 | 4.5 | 1 | Kill crunch, close | 1 | 60 | 0.50 | 30 |
| 5 | 5.0 | 1 | Kill crunch, wide | 1 | 60 | 0.50 | 30 |
| 6 | 5.5 | 2 | Wide surge, eased push-in | 1 | 60 | 1.00 | 60 |
| 7 | 6.5 | 4 | Giants walk in from the rim | 0.5 | 120 | 1.00 | 120 |
| 8 | 8.5 | 2 | Mini-boss enters | 1 | 60 | 1.00 | 60 |
| 9 | 9.5 | 4 | Reveal: the vault opens | 1 | 60 | 2.00 | 120 |
| 10 | 11.5 | 2 | The new tower fires | 1 | 60 | 1.00 | 60 |
| 11 | 12.5 | 4 | Pierce: one bolt through a line | 0.5 | 120 | 1.00 | 120 |
| 12 | 14.5 | 2 | Skill: blade frenzy | 1 | 60 | 1.00 | 60 |
| 13 | 15.5 | 4 | Titan approaches, camera pulls back | 0.25 | 240 | 0.50 | 120 |
| 14 | 17.5 | 2 | Titan slam, walls shake | 1 | 60 | 1.00 | 60 |
| 15 | 18.5 | 8 | Finale: the titan collapses, close | 0.25 | 240 | 1.00 | 240 |
| 16 | 22.5 | 4 | Chapter clear, close | 1 | 60 | 2.00 | 120 |
| 17 | 24.5 | 8 | End card, held to the last frame | - | - | - | 240 |

Read it as a story: the hook lands at 0 s, the player's action is on screen by 2-5 s (the loop by 8 s), every
shot from 6 to 15 is bigger than the one before, the finale is the longest shot, and the end card holds four
seconds while the music fades.

**Handles.** Capture about 0.5 s of game time before and after each moment, so the in-point can be chosen
from the contact sheet. At 240 fps that is 120 extra frames per side; budget the capture time for it.

## Capture rate per shot
| Edit speed | 30 fps output | 60 fps output | Use for |
|---|---|---|---|
| 1 (normal) | 30 | 60 | the loop, UI, anything the player must read |
| 0.5 | 60 | 120 | arrivals, reveals, a hook that needs weight |
| 0.25 | 120 | 240 | the finale, the slam, one hero moment per trailer |

A 240 fps quarter-speed shot holds a quarter as much action per second. Use it once or twice; a trailer of
slow motion reads as slow.

## Staging with debug hooks
- **Spawn, then place.** Call the game's own spawn with a bearing and distance, then set the position the
  shot needs. The entrance, the sound event and the HP bar stay real.
- **Pin what the beat needs.** Boss health that crosses 50% on beat 3, walls that hold at 62% so the shot
  doesn't end in a defeat screen. Pin after the game's own update, every frame.
- **Force rolls for reveals** (the legendary drop) and write it in the NOTES: a forced roll is staging, not
  a promise of odds.
- **Clear the frame.** Hide toasts, tutorial hints and the HUD except the element the shot is about. Use a
  staged save with rank headroom so nothing levels up mid-shot.
- **Count game time in the take**, never wall time.

## Camera moves
Drive the camera from game time with an easing curve; a static camera on a busy field reads as a screen
recording.

- Normalised progress: `p = clamp((t - t0) / duration, 0, 1)`.
- Ease in-out (starts and ends gently, for push-ins and dollies):
  `e = p < 0.5 ? 4p³ : 1 - (-2p + 2)³ / 2`.
- Ease out (a fast start that settles, for a pull-back on an arrival): `e = 1 - (1 - p)³`.
- **Push-in:** `zoom = from + (to - from) · e`, typically 1.0 → 0.82 of the frame over 2 s.
- **Dolly:** `position = a + (b - a) · e`, with the look-at target fixed on the subject.
- **Impact shake:** an offset `A · exp(-t / 0.12) · sin(2π · 18 · t)`, with A a few percent of the frame
  height, starting on the impact frame. Small, short, and never a white flash.
- Pull the camera back over a wind-up so the impact lands inside the vertical frame on the beat.

## Framing per aspect
- **Vertical 1080×1920 (360×640 CSS at scale 3):** the subject in the middle band, filling about 45% of the
  frame height in a close shot. The top ~220 px, the bottom ~420 px and the right ~140 px sit under
  platform overlays: keep faces, impacts and words out of them.
- **16:9 1920×1080 (640×360 CSS at scale 3):** captured natively wide, the subject on a third line, the
  field's width used for the horde. Re-angle where a vertical shot showed the subject from behind.
- **UI shots:** the UI is portrait. For 16:9, show it as a framed phone panel next to a close-up of what the
  tap does.

## What to write in NOTES
A `NOTES.md` beside the takes and the final files:
- the build and its commit;
- per shot: staged or played, what was pinned or forced;
- capture rate and speed per shot;
- the music: title, artist, licence, where the licence is kept;
- known weak spots ("the vault glow clips on the 16:9 panel");
- what nobody checked ("not watched in motion, not heard").
