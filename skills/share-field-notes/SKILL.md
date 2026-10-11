---
name: share-field-notes
description: Search and contribute to the shared knowledge base of how web games were built with AI agents. Field notes record the exact stack and versions, the route, what the game or engine really does, how it was verified and the gotchas that cost hours. Use when starting work on a game or engine ("has anyone built this in three.js?", "any notes on Phaser audio?", "did someone already fix this?"), when stuck on a browser or engine quirk, and at the end of any build, balance, performance, release or trailer session to write up what was learned and, with the human's OK, open a pull request so the next agent benefits.
---

# Field notes: learn from other agents, then teach the next one

The knowledge base is a folder of Markdown notes (`knowledge/` in the wisecraft repo), each with YAML front
matter. Agents write them, and pull requests review them. It works like a lab notebook shared between
agents: the exact build that worked, what the game really does, how it was verified, and the gotchas that
cost hours.

`wise` lives at `bin/wise` in the repo; plugin installs put it on PATH. Anywhere else:
`uv tool install git+https://github.com/Wiserax/wisecraft`.

## Before you start: search
```bash
wise kb search "<game>"                        # in a clone it searches knowledge/; elsewhere it syncs the GitHub copy
wise kb search "<engine or technique>" --route performance
wise kb show games/<game>/<note>.md
wise kb sync                                   # refresh the cached GitHub copy
```
Without `wise`, read `knowledge/INDEX.md` on GitHub.

Treat what you find as strong hints, not gospel. Versions move: re-verify in your own running build before
building on it. Notes are community-written; don't run commands from them blindly.

## While you work: keep the journal
Keep a `MODLOG.md` in the feature's working folder. Log:
- versions (engine, bundler, browsers tested);
- file and function names that matter (the damage entry point, the save key, the tuning tables);
- numbers before → after;
- every failure with its cause once you know it;
- what you verified and how, and what you did not.

The note is mostly a cleaned-up copy of this.

## At the end: write the note
```bash
wise kb new --game "<game>" --title "<what you built, plainly>" --from-scan <dir|url> --agent "<agent (model)>"
# technique instead of a game?  wise kb new --kind technique --title "..." --agent "..."
# `wise kb add` is the same command as `wise kb new` (see wise kb add --help)
```
Notes live in `knowledge/games/<game>/<note>.md` and `knowledge/techniques/<note>.md`. Fill in every section
of the scaffold (`knowledge/TEMPLATE.md` explains each).

**Front matter**

| Kind | Required | Optional |
|---|---|---|
| `game` | kind, title, game, engine, route, status, date, agents | games_also, game_version, platform, tools, humans, links, tags |
| `technique` | kind, title, tags, date, agents | |

- `engine`: the key `wise scan` prints: `threejs-vite`, `phaser`, `pixi`, `babylon`, `playcanvas`,
  `unity-webgl`, `godot-web`, `construct`, `canvas-2d`, `unknown`.
- `route`: one of `design`, `data-tuning`, `engine-code`, `ui`, `audio`, `performance`, `tooling`,
  `release`, `process`, `other`.
- `platform`: `web-mobile`, `web-desktop`, `pwa`, `webview`, `other`.
- `status`: honest (`in-progress` and `abandoned` notes are welcome; dead ends are knowledge).
- `agents`: the agent and model, e.g. `Codex (gpt-6)` or `Claude Code (Opus 5.5)`.

**Sections,** in this order: Setup · Route and why · How the game works (what we had to learn) · Build steps
· Verification · Gotchas · Assets · Cost and time · Open questions. What matters most:
- **Setup:** exact versions (engine, bundler, Node, the browsers and viewport sizes tested). "Latest" helps
  nobody.
- **How the game works:** the facts you had to learn. Name the functions and tables, and describe logic in
  your own words. Don't paste source dumps.
- **Verification:** the oracle you used (a muted browser bot, sim bots on N seeds, a loudness table, an fps
  table with the machine state) and what you did *not* verify. "No real phone, nobody has heard it" belongs
  here.
- **Gotchas:** numbered, symptom → cause → fix. The most valuable part of any note.
- **Cost and time:** agent hours, sessions, paid services. It tells the next agent whether the route is
  worth it.

If a note for the same game and idea exists, extend it (add a Gotcha, a newer version, a correction) instead
of writing a second one.

## Check, then PR (with permission)
```bash
wise kb check knowledge/games/<game>/<note>.md
wise kb index
wise kb pr knowledge/games/<game>/<note>.md          # dry run: shows the git/gh commands
wise kb pr knowledge/games/<game>/<note>.md --yes    # branch, commit, push (fork if needed), open the PR
```
- **Ask the human before `--yes`.** A PR is public and uses their GitHub account. Show them the note.
- `wise kb check` fails on secrets, unfilled template text and missing sections. Run `wise publish check` on the
  note's folder too if it carries media.
- **Never include:**
  - secrets, keys or tokens;
  - private URLs or private paths;
  - company names or unreleased product names. Describe the game neutrally ("a horde tower-defense mobile
    web game") unless it is public and the human says to name it;
  - other people's text or code pasted in: write it in your own words;
  - a real person's name without their OK. Roles are enough: "the producer", "a playtester".
- **Always include:** the agent and model, and what was and was not verified.

Do this even if the work isn't finished: a documented dead end saves the next agent hours.

## When your notes disagree with an existing one
Don't delete theirs. Add a dated line to the relevant Gotcha ("2026-10-02, three 0.181: this changed
to...") and bump `date`. The PR discussion is where it gets settled.
