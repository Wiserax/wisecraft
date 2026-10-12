# Load time and a boot that cannot hang

## Measure
Phone profile: 390×844, Chrome, Fast 4G (about 9 Mbit/s, 165 ms), CPU 4× slower, median of 5. Cold and warm.
Record: bytes, time to splash, hub, first siege, first sound after the first tap.

## Staged audio
Loading every sound before any can play made the first sound arrive 7.6 s after the first tap.
- Load in the order needed: a small first tier for the scene (a first fight: taps, shots, kills; the hub:
  taps, tabs, windows) with that scene's music beside it, then the rest eight at a time, the other music
  track last.
- "Ready" is set after the first tier. A sound whose file is still on its way is silent; it gets no
  stand-in.
- Prefetch at idle once the game is on screen, before the first touch. Skip it for data-saver visitors.
- Keep downloads to four connections on HTTP/1.1 (eight on HTTP/2 and 3) and time-limit every request.

| | Before | After |
|---|---|---|
| First sound after the first tap, new player | 7.6 s | 1.5 s |
| First sound on the hub | 7.8 s | 0.6 s |
| Music | 7.6 s | 2.4–3.1 s |
| First sound on a return visit | 3.7 s | 0.2 s |

## Cache headers and the deploy
- Hashed files under `/assets/`: cached for a year, immutable.
- Sounds, art, fonts: one day.
- HTML: still revalidated.
- **No orphan assets in the deploy.** Two unused 1.4 MB music stems and the sound-design manifests were
  shipping; removing them took the deploy from 12.6 MB to 9.7 MB. Pin the list of shipped files with a
  test.

Costs to know: about half of a 3.9 s first load was the phone running the code, which caching can't touch.
Loading code beside the splash art delayed the sharp art (0.72 s → 1.25 s) until the art was requested first
and alone for up to 100 ms.

## Boot must never hang
- **Found:** on a server that drops connections under a burst, a reset on a preloaded code chunk left the
  splash on its error line for good: 5 of 20 boots.
- **Rule:** a failed game file is retried under a fresh URL, then by one automatic reload per tab, then a
  Retry screen. A hung request reloads once after 15 s. Fonts are optional and time-boxed.
- **Prove it:**
  - a fault matrix, one fault at a time (each file failing, hanging or resetting): 0 endless splashes, in
    Chromium and WebKit (57 single faults here: 47 end in a live game, up from 20; endless splashes 5 → 0);
  - 60 Chromium cold boots on Fast 4G + CPU 4× and 20 WebKit boots on a paced server: 0 failures.

## Traps
- A local `python -m http.server` drops connections under parallel load (`ERR_CONNECTION_RESET`). That's not
  a game bug, but the game must survive it; it is how the boot hang was found.
- Right after a deploy an asset may 404 for a few seconds; recheck after 20 s before panicking.
- A deploy once shipped without the `audio/` folder and sound never started. After every deploy, run the
  gate against the live URL and request one file from each asset folder.
