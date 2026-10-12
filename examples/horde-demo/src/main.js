// Rendering and input only: every rule lives in sim.js. three.js draws the field from straight above.
import * as THREE from "three";
import { createSim, TUNING } from "./sim.js";

const canvas = document.getElementById("field");
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
const scene = new THREE.Scene();
scene.background = new THREE.Color("#14121c");
const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 100);
camera.position.set(0, 50, 0);
camera.lookAt(0, 0, 0);
const ground = new THREE.Mesh(new THREE.CircleGeometry(TUNING.rim + 2, 64), new THREE.MeshBasicMaterial({ color: "#221d33" }));
ground.rotation.x = -Math.PI / 2;
const fort = new THREE.Mesh(new THREE.CylinderGeometry(TUNING.fort, TUNING.fort, 1, 24), new THREE.MeshBasicMaterial({ color: "#ffb020" }));
const MAX = 512;
const horde = new THREE.InstancedMesh(new THREE.BoxGeometry(0.9, 0.9, 0.9), new THREE.MeshBasicMaterial({ color: "#8fe07a" }), MAX);
scene.add(ground, fort, horde);

function resize() {
  const w = innerWidth, h = innerHeight, half = TUNING.rim + 3, aspect = w / h;
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.setSize(w, h, false);
  // fit the whole field on the short side of the screen
  camera.left = -half * Math.max(1, aspect); camera.right = half * Math.max(1, aspect);
  camera.top = half * Math.max(1, 1 / aspect); camera.bottom = -half * Math.max(1, 1 / aspect);
  camera.updateProjectionMatrix();
}
addEventListener("resize", resize);
resize();

const sim = createSim({ seed: Date.now() % 100000 });
// analytics: one small event per wave; automated runs send it too, so the dashboard sees the real build
sim.on((type, data) => {
  if (type === "wave" || type === "lost" || type === "cleared") navigator.sendBeacon?.("/api/events", JSON.stringify({ type, ...data, version: "0.1.0" }));
});

canvas.addEventListener("pointerdown", (ev) => {
  const p = new THREE.Vector3((ev.clientX / innerWidth) * 2 - 1, -(ev.clientY / innerHeight) * 2 + 1, 0).unproject(camera);
  sim.tap(p.x, p.z);
});

const m = new THREE.Matrix4(), el = (id) => document.getElementById(id);
let last = performance.now();
function frame(now) {
  const dt = Math.min(0.05, (now - last) / 1000);
  last = now;
  sim.step(dt);
  const s = sim.state();
  horde.count = Math.min(MAX, s.enemies.length);
  s.enemies.slice(0, MAX).forEach((e, i) => horde.setMatrixAt(i, m.makeTranslation(e.x, 0.5, e.z)));
  horde.instanceMatrix.needsUpdate = true;
  el("wave").textContent = `Wave ${s.wave} / ${s.waves}`;
  el("wall").textContent = `Walls ${Math.round(s.wall)}`;
  el("gold").textContent = `Gold ${s.gold}`;
  if (s.status !== "running") Object.assign(el("end"), { textContent: s.status === "cleared" ? "Stage clear" : "The fort fell" }).style.display = "grid";
  renderer.render(scene, camera);
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);

// debug hook for QA and bots: step time, read state, tap. It never grants rewards.
window.__game = { sim, state: () => sim.state(), step: (seconds) => { for (let t = 0; t < seconds; t += 1 / 60) sim.step(1 / 60); }, tap: (x, z) => sim.tap(x, z) };
