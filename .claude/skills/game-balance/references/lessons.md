# Balance lessons that cost a day each

## The short list
- **Tune count and pressure shape, not HP alone.** A shot-limited weapon doesn't care how soft the bodies
  are; fewer, tougher bodies fixed a first fight that HP cuts could not.
- **The weakest bot hits the try cap first.** Past that point a global multiplier only widens the gap; move
  strong players with changes that scale with their power.
- **Longer waves add gold per stage,** so the chapter gets shorter. Hold gold per stage when stretching time.
- **A fix that makes the game behave as designed shifts balance.** Measure before and after on the same seeds.
- **A tuning agent must not edit UI files;** give it data files and the sim.
- **A bot that never falls measures nothing.** Keep it in the table as a floor; don't tune with it.

## One full pass, as a worked example
The producer on a preview build: "too easy" (aim: 60-70% of the difficulty of an older version), the first
stage trickles for 30-40 s, too many coins, bosses fall too easily, pierce is cheap and essential.

What changed, all in tables:
- Stage multipliers across the chapter raised (up to x3.66 at stage 7).
- The first wave brings 25 bodies, one a second (was 9, one every 3 s). That fixed "boring first minutes".
- Battle gold x0.62.
- Boss HP x1 / x2 / x3 from stages 1 / 2 / 3; the final boss's HP more than doubled.
- Pierce keeps full damage per body and gets a steep price ladder (300 · 600 · 1,200 · 2,400 · 12,000).

What the bots said (6 seeds, tries per chapter with the 5-per-stage cap):
- casual human 15 → 27 (the old reference: 37.5), so 53% of the way back;
- novice 10 → 15 (30%); playtest bot 13 → 17 (21%);
- bosses stand 16-32 s;
- first fight in a real browser: 3 of 3 won with walls 18-61%.

What stayed open, and was said so: two bots stayed under the 60-70% target because the casual human hits
the 5-try cap first. The next levers were the ones that scale with the player's power: the boss tap
multiplier (x0.35) and an armour phase at half health.

## Smaller things worth knowing
- **Count the price of a crowd answer in tries.** Pierce was worth 5 tries (about 9 minutes) of a chapter.
  That number is how you price it.
- **The sim must count what the live game pays.** One did not count the boss drop at first, so its gold was
  not the player's gold.
- **Share one tuning source:** the sim imports the game's tables, never a copy.
- **Hash the sim after performance work.** Same seed, a few thousand steps, old and new: identical hashes
  mean every balance table still stands.
