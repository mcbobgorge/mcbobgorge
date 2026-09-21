import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "build_lib"))

import render  # noqa: E402
from reviews import load_all  # noqa: E402


class FakeReview:
    def __init__(self, slug, brand, overall):
        self.slug = slug
        self.brand = brand
        self.table_name = slug
        self.listing_name = slug
        self.description = ""
        self.scores = {"overall": overall}


class BrandSlugTest(unittest.TestCase):
    def test_apostrophes_and_ampersands(self):
        self.assertEqual(render.brand_slug("Trader Joe's"), "trader-joes")
        self.assertEqual(render.brand_slug("Maui & Sons"), "maui-and-sons")
        self.assertEqual(render.brand_slug("Vita Coco"), "vita-coco")


class GroupingTest(unittest.TestCase):
    def test_only_brands_with_more_than_one_review(self):
        rs = [
            FakeReview("a", "Goya", 4.7),
            FakeReview("b", "Goya", 4.6),
            FakeReview("c", "Parrot", 3.1),
        ]
        brands = render.brands_with_multiple(rs)
        self.assertEqual(list(brands), ["Goya"])

    def test_items_are_best_first(self):
        rs = [FakeReview("a", "Goya", 4.4), FakeReview("b", "Goya", 4.7)]
        self.assertEqual([r.slug for r in render.brands_with_multiple(rs)["Goya"]], ["b", "a"])


class RealSiteTest(unittest.TestCase):
    def setUp(self):
        self.reviews = load_all(ROOT / "content" / "reviews")

    def test_every_brand_page_slug_is_unique(self):
        brands = render.brands_with_multiple(self.reviews)
        slugs = [render.brand_slug(b) for b in brands]
        self.assertEqual(len(slugs), len(set(slugs)))

    def test_review_of_single_review_brand_gets_no_brand_line(self):
        brands = render.brands_with_multiple(self.reviews)
        solo = next(r for r in self.reviews if r.brand not in brands)
        self.assertEqual(render.brand_line(solo, brands), "")

    def test_review_of_repeated_brand_links_to_its_brand_page(self):
        brands = render.brands_with_multiple(self.reviews)
        r = next(r for r in self.reviews if r.brand in brands)
        line = render.brand_line(r, brands)
        self.assertIn(f"../brands/{render.brand_slug(r.brand)}.html", line)

    def test_brand_intro_states_the_real_count_and_best_score(self):
        brands = render.brands_with_multiple(self.reviews)
        ranked = render.by_score(self.reviews)
        items = brands["Vita Coco"]
        intro = render.brand_intro("Vita Coco", items, ranked)
        self.assertIn(f"scored {len(items)} Vita Coco", intro)
        self.assertIn(render.fmt_overall(items[0].scores["overall"]), intro)


if __name__ == "__main__":
    unittest.main()
