import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "build_lib"))

import render  # noqa: E402
import stats  # noqa: E402
from reviews import load_all  # noqa: E402


class StatsPageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reviews = load_all(ROOT / "content" / "reviews")
        cls.page = render.render_stats_page(cls.reviews)

    def test_every_review_lands_in_exactly_one_histogram_bin(self):
        bins = stats.overall_bins(self.reviews)
        self.assertEqual(sum(len(b) for b in bins), len(self.reviews))

    def test_criterion_counts_cover_every_review(self):
        for k in stats.CRITERIA:
            self.assertEqual(sum(stats.criterion_counts(self.reviews, k)), len(self.reviews))

    def test_tag_groups_partition_the_reviews(self):
        for section, groups in stats.tag_groups(self.reviews):
            self.assertEqual(sum(len(items) for _, items in groups), len(self.reviews), section)

    def test_origin_groups_include_unrecorded(self):
        self.assertEqual(sum(len(items) for _, items in stats.origin_groups(self.reviews)), len(self.reviews))

    def test_correlation_matrix_is_symmetric(self):
        m = stats.correlation_matrix(self.reviews)
        for i in range(len(m)):
            for j in range(len(m)):
                self.assertAlmostEqual(m[i][j], m[j][i])

    def test_headline_uses_true_extremes(self):
        figures = dict(stats.headline(self.reviews))
        overall = [r.scores["overall"] for r in self.reviews]
        self.assertEqual(figures["Coconut waters scored"], str(len(self.reviews)))
        self.assertEqual(figures["Highest overall"], f"{max(overall):.1f}")
        self.assertEqual(figures["Lowest overall"], f"{min(overall):.1f}")

    def test_page_has_charts_and_no_prices_or_template_holes(self):
        self.assertIn("<svg", self.page)
        self.assertNotIn("$", self.page)
        for banned in ("price", "per oz", "cost"):
            self.assertNotIn(banned, self.page.lower())


if __name__ == "__main__":
    unittest.main()
