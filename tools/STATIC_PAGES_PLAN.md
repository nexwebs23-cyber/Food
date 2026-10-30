# Static per-recipe pages — plan (NOT DONE yet)

Status: **not implemented** in this run. The JS per-route SEO stopgap in
`index.html` (`setRouteMeta()` — title, canonical, OG/Twitter metas, Recipe
JSON-LD per route) stays in place and is the current live behaviour.

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

## Concrete plan (when this is picked up)

1. Add a stdlib-only Python generator in the same style as
   `tools/split_export.py`. It parses the data blocks out of `index.html`
   (`RECIPES` + `EXTRA`; English text only for v1) and emits thin SEO pages
   at `recipe/<slug>/index.html`, each with: its own `<title>` and
   `<meta name="description">`, canonical + OG/Twitter tags pointing at the
   `www.zaikaworlds.com` recipe URL (canonical domain changed to www on 2026-10-30 per user — the
   user chose on 2026-10-29 to leave the domain as is), a Recipe JSON-LD
   block built from the same data `setRouteMeta()` uses, the recipe text
   (ingredients + steps), the recipe photo with absolute `/assets/…` URL,
   and a prominent link back to the SPA route. No `<base>` script, no SPA JS.
2. Wire the generator into README step 5: run it after `split_export.py` on
   every export, so pages cannot go stale.
3. Deploy to a Vercel preview first and verify: (a) the static file wins
   over the rewrite for `/recipe/biryani`; (b) trailing-slash behaviour and
   that images load (absolute URLs); (c) `/`, `/about`, `/privacy`,
   `/contact` and SPA recipe routes still work; (d) the 404 view for
   `/recipe/<unknown>` still shows; (e) sitemap already lists the URLs, so
   no sitemap change is needed.
4. Only after static pages ship, consider the performance follow-up: split
   `EXTRA_NEW` (41% of the file) into lazy-loaded JSON fetched only when a
   non-English language is selected. That is the larger performance win and
   shares the same loader work — do it as its own change, not bundled with
   static pages.

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
