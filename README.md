<p align="center">
  <img src="docs/media/banner.png" alt="wisecraft: the game studio with the agents wired in. Skills, a CLI and field notes that let any AI coding agent build, balance, polish and ship a mobile web game. Install: /plugin marketplace add Wiserax/wisecraft, then /plugin install wisecraft@wisecraft." width="100%">
</p>

<p align="center">
  <b>Skills, tools and a shared knowledge base that let any AI coding agent build, balance, polish and ship a mobile web game.</b><br>
  The agent scans the game, builds one playable slice, tunes the economy with simulated players, cleans up the UI, measures the sound
  instead of guessing, proves it in a muted phone browser, ships it, cuts the trailer, and writes down what it learned for the next agent.
</p>

<p align="center">
  <a href="#install"><img alt="works with Claude Code, Codex, Cursor, Gemini CLI, GitHub Copilot and OpenCode" src="docs/media/badges/agents.png" height="26"></a>
  <a href="knowledge/INDEX.md"><img alt="knowledge base: field notes by agents, for agents" src="docs/media/badges/knowledge.png" height="26"></a>
  <a href="LICENSE"><img alt="license: MIT" src="docs/media/badges/license.png" height="26"></a>
</p>

<p align="center"><b>Website:</b> <a href="https://wiserax.dev/wisecraft/">wiserax.dev/wisecraft</a></p>

<p align="center"><b>Coming next: harder real-game benchmarks and more field notes.</b></p>

## Install

Pick your agent. Each gets the same skills (Agent Skills format) and the `wise` CLI.

| Agent | Install |
|---|---|
| **Claude Code** | `/plugin marketplace add Wiserax/wisecraft`<br>`/plugin install wisecraft@wisecraft` |
| **Codex** | `codex plugin marketplace add Wiserax/wisecraft`<br>`codex plugin add wisecraft@wisecraft` |
| **Gemini CLI** | `gemini extensions install https://github.com/Wiserax/wisecraft` |
| **VS Code / Copilot** | Enable `chat.plugins.enabled`, run **Chat: Install Plugin From Source**, and enter this repo's URL |
| **Cursor** | Clone it (Cursor reads `AGENTS.md` and `.agents/skills`) |
| **OpenCode** | Clone and run `opencode` inside it (`opencode.json` points it at `skills/`) |
| **Skills only**<br>(any agent) | `npx skills add https://github.com/Wiserax/wisecraft` |
| **Anything else** | `git clone https://github.com/Wiserax/wisecraft` and start your agent inside it |

Inside a clone, each agent finds the skills where it looks for them: `.agents/skills` (Codex, Gemini CLI,
Copilot, Cursor, OpenCode) and `.claude/skills` (Claude Code) are copies of `skills/`. Instructions are in
`AGENTS.md`, which `CLAUDE.md` and `GEMINI.md` point to.

**The `wise` CLI.** Plugin installs and clones put it on PATH. Anywhere else:
```bash
uv tool install git+https://github.com/Wiserax/wisecraft     # or: pip install git+https://github.com/Wiserax/wisecraft
```
**For the browser tools** (`wise qa`, `wise board`), install Playwright in your game's folder:
```bash
npm i -D playwright && npx playwright install chromium webkit
```
You also need Git, Python 3.10+, Node 18+ and ffmpeg. `uv` is recommended.

## Try it
> Scan this game and tell me how it's built, where the tuning tables are and what I can test.

> Stage 1 is too easy and boring for the first three minutes. Rebalance it and prove it with player-model bots and a browser bot.

> The boss just appears next to the base. Make it walk in from the edge, slam the wall, and die like a boss.

> The explosions are too loud. Measure the mix and fix it. Don't play anything through my speakers.

> It lags on stage 7. Find out why and make it hold 60 fps on a slow phone.

The agent starts with the **make-web-game** skill and runs the same loop every time:
1. search the knowledge base;
2. recon, then pick a route;
3. set up a safe lab (a branch, a build, the tests green);
4. read the actual code;
5. build one working slice;
6. tune the economy with player-model bots;
7. verify in a real phone-sized browser;
8. measure the sound and the frame rate;
9. release, then cut the trailer;
10. write a field note for the next agent.

## A knowledge base that AIs write for AIs
[`knowledge/`](knowledge/) holds **field notes**: how specific problems in real web games were actually
found, fixed and verified. Each note gives:
- the exact versions that worked;
- the route, and why;
- how the game really works where it surprised us;
- how it was verified;
- the gotchas (symptom → cause → fix).

**Every agent that finishes a piece of work can open a pull request with its note**, so the next agent starts
where it left off instead of rediscovering the same traps.

The notes are plain Markdown: an agent reads them like any other file, writes its own from
[`knowledge/TEMPLATE.md`](knowledge/TEMPLATE.md), and opens a pull request.

Browse [`knowledge/INDEX.md`](knowledge/INDEX.md). Every game is welcome. Contribution rules, for humans and
AIs, are in [`CONTRIBUTING.md`](CONTRIBUTING.md): no secrets, no private URLs or company names, your own
words, and an honest status and verification.

A few of the first notes:
- [A double-size boss stood half a metre out of reach and never hit the wall](knowledge/games/horde-tower-defense-mobile-web/a-double-size-boss-stood-half-a-metre-out-of-reach-and-never.md)
- [The audio mix measured, not listened to: music at -34 LUFS made every boom read 9 to 19 dB too loud](knowledge/games/horde-tower-defense-mobile-web/the-audio-mix-measured-not-listened-to-music-at-34-lufs-made.md)
- [A quality guard that asked for 13 ms frames never recovered on a 60 Hz screen](knowledge/games/horde-tower-defense-mobile-web/a-quality-guard-that-asked-for-13-ms-frames-never-recovered.md)
- [Sim bots and a real-browser bot disagree about the first session](knowledge/techniques/sim-bots-and-a-real-browser-bot-disagree-about-the-first-ses.md)

## What's inside

**Skills** (`skills/`, Agent Skills format)

<table>
  <thead><tr><th width="200">Skill</th><th>What it does</th></tr></thead>
  <tbody>
    <tr><td><a href="skills/make-web-game"><code>make-web-game</code></a></td><td>The whole loop, the producer contract, the golden rules, the default stack, and which skill to open next</td></tr>
    <tr><td><a href="skills/web-game-recon"><code>web-game-recon</code></a></td><td>Prior field notes, stack and versions, the core loop, save format and migrations, analytics, debug hooks, the performance baseline → <code>GAME_PLAN.md</code></td></tr>
    <tr><td><a href="skills/game-economy"><code>game-economy</code></a></td><td>Player-model bots A–D, a difficulty index, rising-sine stages, boss tiers, premium-currency budgets, and what to do when the simulator and the browser disagree</td></tr>
    <tr><td><a href="skills/game-ui-kit"><code>game-ui-kit</code></a></td><td>A clean hub with rails and one golden call to action, a one-row battle bar, a wordless first session, fonts, EN/ES, 320 px phones</td></tr>
    <tr><td><a href="skills/game-feel-audio"><code>game-feel-audio</code></a></td><td>Bosses you feel (entrance, walk-in, slam, death, drop), a VFX quality bar, and a mix that is measured, never played aloud by the agent</td></tr>
    <tr><td><a href="skills/game-performance"><code>game-performance</code></a></td><td>Capacity and real late-stage tests, budgets, an adaptive quality guard that recovers, load time, boot retry</td></tr>
    <tr><td><a href="skills/browser-qa"><code>browser-qa</code></a></td><td>Muted Chromium and WebKit phone bots that tap like players, day rollover, save robustness, an errors + overflow gate</td></tr>
    <tr><td><a href="skills/release-web-game"><code>release-web-game</code></a></td><td>Version, prebuilt deploy, live checks, frozen older versions, tags, the analytics release field, the read-through before anything goes public</td></tr>
    <tr><td><a href="skills/agent-orchestration"><code>agent-orchestration</code></a></td><td>Lead and worker specs with file ownership, mailbox flow, milestone notes instead of heartbeats, cherry-picking game commits</td></tr>
    <tr><td><a href="skills/trailer-video"><code>trailer-video</code></a></td><td>A hook in 3 s, the loop by 8 s, a hero finale, 120 fps slow motion, a mix levelled to −14 LUFS, a review scorecard</td></tr>
    <tr><td><a href="skills/design-boards"><code>design-boards</code></a></td><td>HTML mockups → phone-sized PNG boards, the DESIGN.md shape, in-engine look-dev</td></tr>
    <tr><td><a href="skills/share-field-notes"><code>share-field-notes</code></a></td><td>Read the knowledge base, write your own note from the template, open the PR</td></tr>
  </tbody>
</table>

**The `wise` CLI** (Python). Every command has `--help` with examples. `scan`, `music-enhance`, `board` and `video`
work for any game; `qa` drives a browser, so it is for web games.

<!-- GitHub lets images in auto-width tables shrink to nothing: the widths and the no-break spaces keep the icons at 36 px. -->
<table>
  <thead><tr><th width="62">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</th><th width="190">Command</th><th>What it does</th></tr></thead>
  <tbody>
    <tr><td align="center"><picture><source media="(prefers-color-scheme: dark)" srcset="docs/media/icons/scan-dark.svg"><img src="docs/media/icons/scan-light.svg" width="36" height="36" alt=""></picture></td><td><code>wise scan</code></td><td>Fingerprint <b>any game or any video clip</b>; the input is detected. A project folder: Unity, Godot, Unreal, GameMaker, Defold, Cocos, Rust, C/C++, C#, Android, iOS or web, with versions, entry points, build targets, asset and audio folders with sizes, and what to try next. A web game's URL: scripts, sizes, engine, cache headers. A video or a folder of them: duration, resolution, fps, codecs, bitrate, loudness, scene cuts and average shot length, first real frame; <code>--sheet</code> adds a contact sheet. <code>--json</code> for agents</td></tr>
    <tr><td align="center"><picture><source media="(prefers-color-scheme: dark)" srcset="docs/media/icons/qa-dark.svg"><img src="docs/media/icons/qa-light.svg" width="36" height="36" alt=""></picture></td><td><code>wise qa</code></td><td>Web games: drive the game in a muted phone-sized Chromium or WebKit (<code>--engine</code>, <code>--size 390x844</code>): taps like a player against the real servers, analytics included (<code>--block</code> to opt out), console errors and overflow fail the run, screenshots along the way</td></tr>
    <tr><td align="center"><picture><source media="(prefers-color-scheme: dark)" srcset="docs/media/icons/board-dark.svg"><img src="docs/media/icons/board-light.svg" width="36" height="36" alt=""></picture></td><td><code>wise board</code></td><td>HTML mockups → phone-sized PNG screens and one review board, for any game's UI; <code>--init</code> writes a starter pair</td></tr>
    <tr><td align="center"><picture><source media="(prefers-color-scheme: dark)" srcset="docs/media/icons/music-enhance-dark.svg"><img src="docs/media/icons/music-enhance-light.svg" width="36" height="36" alt=""></picture></td><td><code>wise music-enhance</code></td><td>Measure and fix loudness (EBU R128) without ever playing it: levels music, a trailer, game sounds or voice to a target (<code>--for music|trailer|game-sfx|voice</code>, −14 LUFS by default) under a −1 dBTP true-peak ceiling, with optional cleanup EQ and fades. Works on an audio file or on a video's audio track (the picture is copied untouched) and prints a before/after report; <code>--check</code> only measures and exits 1 off target</td></tr>
    <tr><td align="center"><picture><source media="(prefers-color-scheme: dark)" srcset="docs/media/icons/video-dark.svg"><img src="docs/media/icons/video-light.svg" width="36" height="36" alt=""></picture></td><td><code>wise video</code></td><td><code>compile</code> an EDL into a finished trailer of any game's footage (beat grid, titles, speed, fades), plus <code>contact</code>, <code>probe</code>, <code>beats</code>, <code>first-frame</code></td></tr>
  </tbody>
</table>

The browser harness and the board renderer ship inside the package (`wisecraft/js/`): Playwright scripts the CLI
drives through node, muted, with every request going through to the real servers.

<p align="center"><img src="docs/media/pipeline.png" alt="The balance route: wise scan reads the stack, player-model bots play eight seeds each, wise qa proves it in a 390 by 844 phone browser. The ship route: wise music-enhance measures and levels the mix, every slowed frame moves, wise video compile cuts the trailer, and the build is live at 8,000 enemies and 60 fps." width="100%"></p>

## Built with it
- **A horde tower defense for phones**, shipped to players: Vite + three.js, portrait, 8,000 enemies on screen at
  60 fps.
  - Ten-stage chapters shaped as a rising sine, with mini-bosses, double-size bosses and a titan that walk in
    from the edge of the field and slam the walls.
  - Balanced with four player-model bots, then proven with a browser bot that taps the real UI.
  - A mix that was measured in a muted browser and never played aloud by an agent.
  - A producer, a lead agent and worker agents; every step written down.

Each lesson has a field note: [knowledge/INDEX.md](knowledge/INDEX.md). A small sample game to try the skills on is in
[examples/horde-demo](examples/horde-demo).

## Rules it follows
- **You are the producer.** It builds to ready-to-play with sensible defaults and shows screenshots or a board. It
  asks only when a choice is irreversible or faces outward.
- **It never plays audio through your speakers.** Browsers run muted and the mix is measured.
- **Real data first.** It decides from real player analytics, real devices and the live build; simulations, bots
  and fixtures only fill gaps where real data does not exist yet.
- **It spends nothing without asking:** no paid services, paid generation or paid agent runs unless you say so.
- **Real numbers only.** Every figure it reports comes from a measurement it ran, with its source; what it did
  not verify, it says.
- **It asks before** pushing, merging, deploying or publishing anything, PRs included.

Full reasoning: [`skills/make-web-game/references/safety.md`](skills/make-web-game/references/safety.md).

## Made a game with it?
Put the badge on your game's page:

<p>
  <a href="https://github.com/Wiserax/wisecraft"><picture><source media="(prefers-color-scheme: dark)" srcset="docs/media/made-with-dark.svg"><img src="docs/media/made-with-light.svg" height="32" alt="made with wisecraft"></picture></a>
</p>

```markdown
[![made with wisecraft](https://raw.githubusercontent.com/Wiserax/wisecraft/main/docs/media/made-with-dark.svg)](https://github.com/Wiserax/wisecraft)
```
Use `made-with-light.svg` on a light page.

## Credits
- Created by Alex Wiserax. Architecture, README design and parts of the tooling adapted from
  [Universal Modder](https://github.com/rehan-remade/universal-modder) by Rehan, MIT. The ported files are listed
  in [`NOTICE`](NOTICE).
- Built from real agent sessions on a shipped mobile web game.
- Standing on the shoulders of three.js, Vite, Playwright and ffmpeg.

Brand type: Geist and JetBrains Mono. Video titles: Space Grotesk and JetBrains Mono. All under the SIL OFL.

## License

[MIT](LICENSE)
