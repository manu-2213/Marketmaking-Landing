import unittest
from pathlib import Path

from event_config import EVENT_CONFIG


class EventConfigTests(unittest.TestCase):
    def test_2026_event_details_are_centralized(self):
        self.assertEqual(EVENT_CONFIG["title"], "AI Market-Making Hackathon 2026")
        self.assertEqual(EVENT_CONFIG["opening_date"], "19 November 2026")
        self.assertEqual(EVENT_CONFIG["competition_date"], "26 November 2026")
        self.assertIn("In person", EVENT_CONFIG["venue"])
        self.assertEqual(EVENT_CONFIG["team_size"], "2–4 participants")

    def test_event_is_not_opened_with_old_persistence(self):
        self.assertFalse(EVENT_CONFIG["registration_open"])
        self.assertEqual(
            EVENT_CONFIG["registration_spreadsheet_secret"],
            "spreadsheet_id_2026",
        )
        self.assertEqual(
            (EVENT_CONFIG["round_count_min"], EVENT_CONFIG["round_count_max"]),
            (9, 10),
        )

    def test_active_landing_content_has_no_old_event_promises(self):
        active_files = (
            Path(__file__).parents[1] / "landing.py",
            Path(__file__).parents[1] / "event_sections.py",
        )
        active_content = "\n".join(
            path.read_text(encoding="utf-8") for path in active_files
        )
        for stale_text in ("2025", "£300", "Alpha Traders", "MAR 25", "APR 1"):
            with self.subTest(stale_text=stale_text):
                self.assertNotIn(stale_text, active_content)


if __name__ == "__main__":
    unittest.main()
