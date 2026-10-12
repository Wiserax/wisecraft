# Shop, offers, the season pass and ads

Every price in a shop is read against the others. Set one reference rate (gems per dollar of the mid pack),
value everything in it, and make the ladder obvious. Figures below are worked examples, computed from the
gem-pack ladder in `currencies-and-sinks.md` (the 4.99 pouch: 500 gems, about 100 gems per dollar).

## 1. Shop layout
- **Top:** one featured offer (the starter pack, then the current event offer). One golden call to action
  per screen; the **game-ui-kit** skill has the hub rules.
- **Then:** the gacha (with its odds one tap away), gem packs, coin packs, cosmetics.
- **Prices in local money from the store,** never typed by hand; gem prices next to an estimate in money
  when the item is premium.
- **Ownership is visible:** a bought one-time offer disappears; an owned cosmetic says so.
- A shop that opens with three popups before the shop is a shop players learn to close.

## 2. Price points and anchors
Standard store tiers: 0.99, 1.99, 4.99, 9.99, 19.99, 49.99, 99.99. Use 4-6 of them.
- **Value per dollar rises with the pack** (80.8 → 100.2 → 110.1 → 130.0 gems per dollar in the example).
- **An anchor:** the big pack next to the mid pack makes the mid pack read as sensible. Mark one pack "most
  popular" only if it is, from the data.
- **First-purchase bonus:** double gems on the first buy of each pack. It turns a non-payer into a payer at
  the moment that matters most, and costs nothing on later buys.

## 3. The starter pack
- One time only, 0.99-4.99, shown after the first meaningful moment: the first chapter clear or the first
  fall, never in the first 30 seconds.
- Its value is 3-6 times the pouch rate, and says so honestly. Worked example at 1.99: 300 gems + an epic
  tower (160 gems in the gacha table) + 10,000 coins (worth 200 gems at the coin-pack rate) = 660 gems of
  value. At the pouch rate 1.99 buys about 199 gems, so the pack is 3.3×.
- It never contains the only answer to a wall. A starter pack that is required is a paywall.
- It expires with a real timer (48-72 h from first show) or not at all. A timer that resets is a fake
  scarcity timer (see `ethics-and-rules.md`).

## 4. Offer triggers and cooldowns
| Trigger | Offer | Why |
|---|---|---|
| First chapter clear | starter pack | the player just learned the game is worth it |
| 3+ falls on the same stage | a power bundle for that stage, after the free rescue gift | the gift first: free help, then the option to pay |
| Gacha just missed the featured item | none | selling into frustration reads as predatory; show the pity counter instead |
| Return after 7+ days away | a comeback pack, mostly free | welcome back, then catch up |
| A new chapter or event starts | the event pass | the reason to spend is new content |

Cooldowns: one interrupting offer a session at most, none during a fight, none over a win screen, none in the
first session. Every offer has a "no thanks" as visible as the buy button. The rescue gift rules are in
`progression-and-retention.md`.

## 5. The season pass
A track of tiers earned with pass XP over a season (usually 28-35 days). A free track for everyone and a
premium track for buyers.

**Size it from play, not from a round number.** Worked example, 30 days, 40 tiers of 1,000 XP (40,000 XP):

| Player | Days played | Daily XP (dailies + battles) | Weekly quests | Total XP | Tier reached |
|---|---|---|---|---|---|
| Engaged | 26 of 30 (87 %) | 700 + 300 = 1,000 | 4 × 3,500 = 14,000 | 40,000 | 40 (done on the last days) |
| Regular | 18 | 700 + 200 = 900 | 2 × 3,500 = 7,000 | 23,200 | 23 |
| Light | 12 | 350 + 150 = 500 | 1 × 3,500 | 9,500 | 9 |

- **Target:** an engaged player (plays 80-90 % of days) finishes in the last week; a regular player reaches
  about half. If the engaged player finishes in week 2, the pass is too cheap; if never, it feels like a scam.
- **Catch-up:** pass XP ×2 while a player is more than 5 tiers behind the day-based pace (day / 30 × 40).
  It makes buying late reasonable and keeps returning players in.
- **Tier skips** at a gem price near the value of one day of pass XP; capped so the pass can't be bought
  outright on day 1.
- **Premium value:** 9.99 for 1,000 gems + 30 vault keys (60 gems each, 1,800) + 2 epic towers (320) + a skin
  = 3,120 gems of value, about 3.1× the pouch rate. Paying back about the price in gems lets an engaged
  buyer renew from the pass alone, which is the loop that keeps them.
- **The free track** gets something every 2-3 tiers and one strong item mid-way, so free players see the
  premium track's value instead of being excluded from the pass.
- Nothing on the premium track is the only answer to a wall.

## 6. Subscriptions
A monthly card: for example 4.99 for 100 gems a day for 30 days (3,000 gems, 6× the pouch rate), collected
by logging in. It rewards habit; show clearly when it runs out and never auto-renew outside the store's own
subscription system.

## 7. Rewarded ads (opt-in only)
- **Placements that work:** double the reward of a run that just ended; one revive a run; one free gacha key
  a day; skip a short wait.
- **Caps:** 5-10 rewarded views a day. A view is worth about 5-15 % of a day's premium budget.
- **Never** an interstitial during a fight, never an ad the player did not ask for in exchange for a reward,
  never an ad inside the first session.
- For a web game the ad SDK depends on where it is hosted (a portal's SDK, or a web ad network). Test with the
  network's test ads; a real ad view is a real transaction in the agent's rules (ask first).

## 8. What to measure after shipping a shop change
Store opens per daily user, offer shown → bought rate per trigger, first-purchase conversion, ARPPU by pack,
refund rate, and the guardrails: D1/D7 retention and session length must not drop. Read
`tuning-from-data.md` for the events and the test design.
