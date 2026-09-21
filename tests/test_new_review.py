"""Test tools/new_review.py intake parsing and file generation."""
import sys
import tempfile
import unittest
from pathlib import Path
from subprocess import run, PIPE
import os

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "build_lib"))

from reviews import ValidationError, load_review  # noqa: E402


HAPPY_PATH_INTAKE = """Brand: Test Brand
Product: Test Water
Date tasted: 2026-09-18
Size: 16.9 fl oz (500 mL)
Still or sparkling: Still
Pasteurized: yes
Added sugar: no
Organic: true
Fair trade: no
Pulp: false
Scores — Taste: 7  Sweetness: 5  Body: 6  Refreshment: 8  Ethics: 4  Overall: 6.5
One-line summary: A test review for a test product.
Notes: This is a test review with some notes about the product. It's quite good.

This is a second paragraph of notes.
Verdict: The verdict is that this is a fine test product. Would recommend testing.
"""

MISSING_REQUIRED_FIELD_INTAKE = """Brand: Missing Field
Product: Water
Date tasted: 2026-09-18
Size: 16.9 fl oz (500 mL)
Still or sparkling: Still
Pasteurized: no
Added sugar: no
Organic: false
Fair trade: false
Pulp: false
Scores — Taste: 5  Sweetness: 5  Body: 5  Refreshment: 5  Ethics: 5  Overall: 5
Notes: Missing one-line summary intentionally.
Verdict: Should fail.
"""

OUT_OF_RANGE_SCORE_INTAKE = """Brand: Bad Score
Product: Water
Date tasted: 2026-09-18
Size: 16.9 fl oz (500 mL)
Still or sparkling: Still
Pasteurized: no
Added sugar: no
Organic: false
Fair trade: false
Pulp: false
Scores — Taste: 11  Sweetness: 5  Body: 6  Refreshment: 8  Ethics: 4  Overall: 7
One-line summary: Out of range score.
Notes: Score out of range.
Verdict: Should fail.
"""

MULTILINE_NOTES_INTAKE = """Brand: Multi Brand
Product: Multi Water
Date tasted: 2026-09-18
Size: 16.9 fl oz (500 mL)
Still or sparkling: Sparkling
Pasteurized: true
Added sugar: true
Organic: false
Fair trade: false
Pulp: false
Scores — Taste: 6  Sweetness: 7  Body: 5  Refreshment: 7  Ethics: 2  Overall: 5.8
One-line summary: Multiple paragraphs test.
Notes: First paragraph of notes.

Second paragraph of notes.

Third paragraph with more details.
Verdict: First paragraph of verdict.

Second paragraph of verdict with final thoughts.
"""


class NewReviewTests(unittest.TestCase):
    """Test the new_review.py script using a temporary repository structure."""

    def setUp(self):
        """Set up a temporary directory tree that mimics the repo structure."""
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)
        
        # Create the directory structure the script expects
        self.content_dir = self.tmp_path / "content" / "reviews"
        self.content_dir.mkdir(parents=True)
        self.img_dir = self.tmp_path / "reviews" / "img"
        self.img_dir.mkdir(parents=True)
        self.build_lib_dir = self.tmp_path / "build_lib"
        self.build_lib_dir.mkdir(parents=True)
        
        # Copy build_lib files so they can be imported
        import shutil
        shutil.copy(ROOT / "build_lib" / "reviews.py", self.build_lib_dir / "reviews.py")
        
        # Copy the tools/new_review.py with ROOT patched to temp dir
        script_content = (ROOT / "tools" / "new_review.py").read_text(encoding="utf-8")
        script_content = script_content.replace(
            'ROOT = Path(__file__).resolve().parent.parent',
            f'ROOT = Path(r"{self.tmp_path}")'
        )
        self.temp_script = self.tmp_path / "new_review.py"
        self.temp_script.write_text(script_content, encoding="utf-8")

    def tearDown(self):
        """Clean up temporary directory."""
        self.tmp.cleanup()

    def run_new_review(self, intake_text, slug=None, extra_args=None):
        """Run tools/new_review.py with given intake text.
        
        Returns (exit_code, stdout, stderr).
        """
        intake_file = self.tmp_path / "intake.txt"
        intake_file.write_text(intake_text, encoding="utf-8")

        cmd = [sys.executable, str(self.temp_script), str(intake_file)]
        if slug:
            cmd.extend(["--slug", slug])
        if extra_args:
            cmd.extend(extra_args)

        env = os.environ.copy()
        env['PYTHONPATH'] = str(self.tmp_path)
        result = run(cmd, stdout=PIPE, stderr=PIPE, text=True, cwd=str(self.tmp_path), env=env)
        return result.returncode, result.stdout, result.stderr

    def test_happy_path_creates_valid_file(self):
        """Test that a valid intake produces a file that loads correctly."""
        exit_code, stdout, stderr = self.run_new_review(HAPPY_PATH_INTAKE, slug="test-brand-water")
        self.assertEqual(exit_code, 0, f"Script failed: {stderr}")
        self.assertIn("Review written to", stdout)

        # Check that file exists and can be loaded
        review_file = self.content_dir / "test-brand-water.md"
        self.assertTrue(review_file.exists(), "Review file was not created")

        # Should load without errors
        review = load_review(review_file)
        self.assertEqual(review.brand, "Test Brand")
        self.assertEqual(review.product, "Test Water")
        self.assertEqual(review.scores["taste"], 7.0)
        self.assertEqual(review.scores["overall"], 6.5)
        self.assertIn("test review with some notes", review.notes.lower())
        self.assertIn("second paragraph", review.notes.lower())

    def test_missing_required_field_fails(self):
        """Test that missing required field (one-line summary) causes failure."""
        exit_code, stdout, stderr = self.run_new_review(MISSING_REQUIRED_FIELD_INTAKE, slug="missing-field")
        self.assertNotEqual(exit_code, 0, "Script should have failed")
        # File should have been cleaned up
        review_file = self.content_dir / "missing-field.md"
        self.assertFalse(review_file.exists(), "Failed review file should have been cleaned up")

    def test_out_of_range_score_fails(self):
        """Test that out-of-range score causes failure."""
        exit_code, stdout, stderr = self.run_new_review(OUT_OF_RANGE_SCORE_INTAKE, slug="bad-score")
        self.assertNotEqual(exit_code, 0, "Script should have failed")
        self.assertIn("out of range", stderr)
        # File should have been cleaned up
        review_file = self.content_dir / "bad-score.md"
        self.assertFalse(review_file.exists(), "Failed review file should have been cleaned up")

    def test_multiline_notes_and_verdict(self):
        """Test that multi-paragraph Notes and Verdict are preserved."""
        exit_code, stdout, stderr = self.run_new_review(MULTILINE_NOTES_INTAKE, slug="multi-brand-water")
        self.assertEqual(exit_code, 0, f"Script failed: {stderr}")

        review_file = self.content_dir / "multi-brand-water.md"
        review = load_review(review_file)
        
        # Notes should have all three paragraphs
        self.assertIn("First paragraph", review.notes)
        self.assertIn("Second paragraph", review.notes)
        self.assertIn("Third paragraph", review.notes)
        
        # Verdict should have both paragraphs
        self.assertIn("First paragraph", review.verdict)
        self.assertIn("Second paragraph", review.verdict)
        self.assertIn("final thoughts", review.verdict)

    def test_file_overwrite_without_force_fails(self):
        """Test that script refuses to overwrite without --force."""
        # Create the file first
        review_file = self.content_dir / "test-brand-water.md"
        review_file.write_text("existing content", encoding="utf-8")

        exit_code, stdout, stderr = self.run_new_review(HAPPY_PATH_INTAKE, slug="test-brand-water")
        self.assertNotEqual(exit_code, 0, "Script should have failed")
        self.assertIn("already exists", stderr)

    def test_force_flag_allows_overwrite(self):
        """Test that --force allows overwriting existing file."""
        # Create the file first
        review_file = self.content_dir / "test-brand-water.md"
        review_file.write_text("old content", encoding="utf-8")

        exit_code, stdout, stderr = self.run_new_review(
            HAPPY_PATH_INTAKE,
            slug="test-brand-water",
            extra_args=["--force"]
        )
        self.assertEqual(exit_code, 0, f"Script failed: {stderr}")
        
        # File should be updated
        review = load_review(review_file)
        self.assertEqual(review.brand, "Test Brand")

    def test_slug_derivation(self):
        """Test that slug is correctly derived from brand and product."""
        exit_code, stdout, stderr = self.run_new_review(HAPPY_PATH_INTAKE)
        self.assertEqual(exit_code, 0)
        # Should derive slug as "test-brand-test-water"
        review_file = self.content_dir / "test-brand-test-water.md"
        self.assertTrue(review_file.exists(), "Review file with derived slug not created")

    def test_bool_field_normalization(self):
        """Test that yes/no/true/false/y/n are normalized to booleans."""
        intake = """Brand: Bool Test
Product: Water
Date tasted: 2026-09-18
Size: 16.9 fl oz (500 mL)
Still or sparkling: Still
Pasteurized: YES
Added sugar: no
Organic: True
Fair trade: N
Pulp: false
Scores — Taste: 5  Sweetness: 5  Body: 5  Refreshment: 5  Ethics: 5  Overall: 5
One-line summary: Boolean test.
Notes: Test.
Verdict: Test.
"""
        exit_code, stdout, stderr = self.run_new_review(intake, slug="bool-test")
        self.assertEqual(exit_code, 0, f"Script failed: {stderr}")

        review_file = self.content_dir / "bool-test.md"
        review = load_review(review_file)
        self.assertTrue(review.pasteurized)
        self.assertFalse(review.added_sugar)
        self.assertTrue(review.organic)
        self.assertFalse(review.fair_trade)
        self.assertFalse(review.pulp)


if __name__ == "__main__":
    unittest.main()
