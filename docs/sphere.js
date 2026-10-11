// The hero: a glowing liquid sphere on a dithered pixel grid, with a spray of particles flowing off its rim.
// WebGL2. One full-screen pass draws the field (2x2-px cells, each picking one of three inks by a staggered random roll),
// one instanced pass draws the particles. ?t=<frame> freezes time (the README banner uses #banner), window.__fx.render(t)
// draws one exact frame, and window.__planet counts frames and the average CPU cost of one.
(() => {
  const cv = document.getElementById('planet'); if (!cv) return;
  const gl = cv.getContext('webgl2', { antialias: false, premultipliedAlpha: false });
  if (!gl) return;
  const q = new URLSearchParams(location.search), freeze = q.has('t') ? +q.get('t') : location.hash === '#banner' ? 260 : null;

  const COMMON = `#version 300 es
precision highp float; precision highp int;
uniform vec2 uRes; uniform float uDpr, uT, uDust; uniform vec4 uE; uniform vec2 uK;   // uE: centre.xy, radii.zw; uK: tilt, wide
const float TAU = 6.2831853;
uint hh(uint x){ x ^= x >> 17; x *= 0xed5ad4bbu; x ^= x >> 11; x *= 0xac4c1b51u; x ^= x >> 15; x *= 0x31848babu; x ^= x >> 14; return x; }
float rf(uint x){ return float(hh(x) >> 8) / 16777216.0; }
vec2 WH(){ return uRes / uDpr; }
float SC(){ vec2 w = WH(); return sqrt(w.x * w.y) / 1440.0; }
vec2 R2(vec2 v, float a){ float c = cos(a), s = sin(a); return vec2(c * v.x - s * v.y, s * v.x + c * v.y); }
// the liquid edge: three slow waves running around the rim
float wob(float th, float t){ return 1.0 + 0.018 * sin(3.0 * th + t * 0.010) + 0.011 * sin(5.0 * th - t * 0.016) + 0.005 * sin(9.0 * th + t * 0.029); }
vec2 edge(float th, float t, out vec2 nrm){
  vec2 r = uE.zw, q = vec2(cos(th), sin(th)) * wob(th, t) * r;
  nrm = R2(normalize(vec2(cos(th) / r.x, sin(th) / r.y)), uK.x);
  return uE.xy + R2(q, uK.x);
}
// copy column: the haze and the spray thin out over the text on wide screens
float textMask(vec2 p){ return uK.y > 0.5 ? mix(0.12, 1.0, smoothstep(0.40, 0.62, p.x / WH().x)) : 1.0; }
float vig(vec2 p){ float n = distance(p, WH() * 0.5) / (1600.0 * SC()); return max(0.2, 1.0 - n * n * n); }
`;

  const FIELD_VS = `#version 300 es
void main(){ gl_Position = vec4(gl_VertexID == 1 ? 3.0 : -1.0, gl_VertexID == 2 ? 3.0 : -1.0, 0.0, 1.0); }`;

  const FIELD_FS = COMMON + `
const vec3 RIM = vec3(0.84, 1.00, 0.97), MID = vec3(0.45, 0.96, 0.93), DEEP = vec3(0.06, 0.20, 1.00), BLK = vec3(0.016, 0.018, 0.045);
const vec3 LIGHT = vec3(-0.50, -0.62, 0.60);
out vec4 o;
float ramp(float d, float l){ return min(1.0, d / l); }
void main(){
  float s = SC(), t = uT;
  vec2 dev = vec2(gl_FragCoord.x, uRes.y - gl_FragCoord.y);
  float grain = (rf(uint(dev.y) * uint(uRes.x) + uint(dev.x) ^ 0x51f15e3du) - 0.5) * (22.0 / 255.0);
  vec2 cell = floor(dev * 0.5) * 2.0, p = (cell + 1.0) / uDpr;
  float shade = vig(p);
  vec3 base = max(BLK * vig(dev / uDpr) + grain, 0.0);

  vec2 lq = R2(p - uE.xy, -uK.x), n = lq / uE.zw;
  float th = atan(n.y, n.x), w = wob(th, t), sd = (length(n) - w) * min(uE.z, uE.w);
  float pr = 0.0, pm = 0.0, pd = 0.0, glow = 0.0;
  float glim = 1.0 + 0.18 * sin(th * 6.0 - t * 0.021) + 0.55 * pow(0.5 + 0.5 * cos(th + 2.3 - t * 0.017), 10.0);
  bool solid = abs(sd) < 2.5 * s;

  if (!solid && sd < 0.0) {
    // inside: a dark, airy body like the reference - dense just under the rim, thinning into sparse blue -
    // with a few liquid islands floating on the surface, turning with the sphere and slowly changing shape
    vec2 m = n / w; float z = sqrt(max(0.0, 1.0 - dot(m, m)));
    vec3 N = vec3(m, z), L = normalize(LIGHT);
    float lit = clamp(dot(N, L) * 1.05 + 0.08, 0.0, 1.0), dp = -sd;
    float spin = t * 0.0016, cs = cos(spin), sn = sin(spin);
    vec3 P = vec3(cs * N.x + sn * N.z, N.y, -sn * N.x + cs * N.z);          // surface point in the sphere's own frame
    // warp the surface at two scales so the islands get ragged, liquid outlines that keep slowly reshaping
    P += 0.16 * vec3(sin(P.y * 4.0 + t * 0.005), sin(P.z * 3.5 - t * 0.004), sin(P.x * 4.5 + t * 0.006));
    P += 0.06 * vec3(sin(P.z * 11.0 - t * 0.009), sin(P.x * 13.0 + t * 0.008), sin(P.y * 12.0 - t * 0.010));
    P = normalize(P);
    float isl = 0.0;
    isl = max(isl, smoothstep(0.825, 0.940, dot(P, normalize(vec3(-0.55, -0.35, 0.76)))));
    isl = max(isl, smoothstep(0.875, 0.970, dot(P, normalize(vec3(0.45, 0.30, 0.84)))));
    isl = max(isl, smoothstep(0.845, 0.950, dot(P, normalize(vec3(0.85, -0.45, -0.28)))));
    isl = max(isl, smoothstep(0.895, 0.985, dot(P, normalize(vec3(-0.30, 0.62, 0.72)))));
    isl = max(isl, smoothstep(0.835, 0.940, dot(P, normalize(vec3(-0.70, 0.20, -0.68)))));
    vec3 C = normalize(N + 0.12 * vec3(sin(N.y * 7.0 + t * 0.006), sin(N.x * 6.0 - t * 0.005), 0.0));
    isl = max(isl, 0.9 * smoothstep(0.885, 0.975, C.z + 0.02 * sin(t * 0.004)));
    float rimBand = exp(-dp / (34.0 * s));
    float core = isl * isl;                                                   // islands are densest in the middle
    pr = exp(-dp / (5.0 * s)) * 0.9 + 0.08 * core * lit;
    pm = (0.62 * rimBand + (0.30 * isl + 0.32 * core) * (0.55 + 0.45 * lit)) * ramp(dp, 3.0 * s);
    pd = (0.06 + 0.24 * exp(-dp / (200.0 * s))) * (0.55 + 0.45 * lit) + 0.12 * isl;
    glow = 0.10;
  } else if (!solid) {
    float d = sd;
    // a thin stippled corona and a smooth bloom; the space beyond stays dark so the spray reads
    pr = exp(-d / (7.0 * s)) * 0.85; pm = exp(-d / (16.0 * s)) * 0.45 * ramp(d, 3.0 * s); pd = exp(-d / (38.0 * s)) * ramp(d, 6.0 * s) * 0.6;
    glow = 0.12 * exp(-d / (120.0 * s));
    float mk = textMask(p); pm *= mk; pd *= mk; pr *= mix(0.3, 1.0, mk); glow *= mk;
  }
  base += DEEP * glow * shade;

  vec3 ink = vec3(0.0); bool on = false;
  if (solid) { ink = RIM * shade * glim; on = true; }
  else {
    float total = min(1.0, pr + pm + pd);
    if (total > 0.003) {
      // each cell keeps its roll for 90 frames; the cells re-roll out of step, so the grain sparkles without flashing
      uint cols = uint(ceil(uRes.x * 0.5)), ci = uint(cell.y * 0.5) * cols + uint(cell.x * 0.5);
      uint bucket = hh(ci ^ 0x1b873593u) % 90u, fr = uint(max(0.0, floor(t)));
      float r = rf(ci ^ (((fr + 89u - bucket) / 90u) * 0x9e3779b1u) ^ 0x7a11c0deu);
      if (r < pr) { ink = RIM * shade * glim; on = true; }
      else if (r < pr + pm) { ink = MID * shade; on = true; }
      else if (r < total) { ink = DEEP * shade; on = true; }
    }
  }
  float scan = mod(floor(dev.y * 0.5), 2.0) < 1.0 ? 1.0 : 0.58;     // CRT scanlines over the ink
  o = vec4(on ? max(ink * scan + grain, 0.0) : base, 1.0);
}`;

  const PART_VS = COMMON + `
out float vA; out vec3 vC;
void main(){
  if (uDust > 0.5) {
    uint dd = hh(uint(gl_VertexID) ^ 0x9b05688cu);
    float a1 = rf(dd), a2 = rf(dd ^ 0x1f83d9abu), a3 = rf(dd ^ 0x5be0cd19u), a4 = rf(dd ^ 0x6a09e667u);
    vec2 w = WH(); float s = SC();
    // most motes sit low and to the left, drifting up and right very slowly, and twinkle
    vec2 p = vec2(pow(a1, 1.9) * w.x * 1.05, w.y * (1.0 - pow(a2, 2.2) * 0.95));
    p += vec2(0.045, -0.03) * s * uT * (0.4 + a3);
    p = mod(p + w * 0.1, w * 1.2) - w * 0.1;
    float tw = 0.5 + 0.5 * sin(uT * (0.01 + 0.03 * a4) + a3 * TAU);
    vA = (0.55 + 0.45 * a4) * (0.45 + 0.55 * tw) * mix(0.35, 1.0, textMask(p));
    vC = a3 > 0.82 ? vec3(0.55, 0.98, 0.95) : vec3(0.95, 0.97, 1.0);
    gl_Position = vec4(p.x / w.x * 2.0 - 1.0, 1.0 - p.y / w.y * 2.0, 0.0, 1.0);
    gl_PointSize = 2.0;
    return;
  }
  uint sd = hh(uint(gl_VertexID) ^ 0x2545f491u);
  float u1 = rf(sd), u2 = rf(sd ^ 0x68e31da4u), u3 = rf(sd ^ 0xb5297a4du), u4 = rf(sd ^ 0x1b56c4e9u),
        u5 = rf(sd ^ 0x7fb5d329u), u6 = rf(sd ^ 0xd2a98b26u), u7 = rf(sd ^ 0x3c6ef372u);
  float s = SC(), t = uT;
  // every particle loops forever: born on the rim, drifts out, fades; most stay close (cube-root bias)
  float th = u1 * TAU;
  float md = max(440.0 * s * (1.0 - pow(u2, 1.0 / 3.0)), 18.0 * s);
  float sp = (0.19 + 0.17 * u3) * s, dp = mod(t * sp + u4 * md, md);
  vec2 nrm, e = edge(th, t, nrm), tg = vec2(-nrm.y, nrm.x);
  float f = 0.004 + 0.011 * u5, k = dp / (dp + 40.0 * s);
  vec2 p;
  if (u7 < 0.10) {                                   // a few glints slide in over the surface
    p = e - nrm * dp * 0.35 + tg * dp * 0.2;
  } else {
    p = e + nrm * dp                                  // out from the rim
      + tg * (dp * 0.28 + 9.0 * s * sin(t * f + u6 * TAU) * k)   // flung round with the spin, swaying
      - vec2(0.0, dp * dp / (md + 1.0) * 0.18);      // and lifting a little as it goes
  }
  float a = max(0.0, min(dp / (9.0 * s), (md - dp) / (md * 0.25)));
  if (u7 < 0.10) a *= 0.7;
  a *= textMask(p);
  vA = a;
  vC = (u6 > 0.80 ? vec3(0.55, 0.98, 0.95) : (u6 < 0.06 ? vec3(0.35, 0.5, 1.0) : vec3(0.93, 1.0, 0.99))) * vig(p);
  vec2 w = WH();
  gl_Position = vec4(p.x / w.x * 2.0 - 1.0, 1.0 - p.y / w.y * 2.0, 0.0, 1.0);
  gl_PointSize = 2.0;
}`;
  const PART_FS = `#version 300 es
precision highp float; in float vA; in vec3 vC; out vec4 o; void main(){ o = vec4(vC, vA); }`;

  const prog = (vs, fs) => {
    const p = gl.createProgram();
    for (const [type, src] of [[gl.VERTEX_SHADER, vs], [gl.FRAGMENT_SHADER, fs]]) {
      const sh = gl.createShader(type); gl.shaderSource(sh, src); gl.compileShader(sh);
      if (!gl.getShaderParameter(sh, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(sh));
      gl.attachShader(p, sh);
    }
    gl.linkProgram(p); if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(p));
    return p;
  };
  const field = prog(FIELD_VS, FIELD_FS), parts = prog(PART_VS, PART_FS);
  gl.bindVertexArray(gl.createVertexArray());
  const loc = (p) => Object.fromEntries(['uRes', 'uDpr', 'uT', 'uE', 'uK', 'uDust'].map((n) => [n, gl.getUniformLocation(p, n)]));
  const L = new Map([[field, loc(field)], [parts, loc(parts)]]);

  let E = [0, 0, 1, 1], K = [0, 0], N = 0, ND = 0, dpr = 1;
  const geom = () => {
    const hero = cv.parentElement, W = hero.clientWidth, H = hero.clientHeight;
    dpr = Math.min(devicePixelRatio || 1, 1.5);
    cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr);
    // fit the sphere into the space the copy leaves free: right of it on wide screens, below it on phones
    const hb = hero.getBoundingClientRect(); let right = 0, bottom = 0;
    const take = (r) => { if (r.width) { right = Math.max(right, r.right - hb.left); bottom = Math.max(bottom, r.bottom - hb.top); } };
    for (const el of hero.children) {
      if (el === cv) continue;
      // text blocks span the whole column, so measure the text itself (each text node), and boxed parts by their box
      if (el.matches('.install')) { take(el.getBoundingClientRect()); continue; }
      const walk = document.createTreeWalker(el, NodeFilter.SHOW_TEXT), rg = document.createRange();
      for (let n = walk.nextNode(); n; n = walk.nextNode()) if (n.textContent.trim()) { rg.selectNodeContents(n); take(rg.getBoundingClientRect()); }
      for (const svg of el.querySelectorAll('svg,img')) take(svg.getBoundingClientRect());
    }
    const wide = W >= H * 1.1 && W >= 900;
    if (wide) {
      const a = Math.min(0.19 * W, 0.285 * Math.sqrt(W * H)), b = Math.min(0.34 * H, 1.12 * a);
      const cx = Math.max(W - Math.max(0.185 * W, 1.02 * a), right + 44 + Math.max(a, b));
      E = [cx, 0.60 * H, a, b]; K = [-0.42, 1];
    } else {
      const r = 0.40 * W;
      E = [0.64 * W, Math.max(bottom + 36 + r * 1.02, H - r * 1.1), r, r * 1.02]; K = [-0.3, 0];
    }
    N = Math.round(0.0034 * W * H); ND = Math.round(0.0016 * W * H);
    gl.viewport(0, 0, cv.width, cv.height);
  };
  const set = (p, t) => {
    const u = L.get(p); gl.useProgram(p);
    gl.uniform2f(u.uRes, cv.width, cv.height); gl.uniform1f(u.uDpr, dpr); gl.uniform1f(u.uT, t);
    gl.uniform4fv(u.uE, E); gl.uniform2fv(u.uK, K); gl.uniform1f(u.uDust, 0);
  };
  const stats = (window.__planet = { frames: 0, ms: 0 });
  const render = (t) => {
    const t0 = performance.now();
    gl.disable(gl.BLEND); set(field, t); gl.drawArrays(gl.TRIANGLES, 0, 3);
    gl.enable(gl.BLEND); gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA); set(parts, t); gl.drawArrays(gl.POINTS, 0, N);
    gl.uniform1f(L.get(parts).uDust, 1); gl.drawArrays(gl.POINTS, 0, ND);
    stats.ms += (performance.now() - t0 - stats.ms) / ++stats.frames;
  };

  geom();
  const T0 = 190;                                     // start mid-flow, never on an empty first frame
  const still = freeze !== null || matchMedia('(prefers-reduced-motion: reduce)').matches;
  let raf = 0, last = 0, clock = 0;
  const loop = (now) => { clock += Math.min(50, now - (last || now)) * 0.06; last = now; render(T0 + clock); raf = requestAnimationFrame(loop); };
  const start = () => { if (still) render(freeze ?? T0); else if (!raf) { last = 0; raf = requestAnimationFrame(loop); } };
  const stop = () => { cancelAnimationFrame(raf); raf = 0; };
  document.addEventListener('visibilitychange', () => (document.hidden ? stop() : start()));
  let rt; addEventListener('resize', () => { clearTimeout(rt); rt = setTimeout(() => { geom(); if (still || !raf) render(T0 + clock); }, 120); });
  start();
  window.__fx = { render: (t) => { stop(); render(t); } };
})();
