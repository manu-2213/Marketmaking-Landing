import unittest
from pathlib import Path

from unittest.mock import patch

from event_config import EVENT_CONFIG
from registration_store import CSVRegistrationStore, REGISTRATION_HEADERS
import components
import csv
import tempfile


class EventConfigTests(unittest.TestCase):
    def test_2026_event_details_are_centralized(self):
        self.assertEqual(EVENT_CONFIG["title"], "AI Market-Making Hackathon 2026")
        self.assertEqual(EVENT_CONFIG["opening_date"], "19 November 2026")
        self.assertEqual(EVENT_CONFIG["competition_date"], "26 November 2026")
        self.assertIn("In person", EVENT_CONFIG["venue"])
        self.assertEqual(EVENT_CONFIG["team_size"], "2–4 participants")

    def test_registration_is_open_and_uses_a_private_csv(self):
        self.assertTrue(EVENT_CONFIG["registration_open"])
        self.assertEqual(
            Path(EVENT_CONFIG["registration_csv"]).name, "registrations.csv"
        )
        self.assertEqual(
            (EVENT_CONFIG["round_count_min"], EVENT_CONFIG["round_count_max"]),
            (9, 10),
        )

    def test_registration_csv_persists_team_hub_updates_and_student_id(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "registrations.csv"
            store = CSVRegistrationStore(path)
            store.append_row([
                "2026-10-27T12:00:00+00:00",
                "Test Student",
                "student@example.edu",
                "Example University",
                "Data Science",
                "",
                "1 (looking for a team)",
                "Intermediate",
                "",
                "",
                "",
                "QM123456",
            ])

            rows = store.get_all_values()
            self.assertEqual(rows[0], list(REGISTRATION_HEADERS))
            self.assertEqual(rows[1][rows[0].index("student_id")], "QM123456")
            self.assertEqual(rows[1][rows[0].index("email")], "student@example.edu")
            store.update_cell(2, rows[0].index("team_name") + 1, "Market Makers")

            with path.open(newline="", encoding="utf-8") as file:
                saved_rows = list(csv.DictReader(file))
            self.assertEqual(saved_rows[0]["team_name"], "Market Makers")
            self.assertEqual(saved_rows[0]["student_id"], "QM123456")

    def test_registration_helpers_share_csv_with_team_hub(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "registrations.csv"
            with patch.object(components, "_REGISTRATION_CSV", path):
                components._save_registration(
                    "Test Student",
                    "QM123456",
                    "student@example.edu",
                    "Example University",
                    "Data Science",
                    "",
                    "1 (looking for a team)",
                    "Intermediate",
                    "",
                )

                self.assertEqual(components.get_team_count(), 1)
                self.assertIsNotNone(components._verify_email("student@example.edu"))
                self.assertIsNotNone(components._verify_student_id("QM123456"))
                self.assertTrue(
                    components._update_team_name(
                        "student@example.edu", "Market Makers"
                    )
                )
                rows = CSVRegistrationStore(path).get_all_values()
                self.assertEqual(rows[1][5], "Market Makers")

    def test_legacy_registration_csv_is_extended_without_losing_rows(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "registrations.csv"
            path.write_text(
                "timestamp,name,email,university,degree,team_name,team_size,"
                "experience,interest,open_for_joining,open_spots\n"
                "old-row,Student,student@example.edu,University,,Team,2,"
                "Beginner,,,,\n",
                encoding="utf-8",
            )
            rows = CSVRegistrationStore(path).get_all_values()

            self.assertEqual(rows[1][1], "Student")
            self.assertEqual(rows[1][2], "student@example.edu")
            self.assertEqual(rows[1][rows[0].index("student_id")], "")

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
