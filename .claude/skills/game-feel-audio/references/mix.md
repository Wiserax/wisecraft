# The measured mix

How to fix "the boom is too loud" without hearing anything. Worked on a horde tower-defense mobile web game
(Vite + three.js, Web Audio).

## 1. Measure first
Nothing is listened to. The game runs in a muted Chromium with a zero-gain output. Record, as files:
- the full output;
- each bus (music, effects, ambience);
- one stem per sound family (boss death, mortar, claims, and so on).

Meter them (BS.1770 / EBU R128, the same numbers `wise loudness` prints). For each family, take the loudest
400 ms and compare it with the music's short-term level in the same scene.

Stage the scenes that matter with the debug hooks: a battle, a boss arrival and death, a titan slam, a
mortar volley, a claim, the hub. Eight captures covered the game here.

## 2. Read the table before touching a fader
The producer said the boss-death boom was far too loud. The table said something else:

| | Before |
|---|---|
| Battle music | -34.1 LUFS (14 dB under the -20 target) |
| Effect families over the +6 dB ceiling | 12 of 17 |
| Loudest offenders vs the music | a skill burst +19.0 dB, claims +15.6, boss arrival +12.1, boss death +11.5, titan slam +11.1, mortar +8.6 |
| Master compressor | never moved more than 0.4 dB |

The booms were not too loud in absolute terms. The music was too quiet, so every effect towered over it.
Turning the booms down alone would have left the whole game 14 dB under its target. And boss death was a rumble and a boom on
the same frame: two sounds summing.

## 3. The bus graph
`input → fixed trim → the player's slider → master`, for each of music, effects and ambience.
- The **fixed trim** per bus is where the mix lives. The player's slider defaults stay unchanged.
- One factor on all three trims moves the whole programme without touching the balance. Keep that knob.

On the effects bus, in front of the trim:
- a 45 Hz high-pass;
- a -3 dB low shelf at 120 Hz, which keeps booms off the music's bass;
- a compressor: threshold about -15.5 dB, ratio 6, attack 6 ms, release 160 ms. A stack of sounds is held
  near the level of one, and the music is never pumped by it because it is on another bus.

## 4. One budget for stacked booms
Rate limits per sound are not enough: five different heavy sounds can land together. Put every heavy impact
(boom, rumble, mortar impact, horde surge, stomp) in **one family with one budget**:
- a hit counts in full for 100 ms, then fades over 0.25 s;
- the family may exceed one full hit by 2 dB;
- the next hit gets what is left of the budget;
- a hit that would land below -10 dB, a fourth hit inside the window, or the same sound again within 30 ms
  is dropped.

Reward stingers (bank, loot, stamp) get the same rule with 3.5 dB of headroom. Expose counters for the
reduction and the dropped hits in the debug metrics, so a capture can prove the rule fired.

Then per-sound trims for the families still over the ceiling (here between 0.31 and 0.8 of the rule volume).

## 5. After

| | Before | After |
|---|---|---|
| Battle music | -34.1 LUFS | -20.0 |
| Menu music | -36.2 | -21.0 |
| Boss death vs music | +11.5 dB | -2.7 |
| Titan slam vs music | +11.1 | -2.6 |
| Boss arrival vs music | +12.1 | -0.3 |
| Mortar vs music | +8.6 | -4.8 |
| Skill burst vs music | +19.0 | +4.8 |
| Claims vs music | +15.6 | +4.2 |
| Families over the ceiling | 12 of 17 | 0 |
| Highest true peak | -6.1 dBTP | -3.3 |

## 6. Check the absolute level too
Raising the music 14 dB raised the whole game: the full output in a fight went from about -26 to -18 LUFS,
8–10 dB louder at the same device volume. The sounds the producer named did not come up with it (boss death
-22.6 → -22.7 LUFS absolute, mortar -25.6 → -25.2).

So the relative table was green and the game was still much louder than the day before. The lead stepped
the whole programme down by 4.4 dB before release, using the one-factor knob from step 3.

**Rule:** report both the relative table (each effect against the music) and the absolute one (the whole
output before and after). Decide the overall level on purpose.

## 7. Deliver
- A loudness table (Markdown and CSV) and a before/after chart.
- 30 s mp3 previews, before and after, for the scenes the producer named. Cut them straight from the
  recorded output with no normalisation, or the comparison lies.
- A board (`wise board`) with the charts.
- Tests that pin the budget rule, the graph and the trim tables.
- The open list. Here: nobody has heard it; WebKit levels were not captured; three sounds were never
  triggered in a capture.

## Traps
- **Normalising previews.** A normalised before/after pair sounds the same loudness. That is the one thing
  being compared.
- **Fixing the named sound only.** The complaint names the symptom. The table finds the cause.
- **Trusting the master compressor.** If it never moves, it isn't protecting anything; put dynamics on the
  effects bus.
- **Loading sound all at once.** Mix work is wasted if the first sound arrives 8 s after the first tap.
  Stage the loading (the **game-performance** skill).
