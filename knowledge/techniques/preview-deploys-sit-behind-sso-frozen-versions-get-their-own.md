---
kind: technique
title: "Preview deploys sit behind SSO, frozen versions get their own origin: what to check live after a deploy"
tags: [release, deploy, preview, sso, origin, localstorage, saves, cache-headers, post-deploy, static-hosting]
date: 2026-10-09
agents: ["Claude Code (Opus 5.5)"]
humans: []
links: []
---

# Preview deploys sit behind SSO, frozen versions get their own origin: what to check live after a deploy

> Three release lessons from a browser game on static hosting. A preview URL can answer with a login
> redirect, so the person who should review the build sees a sign-in page. An older version kept for
> comparison must live on its own origin, or it shares saves with the current one. And a deploy that
> "succeeded" can still be missing a folder: check the live site with requests and a bot, every time.

## When to use it
- Any web game deployed from a prebuilt folder by an agent.
- When a human wants to compare the new build with the last one they liked.
- When several agents build branches and one of them deploys.

## How
**Reviews**
1. Do not send a reviewer a preview URL without fetching it first as an anonymous client. A 302 to a login
   page means the host's preview protection (SSO) is on. This project used Vercel; other hosts have the same
   feature under other names.
2. For review, deploy to production, or to a separate public project. Changing the protection setting is a
   decision for the account's owner, not the agent.

**Frozen versions**
3. Tag the commit and keep its checkout.
4. Deploy it to a **separate project**, so it has a separate origin. `localStorage` is per origin: on the
   same origin the old build would read, migrate and overwrite the current build's save.
5. The main URL then becomes the next version. Tell the reviewer which URL is which and that progress does
   not carry between them.

**Every deploy**
6. Bump the version constant the game shows and sends with analytics.
7. Tests, build, then a prepare step that writes redirects, cache headers and functions, then the prebuilt
   production deploy.
8. Cache headers: hashed assets immutable for a year; audio, art and fonts for a day; HTML left as it was.
9. Check the live site, not the deploy log:

   | Check | How | Catches |
   |---|---|---|
   | every hashed asset returns 200 | request each file the built HTML and manifest name | a partial upload |
   | the bundle contains the new version string | fetch the main chunk and search it | a stale deploy or cache |
   | audio files return 200 | request the audio list | a deploy without its audio folder |
   | sound starts by default | the sound-default probe, muted | audio wired off or files missing |
   | the main regression | the browser run in three profiles against the live URL (`wise qa`) | anything environment-specific |
   | a first session is winnable | the first-stage bot against the live URL | a balance or boot break in the real build |

10. Log the deploy: the commit, what changed for the player, and each gate's result.
11. `wise publish check` before anything goes public: keys, private URLs, large binaries.

## Verification
On a horde tower-defense mobile web game (Vite 7 + three.js 0.180, 8,000 enemies on screen at 60 fps,
portrait 390×844):
- A version was frozen on 2026-10-09 on its own project with separate saves, and stayed unchanged through
  the later releases of the main URL (2.3.0 to 2.3.6).
- Each release entry in the log carries the same gate: tests, browser regression clean locally and live in
  Chromium, WebKit and Chromium at 320×568, 60 fps at 8,000 enemies, sound default, and first-stage runs local
  and live.
- A test (`tests/deploy-output.test.js`) holds the deploy folder's contents; removing two unused audio files
  and the audio manifests took the deploy from about 12.6 MB to 9.7 MB.

## Gotchas
1. **The reviewer got a login page.** **Cause:** preview deployments were behind SSO and answered 302.
   **Fix:** review on production or on a public project.
2. **Sound never started on a live build.** **Cause:** a deploy shipped without its audio folder. Locally
   everything worked. **Fix:** the audio 200 check and the sound-default probe against the live URL.
3. **An asset returned 404 seconds after a deploy.** **Cause:** propagation. **Fix:** recheck after 20 s
   before treating it as a failure.
4. **An old build on the same origin shares the save.** **Fix:** a separate project per frozen version.
5. **"It works on the preview" proved nothing about production.** Cache headers, redirects and functions come
   from the prepare step and apply to the deployed output. Run the live checks on the URL players use.
6. **The version label lied.** Two branches both called their work 2.3.5; one shipped under that number and
   the other went out as the next build. **Fix:** bump the version at merge time, by the one who deploys, and
   check the live bundle for it.
7. **Immutable caching makes a wrong file permanent for a year.** It is safe only for content-hashed names.
   Files with stable names (audio, art) get a day.
8. **Only one agent deploys.** Workers build and report; the lead merges, gates and deploys. A worker with
   deploy rights can overwrite production from a stale branch.

## Open questions
- The sources state the SSO redirect and the audio-less deploy as lessons without dates or counts; how often
  either happened is unknown.
- Rollback was never exercised: no release in the log was reverted.
- Whether the frozen version should import a save from the main origin (for a fair comparison) was not built.

## Seen in
- A horde tower-defense mobile web game, releases 2.2.0 to 2.3.6.
- Related: `answer-the-analytics-endpoint-with-a-204-in-every-automated.md` (live QA must not pollute
  analytics), and the game note
  [A reset connection on one code chunk left the boot splash up for good](../games/horde-tower-defense-mobile-web/a-reset-connection-on-one-code-chunk-left-the-boot-splash-up.md).
