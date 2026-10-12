# Ethics, odds disclosure and the rules around paid randomness

Monetization that players trust earns longer. Monetization that tricks them earns refunds, reviews, store
removals and, in some countries, fines. This file lists the practical rules.

**Not legal advice.** Laws and store policies change; the points below are a summary as of 2026. Check the
current text for every market the game ships in, and say in the report which rules were checked and when.

## 1. Odds disclosure: do it everywhere
Disclosing the odds of every paid random item, before purchase, is required by the major mobile stores and by
law in several countries. Treat it as the default for every game, web included.

| Where | What applies (summary) |
|---|---|
| Apple App Store | the review guidelines require apps offering loot boxes or other paid random items to disclose the odds of each item type before purchase (since late 2017) |
| Google Play | its payments policy requires the same disclosure for randomized items bought with real money or with currency bought with real money (since 2019) |
| China | random-draw odds must be published (Ministry of Culture rules from 2017), with later rules on minors' play and spending |
| South Korea | probability disclosure for paid random items became a legal duty in March 2024 (amended game industry law), with enforcement and fines |
| Japan | "kompu gacha" (complete a set of random items to win a prize) was ruled an illegal premium in 2012; industry guidelines cover disclosure and spending limits for minors |
| Belgium | the gaming regulator found paid loot boxes to be gambling in 2018; publishers removed or disabled paid random items there |
| Netherlands | a 2018 regulator finding was later overturned in court (2022); the debate continues |
| Ratings | ESRB and PEGI add "In-Game Purchases (Includes Random Items)" to games that sell paid random items (since 2020) |
| UK, Australia, EU | UK industry principles (2023) cover disclosure and parental consent for under-18s; Australia's classification rates games with paid loot boxes at least M from late 2024; EU consumer authorities published principles on in-game currencies (show real-money prices, no misleading pressure) |

What a good disclosure has (the format is in `drop-tables-and-gacha.md`, section 8):
- the chance of every tier and every item, base and consolidated with the guarantee;
- the pity rule in words, whether the counter carries over, and what duplicates become;
- the same numbers the code uses: `scripts/drop_table.py` fails when they differ. Put it in the tests.

## 2. Dark patterns the agent does not build
If asked for one of these, the agent says why it is a problem and offers the honest version.

| Pattern | Honest version |
|---|---|
| A countdown that resets ("only 2 h left!" every day) | a real end time, or no timer |
| Confirm-shaming ("No, I like losing") | "No thanks" |
| Hiding the real-money price behind several currencies | show an estimate in money next to premium prices |
| Odd pack sizes so a player always has leftover gems | packs that match the prices of what they buy |
| Waits created to sell their skips as the main sink | waits as pacing, skips as convenience |
| Paid random items with no pity and no odds | disclosed odds and a guarantee |
| Offers right after a near-miss in the gacha | show the pity counter; no offer |
| Pay-to-win against other players with no cap | a power cap, or matchmaking by power |
| A paid answer that is the only way past a wall | a free path within one or two sessions |
| Pre-checked "buy again" or one-tap buys of large amounts | confirm big purchases; no pre-checked boxes |
| Silent resets of a pity counter | counters that carry over and are shown |

## 3. Minors and spending
- Ask the age where the store or platform doesn't, and apply the stricter defaults to minors: monthly spend
  caps, no paid random items without parental consent where the rules ask for it, no personalised offers.
- Spending caps per day or month for everyone are a good product, not a loss: they protect the players whose
  refunds and complaints cost the most.
- Children's data has its own rules (for example COPPA in the US and the GDPR's rules on children in the
  EU). Analytics on minors is a question for the producer before it ships.

## 4. Refunds and fairness
- Purchases go through the store's billing; listen to its refund notifications and reverse what a refunded
  purchase granted (unspent premium currency first).
- Grants are idempotent: one purchase, one grant, whatever the network or the taps did (keyed on the store's
  transaction id; see the reward rule in `progression-and-retention.md`).
- Restoring purchases on a new device works for non-consumables and subscriptions.

## 5. What the agent itself never does: spending money needs a yes
- **Never completes a real purchase,** a real ad view, a subscription or a store checkout, in any build. Test
  spender profiles with debug grants in a local build, the store's sandbox or test accounts, and the ad
  network's test ads.
- **Never turns on a paid service** (paid analytics, paid asset generation, a paid plan, paid agent runs)
  without the producer's explicit yes in this session.
- **Never changes live prices, live offers or a live drop table** without the producer's yes; it prepares the
  change, the numbers and the test plan.
- **Real data first, and never faked:** no invented analytics, no fake reviews, no fake "players are buying
  this" notices.
