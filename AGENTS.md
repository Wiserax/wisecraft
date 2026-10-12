# wisecraft

Skills, a small CLI and a shared knowledge base for AI coding agents: Claude Code, Codex, Cursor, Gemini CLI,
GitHub Copilot, OpenCode and anything else that reads `AGENTS.md`. When someone opens an agent in this repo,
or with this plugin installed, they almost always want one of four things for their game.

## Start here: pick the skill
| They ask for | Open |
|---|---|
| a trailer, a clip, a store video, smoother slow motion, a 16:9 version | `skills/game-trailer/SKILL.md` |
| "too easy", "too hard", waves, HP, damage, prices, bosses, a difficulty target | `skills/game-balance/SKILL.md` |
| loot boxes, gacha, pity, currencies, sinks, shop, offers, season pass, retention | `skills/game-meta/SKILL.md` |
| "test it", "does it work on iPhone", play it like players, lag, a stuck splash | `skills/game-qa/SKILL.md` |

Also included, for narrower jobs: `game-ui-kit` (hub and HUD layout), `game-feel-audio` (bosses you feel, a
measured mix), `design-boards` (mockups to phone-sized boards) and `agent-orchestration` (a lead and workers).

Before you start, read `knowledge/INDEX.md`: field notes by pillar, written by agents for the next agent.
Other agents may already have written down the trap you are about to hit.

## Tools
- **`bin/wise`** is the Python CLI, and it sets itself up with `uv`.
  - Put it on PATH: `export PATH="$PWD/bin:$PATH"`, or install it anywhere with
    `uv tool install git+https://github.com/Wiserax/wisecraft`.
  - Every group has `--help`:
    - `video`: `compile` an EDL into a trailer, `check` a finished file (fps, loudness, cuts, first frame,
      repeated frames), `contact` sheets, `probe`, `beats`, `first-frame`
    - `qa`: web games: a muted phone-sized browser plays like a player (`--persona casual|tapper|idler|spender`);
      errors, overflow and frame time; screenshots and a board
    - `music-enhance`: measures and fixes loudness and true peak of trailers, music, game sounds and voice;
      never played
    - `board`: HTML mockups → phone-sized PNG screens and one review board
  - `qa` and `board` drive Playwright through node: `npm i -D playwright && npx playwright install chromium webkit`
    in the game's folder. `video` and `music-enhance` need ffmpeg.
- **Skill scripts** run without installs: `game-balance/scripts/bots.mjs` (node) and `curves.py`,
  `game-meta/scripts/drop_table.py` and `economy_ledger.py`, `game-trailer/scripts/snap_edl.py` (Python
  standard library).
- **Skills** (`skills/*/SKILL.md`, Agent Skills format) are copied where agents look for them in a clone:
  `.agents/skills` (Codex, Gemini CLI, Copilot, Cursor, OpenCode) and `.claude/skills` (Claude Code). Edit
  `skills/`, then run `python3 scripts/sync_skills.py`; a test fails while the copies differ.

## Rules
- **The person you work with is a producer.** Build to finished with sensible defaults and show the result
  (a video, screenshots, a board, a table); list the defaults so they are easy to change. Ask only when a
  choice is irreversible or faces outward.
- **Real data first.** Decide from real player analytics, real saves, real devices and the live build;
  simulations, bots and fixtures only fill gaps where real data does not exist yet. Say which numbers came
  from where.
- **Spending money needs a yes.** No real purchases, ad views or subscriptions (test spenders with debug
  grants and store sandboxes); no paid services, paid generation or paid agent runs; no live price, offer or
  odds change without the producer's yes.
- **Never play audio aloud.** Browsers run muted; mixes are measured (`wise music-enhance --check`,
  `wise video check`). The human listens, the agent measures, and says nobody has heard it.
- **Prove it in the real browser.** A simulator passing is not the game passing: the first session and every
  gate run in a phone-sized Chromium and WebKit.
- **Ask first** before:
  - pushing, merging, deploying or publishing anything: trailers, boards, PRs and public pages included;
  - sending messages or posting anywhere on the user's behalf;
  - deleting or overwriting work that is not yours (another agent's branch, a worktree, saves, analytics).
- **The repository:** explicit `git add <paths>`, never `git add .`; one writer per file; move files instead
  of deleting them; stop the servers you start and kill by exact PID.
- **What you ship:** no secrets, no private deploy URLs, no company or unreleased product names in public
  repos or notes. Only the game's own footage and assets you can credit. Read what goes out; no command
  checks it for you.
- **When to stop:** the same failure three times, a way forward that breaks a rule above, or a gate that
  can't be measured honestly on this machine right now (a laptop in low-power mode caps the browser at
  30 fps). Report "not confirmed" with the last good measurement.

## Working on the toolkit itself
- **Python:** 3.10+, deps Pillow and numpy (`uv` handles them via `bin/wise`). Code lives in `wisecraft/`,
  one module per CLI group, each with `register(sub)` and a docstring that doubles as `--help`. Node scripts
  the CLI drives live in `wisecraft/js/`.
- **Tests:** `uv run --with pytest pytest -q tests`. CI also runs
  `python3 scripts/sync_skills.py --check` and every command's `--help`. Real-browser tests run when
  `WISE_PLAYWRIGHT` names a folder with Playwright installed.
- **Wording:** keep skills and docs agent-neutral ("the agent", not a product name) except in sections
  about one specific agent.
- **Credits:** the architecture and parts of the tooling are adapted from Universal Modder (MIT). Ported
  files keep their notice; `NOTICE` lists them.
