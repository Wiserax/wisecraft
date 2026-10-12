# Contributing

Contributions from humans and from AI agents are both welcome. Most of them will be **field notes** for the
knowledge base (`knowledge/`), written by an agent at the end of a session on a game. That is the point of
the repo: every problem one agent solves becomes something the next agent can read.

## If you are an AI agent
You just cut a trailer, tuned a game's balance or economy, or tested it in a browser, and you learned things.
Share them:

1. **Ask your human first.** A pull request is public and carries their GitHub identity. Tell them what you
   want to publish and show them the note.
2. **Check it's new:** read `knowledge/INDEX.md` (or `grep -ril "<word>" knowledge/`). If a note already exists, improve it: add your
   versions and gotchas, and fix what's wrong. Don't write a second one.
3. **Start from the template:** copy `knowledge/TEMPLATE.md` to `knowledge/games/<game, described neutrally>/<what-you-built>.md`.
   Cross-game methods go in `knowledge/techniques/`. Take exact versions from the lockfile and the engine's project files.
4. **Fill it in** from your notes of the session:
   - exact versions (the game's build, the bundler, the engine, the browsers, ffmpeg);
   - the route and why;
   - how the game really works where it surprised you;
   - build steps;
   - how you verified it, and what you didn't;
   - numbered **gotchas** (symptom → cause → fix).

   Write for an agent that has never seen this game.
5. **Read it once more** against the hard rules below, and add a line for it to `knowledge/INDEX.md` under
   the pillar it serves (trailer, balance, meta and monetization, QA, or the extras).
6. **Open the PR:** a branch, one commit with the note (and its `media/`, if any) and the index line, push,
   `gh pr create`. Without `gh`, push the branch and open the PR on github.com.

## What's in scope
Any game. Most notes so far are about web games (three.js, Phaser, PixiJS, Babylon.js, PlayCanvas, plain canvas,
engine exports to WebGL), and notes on Unity, Godot, Unreal or any other engine are just as welcome, mobile or desktop.
The four pillars come first: trailers, balance and economy, meta and monetization, and QA in a real browser.
Notes on UI, game feel and audio, and the way agents were organised are welcome too.

## Hard rules (PRs that break these are closed)
- **No secrets:** API keys, tokens, `.env` files. Nothing checks this for you: read the note before you push.
- **No private places or names:** no preview or internal deploy URLs, no company names, no names of unreleased
  products, no real people unless they asked for credit. Describe the game neutrally ("a horde tower-defense
  mobile web game, Vite + three.js").
- **No code or asset dumps.** Describe the logic in your own words and name the files and symbols; keep
  snippets short (a block over 60 lines is a dump, not a snippet). No game art, audio or data
  files that are not yours to publish.
- **Nothing that harms players:** no dark patterns presented as advice, no hidden or false odds, nothing
  that fakes analytics or reviews, nothing that cheats other players.
- **Honesty:**
  - name the agent and model (`agents:`);
  - mark `status` truthfully (`idea`, `in-progress`, `working`, `released`, `abandoned`);
  - list what you did not verify. "Measured, not listened to" and "simulated, not played" are worth saying.
- **Credit** the people and projects you built on.

## Other contributions
- **Tools (`wisecraft/`):**
  - one module per CLI group, with a docstring that doubles as `--help`; node scripts go in `wisecraft/js/`;
  - add a test in `tests/`;
  - `uv run --with pytest pytest -q tests` must pass.
- **Skills (`skills/`):** the Agent Skills format (`SKILL.md` with `name` + `description`). Keep them
  agent-neutral: say "the agent", not a specific product. Put deep material in `references/`.
  - Edit `skills/` only. `.agents/skills` and `.claude/skills` are copies (no symlinks, so Windows clones
    work). Refresh them with `python3 scripts/sync_skills.py`; a test fails while they differ.
- **Ported code:** files adapted from Universal Modder keep their two-line notice and are listed in
  `NOTICE`. Add yours there when you port more.

CI runs the tests, the skill-copy check and the CLI help screens on every PR.
