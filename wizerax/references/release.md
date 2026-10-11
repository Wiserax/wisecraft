# Release

## Branches
- `rc/next` is the integration branch, in its own worktree with its own `.vercel/` link. Workers branch from it (`feat/<topic>`) in their own worktrees. Only the lead merges.
- After every deploy, fast-forward the main game branch to `rc/next` and tag (`vX.Y.Z`). Never push the repository's `main` without explicit permission.
- Explicit `git add <paths>` only (never `git add .` / `-A`). Commit messages end with the session's Co-Authored-By line.
- Bring in a worker's game commits but not its tooling with `git cherry-pick`. MODLOG conflicts: keep both entries.

## Version and deploy
1. Bump `VERSION` (`2.3.4`; `-preview` while iterating).
2. `npm test` → build → `node scripts/prepare-vercel.mjs` (redirects, cache headers, functions) → `vercel deploy --prebuilt --prod`.
3. **Post-deploy:**
   - every hashed asset returns 200 and the bundle contains the new VERSION;
   - audio files return 200, because a deploy once shipped without `audio/` and sound never started;
   - the sound-default check passes;
   - the main QA runs against the live URL;
   - a first-siege bot run passes on the live URL.
4. Log it: the commit, what changed for the player, and the gate results.

## Frozen versions
To let the producer compare builds, deploy the older version to a **separate Vercel project** (e.g. `mygame-v2.vercel.app`). That gives it a separate origin, so separate saves. Tag it and keep its worktree.

## Previews and SSO
Vercel preview URLs may sit behind SSO (302). For producer review, deploy to production, or to a separate public project.
