---
name: design-boards
description: Show designs and results as picture boards instead of documents. Covers HTML mockups at phone size rendered to PNG screens and one composed board (`wise board`), captions with a number, an action and a reason, before/after boards, boards of real screenshots with actions and arrows, in-engine look-dev for new places and chapters, and the shape of a DESIGN.md (flow, numbers, monetization hooks, guard rails, build estimate, open choices with defaults). Use when the user says "design a new feature", "mock it up", "show me how it would look", "make a board", "what would chapter 2 look like", "pitch a monetization system", or at the end of any feature or fix that changed what the player sees.
---

# Design boards and new features

The producer reviews pictures, not paragraphs. Every design or feature delivery ends with a **board**: a PNG
of phone-sized screens with one-line captions, before/after when something changed. A document nobody opens
is not a delivery.

## The tool
```bash
wise board --init design/pacts                               # a starter mockups.html and board.html in that folder
wise board design/pacts/mockups.html --board design/pacts/board.html
```
`wise board` renders each screen of the mockups file to a PNG (phone size, DPR 2), then renders the board page
to one PNG. In a clone it is `bin/wise`. It drives a muted headless browser, so it needs Playwright:
`npm i -D playwright && npx playwright install chromium`.

Without `wise`: `scripts/render-board.mjs` does the same two steps
(`node render-board.mjs <mockups.html> <outDir> [ids] --board board.html`), and
`assets/board-template.html` is the board layout.

## Making mockups fast
1. Write the screens as HTML at 390×844 (one `.screen` div each, each with an `id`) using the game's fonts
   and tokens (the **game-ui-kit** skill). Use real game screenshots as backdrops and overlay the new UI.
   CSS shapes and emoji are fine for a design pass; say so on the board.
2. Render each screen (Playwright, DPR 2), then compose a board page from the shots and render it to one
   PNG. `wise board` does both.
3. Caption every screen: **number · what happens** + one line of *why*.
4. Open the board locally for the producer (the system image viewer). Don't publish it anywhere unless
   asked.

## Boards of real screenshots, with actions and arrows
For anything that already runs, a mockup is the wrong tool. Take screenshots of the real build (`wise qa`
writes them and a `board.png` of each run; the **game-qa** skill) and lay them out as an interface map:
- one screen per frame, in the order a player meets them;
- **mark the action** on each frame: a ring or a hand on the spot that was tapped;
- **an arrow** from that spot to the screen it leads to;
- a caption per frame: number · what the player does · what happens.

A reader should be able to follow a session by the arrows alone. Use this for QA evidence, research on other
games, onboarding reviews and "what changed" reports.

## Before/after boards
- Same scene, same camera, same moment. Red frame for before, green for after (the template has both
  classes).
- The caption under "after" says what changed **for the player**, not what changed in the code.
- For motion or sound, add what a still can't show: a strip of frames, a chart, a preview file path.
- Don't crop away the problem. If the fix made something else worse, it goes on the board too.

## In-engine look-dev
For new places or chapters, prototype the look inside the game, on a throwaway branch or behind a preview
flag: palette, fog, ground, props, particles, recoloured enemies. Capture hub, battle, boss and a 16:9 hero
frame. Real engine shots beat mockups.
- Gate it: the look applies only in preview. Leaving the preview must restore everything; check that in
  Chromium and WebKit.
- Note the cost with the shots: draw calls and triangles of a staged frame (three new biomes cost about
  46–51 draw calls and 121–133k triangles each).
- The same staging gives the hub its chapter previews: short muted loops and posters.

## The design doc (`DESIGN.md`)
Short, and numbered to match the board.
- One line: the fantasy and the twist.
- **Flow:** numbered screens matching the board.
- **Why it's interesting:** rules, not stats; the twist on a popular mechanic.
- **Numbers:** odds, pity, caps, budgets.
- **Monetization hooks,** plus what is *not* sold.
- Balance guard rails, analytics events, a build estimate in days.
- **Open choices,** each with the default already chosen.

The last line is the producer contract in practice: the producer changes a default; they don't answer a
question sheet. `references/design-doc.md` has a template and two designs that landed.

## Done means
- A board PNG at a known path, opened locally for the producer.
- Every frame has a number and a caption; real screenshots show the tapped spot.
- A DESIGN.md for new features, with defaults chosen and a build estimate.
- Nothing published.

## References
- `references/design-doc.md`: the DESIGN.md template and the examples that landed (a pick-1-of-3 system, new
  chapters). Read it when designing a feature.
- `assets/board-template.html`: the board layout (grid of phone screens, before/after frames).
- `scripts/render-board.mjs`: Playwright fallback for `wise board`.
