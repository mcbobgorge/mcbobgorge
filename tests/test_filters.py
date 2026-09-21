"""Filtered ranking pages must agree with the review data, always."""

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "build_lib"))

import filters  # noqa: E402
from reviews import load_all  # noqa: E402


class FilteredSubsetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reviews = load_all(ROOT / "content" / "reviews")

    def test_every_page_has_a_predicate_that_matches_something(self):
        for spec in filters.PAGES:
            subset = filters.page_subset(spec, self.reviews)
            self.assertTrue(subset, f"{spec['slug']} would render an empty ranking")

    def test_subsets_are_sorted_best_first(self):
        for spec in filters.PAGES:
            subset = filters.page_subset(spec, self.reviews)
            scores = [r.scores["overall"] for r in subset]
            self.assertEqual(scores, sorted(scores, reverse=True), spec["slug"])

    def test_organic_page_holds_only_organic_reviews(self):
        spec = next(s for s in filters.PAGES if s["slug"] == "best-organic-coconut-water")
        subset = filters.page_subset(spec, self.reviews)
        self.assertTrue(all(r.organic for r in subset))

    def test_no_added_sugar_page_holds_only_unsweetened_reviews(self):
        spec = next(s for s in filters.PAGES if s["slug"] == "coconut-water-no-added-sugar")
        subset = filters.page_subset(spec, self.reviews)
        self.assertTrue(all(not r.added_sugar for r in subset))

    def test_unpasteurized_page_holds_only_unpasteurized_reviews(self):
        spec = next(s for s in filters.PAGES if s["slug"] == "unpasteurized-coconut-water")
        subset = filters.page_subset(spec, self.reviews)
        self.assertTrue(all(not r.pasteurized for r in subset))

    def test_intro_counts_match_the_data(self):
        """The leading number in each intro is generated, never typed by hand."""
        ranked = sorted(self.reviews, key=lambda r: -r.scores["overall"])
        for spec in filters.PAGES:
            subset = filters.page_subset(spec, self.reviews)
            intro = spec["intro"](subset, ranked)
            self.assertTrue(
                intro.startswith(f"{len(subset)} of the {len(ranked)} "),
                f"{spec['slug']} intro disagrees with its own row count: {intro[:60]}",
            )


class FilteredPageOutputTest(unittest.TestCase):
    """Runs against the in-tree HTML that build.py generates."""

    @classmethod
    def setUpClass(cls):
        cls.reviews = load_all(ROOT / "content" / "reviews")

    def test_row_count_matches_structured_data_count(self):
        for spec in filters.PAGES:
            path = ROOT / f"{spec['slug']}.html"
            if not path.exists():
                self.skipTest(f"{path.name} not built yet")
            html = path.read_text(encoding="utf-8")
            rows = len(re.findall(r"<tr><td>\d+</td>", html))
            declared = int(re.search(r'numberOfItems": (\d+)', html).group(1))
            expected = len(filters.page_subset(spec, self.reviews))
            self.assertEqual(rows, expected, spec["slug"])
            self.assertEqual(declared, expected, spec["slug"])

    def test_pages_are_in_the_sitemap(self):
        sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
        for spec in filters.PAGES:
            self.assertIn(f"/{spec['slug']}.html", sitemap, spec["slug"])


if __name__ == "__main__":
    unittest.main()
