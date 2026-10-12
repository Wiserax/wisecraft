---
kind: game
title: "The audio mix measured, not listened to: music at -34 LUFS made every boom read 9 to 19 dB too loud"
game: "Horde tower defense (mobile web)"
games_also: []
game_version: "2.3.5 (measured against live 2.3.4, released in build 2.3.6), Vite 7 + three.js 0.180"
platform: web-mobile
engine: threejs-vite
route: audio
tools: ["Playwright", "node --test", "ffmpeg", "wise music-enhance --check", "Vite"]
status: released
agents: ["Claude Code (Opus 5.5)"]
humans: []
date: 2026-10-11
links: []
tags: [audio, mix, lufs, "bs.1770", webaudio, compressor, bus, ducking, impacts, loudness, music-bed]
---

# The audio mix measured, not listened to: music at -34 LUFS made every boom read 9 to 19 dB too loud

> The complaint was that a boss's death and the mortar were far too loud. Measurement showed the opposite
> problem: the battle music sat at -34.1 LUFS, 14 dB under its target, so 12 of 17 effect families stood 9 to
> 19 dB over it. The fix raised the music with a bus trim, added dynamics to the effects bus, gave stacked
> impacts one shared budget and trimmed single sounds. Afterwards every family is within +6 dB of the music.
> Nothing was listened to; the agent cannot hear. After release the whole mix was stepped down 4.4 dB.

## Setup
- A horde tower-defense mobile web game (Vite 7 + three.js 0.180, 8,000 enemies on screen at 60 fps,
  portrait 390×844).
- WebAudio. Three buses (music, effects, ambience) into a master chain: master gain → 32 Hz high-pass →
  compressor → limiter. 133 audio files. Music files are normalised to about -18 LUFS on disk.
- Capture method: see the technique note on measuring a mix without playing a sound. Meters are ITU-R BS.1770:
  momentary (loudest 400 ms) and short-term (3 s).

## Route and why
**Audio, by numbers.** Targets given by the lead: battle music about -20 LUFS short-term at default volume
settings; no effect family more than about 6 dB over the music; impacts get their punch from transients, not
level. Turning the named sounds down would have left the music inaudible under everything else, so the bed
was measured first.

## How the game works (what we had to learn)
- **"Too loud" is relative to the bed.** An effect at -22 LUFS over music at -34 reads as +12 dB.
- **The master compressor was not doing anything.** Its deepest gain reduction in any capture was 0.4 dB.
- **A boss death was two full sounds on one frame.** A boom and a rumble together read 2.6 dB over either alone.
- **The browser's `DynamicsCompressorNode` adds its own make-up gain** (about +6 dB at these settings). A trim
  after it has to be set with that included.
- **Default slider values** are music 0.45, effects 0.75, ambience 0.35. Players keep defaults, so the mix is
  measured there.

## Build steps
1. **Bus trims** (`MIX` in `src/audio.js`): each bus is input → fixed trim → the player's slider → master.
   Music 5.07, effects 1.47, ambience 3. Slider defaults stay. One factor on all three moves the whole
   programme without touching the balance.
2. **Effects-bus dynamics, in front of the trim:** 45 Hz high-pass, a -3 dB low shelf at 120 Hz (keeps booms
   off the music's bass), compressor at threshold -15.5 dB, ratio 6, attack 6 ms, release 160 ms. A stack of
   sounds is held near the level of one, and the master compressor (and with it the music) is left alone.
3. **One budget for stacked impacts** (`impactPlan`): boom, rumble, mortar impact, horde surge and stomp share
   it. A hit counts in full for 100 ms, then fades over 0.25 s. The family may exceed one full hit by 2 dB;
   the next hit gets what is left. Below -10 dB, past 3 hits in the window, or the same sound within 30 ms, it
   is dropped. Reward stingers have the same rule with 3.5 dB.
4. **Per-sound trims** (`SFX.trim`, multiplied into the rule volume): boom 0.42, rumble 0.47, horde surge
   0.31, mortar impact 0.32, mortar launch 0.42, stomp and war drum 0.6, the charge skill 0.32, claims
   0.44-0.64, the legendary fanfare 0.52.
5. Music under a modal 0.4 → 0.5 of full; the duck under the charge skill 0.32 → 0.5; menu track gain
   0.24 → 0.27.

## Verification
Same eight scripted captures on the live build and on the fix; 133 audio buffers loaded, 0 failed, in all.

| | Before | After |
|---|---|---|
| Battle music, short-term LUFS | -34.1 | -20.0 |
| Menu music | -36.2 | -21.0 |
| Families over the +6 dB ceiling | 12 of 17 | 0 of 17 |
| Highest output peak, dBTP | -6.1 | -3.3 |
| Deepest master compressor reduction, dB | -0.4 | -1.3 |

Loudest 400 ms of each family against the music bed, dB:

| Family | Before | After | | Family | Before | After |
|---|---|---|---|---|---|---|
| charge skill | +19.0 | +4.8 | | stomp / rumble | +11.1 | -1.4 |
| coins / claims | +15.6 | +4.2 | | UI | +10.3 | +1.3 |
| swipe skill | +14.7 | +5.0 | | gacha | +10.0 | -1.1 |
| celebration | +14.4 | +3.5 | | mortar | +8.6 | -4.8 |
| boss arrival, slams | +12.1 | -0.3 | | enemy voices | +3.8 | -0.9 |
| boss death | +11.5 | -2.7 | | guns | +3.5 | -1.2 |
| fanfare | +11.3 | +1.4 | | tap lightning | +2.7 | -2.7 |
| titan slam | +11.1 | -2.6 | | kills / wall hits | -4.3 / -3.2 | -9.1 / -7.8 |

`tests/audio-mix.test.js` (15 cases: the budget, the graph, the tables) runs under `node --test`.

**Not verified:** nobody heard it. WebKit levels were not captured. Three sounds were never triggered in a
capture (a gift reveal, a merge, the titan's death).

## Gotchas
1. **The named sounds were not the problem.** **Cause:** the music was 14 dB under target. **Fix:** measure the
   bed before touching an effect.
2. **Meeting the relative target made the game louder as a whole.** The whole output in a fight went from
   about -26 to -18 LUFS at the same device volume, because the music had to rise 14 dB. The sounds that were
   complained about stayed put in absolute terms (boss death -22.6 → -22.7 LUFS, titan slam -21.6 → -21.4,
   mortar -25.6 → -25.2). The lead stepped the released mix down 4.4 dB. **Fix:** check absolute level as well
   as the ratio, and decide the programme level on purpose.
3. **Punch survived only where the trim did the work.** Peak minus 3 s loudness for a boss death went from
   23.8 to 20.9 dB, for stomps from 16.3 to 11.4 dB. A compressor fast enough to hold a stack also shaves
   transients; the trims and the budget should carry most of the reduction.
4. **Stacks, not single sounds, hit the ceiling.** Two sounds on one frame add up to 3 dB; five mortar shells
   add more. A per-sound volume cannot fix a sum. **Fix:** a shared budget per family.
5. **A trim in the wrong place changes the dynamics.** The effects trim sits after the compressor, so moving
   it does not move the threshold. Put fixed trims where a later change of level will not retune the bus.
6. **Old tests expected the old volumes.** Two existing audio tests asserted rule volumes; they now expect
   rule volume × trim.

## Assets
No new sounds. Deliverables for the human: a loudness table, before/after charts per scene, spectra, and six
30 s previews cut straight from the recorded output with no normalisation.

## Open questions
- Whether it sounds good. The previews went to the human for that.
- Phone-speaker response was not part of this pass.
- The final released level (4.4 dB lower) was not re-measured per family; ratios should hold if all three
  trims moved together, which the sources do not confirm.
