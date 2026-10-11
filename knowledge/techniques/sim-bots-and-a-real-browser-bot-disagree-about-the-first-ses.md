---
kind: technique
title: "Sim bots and a real-browser bot disagree about the first session: prove the first minutes with real taps"
tags: [verification, oracle, first-session, simulation, browser-bot, playwright, player-models, balance, determinism, frame-rate]
date: 2026-10-09
agents: ["Claude Code (Opus 5.5)"]
humans: []
links: []
---

# Sim bots and a real-browser bot disagree about the first session: prove the first minutes with real taps

> A headless balance simulation said every bot wins the first stage, 12 of 12. A bot playing the shipped
> build through the real UI lost it at about 2:05. The simulation was right about its own bots:
> they bought walls. A new player taps the first attack card that lights up and never opens the defence tab.
> Prove the first minutes with a browser bot that taps what a player taps, then teach the simulation that
> behaviour. And watch for a browser bot whose result depends on how fast the machine is.

## When to use it
- After any change to the opening of a game: first-stage health or counts, starting currency, the tutorial,
  the order or price of the first cards.
- Whenever a simulation is the only evidence for "a new player wins".
- Before a release: three or more real-browser first sessions on the local build, and one on the live URL.

## How
1. **Keep both oracles and know what each is for.** The headless simulation runs many seeds in seconds and
   answers "what does this number do". The browser bot is slow and noisy and answers "what happens to a
   person holding this build".
2. **Drive the real UI.** Project an enemy's world position to screen coordinates and send a touch there.
   Tap upgrade cards by their on-screen element, opening the category tab first when the card is on another
   tab. Reject tap points that are under the HUD or the dock, as a finger would.
3. **Use the debug bridge only to read state and to pass time.** Never to grant currency, set health or win.
4. **Write the players down as models**, each a tap interval, a buy interval and a rule for what to buy:

   | Model | Taps | Buys |
   |---|---|---|
   | passive | every 1 s | nothing |
   | tutorial follower | every 1.5 s | what the tutorial points at, every 10 s |
   | heavy tapper | every 0.45 s | the first affordable attack card, every 5.5 s |
   | efficient | every 0.5 s | attack and defence in balance, every 1 s |

5. **When the two disagree, diff behaviour before numbers.** What did each bot buy, in which order, from
   which tab? What did it tap? Which timed events were active? Was anything granted in one and not the other?
6. **Port the browser bot's behaviour back into the simulation** as a named style, so the cheap oracle covers
   the case from then on.
7. **Report per run**, not a verdict: the wave of a fall, walls at the end, lowest walls around each boss,
   seconds each boss stood, purchases.

## Verification
What the method found on a horde tower-defense mobile web game (Vite 7 + three.js 0.180, 8,000 enemies on
screen at 60 fps, portrait 390×844):
- **The disagreement.** Simulation: first stage won by every bot, 12 of 12. Browser on the live build: lost
  at about 2:05, its walls gone at wave 7.
- **The cause.** The opening is limited by shots: one starting gun fires about 2 shots a second while the
  stage brought about 10 bodies a second. Every simulation bot bought walls and outlasted it. The browser bot
  bought attack cards only and its 100-HP walls fell. Lowering enemy health could not help a shot cap:
  ×0.38 → ×0.15 moved the fall by seconds.
- **The fix was a different lever**: the same health per wave in fewer, tougher bodies (`openingSplit` in
  `src/game/ramp.js`).
- **After.** Browser: 5 of 5 won with 85-100 % walls, plus WebKit and a second language. The simulation's new
  `STYLE=playtest` went from 0 of 6 to 6 of 6.

## Gotchas
1. **The simulation said won, the browser said lost.** **Cause:** the simulated players made a purchase no
   new player makes. **Fix:** a simulation style that copies the browser bot's beat.
2. **Tuning the wrong number.** Earlier rounds had lowered first-stage health to make the opening winnable.
   The limit was fire rate against body count. **Fix:** find the binding constraint (shots, gold, reach)
   before moving a multiplier.
3. **Timed events are a difference to rule out.** In this project a live event had been adding enemy types
   that its on-screen chip did not mention (a player found it, not a bot). **Fix:** list the active events in
   every run's output, for both oracles.
4. **The simulation had no pickups.** A boss's tappable drop exists only with a view, so the real game gave
   skill charge and gold the simulation did not count. **Fix:** the simulation grants the drop as collected.
5. **The browser bot's result depended on machine speed.** The bot's loop sends real taps, then jumps the
   game forward with a debug step of 0.25 s, while real animation frames also advance the game in between.
   How much game time passes as real frames depends on how long each loop takes. The log records that runs
   "scatter widely and depend on the machine's frame rate": on one build the heavy tapper ended with 16 %
   walls and one loss while the laptop was capped at 30 fps, and an earlier cut of the same fix gave 27 % and
   26 % at 60 fps. The size of the effect was not isolated. **Fix:** either all fake time (pause the game loop
   and step it) or all real time; and compare two builds only under the same conditions.
6. **A bot cannot tap what is off screen.** A boss standing under the bottom dock got none of the bot's boss
   taps, and the stage looked easier than it was. When the spawn was fixed the bot's result changed. A
   change in what is visible is a change in the bot.
7. **Three runs is a smoke test.** Browser results on one build ranged 18 / 23 / 31 %. Use them to catch a
   loss, not to rank two builds.
8. **Bots agree with each other more than with people.** All of the above is still bots. Say so in the report.

## Open questions
- A browser bot on a fully faked clock, one simulation step per frame, would be deterministic. It was built
  for trailer capture and not for the playtest bot.
- No recorded human sessions were compared with the models.

## Seen in
- [The first stage as a rising sine](../games/horde-tower-defense-mobile-web/the-first-stage-as-a-rising-sine-odd-waves-push-even-waves-l.md)
- [Fixing a boss that never attacked changed the balance](../games/horde-tower-defense-mobile-web/fixing-a-boss-that-never-attacked-changed-the-balance-measur.md)
- Related: `a-difficulty-index-across-player-model-bots-and-how-to-read.md`,
  `a-laptop-in-low-power-mode-caps-the-browser-at-30-fps-and-si.md`.
