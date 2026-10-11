# QA in real browsers

## Harness rules (every automated browser run)
- Chromium with `--mute-audio` (system Chrome channel is fine); WebKit with the zero-gain `AudioContext.destination` init script; never any speaker output.
- Intercept `**/api/events` with `route.fulfill({ status: 204 })` so test runs never pollute analytics.
- Mobile context: `isMobile`, `hasTouch`, DPR 2–3; viewports 390×844 and 320×568 (and 360×740 for mid Android).
- Collect `pageerror`; the gate is `errors: []` and no horizontal overflow (`scrollWidth > innerWidth`).
- Template: `scripts/qa/browser-qa.template.mjs`.

## The main regression (run before every deploy)
Fresh profile → first battle → result → hub (EN) → switch to ES → shop, workshop, armory, pass, race → second siege → back to EN. Screenshot each step. Run it in Chromium 390, WebKit 390 and Chromium 320. Run it again against the live URL after the deploy.

## Bots that play like people
- Drive the real UI: tap the field, tap dock cards in dock order, open modals by their buttons. Use `__game` only to speed time or set up a profile, never to win.
- **Profiles to cover:**
  - a brand-new player (EN 390 and ES 320);
  - a returning player from older version saves;
  - a mid-game save;
  - a late-game save into the next chapter;
  - a spender (gacha ×10, star-ups, pass);
  - WebKit.
- Return to day 2 / 7 / 8 by overriding `Date`: dailies, weeklies and pass roll over; nothing grants twice after a reload.
- **Robustness:** rotate mid-siege, hide the tab for 30 s (`visibilitychange`), spam double-taps on claim, buy and open buttons, and reload mid-gacha.

## Report format
A table per profile: issue → severity (S1 broken or soft-lock, S2 confusing or wrong, S3 polish) → fixed (commit) or reported. Plus a before/after board of the main fixes.

## Known traps
- A local `python -m http.server` drops connections under parallel load (`ERR_CONNECTION_RESET`). That's not a game bug, but the game must survive it (boot retry).
- Right after a deploy an asset may 404 for a few seconds; recheck after 20 s before panicking.
- Sims and browsers disagree about first sessions; see `economy-balance.md` §6.
