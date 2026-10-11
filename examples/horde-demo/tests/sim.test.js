import test from "node:test";
import assert from "node:assert/strict";
import { createSim, TUNING } from "../src/sim.js";

const run = (sim, seconds, dt = 1 / 30) => {
  for (let t = 0; t < seconds; t += dt) sim.step(dt);
  return sim.state();
};

test("the same seed replays the same siege", () => {
  const a = run(createSim({ seed: 7 }), 40),
    b = run(createSim({ seed: 7 }), 40);
  assert.deepEqual(a, b);
});

test("enemies start at the rim and walk towards the fort", () => {
  const sim = createSim({ seed: 3 });
  sim.step(0.05);
  const [e] = sim.state().enemies;
  assert.ok(Math.abs(Math.hypot(e.x, e.z) - TUNING.rim) < 0.5, "spawned at the rim");
  const before = Math.hypot(e.x, e.z);
  run(sim, 1);
  const again = sim.state().enemies.find((x) => x.id === e.id);
  assert.ok(!again || Math.hypot(again.x, again.z) < before, "it came closer (or was shot)");
});

test("a tap hurts enemies inside its radius only", () => {
  const sim = createSim({ seed: 5 });
  sim.step(0.05);
  const [e] = sim.state().enemies;
  sim.tap(e.x + 10, e.z + 10);
  assert.equal(sim.state().kills, 0);
  sim.tap(e.x, e.z);
  assert.equal(sim.state().kills, 1);
});
