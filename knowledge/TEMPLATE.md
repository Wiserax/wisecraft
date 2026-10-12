---
# Field note: how a web game was built, tuned or shipped, written so the next agent can repeat it. Keep the keys; delete the comments.
# Quote list items with ": ", a comma or only digits in them, e.g. tools: ["Vite 7: dev server"].
kind: game
title: "A boss that walks in and slams the wall in a horde tower defense"   # what you built, in plain words
game: "Horde tower defense (mobile web)"                  # a neutral description of the game: no company or unreleased product names
games_also: []                                            # other games the same work was done in, described the same way
game_version: "2.3.5, Vite 7 + three.js 0.180"            # exact game build and stack versions that worked
platform: web-mobile                                      # web-mobile | web-desktop | pwa | webview | other
engine: threejs-vite                                      # a short engine key (threejs-vite, phaser, pixi, babylon, playcanvas, unity-webgl, godot-web, construct, canvas-2d, unity, godot) or unknown
route: engine-code                                        # design | data-tuning | engine-code | ui | audio | performance | tooling | release | process | other
tools: ["wise qa", "Playwright", "node --test"]
status: working                                           # idea | in-progress | working | released | abandoned
agents: ["Claude Code (Opus 5.5)"]                        # agent + model that did the work
humans: []                                                # handles of the humans involved, if they want credit
date: 2026-10-11
links: []                                                 # public repo, example folder, video, post (never a private preview URL)
tags: []                                                  # free-form: boss, state-machine, wave-pacing, hit-stop, object-pool, ...
---

# A boss that walks in and slams the wall in a horde tower defense

> Two to four sentences: what you built, in what kind of game, by which route, and whether it runs in the real
> game on a phone-sized browser (and how you know).

## Setup
Game build, stack versions (bundler, engine, node), devices and browsers, tools installed first. The versions
that worked are the most useful thing you can write down.

## Route and why
Which route (see `route:`), what else you considered, and why you didn't take it.

## How the game works (what we had to learn)
The facts you discovered about the game and its engine: the update loop and its order, state machines, data
tables, coordinate systems and units, pools and hard limits, what the renderer batches, what the browser
throttles. Describe them in your own words and name the modules and functions; don't paste large chunks of
the game's code or data. Link public docs where they exist.

## Build steps
The shortest path to reproduce, in order: commands, settings, where files go.

## Verification
How you knew it worked: the oracle (a headless simulation, `wise qa` in a muted phone-sized browser, screenshots
you looked at, console logs, frame-time and loudness numbers, a test suite), and what you did NOT verify.

## Gotchas
The most valuable section. Numbered; each one symptom → cause → fix.
1. **Symptom.** What you saw. **Cause:** what it really was. **Fix:** what worked.

## Assets
How art/audio/3D were made (models, prompts, `wise` commands), if any.

## Cost and time
Optional: wall-clock, sessions, API spend.

## Open questions
What's unresolved or would be the next step.
