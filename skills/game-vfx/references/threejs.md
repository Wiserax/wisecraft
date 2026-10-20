# Building the style in Three.js

The techniques the style needs, from cheapest to richest. All of them are unlit (`ShaderMaterial` or
`MeshBasicMaterial`): effects never take scene lighting.

## 1. The cel cutout material (the workhorse)
One grayscale **shape** (a painted blob, a flipbook atlas or noise) is cut with a hard threshold and coloured
through a **ramp** of three or four flat bands. A threshold that rises over the effect's life erodes it into
holes and pieces, which is how it dissipates (rule 9). Because the cutout is opaque, it writes depth and needs
no sorting, which also keeps overdraw low on phones.

```js
const ramp = new THREE.DataTexture(new Uint8Array([
  0x1a, 0x2d, 0x11, 255,  0x46, 0x70, 0x1a, 255,  0x8a, 0xac, 0x0b, 255,  0xf7, 0xfb, 0x4f, 255,
]), 4, 1);                                   // poison: dark, mid, light, core
ramp.magFilter = ramp.minFilter = THREE.NearestFilter;   // flat bands, no blending between them
ramp.needsUpdate = true;   // no colour space and no colorspace include: the hex values reach the screen as-is

const celCutout = new THREE.ShaderMaterial({
  uniforms: {
    uShape: { value: shapeAtlas },           // R channel: density, 1 in the middle of the shape
    uRamp: { value: ramp },
    uGrid: { value: new THREE.Vector2(4, 4) }, // flipbook columns and rows (1, 1 for a single drawing)
    uFrames: { value: 16 },
    uLife: { value: 0 },                     // 0..1 over the effect's life, set per frame
    uErode: { value: new THREE.Vector2(0.12, 0.9) }, // threshold at birth and at death
    uOutline: { value: 0.12 },               // width of the dark band at the edge
  },
  vertexShader: `
    varying vec2 vUv;
    void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
  fragmentShader: `
    uniform sampler2D uShape, uRamp;
    uniform vec2 uGrid, uErode;
    uniform float uFrames, uLife, uOutline;
    varying vec2 vUv;
    void main() {
      float f = min(floor(uLife * uFrames), uFrames - 1.0);   // stepped: a drawing, never a blend of two
      vec2 cell = vec2(mod(f, uGrid.x), uGrid.y - 1.0 - floor(f / uGrid.x));
      float d = texture2D(uShape, (vUv + cell) / uGrid).r;
      float cut = mix(uErode.x, uErode.y, uLife * uLife);   // erodes slowly, then breaks up fast
      if (d < cut) discard;
      float t = (d - cut) / max(1.0 - cut, 1e-3);           // 0 at the edge, 1 in the core
      // texel 0 (dark) is the edge band only; the rest of the shape spreads over mid, light and core
      float u = t < uOutline ? 0.125 : 0.25 + 0.749 * (t - uOutline) / (1.0 - uOutline);
      gl_FragColor = vec4(texture2D(uRamp, vec2(u, 0.5)).rgb, 1.0);
    }`,
});
```

- Clone the material per instance only when uniforms differ; better, put `uLife` in an instanced attribute and
  draw a whole family of effects with one `InstancedMesh`.
- A shape without drawings: replace the atlas lookup with a radial falloff plus noise,
  `d = 1.0 - length(vUv * 2.0 - 1.0) + (noise(vUv * 4.0 + seed + tq) - 0.5) * 0.6`, where
  `tq = floor(uTime * 12.0) / 12.0` keeps the noise on twos (rule 10).
- The shape must fall to 0 before the edge of the card, or the card's square border shows at birth.
- The silhouette survives at a small size only with a big dark band: raise `uOutline` for far or small effects.
- The snippet was rendered in Chromium and WebKit with three r180 (a procedural shape, lives 0, 0.35, 0.65,
  0.9): flat bands, a dark edge, erosion into pieces.

## 2. Flipbooks
Hand-drawn or painted frames in one atlas (4x4 or 8x8, 1024 px for a phone). Play them stepped at 12 to 15
drawings per second, whatever the frame rate. The frames can be made offline: painted, simulated and
posterised, or generated, and then judged against the references like anything else. Generated frames are
paid generation: ask first.

## 3. Shape cards in 2.5D
- **Bursts and puffs:** camera-facing quads (an `InstancedMesh` with a billboard vertex shader, or `Sprite` for
  a handful). Smoke is two-tone: a light top and a dark bottom split by `vUv.y` plus noise, with a dark edge.
- **Ground pieces:** a `PlaneGeometry` turned flat (`rotation.x = -Math.PI / 2`) with `polygonOffset` to avoid
  z-fighting: rings, cracks, puddles, scorch marks. A ring's radius is the gameplay radius.
- **Spikes:** flat triangles or three-sided cones fanned out from the impact point, scaled up with an
  ease-out-back and thinned to zero width to finish. Instanced, with the cutout material or plain flat colour
  plus a dark backface outline.
- **Pillars and walls:** a cylinder without caps with the cutout material and UVs scrolling up.

## 4. Smears and trails
- **A swing:** a crescent from `RingGeometry(inner, outer, 32, 1, start, arc)`. UV u runs along the arc: reveal
  with `u < uLife * 1.4`, taper the width with `sin(u * PI)`, erode the tail first. One or two frames of a
  full smear sell the speed better than a long trail.
- **A projectile:** a ribbon of the last N positions (a `BufferGeometry` strip rebuilt in place, no
  allocation per frame) with the cutout material along its length, plus a dark splat card behind the head.
- **Speed lines:** thin instanced cards stretched along the velocity, shown for 2 to 4 frames.

## 5. Impact frames and the hit target
- One or two frames of a flat white (or dark) silhouette on the target: a `uFlash` uniform on the target's
  material, or an `onBeforeCompile` patch that mixes the output colour to flat white.
- Hit-stop of 40 to 80 ms on big hits, skipped under `prefers-reduced-motion`.

## 6. Solid 3D pieces
Rocks, ice, crystals: low-poly, flat colour in two bands (`MeshToonMaterial` with a 2-step `gradientMap`, or
a basic material with baked bands), with an inverted-hull outline: the same geometry, `side: BackSide`,
pushed out along normals, dark colour.

## 7. Budget for phones
- One atlas and one material per effect family; pools, no allocation in the frame loop.
- Cap the live effects per family and drop the oldest; caps scale with the quality guard (the **game-qa**
  skill).
- Measure with `wise qa` on a phone viewport before and after: p95 frame time must not get worse by more
  than a frame's worth at the busiest moment of the game.
- Post-processing bloom, if the game has it, uses a high threshold so only the core band blooms.
