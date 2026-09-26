---
name: use-chrome
description: Connect OpenCode to the user's existing signed-in Chrome profile through Playwright MCP. Use when OpenCode needs Chrome tabs or a logged-in website, including first-time setup and connection troubleshooting.
---

# Use Chrome from OpenCode

Use the [Playwright Extension](https://github.com/microsoft/playwright/blob/main/packages/extension/README.md) with `@playwright/mcp --extension`. It works with the user's normal Chrome profile and sign-ins. Do not use a separate Playwright profile for a task that requires an existing login.

## Start with a connection check

If the requested Chrome tab is already accessible through the configured browser tool, use it. Setup is only for a missing or failing connection. Run `python3 scripts/setup_opencode.py check` from this skill's directory to inspect OpenCode's MCP command; it does not read cookies or tokens. `opencode mcp list` confirms that the MCP **server** starts, but does not prove that it reached Chrome. Verify by opening the requested site with the browser tool and checking the expected signed-in page.

## First-time setup

1. Identify the Chrome profile that is signed in to the requested site. The user can read the last component of **Profile Path** at `chrome://version`. If browser policy blocks that page, ask the user for the profile directory name; do not use a blocked page through another route.
2. Run `python3 scripts/setup_opencode.py configure --profile-dir-name 'Default'` from this skill's directory, replacing `Default` with the chosen profile directory. The script updates only OpenCode's `mcp.playwright` entry, saves a private backup, and prints no secrets. It accepts `--config PATH` when OpenCode uses a nonstandard config file.
3. Ask the user to install the [Playwright Extension](https://chromewebstore.google.com/detail/playwright-extension/mmlmfjhmonkocbjadbfplnigmagldckm) in that same Chrome profile, if absent. The agent may open the store only when its browser tool permits it. Restart OpenCode after changing its config.
4. Navigate to the requested site through Playwright. On the Playwright **Welcome** page, the user selects the intended tab with **Allow & select**. If it is missing from the list, open that site in Chrome and refresh the newest Welcome page. Only the user should approve a connection to their browser.
5. Check the resulting page URL and content. A LinkedIn authwall, sign-in form, connection timeout, or an extension page is not a successful connection. Report the observed blocker and stop before site-specific work.

Do not copy cookies, browser profile files, or authentication tokens into another browser. Do not spoof browser identity to get around a login or security check. If a browser policy blocks an extension or remote-debugging page, stop that route instead of trying CDP, shell commands, another browser surface, or an indirect route around the block.

## If unattended use is requested

The extension's `PLAYWRIGHT_MCP_EXTENSION_TOKEN` can skip future connection approvals. It does not grant access to all tabs; Playwright still controls its own tab group. Have the user generate and enter a fresh token locally, without pasting it into chat or committing it. Use a secret file with mode `0600` or another local secret store. Verify a **new** OpenCode process can open the signed-in page with no browser click before calling the setup unattended. Keep Chrome running in the signed-in profile. If the page fails to load, report the result and leave scheduling disabled.

The token and profile options are documented in [Playwright's extension guide](https://github.com/microsoft/playwright/blob/main/packages/extension/README.md). OpenCode's local MCP configuration is documented in its [MCP server guide](https://opencode.ai/docs/mcp-servers/).
