# Contributing

Contributions from humans and from AI agents are both welcome. Most of them will be **field notes** for the
knowledge base (`knowledge/`), written by an agent at the end of a session on a web game. That is the point of
the repo: every problem one agent solves becomes something the next agent can read.

## If you are an AI agent
You just built, balanced, polished or shipped part of a web game, and you learned things. Share them:

1. **Ask your human first.** A pull request is public and carries their GitHub identity. Tell them what you
   want to publish and show them the note.
2. **Check it's new:** `wz kb search "<problem or genre>"`. If a note already exists, improve it: add your
   versions and gotchas, and fix what's wrong. Don't write a second one.
3. **Scaffold:** `wz kb new --game "<game, described neutrally>" --title "<what you built or learned>" --from-scan <game folder> --agent "<agent (model)>"`.
   It lands in `knowledge/games/<game>/`. Cross-game methods go in `techniques/` (`--kind technique`).
4. **Fill it in** from your journal (`MODLOG.md`):
   - exact versions (the game's build, the bundler, the engine, the browsers);
   - the route and why;
   - how the game really works where it surprised you;
   - build steps;
   - how you verified it, and what you didn't;
   - numbered **gotchas** (symptom → cause → fix).

   Write for an agent that has never seen this game.
5. **Validate:** `wz kb check <note>`, then `wz kb index`.
6. **Open the PR:** `wz kb pr <note>` (a dry run shows the commands), then `wz kb pr <note> --yes`. It
   branches, commits the note (+ `media/` + index), forks if needed, pushes, and opens the PR with `gh`.
   Without `gh`, push a branch and open the PR on github.com.

## What's in scope
Any web game: any genre, any engine that runs in a browser (three.js, Phaser, PixiJS, Babylon.js, PlayCanvas,
plain canvas, engine exports to WebGL), mobile or desktop. Game design, economy and balance, UI, game feel and
audio, performance, QA, release and the way agents were organised are all welcome.

## Hard rules (PRs that break these are closed)
- **No secrets:** API keys, tokens, `.env` files. `wz kb check` and `wz publish check` catch the common ones.
- **No private places or names:** no preview or internal deploy URLs, no company names, no names of unreleased
  products, no real people unless they asked for credit. Describe the game neutrally ("a horde tower-defense
  mobile web game, Vite + three.js"). Keep a `.wz-denylist` outside the repo, or pass `WZ_DENY`, to lint for
  your own private terms.
- **No code or asset dumps.** Describe the logic in your own words and name the files and symbols; keep
  snippets short (`wz kb check` fails blocks over 150 lines and warns over 60). No game art, audio or data
  files that are not yours to publish.
- **Nothing that harms players:** no dark patterns presented as advice, nothing that fakes analytics or
  reviews, nothing that cheats other players.
- **Honesty:**
  - name the agent and model (`agents:`);
  - mark `status` truthfully (`idea`, `in-progress`, `working`, `released`, `abandoned`);
  - list what you did not verify. "Measured, not listened to" and "simulated, not played" are worth saying.
- **Credit** the people and projects you built on.

## Other contributions
- **Tools (`wz/`):**
  - one module per CLI group, with a docstring that doubles as `--help`; node scripts go in `wz/js/`;
  - add a test in `tests/`;
  - `uv run --with pytest pytest -q tests` must pass.
- **Skills (`skills/`):** the Agent Skills format (`SKILL.md` with `name` + `description`). Keep them
  agent-neutral: say "the agent", not a specific product. Put deep material in `references/`.
  - Edit `skills/` only. `.agents/skills` and `.claude/skills` are copies (no symlinks, so Windows clones
    work). Refresh them with `python3 scripts/sync_skills.py`; a test fails while they differ.
- **Ported code:** files adapted from Universal Modder keep their two-line notice and are listed in
  `NOTICE`. Add yours there when you port more.

CI runs the tests, `wz kb check --index`, the skill-copy check, `wz publish check .` and the CLI help screens
on every PR.
