// Muted real-browser QA harness template (Chromium + WebKit, phone viewports).
// For the gate and the persona bots use `wise qa <url>`; copy this file into the game repo when the flow is custom.
// Needs Playwright: npm i -D playwright && npx playwright install chromium webkit
// Usage: node journey.template.mjs <url> <outDir> [chromium|webkit] [390x844]
// Adapt the JOURNEY section to your game. The gate is: errors [] and overflow false.
import { chromium, webkit } from "playwright";
import fs from "node:fs/promises";

const [url, out = "qa-out", engine = "chromium", size = "390x844"] = process.argv.slice(2);
const [W, H] = size.split("x").map(Number);
await fs.mkdir(out, { recursive: true });

// Never make sound: Chromium is muted by flag; WebKit routes every AudioContext through a zero-gain node.
const browser = engine === "webkit"
  ? await webkit.launch({ headless: true })
  : await chromium.launch({ headless: true, args: ["--mute-audio"] });
const ctx = await browser.newContext({ viewport: { width: W, height: H }, isMobile: true, hasTouch: true, deviceScaleFactor: 2 });
// Every request, analytics included, goes to the real servers: nothing is intercepted.
await ctx.addInitScript(() => {
  const AC = window.AudioContext || window.webkitAudioContext; if (!AC) return;
  const d = Object.getOwnPropertyDescriptor(BaseAudioContext.prototype, "destination");
  Object.defineProperty(AC.prototype, "destination", { get() {
    if (!this.__m) { const g = this.createGain(); g.gain.value = 0; g.connect(d.get.call(this)); this.__m = g; }
    return this.__m;
  } });
});

const page = await ctx.newPage();
const errors = [], log = {};
page.on("pageerror", (e) => errors.push(e.message));
const shot = (n) => page.screenshot({ path: `${out}/${engine}-${W}-${n}.png` });
const click = (sel) => page.evaluate((s) => document.querySelector(s)?.click(), sel);

await page.goto(url);
// ---- JOURNEY (replace with your game's flow; use window.__game only to speed time or set up state) ----
await page.waitForFunction(() => window.__game, null, { timeout: 60000 });
await shot("1-first-screen");
// e.g. tap the field like a player, buy the first card, finish the run, open the hub, switch language...
// await click("[data-action=lang][data-id=es]"); await shot("2-hub-es");
// ----------------------------------------------------------------------------------------------------
log.overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1);
await browser.close();
console.log(JSON.stringify({ engine, size, log, errors }));
