# Economy lessons that cost a day each

## The short list
- **Progression must pay premium currency, not soft currency,** or it pulls chapters forward. Soft currency
  buys power, so a rank reward of coins makes the next stages easier than planned.
- **Checkpoints must not keep the whole run build.** A checkpoint that restores every upgrade turns the rest
  of the chapter into a walk.
- **"Push on" is a trap unless the payoff is real; measure it.** Run the bots through "continue right after
  a clear" and check they can win it. If they can't, the button is a way to lose.
- **Longer waves add gold per stage,** so bots need fewer tries and the chapter gets *shorter*. Hold gold per
  stage when you stretch time.
- **A tuning agent must not edit UI files;** give it data files and the sim.

## One full pass, as a worked example
The producer on a preview build: "too easy" (aim: 60–70% of the difficulty of an older version), the first
stage trickles for 30–40 s, too many coins, gifts for players who never fell, bosses fall too easily, pierce
is cheap and essential.

What changed, all in tables:
- Stage multipliers across the chapter raised (up to ×3.66 at stage 7).
- The first wave brings 25 bodies, one a second (was 9, one every 3 s). That fixed "boring first minutes".
- Battle gold ×0.62.
- Boss HP ×1 / ×2 / ×3 from stages 1 / 2 / 3; the titan's HP more than doubled.
- The welcome gift only with a fall.
- Pierce keeps full damage per body and gets a steep price ladder (300 · 600 · 1,200 · 2,400 · 12,000).
- A 60-gem rank reward moved three ranks later (swapped with a coin boost).

What the bots said (6 seeds, tries per chapter with the 5-per-stage cap):
- casual human 15 → 27 (the old reference: 37.5), so 53% of the way back;
- novice 10 → 15 (30%); playtest bot 13 → 17 (21%);
- premium currency by the chapter clear: 90–102; bosses stand 16–32 s;
- first siege in a real browser: 3 of 3 won with walls 18–61%.

What stayed open, and was said so: two bots stayed under the 60–70% target because the casual human hits the
5-try cap first. That is the difficulty-index trap from the SKILL: move strong players with changes that
scale with their power, not with a flat multiplier.

## Smaller things worth knowing
- **A mini-boss inherits a boss's pay** if it reuses the boss role (premium currency, the drop, pass and goal
  counters). Set its pay on purpose.
- **Count the price of a crowd answer in tries.** Pierce was worth 5 tries (about 9 minutes) of a chapter.
  That number is how you price it.
