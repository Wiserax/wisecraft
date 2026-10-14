# <GAME>: design vN
**<The hook in one ad line.>** <Genre, opponents (real or bots), session length, the twist, in two sentences.>

## The run (matches board-vN.png)
1. **<Screen>:** <what the player does> · <what happens>
2. ...
↺ <Which steps repeat, how often, and what interrupts them.>

## Content for the deadline
- **MUST:** <the smallest build that tests the hypothesis: heroes, enemies, choices, meta, analytics, deploy>
- **SHOULD:** <...>
- **LATER:** <everything else, named so it doesn't creep back>

## Wordless signals
| Information | Signal (in the world first) |
|---|---|
| HP | |
| Progress / XP | |
| Timer | |
| Opponents left | |
| A choice | |
| An ad offer | |

## Test
- **Hypothesis:** players who see <X> keep playing because <Y>.
- **Events:** <session_start, load_complete, run_start, choice (id, t_ms), fail (cause), run_end (placement,
  duration), ad_offer/ad_watch, ftue_step>; release field; a persistent user id.
- **Go / kill:** D1 <…>, D0 playtime <…>, runs per user <…>, CTR vs a control creative <…>, the novel mechanic
  seen by <…>% within <…> s.
- **Hooks:** (1) … (2) … (3) …  Never claim real players if opponents are bots.

## Gates (a playable build at the end of every day)
- **Day 1:** <the novel mechanic playable>
- **Day 2 at 18:00:** <content freeze + perf check>
- **Day 3:** <QA, analytics, trailer, deploy, upload>

## Open choices (defaults chosen)
- <choice>: **<default>** (alternative: <…>)

## Panel log
| Round | Hardcore | Midcore | Casual | Non-reader | Publisher |
|---|---|---|---|---|---|
| v1 | | | | | |
| v2 | | | | | |
