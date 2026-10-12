// Player-model bots: play a game's headless simulation with several kinds of player, on several seeds, and print
// one table per model. The same seeds before and after a change make the two tables comparable.
//
//   node bots.mjs <path/to/sim.js> [--seeds 8] [--seconds 240] [--models passive,casual,tapper,attentive] [--json]
//
// The sim must export createSim({ seed }) -> { step(dt), tap(x, z), state() }, with state() returning
// { time, wall, wallMax, status: "running" | "cleared" | "lost", enemies: [{ x, z, hp }], gold? }.
// Optional, for buying models: sim.offers() -> [{ id, price, kind? }] and sim.buy(id) -> boolean.
// ADAPT the two functions marked ADAPT below when your game's API differs; keep everything else.
import path from "node:path";
import { pathToFileURL } from "node:url";

const args = process.argv.slice(2);
const flag = (name, dflt) => { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : dflt; };
const file = args.find((a) => !a.startsWith("--") && !args[args.indexOf(a) - 1]?.startsWith("--"));
if (!file) { console.error("usage: node bots.mjs <sim.js> [--seeds 8] [--seconds 240] [--models a,b] [--json]"); process.exit(2); }
const SEEDS = Number(flag("--seeds", 8)), SECONDS = Number(flag("--seconds", 240)), DT = 1 / 30;
const mod = await import(pathToFileURL(path.resolve(file)).href);

// Each model is a habit, not a strategy: how often it taps, what it taps, and what it buys.
// A passive player never taps; a casual one taps now and then at random; a heavy tapper taps fast at the nearest
// enemy; an attentive one taps the nearest enemy twice a second and buys the cheapest offer it can afford.
const MODELS = {
  passive: { tapsPerSecond: 0, aim: "none", buys: "none" },
  casual: { tapsPerSecond: 0.7, aim: "random", buys: "first" },
  tapper: { tapsPerSecond: 2, aim: "nearest", buys: "attack" },
  attentive: { tapsPerSecond: 2, aim: "nearest", buys: "cheapest" },
};
const wanted = flag("--models", Object.keys(MODELS).join(",")).split(",");

// ADAPT: what the game offers right now, and how to buy it. Without offers() the models only tap.
const offers = (sim) => (typeof sim.offers === "function" ? sim.offers() : []);
const buy = (sim, id) => (typeof sim.buy === "function" ? sim.buy(id) : false);

function rng(seed) { let a = seed >>> 0; return () => { a = (a + 0x6d2b79f5) >>> 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }

function play(name, seed) {
  const m = MODELS[name], sim = mod.createSim({ seed }), rand = rng(seed * 7919 + 1);
  let tapClock = 0, buyClock = 0, firstHit = null, bought = 0;
  const lows = [];
  for (let t = 0; t < SECONDS; t += DT) {
    const s = sim.state();
    if (s.status !== "running") break;
    if (m.tapsPerSecond && (tapClock -= DT) <= 0 && s.enemies.length) {
      tapClock = 1 / m.tapsPerSecond;
      const e = m.aim === "random" ? s.enemies[Math.floor(rand() * s.enemies.length)]
        : s.enemies.reduce((a, b) => (Math.hypot(a.x, a.z) < Math.hypot(b.x, b.z) ? a : b));
      sim.tap(e.x, e.z);
    }
    if (m.buys !== "none" && (buyClock -= DT) <= 0) {
      buyClock = 1;
      const can = offers(sim).filter((o) => o.price <= (s.gold ?? 0));
      const pick = m.buys === "cheapest" ? can.sort((a, b) => a.price - b.price)[0]
        : m.buys === "attack" ? can.find((o) => /attack|damage|gun|tower/i.test(o.kind ?? o.id)) : can[0];
      if (pick && buy(sim, pick.id)) bought++;
    }
    sim.step(DT);
    const after = sim.state();
    if (firstHit === null && after.wall < after.wallMax) firstHit = after.time;
    if (Math.floor(after.time / 5) !== Math.floor((after.time - DT) / 5)) lows.push(after.wall);
  }
  const end = sim.state();
  return { seed, status: end.status, time: +end.time.toFixed(1), wall: +(100 * end.wall / end.wallMax).toFixed(0), firstHit: firstHit === null ? null : +firstHit.toFixed(1), bought };
}

const stats = (xs) => { const v = xs.filter((x) => x != null); if (!v.length) return null; const mean = v.reduce((a, b) => a + b, 0) / v.length; return { min: Math.min(...v), mean: +mean.toFixed(1), max: Math.max(...v) }; };
const report = {};
for (const name of wanted) {
  if (!MODELS[name]) { console.error(`unknown model ${name}; known: ${Object.keys(MODELS).join(", ")}`); process.exit(2); }
  const runs = Array.from({ length: SEEDS }, (_, i) => play(name, i + 1));
  report[name] = { runs, cleared: runs.filter((r) => r.status === "cleared").length, lost: runs.filter((r) => r.status === "lost").length,
    wallLeft: stats(runs.map((r) => r.wall)), firstHit: stats(runs.map((r) => r.firstHit)), fallAt: stats(runs.filter((r) => r.status === "lost").map((r) => r.time)) };
}
if (args.includes("--json")) { console.log(JSON.stringify({ seeds: SEEDS, seconds: SECONDS, report })); process.exit(0); }
const f = (s) => (s ? `${s.min}-${s.max} (mean ${s.mean})` : "-");
console.log(`player-model bots: ${SEEDS} seeds, up to ${SECONDS} s, sim step ${(DT * 1000).toFixed(1)} ms`);
console.log(["model".padEnd(10), "cleared", "lost", "running", "walls left %".padEnd(22), "first wall hit s".padEnd(22), "fell at s"].join("  "));
for (const [name, r] of Object.entries(report)) {
  console.log([name.padEnd(10), String(r.cleared).padStart(7), String(r.lost).padStart(4), String(SEEDS - r.cleared - r.lost).padStart(7), f(r.wallLeft).padEnd(22), f(r.firstHit).padEnd(22), f(r.fallAt)].join("  "));
}
