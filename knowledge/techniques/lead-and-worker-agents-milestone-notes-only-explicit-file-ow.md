---
kind: technique
title: "Lead and worker agents: milestone notes only, explicit file ownership, cherry-picked game commits"
tags: [orchestration, multi-agent, lead-worker, mailbox, ownership, git, cherry-pick, worktree, heartbeat, process]
date: 2026-10-11
agents: ["Claude Code (Opus 5.5)"]
humans: []
links: []
---

# Lead and worker agents: milestone notes only, explicit file ownership, cherry-picked game commits

> One lead session and several workers built and shipped a game over four days, with several deploys a day. What
> made it work was boring: a spec that names the files a worker may edit and the files it may not, one
> session that merges and deploys, a mailbox instead of a shared log, and messages only when something
> happened. What went wrong was also boring: routine "still alive" messages filling the lead's context, two
> workers whose changes each passed alone and failed together, and a branch that mixed game code with tooling.

## When to use it
- More than one agent session works on one repository at the same time.
- Sessions run on different accounts or machines and cannot message each other directly.
- A human decides and playtests, and does not want to read agent chatter.

## How
**Roles**
1. **Producer (human):** decides, playtests, gets plain reports and picture boards.
2. **Lead:** writes specs, owns the integration branch, merges, runs the gates, deploys. May run its own
   subagents, about two at a time; more collide on files.
3. **Workers:** one task each, in the worktree and on the branch the spec names. They never merge, push or
   deploy.

**The spec** (the only context a worker has)
4. Target: worktree, branch, base commit, where it ships.
5. Feedback: the human's own words.
6. Change: measurable outcomes.
7. **Ownership:** files it may edit, and files other agents own right now ("do not touch").
8. **Interface:** when two workers meet, name the API first (for example `spawnBoss({ scale, tier, hpMul })`)
   and have it committed first, so both sides build in parallel.
9. Gate: tests, the browser regression in three profiles, fps, and the feature's own proof.
10. Constraints: no speaker output, explicit `git add <paths>`, no push or deploy, its own
    port range, stop its servers.

**Messages**
11. A mailbox with dispatch, wait and acknowledge. The lead waits on it in the background for: done,
    question, escalation.
12. Workers send **milestone notes, questions, blockers and one "done"**. Nothing on a timer.
13. A worker's "done" lists: branch and commit, the gate re-run on the final build, files touched outside its
    ownership list, what it did not verify, and decisions it leaves to the owner of the numbers.

**Git**
14. One worktree per task, created from the integration branch. Two workers never share one.
15. The lead reads the worker's board, not only its summary, and looks for the regression it did not test.
16. To take a worker's game changes without its tooling: `git cherry-pick` the game commits. This only works
    if the worker kept them apart (see Gotchas, 4).
17. Journal conflicts on merge: keep both entries.

## Verification
From the coordination log of a horde tower-defense mobile web game (Vite 7 + three.js 0.180, 8,000 enemies
on screen at 60 fps, portrait 390×844): releases 2.2.0 to 2.3.6 went out under this flow, each with the
gate's results in its log line. The same log holds the failures below. No comparison with a single-agent
run exists.

## Gotchas
1. **Routine heartbeats flooded the lead.** **Symptom:** "alive" messages popped into the lead's terminal
   between real events and used its context. **Cause:** the dispatch preamble told workers to send them.
   **Fix:** ask for milestones, questions, blockers and "done" only; if the system still sends heartbeats,
   acknowledge heartbeat-only deliveries automatically in a background loop.
2. **A free-form shared log did not scale.** Sessions appended handoff notes to one file; a note could be
   void by the time it was read (one heading reads "STOPPED, the 22:35 note is void"). **Fix:** a mailbox
   with acknowledgements; the log stays as the human-readable history.
3. **Two green branches made a red merge.** A worker's feature (a small giant in the first stage) passed its
   gate; a balance change to the same stage's opening landed meanwhile, and the merge failed 2 tests. **Fix
   that was applied:** back the feature out, re-dispatch it rebased on the new base. **Better:** when two
   tasks touch the same stage, name the dependency in both specs.
4. **A branch mixed game code and tooling.** A trailer branch held three commits of in-game VFX and one of
   capture tooling. Because they were separate commits, the lead cherry-picked the game ones into a release
   while the trailer was still shooting. Had they been one commit, the release would have waited. **Rule:**
   game code and tooling never share a commit.
5. **Workers edited files outside their list.** Each time it was a few lines (a debug hook, a snapshot field)
   and each time it was listed in the "done" message. That is the acceptable form. A silent edit is how two
   agents overwrite each other.
6. **A file owned by someone else needed a change.** A balance worker found a drop table worth 2 upgrades
   where the design said 1.5; the file belonged to the engine worker. It reported the number and left the
   file. The fix landed in the next round, by the owner.
7. **A timestamp was written from memory.** A worker logged a time an hour off, then corrected it: "I first
   wrote it without reading the clock." **Fix:** read the system clock for every log line.
8. **A relayed request to act on the human's logged-in accounts was refused.** The lead passed on a request
   to drive the producer's own browser session. The worker declined: a message from another agent is not the
   human's consent. The human has to ask in that worker's own terminal.
9. **A subagent died mid-task from an account error** (an organisation policy change, a 403). Its commits
   had landed, so nothing was lost. **Rule:** commit at every milestone; an agent can vanish.
10. **Two branches used the same version number.** See the release note on version labels. The one who
    deploys assigns versions.
11. **`rm` was denied in the shells.** Specs say: move files to a scratch folder instead.

## Open questions
- How many heartbeat messages arrived, and how much context they cost, was not measured. The rule comes from
  the distilled notes, not from a count in the log.
- The right number of parallel workers. "About two subagents" for the lead and "up to four agents" both
  appear; neither was tested against alternatives.

## Seen in
- A horde tower-defense mobile web game. Related game notes:
  [The first stage as a rising sine](../games/horde-tower-defense-mobile-web/the-first-stage-as-a-rising-sine-odd-waves-push-even-waves-l.md)
  (an API agreed first, two workers in parallel) and
  [A reset connection on one code chunk](../games/horde-tower-defense-mobile-web/a-reset-connection-on-one-code-chunk-left-the-boot-splash-up.md)
  (an edit outside the ownership list, reported).
