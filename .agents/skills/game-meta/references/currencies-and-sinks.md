# Currencies, faucets and sinks

An economy is a ledger: what comes in (faucets), what goes out (sinks), and what the player holds in
between. Write it down per kind of player before tuning a single price, and check it with
`python3 scripts/economy_ledger.py`. The worked example at the end is the real output on
`assets/economy-model.template.csv`.

## 1. One job per currency
| Currency | Example | Its job | Rules |
|---|---|---|---|
| Run currency | battle gold | choices inside one run | resets every run; must feel tight; upgrades are choices, not a queue |
| Soft | coins | permanent power | earned by playing; the main sink is power; inflates first |
| Hard / premium | gems | time, choice, cosmetics, the gacha | bought with money and earned slowly; budget it per chapter |
| Event | tokens | one event's track and shop | expires; leftovers convert at a published rate, never vanish silently |
| Progress items | shards, XP | unlocks and star-ups | fed by duplicates and the pass |
| Energy | stamina | session pacing | avoid unless sessions must be capped; it gates the players you most want to keep |

Two rules that cost a day each in a shipped horde tower defense:
- **Progression pays premium currency, not soft.** Rank rewards paid in coins bought power, so the next stages
  became easier than planned and chapters went faster. A 60-gem rank reward swapped with a coin boost fixed
  it.
- **Battle gold must feel tight.** "Too generous in coins" was a real complaint: battle gold went to ×0.62.
  When the player can buy everything that lights up, there are no decisions.

## 2. The daily earn budget
For each currency and each kind of player (light: 1 session a day, engaged: 3, heavy: 6+), write what a day
pays from every source. Then decide what that buys:
- **Soft:** the next meaningful upgrade every session; a "big" buy every 2-3 days.
- **Premium:** about one paid gacha open a day for an engaged player, or one pass tier skip a week; a
  premium item reachable for free in 2-4 weeks. Faster and the shop sells nothing; slower and free players
  feel locked out.
- **Count every source:** ranks, daily goals, chapter clears, events, drops, the free daily pull, the pass,
  ads. The shipped game budgeted chapter 1 at 20-100 gems in total and measured 90-102 gems at the clear
  after a pass that moved rewards around: recount after every balance change, because rewards hide in many
  tables.
- **A mini-boss inherits a boss's pay** when it reuses the boss role in code (premium currency, the drop,
  pass and goal counters). Set its pay on purpose: less than a boss, no premium currency, a drop worth about
  1.5 upgrades.

## 3. Price ladders
A level-based price is `price_L = base × r^(L-1)`; the total for n levels is `base × (r^n - 1) / (r - 1)`.

| r | Level 10 price (base 100) | Total for 10 levels | Level 10 / level 1 | Use |
|---|---|---|---|---|
| 1.15 | 352 | 2,030 | 3.5× | long idle curves where income also grows exponentially |
| 1.35 | 1,489 | 5,459 | 14.9× | a typical upgrade card |
| 1.6 | 6,872 | 18,159 | 68.7× | few levels, each one a decision |

- **Match the ladder to income growth.** If income per session grows ×1.2 a chapter and prices ×1.35 a
  level, the time to afford the next level grows ×1.125 a level: that is the soft wall. Plot time-to-afford,
  not price.
- **Time to afford** = price / income per minute. Targets that worked: the first card in about 5 s of the
  first fight; the next meaningful upgrade every 30-90 s of a run; a permanent upgrade every session.
- **Step off the curve when value does not follow it.** A crowd answer (pierce) is worth little early and a
  great deal late. On the generic curve (150 · 278 · 513 · 949 · 1,756) its last level was bought without a
  thought; with an explicit list (300 · 600 · 1,200 · 2,400 · 12,000) the early levels stay reachable and the
  last one sits next to the dearest late buys (11,000-17,000), against a late session's income of about
  4,000-5,000. See the note
  [the top level of a crowd-answer upgrade needs its own price](../../../knowledge/games/horde-tower-defense-mobile-web/the-top-level-of-a-crowd-answer-upgrade-needs-its-own-price.md).
- **Price an essential upgrade in tries.** Run the same bot and seeds with the upgrade removed (an
  ablation). Pierce was worth 6.5 tries (23 % of the chapter) before its reprice and 5 tries (about 9
  minutes, 12 %) after. That number, not the gold figure, is what the price buys.

## 4. Exchange rates and the value of time
**Gem packs** set the real-money value of a gem. A common ladder:

| Pack | Price | Gems | Gems per dollar | Bonus over the smallest |
|---|---|---|---|---|
| Handful | 0.99 | 80 | 80.8 | |
| Pouch | 4.99 | 500 | 100.2 | +24 % |
| Chest | 19.99 | 2,200 | 110.1 | +36 % |
| Vault | 99.99 | 13,000 | 130.0 | +61 % |

Rising value per dollar rewards bigger packs without making the small one feel like a trap. Price every gem
sink against the pouch rate (about one cent a gem here), and show the real-money price of a gem offer when
it is shown in gems.

**Time skips** cost less per hour the longer the wait (a concave curve). A common shape, interpolated linearly
between anchors: 1 min = 1 gem, 1 h = 20, 1 day = 260, 1 week = 1,000. A 3-hour wait then costs 41 gems, 8
hours 93, 2 days 383. Skipping is a convenience; a game whose main sink is skipping waits it created is a
dark pattern (see `ethics-and-rules.md`).

**Soft to premium:** never sell premium for soft. Selling soft for premium is fine at a rate worse than
earning it (so gems are not the cheap way to power).

## 5. Inflation and dead sinks
- **Inflation:** the soft balance grows faster than anything can absorb it, so prices stop meaning
  anything. It starts when the main sink caps out (early towers at max level) while income keeps rising.
  The cure is a sink that scales with the player (star-ups, higher tiers, a rotating coin shop), not a cut to
  income players already have.
- **Dead sink:** something that takes almost none of the spending. Either make it worth buying, price it for
  the players who do buy it, or remove it from the soft economy (cosmetics often belong in premium).
- **Hoarding premium is normal:** players save gems for a pull or a pass. Check premium for debt (a plan that
  spends gems the player cannot have) and for budget, not for saving.
- **Run currencies don't inflate** but they leak: longer waves pay more gold per stage, so bots need fewer
  tries and the chapter gets shorter. Hold gold per stage when you stretch time.

## 6. Worked ledger
The template is a 7-day plan for an engaged player (3 sessions a day). Run:
```
python3 scripts/economy_ledger.py assets/economy-model.template.csv --soft coins --budget gems=40-90
```
```
coins
  period      faucet      sink       net   balance   kept
  D1           2,300     2,100       200       200     9%
  D2           3,250     2,900       350       550    11%
  D3           4,200     3,650       550     1,100    13%
  D4           5,150     3,900     1,250     2,350    24%
  D5           6,100     3,650     2,450     4,800    40%
  D6           6,850     3,300     3,550     8,350    52%
  D7           8,100     3,050     5,050    13,400    62%
  sources: battle rewards 80%, daily login 8%, chests 12%
  sinks:   tower upgrades 99%, cosmetics 1%

gems
  period      faucet      sink       net   balance   kept
  D1              50         0        50        50   100%
  D2              65        70        -5        45    -8%
  ...
flags:
  coins D5: saving: keeps 40% of what came in (limit 30%)
  coins D6: saving: keeps 52% of what came in (limit 30%)
  coins D7: saving: keeps 62% of what came in (limit 30%)
  coins D7: growing: the balance rose in each of the last 7 periods and holds 13,400, more than a period's spending (3,050)
  coins all: dead sink: cosmetics takes 0.7% of the spending
```
Reading it: from day 5 the early towers hit their max level, coin spending falls from 3,900 a day to 3,050
while battle rewards keep rising, and by day 7 the player holds 13,400 coins with nothing to buy. The gem plan
holds: the free first open and the free daily opens cover the days the balance would dip, and every day's
faucet sits inside 40-90.

**The fix, tested in the same ledger:** add tower star-ups as a coin sink from day 4 (900, 2,000, 3,000,
4,000). The kept share falls to 7 %, 7 %, 8 % and 13 % on days 4-7, the balance ends at 3,500 (less than a
day's spending of 7,050), and the saving and growing flags clear. Cosmetics still take 0.5 %: move them to
gems or drop the coin price. Then prove the new sink with the bots (**game-balance**): star-ups are power, so
they move the difficulty index.
