# QMML AI Market-Making Hackathon 2026

Streamlit event site, registration and Team Hub. The competition engine and its
trading/submission storage live outside this repository.

## Run

```sh
python -m pip install -r requirements.txt
streamlit run landing.py
```

Event information and registration status are in [event_config.py](event_config.py).
The public page renders without credentials; submitting registrations and using
the Team Hub require the Google Sheets configuration below.

## Registrations: back in the original Google account

The website writes to **the first worksheet of the original Google spreadsheet**,
using the original `sheets.spreadsheet_id` and `gcp_service_account` settings.
Configure these in local `.streamlit/secrets.toml` or the deployment's Streamlit
secrets. See [.streamlit/secrets.toml.example](.streamlit/secrets.toml.example).
Share the spreadsheet with the service-account email as an editor.

**This is Google Sheets, not a local CSV.** In your Google account, open the sheet
and use **File → Download → Comma-separated values (.csv)** to get the registrations.
This exports the worksheet, including historical records. For a current-event-only
export, copy rows with `event_id = qmml-2026-november` into a separate tab and download
that tab; do not assume hiding/filtering rows excludes them from CSV exports.
Do not publish the spreadsheet or a participant export.

- New records include name, student email (`email`), student ID (`student_id`),
  university, degree, team name/size, ML experience and an optional note.
- `looking_for_team` is explicitly stored; the Team Hub also uses the existing
  `team_size`, `open_for_joining` and `open_spots` fields.
- The first successful registration adds any missing columns to the header,
  including `student_id`, `event_id` and `looking_for_team`. Existing rows, columns
  and their order are preserved. User values are stored as RAW values, not formulas.
- Historical entries without this event ID remain in your account but are not
  shown on the current Team Hub or used for current-event duplicate checks.
- Nothing is deleted or reset. Do not tag earlier participants as current entries
  unless you deliberately want to enrol them in the November event.
- No local CSV fallback is used if Google Sheets fails. The form shows an error,
  retains entered values and displays success only after the remote append returns.
- The previous local CSV utility is retained for existing files/tests, but the
  website no longer uses it. No local CSVs are automatically uploaded or deleted.

The Team Hub retains its original email-based identification flow; it does not
verify email ownership. Plan stronger authentication before relying on it for
sensitive team administration. Spreadsheet writes are not transactional across
multiple app replicas; run a single app instance for this workflow.

## Verification

```sh
python -m unittest discover -s tests -v
```

Tests use temporary files and mocked Google Sheets; they never send test
registrations to the real account. Coverage includes legacy-row preservation,
current-event filtering, header mapping, raw writes, form submission, required team
name, duplicate email handling, failed-write feedback, zero-sum trade P&L and
inside/outside-spread feedback.

The original account's sheet was reached with read-only credentials during this
update. No production participant data was written, erased or printed. Deployment
has not been performed; publishing these files to the configured Streamlit app is
still required. The invitation files and separate email scripts remain unchanged.

## Design

The site uses a dark navy palette, warm off-white type, cobalt actions, more
balanced typography, a compact event schedule and a grouped registration form.
The interactive section starts with a role choice: Trader or Market Maker. Each
role plays six easy-to-hard rounds, with cumulative P&L shown throughout. Before
locking a trade, Traders see the round's question and the sample bid and ask,
then choose a side and share count; the answer is revealed after the trade.
Exactly half the sample quotes are fair, with the rest mispriced. Market makers
see each question, set an estimate and spread, and trade against a sample trader.
Both roles have zero-sum P&L, a round summary, and an option to restart as the
other role. Scores use simulation credits, not real money or live event data.
Team-management forms are available on demand rather than filling the landing
page. Responsive styles are in [styles.css](styles.css),
with native controls themed in [.streamlit/config.toml](.streamlit/config.toml).
