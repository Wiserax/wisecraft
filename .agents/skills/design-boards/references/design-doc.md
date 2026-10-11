# DESIGN.md: template and examples

## Template
```markdown
# <Feature>
<One line: the fantasy and the twist.>

## Flow (matches the board)
1. <screen · what the player does · what happens>
2. ...

## Why it's interesting
- <a rule, not a stat>
- <the twist on a mechanic players already know>

## Numbers
- Odds: <per rarity>   Pity: <after N>   Caps: <power, per day>   Budget: <premium per chapter>

## Monetization hooks
- <what an ad, premium currency or the pass buys>
- Not sold: <what stays earnable only>

## Guard rails
- Balance: <what must not change: bot targets, premium budget>
- Analytics events: <names, with the release field>
- Save: <new fields, migration, what a reload mid-flow does>

## Build estimate
<N days>: <data> · <logic> · <UI> · <feel and sound> · <tests> · <QA>

## Open choices (defaults already chosen)
- <choice>: **<default>** (alternative: <other>)
```

Keep it to one screen of text. The board carries the rest.

## Examples that landed
- **Pick 1 of 3 "Pacts":** a titan drops a chest, which opens at stage clear; 3 rule-bending cards of random
  rarity; any card can be flipped to a cursed side (one tier stronger + one downside); pacts last while you
  keep fighting. Reroll by ad, seal a pact with gems, a pass perk adds a 4th card.
- **New chapters:** each adds ONE wordless rule (blizzard / wildfire / rising water), a counter upgrade, 2
  enemies, a giant, 2 bosses and a titan variant, plus a new gacha tower and a skin as rewards.

## What made them land
- **Rules, not stats.** "Any card can be flipped to a cursed side" is a decision. "+10% damage" is not.
- **One new rule per chapter, taught without words.** The rule fires once with a golden cue in the world
  (the **game-ui-kit** skill, wordless FTUE).
- **The sink is in the design from the start:** the reroll, the seal, the fourth card. And so is what is not
  sold.
- **A default for every open choice.** The producer edits the list; nothing waits for an answer.

## Caption rules for the board
- **Number · what happens,** then one line of *why*.
- Present tense, the player as the subject: "3 · Tap the chest · three pacts fan out".
- If the art is a placeholder (CSS shapes, emoji), say so once on the board.
