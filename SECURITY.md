# Security

## Reporting a vulnerability
Please report security problems privately, not in a public issue or pull request. Use **Report a
vulnerability** on the repository's **Security** tab (GitHub's private vulnerability reporting). If that button
isn't there, open an issue that asks for a private contact and leave the details out.

There are no release branches: fixes land on `main`.

## What's in scope
The code in this repository: the `wz` CLI (`bin/wz`, `wz/`, the node scripts in `wz/js/`), the hooks and the
agent configs. The parts where a bug matters most:
- **Secrets and private names.** `wz publish check` and `wz kb check` are the last line before something goes
  public. A common key format they miss, or a way to make them pass a file that carries a secret or a private
  deploy URL, is in scope.
- **The browser harness.** `wz qa` and `wz board` open pages in a local headless browser. It must stay muted,
  must answer the blocked analytics pattern with a 204 instead of letting it reach a server, and must write
  only into its output folder. A page that makes the harness do otherwise is in scope.
- **The knowledge-base sync.** `wz kb sync` downloads Markdown and JSON from this repository into a per-user
  cache. A way to make it write outside that cache is in scope.

Out of scope: problems in the tools and services `wz` calls (Playwright and its browsers, node, ffmpeg, GitHub,
a hosting provider). Please report those upstream.
