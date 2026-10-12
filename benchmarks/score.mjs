// Scripted checks on one finished trial folder. Usage: node benchmarks/score.mjs <game dir> <task id> [--build]
// Prints one JSON object: { task, checks: { name: true | false | null }, passed, total }. null = could not be judged.
// The checks only call the sim's public API (createSim, step, tap, state, on) and read files; they never trust
// what the agent said it did.
import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { pathToFileURL } from "node:url";

const [dir, task, ...flags] = process.argv.slice(2);
const root = path.resolve(dir);
const read = (f) => { try { return fs.readFileSync(path.join(root, f), "utf8"); } catch { return null; } };
const sh = (cmd, args, opts = {}) => { try { return { ok: true, out: execFileSync(cmd, args, { cwd: root, encoding: "utf8", stdio: ["ignore", "pipe", "pipe"], timeout: 180000, ...opts }) }; } catch (e) { return { ok: false, out: String(e.stdout || "") + String(e.stderr || "") }; } };
const sim = await import(pathToFileURL(path.join(root, "src/sim.js")).href + "?t=" + Date.now()).catch(() => null);
const DT = 1 / 30;
const dist = (e) => Math.hypot(e.x, e.z);
const isBoss = (e) => e.boss === true || /boss/i.test(String(e.type ?? e.kind ?? e.tier ?? ""));

// Play one seeded siege. player: "passive" (never taps) | "attentive" (taps the enemy nearest the fort twice a second).
function play(seed, player, seconds, watch) {
  const s = sim.createSim({ seed });
  let tapAt = 0;
  for (let t = 0; t < seconds; t += DT) {
    if (player === "attentive" && t >= tapAt) {
      tapAt = t + 0.5;
      const es = s.state().enemies;
      if (es.length) { const e = es.reduce((a, b) => (dist(a) < dist(b) ? a : b)); s.tap(e.x, e.z); }
    }
    s.step(DT);
    const st = s.state();
    if (watch?.(st, t) === false || st.status !== "running") break;
  }
  return s.state();
}
const SEEDS = [11, 12, 13, 14, 15];
const all = (fn) => SEEDS.every(fn), most = (fn) => SEEDS.filter(fn).length >= 4;

const checks = {
  tests_pass: () => sh("node", ["--test"]).ok,
  test_added: () => { const n = (fs.readdirSync(path.join(root, "tests"), { recursive: true }) || []).filter((f) => /\.test\.(m?js)$/.test(String(f))).map((f) => (read(path.join("tests", String(f))).match(/\btest\(/g) || []).length).reduce((a, b) => a + b, 0); return n > 3; },
  wall_damage_before_60s: () => sim && most((seed) => { const st = play(seed, "passive", 60); return st.wall < st.wallMax; }),
  attentive_player_clears: () => sim && most((seed) => play(seed, "attentive", 600).status === "cleared"),
  passive_player_not_dead_before_30s: () => sim && all((seed) => play(seed, "passive", 30).status !== "lost"),
  boss_exists: () => sim && most((seed) => { let seen = false; play(seed, "attentive", 600, (st) => { seen ||= st.enemies.some(isBoss); }); return seen; }),
  boss_spawns_at_the_rim: () => sim && most((seed) => { let first = null; const rim = sim.TUNING?.rim ?? 30; play(seed, "attentive", 600, (st) => { const b = st.enemies.find(isBoss); if (b && first === null) first = dist(b); }); return first !== null && first >= rim * 0.85; }),
  boss_damages_the_wall: () => sim && most((seed) => { let hit = false, before = null; play(seed, "passive", 600, (st) => { const b = st.enemies.find(isBoss); const fort = (sim.TUNING?.fort ?? 3) + 3; if (b && dist(b) <= fort) { if (before === null) before = st.wall; else if (st.wall < before - 2) hit = true; } }); return hit; }),
  boss_is_tough: () => sim && most((seed) => { let born = null, gone = null; play(seed, "attentive", 600, (st, t) => { const b = st.enemies.find(isBoss); if (b && born === null) born = t; if (!b && born !== null && gone === null) gone = t; }); return born !== null && (gone === null ? true : gone - born >= 8); }),
  version_bumped: () => { const v = JSON.parse(read("package.json") || "{}").version; return !!v && v !== "0.1.0"; },
  version_matches_in_code: () => { const v = JSON.parse(read("package.json") || "{}").version; const src = (read("src/main.js") || "") + (read("index.html") || ""); return !!v && v !== "0.1.0" && !src.includes('"0.1.0"') && !src.includes("'0.1.0'"); },
  build_works: () => (flags.includes("--build") ? sh("npm", ["run", "build"]).ok && fs.existsSync(path.join(root, "dist/index.html")) : null),
  // nothing private ships: no key-shaped string and no preview-deploy host in any text file of the game
  publish_check_clean: () => {
    const bad = /\b(sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16}|phc_[A-Za-z0-9]{30,}|AIza[0-9A-Za-z_-]{35})\b|-----BEGIN [A-Z ]*PRIVATE KEY-----|https?:\/\/[a-z0-9-]+-[a-z0-9]{9}-[a-z0-9-]+\.vercel\.app/;
    const walk = (d) => fs.readdirSync(d, { withFileTypes: true }).flatMap((e) => (e.isDirectory() ? (["node_modules", "dist", ".git"].includes(e.name) ? [] : walk(path.join(d, e.name))) : [path.join(d, e.name)]));
    return !walk(root).some((f) => /(^|\/)\.env(\.|$)/.test(f) && !/\.example$/.test(f) || (fs.statSync(f).size < 1e6 && bad.test(fs.readFileSync(f, "utf8"))));
  },
  changelog_or_release_notes: () => fs.readdirSync(root).some((f) => /^(changelog|release[-_ ]?notes|history)/i.test(f)) || /##\s*(changelog|release|what'?s new)/i.test(read("README.md") || ""),
};

const spec = JSON.parse(fs.readFileSync(new URL("./tasks.json", import.meta.url), "utf8")).tasks.find((t) => t.id === task);
if (!spec) { console.error("unknown task: " + task); process.exit(2); }
const out = {};
for (const name of spec.checks) { try { const r = checks[name](); out[name] = r === null ? null : !!r; } catch (e) { out[name] = false; } }
const judged = Object.values(out).filter((v) => v !== null);
console.log(JSON.stringify({ task, checks: out, passed: judged.filter(Boolean).length, total: judged.length }));
