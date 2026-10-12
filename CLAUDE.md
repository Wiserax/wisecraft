@AGENTS.md

## Claude Code specifics
- Installed as a plugin, the skills are namespaced (`/wisecraft:game-trailer`) and a SessionStart hook puts
  `wise` on PATH.
- In a clone, `.claude/settings.json` adds the same PATH hook, and `.claude/skills` is a copy of `skills/`.
