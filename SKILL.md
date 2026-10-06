---
name: use-chrome
description: Connect an MCP-capable coding agent to the user's existing signed-in Chrome profile through Playwright MCP, or to a clean unauthenticated browser when a logged-out view is explicitly requested. Use when an agent needs Chrome tabs, a logged-in website, a logged-out/anonymous view, SERP navigation, or connection troubleshooting.
license: MIT
---

# Use signed-in Chrome

Use the [Playwright Extension](https://github.com/microsoft/playwright/blob/main/packages/extension/README.md) with `@playwright/mcp --extension`. It works with the user's normal Chrome profile and sign-ins. This skill applies to coding agents that can load its `SKILL.md` instructions and use local MCP servers. Each harness has its own skill installation path and MCP configuration format; do not assume OpenCode's format applies elsewhere. Do not use a separate Playwright profile for a task that requires an existing login.

## Choosing the browser: logged-in (default) vs clean

**Default to the user's logged-in Chrome.** Unless the user explicitly asks otherwise, connect to their existing signed-in profile through the extension — that is the rest of this skill. Most tasks need it.

**Use a clean, unauthenticated browser only when the user asks for a logged-out view** — phrases like "use your own profile, not mine", "logged out", "a fresh profile", or "what a real visitor would see". A clean profile is a brand-new empty `user-data-dir`: no cookies, no Google account, no site sign-ins. Never copy the user's cookies, profile files, or tokens into it, and do not spoof browser identity to get around a login or security check.

**Exception — Google SERP work defaults to logged-out.** For Google ranking/SERP checks
("where does X rank", page-1 analysis, etc.) use the clean browser by default, because a
signed-in Google SERP is personalized and shows owner-only panels. Use the user's logged-in
session for a SERP check only when they explicitly ask for *their* personal view.
Details: [references/google-serp.md](references/google-serp.md).

Know which view you are serving. A **logged-in** Google session can show owner-only boxes that a real visitor never sees (e.g. a Search Console "Search performance for this query" panel marked "Visible only to you"). If the question is "what does a normal visitor see?", a logged-in SERP is *not* the answer — use the clean browser. When in doubt, ask.

## Clean (unauthenticated) browser

For logged-out work, launch a standalone Playwright/Chromium with a fresh empty profile, not the user's Chrome:

- **Fresh profile**: `chromium.launchPersistentContext('<tmp>/clean-profile')` on a wiped or brand-new `user-data-dir`. Point `executablePath` at the system Chrome (e.g. `/usr/bin/google-chrome`) when a matching bundled Chromium build is not downloaded.
- **Default to headless** (`headless: true`) for unattended runs.
- **If a captcha blocks you, switch to headful and ask the user.** A headless session on this kind of network gets flagged by Google ("Our systems have detected unusual traffic" / an "I'm not a robot" reCAPTCHA) and cannot solve it itself. Relaunch the **same profile** with `headless: false` and `--start-maximized` so the window is easy to find (a tiny default-size window gets hidden behind other apps), tell the user exactly where it is, and have them click through the captcha. Poll the page until the results render, then continue. **Reuse the same `user-data-dir`** so the cleared state persists across later runs in the same task.
- **Save the full HTML per page** (`page.content()` to disk) and parse it offline rather than reading the live DOM through the relay. For Google SERP specifics — paging, result extraction, captcha detection, and the gotchas — see [references/google-serp.md](references/google-serp.md).

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

## Driving the page reliably

Once connected, drive the target page with the browser tools. These are hard-won gotchas that save
many turns, especially on heavy single-page apps (App Store Connect, Play Console, …).

- **Prefer the accessibility tools first** (`browser_snapshot`, `browser_find`). Some SPAs hide
  action buttons from the accessibility tree even though they are in the DOM: when `browser_find`
  reports "No matches" for a control you can see, fall back to a DOM-level `browser_evaluate`
  click matched on `element.textContent.trim()`.
- **`browser_evaluate` through the extension relay mangles complex JS.** Keep the function
  **single-line** and avoid **regex literals, backslashes, and escaped double quotes** — the relay
  truncates/corrupts them and the call fails with "Unexpected end of input" or "missing ) after
  argument list". Use `.indexOf()` instead of regex, block bodies with an explicit `return`, and
  plain double quotes only.
- **React-controlled inputs and textareas:** assigning `.value` alone does not update React state.
  Use the native value setter, then dispatch events:
  `Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set.call(el, "x")`
  followed by `el.dispatchEvent(new Event("input", { bubbles: true }))` (and `change` / `blur`).
- **Probe before you act.** Run a read-only `browser_evaluate` that lists the candidate controls
  and confirms the target is uniquely identifiable before clicking anything destructive.
- **Keep one persistent connection** so the "current tab" survives across calls; do not restart the
  MCP server per call (that resets tab context and causes connect/disconnect churn).
- **Verify state after each step** (URL, the changed field, the resulting status) before the next
  step.
- **Never print the extension token or the site's secrets/env values** to the transcript or a
  commit; compare through shell variables and print only yes/no/counts.
- **Anti-bot / captcha escalation.** Some sites (notably Google) serve a captcha or
  "unusual traffic" interstitial to automated access. Detect it (URL keywords like
  `sorry/index`, `unusual traffic`, `recaptcha`), and **do not** try to bypass it or spoof
  identity. If you are headless and cannot solve it, relaunch headful with a visible
  (`--start-maximized`) window and **ask the user to solve it**, then continue. For clean
  profiles default to headless and only go headful on a block; see the Clean browser section.

## If unattended use is requested

The extension's `PLAYWRIGHT_MCP_EXTENSION_TOKEN` can skip future connection approvals. It does not grant access to all tabs; Playwright still controls its own tab group. Have the user generate and enter a fresh token locally, without pasting it into chat or committing it. Use a secret file with mode `0600` or another local secret store. Verify a **new** harness process can open the signed-in page with no browser click before calling the setup unattended. Keep Chrome running in the signed-in profile. If the page fails to load, report the result and leave scheduling disabled.

The token and profile options are documented in [Playwright's extension guide](https://github.com/microsoft/playwright/blob/main/packages/extension/README.md). The OpenCode helper follows its [MCP server guide](https://opencode.ai/docs/mcp-servers/).
