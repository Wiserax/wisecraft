TARGET: <one line: what and why>. Worktree <path>, branch <feat/x> from <base branch @ commit> (= <what's live>). Ships in <version/URL>. Budget about <N> min.

PRODUCER FEEDBACK (their words):
- "<quote>"

CHANGE (measurable):
1. <outcome + how it's proven>
2. ...

INTERFACE (if another agent builds against this): <function/flag/data contract>

OWNERSHIP: you may edit <files/dirs>. Don't touch <files owned by other agents right now> (<who/why>).

GATE: tests pass; browser QA errors [] in chromium 390, webkit 390, chromium 320x568; 60 fps at the stress count; <feature-specific proof>; a board at <path>.

CONSTRAINTS: no speaker output (Chromium --mute-audio, WebKit zero-gain); explicit git add only; commit trailer line; don't push, merge or deploy; no rm (move files); ports <range>; stop your servers.

PRODUCER UPDATES: post a plain-language note at each milestone (what changed for the player, where to see it). Start the final report with "What changed in the game". No routine heartbeats; send only milestones, questions, blockers and the final report.

FINAL REPORT (one message, then idle): 1) what changed in the game, for the player; 2) where to see it (board, paths); 3) branch and commits, saying which are game code and which are tooling; 4) the gate on the final commit, or exactly what could not be measured; 5) files touched outside OWNERSHIP, with reasons; 6) not verified / open.
