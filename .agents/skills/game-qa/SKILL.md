---
name: game-qa
description: Virtual testers for a web game in a real browser. Persona bots that play like players (casual, heavy tapper, idler, spender) in muted Chromium and WebKit at phone sizes (390x844, 320x568, 360x740) through `wise qa`; console and page errors, horizontal layout overflow, frame time (p50/p95/p99, frames over 33 ms), screenshots and a board of them as evidence; journeys through the real UI, real player saves and profiles, day rollover, robustness (rotate, hidden tab, double taps, reload mid-reward), boot that never hangs, capacity and late-game frame tests, and an adaptive quality guard that recovers. Use when the user says "test it", "QA this build", "does it work on iPhone", "check the first session", "play it like a player", "does the shop break", "it lags on stage 7", "stuck on the splash", "prove it in the browser", or whenever a change must be verified in the running build and not only in a unit test or a simulator.
---

# Game QA: virtual testers in a real browser

The running build is the oracle. The loop is open → play like a player → **screenshot, read errors, read
frame times** → decide. Build it once per game, then every change is checked in a minute. Unit tests and
simulators don't replace it: they agreed a first session was winnable while real taps lost it.

## 1. The quick gate: `wise qa`
```bash
npm i -D playwright && npx playwright install chromium webkit      # once, in the game repo
wise qa http://127.0.0.1:5173/ --ready "window.__game"              # Chromium 390x844, a casual player, 20 s
wise qa http://127.0.0.1:5173/ --engine webkit
wise qa http://127.0.0.1:5173/ --size 320x568 --seconds 60
```
`wise qa` opens the page in a muted phone browser (touch, device scale 2), lets every request through
(analytics included; `--block` is opt-in), plays for the given time, and fails on page or console errors and
on horizontal overflow. It prints the frame times and writes screenshots (start, each step, middle, end) and
`board.png`, all of them on one sheet, into `qa-out/<engine>-<WxH>-<persona>/`. In a clone it is `bin/wise`.

**The gate before a merge or deploy is three runs:** Chromium 390x844, WebKit 390x844, Chromium 320x568,
all with no errors and no overflow. Run it again against the live URL after a deploy.

## 2. Persona bots: play like the players you have
| Persona | Plays like | Catches |
|---|---|---|
| `casual` (default) | 2 taps a second at random in the play area, buys nothing | crashes, overflow, a first session that stalls |
| `tapper` | 5 taps a second | taps that delete bosses, double grants, input floods, frame drops under spam |
| `idler` | a tap every 5 s; mostly waits | idle timers, piles that grow unattended, offline income, auto-pause bugs |
| `spender` | every other action taps a visible buy / upgrade / claim / open control, least-tapped first | shop and chest flows, currency going negative, modals that trap, sinks that do nothing |

```bash
wise qa http://127.0.0.1:5173/ --persona spender --seconds 90 --start-selector "#play"
wise qa http://127.0.0.1:5173/ --persona spender --buy "[data-buy], .card button"   # name the controls
wise qa http://127.0.0.1:5173/ --persona tapper --max-p95 20                        # also gate on frame time
```
- **The spender never pays real money.** It skips any control that shows a price with a currency sign or
  says pay, purchase, subscribe or checkout. Real purchases need a person's yes; test paid flows with debug
  grants in a local build.
- **Personas tap; they don't cheat.** `window.__game` may set up a profile or speed time; it never wins.
- **A bot can only tap what it can see.** A boss that entered under the upgrade dock could not be tapped, so
  the bot's result did not match a player's. Look at the board, not only the numbers.
- **Prove first sessions here, not in the sim.** Sim bots bought walls; real new players tap attack cards.
  After any early-game change, run 3+ fresh-profile first fights and report walls left at the clear (the
  **game-balance** skill has the worked case).

## 3. Journeys
For a flow `wise qa` can't guess (language switch, shop, a second fight), list the taps:
```bash
wise qa <url> --start-selector "#play" --selector "[data-tab=shop]" ".offer:first-child .buy" "#close" --persona casual
```
A missing selector is an error. For anything longer, copy `scripts/journey.template.mjs` into the game repo
and fill in its JOURNEY section (`node journey.template.mjs <url> <outDir> [chromium|webkit] [390x844]`).

**The main regression, before every deploy:** fresh profile → first fight → result → hub → switch language
→ shop, upgrades, collection, pass, events → second fight → back. Screenshot each step, in Chromium 390,
WebKit 390 and Chromium 320.

Profiles (new, returning from old saves, mid-game, late-game, spender), day rollover (day 2 / 7 / 8) and the
robustness list (rotate, hide the tab 30 s, double taps on claim, reload mid-reward) are in
`references/profiles-and-journeys.md`.

## 4. Harness rules (every automated browser run)
- **Muted, always.** Chromium with `--mute-audio`; WebKit routes every `AudioContext` through a zero-gain
  node; media elements are muted. Never any speaker output.
- **Real data first.** Analytics go to the real endpoint, and a real player's save beats a made-up one.
  Bots and fixtures fill the gaps where no real data exists yet.
- **Mobile context:** `isMobile`, `hasTouch`, device scale 2-3; 390x844 and 320x568, plus 360x740 for mid
  Android.
- **Its own profile and port** per run and per agent. Stop the server you started; kill by exact PID.

## 5. Frame time and performance
`wise qa` reports requestAnimationFrame intervals: frames, fps, p50 / p95 / p99, frames over 33 ms, worst.
Headless frame times compare builds on one machine; they are not a phone's fps.
- **Is this machine fit to measure?** On mains power, low-power mode off, nothing heavy alongside. A laptop
  on battery in low-power mode caps the browser at 30 fps: every build reads a flat 30. Measure the live
  build side by side; if it reads 30 too, the machine changed, not the game. Then report "not confirmed",
  not "failed".
- **Two tests, always both:** capacity (spawn 2,000 / 5,000 / 8,000 enemies, walls held: 60 fps, p95 ≤
  16.8 ms) and real late-stage play (a real late save, real buys, boss + giants on screen) at desktop,
  phone 390x844 @3x and 4x CPU throttle. Capacity misses what real play does.
- **An adaptive quality guard must recover.** On a 60 Hz screen a frame is never under 16.7 ms, so "restore
  after frames under 13 ms" never fires and a slow patch stays a slideshow for the rest of the fight.
- **Boot must never hang:** a failed chunk retries under a fresh URL, then one reload, then a Retry screen.
  Prove it with a fault matrix and 60+ cold boots.

`references/performance.md` has the method and the budgets; `references/quality-guard.md` the recovery
rule; `references/load-and-boot.md` the load numbers and the fault matrix.

## 6. Fake clock or real time
| | Real time | Fake or stepped clock |
|---|---|---|
| Answers | does it feel right, hold fps, boot | is the rule right, is the run repeatable |
| Bot result depends on | the machine's frame rate | nothing but the seed |
| Use for | regression journeys, frame time, first-session feel | day rollover, balance runs, trailer captures |

- An installed fake clock still flows with real time unless you pause it; then advance it one step per action.
- CSS animations and native smooth scrolling run on real time under a paused clock.
- Loops in scripts count game time, not wall time.

## 7. Evidence and report
- Every screenshot has a numbered name; `board.png` puts a run on one sheet. For before/after boards of
  fixes, `wise board` (the **design-boards** skill) lays out mockups or real screenshots.
- **Look at the screenshots yourself before reporting.** No errors with a blank canvas is a pass that isn't.
- **Report:** what changed for the player first; then a table per profile and persona: issue → severity (S1
  broken or soft-lock, S2 confusing or wrong, S3 polish) → fixed (commit) or reported; the frame-time table
  with the machine state; the boards. End with what was not covered: "no real phone, no real Safari" is true
  of every headless run.

## Known traps
- A local `python -m http.server` drops connections under parallel load (`ERR_CONNECTION_RESET`). Not a game
  bug, but the game must survive it (boot retry); it is how a boot hang was found.
- Right after a deploy an asset may 404 for a few seconds; recheck after 20 s before panicking.
- A closing window that keeps its `.modal` class is still "open" to a script on the next frame. Wait for the
  class, not for a timeout.
- Headless WebKit is not Safari on a phone. It catches engine differences (audio, CSS, touch); it does not
  prove device performance.
- A giant wedged between two pieces of scenery soft-locked the last wave in one run of three: soft-locks
  show up as a run that never ends, so give every bot run a time limit and report "still running" apart.

## References
- `references/profiles-and-journeys.md`: profiles to cover, day rollover, robustness. Read it for a release pass.
- `references/performance.md`: machine fitness, capacity and late-stage tests, budgets, the report.
- `references/quality-guard.md`: the guard's levels, the 60 Hz trap and the recovery rule.
- `references/load-and-boot.md`: staged loading, cache headers, the boot fault matrix.
- `scripts/journey.template.mjs`: the muted Chromium/WebKit harness for custom journeys.
- Notes in `knowledge/`: the low-power 30 fps trap, the quality guard that never recovered, the boot splash
  that stayed up, the giant that soft-locked a wave, and sim bots vs a browser bot.
