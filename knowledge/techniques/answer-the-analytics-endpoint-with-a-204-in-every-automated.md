---
kind: technique
title: "Answer the analytics endpoint with a 204 in every automated browser run"
tags: [analytics, qa, playwright, harness, network-stub, test-hygiene, live-checks, localstorage, bots]
date: 2026-10-09
agents: ["Claude Code (Opus 5.5)"]
humans: []
links: []
---

# Answer the analytics endpoint with a 204 in every automated browser run

> Bots play a web game again and again: regressions, playtest models, perf runs, trailer takes, and the
> same checks again on the live URL after a deploy. Each run would send "session start", "first minute" and
> onboarding events as if a person had played. One line in the browser harness answers the game's own
> analytics request with an empty success, so the game behaves exactly as in production and nothing reaches
> the real endpoint. It belongs in the shared launch helper, so no script can forget it.

## When to use it
- Every automated browser run against a build that has analytics, local or live. Especially live.
- Any harness shared by several agents: put the stub where the browser context is created.
- Not for testing analytics itself; that needs its own mock that records what was sent.

## How
1. In the function that creates the browser context (Playwright), before any page opens:
   `await context.route("**/api/events", (r) => r.fulfill({ status: 204 }))`.
   At context level it covers every page and every reload of the run.
2. Use the same helper for every script: regression, playtest bots, perf, audio capture, trailer takes.
   The same helper also mutes audio and sets the phone viewport, so one import carries all three rules.
3. Put the rule in every worker's spec next to "no speaker output", so a worker that writes its own
   harness still does it.
4. For post-deploy checks, run the same harness against the live URL with the stub in place.
5. Tag real events with the game's version, so that if test traffic does leak it can be found and removed.

## Why a 204 and not a blocked request
What the client in this project does (`src/game/analytics.js`), which is typical:
- Events go into a queue that is saved to `localStorage`, at most 200 of them.
- A flush posts up to 25 at a time and removes them from the queue **only when the response is ok**.
- A failed or aborted request leaves them queued and saved.

| Stub | Queue after a flush | Console and network | Result |
|---|---|---|---|
| fulfil with 204 | drained, as in production | clean | the game is in its normal state |
| abort the request | keeps growing to its cap, saved with the profile | a failed request per flush | a harness that gates on errors goes red; saved profiles carry queued events |
| fulfil with 4xx or 5xx | same as abort | an error response per flush | same |
| no stub | drained | clean | test sessions in the real data |

The harness here counts any response of 400 or more, any console error and any page error as a failure, so
an abort or an error status would fail every run for a reason that is not a bug.

## Verification
On a horde tower-defense mobile web game (Vite 7 + three.js 0.180, 8,000 enemies on screen at 60 fps,
portrait 390×844): the rule is in the shared launch helper and is repeated in the coordination rules and in
worker specs from the first handoffs on. Run reports name it ("muted, events stubbed").

**Not verified:** nobody audited the analytics data for leaked bot sessions, so the sources cannot say
whether a leak ever happened or how large it was. The table's "abort" and "4xx" rows follow from reading the
client's flush code; they were not run.

## Gotchas
1. **One script without the stub is enough.** A throwaway probe written outside the shared helper sends real
   events. **Fix:** the stub lives in the launch helper, and new scripts import it; a spec constraint says so.
2. **The live URL is where it matters most.** Post-deploy QA and the first-stage bot run against production.
   Without the stub every release would add fake first sessions on the newest version.
3. **A saved profile can carry a queue.** Profiles exported from a run and seeded into later runs include
   whatever the analytics queue held. With a 204 the queue is empty at export. With a blocked request it is
   not, and the first un-stubbed load would send it. This follows from the client's code; it was not observed.
4. **Opting out is not the same test.** The client has an off switch that skips tracking entirely. A run
   with analytics off does not exercise the code path players run.
5. **Glob the path, not the host.** `**/api/events` matches the local server, a preview and production alike.
   A stub keyed on one host misses the others.
6. **Driving a human's logged-in analytics dashboard is a different matter.** Reading session data from the
   producer's own browser needs that person's go-ahead; a worker declined it when the request came through
   another agent.

## Open questions
- No automated check asserts that zero requests reached the real endpoint during a run. A counter in the
  route handler, printed with the run's report, would make the rule verifiable.
- Third-party analytics scripts loaded from another origin would need their own routes. Whether this build
  loads any was not checked for this note; the stub covers the game's own endpoint only.

## Seen in
- Every automated run of a horde tower-defense mobile web game. Related:
  `preview-deploys-sit-behind-sso-frozen-versions-get-their-own.md`,
  `lead-and-worker-agents-milestone-notes-only-explicit-file-ow.md`.
