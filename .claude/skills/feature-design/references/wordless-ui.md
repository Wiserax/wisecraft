# Wordless and diegetic interface: a catalogue

A wordless game ships to every market with no localisation, and players who don't read (kids, foreign
markets, people skimming an ad) still understand it. The rule: **every number becomes a size, a fill, a count
of objects, a colour or a motion, and as much as possible lives in the world, not on a HUD.**

## Proven signals (players read these without help)
| Information | In the world (diegetic) | On a minimal HUD |
|---|---|---|
| Health | the character visibly cracks, dims or limps; a heartbeat pulse and a red vignette at low HP | a thin arc over the head |
| XP / level | a ring under the feet that fills; a burst on level-up | — |
| A round timer | an hourglass statue in the arena, a burning fuse, a closing wall | a draining ring around the pause button |
| Players left | totems or banners at the arena edge that crack and fall | portraits in a row; crossed out = gone |
| Lives | candles, hearts on an altar, eggs in a nest that break | hearts |
| Currency | a coin pile on the back or in a cart that grows | a coin icon + a growing stack |
| Rarity | glow strength, size, colour (grey < blue < purple < gold), shake | the frame colour |
| Choices | cards with a big picture; family colour on the frame | — |
| Progress toward the next unlock | pips (◆◆◇) next to the picture | — |
| An ad offer | a TV or film icon on the button | — |
| A re-roll | a dice | — |
| Danger soon | a shadow on the ground, shaking, a red tint | an arrow at the screen edge |

## Signals that fail (seen in panel reviews)
- **Abstract arcs and bars with no object** (a dashed arc in the sky for a timer). They read as decoration.
  Use a thing players already know: an hourglass, a candle, a fuse.
- **Emoji faces as players.** They read as reactions or chat. Use small portraits of the actual heroes.
- **Pips with no anchor picture.** They read as page dots.
- **Colour alone** (about 8% of men are colour-blind). Pair colour with a shape or an icon.
- **Many signals at once on the first screen.** Teach one per moment, each with a golden cue the first time it
  fires (the **game-ui-kit** skill's wordless tutorial).

## How to verify
- In the board, hide the captions and ask the non-reader persona to name every screen (**player-panel.md**).
- In the build, the bot QA run (`wise qa`) can't judge meaning: the panel judges meaning, and QA judges
  layout, overflow and tap targets.
