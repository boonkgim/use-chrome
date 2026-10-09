# Navigating Google SERPs

Hard-won notes for reading Google search results in a browser (logged-out or logged-in).
Load this only when the task is actually about Google SERP navigation / ranking checks.

> **This file is a reference, not a hard rule.** The selectors and class names below
> (`LC20lb`, `yuRUbf`, `MheKwc`, `/goto?url=`, …) are what Google served at the time of
> writing. **Website layouts change.** Use these as a starting point: if a selector no
> longer matches, **do not** assume the page has no results — investigate the actual HTML
> (dump it, look at what changed, find the new marker) instead of following this file
> blindly. A count of 0 is a signal to re-inspect, not a conclusion.

## Decide logged-in vs logged-out first

**For Google SERP work, default to logged-out (clean profile).** Only use a logged-in
session for a SERP check if the user explicitly asks for their personal view.

- **Logged-out (clean profile)** = the generic view a normal visitor sees. Use this for
  "where does X rank", "what does a visitor see on page 1", or any ranking/SERP analysis.
- **Logged-in is not a fair answer to "where does it rank"** for two reasons:
  1. Google personalizes SERPs per account (search history, location, sign-in state), so the
     user's results differ from the general population.
  2. A signed-in site owner gets extra owner-only panels (Search Console insights boxes,
     "Visible only to you") that change the on-screen result count.
- If a logged-in session was used anyway, say so explicitly and strip those boxes before
  reporting positions.

## Run SERP checks headful, and what the window will look like

Open the clean profile with `--headed` (see SKILL.md "Clean browser"): a clean *headless*
Chrome is served the "unusual traffic" captcha nearly every time (reloading does not clear
it), while a headful clean profile usually sails straight to results.

Two cosmetic things the user will see in the window — **neither is an error**:

- **Flag infobar:** "You are using an unsupported command-line flag:
  `--disable-blink-features=AutomationControlled`…". The CLI adds that flag to suppress the
  "Chrome is being controlled by automated test software" banner, and Chromium warns about
  unsupported flags. Harmless — dismiss with the ×; do not try to remove the flag (it would
  only bring the automation banner back).
- **Page narrower than the window:** `playwright-cli resize` sets the *viewport*, not the
  OS window. If the window ends up wider than the viewport (e.g. maximized afterwards),
  Chrome renders the page at the viewport width and shows the leftover space as gray.
  Irrelevant for SERP work (you parse the HTML); to make it look full, resize the viewport
  to match the window or drag the window to the viewport width.

## Paging

- One page = 10 organic results. Page N is `?q=<query>&start=(N-1)*10` (start=0 is page 1).
  E.g. page 4 → `&start=30` (global positions 31–40).
- Navigate per page with `playwright-cli -s=<session> goto "https://www.google.com/search?q=<query>&start=<start>"`,
  then `sleep 4` before capturing the HTML.

## Save the full HTML; parse offline

Do **not** rely on extracting the live DOM through the relay — it is flaky and the
selectors below rarely survive it. Instead capture each page's full HTML to a file and
parse the file. This is the reliable path and lets you re-run analysis without re-fetching.

`run-code` looks tempting but **cannot write files**: its VM sandbox has no `require`
(`ReferenceError: require is not defined`) and `await import('node:fs')` throws
`ERR_VM_DYNAMIC_IMPORT_CALLBACK_MISSING`. Use `eval --raw` + a shell redirect instead:

```
playwright-cli -s=serp eval --raw "document.documentElement.outerHTML" > /tmp/serp-p1.raw
```

The `--raw` output is a JSON-quoted string, so unquote it in Python before parsing:

```python
import json
s = json.loads(open('/tmp/serp-p1.raw', encoding='utf-8').read())
```

Field notes:

- A full SERP page is ~3 MB raw — that's fine.
- If your `eval` returns an **object** via `JSON.stringify(...)`, the CLI prints it as a
  plain string, so `json.loads` **twice**. Simpler: return the bare HTML string and parse
  once.
- `eval` in a self-launched (CDP) session is forgiving — a one-line
  `async () => { await new Promise(r => setTimeout(r, 1000)); return document.documentElement.outerHTML; }`
  works.

## Detecting a captcha (stop and escalate)

A captcha means Google flagged the request. Detect by URL/keywords, then escalate to the user:

```js
const sorry = /sorry\/index|unusual traffic|recaptcha/i.test(
  location.href + ' ' + document.title
);
```

When `sorry` is true the results never render. SERP work already runs **headful**, so just
point the user at the window, have them solve the captcha, and poll `eval`/`snapshot` until
real results render. Reuse the same profile dir so state persists.

## Extracting results from saved HTML (modern Google layout)

Google's current HTML **does not** use the old `class="g"` organic-result wrapper. The
signals that do exist:

- **Result titles**: `<h3 class="LC20lb ...">Title</h3>`. Count these to know how many
  organic results a page served.
- **The real destination URL is not plain text.** It is wrapped as
  `href="/goto?url=CAES<base64>"` and in `ping="/url?...&url=CAES<base64>"` — a base64 blob.
  The human-readable domain *also* appears as plain text in the display URL / embedded data
  blob, so the robust trick is: after each title's `</h3>`, scan the next ~15 KB for the
  first `https?://host` that is not a Google asset.

```python
import re, html as ih, urllib.parse
def parse(fn):
    s = open(fn, encoding='utf-8', errors='ignore').read()
    out = []
    for m in re.finditer(r'<h3 class="LC20lb[^"]*"[^>]*>(.*?)</h3>', s, re.S):
        title = ih.unescape(re.sub(r'<[^>]+>', '', m.group(1))).strip()
        window = s[m.end(): m.end()+15000]
        dom = None
        for dm in re.finditer(r'https?://([a-z0-9.-]+\.[a-z]{2,})', window, re.I):
            host = dm.group(1).lower()
            if not re.search(r'google|gstatic|ggpht|golang|lens\.google|support\.google|'
                             r'accounts\.|googleadservices|schema\.org|w3\.org|ytimg|youtube', host):
                dom = host; break
        out.append((title, dom))
    return out
```

- Global position = `(page-1)*10 + in-page-index`.
- **If the `LC20lb` count comes back 0 (or far lower than expected), do not conclude the
  page has no results** — Google likely changed its markup. Dump the page's HTML, find the
  new title/URL markers, and re-derive the parser for *this* response. The exact class
  names are a snapshot, not a contract.
- **Page 1 often serves only 9 organic results, not 10.** The 10th `<h3>` is frequently an
  **AI Mode / AI Overview reply** box (class `MheKwc`, title like "AI Mode reply for <query>"),
  and a local map pack + "People also ask" further compress the page. So a total of 98–100
  across 10 pages is normal, not a parsing gap.

## Gotcha: image carousels are not organic results

A domain's mention count is not a ranking hit. Google embeds image-carousel / attribution
items ("atritem", `client=IMAGE_SEARCH` favicons, hero images, `about-this-image` links)
that reference a site's assets even when that site has **no organic result** on the page.
Before claiming "X is also on page N", verify the hit belongs to an organic result — the
display-URL `cite` block that follows the result's `<h3>` (e.g.
`class="byrV5b"><cite ...>https://glimousine.com</cite>`). Hits that live only inside
image payloads are image results, not organic positions.

## Gotcha: brand-substring false positives

Grepping a brand name matches *other companies* that contain the string. Example: searching
for `glimousine.com` and grepping `"glimousine"` also matches the **different** company
`sglimousinetaxi.com` ("s**glimousine**taxi"). Always grep the **exact domain**
(`glimousine.com`, ideally with the `.com`), not the bare brand, when locating a specific
site's rank. A loose brand match at some position is a false positive unless the exact
domain confirms it.

## Verifying a page really rendered

Before trusting "site X is not on page Y", confirm the page actually loaded results: check
the result count from the `LC20lb`/`yuRUbf` markers, or confirm a few known competitor
domains are present as plain text. An empty/captcha page has 0 results and a false
"not found" is meaningless.
