# When the sim and the browser disagree

Simulators lie about first sessions. This is the worked case, then the checklist.

## The case: a first siege the sim won and the browser lost
- **Symptom.** Every sim bot cleared stage 1. The real-browser playtest bot lost at wave 7, every time.
- **Cause.** The bots bought walls from the Defense tab and outlasted the horde. The browser bot does what a
  new player does: it buys the first affordable Attack card and never opens Defense. The first siege was
  *shot-limited*: one starting weapon fired about 2 shots a second while the stage brought about 10 bodies
  a second.
- **What did not fix it.** Lowering enemy HP. A shot cap doesn't care how soft the bodies are: cutting stage
  HP from ×0.38 to ×0.15 moved the fall by seconds.
- **Fix.** Same health per wave, fewer and tougher bodies in the opening stages (a cap on how far a wave's
  health may be split into bodies: 1.2× the base count on stage 1, 2× on stage 2).
- **Result.** Browser: first siege won 5 of 5 with walls 85–100% at the clear, plus WebKit and Spanish. Sim:
  a new bot style that copies the browser bot's buying cleared 6 of 6 (was 0 of 6).

The lesson is rule 1 of the router: tune count and pressure shape, not HP. And add a sim style that buys
like the browser bot, so the next disagreement shows up in the sim first.

## Checklist when they disagree
1. **What does each bot buy?** Compare the purchase lists wave by wave. This was the answer above.
2. **What does each bot tap?** A boss hidden under the upgrade dock can't be tapped by a bot that taps the
   field. One was, until bosses were made to enter from up the screen.
3. **Which events are active?** Weekend events, gifts, blessings and tutorial steps exist in the browser and
   often not in the sim.
4. **What time base?** The sim steps a fixed clock. The browser runs on real frames. See below.
5. Only then tune.

## Browser bot results depend on machine speed
A bot that taps on a real-time interval gets fewer taps per simulated second when the page runs slowly. The
same build then gives different results on different machines, or on the same machine an hour later.

Measured on one build, model C (heavy tapper), walls left at the stage-1 clear:
- at 60 fps: 27% and 26%;
- on the same laptop on battery in low-power mode (browser capped at 30 fps): 16% and one loss;
- the unchanged live build under the same low-power conditions: 23% and 31%.

So one loss on a slow machine is not a regression by itself.
- **Run the live build side by side** in the same session, on the same machine state, before blaming the
  change.
- **Prefer game time to wall time** in bots: tap every N simulated milliseconds, or step the sim through the
  debug hook, when the question is balance and not feel.
- **Report the scatter.** Three or more runs per model, the range and not the mean alone. Headless models on
  8 seeds gave model B 22–61% (mean 44) and model C 16–52% (mean 30) on that build: a wide band is the
  honest answer.
- **Say which numbers are sim and which are browser** in the report.

## Making the two comparable
- Share one tuning source: the sim imports the game's tables, never a copy.
- The sim counts what the live game pays. Ours did not count the boss drop at first, so its gold was not the
  player's gold.
- Fix the simulation rate the sims use (30 Hz there) and prove that performance work doesn't change it: hash
  the sim state before and after an optimisation (see the **game-performance** skill).
