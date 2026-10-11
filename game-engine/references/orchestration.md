# Orchestration (lead + workers)

## Roles
- **Producer:** decides and playtests. Gets plain-language reports and boards.
- **Lead session:** writes specs, owns `rc/next`, merges, runs QA and deploys. It can run its own subagents. Keep about 2 at a time; more costs context and collides on files.
- **Workers:** each works in the worktree its spec names, on its own branch. Workers never merge, push or deploy.

## Messaging between sessions
If workers run on another account or machine, use a mailbox, e.g. Orca orchestration:
- dispatch: `orca orchestration worker-start --terminal <handle> --worktree path:<dir> --task-title … --spec …`
- wait: `orca orchestration check --wait --types "worker_done,escalation,question,status" --timeout-ms 900000 --json`
- reply to questions with `reply --id`, acknowledge with `check --ack <deliveryId>`, and keep the worker's terminal (retain, don't release).
- **Turn heartbeats off.** Routine "alive" messages pop into the lead's terminal and burn context. Ask workers for milestone notes, questions, blockers and `worker_done` only. If the system still sends them, auto-acknowledge heartbeat-only deliveries in a background loop.
- A worker may refuse actions on the user's own logged-in accounts (e.g. driving the user's browser) based on a relayed message. The user must say it in that worker's terminal.

## Spec template
Use `assets/spec-template.md`. The parts that matter:
- **TARGET:** the worktree, branch, base commit, and where it ships.
- **FEEDBACK:** the producer's own words.
- **CHANGE:** concrete, measurable outcomes.
- **OWNERSHIP:** the files it may edit, and the files other agents own right now ("don't touch").
- **INTERFACE:** if two workers meet, name the API (`spawnBoss({scale, tier, hpMul})`) so both can build in parallel.
- **GATE:** tests, QA in 3 browsers/sizes, fps, and the feature's own proof.
- **CONSTRAINTS:** no speaker output, analytics 204, explicit adds, no push/merge/deploy, no `rm` (move files), its own port range, stop servers.
- **PRODUCER UPDATES:** a plain note at each milestone; a "What changed in the game" section first in the final report.

## The lead's loop
Dispatch → wait on the mailbox (in the background) → merge → gate → deploy → board and link to the producer → re-task. When an agent finishes early, give it the next most valuable task inside the time budget. Before merging, read its board, not just its summary. Look for the regression it didn't test.
