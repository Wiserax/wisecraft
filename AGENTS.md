# wisecraft

A game studio toolkit and a shared knowledge base for AI coding agents: Claude Code, Codex, Cursor, Gemini
CLI, GitHub Copilot, OpenCode and anything else that reads `AGENTS.md`. When someone opens an agent in this
repo, or with this plugin installed, they almost always want to **build, balance, polish or ship a mobile web
game** (Vite + three.js or similar), or to learn how a problem in one was solved.

## Start here
1. **Read `skills/make-web-game/SKILL.md` and follow its loop:** intake → recon → route → lab → source of
   truth → vertical slice → economy → UI → feel and audio → performance → browser QA → release → trailer →
   field note. It says which skill to open next.
2. **Read the knowledge base first:** `knowledge/INDEX.md` lists the field notes by game, engine and route.
   Other agents may already have written down the versions, the route and the gotchas.
3. **At the end, share what you learned:** write a field note from `knowledge/TEMPLATE.md` and, once your
   human agrees, open a PR. See `knowledge/README.md` and `CONTRIBUTING.md`.

## Tools
- **`bin/wise`** is the Python CLI, and it sets itself up with `uv`.
  - Put it on PATH: `export PATH="$PWD/bin:$PATH"`, or install it anywhere with
    `uv tool install git+https://github.com/Wiserax/wisecraft`.
  - Every group has `--help`:
    - `scan`: any game project (Unity, Godot, Unreal, GameMaker, Defold, Cocos, Rust, C/C++, C#, Android, iOS,
      web), a web game's URL, or any video clip: engine and versions, entry points, build targets, assets
    - `qa`: web games only: a muted phone-sized browser that taps like a player; console errors, overflow,
      screenshots
    - `board`: HTML mockups → phone-sized PNG screens and one review board
    - `music-enhance`: measures and fixes loudness and true peak of music, trailers, game sounds and voice;
      never played
    - `video`: contact sheets and EDL trailer edits, for footage of any game
  - `qa` and `board` drive Playwright through node: `npm i -D playwright && npx playwright install chromium webkit`
    in the game's folder. `music-enhance`, `video` and a video `scan` need ffmpeg.
- **Skills** (`skills/*/SKILL.md`, Agent Skills format) are copied where agents look for them in a clone:
  `.agents/skills` (Codex, Gemini CLI, Copilot, Cursor, OpenCode) and `.claude/skills` (Claude Code). Edit
  `skills/`, then run `python3 scripts/sync_skills.py`; a test fails while the copies differ.

## Rules (full reasoning in `skills/make-web-game/references/safety.md`)
- **The person you work with is a producer.** Build to ready-to-play with sensible defaults and show
  screenshots or a board; list the defaults so they are easy to change. Ask only when a choice is
  irreversible or faces outward.
- **Never play audio aloud.** Browsers run muted; mixes are measured (`wise music-enhance --check`, muted captures). The
  human listens, the agent measures.
- **Never touch real players' data.** Automated runs answer analytics calls with a 204 and never write to
  live saves, leaderboards or purchases. Debug hooks and previews never grant real rewards.
- **Prove it in the real browser.** A simulator passing is not the game passing: the first session and every
  gate run in a phone-sized Chromium and WebKit.
- **Ask first** before:
  - pushing, merging, deploying or publishing anything, PRs and public pages included;
  - sending messages or posting anywhere on the user's behalf;
  - deleting or overwriting work that is not yours (another agent's branch, a worktree, saves).
- **What you ship:** no secrets, no private deploy URLs, no company or unreleased product names in public
  repos or notes. Read what goes out; no command checks it for you.
- **Keep a journal:** a `MODLOG.md` in the game's working folder. It becomes your field note at the end.

## Working on the toolkit itself
- **Python:** 3.10+, deps Pillow and numpy (`uv` handles them via `bin/wise`). Code lives in `wisecraft/`,
  one module per CLI group, each with `register(sub)` and a docstring that doubles as `--help`. Node scripts
  the CLI drives live in `wisecraft/js/`.
- **Tests:** `uv run --with pytest pytest -q tests`. CI also runs
  `python3 scripts/sync_skills.py --check` and every command's `--help`.
- **Wording:** keep skills and docs agent-neutral ("the agent", not a product name) except in sections
  about one specific agent.
- **Credits:** the architecture and parts of the tooling are adapted from Universal Modder (MIT). Ported
  files keep their notice; `NOTICE` lists them.
