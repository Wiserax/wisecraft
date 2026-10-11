// Screenshot the site and the README media templates. Local tool, not part of the site.
//   node scripts/shoot.mjs <folder that has node_modules/playwright> <media templates .html>
// Writes docs/media/{banner,pipeline,before-after-*,benchmark-*}.png, docs/media/badges/*.png, and into _preview/:
// site-desktop.png (1440x900), site-mobile.png (390x844), tile.png (the teaser's end tile). Needs the network once,
// for the two Google Fonts. Prints any console error the site raised.
import { createRequire } from "node:module";
import path from "node:path";
import fs from "node:fs";
import { fileURLToPath, pathToFileURL } from "node:url";

const [pwRoot, mediaPage] = process.argv.slice(2);
const require = createRequire(path.resolve(pwRoot) + "/");
const { chromium } = require("playwright");
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const site = pathToFileURL(path.join(ROOT, "docs/index.html")).href;
const out = (p) => { const f = path.join(ROOT, p); fs.mkdirSync(path.dirname(f), { recursive: true }); return f; };

const browser = await chromium.launch({ channel: "chrome", args: ["--mute-audio"] });
const errors = [];
async function page(viewport, scale = 1) {
  const ctx = await browser.newContext({ viewport, deviceScaleFactor: scale, colorScheme: "dark" });
  const p = await ctx.newPage();
  p.on("console", (m) => m.type() === "error" && errors.push(m.text()));
  p.on("pageerror", (e) => errors.push(String(e)));
  return p;
}
const settle = async (p) => { await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(500); };

let p = await page({ width: 1440, height: 900 });
await p.goto(site); await settle(p);
await p.screenshot({ path: out("_preview/site-desktop.png") });
await p.screenshot({ path: out("_preview/site-full.png"), fullPage: true });
p = await page({ width: 390, height: 844 }, 2);
await p.goto(site); await settle(p);
await p.screenshot({ path: out("_preview/site-mobile.png") });
const overflow = await p.evaluate(() => document.documentElement.scrollWidth - innerWidth);
p = await page({ width: 1280, height: 640 });
await p.goto(site + "#banner"); await settle(p);
await p.screenshot({ path: out("docs/media/banner.png") });

if (mediaPage) {
  for (const scale of [1, 2]) {
    p = await page({ width: 1000, height: 900 }, scale);
    await p.goto(pathToFileURL(path.resolve(mediaPage)).href); await settle(p);
    for (const el of await p.$$("[data-shot]")) {
      const name = await el.getAttribute("data-shot"), want = Number((await el.getAttribute("data-scale")) || 1);
      if (want !== scale) continue;
      const file = name.startsWith("@") ? out(`_preview/${name.slice(1)}.png`) : out(`docs/media/${name}.png`);
      await el.screenshot({ path: file, omitBackground: !!(await el.getAttribute("data-clear")) });
    }
  }
}
// five seconds of the hero in motion (webm; convert with ffmpeg), and what a frame of the animation costs
const vctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, colorScheme: "dark", recordVideo: { dir: out("_preview/video/x").replace(/x$/, ""), size: { width: 1440, height: 900 } } });
const vp = await vctx.newPage();
vp.on("pageerror", (e) => errors.push(String(e)));
await vp.goto(site); await vp.waitForTimeout(5600);
const planet = await vp.evaluate(() => (window.__planet ? { ...window.__planet, ms: +window.__planet.ms.toFixed(2) } : null));
const video = await vp.video().path();
await vctx.close();
const still = await browser.newContext({ viewport: { width: 1440, height: 900 }, reducedMotion: "reduce" });
const sp = await still.newPage(); await sp.goto(site); await sp.waitForTimeout(700);
const reduced = await sp.evaluate(() => (window.__planet ? window.__planet.frames : null));
await browser.close();
console.log(JSON.stringify({ errors, mobileOverflowPx: overflow, planet, framesWithReducedMotion: reduced, video }));
