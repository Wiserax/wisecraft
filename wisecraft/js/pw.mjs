// Shared by the scripts `wise` drives: read the options, load Playwright from wherever the CLI found it,
// launch a browser that can never make sound.
import { createRequire } from "node:module";

export const INSTALL = "npm i -D playwright && npx playwright install chromium webkit";

// One JSON argument carries every option, so nothing is lost to shell quoting.
export function readOptions() {
  try {
    return JSON.parse(process.argv[2] || "");
  } catch {
    fatal(`expected one JSON argument with the options (this script is driven by the wise CLI)`);
  }
}

// Exit 2: the run could not start (Playwright or a browser is missing). The CLI prints the message.
export function fatal(message) {
  console.log(JSON.stringify({ fatal: message }));
  process.exit(2);
}

// `opts.playwright` is the entry file the CLI resolved (cwd, --playwright DIR or WISE_PLAYWRIGHT);
// a bare `playwright` next to this script is the fallback.
export function loadPlaywright(opts) {
  const require = createRequire(import.meta.url);
  try {
    return require(opts.playwright || "playwright");
  } catch (e) {
    fatal(`playwright could not be loaded (${String(e.message).split("\n")[0]}). Install it: ${INSTALL}`);
  }
}

// Chromium is muted by flag. When Playwright's own Chromium was never downloaded, the system Chrome
// does the same job, and the result says so in `channel`.
export async function launchChromium(pw, opts = {}) {
  const base = { headless: true, args: ["--mute-audio"] };
  try {
    if (opts.channel) return { browser: await pw.chromium.launch({ ...base, channel: opts.channel }), channel: opts.channel };
    try {
      return { browser: await pw.chromium.launch(base), channel: null };
    } catch (e) {
      if (!/Executable doesn't exist|playwright install/i.test(String(e.message))) throw e;
      return { browser: await pw.chromium.launch({ ...base, channel: "chrome" }), channel: "chrome" };
    }
  } catch (e) {
    fatal(`chromium could not start (${String(e.message).split("\n")[0]}). Install the browsers: npx playwright install chromium webkit`);
  }
}

export async function launchWebkit(pw) {
  try {
    return { browser: await pw.webkit.launch({ headless: true }), channel: null };
  } catch (e) {
    fatal(`webkit could not start (${String(e.message).split("\n")[0]}). Install the browsers: npx playwright install chromium webkit`);
  }
}
