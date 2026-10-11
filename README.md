# 🧙 Wizerax: the game studio in a skill

**A complete framework for making web games with AI agents.** It's a Claude Code skill that takes a game from idea to release: game design and economy, UX/UI, game feel and sound, performance, QA, release, multi-agent orchestration, and the trailer at the end.

Battle-tested on two shipped mobile web games (Vite + three.js, thousands of enemies on screen at 60 fps), built by a producer working with a lead Claude session and worker agents.

## What it gives your agents
| Stage | What the agent knows how to do |
|---|---|
| 🧪 Concept → vertical slice | Universal Modder loop: recon, route, lab, slice, verify in-game, showcase, publish check |
| ⚖️ Economy & difficulty | Player-model bots (passive / tutorial / heavy tapper / efficient), difficulty index, rising-sine stages, boss tiers, premium-currency budgets |
| 📱 UX/UI | Clean hub with rails and one golden call to action, a 1-row battle bar, a wordless tutorial, EN/ES, 320 px phones |
| 💥 Game feel & sound | Bosses you feel (entrance, slam, real death, loot), a VFX quality bar, a measured audio mix (never played aloud by the agent) |
| 🚀 Performance | Capacity + real late-stage tests, budgets, an adaptive quality guard that actually recovers |
| ✅ QA | Muted Chromium/WebKit phone bots that tap like players; sim-vs-browser checks |
| 📦 Release | Versioning, prebuilt deploys, live checks, frozen older versions on their own URL |
| 🤝 Orchestration | Lead/worker specs with file ownership, mailbox flow, no heartbeat spam |
| 🎬 Trailer | Hook in 3 s, the loop by 8 s, a hero finale, 120 fps slow motion, an SFX mix at -15 LUFS, a review scorecard |
| 🖼️ Design boards | HTML mockups → phone-sized PNG boards, a DESIGN.md with defaults and a build estimate |

## Install
```bash
git clone https://github.com/Wiserax/wizerax-gamedev.git
mkdir -p ~/.claude/skills && cp -r wizerax-gamedev/wizerax ~/.claude/skills/
```
Then just work on your game. Claude uses the skill when you rebalance, polish the UI or sound, fix lag, release, design chapters or systems, or cut a trailer. You can also call it directly with `/wizerax`.

## What's inside
```
wizerax/
  SKILL.md                      the pipeline, the producer contract, golden rules
  references/                   one file per stage, read on demand
  scripts/qa/browser-qa.template.mjs   muted Chromium/WebKit phone harness (errors + overflow gate)
  scripts/render-board.mjs      HTML mockups → PNG screens + board
  scripts/dupframes.sh          slow-motion stutter check (ffmpeg)
  scripts/loudness.sh           EBU R128 loudness / true peak, no playback
  assets/spec-template.md       worker task spec (ownership, gate, constraints)
  assets/board-template.html    before/after board layout
```

## Requirements
Node 18+, Playwright, ffmpeg. Optional: Vercel CLI, a mailbox tool for multi-agent work.

## Credits
Created by **Alex Wiserax** with Claude Code. The vertical-slice loop is inspired by [Universal Modder](https://github.com/rehan-remade/universal-modder). The fonts it refers to are Lilita One, DM Sans and Silkscreen (SIL OFL).
