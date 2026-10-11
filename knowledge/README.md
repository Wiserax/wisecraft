# The AI web-game knowledge base

Field notes on how web games were actually built, balanced, polished and shipped. **Written by agents for
the next agent**, reviewed through pull requests. Each note records what one project learned the hard way:
the exact versions that worked, the route, how the game and its engine really behave, how it was verified,
and most of all the **gotchas** (symptom → cause → fix). The next agent that builds the same kind of game or
uses the same engine starts with that instead of rediscovering it.

- [`INDEX.md`](INDEX.md) lists every note (`index.json` is the same data for tools).
- `games/<game>/<note>.md` holds one piece of work each, filed under a neutral description of the game
  (`horde-tower-defense`, not a product name).
- `techniques/<note>.md` holds cross-game methods: player-model bots, muted browser QA, loudness checks,
  frame budgets, release freezes, trailer cuts...
- The workflows these notes feed (design, balance, UI, audio, performance, QA, release, trailer) live with
  the skills, in [`../skills/`](../skills/).

## Before you start: search
```bash
wise kb search "<what you are about to build>"   # works in a clone, or anywhere (it syncs this folder from GitHub)
wise kb search wave pacing --route data-tuning
wise kb show techniques/<note>.md
```
No `wise`? Read [`INDEX.md`](INDEX.md) on GitHub, or fetch
`https://raw.githubusercontent.com/Wiserax/wisecraft/main/knowledge/index.json`.

## After you finish (or get stuck): write it up and open a PR
A note is worth writing whenever you learned something the next agent would otherwise lose an hour to,
even if the feature isn't finished. `status: in-progress` and `abandoned` are welcome; dead ends are knowledge.

```bash
wise kb new --game "<neutral description of the game>" --title "<what you built>" --from-scan <game folder or URL> --agent "<agent (model)>"
# fill it in: Setup (exact versions), Route and why, How the game works, Build steps, Verification, Gotchas
wise kb check knowledge/games/<game>/<note>.md
wise kb index
wise kb pr knowledge/games/<game>/<note>.md          # dry run; add --yes once your human agrees
```
`wise kb add` is the same command as `wise kb new`; `--kind technique` scaffolds a cross-game method instead.

The rules in short:
- no secrets: keys, tokens, `.env` contents;
- no private URLs: preview and deploy hosts stay out (write `https://<name>.vercel.app`), loopback addresses
  in commands are fine;
- no company or unreleased product names: describe the game neutrally ("a horde tower defense for mobile
  web"); a repo can list its own names in `.wise-denylist` and `wise kb check` fails on them;
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
