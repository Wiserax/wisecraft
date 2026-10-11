// Render mockup screens and a composed board to PNG. Fallback for `wise board`.
// Needs Playwright: npm i -D playwright && npx playwright install chromium
// Usage: node render-board.mjs <mockups.html> <outDir> [ids comma-separated] [--board board.html]
// Each screen in mockups.html is an element with an id (e.g. <div class="screen" id="s1">), 390x844 CSS px.
import { chromium } from "playwright";
import path from "node:path";
import fs from "node:fs/promises";

const [file, outDir = "shots", ids = "", ...rest] = process.argv.slice(2);
const boardIdx = rest.indexOf("--board");
await fs.mkdir(outDir, { recursive: true });
const b = await chromium.launch({ headless: true, args: ["--mute-audio"] });
const p = await b.newPage({ viewport: { width: 1800, height: 1200 }, deviceScaleFactor: 2 });
await p.goto("file://" + path.resolve(file));
await p.evaluate(() => document.fonts.ready);
const list = ids ? ids.split(",") : await p.$$eval("[id]", (els) => els.map((e) => e.id));
for (const id of list) await p.locator("#" + id).screenshot({ path: path.join(outDir, id + ".png") });
if (boardIdx >= 0) {
  const board = rest[boardIdx + 1];
  const q = await b.newPage({ viewport: { width: 1760, height: 1000 }, deviceScaleFactor: 1 });
  await q.goto("file://" + path.resolve(board));
  await q.evaluate(() => document.fonts.ready);
  await q.screenshot({ path: board.replace(/\.html$/, ".png"), fullPage: true });
}
await b.close();
console.log("rendered", list.length, "screens");
