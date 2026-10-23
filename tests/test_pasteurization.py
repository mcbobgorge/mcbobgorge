"""Unknown pasteurization must not be classified as yes or no."""
import csv
import io
import sys
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "build_lib"))
import dataset
import filters
import render
from reviews import load_all
sys.path.insert(0, str(ROOT / "tools"))
from new_review import generate_review_content, parse_intake
from test_new_review import HAPPY_PATH_INTAKE


class PasteurizationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.review = load_all(ROOT / "content/reviews")[0]

    def test_unknown_display_and_categories(self):
        r = replace(self.review, pasteurized=None)
        self.assertIn("Pasteurization unknown", render.meta_line(r))
        self.assertIn("Pasteurization unknown", render.listing_meta_line(r))
        self.assertIn('<td class="tc">Unknown</td>', render.render_table_row(r))
        self.assertNotIn("pasteurized", render.tags_attr(r).split())
        spec = next(s for s in filters.PAGES if s["slug"] == "unpasteurized-coconut-water")
        self.assertEqual(filters.page_subset(spec, [r]), [])

    def test_csv_distinguishes_known_and_unknown(self):
        for flag, expected in [(True, "yes"), (False, "no"), (None, "")]:
            with self.subTest(flag=flag):
                r = replace(self.review, pasteurized=flag)
                row = next(csv.DictReader(io.StringIO(dataset.csv_text([r]))))
                self.assertEqual(row["pasteurized"], expected)

    def test_known_display_is_unchanged(self):
        for flag, label, cell in [(True, "Pasteurized", "Yes"), (False, "Unpasteurized", "No")]:
            with self.subTest(flag=flag):
                r = replace(self.review, pasteurized=flag)
                self.assertIn(label, render.meta_line(r))
                self.assertIn(label, render.listing_meta_line(r))
                self.assertIn(f'<td class="tc">{cell}</td>', render.render_table_row(r))

    def test_intake_unknown_or_omitted_omits_field(self):
        for line in ["Pasteurized: unknown\n", ""]:
            with self.subTest(line=line):
                data = parse_intake(HAPPY_PATH_INTAKE.replace("Pasteurized: yes\n", line))
                content = generate_review_content(data, "test", "Test", "Test")
                self.assertNotIn("pasteurized =", content)

    def test_intake_known_yes_no_preserves_boolean(self):
        for value, expected in [("yes", "true"), ("no", "false")]:
            with self.subTest(value=value):
                data = parse_intake(HAPPY_PATH_INTAKE.replace("Pasteurized: yes", f"Pasteurized: {value}"))
                content = generate_review_content(data, "test", "Test", "Test")
                self.assertIn(f"pasteurized = {expected}\n", content)
