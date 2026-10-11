@AGENTS.md

## Claude Code specifics
- Installed as a plugin, the skills are namespaced (`/wizerax:make-web-game`) and a SessionStart hook puts
  `wz` on PATH.
- In a clone, `.claude/settings.json` adds the same PATH hook, and `.claude/skills` is a copy of `skills/`.
