"""wizerax: tools any AI agent (Claude Code, Codex, Cursor, Gemini CLI, ...) uses to build and ship web games.

Subcommands (see `wz --help`):
  scan       fingerprint a web game (folder or URL): stack, versions, entry points, debug hooks, analytics, audio, bundle size
  qa         drive the game in a muted phone-sized browser: taps like a player, console errors, overflow, screenshots
  board      render HTML mockups to phone-sized PNG screens and one review board
  loudness   measure loudness and true peak of an audio or video file (EBU R128), without playing it
  dupframes  count repeated frames in a video (the stutter check for slow motion)
  video      compile styled trailers from an EDL, contact sheets, probe, beats
  kb         the knowledge base: search prior field notes, write your own, check it, open a PR
  publish    lint a folder before it goes public: secrets, keys, private URLs, large binaries, names on a denylist
"""

__version__ = "0.2.0"
