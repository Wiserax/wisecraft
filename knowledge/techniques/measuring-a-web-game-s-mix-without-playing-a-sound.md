---
kind: technique
title: "Measuring a web game's mix without playing a sound"
tags: [audio, webaudio, audioworklet, lufs, "bs.1770", stems, measurement, playwright, headless, loudness, calibration]
date: 2026-10-11
agents: ["Claude Code (Opus 5.5)"]
humans: []
links: []
---

# Measuring a web game's mix without playing a sound

> An agent cannot hear, and must not play audio on the human's machine. A WebAudio game can still be measured
> exactly: run the real game in a muted browser with its output replaced by a zero-gain sink, tap the graph
> with an AudioWorklet that only collects samples, record the output, each bus and one stem per sound, and
> meter them with BS.1770. The result is a table of every effect family against the music bed, before and
> after. It says whether levels are right, not whether the mix sounds good.

## When to use it
- A complaint about loudness ("the explosion is too loud", "I cannot hear the music").
- Setting mix targets for a game whose sounds were added one at a time.
- Before and after any change to bus gains, compressors or per-sound volumes.
- Not for judging timbre or taste. Give the human previews for that.

## How
1. **Make silence certain, twice.** Launch Chromium with `--mute-audio`. Also inject a script before the page
   loads that makes every `AudioContext.destination` return a gain node at 0. Either alone is enough; both
   means a mistake in one cannot make noise. WebKit has no mute flag, so there the sink is the only guard.
2. **Fix the sample rate.** Create the game's context at 48 kHz so a capture does not depend on the output
   device the machine happens to have.
3. **Record with an AudioWorklet.** One processor with many inputs that copies samples to the page in blocks
   and outputs silence. An extra `connect()` from a node to the recorder does not change what that node feeds,
   so the game's graph is untouched.
4. **Tap four kinds of point:**

   | Tap | Where | Answers |
   |---|---|---|
   | output | whatever reaches the destination, after the master chain | what the player hears |
   | music bus | after its slider, before the master chain | the bed |
   | effects + ambience bus | same point | the effects as a whole |
   | one stem per sound key | each voice's last node before its bus | which sound is responsible |

5. **Log on the audio clock**, at 20 Hz and per event: every sound started (key, file variant, the gain and
   rate the voice really got, bus), the game events (boss arrives, boss dies, a slam), every bus gain, the
   master compressor's gain reduction, the voice count.
6. **Script scenarios in real time** against the real build: a minute of ordinary battle, a boss's arrival
   and death, a titan's slam, a mortar barrage, a skill, a celebration, the hub. Switch the sound on the way
   a player does, with a first touch.
7. **Meter with ITU-R BS.1770** K-weighting: momentary (400 ms), short-term (3 s), integrated with gates at
   -70 LUFS and -10 LU. Decode files through ffmpeg to a pipe. Check the meter against ffmpeg's `ebur128` on
   every full-output file. `wise loudness` gives the file-level figures (integrated, true peak).
8. **Define the music bed** as the median short-term loudness of the music stem while its fader is full and
   nothing ducks it. Express every effect as dB over that bed.
9. **Shift stems to "as heard".** Stems are tapped before the master chain, so add the chain's static gain
   (master gain × the compressor's built-in make-up), measured from a capture where the compressor is idle.
10. **Group keys into families** (boss death, mortar, coins, UI…). For moment families, count only the
    family's keys inside the window the game event opens.
11. **State the pass rule.** Here: a family passes when its loudest 400 ms is at most +6 dB over the music's
    short-term bed. Report the 3 s figure next to it; a single boom always reads lower over 3 s.
12. **Report punch separately:** peak minus short-term loudness per family, so a reduction in level that also
    flattens transients is visible.

## Verification
Used on a horde tower-defense mobile web game (Vite 7 + three.js 0.180, 8,000 enemies on screen at 60 fps,
portrait 390×844): 8 scenarios, 133 audio buffers, 17 effect families, the same captures on two builds. It
found the battle music at -34.1 LUFS and 12 of 17 families over the ceiling, and confirmed 0 of 17 after the
fix. The analyser checks its own meter against ffmpeg's on every full-output file.

**Not verified:** WebKit captures; the correlation between these numbers and what a person hears on a phone
speaker.

## Gotchas
1. **Stems stopped adding up to the bus.** **Symptom:** after the fix, per-sound stems summed to a different
   level than the recorded effects bus. **Cause:** the new build put a high-pass, a shelf, a compressor with
   make-up gain and a fixed trim between the voices and the bus tap; the tool modelled only a gain. **Fix:**
   calibrate against the recorded bus: fit one gain for everything feeding the effects bus and one for
   ambience, least squares on power, weighted to the loud moments, so the stems' momentary loudness adds up
   to the bus. Report the fit error and mark a capture as approximate when the fit is poor.
2. **A bus with its own dynamics has no single "gain".** After calibration a stem's level is its level at the
   bus's average gain. Inside a dense stack the compressor takes more. Read per-key numbers as attribution,
   and the bus recording as truth.
3. **The browser's compressor adds make-up gain by itself.** `DynamicsCompressorNode` raised the bus by about
   6 dB at the settings used. A static-gain model that ignores it is off by that much.
4. **A stack of voices can clip a 16-bit stem.** **Fix (built in from the start):** store key stems at -6 dB
   and count clipped samples in the recorder.
5. **A sound that was never triggered has no measurement.** Three keys were missing from every scenario. List
   the keys with zero plays in the report.
6. **A capture can depend on the output device.** A context created at the device's default rate records at
   whatever rate the machine's output has. **Fix:** create the context at 48 kHz.
7. **Relative targets hide absolute level.** Every family can be within +6 dB of the bed while the whole game
   is 8 dB louder than last week. Put integrated output loudness per scenario, before and after, in the same
   table.
8. **Nobody has heard it.** Write that sentence in the report. Deliver short previews cut straight from the
   recorded output, with no normalisation, so the human hears what was measured.

## Open questions
- A phone-speaker model (band-limit, then meter) was used in an earlier pass and not in this one.
- Whether per-voice taps cost enough CPU to change voice stealing in a dense scene was not measured.

## Seen in
- [The audio mix measured, not listened to](../games/horde-tower-defense-mobile-web/the-audio-mix-measured-not-listened-to-music-at-34-lufs-made.md)
