import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "build_lib"))

import render  # noqa: E402
from reviews import load_all  # noqa: E402

GUIDE = (ROOT / "templates" / "rating-guide.html").read_text(encoding="utf-8")


class RatingGuideTest(unittest.TestCase):
    def test_every_review_page_links_the_guide(self):
        reviews = load_all(ROOT / "content" / "reviews")
        for r in reviews:
            self.assertIn('href="../rating-guide.html"', render.render_review_page(r, reviews), r.slug)

    def test_guide_explains_all_six_scores(self):
        for name in ("Taste", "Sweetness", "Body", "Refreshment", "Ethics"):
            self.assertIn(f">{name}<", GUIDE)
        self.assertIn("it is not an average", GUIDE)

    def test_guide_is_in_the_sitemap(self):
        sitemap = (ROOT / "templates" / "sitemap.xml").read_text(encoding="utf-8")
        self.assertIn("https://natewooding.com/rating-guide.html", sitemap)


if __name__ == "__main__":
    unittest.main()
