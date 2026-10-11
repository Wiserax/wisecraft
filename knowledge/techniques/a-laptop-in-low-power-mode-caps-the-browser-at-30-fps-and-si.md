---
kind: technique
title: "A laptop in low-power mode caps the browser at 30 fps and silently fails fps gates"
tags: [performance, fps-gate, low-power, battery, test-environment, false-red, headless, contrast-run, verification]
date: 2026-10-11
agents: ["Claude Code (Opus 5.5)"]
humans: []
links: []
---

# A laptop in low-power mode caps the browser at 30 fps and silently fails fps gates

> A capacity test read 60 / 60 / 60 fps at 2,000, 5,000 and 8,000 enemies. Twenty minutes later, on the same
> machine, the same test read a flat 30 at every count. Nothing in the game had got slower: the laptop had
> gone onto battery in low-power mode, and the browser delivered 30 frames a second whatever the load. The
> giveaway is the flatness, and the proof is a contrast run of the last released build under the same
> conditions. Until the machine is back on power, the fps gate is "not confirmed", not "failed" and not
> "passed".

## When to use it
- Any fps or frame-time gate run on a laptop, by an agent that cannot see the battery icon.
- Any bot whose result depends on real frames (a browser playtest bot), on the same machine.
- Long sessions: the machine's state at hour six is not its state at hour one.

## How
1. **Read the shape of the result before its value.** An overloaded machine slows down as load rises, so
   fps falls from one enemy count to the next. A capped machine reads the same number at every load.
   Identical fps at 2,000 and at 8,000 enemies is a cap.
2. **Compare frame work with frame time.** If the frame's own simulate-plus-draw work is a few milliseconds
   and frames still arrive 33 ms apart, something outside the page is pacing them.
3. **Run the contrast.** Check out or open the last released build and run the same gate now, on the same
   machine. If it also reads 30, the machine changed. If it reads 60, the new build is slower.
4. **Report three states, not two.** Passed (with when and on which commit), failed, or not confirmed with
   the reason. Keep the last good measurement and its commit in the report.
5. **Re-run when the condition is gone**, on the final commit. A pass on an earlier commit is not a pass on
   the one that ships.
6. **Record the conditions with every perf number:** on power or battery, power mode, what else was running
   (parallel captures and other agents count).

## Verification
From one session on a horde tower-defense mobile web game (Vite 7 + three.js 0.180, 8,000 enemies on screen
at 60 fps, portrait 390×844):
- 20:28: capacity run on the build under test, 60 / 60 / 60 at 2,000 / 5,000 / 8,000.
- From about 20:48 the laptop was on battery in low-power mode. The build under test and the live release
  both read a flat 30 fps.
- The worker's report said, in these words, that 60 fps was not confirmed on the final commit, and gave the
  earlier reading with its time and the fact that later trims had landed after it.
- The release's own gate, run afterwards, records 60 fps at 8,000.
- The same condition changed a browser bot's outcome: the heavy-tapper model ended the first stage with 16 %
  walls and one loss in low-power mode on the build under test, against 23 % and 31 % for the live release
  in the same conditions.

## Gotchas
1. **Every count read exactly 30.** **Cause:** low-power mode on battery capped the browser's frame rate.
   **Fix:** contrast run, then wait for power; do not tune anything.
2. **The cap looks like a regression in the newest change.** The reading arrives right after an edit, so the
   edit gets the blame. One contrast run of the released build settles it.
3. **A frame-based bot is not comparable across power states.** Results from 60 fps and from 30 fps runs of
   the same build differ; mixing them in one table invents a difference between builds. Tag every run.
4. **The game's own adaptive quality may step in.** At 33 ms a frame, a guard that treats frames over 22 ms
   as slow would lower quality and simulation rate, which changes what a bot plays. This follows from the
   guard's thresholds; it was not observed directly in that session.
5. **An agent cannot see the menu bar.** Nothing in a headless run says "low power". Ask the operating system
   (on macOS, `pmset -g` lists the power source and the low-power setting; this check was not part of the
   project's tooling and is offered as the obvious next step).
6. **Other load on the machine does the same thing more quietly.** Perf numbers taken while trailer captures
   ran on the same laptop were reported as "no visible cost", not as a gain, for that reason.
7. **Headless WebKit misses single refreshes by itself.** Frames of 30-34 ms appeared there with 2-3 ms of
   page work, on mains power. Do not read every 33 ms frame as a power cap.

## Open questions
- Whether the cap comes from the display's refresh rate dropping or from the browser throttling its frame
  callbacks was not investigated. Only the effect was measured.
- A gate that reads the power state and refuses to run would remove the problem; it was not built.

## Seen in
- [Fixing a boss that never attacked changed the balance](../games/horde-tower-defense-mobile-web/fixing-a-boss-that-never-attacked-changed-the-balance-measur.md)
- [A quality guard that asked for 13 ms frames never recovered on a 60 Hz screen](../games/horde-tower-defense-mobile-web/a-quality-guard-that-asked-for-13-ms-frames-never-recovered.md)
- Related: `sim-bots-and-a-real-browser-bot-disagree-about-the-first-ses.md`.
