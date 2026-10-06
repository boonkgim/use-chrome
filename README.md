# use-chrome

Connect an AI coding agent to your **existing signed-in Chrome profile** with the [Playwright Extension](https://github.com/microsoft/playwright/blob/main/packages/extension/README.md) and Playwright MCP. The skill helps with first-time setup, an interactive connection check, and an optional no-click connection for scheduled work.

## Compatibility

Playwright MCP works with [many MCP clients](https://github.com/microsoft/playwright-mcp#readme). This skill works in a harness that can load `SKILL.md` instructions and run a local MCP server. Each harness has its own skill location and MCP configuration format. The bundled `scripts/setup_opencode.py` helper is specific to **OpenCode**; the instructions in `SKILL.md` cover other MCP-capable harnesses.

The first-run setup and no-click connection were tested with OpenCode, Chrome, and the Playwright Extension on Linux. Other harnesses should verify their own connection before relying on it.

## Install

Clone this repository into the skill directory used by your harness. For example:

```bash
# OpenCode
git clone https://github.com/boonkgim/use-chrome.git ~/.config/opencode/skills/use-chrome

# Claude Code
git clone https://github.com/boonkgim/use-chrome.git ~/.claude/skills/use-chrome

# Codex
git clone https://github.com/boonkgim/use-chrome.git ~/.agents/skills/use-chrome
```

Use the path for **one** harness, or clone once and link it into the others. Restart the harness after installing or changing its MCP configuration.

## First use

Ask your agent to use `use-chrome` to open a page in your signed-in Chrome profile. It will:

1. Check whether it can already reach the requested tab.
2. Configure Playwright MCP in extension mode if needed. OpenCode users can run `python3 scripts/setup_opencode.py configure --profile-dir-name 'Default'` from this repo, replacing `Default` with their Chrome profile directory name.
3. Guide you to install the Playwright Extension in that profile and approve the first connection with **Allow & select**.
4. Verify the actual signed-in page. An MCP server marked “connected” is not enough to prove browser access.

For unattended work, the extension supports a profile-specific connection token. Enter it locally and keep it out of chat and Git. A fresh process must open the target page without a click before scheduling the task. The token does not give access to every Chrome tab.

The full agent instructions and troubleshooting boundaries are in [SKILL.md](SKILL.md). The OpenCode helper checks or updates only its Playwright MCP entry and makes a private backup before changing an existing config.

## License

MIT. See [LICENSE](LICENSE).
