---
name: agent-orchestration
description: Run a lead agent and worker agents in parallel on one game without collisions. Covers roles (producer, lead, workers), task specs with file ownership and a measurable gate (template in assets/), one writer per file, worktrees and branches, mailbox flow with milestone notes instead of heartbeats, explicit `git add` paths, cherry-picking game commits out of a tooling or trailer branch, merges only by the lead, time budgets and re-tasking, and what a worker's final report contains (what changed for the player first). Use when the work is big enough to split, when the user says "use agents", "run this in parallel", "give this to a worker", "who owns this file", "merge the worker's branch", or when writing or receiving a task spec.
---

# Agent orchestration (lead + workers)

Parallel agents are fast until two of them edit the same file. The whole method is: one owner per file,
written down before work starts; one agent that merges; reports a producer can read.

## Roles
- **Producer:** decides and playtests. Gets plain-language reports and boards. Wants finished features with
  screenshots, not question sheets.
- **Lead:** writes specs, owns `rc/next`, merges, runs QA and deploys. It can run its own subagents. Keep
  about 2 at a time; more costs context and collides on files.
- **Workers:** each works in the worktree its spec names, on its own branch. Workers never merge, push or
  deploy.

## The spec
Use `assets/spec-template.md`. The parts that matter:
- **TARGET:** the worktree, branch, base commit, and where it ships. Plus the time budget.
- **FEEDBACK:** the producer's own words. The worker should solve the complaint, not the lead's reading of
  it.
- **CHANGE:** concrete, measurable outcomes.
- **OWNERSHIP:** the files it may edit, and the files other agents own right now ("don't touch").
- **INTERFACE:** if two workers meet, name the API (`spawnBoss({scale, tier, hpMul})`) so both can build in
  parallel.
- **GATE:** tests, QA in 3 browsers/sizes, fps, and the feature's own proof.
- **CONSTRAINTS:** no speaker output, analytics 204, explicit adds, no push/merge/deploy, no `rm` (move
  files), its own port range, stop servers.
- **PRODUCER UPDATES:** a plain note at each milestone; a "What changed in the game" section first in the
  final report.

A spec is self-contained. The worker has none of the lead's context: if the spec doesn't say it, the worker
doesn't know it.

## One writer per file
- One worktree per task, created by the lead from `rc/next`. Two workers never share a worktree.
- Ownership is by file or folder, never by "area". Two specs that both say "the hub" will collide.
- Typical split that held: tuning (data files and the sim, no UI) · engine (spawn, collision, renderer) ·
  UI (hub, HUD, tutorial) · feel and audio · tooling and trailer.
- A worker that must touch a file outside its list keeps the edit minimal and lists it in the report
  ("two lines in the app file: the presenter and the flag"). The lead then knows where to look for a
  conflict.
- A shared log (MODLOG) is the one file everyone appends to. On conflict keep both entries.

## The lead's loop
Dispatch → wait on the mailbox (in the background) → merge → gate → deploy → board and link to the producer
→ re-task.
- **Before merging, read the worker's board, not just its summary.** Look for the regression it didn't
  test.
- **Only the lead merges.** It runs the full gate on the merged result, not on each branch alone.
- **Time budgets.** Every spec has one. When an agent finishes early, give it the next most valuable task
  inside the budget instead of stopping halfway.
- **The lead owns version numbers and tuning numbers.** A worker that fixes a bug which shifts balance
  ships the fix at its weakest setting, reports the bot table before and after, and names the levers; the
  lead or the balance owner turns them.

## Git rules
- **Explicit `git add <paths>` only.** Never `git add .` or `-A`: capture output and other agents'
  half-finished files end up in the commit.
- **Commit each working step.** A worker session can die mid-task (one was cut off by an account error).
  Its committed rounds had landed; anything uncommitted would have been lost.
- **Cherry-pick game commits out of a mixed branch.** A trailer or tooling branch often carries a game fix
  the release needs. Keep game code and tooling in separate commits from the start, say in the report which
  commits are which, and the lead brings in the game ones with `git cherry-pick`. A VFX upgrade shipped
  that way while the trailer on the same branch was still shooting.
- **A trailer branch is frozen at a build.** Later merges into the release branch must not change what is
  being filmed.
- Never push the repository's `main` without explicit permission. Commit messages end with the session's
  Co-Authored-By line. No `rm`: move files to a scratch folder.

## Messaging
If workers run on another account or machine, use a shared mailbox: any agent-orchestration tool with
dispatch, wait and acknowledge. `references/mailbox.md` has the flow and a worked example with one tool.
- **Milestone notes, not heartbeats.** Routine "alive" messages pop into the lead's terminal and burn
  context. Ask workers for milestone notes, questions, blockers and the final report only.
- **A question blocks; a default doesn't.** The producer forbids question sheets, so a worker picks a
  default, notes it, and asks only when a choice can't be undone.
- A worker may refuse actions on the user's own logged-in accounts (e.g. driving the user's browser) based
  on a relayed message. The user must say it in that worker's terminal.

## A worker's final report
In this order:
1. **What changed in the game,** for the player, in plain language. No file names here.
2. **Where to see it:** the board, screenshots, previews, paths.
3. **Branch and commits:** which are game code and which are tooling; "not merged, not pushed, not
   deployed".
4. **Gate on the final commit:** tests, QA in the three browsers/sizes, fps, the feature's own proof. If a
   gate was measured on an earlier commit or couldn't be measured (the machine dropped to 30 fps on
   battery), say exactly that.
5. **Files touched outside the ownership list,** each with a reason.
6. **Not verified / open:** no real phone, nobody has heard it, what was not captured, and which lever would
   move an open number.

Exactly one final message per task, then go idle.

## Done means
- Every spec named its files; no two live specs shared one.
- Every merge was done by the lead after reading the board.
- The producer got one plain message per milestone and one final report per task.
- Nothing was pushed or deployed by a worker.

## References
- `assets/spec-template.md`: the task spec to fill in and dispatch.
- `references/mailbox.md`: the mailbox flow between sessions, turning heartbeats off, and example commands.
  Read it when workers run in another session, account or machine.
