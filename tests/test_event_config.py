import unittest
from pathlib import Path

from unittest.mock import patch

from event_config import EVENT_CONFIG
from event_sections import (
    MAKER_QUESTIONS,
    TRADER_QUESTIONS,
    _maker_quote_result,
    _quote_prices,
    _trade_credits,
)
from registration_store import CSVRegistrationStore, REGISTRATION_HEADERS
import components
import csv
import tempfile


class EventConfigTests(unittest.TestCase):
    def test_quote_prices_are_centered_on_the_estimate(self):
        self.assertEqual(_quote_prices(100, 4), (98, 102))
        self.assertEqual(_quote_prices(100, 0), (100, 100))

    def test_trader_trade_and_market_maker_pnl_are_zero_sum(self):
        buy_pnl = _trade_credits("Buy at ask", 95, 105, 110, 1)
        sell_pnl = _trade_credits("Sell at bid", 95, 105, 90, 1)
        self.assertEqual(buy_pnl, 4.5)
        self.assertEqual(sell_pnl, 5.6)

    def test_on_target_market_maker_makes_the_same_pnl_on_either_side(self):
        buy_pnl = _trade_credits("Buy at ask", 95, 105, 100, 2)
        sell_pnl = _trade_credits("Sell at bid", 95, 105, 100, 2)
        self.assertEqual(buy_pnl, -10.0)
        self.assertEqual(sell_pnl, buy_pnl)

    def test_market_maker_feedback_checks_inside_and_outside(self):
        self.assertEqual(_maker_quote_result(95, 105, 100), ("inside", 5))
        self.assertEqual(_maker_quote_result(95, 105, 110), ("above", 5))
        self.assertEqual(_maker_quote_result(95, 105, 90), ("below", 5))

    def test_both_question_banks_have_six_easy_to_hard_rounds(self):
        expected_difficulty = ["Easy", "Easy", "Medium", "Medium", "Hard", "Hard"]
        for bank in (TRADER_QUESTIONS, MAKER_QUESTIONS):
            self.assertEqual(len(bank), 6)
            self.assertEqual(
                [question["difficulty"] for question in bank], expected_difficulty
            )
            self.assertEqual(len({question["prompt"] for question in bank}), 6)
            for question in bank:
                self.assertLessEqual(question["estimate"], question["maximum"])

    def test_2026_event_details_are_centralized(self):
        self.assertEqual(EVENT_CONFIG["title"], "AI Market-Making Hackathon 2026")
        self.assertEqual(EVENT_CONFIG["opening_date"], "19 November 2026")
        self.assertEqual(EVENT_CONFIG["competition_date"], "26 November 2026")
        self.assertIn("In person", EVENT_CONFIG["venue"])
        self.assertEqual(EVENT_CONFIG["team_size"], "2–4 participants")

    def test_registration_is_open_and_no_longer_uses_local_csv(self):
        self.assertTrue(EVENT_CONFIG["registration_open"])
        self.assertNotIn("registration_csv", EVENT_CONFIG)
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
            with patch.object(
                components, "_get_registration_store",
                return_value=CSVRegistrationStore(path),
            ):
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

    def test_registration_stats_count_teams_and_people_without_double_counting(self):
        rows = [
            ["team_name", "team_size"],
            ["Market Makers", "3"],
            ["market makers", "1 (looking for a team)"],
            ["New Team", "1 (looking for a team)"],
            ["New Team", "1 (looking for a team)"],
            ["", "1 (looking for a team)"],
            ["", "4"],
            ["Solo interest", "1 (looking for a team)"],
        ]

        class InMemoryStore:
            def get_all_values(self):
                return rows

        with patch.object(
            components, "_get_registration_store", return_value=InMemoryStore()
        ):
            self.assertEqual(components.get_registration_stats(), (3, 11))

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
        for stale_text in ("£300", "Alpha Traders", "MAR 25", "APR 1"):
            with self.subTest(stale_text=stale_text):
                self.assertNotIn(stale_text, active_content)


if __name__ == "__main__":
    unittest.main()
