# Universal Modder loop (concept → shippable slice)

The Universal Modder (UM) loop is how a new mode or feature goes from an idea to something playable inside
the real game, without breaking the base game. The game mode behind our first shipped title was built this
way. The method follows github.com/rehan-remade/universal-modder (MIT). UM mods a PC game someone else made;
here you own the source, so "mod loader" means the hooks in your own code.

## Steps
1. **Recon:** read the game's loop, save format, mod loader and event bus. Write down which hooks exist
   (`registerMod({event})`, run lifecycle, spawn, kill, reward). See the **web-game-recon** skill.
2. **Route:** choose the smallest change that delivers the fantasy. Write a one-paragraph pitch: what the
   player feels, and what changes in the loop.
3. **Lab:** prototype the risky part alone (a sim script, a debug spawn, a throwaway branch). Kill bad ideas
   here.
4. **Vertical slice:** build it end to end in the real build: data, logic, UI, feel, sound and save
   migration. It must be playable from a fresh profile *and* from an old save.
5. **In-game verification:** drive the real build in a headless browser (an agent bridge via
   `window.__game`) and prove the slice works. See the **browser-qa** skill.
6. **Showcase:** record scripted takes (`showcase/record.mjs`) and compile a short video from an EDL
   (`wise video compile`). See the **trailer-video** skill.
7. **Publish check:** tests, QA, fps, analytics events tagged with `game_version`, save import from previous
   versions, and a separate save key while it's a prototype. See the **release-web-game** skill.

## Routes that were rejected, and why
On the first mode, two cheaper-looking routes lost to a small source-level mod loader (`registerMod`, `hook`,
`hookValue`, a handful of hook points, all mod logic in `src/mods/<mod>/`):
- **Console or userscript injection into the built bundle.** Fine for a demo. It can't ship to testers and
  doesn't survive minification.
- **Forking the app file again.** Fastest today. It makes the new mode impossible to diff against the base.

## Files every mod keeps
- `src/mods/<mod>/README.md`: what it changes, how to install, credits.
- `src/mods/<mod>/MODLOG.md`: a dated entry per change: **what, why (producer words), numbers before →
  after, how verified**. Merge conflicts in MODLOG: keep both entries.
- `src/mods/<mod>/FIELD-NOTE.md`: lessons for the next modder. This is the draft of the knowledge-base note
  (the **share-field-notes** skill).
- `src/mods/<mod>/showcase/`: takes, EDLs, capture tooling. Keep it out of the shipped bundle.

## Prototype → main game
- Run A/B prototypes on separate paths (`/mastery/`, `/sieges/`) with separate saves. When one wins, promote
  it to the root, redirect the others (307), import the old saves once, and keep the analytics identity.
- Never call the main game a "prototype" again once it's promoted.

## What changes from UM when the game is yours
| UM (someone else's PC game) | Here (your web game) |
|---|---|
| `um scan` finds the install and the engine | `wise scan <dir\|url>` reads the repo or the live page |
| Back up saves before a modded launch | A separate save key and origin for prototypes; old saves kept as QA fixtures |
| The running game is the oracle, driven by window input | The running build is the oracle, driven by a muted headless phone browser |
| Never ship game files | Never ship secrets, private URLs or assets you can't license |
| Publishing is the user's call | The same |
