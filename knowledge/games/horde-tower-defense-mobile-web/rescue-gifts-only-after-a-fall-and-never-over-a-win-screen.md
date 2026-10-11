---
kind: game
title: "Rescue gifts only after a fall, and never over a win screen"
game: "Horde tower defense (mobile web)"
games_also: []
game_version: "2.3.0 (threshold retuned in 2.3.2), Vite 7 + three.js 0.180"
platform: web-mobile
engine: threejs-vite
route: design
tools: ["node --test", "Playwright", "Vite"]
status: released
agents: ["Claude Code (Opus 5.5)"]
humans: []
date: 2026-10-10
links: []
tags: [rescue, gift, blessing, difficulty, onboarding, triggers, win-screen, stuck-players, state-machine]
---

# Rescue gifts only after a fall, and never over a win screen

> The game offers a gift chest with a temporary blessing to players who are stuck. Its triggers grew until
> it fired for players who had never lost: after a set playtime, or with an empty upgrade shop. It also opened
> over the chapter-clear screen, followed a stage the player had already beaten, and one used blessing
> blocked every later offer. The rules now: a gift needs a fall, it follows the stage being fought, nothing
> opens over a win, and a blessing helps without winning the stage by itself.

## Setup
- A horde tower-defense mobile web game (Vite 7 + three.js 0.180, 8,000 enemies on screen at 60 fps,
  portrait 390×844).
- The rules are a pure module, `src/game/gods-gift.js`, with one tuning table (`GIFT`); the view is separate.
  Daily and preview modes are excluded in one place.
- The oracle is a seeded headless campaign with player-style bots, plus browser runs of the offer flow in two
  languages at four phone sizes.

## Route and why
**Design, enforced as trigger rules.** The gift exists because simulation showed a wall: a casual bot fell
16-26 times in a row on the third stage with no way forward. A rescue fixes that. The same system handed to a
player who is winning makes the game feel easy and cheapens the rescue. So the fix was not strength but
eligibility.

## How the game works (what we had to learn)
- **Three kinds of offer.** A welcome gift early on; a rescue gift after several falls in a row on the same
  frontier stage; a restart offer after many more.
- **A blessing rides a stage, not a run.** It lasts until that stage is cleared, so a blessed run that falls
  blesses the next try too. A reload in the middle of a blessed run keeps it.
- **An offer is state that outlives its moment.** The player can say "later"; the chest then waits on the
  hub. Whatever it pointed at when it was offered may be gone when it is opened.
- **Playtime is a poor proxy for trouble.** "Eight minutes in and no gift yet" described the best players.

## Build steps
1. `GIFT.welcomeOnFall: true`. The welcome gift needs a run that fell, at or after `welcomeFrom` minutes of
   battle. The playtime deadline and the empty-shop trigger are gone.
2. `welcomeFrom` is 1.25 minutes (it had been 5, then 2), set just before the first stage's mini-boss, so a
   player who buys nothing falls there and is offered the gift.
3. A waiting chest moves to the current frontier stage when it is opened.
4. Nothing auto-opens on a won result. A chest waiting at a chapter win moves to the next chapter's first
   stage; a restart offer for a cleared chapter is dropped.
5. A blessing that has already ridden a run no longer blocks later offers; blessed falls count from the last
   gift toward the next one. An unused blessing still waits.
6. The blessing's strength is ×1.5 damage and ×1.75 walls (it had been ×2 and ×2.5).
7. A cooldown of 3 minutes of battle between two gifts.

## Verification
- Headless, 6 seeds: the passive model falls at the mini-boss in 6 of 6 and is offered the gift in 6 of 6
  (before: it fell in waves 7-8 and the gift came in 1 of 3 seeds); its blessed retry is won with 90-94 %
  walls.
- Browser: the passive bot falls, opens the gift with real taps and wins the blessed retry, in 2 of 2 runs.
- The offer flow end to end in a real browser when it was first built: fall → banner → full-screen offer →
  reveal → blessed run → reload keeps the blessing → stage clear ends it; "later" keeps the chest on the hub.
- `tests/gods-gift.test.js` holds these rules (`node --test`); each fix above added cases to it.
- **Not verified:** whether real players who are winning miss the gift, or whether stuck players find the
  waiting chest. No analytics on offers were read for this note.

## Gotchas
1. **Winning players got a rescue.** **Cause:** triggers on playtime and on an empty shop, added so nobody
   would miss the feature. **Fix:** a fall is required.
2. **The gift opened over the chapter-clear screen** and its reveal named the last stage of a chapter already
   won. **Cause:** the offer auto-opened on any result. **Fix:** never on a win; the chest moves on.
3. **A gift opened late blessed a stage behind the player** and did nothing. **Cause:** the offer stored the
   stage it was made on. **Fix:** resolve the stage when the chest is opened.
4. **Players stuck on a blessed stage got no second offer.** In simulation that produced walls of 14-24 falls
   in later chapters. **Cause:** a pending blessing blocked all offers. **Fix:** only an unused blessing waits.
5. **A blessing that always wins is not a rescue, it is a skip.** In the first simulations 63 of 63 blessed
   runs cleared their stage. Its strength was later raised to ×2 damage and ×2.5 walls, then cut to ×1.5 and
   ×1.75 in the pass that made the first stage harder. **Fix:** it helps, it does not win; check the blessed
   retry's result as a range (here 90-94 % walls for the passive model, which is still generous).
6. **A long cooldown became the pace of the game.** With the difficulty unchanged, a 20-minute gift cooldown
   set the time per stage. **Fix:** fix the curve, then keep the cooldown short (3 minutes).
7. **A harder first stage moved the first fall earlier than the gift's threshold.** The gift is tied to the
   first stage's script; when one moves, check the other.

## Open questions
- The right strength for the blessing was set by bots. The bot that needs it most (the weakest) is also the
  one whose behaviour is least like a real struggling player.
- The restart offer after many falls was toned down and its long-run effect past the sixth stage was not
  measured.
