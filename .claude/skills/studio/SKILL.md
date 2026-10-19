---
name: studio
description: Open the live studio panel (`wise studio`) in a side browser pane, so the producer watches every agent at work and reviews what they make as it lands. It shows each Claude lead session and subagent, Orca terminal and Codex job with what it is doing right now, time, tokens and API-equivalent $, and a feed of new screenshots, videos and 3D models with 👍 / 👎 and notes. Use when the user asks to "show the panel", "visualize the agents", "show me the work", "a feed of screenshots", "let me review the assets", or wants to see agents and outputs live; also read reviews.jsonl before redoing an asset the producer has reviewed.
---

# Studio: the live panel beside the work

`wise studio` is a small local server (Python standard library and Pillow, 127.0.0.1 only) with one page built
for a narrow side pane, 360-480 px, dark. It is the live version of `/progress` (the `progress` skill) and
reuses its transcript parser, plus a feed of everything the agents render.

## 1. Launch it once (it is idempotent)
```
wise studio --open        # serves http://127.0.0.1:5480 and opens it in Orca's browser pane
```
- Run it in the background (it keeps serving). A second launch sees the running one, prints the URL and, with
  `--open`, only opens the tab.
- Without Orca it prints the URL; open it in any browser pane.
- `--hours 4` shortens the window (default 8). `--port` picks another port. `wise studio --print-config` lists
  the watched folders.
- Stop it by its PID (`lsof -nP -iTCP:5480 -sTCP:LISTEN`), never with a broad `pkill`.

## 2. What the page shows
- **Agents**, refreshed every 3 s while the page is visible:
  - Claude Code lead sessions and their subagents (`~/.claude*/projects`) and background task transcripts,
    grouped by session, each with a state dot, its description, the current action (its last tool call's
    description, e.g. "Running probe.py on both heroes"), time, tokens and ≈ API $;
  - Orca terminals (busy ◐ or idle ✳), matched to their session when the title agrees; tap one for a short,
    redacted screen preview;
  - Codex sessions (`~/.codex/sessions`) with their task and last command.
  - Only running agents show by default; "Show all" adds the finished and idle ones.
- **Feed**, newest first: images, videos and models (.glb, .fbx) created or changed in the watched folders.
  Each card has a thumbnail, the file, the project (worktree) and, when a transcript named the file, the agent
  ("likely" when only its folder was named). A checkout or batch export (60+ files in seconds) is one card.
  Filters: All, Images, 3D, Video and a project. Tap for a lightbox; a .glb opens in a 3D viewer
  (model-viewer, pinned on a CDN); videos play muted.
- **Mailbox**, collapsed: recent Orca orchestration messages.

## 3. Watched folders
`~/.config/wisecraft/studio.json` (all keys optional):
```json
{"base": "~/Documents/Codex", "roots": ["*/outputs", "*/shots", "*/qa", "*/art-shots", "design/**"], "hours": 8}
```
Roots are globs under `base`, or absolute paths; each match is watched with its subfolders (`node_modules`,
`build`, `dist` and hidden folders are skipped). To make a new asset show up, write it under one of them.
Put a `.png` with the same name next to a `.glb` or `.fbx` and it becomes the card's thumbnail.

## 4. Read the producer's reviews
Every 👍, 👎 or note appends one JSON line to `~/.config/wisecraft/reviews.jsonl`:
```json
{"time": "2026-10-19T17:02:11+05:00", "path": "/abs/path/hero-select.png", "verdict": "down", "note": "hero too dark", "project": "my-game-heroes"}
```
- `verdict` is `up`, `down` or `note` (a note on its own). The last line for a path wins.
- Before redoing or shipping an asset, read the lines for its path (or its folder):
  `grep -F '/hero-select.png' ~/.config/wisecraft/reviews.jsonl | tail -1`.
- A 👎 with a note is a change request: act on it, then say which review you answered.

## Rules
- It binds 127.0.0.1 only and serves only files inside the watched folders (real paths, no traversal). Its
  only writes are reviews.jsonl and thumbnails in `~/.cache/wisecraft/studio`.
- It hides keys, tokens and anything that reads `~/.config` or the environment. Don't add sources that show
  secrets.
- It stays cool: scans are mtime-cached and run only while a page is polling; a hidden page stops polling.
  Measure `ps -o %cpu -p <pid>` after changes; idle should stay around 1%.
- It never plays sound: videos are muted.
