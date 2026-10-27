"""Account-backed registrations using the original Google spreadsheet."""

import gspread
import streamlit as st
from google.auth.exceptions import GoogleAuthError
from google.oauth2.service_account import Credentials
from requests.exceptions import RequestException

from registration_store import REGISTRATION_HEADERS


class RegistrationStorageError(RuntimeError):
    """Storage is unavailable or its schema cannot be used safely."""


STORAGE_ERRORS = (
    RegistrationStorageError,
    PermissionError,
    gspread.exceptions.GSpreadException,
    GoogleAuthError,
    RequestException,
)


@st.cache_resource(ttl=300)
def get_registration_store():
    try:
        spreadsheet_id = st.secrets["sheets"]["spreadsheet_id"]
        account = dict(st.secrets["gcp_service_account"])
    except (KeyError, FileNotFoundError) as exc:
        raise RegistrationStorageError("Google Sheets is not configured.") from exc
    try:
        credentials = Credentials.from_service_account_info(
            account, scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
    except ValueError as exc:
        raise RegistrationStorageError("Google Sheets credentials are invalid.") from exc
    client = gspread.authorize(credentials)
    client.set_timeout(20)
    return SheetsRegistrationStore(client.open_by_key(spreadsheet_id).sheet1)


class SheetsRegistrationStore:
    """Expose current-event rows without modifying or displaying legacy records."""

    def __init__(self, worksheet, event_id="qmml-2026-november"):
        self.worksheet = worksheet
        self.event_id = event_id

    def _read(self):
        rows = self.worksheet.get_all_values()
        if not rows:
            return [], []
        header = rows[0]
        if len(set(header)) != len(header) or any(not name for name in header):
            raise RegistrationStorageError("Registration columns need administrator review.")
        if not {"email", "name", "team_name"}.issubset(header):
            raise RegistrationStorageError("Unexpected registration worksheet schema.")
        return header, rows[1:]

    def _current_rows(self, header, rows):
        if "event_id" not in header:
            return []
        index = header.index("event_id")
        return [
            (number, dict(zip(header, row)))
            for number, row in enumerate(rows, start=2)
            if len(row) > index and row[index] == self.event_id
        ]

    def get_all_values(self):
        header, rows = self._read()
        return [list(REGISTRATION_HEADERS)] + [
            [record.get(name, "") for name in REGISTRATION_HEADERS]
            for _, record in self._current_rows(header, rows)
        ]

    def append_row(self, values):
        if len(values) != len(REGISTRATION_HEADERS):
            raise RegistrationStorageError("Unexpected registration field count.")
        header, _ = self._read()
        required = (*REGISTRATION_HEADERS, "event_id", "looking_for_team")
        extended = header + [name for name in required if name not in header]
        if extended != header:
            # Only extend the header; historical rows and their order remain intact.
            if self.worksheet.col_count < len(extended):
                self.worksheet.add_cols(len(extended) - self.worksheet.col_count)
            self.worksheet.update(
                range_name="A1", values=[extended], value_input_option="RAW"
            )
        record = dict(zip(REGISTRATION_HEADERS, values))
        record["event_id"] = self.event_id
        record["looking_for_team"] = (
            "yes" if record["team_size"] == "1 (looking for a team)" else "no"
        )
        self.worksheet.append_row(
            [record.get(name, "") for name in extended], value_input_option="RAW"
        )

    def update_cell(self, row_number, column_number, value):
        header, rows = self._read()
        current = self._current_rows(header, rows)
        if not 2 <= row_number <= len(current) + 1:
            raise RegistrationStorageError("Registration no longer exists. Reload the page.")
        if not 1 <= column_number <= len(REGISTRATION_HEADERS):
            raise RegistrationStorageError("Unexpected registration column.")
        field = REGISTRATION_HEADERS[column_number - 1]
        if field not in header:
            raise RegistrationStorageError("Registration column is missing.")
        actual_row = current[row_number - 2][0]
        self.worksheet.update(
            range_name=gspread.utils.rowcol_to_a1(actual_row, header.index(field) + 1),
            values=[[str(value)]],
            value_input_option="RAW",
        )
