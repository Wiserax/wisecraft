---
kind: game
title: "A reset connection on one code chunk left the boot splash up for good"
game: "Horde tower defense (mobile web)"
games_also: []
game_version: "2.3.0-preview, Vite 7 + three.js 0.180"
platform: web-mobile
engine: threejs-vite
route: engine-code
tools: ["Playwright", "node --test", "Vite"]
status: released
agents: ["Claude Code (Opus 5.5)"]
humans: []
date: 2026-10-09
links: []
tags: [boot, loading, chunk, retry, preload, connection-reset, splash, fault-injection, cold-boot, fonts]
---

# A reset connection on one code chunk left the boot splash up for good

> During QA the game sometimes stayed on its splash with an error line and nothing retrying. The cause was a
> connection reset on one preloaded code chunk: 5 of 20 boots against a local server under load. Boot now
> retries a failed file under a fresh URL, then reloads the page once per tab, then shows a Retry screen; a
> request that hangs triggers one reload after 15 s. A matrix of 57 single faults went from 20 to 47 boots
> ending in a live game and from 5 endless splashes to 0, the same in WebKit. 80 cold boots passed.

## Setup
- A horde tower-defense mobile web game (Vite 7 + three.js 0.180, 8,000 enemies on screen at 60 fps,
  portrait 390×844).
- The build is Vite with code split into an app chunk, a three.js chunk and an audio chunk. An earlier
  load-time pass had added a plugin that preloads those chunks and the stylesheet from the page head.
- The page that hosts the game is `play.html`; the loader is `src/game/boot.js`.
- Local QA served the built folder with Python's `http.server`, with several browser jobs in parallel.

## Route and why
**Engine code in the loader, proven by fault injection.** The local server is not production, and the first
reading was "a test-environment problem". But a phone on a train drops connections the same way, and a boot
that cannot recover from one lost file is a real defect. So the server's behaviour became the test case.

## How the game works (what we had to learn)
- **A failed preload took the import down with it.** When the preloaded chunk's request was reset, the game's
  own import of the same URL failed too, and asking again for the same URL was answered by the failed request.
  (Observed behaviour; the browser internals were not investigated.)
- **A hung request gives no error.** There is nothing to catch, so a retry on error never runs.
- **Fonts were on the critical path.** Boot waited for them.
- **The hand-off from splash to game waited on an animation frame** with no timer behind it.
- **Preloading everything from the head competes with the splash art** on a slow link. The art that the
  player is looking at arrived later (1.25 s against 0.72 s before the preload plugin, Fast 4G profile).

## Build steps
1. Remove the static chunk preloads from the head. Ask for the splash art first and alone for up to 100 ms,
   then send fonts and code together.
2. Retry a failed game file under a URL the browser has not asked for: append `?retry=<n>`. Stylesheet first
   if that is what failed, then the game.
3. If that fails, reload the page, once per tab. A `sessionStorage` flag marks the reload; it is cleared when
   the game comes up.
4. If no file of any kind has arrived for 15 s while the code is wanted, reload once (same flag).
5. After the reload has been used, show a Retry screen with a button. Never an endless splash.
6. Fonts optional and time-boxed. The frame hand-off gets a 250 ms timer. The host page guards its own entry
   script.
7. Sound downloads keep to four connections on HTTP/1.1 (eight on HTTP/2 and 3), and every request has a time
   limit.

## Verification
- **Reproduction:** the old code against `http.server`, right after two heavy parallel jobs: 5 of 20 boots
  failed with `ERR_CONNECTION_RESET` on the preloaded three.js chunk and stayed on the error line.
- **Fault matrix:** 57 single faults (one file failing or hanging, per file and per fault type), old → new:
  boots ending in a live game 20 → 47; endless splashes 5 → 0. Same counts in WebKit. The remaining 10 are
  not endless; the sources do not list their end states one by one.
- **Stress:** 60 Chromium cold boots on Fast 4G with the CPU slowed 4×, and 20 WebKit boots against a server
  paced to 1 MB/s with 150 ms per request: 0 failures, median 3.5 s and 1.9 s to a live game.
- **Side effects measured:** splash art in at 0.77-0.81 s on Fast 4G (was 1.25 s) for 24-44 ms later code;
  the full sound set finishes about 2 s later on HTTP/1.1; 126 of 126 buffers, 0 failed.
- `tests/boot.test.js` was added for the loader's rules (`node --test`).
- **Not verified:** real mobile networks; a CDN that serves a truncated file with a 200.

## Gotchas
1. **The splash stayed up for good with an error line.** **Cause:** a reset on a preloaded chunk; the failed
   preload also failed the import, and nothing retried. **Fix:** retry under a fresh URL, reload once, then a
   Retry screen.
2. **Retrying the same URL fails again at once.** **Cause:** the browser answers from the failed request.
   **Fix:** a query string it has not seen.
3. **An unconditional reload on failure is a reload loop.** **Fix:** one reload per tab, tracked in
   `sessionStorage`, cleared on success.
4. **A hang never reaches the error handler.** **Fix:** a watchdog on "no file has arrived for 15 s".
5. **`python -m http.server` drops connections under parallel load.** Its resets are a harness problem, not a
   game bug, and also a free fault injector: the game has to survive them. Keep it in the stress set.
6. **The original evidence was gone.** The first hang was seen once and the server log was lost. **Fix:**
   reproduce before fixing, and say in the report that the reproduction is an equivalent, not the original.
7. **The load-time optimisation caused the fragility.** Preloading chunks from the head saved time on a good
   link and made one lost file fatal. Head-only hints (`fetchpriority`) were measured and did nothing.
8. **The fix touched a file outside the worker's ownership list** (the build config, to remove the plugin).
   It was reported as such. Say so every time.

## Open questions
- 10 of 57 single faults still do not end in a live game. Which of those could recover silently was not
  worked out.
- Whether a service worker would make cold boots after the first one immune was not tried.
