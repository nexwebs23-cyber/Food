# Static per-recipe pages — IMPLEMENTED 2026-10-30

Status: **implemented** by `build_site.py` (repo root, stdlib-only Python).
The JS per-route SEO stopgap in `index.html` (`setRouteMeta()`) still runs
in the SPA, but crawlers now get real static pages (see below).

## What was built (2026-10-30)

- `build_site.py` parses the data out of `index.html` (source of truth) and,
  on every Vercel build (`buildCommand: "python3 build_site.py"` in
  `vercel.json`), regenerates:
  - `data/*.js` (30 files, ~3.0 MB total): `recipes.js`, `extra-en.js`,
    `extra-<lang>.js` ×12, `ui-en.js`, `ui-<lang>.js` ×12,
    `lang-data-hi.js`, `lang-data-ru.js`, `lang-new.js`.
  - 58 thin static pages: `recipe/<slug>/index.html` ×32,
    `category/<slug>/index.html` ×7, `country/<slug>/index.html` ×16,
    `about/index.html`, `privacy/index.html`, `contact/index.html`. Each has
    its own `<title>` (≤60 chars), meta description, canonical + OG/Twitter
    tags, JSON-LD mirroring `setRouteMeta()`, the route's content, the photo
    with an absolute `/assets/…` URL, and a prominent link back to the SPA
    route. No `<base>` script, no SPA JS.
  - A slim `index.html` (~160 KB, was 3,144,085 bytes): data blocks become
    empty declarations, an async loader pulls `data/*.js` (English first,
    other languages on demand), and the six raw `<h1>` elements become one
    `<h1>` plus runtime heading promotion (`promoteH1()` in `showView()`).
- `index.html` in the repo stays FAT (the daily new-recipe cron edits it
  directly); the build produces the slim version in place at deploy time.
  The build refuses to run on an already-slim file (marker
  `ZAIKA_SLIM_BUILD`), so it cannot corrupt the source. Committed `data/` and
  static pages are snapshots for local serving; Vercel regenerates them.
- `vercel.json`: `buildCommand` + trailing-slash rewrites
  (`/recipe/:slug/`, `/category/:slug/`, `/country/:slug/` → `/index.html`)
  so unknown trailing-slash slugs show the SPA 404 view, not a bare 404.
  The apex (`zaikaworlds.com` → www, 308) and http → https (308) redirects
  are correct and unchanged; nothing on the site links to them.
- Measured data blocks (2026-10-30, corrected — the earlier figures below
  were from a stale measurement): main inline `<script>` 3,053,458 bytes;
  `EXTRA_NEW` 1,935,646 bytes; `EXTRA` 640,664 bytes; `RECIPES` 59,888
  bytes; `LANG_DATA` (hi/ru only) ~55 KB; `LANG_NEW_RAW/2/3` ~54 KB
  (short-form name/desc/alt for the other 10 languages, merged into
  `LANG_DATA` by a top-level loop that reads `RECIPES.length` — the loop now
  runs inside `_mergeLangNew()`, called by the loader after the data loads);
  `UI` ~91 KB (plus 78 `UI.en/ru/hi.<key>=…` patch statements, now carried
  in the per-language UI data files); `INFO` ~117 KB; `LINK_TXT` ~6 KB
  (kept inline, small); `_CL/_DF/_SV/_DS` + `IMG_DIMS` ~3 KB (kept inline).
- Verified locally (jsdom, 51 checks) and on the Vercel preview before
  pushing to main: home renders 32 cards, Hindi switch, recipe route +
  video embed, search, Saved (localStorage `zaika-saved`), H1 promotion
  (exactly 1 `<h1>` per view), all 58 static pages (title ≤60, unique,
  canonical, 1 H1, valid JSON-LD), trailing slash, `?lang=hi` canonical.

## SEO audit round 2 — IMPLEMENTED 2026-10-30 (branch seo-audit-round2)

All items from `~/workspace/user/files/zaikaworlds_seo_audit.xlsx` (8 sheets,
audit date 30 Oct 2026) resolved in one go, verified locally and live.

- **A. Raw lists fixed**: recipe pages rendered Notes/Variations/Common
  mistakes as Python repr `['...']`; now `<ul><li>` on all 32 pages (and
  split ingredients in HTML + JSON-LD + the SPA's data files).
- **B. Real URLs**: nav/hero/footer now point at /recipes, /category/world-food,
  /trending, /faqs (new static pages); WhatsApp shares the real page URL.
- **C. Country cards**: all 14 link to /country/<slug>; country intros are
  unique per country (recipe names + first recipe's description).
- **D. Static URL primary**: og:url + canonical are the static URL; a share/copy
  link for the static URL is on each recipe page; the hash URL is kept only as
  the "Open interactive recipe" CTA.
- **E. og:type article** on recipe pages + article:published_time 2026-10-28
  for all 32 (git root commit 860a4e7 — the real first-add date; modified
  omitted, no per-recipe date exists). Recorded in recipe_dates.json (repo root — tools/ is vercelignored).
- **F. Titles/descriptions**: recipe pattern "<Dish> Recipe (<Adj>, <time> Min)
  | Zaika Worlds" (all ≤60); descriptions 140-155 (all 32 English in range,
  unique); list/info/new pages each unique 140-155; homepage title/H1 include
  'recipes' + 'Pakistani'. SPA setRouteMeta() mirrors the patterns.
- **G. Ingredients one-per-line**: split at build time in static pages, SPA
  data files and JSON-LD. EN 223 → 409 items (all 13 languages: 2,899 → 5,276).
  Qualifier fragments re-attach as parentheticals, never orphan <li>s.
- **H. Unique OG image**: each recipe page uses its own photo; category/country
  pages use a representative recipe photo; homepage keeps the biryani hero.
- **I. WebP**: the last 10 recipe JPGs converted (quality 85, 43–58% of JPEG
  size); feed.xml enclosure URLs + byte lengths updated; stale .jpgs deleted.
- **J. About**: names Muhammad Habib (runs Zaika Worlds; no invented
  credentials) and states plainly that recipe photos are unique AI-generated
  images, not photographs; the Desi passage now matches the real categories
  (no bread recipe exists — not promised).
- **K. Video embed + VideoObject**: YouTube iframe (youtube-nocookie, matching
  language's video) + VideoObject JSON-LD on the 15 recipes with videos
  (uploadDate only from real publish records). SPA already embeds via YT.Player.
- **L. Recipe schema validated**: name, image, split ingredients, instructions,
  totalTime (real minutes, no invented prep/cook split), recipeYield;
  BreadcrumbList on all pages; FAQPage on recipe pages, homepage and /faqs.
- **M. Homepage without JS**: slim index.html carries a static 32-card grid
  (same markup as the SPA's cardHtml); SPA render() replaces it on load.
- **N. Multilingual URLs + hreflang**: recipe pages + homepages for all 13
  languages (data complete 32/32 in every language); hreflang for every
  variant + x-default → English root; language pages fully in-language from
  the site's own translations. Category/country language variants NOT done
  (follow-up).
- **O. Content gaps**: audit's "Not covered" claims for chapli kebab and halwa
  puri were WRONG (both live). Genuinely missing Pakistani staples (haleem,
  korma, paratha, kheer, seekh kebab) are new recipes, not built here — the
  posting queue was reordered so they come first (R317–R321, positions 6–10;
  Kabuli Pulao moved to 11). Hubs /eid-recipes (11) + /ramadan-recipes (12)
  from existing recipes only; /bbq-recipes skipped (BBQ has just 2 recipes —
  the category page serves it). Guide /guides/dum-cooking from real
  biryani/karahi/nihari tips, attributed. "How to make biryani masala" and
  "biryani vs pulao" do not exist in the data — reported as gaps, not invented.
- **P. Homepage FAQ**: 10 real cooking Q&As verbatim from recipe EXTRA faq
  data (in all 13 languages) + the language-menu question; FAQPage JSON-LD on
  the homepage and /faqs. Stale UI.en.faq answers (Saved localStorage, 15
  videos) fixed as part of the replacement.
- **Q. Verified**: robots.txt fine (does not block /assets/); sitemap.xml now
  generated by build_site.py (461 URLs) so it cannot go stale; full internal
  link crawl on the generated pages (3,056 links, 0 broken); PageSpeed could
  not be run — LCP/CLS risks checked were hero fetchpriority, WebP sizes and
  the static grid; a real PageSpeed run is still needed.
- **Privacy fix (found while verifying)**: the Privacy page said "No analytics"
  while Google Analytics (G-KYH4YJMWB4) is live. English privacy now discloses
  Google Analytics (aggregate visits, GA cookies, no personal data) and
  corrects the Cookies section. The 12 translated privacy texts still say
  "no analytics" — they need a translator.
- **Known limitations**: 7 CJK (zh/ja) recipe descriptions land under 140
  chars (CJK text is denser; ≤155 and unique, reported not padded); 3 CJK
  language-homepage descriptions likewise; non-English faqIntro lines are
  still site-usage worded (Q&As are fully translated cooking questions);
  category/country language variants not generated; Google Rich Results Test
  and PageSpeed still need a manual run.
- **Future-proofing**: `python3 build_site.py --check` generates all 460 static
  pages in memory and FAILS (exit 1) on regressions (raw lists, titles >60,
  descriptions >155 / English recipe descriptions outside 140-155, duplicate
  English recipe descriptions, missing canonical/og:image, og:type not
  article, H1 != 1, JSON-LD parse failures, missing Recipe fields, qualifier
  orphans, TREND_IDS drift, sitemap/page mismatch). Authoring rules are in
  build_site.py's docstring.

## Why not now (measured, 2026-10-30)

- `index.html` is 3,126,308 bytes, one file, no build step (Vercel Framework
  "Other", no build command). The main inline `<script>` is 2,079,372 bytes
  (66.5%). Biggest block is `EXTRA_NEW` — 1,283,670 bytes (41.1%) of
  translated long-form text, merged into `EXTRA` at runtime by a loop just
  before `applyLang(); applyRoute();`. There is zero `fetch`/`import()` in the
  file: everything is consumed synchronously. Splitting data out needs an
  async loader + a build step, and `tools/split_export.py` rebuilds
  `index.html` wholesale from each new export, so any hand-split would be
  wiped on the next export unless the split becomes part of that workflow.
- A plain static SEO page loses all SPA behaviour: language switching
  (`setLang`/`applyLang`, `LANG_DATA`/`EXTRA_NEW`/`UI`), video embeds
  (`videos` dict + `ytPlayer`, 13 recipes), Saved (localStorage key
  `zaika-saved`), search/filters (`filtered()`), routing (`openRecipe` /
  `history.pushState` / `popstate`, incl. legacy `#recipe/<slug>` hashes).
  A full SPA-shell copy per recipe would be ~3.1 MB × 32 ≈ 100 MB and
  defeats the purpose. So a static page must be a **thin SEO shell** that
  links back to the SPA route ("Open interactive recipe"), not a copy.
- Vercel precedence (verified from official docs, not assumed):
  `vercel.com/docs/project-configuration/vercel-json`, rewrites section —
  "The `source` property should NOT be a file because precedence is given
  to the filesystem prior to rewrites being applied." A static file therefore
  wins over the `/recipe/:slug → /index.html` rewrite. Still to be verified
  on a preview deployment (see checklist).
- Path hazard: `cleanUrls` is not set, so pages must be directory-style
  `recipe/<slug>/index.html`, not flat `recipe/<slug>.html` (the latter would
  not match `/recipe/<slug>`). The SPA `<base>` script's regex requires the
  pathname to end exactly at the slug; a directory-index URL with a trailing
  slash (`/recipe/biryani/`) does not match that branch, so relative
  `assets/…` references would resolve under `/recipe/biryani/` → 404s.
  Static pages must therefore use **absolute `/assets/…` URLs and omit the
  `<base>` script**.
- Staleness: `split_export.py` leaves files other than `index.html` /
  `assets/` / `videos/` untouched, so generated `recipe/` files would survive
  a re-run — but they would go stale when the export changes unless
  regeneration is wired into the export workflow.

## Concrete plan — done 2026-10-30

1. ✅ Stdlib-only Python generator `build_site.py` (repo root, not `tools/`
   — `tools/` is vercelignored, so the build script must live at the root).
   It parses the data blocks out of `index.html` and emits thin SEO pages
   at `recipe/<slug>/index.html` (plus category/country/about/privacy/
   contact), each with its own `<title>` and `<meta name="description">`,
   canonical + OG/Twitter tags pointing at the `www.zaikaworlds.com` URL, a
   Recipe/CollectionPage JSON-LD block built from the same data
   `setRouteMeta()` uses, the recipe text (ingredients + steps), the recipe
   photo with absolute `/assets/…` URL, and a prominent link back to the
   SPA route. No `<base>` script, no SPA JS.
2. ✅ Staleness wired in via the Vercel build command, not a README step:
   `vercel.json` has `buildCommand: "python3 build_site.py"`, so every
   deploy (including a push from the daily new-recipe cron, which edits
   `index.html` directly) regenerates `data/` and the static pages from the
   current `index.html`. No extra manual step. The cron does NOT need to run
   the generator or commit the generated files — but if it does, the build
   regenerates them identically.
3. ✅ Deployed to a Vercel preview first and verified: (a) the static file
   wins over the rewrite for `/recipe/biryani`; (b) trailing-slash URLs
   serve the correct page and images load (absolute URLs); (c) `/`, `/about`,
   `/privacy`, `/contact` and SPA recipe routes still work; (d) the 404 view
   for `/recipe/<unknown>` still shows; (e) sitemap already lists the URLs,
   so no sitemap change was needed.
4. ✅ The performance follow-up (split `EXTRA_NEW` into lazy-loaded files)
   was done as part of this change, not separately: `EXTRA_NEW`, `EXTRA`,
   `RECIPES`, `UI`, `INFO`, `LANG_DATA` and `LANG_NEW_RAW/2/3` are all
   externalised into `data/*.js` with an async loader, and `index.html` is
   ~160 KB (was 3,144,085 bytes).

## Related performance state (2026-10-30, batch 2)

- 14 of 24 recipe JPGs converted to WebP (quality 82, same dimensions):
  total 4,680,240 → 2,229,116 bytes (−52% for those 14). The other 10 JPGs
  stay JPG because WebP at quality 82 was **larger** than the original
  (up to 203% for bouillabaisse) — only switch where WebP wins. Original
  JPGs are kept in `assets/` (feed.xml still references the JPG URLs, and
  they are the rollback path).
- Hero image now has `fetchpriority="high"` (LCP element).
- Not done: `srcset`/`sizes` responsive variants (no variant is generated
  anywhere today; the 1920×2560 hero and 1200×1800 recipe images are served
  full-size to phones and ~300 px cards) — biggest remaining image win,
  needs variant generation + template changes; no `Cache-Control` added for
  `index.html` itself (Vercel default must-revalidate is correct for a
  frequently-updated SPA; a long cache would risk stale content).

## SEO audit 2026-10-31 — 3 issues, FIXED (WhatsApp 429, thin hub links, empty anchors)

Audit (Ahrefs-style, discovered 31 Oct 2026 10:36). All three fixes live
in `build_site.py` + `index.html` (source); generated files are never
edited directly. `--check` enforces all three permanently (see below).

1. **"3 external links are broken" (WhatsApp share links, HTTP 429).**
   Verified by curl: a single wa.me share URL returns HTTP 302 (redirect
   to api.whatsapp.com/send/) with a browser UA, a crawler UA and no UA —
   the link works for real users; the 429 was WhatsApp burst
   rate-limiting of the audit crawler (64 of 67 requests succeeded), i.e.
   a crawler false positive. Fix (permanent, share button kept): the
   wa.me URL is NEVER a plain href anywhere now — it is built only on
   click. Static recipe pages: `<button class="share-btn"
   data-wa="<percent-encoded text>">Share on WhatsApp</button>` plus a
   `Copy recipe link` button (`data-copy`), with one delegated inline
   `<script>` (`SHARE_JS`, in `page_shell()`) that opens the URL on click
   (host split across a string concatenation so no literal share URL
   appears in the HTML for a crawler to extract). SPA: the `#waShare`
   anchor became a `<button>`, `render()` stores the text in `data-wa`
   instead of setting `href`, and the delegated document click handler
   opens it. The copy button also removes the old bare-URL self-link
   (`<a href="SELF">SELF</a>`), which audit tools flag as no/descriptive
   anchor text.
2. **"5 pages have only one incoming internal link"** (`/about`,
   `/contact`, `/faqs`, `/privacy`, `/trending`). Root cause: the five
   were linked only from the SPA homepage footer/nav. Fix: all five are
   now in `SITE_FOOTER` (every static page links them), recipe pages
   link `/faqs` + `/trending` in the "More" paragraph, and the three
   info pages cross-link each other + FAQs (`INFO_MORE`). Verified by
   in-memory crawl: about 478, contact 476, faqs 909, privacy 476,
   trending 903 incoming links (was ~1 each). Do NOT raise the general
   orphan threshold: language recipe pages legitimately sit at 2.
3. **"87 / 67 links have no anchor text" (recipe pages).** Exhaustive
   verification found ZERO empty `<a>` anchors anywhere (full 474-page
   in-memory scan, live curl, jsdom SPA renders in EN/RU/HI) — the flag
   did not reproduce. The two real defects that could plausibly cause it
   were still fixed: (a) the bare-URL self-link on every recipe page
   (removed by the Issue 1 button conversion — it was the ONLY self-link
   anchor on recipe pages, matching the audit rows' Page URL == Link
   URL pattern); (b) `r_text_lang()` returned an EMPTY alt for every
   recipe in all 12 non-English languages — it now
   falls back to the English alt. If the flag persists after a re-crawl
   it is the tool counting `<link>` (canonical/hreflang) elements,
   which cannot carry anchor text by design.

**`--check` guards added (fail the build on regression):** no literal
share URL in any generated page; no `alt=""`; every `<a>` must have
visible text, a non-empty img alt, or an aria-label (checked on all
static pages AND the slim homepage); each of the five hub pages must
have ≥10 incoming internal links.
