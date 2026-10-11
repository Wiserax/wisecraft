# game-engine: a Claude Code skill for building and shipping web games

A studio playbook packaged as a Claude Code skill. It covers concept → vertical slice (Universal Modder loop) → economy and difficulty with simulated player bots → mobile UI kit → game feel and audio mix → performance → real-browser QA → Vercel release → lead/worker agent orchestration → trailer → design boards.

It was distilled from building and shipping *Zombie Tower: Short Sieges* (Vite + three.js, v1 → 2.3.x) with a producer, a lead Claude session and worker agents.

## Install
```bash
git clone https://github.com/Wiserax/game-engine-skill.git
mkdir -p ~/.claude/skills && cp -r game-engine-skill/game-engine ~/.claude/skills/
```
Claude Code picks it up automatically when you work on a web game: rebalancing, polishing UI or sound, fixing lag, releasing, cutting a trailer, designing new chapters or systems.

## What's inside
```
game-engine/
  SKILL.md                     the pipeline, producer contract, golden rules
  references/                  one file per stage (read on demand)
    um-loop.md  economy-balance.md  ui-kit.md  feel-audio.md  performance.md
    qa.md  release.md  orchestration.md  trailer.md  design-boards.md
  scripts/
    qa/browser-qa.template.mjs muted Chromium/WebKit phone harness (errors + overflow gate)
    render-board.mjs           HTML mockups → PNG screens + board
    dupframes.sh               slow-motion stutter check (ffmpeg)
    loudness.sh                EBU R128 loudness and true peak, no playback
  assets/
    spec-template.md           worker task spec (ownership, gate, constraints)
    board-template.html        before/after board layout
```

## Requirements
Node 18+, Playwright (`npm i -D playwright`), ffmpeg. Optional: Vercel CLI, an Orca-style mailbox for multi-agent work.

## Credits
- Method and lessons: Alex Wiserax with Claude Code.
- Vertical-slice loop inspired by Universal Modder (github.com/rehan-remade/universal-modder).
- Fonts referenced: Lilita One, DM Sans, Silkscreen (SIL OFL, via Google Fonts).
