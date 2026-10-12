# Frame-exact capture

The goal: every captured frame shows a new game state, at full resolution, the same on every run. A take is
a small script (`takes/<shot>.mjs`) that stages one moment and names its length in game time. A shot-list
script runs them all, so a reshoot after a fix is one command.

## The method
1. **Serve a frozen build** on its own port, from its own checkout. One browser context per take, muted, a
   fresh profile (or a staged save with headroom, so no rank-up toast covers the shot).
2. **Install a fake clock before the page loads, then pause it.** An installed clock still flows with real
   time until it is paused.
3. **Per frame:** run the take's staging code in the page, advance the clock by `1 / fps` seconds, step the
   simulation once, render once, take one screenshot.
4. **Encode** the frames at the take rate, converted to video-range BT.709 and tagged.
5. **Check** the take with `wise video check takes/<shot>.mp4`: near-duplicates must be 0.

## A take skeleton
Adapt the hook names to the game. The skeleton assumes the game exposes a debug hook such as
`window.__game` with a way to step and render; most games can add one behind a URL flag. Check the
`page.clock` calls against the installed Playwright version (the clock API arrived in 1.45).

```js
// takes/titan-slam.mjs   node takes/titan-slam.mjs <url> <outDir> [fps] [seconds]
import { chromium } from "playwright";
import fs from "node:fs/promises";

const [url, out = "takes/titan-slam", FPS = "240", SECONDS = "2.5"] = process.argv.slice(2);
const fps = Number(FPS), frames = Math.round(Number(SECONDS) * fps);
await fs.mkdir(out, { recursive: true });

const browser = await chromium.launch({ args: ["--mute-audio"] });       // never any sound
const ctx = await browser.newContext({ viewport: { width: 360, height: 640 }, deviceScaleFactor: 3 }); // 1080x1920
const page = await ctx.newPage();
await page.clock.install({ time: new Date("2026-01-01T00:00:00Z") });   // before the page loads
await page.goto(url + "?capture=1");      // the flag pins framing, lifts the DPR cap, and stops the game's own
                                          // frame loop, so only g.step() below moves the simulation
await page.waitForFunction(() => window.__game?.ready);
await page.clock.pauseAt(new Date("2026-01-01T00:01:00Z"));              // from here nothing moves unless told

// staging, once: use the game's own functions, then pin
await page.evaluate(() => {
  const g = window.__game;
  g.setSlowMotion?.(false);                 // in-game slow motion and hit-stops off: the capture rate makes it
  g.spawnBoss({ kind: "titan", bearing: 0.1 });
  g.hud.hide({ except: ["boss-bar"] });
});

for (let i = 0; i < frames; i++) {
  const t = i / fps;                                                    // game time, never wall time
  await page.evaluate(({ t, dt }) => {
    const g = window.__game;
    g.walls.pin(0.62);                      // pinned values, per frame, after the game's own update
    g.camera.pushIn({ t, from: 1.0, to: 0.82, over: 2.0 });            // an eased move, by game time
    g.step(dt);                             // exactly one simulation step
    g.render();                             // exactly one render
  }, { t, dt: 1 / fps });
  await page.clock.runFor(1000 / fps);      // timers and Date follow the same clock
  await page.screenshot({ path: `${out}/${String(i).padStart(5, "0")}.png` });
}
await browser.close();
```

If the game has no `step`/`render` hook, `page.clock.runFor(1000 / fps)` alone drives its
`requestAnimationFrame` loop. Then check that the game's fixed-step accumulator takes exactly one step per
captured frame at the take rate; if it takes several (or none), add the hook.

## Encode, BT.709, tagged
From PNG frames (RGB):
```bash
ffmpeg -framerate 240 -i takes/titan-slam/%05d.png \
  -vf "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p,setparams=range=tv:colorspace=bt709:color_primaries=bt709:color_trc=bt709" \
  -c:v libx264 -preset slow -crf 14 -movflags +faststart takes/titan-slam.mp4
```
From JPEG frames (full-range BT.601), change the scale to
`scale=in_color_matrix=bt601:in_range=full:out_color_matrix=bt709:out_range=tv`. `ffprobe` should then
report `color_range=tv`, `color_space=bt709`, `color_primaries=bt709`, `color_transfer=bt709`.

`-framerate` is the take rate. A 240 fps take played at quarter speed in a 60 fps edit is one sim step per
output frame.

## Traps
| # | Symptom | Cause | Fix |
|---|---|---|---|
| 1 | The trailer looks about 360p | a screencast delivers CSS pixels, and the renderer capped its pixel ratio | one screenshot per frame at device scale 3; lift the cap for capture only |
| 2 | Takes are accidental slow motion and differ per run | real-time capture lags under load | fake clock, paused, one step per frame |
| 3 | A "15 s" take holds about 4 s of game | the take looped on the wall clock | count game time in every take |
| 4 | UI animations stutter or race | CSS animations and native smooth scrolling run on real time under a paused clock | step CSS animations one frame per capture (Web Animations `currentTime`); scroll by setting `scrollTop` per frame |
| 5 | Slow motion stutters: the same state for several frames | the take was shot at the output rate, or the game slowed its own time without stepping finer | take fps = output fps ÷ speed; turn in-game slow motion off for takes |
| 6 | A shot is slowed twice | in-game slow motion on during a 240 fps take | in-game slow motion and hit-stops off |
| 7 | Contrast shifts after upload | frames encoded untagged, or full-range JPEG treated as video range | convert to video-range BT.709 and tag it (above) |
| 8 | The camera fights the take | the game's adaptive framing rewrites the zoom every frame | a capture flag that pins the framing |
| 9 | A purchase in a take resets the walls | the real buy path does more than the visual | pin the staged values per frame, after the call |
| 10 | Toasts and level-up popups cover the shot | a fresh profile ranks up on any fight | stage a profile with headroom; hide what the shot isn't about |
| 11 | Timing changed once capture became exact | real-time takes lagged, so effects had looked longer | re-time shots in true game time; a skill ring may be a 0.3 s burst |
| 12 | 16:9 has near-still frames | quarter-speed shots and UI panels shot at too low a rate | 240 fps for those; run `wise video check` on the 16:9 file too |
| 13 | Footage changes between takes | the game branch kept moving | shoot from a frozen build in its own checkout |

A near-still frame is not a duplicate. A quiet quarter-speed shot can flag a few near-duplicates that are in
fact different frames. When the count is not zero, open those timestamps with `wise video contact --start`
and `--end` and look before reshooting.

## Staging rules
- Use the game's own spawn, buy and skill functions, then place and pin. The flash, the sound event and the
  purchase are then the real ones.
- Pin health (boss, walls) so a beat lands where the edit needs it.
- Hide the HUD in beauty shots, except the element the shot is about.
- For a reveal, force the roll and say so in the NOTES.
- Fewer enemies and lower camera angles in close shots; a 6,000-enemy wide shot reads as one mass.
- UI is portrait by design: for 16:9, lay it out as a framed phone panel that arrives on the beat.

## Cost
A 30 s trailer at 60 fps is 1,800 screenshots per aspect, and a 240 fps quarter-speed second is 240 for one
second of output. Run takes as parallel shooters on separate ports, and don't measure fps on the same
machine meanwhile.
