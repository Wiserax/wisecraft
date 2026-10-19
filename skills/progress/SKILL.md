---
name: progress
description: Show a short, emoji status board of all ongoing agent work, grouped by account. It covers the lead's own subagents, worker terminals (Orca or tmux) and their subagents, and Codex jobs, with one line per agent showing a stage bar, time, tokens and API-equivalent $. Use when the user types /progress or asks "what's running", "status of the agents", "who is doing what", "how much did it cost" or "progress".
---

# /progress: who is doing what, right now

A producer reads this on the go. One glance must answer four things: who is working, on what, how far along, and how much it has used. Only report what you can see; never invent numbers.

## 1. Collect (read-only, in parallel, a few seconds)
- **Tokens, $ and time for every Claude agent:**
  ```
  python3 <this skill>/scripts/agents.py --hours 8 <your session dir> <each worker's project dir>
  ```
  - Session dir: `~/.claude/projects/<project>/<session-id>`.
  - A project dir uses its latest session.
  - It prints one row per agent:
    - state: `running`, `done` or `stopped`;
    - minutes active and tokens;
    - $ at API list price (a subscription pays a flat fee, so label it "≈ API $");
    - the agent's description.
  - Never read transcripts yourself.
- **Your own subagents:** take the stage from each one's latest progress line.
- **Worker terminals** (only the workers this project delegates to, not every open terminal):
  - Orca: `orca terminal read --terminal <handle> | tail -40`.
  - tmux: `tmux capture-pane -p -t <pane> | tail -40`.
  - The footer gives the account (email) and its subagent lines.
- **Codex jobs:** `pgrep -fl "codex exec"`. If none is running, show "idle" and the last output.
- **Proof:** new commits per worker branch, from `git -C <worktree> log --oneline <base>..`.

## 2. Print it in chat (plain markdown, no code block)
```
### 📊 Progress · <day> <HH:MM>

**🧠 <lead session>** · <account> · 💰 ≈$<sum> · 🔢 <sum>M tok
- 🟢 **<Agent>** · <task, ≤4 words>
  `▓▓▓░░` QA · ⏱ 31m · 🔢 13.8M · 💰 $11
- ✅ **<Agent>** · <result, ≤4 words> · ⏱ 54m · 💰 $19

**🛠️ <worker>** · <account> · 💰 ≈$<sum>
- 🟡 **<Agent>** · <task> · waiting for <what>

**🎨 Codex** · <account>
- 💤 idle · last: <output>

**Next:** <one line: merge or deploy next, plus the playable link>
🙋 **You:** <the decision or action the user owes, if any>
```

**The stage bar** has 5 cells and comes from the stage the agent reports, never from a guess:

| Bar | Stage |
|---|---|
| `▓░░░░` | starting or reading |
| `▓▓░░░` | building |
| `▓▓▓░░` | QA or testing |
| `▓▓▓▓░` | fixing or polishing |
| `▓▓▓▓▓` | report or done |

If the agent printed a count (`3/4 models`), use that instead.

**Status emoji:**
- 🟢 running
- 🟡 waiting or blocked (say on what)
- ✅ done, not merged yet
- 🚀 merged or shipped
- 🔴 failed or stuck
- 💤 idle
- ⏸️ stopped by the user

**Layout rules:**
- One agent per entry: a name and a few words on line 1, then the bar and numbers on line 2. Round $ to whole dollars and tokens to one decimal (M).
- Agents that finished earlier today: put them on one ✅ line at the end of their group, with the total $.
- Show agents that were stopped only if they used more than $1.
- If more workers are running than the agreed cap, add one `⚠️` line.

## Live panel
For a board that stays open and updates itself, with a feed of the screenshots, videos and models the agents
make, launch `wise studio --open` (the `studio` skill). It reads the same transcripts with `scripts/agents.py`.

## Don'ts
- No paragraphs and no file paths, unless the user asks.
- No percentages that don't come from a stage or a printed count.
- Don't spawn agents to build the board.
