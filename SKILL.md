---
name: use-chrome
description: Drive the user's existing signed-in Chrome through the Playwright Agent CLI (`playwright-cli`), or a clean unauthenticated browser when a logged-out view is explicitly requested. Connects via the Playwright Extension (logged-in) or a fresh profile (clean). Uses `playwright-cli` shell commands through the agent's bash tool instead of an MCP server. Use when an agent needs Chrome tabs, a logged-in website, a logged-out/anonymous view, SERP navigation, or connection troubleshooting.
license: MIT
---

# Use signed-in Chrome (via `playwright-cli`)

Drive Chrome with the [Playwright Agent CLI](https://playwright.dev/agent-cli/introduction) — `playwright-cli` from the `@playwright/cli` package. The agent issues `playwright-cli ...` commands through its `bash` tool. There is **no MCP server and no browser tool schemas in the prompt** — that is the point. To reuse the user's signed-in profile, attach through the [Playwright Extension](https://github.com/microsoft/playwright/blob/main/packages/extension/README.md) with `attach --extension`.

- **Install once:** `npm install -g @playwright/cli` (verify: `playwright-cli --version`). If a global install is not possible, `npx @playwright/cli` works the same way but is slower per call.
- **Command reference on demand:** `playwright-cli --help` and `playwright-cli <cmd> --help`. For a resident, compact reference install the skill: `playwright-cli install --skills` (or `--skills=agents -g` for a shared install). Each harness has its own skill install path; do not assume OpenCode's applies elsewhere.
- **Do not** use a separate Playwright profile for a task that requires an existing login.

## Choosing the browser: logged-in (default) vs clean

**Default to the user's logged-in Chrome.** Unless the user explicitly asks otherwise, attach to their existing signed-in profile through the extension — that is the rest of this skill. Most tasks need it.

**Use a clean, unauthenticated browser only when the user asks for a logged-out view** — phrases like "use your own profile, not mine", "logged out", "a fresh profile", or "what a real visitor would see". A clean profile is a brand-new empty `user-data-dir`: no cookies, no Google account, no site sign-ins. Never copy the user's cookies, profile files, or tokens into it, and do not spoof browser identity to get around a login or security check.

**Exception — Google SERP work defaults to logged-out, and headful.** For Google
ranking/SERP checks ("where does X rank", page-1 analysis, etc.) use the clean browser by
default, because a signed-in Google SERP is personalized and shows owner-only panels. Use
the user's logged-in session for a SERP check only when they explicitly ask for *their*
personal view. Open the clean profile with `--headed` — a headless clean Chrome is
reliably captcha'd by Google. Details: [references/google-serp.md](references/google-serp.md).

Know which view you are serving. A **logged-in** Google session can show owner-only boxes that a real visitor never sees (e.g. a Search Console "Search performance for this query" panel marked "Visible only to you"). If the question is "what does a normal visitor see?", a logged-in SERP is *not* the answer — use the clean browser. When in doubt, ask.

## Logged-in attach (default)

Attach to the running Chrome via the extension, reusing its sign-ins, cookies, and tabs:

```
# the CLI reads the same PLAYWRIGHT_MCP_* namespace as the old MCP server.
# the token auto-approves the connection (no "Allow & select" click):
export PLAYWRIGHT_MCP_EXTENSION_TOKEN="$(cut -d= -f2 "$HOME/.config/playwright-cli/extension-token")"

playwright-cli -s=chrome attach --extension        # default channel = Chrome
# or a specific channel:  playwright-cli -s=chrome attach --extension=chrome-canary
```

- Use one named session (`-s=chrome`) so "the current tab" survives across commands; do **not** re-attach per call (that resets tab context and causes connect/disconnect churn).
- `attach` reuses the browser that's already running; it does not open a new one. The first `playwright-cli -s=chrome snapshot` returns the accessibility tree of the current tab.
- **Pass the channel inside the flag, never as the positional name.** `attach --extension=chrome` is correct; `attach chrome --extension=chrome` fails ("only one of [name], --cdp, --endpoint, or --extension can be specified") — the positional `[name]` is for attaching to a Playwright browser-server instance, not for the extension channel.
- When done, **`playwright-cli -s=chrome detach`** tears down the CLI session while leaving the user's Chrome running. Only `close` shuts a browser the CLI launched itself.

If the token is absent or expired, the Playwright **Welcome** page appears instead: have the user select the intended tab with **Allow & select** (only the user should approve a connection to their browser). If the target tab is missing from the list, open that site in Chrome and refresh the newest Welcome page. See "If unattended use is requested" below for setting up a token.

### Navigating an attached session: `goto` and `tab-new`, never `open`

**`open` is a *launch* verb, not a navigate verb.** In an extension-attached session, `playwright-cli open <url>` does **not** navigate your user's Chrome — it starts a brand-new local Playwright browser with a fresh temp `user-data-dir` (`/tmp/playwright_chromiumdev_profile-…`, `--disable-extensions`), so every page shows logged-out sign-in views even though the user is fully signed in. The tell in output is a line like `### Browser \`chrome\` opened with pid …` — any navigation command in an attached session that prints that line silently switched you to the clean context.

Navigate inside the user's browser with:

- `goto <url>` — navigate the current tab.
- `tab-new [url]` / `tab-list` / `tab-select <i>` — work in the extension's tab group; `tab-list` also tells you which tabs (hence which browser) you are in.
- `snapshot`, `find`, and the action commands — as usual, on whatever tab is current.

**Verify you are in the user's browser before site-specific work.** A sign-in form, a "logged out" marketing landing, or a `tab-list` with only the page you just opened means you are in a CLI-launched clean context: stop, `close` the launched browser, re-`attach`, and navigate with `goto`. The positive proof is a signed-in landing (an inbox, an account dashboard, an app workspace). A sign-in page on one site can also simply mean *that site* is not signed into the profile — check `tab-list` and try a second site before concluding the connection failed.

## Clean (unauthenticated) browser

For logged-out work, launch a standalone browser with a fresh empty profile, not the user's Chrome:

- **In-memory profile (default):** `playwright-cli open <url> --browser=chrome` — a brand-new empty profile, no cookies, no sign-ins. The CLI runs **headless by default**; add `--headed` to see it.
- **Reuse across runs in the same task:** `--persistent` (profile on disk, survives restarts) or `--profile=<dir>` (a wiped or brand-new `user-data-dir`). Reuse the same dir so cleared state persists across later runs.
- **Headful for Google SERP work:** open the clean profile with `--headed` from the start. A clean *headless* browser is served the Google "unusual traffic" captcha nearly every time, and reloading does not clear it — a headful clean profile sails through without one. For other unattended work stay headless and **if a captcha blocks you, switch to headful and ask the user:** relaunch the **same profile** with `--headed`.
- **A `--headed` window opens small and can hide behind other apps.** There is no `--start-maximized` flag; right after `open` run `playwright-cli -s=<name> resize 1400 900` (or `--mobile`) so the user can find it. Tell the user exactly where it is, have them click through the captcha, then poll `snapshot` until the results render.
- **Expect two harmless cosmetic things in the window** (do not "fix" them): the Chromium infobar "unsupported command-line flag: --disable-blink-features=AutomationControlled" (the CLI adds that flag to hide the automation banner, and Chromium warns about it — dismiss with ×), and a page that is narrower than a maximized window (`resize` sets the viewport, not the OS window; leftover space renders as gray). Details: [references/google-serp.md](references/google-serp.md).
- **Save the full HTML per page and parse offline** rather than reading the live DOM through the relay — see the "Driving the page reliably" note and [references/google-serp.md](references/google-serp.md) for SERP specifics (paging, extraction, captcha detection, and capturing full HTML with `eval --raw` + shell redirect — `run-code` cannot write files).

## Start with a connection check

If the requested Chrome tab is already accessible, just use it. Setup is only for a missing or failing connection. Identify the current harness and, for OpenCode, `python3 scripts/setup_opencode.py check` from this skill's directory verifies the CLI path **without reading cookies or tokens**: `playwright-cli` on PATH, the extension-token secret present, and the Playwright Extension installed in the profile. It proves the *CLI* is wired up; verify Chrome access by opening the requested site and checking the expected signed-in page.

**Token case (no approval click needed).** If the secret file carries a valid `PLAYWRIGHT_MCP_EXTENSION_TOKEN`, the extension auto-approves the connection and the Welcome/Allow-&-select flow is skipped entirely. In that case do **not** ask the user to click Allow & select — just open a site the user is known to be signed into (e.g. `mail.google.com`); the inbox landing proves the token works. A sign-in form or authwall on one site then means *that site is simply not signed into this profile*, not that the connection failed: have the user sign in once in their own Chrome (or pick the right profile), and never re-run token setup for that. Only when the token is absent or expired does the Welcome page appear.

## First-time setup

1. Identify the Chrome profile that is signed in to the requested site. The user can read the last component of **Profile Path** at `chrome://version`. If browser policy blocks that page, ask the user for the profile directory name; do not use a blocked page through another route.
2. Confirm the Playwright Extension is installed in that same Chrome profile ([store page](https://chromewebstore.google.com/detail/playwright-extension/mmlmfjhmonkocbjadbfplnigmagldckm)); the agent may open the store only when its browser tool permits it.
3. Attach and drive: `playwright-cli -s=<name> attach --extension` (with the token set, see above). Check the resulting page URL and content. An authwall, sign-in form, connection timeout, or an extension page is **not** a successful connection. Report the observed blocker and stop before site-specific work.

Do not copy cookies, browser profile files, or authentication tokens into another browser. Do not spoof browser identity to get around a login or security check. If a browser policy blocks an extension or remote-debugging page, stop that route instead of trying CDP, shell commands, another browser surface, or an indirect route around the block.

## Driving the page reliably

Once attached, drive the target page with `playwright-cli` commands. The pattern is: **`snapshot` → read the element refs → act by ref** (refs look like `e15`). These are hard-won gotchas that save many turns, especially on heavy single-page apps (App Store Connect, Play Console, …).

- **Navigate attached sessions with `goto` / `tab-new`, never `open`** — `open` launches a clean browser with no sign-ins. See "Navigating an attached session" above.

- **Prefer the accessibility tools first** (`snapshot`, `find`). Some SPAs hide action buttons from the accessibility tree even though they are in the DOM: when `find` reports "No matches" for a control you can see, fall back to a DOM-level `eval` click matched on `element.textContent.trim()`.
- **`eval` through the extension relay mangles complex JS (extension mode).** Keep the function **single-line** and avoid **regex literals, backslashes, and escaped double quotes** — the relay truncates/corrupts them and the call fails with "Unexpected end of input" or "missing ) after argument list". Use `.indexOf()` instead of regex, block bodies with an explicit `return`, and plain double quotes only. Over a CDP/self-launched browser the relay is not in the path, so `eval` is more forgiving.
- **React-controlled inputs and textareas:** assigning `.value` alone does not update React state. Use the native value setter, then dispatch events:
  `Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set.call(el, "x")`
  followed by `el.dispatchEvent(new Event("input", { bubbles: true }))` (and `change` / `blur`).
- **Probe before you act.** Run a read-only `eval` that lists the candidate controls and confirms the target is uniquely identifiable before clicking anything destructive.
- **Keep one persistent session** (`-s=chrome`) so the "current tab" survives across commands; do not re-attach per call.
- **Verify state after each step** (URL, the changed field, the resulting status) before the next step. `playwright-cli -s=chrome snapshot` re-reads the page.
- **Network inspection** is available without MCP: `requests` (numbered list), `request <n>` (full details), `route`/`unroute` to mock.
- **Never print the extension token or the site's secrets/env values** to the transcript or a commit; compare through shell variables and print only yes/no/counts.
- **Anti-bot / captcha escalation.** Some sites (notably Google) serve a captcha or "unusual traffic" interstitial to automated access. Detect it (URL keywords like `sorry/index`, `unusual traffic`, `recaptcha`), and **do not** try to bypass it or spoof identity. If you are headless and cannot solve it, relaunch headful with a visible window and **ask the user to solve it**, then continue. For clean profiles default to headless for general unattended work, but **for Google SERP work go headful from the start** — see the Clean browser section.

## If unattended use is requested

The extension token (`PLAYWRIGHT_MCP_EXTENSION_TOKEN`) can skip future connection approvals. It does not grant access to all tabs; Playwright still controls its own tab group. Have the user generate and enter a fresh token locally, without pasting it into chat or committing it. Store it in a secret file with mode `0600` — the default here is `~/.config/playwright-cli/extension-token` (created by this setup) — and feed it to the CLI with `export PLAYWRIGHT_MCP_EXTENSION_TOKEN="$(cut -d= -f2 "$HOME/.config/playwright-cli/extension-token")"` before `attach --extension`. Verify a **new** CLI process can open the signed-in page with no browser click before calling the setup unattended. Keep Chrome running in the signed-in profile. If the page fails to load, report the result and leave scheduling disabled.

The token and extension options are documented in [Playwright's extension guide](https://github.com/microsoft/playwright/blob/main/packages/extension/README.md); CLI configuration and the full `PLAYWRIGHT_MCP_*` env list are in [the CLI configuration docs](https://playwright.dev/agent-cli/configuration).
