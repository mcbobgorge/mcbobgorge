import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "build_lib"))

from reviews import ValidationError, load_all, load_review  # noqa: E402

GOOD = """+++
brand = "TestBrand"
product = "Test Water"
listing_name = "TestBrand — Test"
table_name = "TestBrand Test"
order = 1
date = "2025-01-01"
size = "12 fl oz"
style = "Still"
pasteurized = true
added_sugar = false
organic = true
fair_trade = false
pulp = false
extra_tags = []
image = "reviews/img/PLACEHOLDER.jpg"
description = "A test review."
scores = { taste = 5, sweetness = 5, body = 5, refreshment = 5, ethics = 5, overall = 5 }
+++

## Notes

Some notes.

## Verdict

Some verdict.
"""


class ReviewLoadingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.content_dir = Path(self.tmp.name) / "content" / "reviews"
        self.content_dir.mkdir(parents=True)
        self.reviews_root = Path(self.tmp.name) / "reviews" / "img"
        self.reviews_root.mkdir(parents=True)
        (self.reviews_root / "PLACEHOLDER.jpg").write_bytes(b"x")

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, slug, text):
        p = self.content_dir / f"{slug}.md"
        p.write_text(text, encoding="utf-8")
        return p

    def test_loads_valid_review(self):
        p = self.write("test-water", GOOD)
        r = load_review(p)
        self.assertEqual(r.brand, "TestBrand")
        self.assertEqual(r.scores["overall"], 5)
        self.assertEqual(r.notes, "Some notes.")

    def test_missing_field_raises(self):
        bad = GOOD.replace('brand = "TestBrand"\n', "")
        p = self.write("bad", bad)
        with self.assertRaisesRegex(ValidationError, "brand"):
            load_review(p)

    def test_score_out_of_range_raises(self):
        bad = GOOD.replace("overall = 5", "overall = 15")
        p = self.write("bad-score", bad)
        with self.assertRaisesRegex(ValidationError, "out of range"):
            load_review(p)

    def test_missing_image_raises(self):
        bad = GOOD.replace("PLACEHOLDER.jpg", "does-not-exist.jpg")
        p = self.write("bad-image", bad)
        with self.assertRaisesRegex(ValidationError, "image"):
            load_review(p)

    def test_duplicate_slug_via_duplicate_order(self):
        self.write("first", GOOD)
        self.write("second", GOOD)  # same order=1 as "first"
        with self.assertRaisesRegex(ValidationError, "duplicate order"):
            load_all(self.content_dir)

    def test_load_all_sorts_by_order(self):
        self.write("first", GOOD)
        second = GOOD.replace("order = 1", "order = 2").replace(
            'listing_name = "TestBrand — Test"', 'listing_name = "TestBrand — Test 2"'
        )
        self.write("second", second)
        reviews = load_all(self.content_dir)
        self.assertEqual([r.order for r in reviews], [1, 2])


if __name__ == "__main__":
    unittest.main()


class OrderingTest(unittest.TestCase):
    def test_the_real_listing_is_newest_first(self):
        content = Path(__file__).resolve().parents[1] / "content" / "reviews"
        dates = [r.date for r in load_all(content)]
        self.assertEqual(dates, sorted(dates, reverse=True))
