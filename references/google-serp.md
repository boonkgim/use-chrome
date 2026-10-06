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

## Paging

- One page = 10 organic results. Page N is `?q=<query>&start=(N-1)*10` (start=0 is page 1).
  E.g. page 4 → `&start=30` (global positions 31–40).
- Navigate per page with `page.goto(url, {waitUntil:'domcontentloaded'})`, wait ~2s, then act.

## Save the full HTML; parse offline

Do **not** rely on extracting the live DOM through the MCP relay — it is flaky and the
selectors below rarely survive the relay. Instead `page.content()` each page to a file and
parse the file. This is the reliable path and lets you re-run analysis without re-fetching.

```js
const html = await page.content();
fs.writeFileSync(`/tmp/serp-p${n}.html`, html);
```

## Detecting a captcha (stop and escalate)

A captcha means Google flagged the request. Detect by URL/keywords, then escalate to the user:

```js
const sorry = /sorry\/index|unusual traffic|recaptcha/i.test(
  location.href + ' ' + document.title
);
```

When `sorry` is true the results never render. Strategy (see SKILL.md "Clean browser"):
if headless got blocked, relaunch headful + `--start-maximized`, point the user at the
window, have them solve it, then poll until results appear. Reuse the same profile so the
cleared state persists.

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
