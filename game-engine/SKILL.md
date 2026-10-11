---
name: game-engine
description: End-to-end studio workflow for building, balancing, polishing and shipping a mobile-first web game (Vite + three.js or similar) with Claude Code agents. It covers the concept, vertical slices in the Universal Modder style, economy and difficulty tuned with simulated player bots, a clean mobile UI kit (hub, wordless tutorial, fonts, EN/ES), game feel and audio mix, performance budgets, real-browser QA, Vercel releases with frozen versions, lead/worker agent orchestration, the trailer pipeline, and design boards with mockups. Use this skill whenever the user is making or iterating a web or HTML5 game, especially a tower defense, idle, roguelite, horde or casual mobile game: designing chapters, stages, bosses or a monetization system; rebalancing ("too easy", "too hard", "boring first minutes"); fixing lag; polishing UI, FTUE, sound or VFX; preparing a release; or cutting a trailer, even if they never say "engine" or "skill".
---

# Game Engine: how we build and ship web games

This is the playbook distilled from shipping *Zombie Tower: Short Sieges* (v1 → 2.3.x) with a producer, a lead Claude session and worker agents. It's opinionated because each rule here was paid for by a real mistake. Read this file, then open only the reference you need.

## The producer contract (read first)
The person you work with is a **producer**, not a reviewer of question sheets.
- **Build, don't ask.** Pick sensible defaults, build to ready-to-play, and show screenshots or a board. List the defaults as easy-to-change notes. Ask only when a choice is truly irreversible or outward-facing.
- **Ship when green.** When tests, browser QA and fps pass, deploy, then send the link and the board. "Ship — why ask."
- **A question is not a go.** "What about X?" means report the status and offer; don't start or take over work.
- **Use the whole time budget.** Re-task agents that finish early instead of stopping halfway.
- **Plain language.** No jargon in reports; say what changed for the *player*. Keep chat posts short and simple, because the team may not be native English speakers. Offer Spanish when relevant.
- **Never publish anywhere without being asked:** no public pages, no Slack posts, no claude.ai artifacts. Show work locally (open the file in QuickTime, Preview or Finder) or on a host the user names (GitHub, Vercel).

## The pipeline
Work moves through these stages. Each one has a reference with the details and the traps.

| # | Stage | What "done" means | Reference |
|---|---|---|---|
| 1 | **Concept and slice:** Universal Modder loop: recon → route → lab → vertical slice → in-game verify → showcase → publish check | A playable slice in the real build, a MODLOG entry, a showcase take | `references/um-loop.md` |
| 2 | **Systems and economy:** stages, waves, bosses, currencies, sinks | Sim bots meet the targets per player model; browser runs agree with the sim | `references/economy-balance.md` |
| 3 | **UI kit:** hub, battle HUD, wordless tutorial, fonts, i18n | One golden call to action, a ≤ 1-row battle bar, works at 320 px, EN and ES | `references/ui-kit.md` |
| 4 | **Game feel and audio:** juice, bosses you *feel*, the mix | Every tap, window and claim has motion and sound; mix measured, not guessed | `references/feel-audio.md` |
| 5 | **Performance** | 60 fps at the stress count and in **real late-stage play**; adaptive quality that recovers | `references/performance.md` |
| 6 | **QA:** muted real browsers, bots that tap like players | `errors []` in Chromium, WebKit and 320 px; no overflow; first session proven in the browser | `references/qa.md` |
| 7 | **Release** | Version bump, prebuilt deploy, live asset checks, tag, frozen older version on its own URL | `references/release.md` |
| 8 | **Orchestration:** lead and workers in parallel | Specs with ownership; merges only by the lead; no heartbeat spam | `references/orchestration.md` |
| 9 | **Trailer** | A hook in 3 s, the loop by 8 s, a hero finale, 120 fps slow motion, an SFX mix at about -15 LUFS | `references/trailer.md` |
| 10 | **Design boards and new features** | HTML mockups rendered to PNG at phone size, plus a DESIGN.md with defaults and a build estimate | `references/design-boards.md` |

## Golden rules (the ones that hurt most when skipped)
1. **Tune enemy COUNT and pressure shape, not just HP.** Players feel "a thousand of them keep coming", not a bigger number. Give crowds an answer (pierce, splash) and gate the opening by *hits to kill*, so the first upgrade matters.
2. **Simulators lie about first sessions.** Bots buy walls; real new players tap Attack cards. Always prove the first 3 minutes with a real-browser bot that taps the actual UI (`scripts/qa/browser-qa.template.mjs`).
3. **Shape the curve:** a rising sine. Odd waves push, even waves let you spend; mini-boss mid-stage, a big boss at the end, and the last stage of a chapter is the hardest. A finale easier than stage 5 is a bug.
4. **Bosses must be felt:** entrance (shake and boom), walk in from the field edge (never spawn next to the base), a slam that hits the base, a real death (stagger, collapse, slow motion), a tappable drop. Taps must not delete bosses: give boss taps a damage multiplier or an armour phase.
5. **Gifts and rescues only after a fall.** Free help for a player who never died makes the game boring.
6. **Measure audio, never play it aloud from the agent.** Music about -20 LUFS short-term in battle; no SFX more than about 6 dB over the music; rate-limit stacked booms. The producer listens; the agent measures.
7. **Adaptive quality must recover.** A guard that degrades but can't step back up on a 60 Hz screen turns stage 7 into a slideshow.
8. **One idea per screen.** Hubs get rails for the important features (events, daily login, pass, vault, race), but only one glowing call to action at a time.
9. **Every report starts with what changed for the player,** then where to see it (paths, screenshots), then what's still open.

## Default stack and conventions
- Vite + three.js, mobile portrait first (390×844 baseline; 320×568 is the small-phone check), deployed on Vercel from a prebuilt `dist`.
- Fonts (Google Fonts, OFL): **Lilita One** for display and buttons, **DM Sans** for body, **Silkscreen** for the pixel chat log and tiny HUD labels.
- Data-driven tuning: every number lives in a named constant or table (`ramp.js`, `first-siege.js`, `boss-tiers.js`), so the balance owner changes data and not code.
- Every feature ships with a test (`node --test`) for its rule (grants once, survives reload, its spawn reaches the wall, and so on).
- `window.__game` exposes debug hooks for QA (time step, spawn boss or carrier, set state). Previews and debug never grant real rewards.
- Analytics: batch events to `/api/events`. In every automated browser run, intercept `**/api/events` with a 204.

## How to start a request
1. Find the matching stage(s) in the table and read those reference files.
2. If the work is big, split it into **owners** with disjoint files (`references/orchestration.md` has the spec template in `assets/spec-template.md`).
3. Build, then prove it with the stage's "done" criteria, then show a board (`scripts/render-board.mjs`), then ship or hand back with the open list.
