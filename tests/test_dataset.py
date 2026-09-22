import csv
import io
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "build_lib"))

import dataset  # noqa: E402
from reviews import load_all  # noqa: E402


class DatasetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reviews = load_all(ROOT / "content" / "reviews")

    def test_csv_has_one_row_per_review_with_true_scores(self):
        rows = list(csv.DictReader(io.StringIO(dataset.csv_text(self.reviews))))
        self.assertEqual(len(rows), len(self.reviews))
        by_slug = {r.slug: r for r in self.reviews}
        for row in rows:
            self.assertEqual(float(row["overall"]), by_slug[row["slug"]].scores["overall"])

    def test_csv_never_carries_price_or_value(self):
        header = dataset.csv_text(self.reviews).splitlines()[0].lower()
        for banned in ("price", "cost", "value", "per_oz"):
            self.assertNotIn(banned, header)

    def test_correlations_are_valid_and_overall_has_none(self):
        for k, avg, lo, hi, corr in dataset.criterion_rows(self.reviews):
            self.assertLessEqual(lo, avg)
            self.assertLessEqual(avg, hi)
            if k == "overall":
                self.assertIsNone(corr)
            else:
                self.assertTrue(-1.0 <= corr <= 1.0)

    def test_origin_table_counts_only_recorded_origins(self):
        total = sum(n for _, n, _, _ in dataset.origin_rows(self.reviews))
        self.assertEqual(total, sum(1 for r in self.reviews if r.origin))


if __name__ == "__main__":
    unittest.main()
