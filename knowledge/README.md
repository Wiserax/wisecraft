# The AI web-game knowledge base

Field notes on how real games were trailered, balanced, monetized and tested. **Written by agents for
the next agent**, reviewed through pull requests. Each note records what one project learned the hard way:
the exact versions that worked, the route, how the game and its engine really behave, how it was verified,
and most of all the **gotchas** (symptom → cause → fix). The next agent that builds the same kind of game or
uses the same engine starts with that instead of rediscovering it.

- [`INDEX.md`](INDEX.md) lists every note, by game and by technique.
- `games/<game>/<note>.md` holds one piece of work each, filed under a neutral description of the game
  (`horde-tower-defense`, not a product name).
- `techniques/<note>.md` holds cross-game methods: player-model bots, muted browser QA, loudness checks,
  frame budgets, trailer captures...
- The workflows these notes feed (trailer, balance, meta and monetization, QA, and the extras: UI, feel and
  audio, boards, orchestration) live with the skills, in [`../skills/`](../skills/).

## Before you start: read
The notes are plain Markdown. Open [`INDEX.md`](INDEX.md) and read the ones for your kind of game, your engine
or your problem; `grep -ril "<word>" knowledge/` finds a word in any of them. Outside a clone, read the same
files on GitHub.

Treat a note as a strong hint, not as gospel: versions move, so check it in your own running build.

## After you finish (or get stuck): write it up and open a PR
A note is worth writing whenever you learned something the next agent would otherwise lose an hour to,
even if the feature isn't finished. `status: in-progress` and `abandoned` are welcome; dead ends are knowledge.

1. Copy [`TEMPLATE.md`](TEMPLATE.md) to `games/<game, described neutrally>/<what-you-built>.md` (or to
   `techniques/<method>.md` for something that holds across games; that kind needs only `kind`, `title`,
   `tags`, `date` and `agents` in its front matter).
2. Fill it in: Setup (exact versions, from the lockfile and the engine's project files), Route and why, How the game works,
   Build steps, Verification, Gotchas.
3. Add one line for it to [`INDEX.md`](INDEX.md).
4. Once your human agrees, open a pull request with the note (`git switch -c note/<slug>`, commit, push,
   `gh pr create`, or the button on github.com).

The rules in short:
- no secrets: keys, tokens, `.env` contents;
- no private URLs: preview and deploy hosts stay out (write `https://<name>.example.app`), loopback addresses
  in commands are fine;
- no company or unreleased product names: describe the game neutrally ("a horde tower defense for mobile
  web");
- describe what you learned in your own words;
- name the agent and model;
- say honestly what you did and didn't verify.

## What makes a good note
- **Versions.** "Vite 7.1 + three.js 0.180 on iOS Safari 18" beats "latest".
- **Gotchas with causes.** "The boss's slam landed a frame before its animation, because damage ran in the
  fixed step and the animation in the render step" is reusable; "the boss felt off" isn't.
- **The oracle.** How you knew it worked (a simulation, a muted browser run, a measured number), so the next
  agent can re-verify after the game changes.
- **Short code.** A snippet of *your own* code is fine. Link to the repo for the rest.
