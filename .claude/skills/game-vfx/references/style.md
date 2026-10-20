# The house VFX style: hand-drawn 2.5D, stylised hybrid CGI

2D hand-drawn effect shapes, animated like cel animation, placed in a 3D scene. Think of the effect sheets of
stylised action and fighting games: flat colour, bold shapes, ink-dark accents, sharp timing. The producer's
own reference set (local only, never in the repo) is described in `knowledge/vfx-style/README.md`.

Every effect is checked against the twelve rules below. The comparison board (`scripts/vfx_board.py`) shows
the silhouette and the value bands next to the references, so most of them can be checked by eye in seconds.

## Shape
1. **Silhouette first.** The effect reads as one bold shape in solid black and white (the board's
   silhouette row). If the silhouette is a fog or confetti, the effect fails before colour is discussed.
2. **Sharp, tapered, directional.** Spikes, teardrops, crescents, S-curves and splats that point the way the
   force goes. Edges are ragged with holes and broken-off pieces. No perfect circles, no uniform particles,
   no soft blobs on their own.
3. **Dark shapes are part of the effect.** A near-black tinted band or mass sits behind or around the bright
   part: an ink splat behind a projectile, a dark cloud with glowing bubbles, dark outlines on smoke and rocks.
   This is what keeps the effect readable over a busy, lit 3D ground.
4. **Big, medium, small.** One main shape, two or three secondary shapes, then a few chips, sparks or
   droplets. Secondary detail never competes with the main shape.

## Colour
5. **Three or four flat value bands per element:** dark (tinted near-black), saturated mid, light, and a hot
   core near white. Hard steps between bands, no smooth gradients. Starting palettes, sampled from the
   reference set and spread so each band reads on its own, darkest first:

   | Element | Dark | Mid | Light | Core |
   |---|---|---|---|---|
   | poison, nature | `#1a2d11` | `#46701a` | `#8aac0b` | `#f7fb4f` |
   | fire, explosion | `#562f2c` | `#a24a29` | `#f38345` | `#fffe80` |
   | blood, red slash | `#590213` | `#b10d22` | `#fd1532` | `#fa68ce` |
   | ice, wind, cyan slash | `#35797c` | `#549c9c` | `#47cad5` | `#e8ffff` |
   | arcane, purple | `#5b0779` | `#9d3fba` | `#fb47f7` | `#ffd6ff` |
   | lightning | `#3d1a5c` | `#a054cd` | `#ffc041` | `#ffffff` |

   One small accent in the complementary hue (purple flecks in a green heal) makes the main colour sing; keep
   it under a tenth of the area.

6. **Colour means gameplay.** One element, one palette, everywhere in the game: a poison hit, a poison aura
   and a poison drop share it. Team or owner colour goes on a ring or outline, never on the element itself.
7. **Glow is a band, not a blur.** Use one lighter flat band around the core. A soft additive glow is allowed
   only as a small halo under the core, never as the effect itself.

## Motion and timing
8. **Anticipation, impact, follow-through, dissipation.** A short gather (3 to 6 frames at 60 fps), an impact
   frame that is the biggest and brightest (1 or 2 frames, a flat white or dark flash is fine), the main
   motion, then dissipation.
9. **Dissipate by breaking up, never by fading.** Shapes thin, erode into holes and split into pieces that fly
   off. An opacity fade over the whole effect is the prototype look.
10. **Animate the drawing on twos.** The shapes change at 12 to 15 drawings per second (stepped), while the
    game, the emitter and the camera stay at full frame rate. Smears and speed lines carry fast motion:
    a crescent smear for a swing, streaks for a dash.

## 2.5D
11. **Flat cards in a 3D scene.** Shapes are cards facing the camera (puffs, bursts), lying on the ground
    (rings, cracks, puddles) or standing on an axis (pillars, walls). A few solid 3D pieces (rocks, ice
    spikes, crystals) are flat-shaded with a dark outline, never lit like PBR.
12. **Readable on a phone at gameplay zoom.** Judge the effect in the real camera on a 390 px wide screen
    with enemies around it. A ground ring is exactly the size of its gameplay radius.

## What fails (the prototype look)
- Glowing additive circles and spheres, smooth alpha fades, soft particle confetti.
- One colour at one value, so the effect vanishes over grass or a lit floor.
- PBR-lit or default-material meshes as effects.
- Every effect the same size and the same 1-second timing.
