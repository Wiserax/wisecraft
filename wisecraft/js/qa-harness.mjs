// Muted real-browser QA harness (Chromium + WebKit, phone viewports), driven by `wise qa`.
// Usage: node qa-harness.mjs '<options JSON>'      (wisecraft/qa.py builds the options)
// Prints one JSON line. The gate is: errors [] and overflow []. Exit 0 pass, 1 gate, 2 could not start.
import fs from "node:fs/promises";
import path from "node:path";
import { readOptions, loadPlaywright, launchChromium, launchWebkit } from "./pw.mjs";

const opts = readOptions();
const {
  url, engine = "chromium", width: W = 390, height: H = 844, dpr = 2, out = "qa-out", seconds = 20, seed = 1,
  selectors = [], startSelector = null, area = null, ready = 'document.readyState === "complete"',
  block = ["**/api/events"], noOverflow = false, timeoutMs = 60000,
} = opts;
const pw = loadPlaywright(opts);
await fs.mkdir(out, { recursive: true });

// Never make sound: Chromium is muted by flag; WebKit routes every AudioContext through a zero-gain node.
const { browser, channel } = engine === "webkit" ? await launchWebkit(pw) : await launchChromium(pw, opts);
const ctx = await browser.newContext({ viewport: { width: W, height: H }, isMobile: true, hasTouch: true, deviceScaleFactor: dpr });
let blocked = 0;
const answered = new WeakSet(); // requests this harness answered itself; Chromium reports a fulfilled beacon as aborted
for (const pattern of block) {
  await ctx.route(pattern, (r) => { blocked++; answered.add(r.request()); return r.fulfill({ status: 204 }); }); // keep test runs out of analytics
}
await ctx.addInitScript(() => {
  // <audio>/<video> elements never reach the speakers either
  const play = HTMLMediaElement.prototype.play;
  HTMLMediaElement.prototype.play = function () { this.muted = true; return play.apply(this, arguments); };
  const AC = window.AudioContext || window.webkitAudioContext; if (!AC || !window.BaseAudioContext) return;
  const d = Object.getOwnPropertyDescriptor(BaseAudioContext.prototype, "destination");
  Object.defineProperty(AC.prototype, "destination", { get() {
    if (!this.__m) { const g = this.createGain(); g.gain.value = 0; g.connect(d.get.call(this)); this.__m = g; }
    return this.__m;
  } });
});

const page = await ctx.newPage();
const errors = [], failedRequests = [], screenshots = [], steps = [], overflow = [];
const push = (list, item, key = JSON.stringify(item)) => { if (list.length < 50 && !list.some((x) => JSON.stringify(x) === key)) list.push(item); };
page.on("pageerror", (e) => push(errors, "pageerror: " + e.message));
page.on("console", (m) => {
  if (m.type() !== "error") return;
  const at = m.location()?.url;
  push(errors, "console: " + m.text() + (at && at !== page.url() && !m.text().includes(at) ? ` (${at})` : ""));
});
page.on("requestfailed", (r) => answered.has(r) || push(failedRequests, { url: r.url(), method: r.method(), error: r.failure()?.errorText || "failed" }));
page.on("response", (r) => { if (r.status() >= 400) push(failedRequests, { url: r.url(), method: r.request().method(), status: r.status() }); });
page.on("dialog", (d) => d.dismiss().catch(() => {}));

const shot = async (name) => {
  const file = path.join(out, name + ".png");
  try { await page.screenshot({ path: file }); screenshots.push(file); } catch (e) { push(errors, `screenshot ${name}: ${String(e.message).split("\n")[0]}`); }
};

// Horizontal overflow: the document scrolls sideways, or a visible element crosses the right edge.
// The edge is the device width: a mobile browser zooms out to fit wide content, which makes innerWidth
// grow with it, so `scrollWidth > innerWidth` alone would never fire on a phone.
// Skipped: elements an ancestor (other than the page itself) clips, and decoration (no text and either
// pointer-events:none or aria-hidden), which is how full-bleed glows and vignettes are built.
const checkOverflow = async (at) => {
  let found = [];
  try {
    found = await page.evaluate(({ limit, device }) => {
      const vw = Math.min(window.innerWidth, device), de = document.documentElement, list = [];
      // without a viewport meta a phone lays the page out about 980 px wide and shrinks it: everything "overflows"
      if (!document.querySelector('meta[name="viewport"]') && window.innerWidth > device + 1) {
        return [{ kind: "viewport", selector: 'meta[name="viewport"]', layoutWidth: window.innerWidth, innerWidth: device }];
      }
      if (de.scrollWidth > vw + 1) list.push({ kind: "document", selector: "html", scrollWidth: de.scrollWidth, innerWidth: vw });
      const one = (el) => el.tagName.toLowerCase() + (el.id ? "#" + CSS.escape(el.id)
        : [...el.classList].slice(0, 2).map((c) => "." + CSS.escape(c)).join(""));
      const name = (el) => { const parts = []; for (let e = el; e && e !== document.body && parts.length < 3; e = e.parentElement) { parts.unshift(one(e)); if (e.id) break; } return parts.join(" > "); };
      const clipped = (el) => {
        for (let p = el.parentElement; p && p !== document.body && p !== de; p = p.parentElement) {
          if (getComputedStyle(p).overflowX !== "visible" && p.getBoundingClientRect().right <= vw + 1) return true;
        }
        return false;
      };
      const flagged = new Set();
      for (const el of document.body ? document.body.querySelectorAll("*") : []) {
        if (flagged.has(el.parentElement)) { flagged.add(el); continue; } // report the outermost element only
        const r = el.getBoundingClientRect();
        if (r.width < 1 || r.height < 1 || r.right <= vw + 1 || r.left >= vw) continue;
        const cs = getComputedStyle(el);
        if (cs.display === "none" || cs.visibility === "hidden" || Number(cs.opacity) === 0) continue;
        const decoration = !el.textContent.trim() && (cs.pointerEvents === "none" || el.closest('[aria-hidden="true"]'));
        if (decoration || clipped(el)) continue;
        flagged.add(el);
        if (list.length < limit) list.push({ kind: "element", selector: name(el), left: Math.round(r.left), right: Math.round(r.right), innerWidth: vw });
      }
      return list;
    }, { limit: 8, device: W });
  } catch (e) { push(errors, `overflow check (${at}): ${String(e.message).split("\n")[0]}`); }
  for (const o of found) if (!overflow.some((x) => x.selector === o.selector)) overflow.push({ ...o, at });
};

// A tap the way a finger does it; a DOM click is the fallback when something covers the element.
const tap = async (selector) => {
  const loc = page.locator(selector).first();
  if (!(await loc.count().catch(() => 0))) return { selector, found: false };
  try { await loc.tap({ timeout: 5000 }); return { selector, found: true, via: "tap" }; } catch {
    const ok = await page.evaluate((s) => { const el = document.querySelector(s); el?.click(); return !!el; }, selector).catch(() => false);
    return { selector, found: ok, via: "click" };
  }
};

const started = Date.now();
try { await page.goto(url, { waitUntil: "load", timeout: timeoutMs }); } catch (e) { push(errors, "navigation: " + String(e.message).split("\n")[0]); }
const readyState = { expression: ready, ok: true, ms: 0 };
try { await page.waitForFunction(ready, null, { timeout: timeoutMs }); } catch (e) {
  readyState.ok = false;
  push(errors, /Timeout/.test(e.message) ? `ready: not true after ${timeoutMs} ms: ${ready}` : "ready: " + String(e.message).split("\n")[0]);
}
readyState.ms = Date.now() - started;

// Debug hooks are reported, never driven: this run plays through the real UI.
const game = await page.evaluate(() => {
  const g = window.__game;
  return {
    found: g != null,
    keys: g != null && (typeof g === "object" || typeof g === "function") ? Object.keys(g) : [],
    hooks: Object.getOwnPropertyNames(window).filter((k) => k.startsWith("__") && !/^__(pw|playwright)/i.test(k)),
  };
}).catch(() => ({ found: false, keys: [], hooks: [] }));

await shot("1-start");
await checkOverflow("start");

// ---- JOURNEY: start button, the listed selectors in order, then taps in the play area ----
const journey = [...(startSelector ? [startSelector] : []), ...selectors];
for (const selector of journey) {
  const step = await tap(selector);
  steps.push(step);
  if (!step.found) push(errors, `selector not found: ${selector}`);
  await page.waitForTimeout(400);
  await shot(`step-${steps.length}`);
}

const box = await page.evaluate((sel) => {
  const vw = innerWidth, vh = innerHeight;
  let el = sel ? document.querySelector(sel) : null, source = sel;
  if (!sel) {
    let best = 0;
    for (const c of document.querySelectorAll("canvas")) {
      const r = c.getBoundingClientRect(), a = Math.max(0, Math.min(r.right, vw) - Math.max(r.left, 0)) * Math.max(0, Math.min(r.bottom, vh) - Math.max(r.top, 0));
      if (a > best) { best = a; el = c; source = "canvas"; }
    }
  }
  const r = el?.getBoundingClientRect();
  const b = r ? { x: Math.max(0, r.left), y: Math.max(0, r.top), w: Math.min(vw, r.right) - Math.max(0, r.left), h: Math.min(vh, r.bottom) - Math.max(0, r.top) } : null;
  return b && b.w >= 40 && b.h >= 40 ? { ...b, source } : { x: 0, y: 0, w: vw, h: vh, source: sel ? `viewport (${sel} not found or too small)` : "viewport" };
}, area).catch(() => ({ x: 0, y: 0, w: W, h: H, source: "viewport" }));

// mulberry32: the same seed taps the same points
let s = seed >>> 0;
const rnd = () => { s = (s + 0x6d2b79f5) >>> 0; let t = s; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
const total = Math.max(0, Math.round(opts.taps ?? seconds * 2));
const interval = total ? (seconds * 1000) / total : 0;
const pad = 0.06;
let done = 0;
const t0 = Date.now();
for (let i = 0; i < total; i++) {
  if (i === Math.floor(total / 2)) { await shot("2-middle"); await checkOverflow("middle"); }
  const x = box.x + box.w * (pad + rnd() * (1 - 2 * pad)), y = box.y + box.h * (pad + rnd() * (1 - 2 * pad));
  try { await page.touchscreen.tap(x, y); done++; } catch (e) { push(errors, "tap: " + String(e.message).split("\n")[0]); break; }
  await page.waitForTimeout(Math.max(0, t0 + (i + 1) * interval - Date.now()));
}
if (!total) { await page.waitForTimeout(seconds * 500); await shot("2-middle"); await checkOverflow("middle"); await page.waitForTimeout(seconds * 500); }
// --------------------------------------------------------------------------------------------
await shot("3-end");
await checkOverflow("end");
await browser.close();

const ok = errors.length === 0 && (noOverflow || overflow.length === 0);
console.log(JSON.stringify({
  url, engine, size: `${W}x${H}`, ok, errors, overflow, failedRequests, screenshots, game,
  ready: readyState, steps, taps: { done, planned: total, seconds, seed, area: box }, blocked: { patterns: block, requests: blocked },
  gate: { errors: true, overflow: !noOverflow }, channel, out, ms: Date.now() - started,
}));
process.exit(ok ? 0 : 1);
