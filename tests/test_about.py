import datetime
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build_lib"))
import render


class AgeTest(unittest.TestCase):
    def test_counts_up_on_the_birthday(self):
        cases = {
            datetime.date(2026, 10, 1): 26,
            datetime.date(2026, 10, 2): 27,
            datetime.date(2027, 1, 1): 27,
            datetime.date(1999, 10, 2): 0,
        }
        for day, expected in cases.items():
            self.assertEqual(render.age_today(day), expected, day)

    def test_about_page_states_the_age(self):
        self.assertIn(f'id="age">{render.age_today()}<', render.render_about_page())


if __name__ == "__main__":
    unittest.main()
