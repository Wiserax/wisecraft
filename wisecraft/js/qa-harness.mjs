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
  block = [], noOverflow = false, timeoutMs = 60000, persona = "casual", buy = null, maxP95 = null,
} = opts;
// How each virtual player behaves: taps per second in the play area, and how often it looks for something to buy.
const PERSONAS = {
  casual: { rate: 2, spendEvery: 0 },       // taps now and then, buys nothing: the default smoke run
  tapper: { rate: 5, spendEvery: 0 },       // hammers the field: finds what taps break (bosses deleted, double grants)
  idler: { rate: 0.2, spendEvery: 0 },      // sets the phone down: timers, idle income, piles that grow unattended
  spender: { rate: 1, spendEvery: 2 },      // buys whatever in-game currency allows, every 2 actions; never real money
};
const P = PERSONAS[persona] || PERSONAS.casual;
const pw = loadPlaywright(opts);
await fs.mkdir(out, { recursive: true });

// Never make sound: Chromium is muted by flag; WebKit routes every AudioContext through a zero-gain node.
const { browser, channel } = engine === "webkit" ? await launchWebkit(pw) : await launchChromium(pw, opts);
const ctx = await browser.newContext({ viewport: { width: W, height: H }, isMobile: true, hasTouch: true, deviceScaleFactor: dpr });
let blocked = 0;
const answered = new WeakSet(); // requests this harness answered itself (--block); Chromium reports a fulfilled beacon as aborted
// Nothing is intercepted by default: analytics and every other request reach the real servers.
for (const pattern of block) {
  await ctx.route(pattern, (r) => { blocked++; answered.add(r.request()); return r.fulfill({ status: 200, body: "" }); }); // opt-in --block only
}
// Frame times from requestAnimationFrame, collected from the first frame on (read at the end).
await ctx.addInitScript(() => {
  const f = (window.__wiseFrames = []);
  let last = 0;
  const tick = (t) => { if (last && f.length < 50000) f.push(t - last); last = t; requestAnimationFrame(tick); };
  requestAnimationFrame(tick);
});
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
// Chromium reports a request as aborted when the page never reads a body the server already sent in full
// (a fire-and-forget analytics fetch): the server answered, so that is not a failure.
const answeredByServer = (r) => r.failure()?.errorText === "net::ERR_ABORTED" && r.timing().responseEnd > 0;
page.on("requestfailed", (r) => answered.has(r) || answeredByServer(r) || push(failedRequests, { url: r.url(), method: r.method(), error: r.failure()?.errorText || "failed" }));
page.on("response", (r) => { if (r.status() >= 400) push(failedRequests, { url: r.url(), method: r.request().method(), status: r.status() }); });
page.on("dialog", (d) => d.dismiss().catch(() => {}));
// Requests reach real servers, so let the ones still in flight finish before the browser closes.
const inFlight = new Set();
page.on("request", (r) => inFlight.add(r));
page.on("requestfinished", (r) => inFlight.delete(r));
page.on("requestfailed", (r) => inFlight.delete(r));
const settle = async (ms = 3000) => { const end = Date.now() + ms; while (inFlight.size && Date.now() < end) await page.waitForTimeout(50); };

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
    hooks: Object.getOwnPropertyNames(window).filter((k) => k.startsWith("__") && !/^__(pw|playwright|wise)/i.test(k)),
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

// The spender: tap the visible control that says buy / upgrade / claim / open, least-tapped first. Anything that
// shows a real-money price or says pay / purchase / subscribe is never touched: spending real money needs a yes.
const spends = [], spentOn = {};
const spend = async () => {
  const pick = await page.evaluate(({ sel, counts }) => {
    const BUY = /buy|upgrade|claim|collect|unlock|open|level ?up|spin|pull|summon|chest|reward|get\b/i;
    const MONEY = /[$€£¥₹]|\b(usd|eur|gbp|pay|purchase|subscribe|checkout|billing)\b|\d+[.,]\d{2}\b/i;
    const vw = innerWidth, vh = innerHeight, list = [];
    for (const el of document.querySelectorAll(sel || 'button, [role="button"], [data-action], a[href="#"], [onclick]')) {
      const r = el.getBoundingClientRect(), cs = getComputedStyle(el);
      if (r.width < 8 || r.height < 8 || r.right < 0 || r.bottom < 0 || r.left > vw || r.top > vh) continue;
      if (el.disabled || el.getAttribute("aria-disabled") === "true" || cs.visibility === "hidden" || cs.pointerEvents === "none" || Number(cs.opacity) < 0.1) continue;
      const text = [el.innerText, el.getAttribute("aria-label"), el.title, el.dataset?.action].filter(Boolean).join(" ").trim().slice(0, 60);
      if (MONEY.test(text) || (!sel && !BUY.test(text))) continue;
      const at = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
      if (at && at !== el && !el.contains(at)) continue;          // covered by something else
      list.push({ label: text || el.tagName.toLowerCase(), x: r.left + r.width / 2, y: r.top + r.height / 2 });
    }
    list.sort((a, b) => (counts[a.label] || 0) - (counts[b.label] || 0));
    return list[0] || null;
  }, { sel: buy, counts: spentOn }).catch(() => null);
  if (!pick) return false;
  try { await page.touchscreen.tap(pick.x, pick.y); } catch { return false; }
  spentOn[pick.label] = (spentOn[pick.label] || 0) + 1;
  if (spends.length < 200) spends.push({ at: +((Date.now() - t0) / 1000).toFixed(1), label: pick.label });
  return true;
};

// mulberry32: the same seed taps the same points
let s = seed >>> 0;
const rnd = () => { s = (s + 0x6d2b79f5) >>> 0; let t = s; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
const total = Math.max(0, Math.round(opts.taps ?? seconds * P.rate));
const interval = total ? (seconds * 1000) / total : 0;
const pad = 0.06;
let done = 0;
const t0 = Date.now();
for (let i = 0; i < total; i++) {
  if (i === Math.floor(total / 2)) { await shot("2-middle"); await checkOverflow("middle"); }
  if (P.spendEvery && i % P.spendEvery === P.spendEvery - 1 && (await spend())) {
    await page.waitForTimeout(Math.max(0, t0 + (i + 1) * interval - Date.now()));
    continue;
  }
  const x = box.x + box.w * (pad + rnd() * (1 - 2 * pad)), y = box.y + box.h * (pad + rnd() * (1 - 2 * pad));
  try { await page.touchscreen.tap(x, y); done++; } catch (e) { push(errors, "tap: " + String(e.message).split("\n")[0]); break; }
  await page.waitForTimeout(Math.max(0, t0 + (i + 1) * interval - Date.now()));
}
if (!total) { await page.waitForTimeout(seconds * 500); await shot("2-middle"); await checkOverflow("middle"); await page.waitForTimeout(seconds * 500); }
// --------------------------------------------------------------------------------------------
await shot("3-end");
await checkOverflow("end");
// Frame times since the page started: a headless browser is not a phone, so read them as a comparison between
// builds on the same machine, not as the fps a player gets.
const frames = await page.evaluate(() => (window.__wiseFrames || []).slice()).catch(() => []);
const sorted = frames.slice(1).sort((a, b) => a - b);   // the first interval includes page start-up
const q = (p) => (sorted.length ? +sorted[Math.min(sorted.length - 1, Math.floor(p * sorted.length))].toFixed(1) : null);
const ms = sorted.reduce((a, b) => a + b, 0);
const frameTime = { frames: sorted.length, fps: ms ? +(sorted.length * 1000 / ms).toFixed(1) : null, p50: q(0.5), p95: q(0.95), p99: q(0.99),
  over33: sorted.filter((d) => d > 33.4).length, worst: sorted.length ? +sorted[sorted.length - 1].toFixed(1) : null, maxP95 };
if (maxP95 != null && frameTime.p95 != null && frameTime.p95 > maxP95) push(errors, `frame time: p95 ${frameTime.p95} ms > --max-p95 ${maxP95} ms`);
await settle();
await browser.close();

const ok = errors.length === 0 && (noOverflow || overflow.length === 0);
console.log(JSON.stringify({
  url, engine, size: `${W}x${H}`, ok, errors, overflow, failedRequests, screenshots, game,
  ready: readyState, steps, persona, spends, frameTime, taps: { done, planned: total, seconds, seed, area: box }, blocked: { patterns: block, requests: blocked },
  gate: { errors: true, overflow: !noOverflow }, channel, out, ms: Date.now() - started,
}));
process.exit(ok ? 0 : 1);
