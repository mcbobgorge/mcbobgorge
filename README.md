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
- `content/site.toml` — site-wide settings (currently informational).
- `build_lib/reviews.py` — loads and validates `content/reviews/*.md`.
- `build_lib/render.py` — turns validated review data into HTML/XML using
  the templates below.
- `templates/` — the HTML/XML templates (`string.Template`, `$name`
  placeholders — no Jinja, no build step, no dependencies).
- `build.py` — the generator entry point. Reads `content/`, writes:
  - `reviews/<slug>.html` — one page per review
  - `coconut-water.html` — the listing + tag filters + comparison table
  - `feed.xml` — RSS, newest first
  - `sitemap.xml`
  - `index.html`, `about.html`, `style.css` — copied from `templates/`
- `tools/extract_legacy.py` — one-off script used to migrate the original
  hand-written HTML into `content/reviews/*.md`. Kept for reference; you
  should not need to run it again.
- `tools/compare_legacy.py` — diffs generated pages against the last
  hand-written versions, ignoring whitespace differences. Used while
  building the generator; see `tools/VERIFICATION.md` for the results.
- `tests/test_reviews.py` — unit tests for the data loading/validation
  rules in `build_lib/reviews.py`.

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
succeed — publishes the repository (including the freshly built pages,
`CNAME`, and `robots.txt`) to GitHub Pages via
`actions/upload-pages-artifact` + `actions/deploy-pages`.

There is no separate "commit the build output" step: the workflow builds
and deploys directly, so the files on GitHub Pages always match the
current `content/reviews/*.md`. You can also build and commit locally if
you want the generated HTML in git for diffing (this repo keeps the
generated files committed for that reason).
