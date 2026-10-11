---
name: release-web-game
description: Version, deploy and verify a web game release. Covers the pre-release lint (`wise publish check` for secrets, keys, private URLs, large binaries and denylisted names), the version bump, tests and a prebuilt deploy, live checks of assets and audio, the regression run against the live URL, tags, the analytics release field, frozen older versions on their own URL for side-by-side comparison, and preview URLs behind sign-in. Use when the user says "ship it", "deploy", "release 1.2", "put the old version up next to it", "is it live?", "tag it", or when tests, browser QA and fps are green and the producer has said to ship on green. The agent never pushes or deploys without being asked.
---

# Release a web game

A release is a version number, a deploy that was built once and uploaded as built, and proof that the live
URL plays. Only the lead releases. Workers hand over branches.

**Never push or deploy unasked.** A deploy needs the producer's word: either for this release, or a standing
"ship when green" for the project. A push to the repository's `main` needs explicit permission every time.

## 1. Lint
```bash
wise publish check dist            # the build that will be uploaded
wise publish check .               # the repo, before it or any part of it goes public
```
It looks for secrets and keys, private URLs, large binaries and denylisted names (a company or product
name that must not appear in a public repo).

Fix every FAIL. Resolve each WARN on purpose: a 1.4 MB music stem nobody plays is a large binary worth
acting on (two of them once rode along in every deploy).

## 2. Gate (all green before the bump)
| Gate | How | Skill |
|---|---|---|
| Tests | `npm test` | |
| Browser | main regression, `errors []`, no overflow, in Chromium 390, WebKit 390, Chromium 320 | browser-qa |
| First session | a fresh-profile first fight won by the playtest bot | browser-qa |
| Performance | 60 fps at 2,000 / 5,000 / 8,000, on mains power | game-performance |
| Sound | the sound-default check passes in both engines | game-feel-audio |
| Balance | bot table unchanged, or the change is the point and is reported | game-economy |

If a gate can't be measured honestly (a laptop in low-power mode reads a flat 30 fps on every build), say
"not confirmed" with the last good run. Don't wave it through and don't block on a false failure.

## 3. Version and deploy
1. Bump `VERSION` (`2.3.4`; `-preview` while iterating). The lead owns version numbers. A worker's branch
   doesn't know what shipped meanwhile: one titled its log entries with a version the lead had already
   released from another branch. Workers title entries by date and topic.
2. `npm test` → build → the prepare step (`node scripts/prepare-vercel.mjs`: redirects, cache headers,
   functions) → `vercel deploy --prebuilt --prod`. Prebuilt, so what was tested is what ships.
3. **Post-deploy:**
   - every hashed asset returns 200 and the bundle contains the new VERSION;
   - audio files return 200, because a deploy once shipped without `audio/` and sound never started;
   - the sound-default check passes;
   - the main QA runs against the live URL;
   - a first-siege bot run passes on the live URL.
   An asset may 404 for a few seconds right after a deploy; recheck after 20 s before panicking.
4. Log it: the commit, what changed for the player, and the gate results.

## 4. Branches and tags
- `rc/next` is the integration branch, in its own worktree with its own `.vercel/` link. Workers branch
  from it (`feat/<topic>`) in their own worktrees. Only the lead merges.
- After every deploy, fast-forward the main game branch to `rc/next` and tag (`vX.Y.Z`). Never push the
  repository's `main` without explicit permission.
- Explicit `git add <paths>` only (never `git add .` / `-A`). Commit messages end with the session's
  Co-Authored-By line.
- Bring in a worker's game commits but not its tooling with `git cherry-pick`. MODLOG conflicts: keep both
  entries. (The **agent-orchestration** skill has the details.)

## 5. The analytics release field
Tag every event with the version (`game_version`, or a `release` field). Without it nobody can tell whether
a retention change came from the release or from the week.
- Check after the deploy without sending anything: in the live QA run, the route that answers
  `**/api/events` with 204 can read the request body first. Assert the field equals the new version.
- Automated runs always answer with 204. The live check must not add bot traffic.
- A promoted prototype keeps its analytics identity, so players don't restart as new users.

## 6. Frozen versions
To let the producer compare builds, deploy the older version to a **separate project** on the host (a name
like `mygame-v2`). That gives it a separate origin, so separate saves. Tag it and keep its worktree.
- Why its own URL and not a path: same origin means shared storage, and the old build would read or
  overwrite the new build's save.
- Freeze from the tag, not from a branch that keeps moving.
- Tell the producer both URLs and which is which.

## 7. Previews and sign-in
Preview URLs on the host (Vercel previews, for one) may sit behind single sign-on: a 302 to a login page
the producer may not have. For producer review, deploy to production, or to a separate public project.

## 8. Tell the producer
One short message, in plain language:
- what changed for the player (three bullets at most);
- the link, and the frozen link if there is one;
- the board;
- the gate line ("516 tests, QA clean local and live, 60 fps at 8,000, sound ok");
- what is still open.

## Done means
- `wise publish check` has no FAIL.
- The live URL serves the new VERSION, all assets and audio return 200, and the regression and a first-fight
  bot pass against it.
- The commit is tagged; the game branch is fast-forwarded; the release is logged.
- The older version is still reachable on its own URL if the producer wants to compare.

## References
- `references/checklist.md`: the release as a copy-and-tick list, plus the traps by symptom. Read it while
  releasing.
