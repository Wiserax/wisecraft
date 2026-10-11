# Economy and difficulty

## Contents
1. Player models and the difficulty index
2. Stage and chapter curve
3. Bosses, mini-bosses, titans
4. Economy budgets and sinks
5. Rescue systems
6. Sim ↔ browser agreement
7. Lessons that cost us a day each

## 1. Player models (simulate them all, 6+ seeds each)
| Model | Behaviour | Typical target |
|---|---|---|
| A passive | taps only, buys nothing | falls at the mid-stage mini-boss; the retry (with the gift) is winnable |
| B tutorial follower | buys what the tutorial points at, ~1 buy / 10 s | wins the first stage with walls ending 20–50% |
| C producer-like / heavy tapper | taps ~2/s, buys the first affordable Attack card every ~5 s | wins, but dips below 75% walls at each boss; boss lasts 25–35 s |
| D efficient | balanced attack + defence, buys every chance | wins comfortably (≥ 70%) |
| novice / average / casual-human | campaign bots for chapters | casual human ≤ 4–6 tries per stage, novice falls a few times per chapter |

**Difficulty index:** tries to clear stages 1–10 per bot, each stage capped at 5. Compare against a reference version (100%). When the producer says "60–70%", compute it this way and report all three bots. The weakest bot hits the cap first, so a change that hits strong builds harder (boss tap multiplier, armour phases, threat scaled to fort power) moves strong players without walling weak ones.

## 2. Curve shape
- **Inside a stage (≈ 3 min, 10 waves):** a rising sine. Pushes on odd waves, breathers on even waves; a mid-stage mini-boss (wave 5), a boss wave at the end (horde ×2, a big boss). Something new to watch or buy at least every 5 s. Plot alive count *and* wall damage per 5 s: if wall damage is zero for the first minute, the opening is boring.
- **Across a chapter:** a sawtooth rising to stage 10, the hardest stage. Boss and titan stages are local peaks with a breather after.
- **First siege:** HP-gated (a basic enemy needs about 3 hits from the starting weapon) so the first upgrade is felt; the first card is affordable within about 5 s; no upgrades means you lose.
- Count × HP is the pressure. A low-damage start can't handle 30% more bodies *and* 3-hit HP; pick fewer, tougher bodies there.

## 3. Bosses
- Tiers: `{ scale, tier: "mini"|"boss", hpMul }` on one spawn API. The model, hit area, HP bar and presence follow scale. ×2 bosses need camera pull-back and must not hide the base (dither where they overlap it).
- Spawn at the field edge and walk in. Large bodies need collision that can't wedge (squeeze past scenery), and attack reach that scales with radius. Test: a scale-2 boss reaches the wall from every angle and deals damage.
- Taps vs bosses: ×0.35 on bosses, ×0.5 on minis (or an armour phase at 50% HP), otherwise heavy tappers delete them.
- Mini-boss pay: less than a boss (no premium currency); its drop is about 1.5 upgrades.

## 4. Economy
- Premium currency budget per chapter, e.g. Chapter 1 ≈ 20–100 gems in total. Count every source (ranks, camo goals, events, drops) and check after every balance change.
- Battle gold must feel tight: "too generous in coins" is a real complaint. Upgrades should be choices, not a queue.
- **Sinks:** gacha towers (the Vault: free first open, 1 free per day, a paid open around 60 gems, a cap on power), cosmetics, and later pick-1-of-3 pacts.
- Crowd answers (pierce, splash) are essential, so price them as deliberate buys. Cap pierce at L5 with a top-tier L5 price, and keep full damage per pierced body.

## 5. Rescues
- Gifts and blessings only after a fall. A blessing helps (×1.5 damage, ×1.75 walls), it doesn't auto-win.
- A gift follows the stage being played; it never pops over a win screen.

## 6. Sim ↔ browser
- After any early-game change, run 3+ real-browser first sieges with the playtest bot. If the sim says won and the browser says lost, find the behaviour difference (what the bot buys, taps, events active) before tuning more.
- Report per-wave tables: alive mean and peak, gold earned and spent, buys, walls at wave end, boss time under fire.

## 7. Lessons
- Progression must pay premium currency, not soft currency, or it pulls chapters forward.
- Checkpoints must not keep the whole run build.
- "Push on" is a trap unless the payoff is real; measure it.
- Longer waves add gold per stage, so bots need fewer tries and the chapter gets *shorter*. Hold gold per stage when you stretch time.
- A tuning agent must not edit UI files; give it data files and the sim.
