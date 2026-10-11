// Render mockup screens and a composed board to PNG, driven by `wise board`.
// Usage: node render-board.mjs '<options JSON>'    (wisecraft/board.py builds the options)
// Each screen in mockups.html is an element with an id (e.g. <div class="screen" id="s1">), 390x844 CSS px.
// Prints one JSON line: the screens written, their sizes, the board PNG.
import path from "node:path";
import fs from "node:fs/promises";
import { pathToFileURL } from "node:url";
import { readOptions, loadPlaywright, launchChromium } from "./pw.mjs";

const opts = readOptions();
const { mockups, out = "shots", ids = [], board = null, width: W = 390, height: H = 844, scale = 2 } = opts;
const pw = loadPlaywright(opts);
await fs.mkdir(out, { recursive: true });
const { browser: b, channel } = await launchChromium(pw, opts);
const p = await b.newPage({ viewport: { width: Math.max(1800, W * 4 + 240), height: Math.max(1200, H + 200) }, deviceScaleFactor: scale });
await p.goto(pathToFileURL(path.resolve(mockups)).href);
await p.evaluate(() => document.fonts.ready);
// .screen elements when the page marks them; otherwise every element with an id, as before
const list = ids.length ? ids : await p.evaluate(() => {
  const marked = [...document.querySelectorAll(".screen[id]")].map((e) => e.id);
  return marked.length ? marked : [...document.querySelectorAll("[id]")].map((e) => e.id);
});
const screens = [], warnings = [];
for (const id of list) {
  const loc = p.locator(`[id="${id.replace(/"/g, '\\"')}"]`).first();
  if (!(await loc.count())) { warnings.push(`no element with id "${id}"`); continue; }
  const box = await loc.boundingBox();
  const file = path.join(out, id + ".png");
  await loc.screenshot({ path: file });
  const w = Math.round(box?.width ?? 0), h = Math.round(box?.height ?? 0);
  screens.push({ id, file, width: w, height: h });
  if (w !== W || h !== H) warnings.push(`#${id} is ${w}x${h} CSS px, not ${W}x${H}`);
}
let boardPng = null;
if (board) {
  const q = await b.newPage({ viewport: { width: 1760, height: 1000 }, deviceScaleFactor: 1 });
  await q.goto(pathToFileURL(path.resolve(board)).href);
  await q.evaluate(() => document.fonts.ready);
  const missing = await q.evaluate(() => [...document.images].filter((i) => !i.complete || !i.naturalWidth).map((i) => i.getAttribute("src")));
  for (const src of missing) warnings.push(`board image did not load: ${src}`);
  boardPng = opts.boardOut || board.replace(/\.html?$/i, "") + ".png";
  await q.screenshot({ path: boardPng, fullPage: true });
}
await b.close();
console.log(JSON.stringify({ screens, board: boardPng, warnings, channel, size: `${W}x${H}`, scale }));
