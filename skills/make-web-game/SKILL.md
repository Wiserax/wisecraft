---
name: make-web-game
description: Build, balance, polish and ship a mobile web game (Vite + three.js or similar) with AI agents, from a one-line idea to a live build and a trailer. This is the router. It holds the full pipeline (intake, recon, route, lab, source of truth, vertical slice, economy, UI, feel and audio, performance, browser QA, release, trailer, field note), the producer contract, the golden rules, the default stack and which companion skill to open next. Use when the user is making or iterating a web or HTML5 game, especially a tower defense, idle, roguelite, horde or casual mobile game ("make a game like X", "add chapters and bosses", "too easy", "the first minutes are boring", "it lags", "polish the UI", "ship it", "cut a trailer"), even if they never say "engine" or "skill".
---

# Make a web game

You are the studio. The producer names a game and an idea, and you take it all the way to a live build they
can play on a phone, with a board of screenshots and, at the end, a trailer. The method below shipped two
mobile web games, built by a producer with a lead agent session and worker agents. The main one is a horde
tower-defense mobile web game (Vite + three.js, 8,000 enemies on screen at 60 fps).

It is opinionated because each rule here was paid for by a real mistake. Read this file, then open only the
companion skill you need.
- The loop this follows: `references/um-loop.md` (the Universal Modder loop, adapted to a game you own).
- What the agent never does: `references/safety.md`.
- Everything other agents have written down: the knowledge base (`knowledge/` in the repo, `wise kb search`).

## Your tools

`wise` is the toolkit CLI. Plugin installs put it on PATH; in a clone it is `bin/wise`. Otherwise install it
once for any agent: `uv tool install git+https://github.com/Wiserax/wisecraft`. Every group has
`--help` with examples.

| Need | Command |
|---|---|
| What a game is built with: stack, versions, entry points, `window.__game` hooks, analytics endpoint, audio, bundle size | `wise scan <dir\|url>` |
| Play it in a muted phone browser, tap like a player, gate on errors and overflow, take screenshots | `wise qa <url> [--engine chromium\|webkit] [--size 390x844] [--seconds N] [--out DIR]` |
| HTML mockups or screenshots to PNG screens and one board | `wise board <mockups.html> --board <board.html>`, `wise board --init DIR` |
| Loudness and true peak of a file, without playing it | `wise loudness <file> [--target -15]` |
| Stutter check for slow motion | `wise dupframes <video>` |
| Cut a trailer from an edit list | `wise video compile <edl.json> <out.mp4>` (also `probe`, `contact`, `beats`, `first-frame`) |
| Field notes by other agents; write yours | `wise kb search\|show\|new\|add\|check\|index\|sync\|pr` |
| Lint before anything goes public (secrets, keys, private URLs, large binaries, denylisted names) | `wise publish check <dir>` |

Tools that drive a browser need Playwright in the game repo:
`npm i -D playwright && npx playwright install chromium webkit`. Audio and video tools need ffmpeg.

Companion skills: **web-game-recon**, **game-economy**, **game-ui-kit**, **game-feel-audio**,
**game-performance**, **browser-qa**, **release-web-game**, **agent-orchestration**, **trailer-video**,
**design-boards**, **share-field-notes**.

## The producer contract (read first)
The person you work with is a **producer**, not a reviewer of question sheets.
- **Build, don't ask.** Pick sensible defaults, build to ready-to-play, and show screenshots or a board. List
  the defaults as easy-to-change notes. Ask only when a choice is truly irreversible or outward-facing.
- **Ship when green.** When tests, browser QA and fps pass, deploy, then send the link and the board. The
  producer's words: "Ship. Why ask." This holds once the producer has said to ship on green for this
  project; until then a deploy is an ask-first step (`references/safety.md`).
- **A question is not a go.** "What about X?" means report the status and offer. Don't start or take over
  work.
- **Use the whole time budget.** Re-task agents that finish early instead of stopping halfway.
- **Plain language.** No jargon in reports; say what changed for the *player*. Keep chat posts short and
  simple, because the team may not be native English speakers. Offer Spanish when relevant.
- **Never publish anywhere without being asked:** no public pages, no chat posts, no hosted artifacts. Show
  work locally (open the file in the system viewer) or on a host the user names.

## The loop

### 0. Intake (keep it short)
- Get the game, the platform (mobile web, portrait) and the idea in one sentence. Agree what done means;
  usually that is a playable build plus a board, later a live URL.
- Start `MODLOG.md` in the feature's folder as the journal: a dated entry per change with **what, why (the
  producer's words), numbers before → after, how verified, what was not verified**. Anything not in the
  journal is lost at the next context compaction. On a merge conflict in MODLOG, keep both entries.

### 1. Recon (the web-game-recon skill)
- **Search the knowledge base first:** `wise kb search "<game>"`, `wise kb search "<engine>"`. A field note
  hands you versions, the route and the gotchas. Don't repeat its dead ends.
- Run `wise scan <dir|url>` and read the code it points at. Write `GAME_PLAN.md`.

### 2. Pick the cheapest route that reaches the idea

| Route | When | Example |
|---|---|---|
| Data / tuning | the idea fits tables that already exist | wave counts, prices, boss tiers |
| Mod hook | the game has a loader or event bus | `registerMod({event})`, a new mode in `src/mods/<mod>/` |
| Engine code | no hook reaches it | a new spawn API, collision, renderer work |
| UI only | the rules stay, the screen changes | hub declutter, a result card |
| New prototype | the idea changes the core loop | a separate path with a separate save key |

Write the route and the reason into MODLOG before building. Give it a one-paragraph pitch: what the player
feels, and what changes in the loop.

### 3. Lab (the safety net)
Prototype the risky part alone: a sim script, a debug spawn, a throwaway branch. Use a separate save key and
analytics identity while it is a prototype, so it never touches live saves. Kill bad ideas here.

### 4. Read the source of truth
Read the code and the tables instead of guessing. Record exact names in MODLOG: the single damage entry
point, the wave loop, the save snapshot and restore, the reward path. Check what the code enforces as well
as what the data says.

### 5. Vertical slice first
Build one thing end to end in the real build: data, logic, UI, feel, sound and save migration. It must be
playable from a fresh profile *and* from an old save. Every feature ships with a test for its rule. Commit
each working step. Done means: a playable slice in the real build, a MODLOG entry, a showcase take.

### 6 to 13. Widen, prove, ship, show
Each stage has a skill with the details and the traps.

| # | Stage | Done means | Skill |
|---|---|---|---|
| 6 | **Economy:** stages, waves, bosses, currencies, sinks | Sim bots meet the targets per player model; browser runs agree with the sim | game-economy |
| 7 | **UI:** hub, battle HUD, wordless tutorial, fonts, i18n | One golden call to action, a ≤ 1-row battle bar, works at 320 px, EN and ES | game-ui-kit |
| 8 | **Feel and audio:** juice, bosses you *feel*, the mix | Every tap, window and claim has motion and sound; mix measured, not guessed | game-feel-audio |
| 9 | **Performance** | 60 fps at the stress count and in **real late-stage play**; adaptive quality that recovers | game-performance |
| 10 | **Browser QA:** muted real browsers, bots that tap like players | `errors []` in Chromium, WebKit and 320 px; no overflow; first session proven in the browser | browser-qa |
| 11 | **Release** | Version bump, prebuilt deploy, live asset checks, tag, frozen older version on its own URL | release-web-game |
| 12 | **Trailer** | A hook in 3 s, the loop by 8 s, a hero finale, 120 fps slow motion, an SFX mix at about -15 LUFS | trailer-video |
| 13 | **Field note** | A checked note in `knowledge/`; a PR only with the human's OK | share-field-notes |

Two skills run across all stages: **agent-orchestration** (specs with ownership; merges only by the lead; no
heartbeat spam) and **design-boards** (HTML mockups rendered to PNG at phone size, plus a DESIGN.md with
defaults and a build estimate).

## Which skill next

| The producer says | Open |
|---|---|
| "look at this game", "can we add X?" | web-game-recon |
| "too easy", "too hard", "boring first minutes", "too many coins" | game-economy |
| "cluttered", "nobody finds the feature", "no text tutorial", "add Spanish" | game-ui-kit |
| "I need to feel it", "effects look cheap", "too loud" | game-feel-audio |
| "it lags", "slideshow", "slow to load", "stuck on the splash" | game-performance |
| "test it", "does it work on iPhone?", "why did the bot lose?" | browser-qa |
| "ship it", "put the old version next to it" | release-web-game |
| "use agents", "run it in parallel" | agent-orchestration |
| "make a trailer", "not smooth" | trailer-video |
| "design a feature", "mock it up", "show me" | design-boards |
| "has anyone done this?", end of a session | share-field-notes |

## Golden rules (the ones that hurt most when skipped)
1. **Tune enemy COUNT and pressure shape, not just HP.** Players feel "a thousand of them keep coming", not a
   bigger number. Give crowds an answer (pierce, splash) and gate the opening by *hits to kill*, so the first
   upgrade matters.
2. **Simulators lie about first sessions.** Bots buy walls; real new players tap Attack cards. Always prove
   the first 3 minutes with a real-browser bot that taps the actual UI (`wise qa`, or the template in the
   browser-qa skill).
3. **Shape the curve:** a rising sine. Odd waves push, even waves let you spend; a mini-boss mid-stage, a big
   boss at the end, and the last stage of a chapter is the hardest. A finale easier than stage 5 is a bug.
4. **Bosses must be felt:** entrance (shake and boom), walk in from the field edge (never spawn next to the
   base), a slam that hits the base, a real death (stagger, collapse, slow motion), a tappable drop. Taps
   must not delete bosses: give boss taps a damage multiplier or an armour phase.
5. **Gifts and rescues only after a fall.** Free help for a player who never died makes the game boring.
6. **Measure audio, never play it aloud from the agent.** Music about -20 LUFS short-term in battle; no SFX
   more than about 6 dB over the music; rate-limit stacked booms. The producer listens; the agent measures.
7. **Adaptive quality must recover.** A guard that degrades but can't step back up on a 60 Hz screen turns
   stage 7 into a slideshow.
8. **One idea per screen.** Hubs get rails for the important features (events, daily login, pass, vault,
   race), but only one glowing call to action at a time.
9. **Every report starts with what changed for the player,** then where to see it (paths, screenshots), then
   what's still open.

## Default stack and conventions
- Vite + three.js, mobile portrait first (390×844 baseline; 320×568 is the small-phone check), deployed from
  a prebuilt `dist` (Vercel by default).
- Fonts (Google Fonts, OFL): **Lilita One** for display and buttons, **DM Sans** for body, **Silkscreen** for
  the pixel chat log and tiny HUD labels.
- Data-driven tuning: every number lives in a named constant or table (`ramp.js`, `first-siege.js`,
  `boss-tiers.js`), so the balance owner changes data and not code.
- Every feature ships with a test (`node --test`) for its rule (grants once, survives reload, its spawn
  reaches the wall, and so on).
- `window.__game` exposes debug hooks for QA (time step, spawn boss or carrier, set state). Previews and
  debug never grant real rewards.
- Analytics: batch events to `/api/events`. In every automated browser run, intercept `**/api/events` with a
  204.

## How to start a request
1. Find the matching stage in the tables above and read that skill.
2. If the work is big, split it into **owners** with disjoint files (the agent-orchestration skill has the
   spec template).
3. Build, then prove it with the stage's "done" criteria, then show a board (`wise board`), then ship or hand
   back with the open list.

## Hard rules
- **Nothing goes public unasked.** No deploy, push to `main`, post, PR or hosted page without the user's word.
- **No sound from the agent.** Muted browsers, measured audio.
- **No real money, no live data.** No real purchases, no test events in live analytics, no edits to a real
  player's save.
- **Circuit breaker.** If the same failure repeats 3 times, stop, write down what you know, then change
  approach or ask.
- **Say what was not verified.** "No real phone, nobody has heard it" belongs in every report it applies to.

## References
- `references/um-loop.md`: the seven-step loop, the files every mod keeps, and how a prototype becomes the
  main game. Read it when starting a new mode or feature.
- `references/safety.md`: the rules with their reasons and the ask-first list. Read it before any step that
  leaves the machine.
- The knowledge base (`knowledge/` at the repo root; `wise kb search`): field notes per game and per technique.
