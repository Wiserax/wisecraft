# Profiles, day rollover and robustness

## Profiles to cover
| Profile | How to set it up | What it catches |
|---|---|---|
| A brand-new player (EN 390 and ES 320) | fresh browser profile | the first session, the tutorial, overflow in Spanish on a small phone |
| A returning player from older version saves | load a real player's save of each older version into storage before boot (a fixture only where none exists) | migrations, grants paid twice, missing fields |
| A mid-game save | a real save, else a fixture | the hub with every rail unlocked, mid-chapter balance |
| A late-game save into the next chapter | a real save, else a fixture | chapter clear, the celebration, the next chapter's start |
| A spender (gacha ×10, star-ups, pass) | a real spender's save, else debug grants in a local build | sinks, premium UI, caps |
| WebKit | the same journeys in WebKit | audio start, CSS and touch differences |

Real data first: real players' saves from the live build and real devices are the best profiles. Keep one
fixture save per released version in the repo's test data only to fill the versions no real save covers.

## Day rollover
Return on day 2 / 7 / 8 by overriding `Date` (or a fake clock, paused and advanced): dailies, weeklies and
pass roll over; nothing grants twice after a reload.
- Day 2: the daily login and daily goals reset.
- Day 7: the weekly edge.
- Day 8: the first day of the second week, where off-by-one errors live.
- After each jump, reload and check the wallet did not change.

## Robustness
- Rotate mid-siege.
- Hide the tab for 30 s (`visibilitychange`), then return.
- Spam double-taps on claim, buy and open buttons.
- Reload mid-gacha, and mid-celebration: rewards must be paid once, the instant the run ends.
- Boot with a file failing or hanging (the **game-performance** skill has the fault matrix).

## Driving rules
- Tap the field like a player; tap dock cards in dock order; open modals by their own buttons.
- `window.__game` may speed time or set up a profile. It never wins the fight.
- One port range and one browser profile folder per agent, so parallel runs don't share storage.

## What a release QA pass reported, as a size guide
Old saves from the previous major version migrated cleanly in 4 profiles and both engines; 8 of 8 journeys
passed; 8 of 8 feature walkthroughs in EN and ES; 60 fps at the stress count. That is about the scope to
aim for before a release.
