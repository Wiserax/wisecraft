# The publisher lens: will it ship, and is it worth testing?

A studio that ships a prototype a week can't afford designs that are fun but untestable, too big for the
deadline, or me-too. Answer these before building. The publisher reviewer in **player-panel.md** asks the
same questions; answer them yourself first, then compare.

## 1. USPs: the reason to install
- At most 3, ranked. Each one fits in **one ad line** and one 3-second shot.
  - Good: "You become what you kill: your hero grows the claws of every monster it beats."
  - Weak: "30 skills" (a stat, not a hook).
- The test: describe the 3-second ad. If you can't, there's no hook yet.

## 2. The market
- Name the 3-5 closest games. For each feature, say whether it is **differentiated** or **me-too**.
- Me-too features are fine as the frame (the joystick shooter is known); the USP must sit on top.

## 3. The pillars
- The 3 things the prototype must nail. Everything else is cut or faked.
- Write the **non-pillars** explicitly; the scope fight is easier when they're named up front.

## 4. Scope to the deadline
- **MUST / SHOULD / LATER,** sized in days against the real team (agents + producer).
- The **smallest build that tests the hypothesis** goes first; it must be playable by day 2 of 3.
- Fake whatever isn't the hypothesis: bots instead of netcode, a static shop, a still result screen.
- Plan per day with a playable build at the end of each day; the last day is QA, analytics, the trailer and
  the deploy (the **game-qa**, **game-trailer** skills).

## 5. The test: hypothesis, events, thresholds
- One sentence: "Players who see X keep playing because Y."
- **Events:** the session and run start/end, each choice (with its id), each fail (with its cause),
  placement or score, ad offers and watches, the tutorial steps. Add the release field.
- **Go/kill thresholds,** set before the test, e.g.:
  - D1 ≥ 35% (go), 25-35% (iterate), < 25% (kill);
  - median session ≥ 8 min;
  - ≥ 3 runs per user on day 0.
  Use the studio's real benchmarks when you have them (the **game-meta** skill reads real data).

## 6. Scalability: is it a live game?
- The content unit (a family, a hero, a biome, an event) and its cost in days.
- The cadence it allows (e.g. a new family every 2 weeks).
- Monetisation that fits: cosmetics, re-rolls, a pass. Say what's **not sold**.
- **Policy risk:** bots presented as players, odds disclosure, ads aimed at children. Bots are fine when
  they're labelled in the store text; never claim "real players" in an ad.

## 7. Risks, ranked, with mitigations

## 8. The verdict
Green-light / green-light with changes (list them) / kill. A kill is a valid, cheap outcome on day 1.
