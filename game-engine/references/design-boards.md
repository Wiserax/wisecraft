# Design boards and new features

The producer reviews pictures, not paragraphs. Every design or feature delivery ends with a **board**: a PNG of phone-sized screens with one-line captions, before/after when something changed.

## Making mockups fast
1. Write the screens as HTML at 390×844 (one `.screen` div each) using the game's fonts and tokens (`ui-kit.md`). Use real game screenshots as backdrops and overlay the new UI. CSS shapes and emoji are fine for a design pass; say so on the board.
2. Render each screen with `scripts/render-board.mjs` (Playwright, DPR 2), then compose a board page from the shots and render it to one PNG.
3. Caption every screen: **number · what happens** + one line of *why*.
4. Open the board locally for the producer (Preview). Don't publish it anywhere unless asked.

## In-engine look-dev
For new places or chapters, prototype the look inside the game, on a throwaway branch or behind a preview flag: palette, fog, ground, props, particles, recoloured enemies. Capture hub, battle, boss and a 16:9 hero frame. Real engine shots beat mockups.

## Design doc shape (`DESIGN.md`)
- One line: the fantasy and the twist.
- **Flow:** numbered screens matching the board.
- **Why it's interesting:** rules, not stats; the twist on a popular mechanic.
- **Numbers:** odds, pity, caps, budgets.
- **Monetization hooks,** plus what is *not* sold.
- Balance guard rails, analytics events, a build estimate in days.
- **Open choices,** each with the default already chosen.

## Examples that landed
- **Pick 1 of 3 "Pacts":** a titan drops a chest, which opens at stage clear; 3 rule-bending cards of random rarity; any card can be flipped to a cursed side (one tier stronger + one downside); pacts last while you keep fighting. Reroll by ad, seal a pact with gems, a pass perk adds a 4th card.
- **New chapters:** each adds ONE wordless rule (blizzard / wildfire / rising water), a counter upgrade, 2 enemies, a giant, 2 bosses and a titan variant, plus a new gacha tower and a skin as rewards.
