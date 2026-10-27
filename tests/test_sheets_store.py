import unittest
from unittest.mock import Mock, patch

from streamlit.testing.v1 import AppTest

from registration_store import REGISTRATION_HEADERS
from sheets_store import RegistrationStorageError, SheetsRegistrationStore


def registration(email="student@example.edu", team="Test Team", size="2"):
    return [
        "2026-10-27", "Test Student", email, "Example University", "Computing",
        team, size, "Intermediate", "", "", "", "STUDENT-01",
    ]


class SheetsStoreTests(unittest.TestCase):
    def test_legacy_rows_are_not_shown_or_modified_during_read(self):
        worksheet = Mock()
        worksheet.get_all_values.return_value = [
            list(REGISTRATION_HEADERS[:-1]), registration()[:-1],
        ]
        store = SheetsRegistrationStore(worksheet)
        self.assertEqual(store.get_all_values(), [list(REGISTRATION_HEADERS)])
        worksheet.update.assert_not_called()
        worksheet.append_row.assert_not_called()

    def test_appending_preserves_existing_columns_and_uses_raw_values(self):
        worksheet = Mock(col_count=11)
        header = list(REGISTRATION_HEADERS[:-1]) + ["organiser_note"]
        worksheet.get_all_values.return_value = [header, registration()[:-1] + ["retain"]]
        store = SheetsRegistrationStore(worksheet)
        values = registration(team="=not_a_formula", size="1 (looking for a team)")
        store.append_row(values)
        extended = worksheet.update.call_args.kwargs["values"][0]
        self.assertEqual(extended[:len(header)], header)
        worksheet.update.assert_called_once()
        self.assertEqual(worksheet.update.call_args.kwargs["range_name"], "A1")
        saved = dict(zip(extended, worksheet.append_row.call_args.args[0]))
        self.assertEqual(saved["student_id"], "STUDENT-01")
        self.assertEqual(saved["team_name"], "=not_a_formula")
        self.assertEqual(saved["event_id"], "qmml-2026-november")
        self.assertEqual(saved["looking_for_team"], "yes")
        self.assertEqual(saved["organiser_note"], "")
        self.assertEqual(worksheet.append_row.call_args.kwargs["value_input_option"], "RAW")

    def test_update_maps_current_event_row_to_original_sheet_row(self):
        worksheet = Mock()
        header = list(REGISTRATION_HEADERS) + ["event_id"]
        worksheet.get_all_values.return_value = [
            header,
            registration() + [""],
            registration("new@example.edu") + ["qmml-2026-november"],
        ]
        store = SheetsRegistrationStore(worksheet)
        self.assertEqual(len(store.get_all_values()), 2)
        store.update_cell(2, 6, "New name")
        worksheet.update.assert_called_once_with(
            range_name="F3", values=[["New name"]], value_input_option="RAW"
        )

    def test_storage_errors_do_not_fall_back_to_csv(self):
        worksheet = Mock()
        worksheet.get_all_values.side_effect = RegistrationStorageError("Unavailable")
        with self.assertRaises(RegistrationStorageError):
            SheetsRegistrationStore(worksheet).append_row(registration())

    def test_unknown_schema_is_not_overwritten(self):
        worksheet = Mock()
        worksheet.get_all_values.return_value = [["unrelated", "data"]]
        with self.assertRaises(RegistrationStorageError):
            SheetsRegistrationStore(worksheet).append_row(registration())
        worksheet.update.assert_not_called()

    def test_original_spreadsheet_configuration_is_used(self):
        from sheets_store import get_registration_store

        get_registration_store.clear()
        client = Mock()
        with patch("sheets_store.st.secrets", {
            "sheets": {"spreadsheet_id": "original-account-sheet"},
            "gcp_service_account": {"test": "mock-credentials"},
        }), patch("sheets_store.Credentials.from_service_account_info"), patch(
            "sheets_store.gspread.authorize", return_value=client
        ):
            store = get_registration_store()
            client.open_by_key.assert_called_once_with("original-account-sheet")
            self.assertIs(store.worksheet, client.open_by_key.return_value.sheet1)
        get_registration_store.clear()


class RegistrationFormTests(unittest.TestCase):
    def app(self, store):
        self.mock_store = patch("components._get_registration_store", return_value=store)
        self.mock_store.start()
        self.addCleanup(self.mock_store.stop)
        return AppTest.from_string(
            "from components import render_registration\nrender_registration()"
        ).run()

    def fill(self, app, team_size="Looking for a team", team=""):
        for key, value in {
            "signup_name": "Test Student",
            "signup_email": "student@example.edu",
            "signup_id": "STUDENT-01",
            "signup_university": "Example University",
            "signup_team": team,
        }.items():
            app.text_input(key=key).set_value(value)
        app.selectbox(key="signup_team_size").select(team_size)
        return app

    def test_individual_registration_reaches_account_store(self):
        store = Mock()
        store.get_all_values.return_value = [list(REGISTRATION_HEADERS)]
        app = self.fill(self.app(store))
        app.button[0].click().run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.success), 1)
        saved = store.append_row.call_args.args[0]
        self.assertEqual(saved[2], "student@example.edu")
        self.assertEqual(saved[6], "1 (looking for a team)")
        self.assertEqual(saved[11], "STUDENT-01")

    def test_team_requires_name_and_retains_input_after_validation(self):
        store = Mock()
        store.get_all_values.return_value = [list(REGISTRATION_HEADERS)]
        app = self.fill(self.app(store), "Team of 3")
        app.button[0].click().run()
        self.assertIn("team name", app.warning[0].value)
        self.assertEqual(app.text_input(key="signup_name").value, "Test Student")
        store.append_row.assert_not_called()
        app.text_input(key="signup_team").set_value("Example Makers")
        app.button[0].click().run()
        self.assertEqual(len(app.success), 1)
        self.assertEqual(store.append_row.call_args.args[0][5:7], ["Example Makers", "3"])

    def test_failed_remote_write_is_not_reported_as_success(self):
        store = Mock()
        store.get_all_values.return_value = [list(REGISTRATION_HEADERS)]
        store.append_row.side_effect = RegistrationStorageError("private diagnostic")
        app = self.fill(self.app(store))
        app.button[0].click().run()
        self.assertEqual(len(app.success), 0)
        self.assertEqual(len(app.error), 1)
        self.assertNotIn("private diagnostic", app.error[0].value)
        self.assertEqual(app.text_input(key="signup_id").value, "STUDENT-01")

    def test_duplicate_email_does_not_append(self):
        store = Mock()
        store.get_all_values.return_value = [list(REGISTRATION_HEADERS), registration()]
        app = self.fill(self.app(store))
        app.button[0].click().run()
        self.assertIn("already registered", app.error[0].value)
        store.append_row.assert_not_called()

    def test_duplicate_student_id_does_not_append(self):
        store = Mock()
        store.get_all_values.return_value = [
            list(REGISTRATION_HEADERS), registration(email="other@example.edu"),
        ]
        app = self.fill(self.app(store))
        app.button[0].click().run()
        self.assertIn("student ID is already registered", app.error[0].value)
        store.append_row.assert_not_called()

    def test_invalid_email_keeps_form_data_without_contacting_storage(self):
        store = Mock()
        app = self.fill(self.app(store))
        app.text_input(key="signup_email").set_value("invalid")
        app.button[0].click().run()
        self.assertIn("valid student email", app.warning[0].value)
        self.assertEqual(app.text_input(key="signup_email").value, "invalid")
        store.get_all_values.assert_not_called()

    def test_landing_page_renders_without_storage_or_historical_records(self):
        from pathlib import Path

        with patch("components._get_registration_store") as store:
            store.return_value.get_all_values.side_effect = RegistrationStorageError(
                "Google Sheets is not configured."
            )
            app = AppTest.from_file(str(Path(__file__).parents[1] / "landing.py")).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.get("form")), 1)
        store.assert_called_once()
        self.assertIn(
            "Live registration counts are temporarily unavailable.",
            [caption.value for caption in app.caption],
        )


if __name__ == "__main__":
    unittest.main()
