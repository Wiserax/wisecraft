# Drop tables, chests and gacha

A drop table is a promise about money and time. Compute what it gives before anyone tunes by feel, and
publish the same numbers the code uses. Every number in this file comes from
`python3 scripts/drop_table.py assets/drop-table.template.json` (the template is an example vault chest).

## 1. Structure: tiers first, items inside tiers
Roll the tier, then the item inside the tier. Two small tables are easier to reason about, disclose and
change than one flat list of 40 items.

| Field | Meaning |
|---|---|
| `weight` (integer) | tier probability = weight / sum of weights. Use a round sum (10,000) so percentages read straight off |
| `items[].weight` | probability inside the tier; item probability = tier × item weight / tier item weights |
| `value` | what one drop is worth in one unit (the hard currency is the usual choice) |
| `pity` | the tier that has a guarantee, and its ramp |
| `featured` | the item on the banner and its share of the pity tier (the 50/50) |
| `duplicates` | what a repeat converts into, and the spark cost |

Template rates: common 70.4 %, rare 23 %, epic 6 %, legendary 0.6 %. Inside legendary the three towers are
0.2 % each.

**Rarity tiers that work:** 3 to 5 tiers. Each step up is roughly 3-10 times rarer and 3-8 times more
valuable. A top tier under about 0.5 % without pity is a lottery, not a reward: see section 3.

## 2. Without pity: the geometric tail
With a fixed rate p per pull:
- mean pulls to the first hit = 1 / p;
- P(at least one in n pulls) = 1 - (1 - p)^n;
- pulls for a chance q = ln(1 - q) / ln(1 - p).

For p = 0.6 %: mean 166.7 pulls. P(one in 100) = 45.2 %. Median 116 pulls, 90th percentile 383, 99th
percentile 766. One player in a hundred pays 4.6 times the mean. That tail is what players remember and
what regulators look at; pity exists to cut it.

## 3. Pity: soft ramp and hard guarantee
Count pulls since the last drop of the pity tier (k = 1, 2, ...). The rate on pull k:

```
p_k = base                                 for k < soft_start
p_k = min(1, base + soft_step * (k - soft_start + 1))   for soft_start <= k < hard
p_k = 1                                    for k = hard
```
P(first hit on pull k) = p_k × Π(1 - p_j) for j < k. The mean is Σ k × P(k), and the **consolidated rate**,
the long-run share of pulls that give the tier, is 1 / mean. That is the number to disclose next to the base
rate.

Template: base 0.6 %, soft pity from pull 60 at +6 % a pull, hard pity at 75. The rate is 6.6 % on pull 60,
42.6 % on pull 66, 66.6 % on pull 70 and 90.6 % on pull 74.

| | Mean pulls | p50 | p90 | p99 | Consolidated rate |
|---|---|---|---|---|---|
| No pity | 166.7 | 116 | 383 | 766 | 0.6 % |
| Soft 60 + hard 75 | 53.1 | 62 | 66 | 69 | 1.882 % |

P(at least one legendary): 5.8 % in 10 pulls and 26.0 % in 50, the same with or without pity; 53.4 % in 62
pulls (31.1 % without) and 99.7 % in 70 (34.4 % without). Pity changes nothing for a light spender and
everything for the unlucky one.

Reading it:
- **Almost nobody reaches hard pity** in the template: the soft ramp catches them first (the share of drops
  that wait for pull 75 rounds to 0.00 %). The hard number is still the one to print; it is the promise.
- **Soft pity sets the mean, base rate sets the early luck.** To make the tier "feel" more common without
  changing cost, raise the base and push the ramp later; the mean barely moves.
- **The counter carries over** sessions and banners of the same pool, and is shown to the player. A counter
  that resets silently is a dark pattern (see `ethics-and-rules.md`).

## 4. The featured item and the 50/50
When the pity tier drops, it is the featured item with probability `rate` (usually 0.5). With the guarantee,
the next drop after a miss is the featured item for sure. Pulls to featured = one pity cycle (probability
0.5) or two cycles (0.5), so the mean is 1.5 cycles.

| Rule | Mean pulls | p50 | p90 | p99 | Worst case | Mean cost at 60 gems |
|---|---|---|---|---|---|---|
| 50/50 with the guarantee | 79.7 | 67 | 128 | 134 | 150 | 4,781 |
| 50/50, no guarantee | 106.2 | 67 | 202 | 390 | none | 6,375 |

The guarantee cuts the 99th percentile from 390 pulls to 134 and gives a worst case. Ship it.

## 5. Value per pull and the price
EV per pull = Σ P(tier) × value. Template: 37.71 gems at base rates, **52.71 gems with pity**, 87.8 % of the
60-gem price. Rules of thumb:
- EV with pity between about 70 % and 100 % of the price, counted in the same unit, for a box that sells. Over
  100 % and the box is the best item in the shop; every other offer is measured against it.
- Value the top tier by what it does for power or collection, then check the EV still makes sense. Changing
  the legendary's value from 1,800 to 1,200 moved the template from 106.7 % to 87.8 % of the price.
- A **free daily pull** pays about EV per day for nothing: 52.7 gems here. Count it in the premium budget.
- A **10-pull with a rare-or-better guarantee:** P(no rare or better in 10 pulls) = 0.704^10 = 3.0 %, so the
  guarantee fires on 3 % of 10-pulls and costs little. Offer it at the price of 10, not as a discount.

## 6. Duplicates, shards and the spark
Late in a pool most drops are duplicates. Without a conversion, pulls stop being worth anything.
- Each duplicate converts to shards by tier (template: 1 / 5 / 20 / 80).
- When everything is a duplicate, a pull gives 4.52 shards. A spark of 400 shards buys the featured item
  outright after 88.5 pulls of duplicates, about the 50/50 mean (79.7). That is the point: the spark
  protects collectors without being cheaper than luck.
- **Bad-luck protection for non-pity tiers:** cap the streak ("an epic at least every 20 pulls") with the same
  ramp formula. Disclose it the same way.
- **Duplicate protection** for small pools: remove owned items from the roll until the set is complete. It
  changes the item rates, so disclose "owned items are excluded".

## 7. The vault pattern from a shipped horde tower defense
- The first open is free and guaranteed good: it teaches the loop.
- One free open a day; a paid open around 60 gems; a premium budget that allows about one paid open a day for
  an engaged player (see `currencies-and-sinks.md`).
- A cap on power from the vault, so a spender is stronger but cannot skip the curve: chapters stay tuned for
  the free player. Prove it with the spender bot from the **game-balance** skill.
- Two taps on "open" must open one crate. Spend the gems and roll in one idempotent step keyed on an open id,
  and test the double tap in a real browser (the **game-qa** skill). A double tap opening two crates was a
  real bug.

## 8. The disclosure table
Put this on the screen before the purchase, one tap from the buy button, in the player's language:

| Tier | Chance per pull | With guarantee | Items |
|---|---|---|---|
| Legendary | 0.6 % | 1.88 % | Titan Tower 0.2 % (featured: 50 % of legendaries; the next legendary after a miss is Titan Tower), Storm Tower 0.2 %, Dragon Tower 0.2 % |
| Epic | 6 % | | Frost Tower 3 %, Mortar Tower 3 % |
| Rare | 23 % | | ... |
| Common | 70.4 % | | ... |

Plus, in words: the guarantee ("a legendary within 75 pulls"), whether the counter carries over, and what a
duplicate becomes. `drop_table.py` checks the disclosed base and consolidated percentages against the weights
and fails (exit 1) when they disagree: run it in the game's tests whenever the table changes.
