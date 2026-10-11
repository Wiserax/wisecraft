---
name: browser-qa
description: Test a web game the way a player meets it, in muted headless phone browsers. Covers `wise qa` and a template script for custom flows, Chromium and WebKit at 390x844 and 320x568, bots that tap the real UI, analytics answered with a 204 so test runs never pollute data, the errors and overflow gate, the main regression journey, player profiles and old saves, day rollover, robustness (rotate, hide the tab, double taps, reload), fake clock versus real time, and screenshot boards as evidence. Use when the user says "test it", "does it work on iPhone", "check the first session", "QA before release", "why did the bot lose", "prove it in the browser", or whenever a change must be verified in the real build and not only in a unit test or a simulator.
---

# Browser QA: the agent's hands and eyes

The running build is the oracle. The loop is open → tap like a player → **screenshot and read errors** →
decide. Build it once per game, then every change can be checked in a minute. Unit tests and simulators
don't replace it: they agreed the first session was winnable while real taps lost it.

## The quick gate: `wise qa`
```bash
npm i -D playwright && npx playwright install chromium webkit      # once, in the game repo
wise qa http://localhost:5173/ --out qa-out                          # Chromium, 390x844
wise qa http://localhost:5173/ --engine webkit --out qa-out
wise qa http://localhost:5173/ --size 320x568 --seconds 60 --out qa-out
```
`wise qa` opens the page in a muted phone browser, answers `/api/events` with 204, taps like a player for the
given time, takes screenshots, and fails on page errors or horizontal overflow. In a clone it is `bin/wise`.

The gate before a merge or deploy is three runs: **Chromium 390×844, WebKit 390×844, Chromium 320×568**, all
with `errors []` and no overflow.

For a flow `wise qa` can't guess (language switch, shop, a second fight), copy
`scripts/browser-qa.template.mjs` into the game repo and fill in its JOURNEY section:
```bash
node browser-qa.template.mjs <url> <outDir> [chromium|webkit] [390x844]
```

## Harness rules (every automated browser run)
- **Muted, always.** Chromium with `--mute-audio` (system Chrome channel is fine); WebKit with the zero-gain
  `AudioContext.destination` init script; never any speaker output.
- **Analytics blocked.** Intercept `**/api/events` with `route.fulfill({ status: 204 })` so test runs never
  pollute analytics. A 204 and not an abort: the game must see a normal answer and take its normal path.
- **Mobile context:** `isMobile`, `hasTouch`, DPR 2–3; viewports 390×844 and 320×568 (and 360×740 for mid
  Android).
- **The gate:** collect `pageerror`; `errors: []` and no horizontal overflow
  (`scrollWidth > innerWidth`).
- **Its own profile and port.** A fresh profile per run unless the test is about a returning player. Stop
  the server you started.

## The main regression (run before every deploy)
Fresh profile → first battle → result → hub (EN) → switch to ES → shop, workshop, armory, pass, race →
second siege → back to EN. Screenshot each step. Run it in Chromium 390, WebKit 390 and Chromium 320. Run it
again against the live URL after the deploy.

## Bots that play like people
- **Drive the real UI:** tap the field, tap dock cards in dock order, open modals by their buttons. Use
  `__game` only to speed time or set up a profile, never to win.
- **Prove the first session in the browser.** Simulators lie about first sessions: sim bots buy walls, real
  new players tap Attack cards. After any early-game change, run 3+ fresh-profile first fights with the
  playtest bot and report walls left at the clear.
- **A bot can only tap what it can see.** A boss that entered under the upgrade dock could not be tapped, so
  the bot's result did not match a player's. Look at the screenshots, not only the numbers.

Profiles, day rollover and the robustness list are in `references/profiles-and-journeys.md`.

## Fake clock or real time
Choose on purpose; the two answer different questions.

| | Real time | Fake or stepped clock |
|---|---|---|
| Answers | does it feel right, does it hold fps, does boot work | is the rule right, is the take repeatable |
| Bot result depends on | the machine's frame rate | nothing but the seed |
| Use for | the regression journey, performance, first-session feel | day rollover, balance runs, trailer captures |

- **Bot results that depend on machine speed.** A bot tapping every N real milliseconds lands fewer taps per
  game second on a slow machine. The same build cleared stage 1 with 27% walls at 60 fps and lost once on
  the same laptop capped at 30 fps. Run the live build side by side before blaming the change, or tap on
  game time (the **game-economy** skill has the worked case in its sim-vs-browser reference).
- **An installed fake clock still flows with real time unless you pause it.** Pause it, then advance it one
  step per action or frame.
- **Not everything follows the fake clock.** CSS animations and native smooth scrolling run on real time
  under a paused clock. Step animations explicitly and scroll by setting `scrollTop`.
- **Loops in scripts count game time, not wall time.** A take that looped for "15 s" on the wall clock
  captured about 4 s of game.

## Evidence: boards, not paragraphs
- Screenshot every step with a numbered name (`chromium-390-3-hub-es.png`).
- Compose the main fixes into a before/after board (`wise board`, the **design-boards** skill). A board of
  real screenshots with the tapped spot marked beats a paragraph.
- Look at the screenshots yourself before reporting. `errors []` with a blank canvas is a pass that isn't.

## Report format
A table per profile: issue → severity (S1 broken or soft-lock, S2 confusing or wrong, S3 polish) → fixed
(commit) or reported. Plus a before/after board of the main fixes. Start with what changed for the player.
End with what was not covered: "no real phone, no real Safari" is true of every headless run.

## Known traps
- A local `python -m http.server` drops connections under parallel load (`ERR_CONNECTION_RESET`). That's
  not a game bug, but the game must survive it (boot retry; the **game-performance** skill).
- Right after a deploy an asset may 404 for a few seconds; recheck after 20 s before panicking.
- Sims and browsers disagree about first sessions; see the **game-economy** skill.
- A closing window that keeps its `.modal` class is still "open" to a script on the next frame. Wait for the
  class, not for a timeout.
- Headless WebKit is not Safari on a phone. It catches engine differences (audio, CSS, touch); it does not
  prove device performance.

## References
- `references/profiles-and-journeys.md`: the player profiles to cover, returning on day 2 / 7 / 8, and the
  robustness list. Read it for a release QA pass.
- `scripts/browser-qa.template.mjs`: the muted Chromium/WebKit harness for custom journeys (needs
  Playwright).
