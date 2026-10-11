---
name: web-game-recon
description: Inspect an existing web game before changing it, so every later step rests on facts and not on guesses. Covers the stack and versions (`wise scan`), entry points, the core loop, the save format with its versions and migrations, analytics events and the endpoint, debug and mod hooks (`window.__game`), tests, the performance baseline and where the tuning tables live. Use when the user says "look at this game first", "what is this built with", "how does the save work", "can we add X to this game", "take over this repo", or at the start of any task on a game the agent did not write in this session. Produces GAME_PLAN.md.
---

# Web game recon

Goal: in about ten minutes, know what you're dealing with and which route to take. Write the answer down so
every later step can rely on it. Recon reads; it changes nothing in the game.

## 0. Has another agent been here?
`wise kb search "<game>"` and `wise kb search "<engine>"` (for example `threejs-vite`). A field note in the
shared knowledge base can hand you the working versions, the route and the gotchas before you touch
anything. See the **share-field-notes** skill. Also read the repo's own `MODLOG.md` files if it has them.

## 1. Fingerprint it
```bash
wise scan .                       # a repo: stack, versions, entry points, hooks, analytics endpoint, audio, bundle size
wise scan https://example.com/    # a live page: the same, from what the browser is served
```
`wise` lives at `bin/wise` in a clone; plugin installs put it on PATH. `wise scan` reads only. It prints an engine
key that the knowledge base uses: `threejs-vite`, `phaser`, `pixi`, `babylon`, `playcanvas`, `unity-webgl`,
`godot-web`, `construct`, `canvas-2d` or `unknown`.

The scan can't see everything, so check these by hand:
- **A live URL without source:** the bundle is minified. You can read hooks and network calls, not design
  intent. Ask for the repo.
- **Several entry points:** a landing page, a play page and prototype paths are common. Note each one.
- **Hooks that exist only in dev builds:** open the built page and check `window.__game` there too.

## 2. Read the source of truth
Open the files the scan names and write exact names into the plan. Don't guess how the game behaves.

| Question | What to find | Why it matters |
|---|---|---|
| The core loop | the run object, the wave loop, the single damage entry point, the reward path | every feature hangs off these; one damage entry point means one place to hook |
| Save format | the storage key, a version field, migrations, snapshot and restore of a run | a feature that works on a fresh profile can still break a returning player |
| Grants | what pays once (ranks, pass, dailies) and what key it uses | a restored run that keeps its old id can be paid twice for the same waves |
| Analytics | the endpoint (`/api/events`), batching, event names, the version or release field | QA must block it; a release must tag it |
| Debug and mod hooks | `window.__game` (time step, spawn, set state), a mod loader (`registerMod`), the event bus | this is how bots, takes and tests drive the build |
| Tests | the runner (`node --test`), what is covered, how long it takes | the gate for every change |
| Tuning tables | where numbers live (`ramp.js`, `first-siege.js`, `boss-tiers.js`) and who owns them | balance changes data, not code |
| Audio | the bus graph, how sounds load, the first-gesture start | the mix and the load order depend on it |
| Deploy | the build command, a prepare step (redirects, cache headers), the host and project | a release repeats exactly this |

## 3. Take the baseline (before you change anything)
A later "it got slower" or "it got harder" needs a before.
- **Performance:** fps and p95 frame time at the stress counts and in one real late-stage fight (the
  **game-performance** skill). Note the machine and that it was on mains power.
- **Browser:** `wise qa <url>` in Chromium 390×844, WebKit 390×844 and Chromium 320×568. Record errors and
  overflow as they are today (the **browser-qa** skill).
- **Balance:** if the repo has sim bots, run them and keep the table (the **game-economy** skill).
- **Size and load:** bundle size from the scan; time to first screen if load is in scope.

## 4. Decide
- **Route:** data or tuning > mod hook > engine code > UI only > a new prototype path. Pick the first that
  reaches the producer's idea.
- **Risk:** what could break a returning player (save shape, grants), and what test will catch it.
- **Owners:** if the work will be split, which files belong to which owner (the **agent-orchestration**
  skill).

## 5. Write GAME_PLAN.md
```markdown
# <Game> plan
- Repo: <path or URL>, branch <x> @ <commit>; live: <URL>, version <x>
- Stack: <engine key + versions> (e.g. threejs-vite: three 0.180, Vite 7), language, test runner
- Entry points: <files / paths>; build: <command>; deploy: <host, prepare step>
- Core loop: <run object, wave loop, damage entry point, reward path: file and function names>
- Save: key <x>, version <n>, migrations <where>, run snapshot/restore <where>; grant keys <list>
- Analytics: endpoint <x>, events <list>, release field <name>
- Hooks: window.__game <list>; mod loader / event bus <how>
- Tuning tables: <files>, owner <who>
- Baseline: tests <n pass>; QA errors <n>, overflow <yes/no> per browser; fps <table>; bots <table>; bundle <KB>
- Chosen route for "<idea>": <route> because <reason>
- Lab plan: branch <x>, save key <x>, debug spawn <how>
- Unknowns to resolve first: <list>
```
Then continue with the **make-web-game** loop (lab → source of truth → vertical slice).

## Traps
- **Reading the data and not the code.** A table can hold a value the code never reaches. On one build a
  double-size boss had correct stats and never hit the wall: collision held it farther out than its reach.
  Check behaviour in the running build.
- **Skipping the old-save check.** List the save versions in the wild and keep one fixture of each.
- **No baseline.** Without a before, every later number is an argument.
