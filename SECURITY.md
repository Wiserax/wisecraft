# Security

## Reporting a vulnerability
Please report security problems privately, not in a public issue or pull request. Use **Report a
vulnerability** on the repository's **Security** tab (GitHub's private vulnerability reporting). If that button
isn't there, open an issue that asks for a private contact and leave the details out.

There are no release branches: fixes land on `main`.

## What's in scope
The code in this repository: the `wise` CLI (`bin/wise`, `wisecraft/`, the node scripts in `wisecraft/js/`), the hooks and the
agent configs. The parts where a bug matters most:
- **The browser harness.** `wise qa` and `wise board` open pages in a local headless browser. It must stay muted and
  must write only into its output folder; with `--block`, a matching request must be answered in the browser and
  never reach a server. A page that makes the harness do otherwise is in scope.
- **Files the CLI writes.** `wise music-enhance` and `wise scan --sheet` write new files next to their input (or
  where `-o`, `--out-dir` or `--sheet` point) and never change the input. A way to make them overwrite the input,
  or write somewhere else, is in scope.

Out of scope: problems in the tools and services `wise` calls (Playwright and its browsers, node, ffmpeg, GitHub,
a hosting provider). Please report those upstream.
