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
import filters  # noqa: E402
import dataset  # noqa: E402

CONTENT_REVIEWS = ROOT / "content" / "reviews"
OUT_REVIEWS = ROOT / "reviews"
OUT_BRANDS = ROOT / "brands"
TEMPLATES = ROOT / "templates"


def siblings_line(current) -> str:
    """Cross-links from one filtered ranking to the full ranking and the others."""
    others = [s for s in filters.PAGES if s["slug"] != current["slug"]]
    links = " ".join(
        f'<a href="{s["slug"]}.html">{s["h1"]}</a>.' for s in others
    )
    return (
        'The full ranking of everything I have scored: '
        '<a href="best-coconut-water.html">the best coconut water</a>. '
        f"Other cuts of the same scores: {links}"
    )


def site_config() -> dict:
    with open(ROOT / "content" / "site.toml", "rb") as fh:
        return tomllib.load(fh)


PUBLISH_FILES = [
    "index.html",
    "best-coconut-water.html",
    "404.html",
    "rating-guide.html",
    "about.html",
    "coconut-water.html",
    "style.css",
    "feed.xml",
    "sitemap.xml",
    "robots.txt",
    "CNAME",
    "coconut-water-data.html",
    "coconut-water-scores.csv",
] + [f"{spec['slug']}.html" for spec in filters.PAGES]


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

    (ROOT / "coconut-water.html").write_text(render.render_listing_page(reviews, filters.narrower_links()), encoding="utf-8")
    (ROOT / "best-coconut-water.html").write_text(
        render.render_best_page(reviews, site_config()["best_page_intro"], filters.narrower_links()), encoding="utf-8"
    )
    (ROOT / "rating-guide.html").write_text(
        (TEMPLATES / "rating-guide.html").read_text(encoding="utf-8"), encoding="utf-8"
    )
    (ROOT / "404.html").write_text(
        (TEMPLATES / "404.html").read_text(encoding="utf-8"), encoding="utf-8"
    )

    for spec in filters.PAGES:
        subset = filters.page_subset(spec, reviews)
        page = render.render_filtered_page(spec, subset, ranked, siblings_line(spec))
        (ROOT / f"{spec['slug']}.html").write_text(page, encoding="utf-8")

    (ROOT / "coconut-water-data.html").write_text(render.render_data_page(reviews), encoding="utf-8")
    (ROOT / "coconut-water-scores.csv").write_text(dataset.csv_text(reviews), encoding="utf-8")

    (ROOT / "feed.xml").write_text(render.render_feed(reviews), encoding="utf-8")
    (ROOT / "sitemap.xml").write_text(render.render_sitemap(reviews), encoding="utf-8")

    shutil.copy(TEMPLATES / "index.html", ROOT / "index.html")
    (ROOT / "about.html").write_text(render.render_about_page(), encoding="utf-8")
    shutil.copy(TEMPLATES / "style.css", ROOT / "style.css")

    tag = render.analytics_snippet(site_config().get("ga_measurement_id", ""))
    if tag:
        names = ["index.html", "about.html", "coconut-water.html", "best-coconut-water.html", "404.html", "coconut-water-data.html", "rating-guide.html"]
        names += [f"{spec['slug']}.html" for spec in filters.PAGES]
        pages = [ROOT / n for n in names]
        pages += sorted(OUT_REVIEWS.glob("*.html")) + sorted(OUT_BRANDS.glob("*.html"))
        for page in pages:
            html = page.read_text(encoding="utf-8")
            if "googletagmanager.com" in html:
                continue
            page.write_text(html.replace("</head>", tag + "</head>", 1), encoding="utf-8")
        print(f"analytics tag added to {len(pages)} pages")

    if out_dir is not None:
        stage(out_dir, reviews, brands)
        print(f"staged publishable files in {out_dir.name}/")

    print(f"built {len(reviews)} review pages + {len(brands)} brand pages + listing + feed + sitemap")
    return 0


if __name__ == "__main__":
    sys.exit(main())
