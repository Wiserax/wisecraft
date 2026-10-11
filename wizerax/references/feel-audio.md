# Game feel and audio

## UI feel (global hooks, not per-screen code)
- Taps: squash to 0.94, a ripple, a release overshoot. Disabled, locked or unaffordable: a "no" wobble.
- Windows: pop in with a stagger and close through a short ghost. The ghost must not keep the `.modal` class, or tests and scripts will see it.
- Claims: an 80 ms charge, a shine, a burst, a counter punch and a number roll; bigger tiers for big claims (chapter clear, legendary).
- Counters roll up smoothly even if the HUD rewrites them every frame (tween in the feel layer).
- Tabs crossfade (<200 ms). Reduced motion collapses everything to fades with no vibration.

## Presence (bosses, giants, titans)
- **Entrance:** boom, shockwave ring, dust, camera shake scaled to size.
- **Footsteps** for big bodies, rate-limited.
- **Hits:** a hit flash and recoil.
- **Slam:** a camera kick, wall flash, ring.
- **Death:** stagger → collapse with dust → 0.3–0.4 s slow motion → burst → a tappable drop. It must play on *every* kill path, including skill kills.
- **Boss-wave cues:** drums and a sky tint on the wave before, a surge ripple at the boss wave. Keep the tint under about half strength, with the edges stronger than the centre, so the base and enemies keep contrast.

## VFX quality bar
- **Explosions:** an additive hot core + an eased shockwave + flame lobes + smoke + thrown chunks, in one draw. No flat polygon shapes.
- **Lightning:** thick ribbons with a glow halo and a short afterimage.
- **Crowd readability:** rim light on heads and backs, darker feet, value spread between enemy types, a contact shadow, so the crowd never reads as foliage.
- **Slow motion:** step the simulation in finer slices so every slowed frame shows a new state.

## Audio rules
- **The agent never plays audio aloud** (no afplay or speakers). Headless Chromium `--mute-audio`; WebKit gets a zero-gain destination init script (see `scripts/qa/browser-qa.template.mjs`). Judge by measurement: LUFS, true peak, spectra, onsets.
- **Mix targets:**
  - Music about -20 LUFS short-term in battle.
  - No single SFX event more than about 6 dB over the music short-term.
  - Impacts get punch from transients, not level.
  - An SFX bus limiter, plus rate-limits so stacked explosions don't sum into a wall.
- **Phone speakers:** keep hits and deaths audible (add 1–3 kHz presence) and avoid harsh 2–5 kHz on pickups. Use 44.1 kHz throughout, mono SFX.
- **Sources:** CC0 recordings (Freesound CC0, Kenney) with a CREDITS line per file; synthesis as the fallback. Formant-synth groans sound like a vocoder, so prefer recordings.
- **Sound defaults to ON.** Don't add "remember mute" unless asked. Music starts on the first gesture.
- **Deliver before/after mp3 previews and a loudness table** for the human to listen to.
