---
name: game-feel-audio
description: Make a web game feel good and sound right without the agent ever hearing it. Covers UI juice (taps, windows, claims, counters), presence beats for bosses (entrance, walk in from the field edge, slam, death, drop), the VFX quality bar (explosions, lightning, crowd readability, slow motion) and a measured audio mix (music about -20 LUFS short-term in battle, no effect more than about 6 dB over it, one budget for stacked booms, a compressor on the effects bus, absolute level checked too). Use when the user says "I need to feel the boss", "the effects look cheap", "the boom is too loud", "the music is too quiet", "add juice", "fix the sound", or asks for VFX, SFX, music or mix work. Audio is measured with `wise loudness` and muted captures, never played aloud.
---

# Game feel and audio

Every tap, window and claim has motion and sound. Bosses are felt, not just drawn. The mix is measured, not
guessed, because the agent can't listen and must never make sound on the user's machine.

## UI feel (global hooks, not per-screen code)
- **Taps:** squash to 0.94, a ripple, a release overshoot. Disabled, locked or unaffordable: a "no" wobble.
- **Windows:** pop in with a stagger and close through a short ghost. The ghost must not keep the `.modal`
  class, or tests and scripts will see it: a `.modal` query must find 0 nodes on the frame after a close.
- **Claims:** an 80 ms charge, a shine, a burst, a counter punch and a number roll; bigger tiers for big
  claims (chapter clear, legendary).
- **Counters** roll up smoothly even if the HUD rewrites them every frame (tween in the feel layer). Roll up
  on gains; drop at once on spends; never show more than the real amount.
- **Tabs** crossfade (<200 ms). Reduced motion collapses everything to fades with no vibration.

## Presence (bosses, giants, titans)
The five beats: **entrance → walk in → slam → death → drop.** A boss that skips one reads as a stat block.
- **Entrance:** boom, shockwave ring, dust, camera shake scaled to size.
- **Walk in from the field edge.** Never spawn next to the base. The producer on a build that did: bosses
  "appear right near" the fort. Start them on the horde's own spawn ring, from up the screen, not from the
  camera side where the dock hides them.
- **Footsteps** for big bodies, rate-limited.
- **Hits:** a hit flash and recoil.
- **Slam:** a camera kick, wall flash, ring. The slam must hit the base: test that a double-size boss reaches
  the wall from every angle (one stood 7 m out through several releases because its reach was shorter than
  its collision stand-off).
- **Death:** stagger → collapse with dust → 0.3–0.4 s slow motion → burst → a tappable drop. It must play on
  *every* kill path, including skill kills, and when the battle clock stops (a stage-clear window froze the
  sim and the boss vanished instead of dying: advance deaths on real time when simulated time is 0).
- **Boss-wave cues:** drums and a sky tint on the wave before, a surge ripple at the boss wave. Keep the
  tint under about half strength, with the edges stronger than the centre, so the base and enemies keep
  contrast.
- Scale everything by size (scout < giant < boss < titan) and respect `prefers-reduced-motion`: no shake, no
  slow motion, no hit-stop.

## VFX quality bar
- **Explosions:** an additive hot core + an eased shockwave + flame lobes + smoke + thrown chunks, in one
  draw. No flat polygon shapes. The producer's words on the flat version: "the effects are cheap".
- **Lightning:** thick ribbons with a glow halo and a short afterimage.
- **Crowd readability:** rim light on heads and backs, darker feet, value spread between enemy types, a
  contact shadow, so the crowd never reads as foliage.
- **Slow motion:** step the simulation in finer slices so every slowed frame shows a new state (9 of 24
  slowed frames were new before this, 23 of 24 after).

## Audio rules
- **The agent never plays audio aloud** (no `afplay`, no speakers). Headless Chromium `--mute-audio`; WebKit
  gets a zero-gain destination init script (the template in the **browser-qa** skill). Judge by measurement:
  LUFS, true peak, spectra, onsets.
- **Mix targets:**
  - Music about -20 LUFS short-term in battle.
  - No single SFX event more than about 6 dB over the music short-term.
  - Impacts get punch from transients, not level.
  - An SFX bus limiter or compressor, plus rate-limits so stacked explosions don't sum into a wall: one
    budget shared by every boom.
  - Check the absolute level too. Raising the music to its target raises the whole game.
- **Phone speakers:** keep hits and deaths audible (add 1–3 kHz presence) and avoid harsh 2–5 kHz on
  pickups. Use 44.1 kHz throughout, mono SFX.
- **Sources:** CC0 recordings (Freesound CC0, Kenney) with a CREDITS line per file; synthesis as the
  fallback. Formant-synth groans sound like a vocoder, so prefer recordings.
- **Sound defaults to ON.** Don't add "remember mute" unless asked. Music starts on the first gesture.
- **Deliver before/after mp3 previews and a loudness table** for the human to listen to. Say in the report
  that nobody has heard it.

## Measuring
```bash
wise loudness preview-battle.mp3                 # integrated LUFS, range, true peak; nothing is played
wise loudness trailer.mp4 --target -15           # compare against a target
bash scripts/loudness.sh preview-battle.mp3    # fallback: plain ffmpeg ebur128, same numbers
```
To measure the game itself, run it in a muted browser, record the output and each bus, and meter the files.
`references/mix.md` has the method, the bus graph and a full before/after table.

## Done means
- Every tap, window and claim has motion and sound; reduced motion still works.
- Each boss tier has all five beats, proven by a test (reaches the wall, slams, dies on every kill path).
- A loudness table: music at target, every effect family within about +6 dB of it, the true peak, and the
  absolute level before and after.
- Previews for the human, and a board of before/after frames (`wise board`).

## References
- `references/mix.md`: how to measure a game's mix without hearing it, the bus graph, the stacked-boom
  budget, and the case where the fix made the whole game louder. Read it before changing any volume.
- `scripts/loudness.sh`: ffmpeg fallback for `wise loudness`.
