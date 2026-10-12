# Benchmark: with vs without Wisecraft

A small, honest test of whether the plugin changes what an agent delivers.

**Status: run once, on 2026-10-11.** 18 headless sessions (claude-opus-5-5 (the CLI's default), 60 turns at most, about
17 USD in total). Every trial is in [`results.json`](results.json); the README chart is drawn from it.

| | with Wisecraft | without |
|---|---:|---:|
| Checks passed (mean ± sd, n = 9) | 100.0% ± 0.0 | 97.8% ± 6.7 |
| Trials passing every check | 9 of 9 | 8 of 9 |
| Minutes per task | 3.7 ± 1.3 | 3.6 ± 1.6 |
| Tokens per task, cached reads included | 0.88 M ± 0.45 | 0.83 M ± 0.42 |

**What it shows: nothing yet.** Both arms pass nearly every scripted check, so the checks hit their ceiling and
cannot separate the arms. The one failure (without the plugin, first-stage task) was a stage that killed a
passive player inside 30 s. Time and tokens are within each other's spread. To be useful this benchmark needs
harder tasks and checks that look at quality: pressure shape over the waves, a boss the player sees coming, a
build proven in a phone browser.

## What it does
- **The game:** [`examples/horde-demo`](../examples/horde-demo), about 200 lines of Vite + three.js, unfinished on purpose.
- **Three tasks** ([`tasks.json`](tasks.json)), given as one prompt each, with no follow-up:
  1. "the first stage is boring and too easy, fix it";
  2. "add a boss that walks in and slams the base";
  3. "make it ready to release".
- **Two arms:** the same headless agent, model and turn limit; one loads this plugin, one runs with skills disabled.
- **Scoring by script** ([`score.mjs`](score.mjs)): the checks play seeded sieges through the sim's public API
  and read files. They never read what the agent said. Examples: the tests pass and a test was added; the walls
  take damage in the first 60 s but an attentive player still clears; the boss first appears at the rim, reaches
  the fort, damages the walls and survives at least 8 s of tapping; the version changed everywhere it is written;
  the build carries no key or private URL.
- **Measured:** share of checks passed, wall-clock minutes, tokens as reported by the agent CLI; mean and standard
  deviation over the trials of each arm.

## Run it
```bash
python3 benchmarks/run.py --dry-run          # the 18 commands, nothing run
python3 benchmarks/run.py --trials 3         # spends real tokens: 18 agent sessions
python3 benchmarks/run.py --report ~/.wisecraft/bench/<stamp>
node benchmarks/score.mjs examples/horde-demo boss-walks-in      # score any folder by hand
```
The untouched sample game scores 3 of 5, 1 of 6 and 2 of 5: that is the floor.

## What it cannot tell you
- Three small tasks on one tiny game are not a real project. The numbers in the README's before/after chart come
  from one; these would come from a toy.
- The checks reward what they can see. A boss with a beautiful entrance and a boss that is a bigger box score the same.
- Three trials per cell is a small sample: read the standard deviation before the mean.
- The "without" arm disables all skills, so it also loses any other skills the machine has installed.
