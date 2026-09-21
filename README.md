# natewooding.com

Source for [natewooding.com](https://natewooding.com): 30+ hand-tasted
coconut water reviews, a comparison table, an RSS feed, and a sitemap,
generated from plain data files by a small Python static-site generator.

To add a new review, see [PUBLISHING.md](PUBLISHING.md) — no HTML editing
required.

## Layout

- `content/reviews/*.md` — one file per review: TOML front matter (brand,
  scores, tags, image, etc.) plus `## Notes` / `## Verdict` body text.
  This is the only thing you normally edit.
- `content/reviews/_template.md` — copy this to start a new review.
- `content/site.toml` — site-wide settings. `ga_measurement_id` holds the
  Google Analytics 4 ID (e.g. `G-ABC1234XYZ`); leave it empty and the site
  ships with no analytics at all. When set, `build.py` injects one async
  gtag snippet into the `<head>` of every generated page. Clearing the value
  removes tracking everywhere on the next build. Invalid IDs fail the build
  rather than emitting a broken tag.
- `content/site.toml` — site-wide settings (currently informational).
- `build_lib/reviews.py` — loads and validates `content/reviews/*.md`.
- `build_lib/render.py` — turns validated review data into HTML/XML using
  the templates below.
- `templates/` — the HTML/XML templates (`string.Template`, `$name`
  placeholders — no Jinja, no build step, no dependencies).
- `build.py` — the generator entry point. Reads `content/`, writes:
  - `reviews/<slug>.html` — one page per review
  - `coconut-water.html` — the listing + tag filters + comparison table
  - `best-coconut-water.html` — every review ranked by overall score
  - `brands/<brand>.html` — one page per brand with more than one review,
    generated automatically from the `brand` field. A brand appears here as
    soon as it has a second review, and disappears if it drops back to one;
    there is nothing to maintain by hand. Reviews of those brands get a link
    to their brand page, and `coconut-water.html` lists them under "By Brand".
    Note that brands are grouped on the exact `brand` string, so
    `Zico` and `Zico Pure` currently count as two different brands.
  - `feed.xml` — RSS, newest first
  - `sitemap.xml`
  - `index.html`, `about.html`, `style.css` — copied from `templates/`
- `tools/new_review.py` — converts a plain-text intake block (email format)
  into a review data file. Validates the result and refuses to overwrite
  existing files. See "If you email the review to Woody" in PUBLISHING.md.
- `tools/check_site.py` — checks the built site for broken local links,
  pages without exactly one `<h1>`, and missing or thin titles and meta
  descriptions. Runs in the deploy workflow, so a regression fails the build.
- `tools/extract_legacy.py` — one-off script used to migrate the original
  hand-written HTML into `content/reviews/*.md`. Kept for reference; you
  should not need to run it again.
- `tools/compare_legacy.py` — diffs generated pages against the last
  hand-written versions, ignoring whitespace differences. Used while
  building the generator; see `tools/VERIFICATION.md` for the results.
- `tests/` — unit tests: `test_reviews.py` (data loading/validation),
  `test_new_review.py` (email intake), `test_about.py` (age line) and
  `test_brands.py` (brand grouping, slugs and cross-links).

## Build locally

Requires Python 3.11+ (standard library only, nothing to `pip install`).

```
python3 build.py
```

This validates every file in `content/reviews/`, exits non-zero with a
clear error if something is wrong (missing field, out-of-range score,
missing image, duplicate slug/order), and otherwise rewrites the site's
HTML/XML files in place.

Run the tests with:

```
python3 -m unittest discover -s tests
```

## Deploy

Deployment is automatic: `.github/workflows/deploy.yml` runs on every push
to `main`. It runs `python3 build.py`, runs the unit tests, and — if both
succeed — publishes the site to GitHub Pages via
`actions/upload-pages-artifact` + `actions/deploy-pages`.

The workflow builds with `python3 build.py --out _site`, which stages only
the publishable files (pages, `style.css`, `feed.xml`, `sitemap.xml`,
`robots.txt`, `CNAME`, `reviews/img/`) into `_site/` and deploys that, so
the generator, templates and content sources are not served publicly.
`_site/` is gitignored; it is also handy for previewing the real site
locally: `python3 build.py --out _site && (cd _site && python3 -m http.server 8099)`.

There is no separate "commit the build output" step: the workflow builds
and deploys directly, so the files on GitHub Pages always match the
current `content/reviews/*.md`. You can also build and commit locally if
you want the generated HTML in git for diffing (this repo keeps the
generated files committed for that reason).

## Filtered ranking pages

`build_lib/filters.py` defines one spec per filtered ranking (slug, h1, meta
description, predicate, intro builder). `build.py` renders each with
`render.render_filtered_page` into `<slug>.html` using `templates/filtered-rank.html`
and the shared `rank_row.html`.

Current pages: best-organic-coconut-water, coconut-water-no-added-sugar,
unpasteurized-coconut-water. They regenerate from the `organic`, `added_sugar`
and `pasteurized` fields, so a new review joins the right rankings automatically.

To add one: append a spec to `PAGES`, add the filename to `PUBLISH_FILES` in
build.py, and add a `<url>` line to `templates/sitemap.xml`. Intro text must be
generated from Nate's own scores and flags only — never written tasting language.
