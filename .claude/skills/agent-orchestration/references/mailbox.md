# Mailbox flow between sessions

Agents in one session can message each other directly. Agents in different sessions, accounts or machines
can't. A shared mailbox can: a tool that stores messages on disk, survives restarts, and offers dispatch,
wait and acknowledge. Any agent-orchestration tool with those three verbs works.

## The flow
```
Producer ⇄ Lead (one mailbox for the run) ⇄ Workers (one dispatched task each)
```
1. **The lead dispatches** a self-contained spec (target, change, constraints, ownership, acceptance) into
   the worker's terminal. The tool adds a preamble with the task and dispatch IDs. That preamble is the
   worker's authority.
2. **The worker works** only in the worktree the spec names. For a truly blocking question it uses the
   tool's ask command, which waits for the lead's reply. Otherwise it picks a default.
3. **The worker finishes** with exactly one "done" message (outcome succeeded or failed, commit hashes, a
   three-sentence summary), then goes idle.
4. **The lead waits** on the mailbox in the background, answers questions, processes each delivery and then
   acknowledges it.
5. **The lead merges** the worker's branch into `rc/next`, runs tests and the browser gate, deploys, and
   fast-forwards the game branch. Workers never merge, push or deploy.

## Heartbeats
**Turn heartbeats off.** Routine "alive" messages pop into the lead's terminal and burn context. Ask workers
for milestone notes, questions, blockers and `worker_done` only. If the system still sends them,
auto-acknowledge heartbeat-only deliveries in a background loop.

A milestone note says what changed for the player and where to see it. "Still working" is not a milestone.

## Example: Orca
This section is about one specific tool. Other tools have the same verbs under other names.
- dispatch:
  `orca orchestration worker-start --terminal <handle> --worktree path:<dir> --task-title … --spec …`
- wait:
  `orca orchestration check --wait --types "worker_done,escalation,question,status" --timeout-ms 900000 --json`
- reply to questions with `reply --id`, acknowledge with `check --ack <deliveryId>`, and keep the worker's
  terminal (retain, don't release).
- who is doing what: `worker-list --run <run> --json`; one worker: `worker-show --dispatch <id> --json`.
- mail a worker mid-task: `send --to dispatch:<id> --subject … --body …`. The worker checks for follow-ups
  at its checkpoints.

## Things that went wrong
| Symptom | Cause | Fix |
|---|---|---|
| The lead's context fills with "alive" messages | heartbeats on | milestones only; auto-acknowledge the rest |
| A worker refuses a relayed instruction to use the user's browser or accounts | it can't tell a relayed message from the user | the user says it in that worker's terminal |
| A worker's log entries carry a version already released | the lead shipped from another branch meanwhile | the lead owns versions; workers title entries by date and topic |
| A worker vanishes mid-task | its session lost access | commit each working step; the lead re-dispatches from the last commit |
| Two workers' servers collide | shared ports | a port range per worker in the spec; stop servers at the end |
