# Universal Modder loop (concept → shippable slice)

The Universal Modder (UM) loop is how a new mode or feature goes from an idea to something playable inside the real game, without breaking the base game. The game mode behind our first shipped title was built this way. The method follows github.com/rehan-remade/universal-modder.

## Steps
1. **Recon:** read the game's loop, save format, mod loader and event bus. Write down which hooks exist (`registerMod({event})`, run lifecycle, spawn, kill, reward).
2. **Route:** choose the smallest change that delivers the fantasy. Write a one-paragraph pitch: what the player feels, and what changes in the loop.
3. **Lab:** prototype the risky part alone (a sim script, a debug spawn, a throwaway branch). Kill bad ideas here.
4. **Vertical slice:** build it end to end in the real build: data, logic, UI, feel, sound and save migration. It must be playable from a fresh profile *and* from an old save.
5. **In-game verification:** drive the real build in a headless browser (an agent bridge via `window.__game`) and prove the slice works; see `qa.md`.
6. **Showcase:** record scripted takes (`showcase/record.mjs`) and compile a short video (an EDL); see `trailer.md`.
7. **Publish check:** tests, QA, fps, analytics events tagged with `game_version`, save import from previous versions, and a separate save key while it's a prototype.

## Files every mod keeps
- `src/mods/<mod>/README.md`: what it changes, how to install, credits.
- `src/mods/<mod>/MODLOG.md`: a dated entry per change: **what, why (producer words), numbers before → after, how verified**. Merge conflicts in MODLOG: keep both entries.
- `src/mods/<mod>/FIELD-NOTE.md`: lessons for the next modder.
- `src/mods/<mod>/showcase/`: takes, EDLs, capture tooling. Keep it out of the shipped bundle.

## Prototype → main game
- Run A/B prototypes on separate paths (`/mastery/`, `/sieges/`) with separate saves. When one wins, promote it to the root, redirect the others (307), import the old saves once, and keep the analytics identity.
- Never call the main game a "prototype" again once it's promoted.
