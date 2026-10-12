# Release checklist

Copy into the release log entry and tick as you go.

```markdown
## Release <X.Y.Z> = <commit>
- [ ] The producer asked for this release, or "ship when green" stands for the project
- [ ] Machine on mains power, low-power mode off
- [ ] Merged into rc/next by the lead; worker tooling left out (cherry-picked game commits only)
- [ ] npm test: <n>/<n>
- [ ] Main regression errors [] and no overflow: Chromium 390, WebKit 390, Chromium 320x568
- [ ] First fight, fresh profile, playtest bot: won, walls <n>%
- [ ] 60 fps at 2,000 / 5,000 / 8,000 (or "not confirmed" + last good run)
- [ ] Sound-default check: Chromium, WebKit
- [ ] VERSION bumped to <X.Y.Z>
- [ ] Build; prepare step; the build read through for keys, private URLs and names: none
- [ ] Prebuilt deploy to production
- [ ] Live: hashed assets 200; bundle contains <X.Y.Z>; audio files 200
- [ ] Live: main regression; first-fight bot
- [ ] Live: analytics release field = <X.Y.Z>
- [ ] Game branch fast-forwarded to rc/next; tag v<X.Y.Z>
- [ ] Older version frozen at <URL> (if asked)
- [ ] Producer told: what changed for the player, link, board, gate line, open items
```

## Traps by symptom
| Symptom | Cause | Fix |
|---|---|---|
| No sound on the live build, fine locally | the deploy shipped without the `audio/` folder | check audio URLs return 200 after every deploy |
| An asset 404s right after the deploy | the host is still propagating | recheck after 20 s |
| The producer can't open the link | a preview URL behind single sign-on (302) | deploy to production or a separate public project |
| The old and new builds share a save | both on one origin | freeze the old build on its own project and origin |
| The live bundle shows the old version | the build was not rerun after the bump, or a cached HTML | bump, then build; HTML must revalidate |
| fps gate fails on every build, live included | the laptop is on battery in low-power mode (30 fps cap) | plug in, re-measure, or report "not confirmed" |
| A worker's tooling is in the game build | its whole branch was merged | cherry-pick the game commits only |
| Unrelated files in the release commit | `git add .` | explicit `git add <paths>` |
| The deploy is several MB larger than the game needs | orphan assets | pin the list of shipped files with a test |

## Cache headers the prepare step sets
- Hashed files under `/assets/`: one year, immutable.
- Audio, art, fonts: one day.
- HTML: revalidated.
- Redirects for promoted prototype paths: 307 to the root.
