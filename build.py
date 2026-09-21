#!/usr/bin/env python3
"""Build the static site from content/reviews/*.md into the repo tree.

Run: python3 build.py
Reads content/reviews/*.md, writes reviews/<slug>.html, coconut-water.html,
feed.xml, sitemap.xml, and copies templates/index.html, about.html, style.css.
Exits non-zero with a clear message if validation fails.
"""
import shutil
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "build_lib"))

from reviews import ValidationError, load_all  # noqa: E402
import render  # noqa: E402

CONTENT_REVIEWS = ROOT / "content" / "reviews"
OUT_REVIEWS = ROOT / "reviews"
OUT_BRANDS = ROOT / "brands"
TEMPLATES = ROOT / "templates"


def site_config() -> dict:
    with open(ROOT / "content" / "site.toml", "rb") as fh:
        return tomllib.load(fh)


PUBLISH_FILES = [
    "index.html",
    "best-coconut-water.html",
    "about.html",
    "coconut-water.html",
    "style.css",
    "feed.xml",
    "sitemap.xml",
    "robots.txt",
    "CNAME",
]


def stage(out_dir: Path, reviews, brands) -> None:
    """Copy only the files the public site needs into out_dir (for deployment)."""
    if out_dir.exists():
        shutil.rmtree(out_dir)
    (out_dir / "reviews").mkdir(parents=True)
    (out_dir / "brands").mkdir(parents=True)
    for name in PUBLISH_FILES:
        src = ROOT / name
        if src.exists():
            shutil.copy(src, out_dir / name)
    # Loose images used by the top-level pages (e.g. wooding-pond.jpg)
    for pattern in ("*.jpg", "*.png", "*.ico", "*.svg"):
        for src in ROOT.glob(pattern):
            shutil.copy(src, out_dir / src.name)
    for r in reviews:
        shutil.copy(OUT_REVIEWS / f"{r.slug}.html", out_dir / "reviews" / f"{r.slug}.html")
    shutil.copytree(OUT_REVIEWS / "img", out_dir / "reviews" / "img")
    for brand in brands:
        name = f"{render.brand_slug(brand)}.html"
        shutil.copy(OUT_BRANDS / name, out_dir / "brands" / name)


def main() -> int:
    out_dir = None
    args = sys.argv[1:]
    if args[:1] == ["--out"] and len(args) == 2:
        out_dir = ROOT / args[1]
    elif args:
        print("usage: build.py [--out DIR]", file=sys.stderr)
        return 2
    try:
        reviews = load_all(CONTENT_REVIEWS)
    except ValidationError as e:
        print(f"build failed: {e}", file=sys.stderr)
        return 1

    ranked = render.by_score(reviews)
    brands = render.brands_with_multiple(reviews)
    for r in reviews:
        out_path = OUT_REVIEWS / f"{r.slug}.html"
        out_path.write_text(render.render_review_page(r, ranked, brands), encoding="utf-8")

    OUT_BRANDS.mkdir(exist_ok=True)
    for brand, items in brands.items():
        page = render.render_brand_page(brand, items, ranked, brands)
        (OUT_BRANDS / f"{render.brand_slug(brand)}.html").write_text(page, encoding="utf-8")

    (ROOT / "coconut-water.html").write_text(render.render_listing_page(reviews), encoding="utf-8")
    (ROOT / "best-coconut-water.html").write_text(
        render.render_best_page(reviews, site_config()["best_page_intro"]), encoding="utf-8"
    )
    (ROOT / "feed.xml").write_text(render.render_feed(reviews), encoding="utf-8")
    (ROOT / "sitemap.xml").write_text(render.render_sitemap(reviews), encoding="utf-8")

    shutil.copy(TEMPLATES / "index.html", ROOT / "index.html")
    (ROOT / "about.html").write_text(render.render_about_page(), encoding="utf-8")
    shutil.copy(TEMPLATES / "style.css", ROOT / "style.css")

    if out_dir is not None:
        stage(out_dir, reviews, brands)
        print(f"staged publishable files in {out_dir.name}/")

    print(f"built {len(reviews)} review pages + {len(brands)} brand pages + listing + feed + sitemap")
    return 0


if __name__ == "__main__":
    sys.exit(main())
