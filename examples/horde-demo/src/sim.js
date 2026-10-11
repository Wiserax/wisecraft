// The whole game rule set, with no rendering and no browser APIs, so `node --test` and player-model bots can run it.
// Public API (keep it stable: tests and tools call it): createSim({ seed }) -> { step(dt), tap(x, z), state(), on(fn) }.
// Units: metres and seconds. The fort is a circle of radius FORT at the origin; enemies walk in from the rim.
export const TUNING = {
  rim: 30, // spawn distance
  fort: 3, // wall radius
  wallHp: 100,
  waveSeconds: 12,
  waveSize: [4, 4, 4, 4, 4, 4, 4, 4, 4, 4], // enemies per wave, stage 1
  enemy: { hp: 2, speed: 2.2, bite: 1, biteEvery: 1 },
  turret: { range: 16, damage: 1, every: 0.45 },
  tap: { radius: 1.6, damage: 2 },
  gold: { perKill: 1 },
};

// mulberry32: a tiny seeded generator, so a run can be replayed exactly
function rng(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function createSim({ seed = 1, tuning = TUNING } = {}) {
  const T = tuning,
    rand = rng(seed),
    listeners = [];
  const s = { time: 0, wave: 0, waveClock: 0, wall: T.wallHp, gold: 0, kills: 0, status: "running", enemies: [], cooldown: 0, nextId: 1, toSpawn: 0, spawnClock: 0 };
  const emit = (type, data = {}) => listeners.forEach((fn) => fn(type, data));

  function spawn() {
    const a = rand() * Math.PI * 2;
    s.enemies.push({ id: s.nextId++, x: Math.cos(a) * T.rim, z: Math.sin(a) * T.rim, hp: T.enemy.hp, bite: 0 });
  }
  function startWave() {
    s.wave++;
    s.waveClock = 0;
    s.toSpawn = T.waveSize[s.wave - 1];
    s.spawnClock = 0;
    emit("wave", { wave: s.wave });
  }
  function hurt(e, damage) {
    e.hp -= damage;
    if (e.hp <= 0) {
      s.enemies.splice(s.enemies.indexOf(e), 1);
      s.kills++;
      s.gold += T.gold.perKill;
      emit("kill", { id: e.id, x: e.x, z: e.z });
    }
  }
  function step(dt) {
    if (s.status !== "running") return;
    s.time += dt;
    if (s.wave === 0) startWave();
    s.waveClock += dt;
    // a wave's enemies arrive spread over its first half
    s.spawnClock -= dt;
    if (s.toSpawn > 0 && s.spawnClock <= 0) {
      spawn();
      s.toSpawn--;
      s.spawnClock = T.waveSeconds / 2 / T.waveSize[s.wave - 1];
    }
    for (const e of s.enemies) {
      const d = Math.hypot(e.x, e.z);
      if (d > T.fort + 0.4) {
        e.x -= (e.x / d) * T.enemy.speed * dt;
        e.z -= (e.z / d) * T.enemy.speed * dt;
      } else if ((e.bite -= dt) <= 0) {
        e.bite = T.enemy.biteEvery;
        s.wall = Math.max(0, s.wall - T.enemy.bite);
        emit("wall", { wall: s.wall });
      }
    }
    // one turret on the fort shoots the nearest enemy in range
    s.cooldown -= dt;
    if (s.cooldown <= 0) {
      let best = null,
        bd = T.turret.range;
      for (const e of s.enemies) {
        const d = Math.hypot(e.x, e.z);
        if (d < bd) [best, bd] = [e, d];
      }
      if (best) {
        s.cooldown = T.turret.every;
        emit("shot", { id: best.id, x: best.x, z: best.z });
        hurt(best, T.turret.damage);
      }
    }
    if (s.wall <= 0) {
      s.status = "lost";
      emit("lost", { wave: s.wave });
    } else if (s.waveClock >= T.waveSeconds && s.toSpawn === 0) {
      if (s.wave >= T.waveSize.length) {
        if (s.enemies.length === 0) {
          s.status = "cleared";
          emit("cleared", { wall: s.wall });
        }
      } else startWave();
    }
  }
  // a tap on the field at (x, z) hurts every enemy inside the tap radius
  function tap(x, z) {
    for (const e of [...s.enemies]) if (Math.hypot(e.x - x, e.z - z) <= T.tap.radius) hurt(e, T.tap.damage);
  }
  const state = () => ({ time: s.time, wave: s.wave, waves: T.waveSize.length, wall: s.wall, wallMax: T.wallHp, gold: s.gold, kills: s.kills, status: s.status, enemies: s.enemies.map((e) => ({ ...e })) });
  return { step, tap, state, on: (fn) => listeners.push(fn), tuning: T };
}
