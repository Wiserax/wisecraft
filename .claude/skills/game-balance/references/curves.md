# Curves: waves, HP, DPS and prices

Arithmetic first, then bots, then a browser. The formulas below give a table a shape before anything runs;
they never replace a measured run.

## The quantities
| Name | Formula | Read it as |
|---|---|---|
| Enemy HP at wave w | `hp(w) = hp0 x g^(w-1)` | g = 1.08-1.15 per wave inside a stage |
| Count at wave w | `n(w) = n0 x c^(w-1) x (1 + a x sin(pi (w - 0.5)))` | the sine term pushes odd waves up and lets even waves down by `a` |
| Pressure | `P(w) = (n(w) x hp(w) + boss HP) / wave_seconds` | HP arriving per second |
| Player DPS | `D(k) = D0 x d^k` at upgrade level k | d = damage gain per level, e.g. 1.2 |
| Coverage | `D / P` | below 1.0 the horde piles up; well above 1.5 nothing threatens |
| Time to kill one enemy | `hp / (damage per hit x hits per second)` | the first enemy should take about 3 hits from the starting weapon |
| Boss time under fire | `boss HP / (D + tap DPS x tap multiplier)` | the per-model target, e.g. 25-35 s for the heavy tapper |
| Price of level n | `price(n) = base x r^n` | r = 1.3-1.6 for power; a crowd answer's top level gets its own price |
| Levels affordable by wave w | the largest k with `sum(price(0..k-1)) <= gold earned by w` | where income and the ladder meet |

Coverage is the one to plot. A designed stage moves around 1.0: pushes under it, breathers over it, a boss
wave as the low point that walls and taps must absorb.

## A worked stage
`scripts/curves.py assets/curves.template.json`: 10 waves of 18 s, enemy HP 3 growing x1.12, 14 bodies
growing x1.08 with a 0.3 sine, a mini-boss at wave 5 (x25 HP) and a boss at wave 10 (x60 HP); the player
starts at 3 DPS, +22% per level, prices 10 x 1.4^n, 1 gold a kill.

```
wave count      hp boss  HP/s in   gold lvl   next     DPS DPS/in
   1    18     3.0           3.0     10   1     14    3.66   1.22
   2    11    3.36          2.05     28   2     20    4.47   2.17  <- nothing threatens
   3    21    3.76          4.39     39   2     20    4.47   1.02
   4    12    4.21          2.81     60   3     27    5.45   1.94  <- nothing threatens
   5    25    4.72  yes    13.11     72   4     38    6.65   0.51  <- piles up
   6    14    5.29          4.11    118   5     54    8.11   1.97  <- nothing threatens
   7    29    5.92          9.54    132   5     54    8.11   0.85  <- piles up
   8    17    6.63          6.26    161   5     54    8.11   1.29
   9    34    7.43         14.03    178   6     75    9.89   0.71  <- piles up
  10    20    8.32  yes    36.97    212   6     75    9.89   0.27  <- piles up
```
What it says, before any bot:
- **The sine works:** coverage alternates 1.22 / 2.17 / 1.02 / 1.94; the even waves are spending windows.
- **The breathers are too soft:** 1.9-2.2 on even waves is "nothing threatens". Lower `amp` or raise the
  even-wave floor.
- **The ladder outruns income late:** prices 10, 14, 20, 27, 38, 54, 75, 105 against about 35 gold a wave.
  The player sits at level 5 from wave 6 to 8 while HP grows 25%. With r = 1.25 (10, 12, 16, 20, 24, 31, 38,
  48) the player reaches level 8 by wave 10 and coverage there rises from 0.27 to 0.40.
- **The final boss is the cliff:** 0.27 means about 67 s to burn the wave at turret DPS alone, against an
  18 s wave. Taps, walls and the mini-boss's drop must carry it, or `hp_mul` comes down (x30 gives 0.43).

Then the bots decide. Arithmetic ignores targeting, overkill, walking time, walls and taps; a coverage of 0.5
can be a fine boss wave when the walls hold for 40 s.

## Across a chapter
- **A sawtooth:** stage multipliers rise to stage 10; boss stages are local peaks with an easier stage after.
- **Stage multipliers apply to HP and count separately.** Raising only HP keeps the screen empty; raising
  only count can outrun a shot-limited weapon (see `sim-vs-browser.md`).
- **The worked pass in `lessons.md`** raised stage multipliers up to x3.66 at stage 7, cut battle gold to
  x0.62 and moved bosses to x1 / x2 / x3 HP over stages 1 / 2 / 3.

## Price ladders, in practice
- Start from what one level is worth: its DPS gain in seconds saved per wave, or in tries saved per
  chapter. Price it against the gold a player has at the wave you want it bought.
- One ladder per kind of upgrade: power (r 1.3-1.6), utility (flatter), crowd answers (a steep top level).
- Check affordability per model: the casual bot should afford its first card within about 5 s of the first
  fight, the attentive bot should never sit on more than one unspent level of gold.
- After a price change, run the bots on the same seeds and report gold earned, gold spent and unspent gold
  at each wave end, per model.
