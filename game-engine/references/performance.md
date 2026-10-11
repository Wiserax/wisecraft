# Performance

## Two tests, always both
1. **Capacity:** spawn 2,000 / 5,000 / 8,000 enemies with the walls held and measure fps and p95 frame time. Target 60 fps, p95 ≤ 16.8 ms on a desktop-class machine.
2. **Real late-stage play:** load a realistic save at the late stages (e.g. 7–9), walls **not** held, real buys, boss + giants + titan on screen. Test at desktop retina (1440×900 @2x), phone 390×844 @3x, and Chrome with 4× CPU throttle. Capacity tests miss what real play does: sustained slow patches, guard state and VFX bursts.

## Budgets that worked (three.js, instanced crowd)
- ~300k triangles per frame at peak (low-poly corpses, LOD or impostors for far giants), ~60–70 draw calls, a shadow budget (only hero objects cast).
- No per-frame allocations in hot paths; write instance matrices directly; no forced layout per frame (reading DOM sizes inside the render loop).
- The crowd collision solver dominates the sim at thousands of bodies; one pass instead of two is a valid degradation step.

## Adaptive quality guard
- When frames stay above ~22 ms for 2 s, step down whichever side costs more:
  - **sim:** 30 Hz steps → 1 step per frame → 1 collision pass;
  - **draw:** pixel ratio 1.25 → 1.0, shadows off.
- **It must recover:** step back up after sustained good frames using a threshold that a 60 Hz vsync can actually meet (frames ~16.7 ms, so "under 13 ms" never happens). Our first guard never recovered, and stage 7 stayed a slideshow for the rest of the siege.
- Expose its state (`__game.guard`) and include it in perf reports.

## Load time
- Measure cold and warm loads on Fast 4G + 4× CPU: bytes, time to splash, hub, first siege, first sound after the first tap.
- Stage audio loading (UI first, battle later, idle prefetch), immutable cache headers for hashed assets, one-day cache for audio and art, and no orphan assets in the deploy.
- **Boot must never hang:** retry a failed chunk under a fresh URL, reload once, then show a Retry screen. Prove it with 60+ cold boots.
