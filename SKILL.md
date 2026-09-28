---
name: use-chrome
description: Connect an MCP-capable coding agent to the user's existing signed-in Chrome profile through Playwright MCP. Use when an agent needs Chrome tabs or a logged-in website, including first-time setup and connection troubleshooting.
license: MIT
---

# Use signed-in Chrome

Use the [Playwright Extension](https://github.com/microsoft/playwright/blob/main/packages/extension/README.md) with `@playwright/mcp --extension`. It works with the user's normal Chrome profile and sign-ins. This skill applies to coding agents that can load its `SKILL.md` instructions and use local MCP servers. Each harness has its own skill installation path and MCP configuration format; do not assume OpenCode's format applies elsewhere. Do not use a separate Playwright profile for a task that requires an existing login.

## Start with a connection check

If the requested Chrome tab is already accessible through a browser tool, use it. Setup is only for a missing or failing connection. Identify the current harness and inspect its MCP configuration. For OpenCode, `python3 scripts/setup_opencode.py check` from this skill's directory checks the MCP command without reading cookies or tokens. An MCP server shown as connected proves only that the **server** starts; verify Chrome access by opening the requested site and checking the expected signed-in page.

**Token case (no approval click needed).** If the MCP server's environment carries a valid `PLAYWRIGHT_MCP_EXTENSION_TOKEN` (e.g. set in the harness's MCP config), the extension auto-approves the connection and the Welcome/Allow-&-select flow is skipped entirely. In that case do **not** ask the user to click Allow & select — just open a site the user is known to be signed into (e.g. `mail.google.com`); the inbox landing proves the token works. A sign-in form or authwall on one site then means *that site is simply not signed into this profile*, not that the connection failed: have the user sign in once in their own Chrome (or pick the right profile), and never re-run token setup for that. Only when the token is absent or expired does the Welcome page appear.

## First-time setup

1. Identify the Chrome profile that is signed in to the requested site. The user can read the last component of **Profile Path** at `chrome://version`. If browser policy blocks that page, ask the user for the profile directory name; do not use a blocked page through another route.
2. Configure the harness's local MCP server to run `npx -y @playwright/mcp@latest --extension --profile-dir-name=<profile>`. Use the harness's own MCP configuration syntax from [Playwright's client examples](https://github.com/microsoft/playwright-mcp#readme). For OpenCode, `python3 scripts/setup_opencode.py configure --profile-dir-name 'Default'` from this skill's directory is a tested shortcut; replace `Default` with the chosen profile directory. It updates only `mcp.playwright`, saves a private backup, and prints no secrets. It accepts `--config PATH` for a nonstandard config file.
3. Ask the user to install the [Playwright Extension](https://chromewebstore.google.com/detail/playwright-extension/mmlmfjhmonkocbjadbfplnigmagldckm) in that same Chrome profile, if absent. The agent may open the store only when its browser tool permits it. Restart the harness after changing its MCP config.
4. *(Only when no token is configured — see the Token case above.)* Navigate to the requested site through Playwright. On the Playwright **Welcome** page, the user selects the intended tab with **Allow & select**. If it is missing from the list, open that site in Chrome and refresh the newest Welcome page. Only the user should approve a connection to their browser.
5. Check the resulting page URL and content. An authwall, sign-in form, connection timeout, or an extension page is not a successful connection. Report the observed blocker and stop before site-specific work.

Do not copy cookies, browser profile files, or authentication tokens into another browser. Do not spoof browser identity to get around a login or security check. If a browser policy blocks an extension or remote-debugging page, stop that route instead of trying CDP, shell commands, another browser surface, or an indirect route around the block.

## If unattended use is requested

The extension's `PLAYWRIGHT_MCP_EXTENSION_TOKEN` can skip future connection approvals. It does not grant access to all tabs; Playwright still controls its own tab group. Have the user generate and enter a fresh token locally, without pasting it into chat or committing it. Use a secret file with mode `0600` or another local secret store. Verify a **new** harness process can open the signed-in page with no browser click before calling the setup unattended. Keep Chrome running in the signed-in profile. If the page fails to load, report the result and leave scheduling disabled.

The token and profile options are documented in [Playwright's extension guide](https://github.com/microsoft/playwright/blob/main/packages/extension/README.md). The OpenCode helper follows its [MCP server guide](https://opencode.ai/docs/mcp-servers/).
