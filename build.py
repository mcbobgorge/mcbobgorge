#!/usr/bin/env python3
"""Build the static site from content/reviews/*.md into the repo tree.

Run: python3 build.py
Reads content/reviews/*.md, writes reviews/<slug>.html, coconut-water.html,
feed.xml, sitemap.xml, and copies templates/index.html, about.html, style.css.
Exits non-zero with a clear message if validation fails.
"""
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "build_lib"))

from reviews import ValidationError, load_all  # noqa: E402
import render  # noqa: E402

CONTENT_REVIEWS = ROOT / "content" / "reviews"
OUT_REVIEWS = ROOT / "reviews"
TEMPLATES = ROOT / "templates"


def main() -> int:
    try:
        reviews = load_all(CONTENT_REVIEWS)
    except ValidationError as e:
        print(f"build failed: {e}", file=sys.stderr)
        return 1

    for r in reviews:
        out_path = OUT_REVIEWS / f"{r.slug}.html"
        out_path.write_text(render.render_review_page(r), encoding="utf-8")

    (ROOT / "coconut-water.html").write_text(render.render_listing_page(reviews), encoding="utf-8")
    (ROOT / "feed.xml").write_text(render.render_feed(reviews), encoding="utf-8")
    (ROOT / "sitemap.xml").write_text(render.render_sitemap(reviews), encoding="utf-8")

    shutil.copy(TEMPLATES / "index.html", ROOT / "index.html")
    shutil.copy(TEMPLATES / "about.html", ROOT / "about.html")
    shutil.copy(TEMPLATES / "style.css", ROOT / "style.css")

    print(f"built {len(reviews)} review pages + listing + feed + sitemap")
    return 0


if __name__ == "__main__":
    sys.exit(main())
