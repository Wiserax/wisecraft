---
kind: game
title: "Pay rewards the instant the run ends; the celebration only presents them"
game: "Horde tower defense (mobile web)"
games_also: []
game_version: "2.3.1, Vite 7 + three.js 0.180"
platform: web-mobile
engine: threejs-vite
route: ui
tools: ["node --test", "Playwright", "Vite"]
status: released
agents: ["Claude Code (Opus 5.5)"]
humans: []
date: 2026-10-10
links: []
tags: [rewards, idempotency, reload, celebration, save, double-grant, result-screen, slow-motion, run-id]
---

# Pay rewards the instant the run ends; the celebration only presents them

> A chapter-clear celebration was added: one second of quarter-speed play, a white flash, fireworks, a medallion
> turning gold, stars landing, then the rewards. A long show between "the run ended" and "the player has the
> reward" is where a reload loses the grant or pays it twice. The rule built in from the start: the profile
> is settled on the frame the run ends, keyed on the run's id, and everything after that is presentation. A
> test settles the same result twice and across a save round trip and requires one payment.

## Setup
- A horde tower-defense mobile web game (Vite 7 + three.js 0.180, 8,000 enemies on screen at 60 fps,
  portrait 390×844).
- The profile is a JSON object in `localStorage`. A run in progress is saved inside it (`active`) so a reload
  resumes the fight.
- A finished run produces a result object with an id. `settleRun(profile, result)` in `src/game/profile.js`
  pays coins, premium currency, records and milestones.

## Route and why
**UI, with the money moved out of it.** The celebration layer (`chapter-celebration.js` and its stylesheet)
takes numbers to show and owns no state. This note records a rule that was designed in and tested, not a
double grant that reached players: the sources hold the rule, the test and the reasoning, and no report of a
duplicate payout in the wild. Bugs of the same family were real in the same week: a double tap opened two
gacha crates, and a rescue gift popped over the win screen.

## How the game works (what we had to learn)
- **Three moments look like one.** The run ends; the profile is paid; the player sees the payment. With a
  result sheet they are the same frame. With a show several seconds long they are not.
- **A resumable run is a second way to finish.** If the saved run still exists after the payout, a reload
  resumes it and it ends again.
- **Slow motion is real time.** The quarter-speed beat before the flash is time in which the tab can be
  closed or reloaded.
- **The wallet animation is separate again.** Coins fly into the wallet on the hub afterwards, driven by a
  claims layer that animates a difference already stored.

## Build steps
1. On the frame the run's status becomes won or lost: build the result, call `settleRun`, clear the saved
   run, write the profile. Only then start the slow motion and the show.
2. `settleRun` returns `{ duplicate: true, coins: 0, gems: 0 }` when the profile's history already holds the
   result's id. Every caller can call it again safely.
3. The celebration receives `{ chapter, coins, gems }` and renders. Its primary button goes to the hub; a
   secondary one shows the plain results sheet.
4. The wallet count-up reads what was paid; it grants nothing.
5. Reduced motion: one fade, no flash, no slow motion. The payout path is the same.
6. Layout checked in two languages and at 320×568.

## Verification
- `tests/chapter-celebration.test.js` (`node --test`): a won run is settled once and pays the chapter bonus;
  settling the same result again returns `duplicate` and changes nothing; the profile is serialised, parsed
  and normalised (a reload), has no saved run left to resume, and settling again still pays nothing.
- The same file checks the layer's content and the order of its sounds with fake timers.
- QA profiles in a real browser include double taps on claim, buy and open buttons and a reload in the
  middle of a gacha opening.
- **Not verified:** a real kill of the tab during the slow-motion second on a phone. The test covers the
  logic of that case, not the browser's storage flush.

## Gotchas
1. **A reload during the show would lose or repeat the grant.** **Cause:** paying at the end of the
   presentation. **Fix:** pay when the run ends; the show waits, the money does not.
2. **A second tap on the finishing button pays again.** **Cause:** a handler that both grants and navigates.
   **Fix:** the grant is idempotent on the run's id, so the handler cannot matter.
3. **Clearing the saved run after the show leaves a resumable finished run.** **Fix:** clear it in the same
   write as the payout, and assert in the test that nothing is left to resume.
4. **Reward sounds follow the same rule as reward money.** An earlier reward flow played its claim tick on a
   button that only navigated, and needed its own sound entry. **Fix:** the celebration reuses existing stings
   (a fanfare, a coin per star, the bank sound) in a fixed order, and the test pins that order.
5. **A rescue gift opened over the chapter-clear screen**, naming a stage already won. **Cause:** an offer
   with its own "open when the result shows" trigger. **Fix:** nothing auto-opens on a won result (see the
   note on rescue gifts).
6. **The celebration's primary button said the wrong thing.** After a win the button must name what happens
   next (next stage, next chapter), not offer to defend again.

## Open questions
- Whether the profile's history of run ids is ever trimmed, and what settling a very old id does then, was
  not checked.
- Server-side validation does not exist; the profile is local.
