# QMML AI Market-Making Hackathon 2026

This repository contains the Streamlit event site, registration form, and team-formation hub. The live market simulator, trading engine, datasets, and scoring service are not part of this repository.

## Run locally

```sh
python -m pip install -r requirements.txt
streamlit run landing.py
```

Event dates, team sizes, registration status, CSV location, round count, and prize text are centralized in `event_config.py`.

## Registration and CSV storage

Registration is open. The form collects name, student ID, student email, university, degree/background, team name (optional when looking for a team), team size/looking-for-team status, ML experience, and an optional note. Student ID and student email must be unique. The Team Hub can update registrations and find/join teams using the same CSV.

On the first registration, the app creates `registrations.csv` beside `landing.py`, unless `QMML_REGISTRATIONS_CSV` points to a different location. The CSV contains private participant details and is excluded from Git by `.gitignore`. If an existing `registrations.csv` is present, rows are preserved; the app adds the `student_id` column when needed. It never writes to the old Google Sheet.

**Deployment note:** local CSV storage is suitable only when the Streamlit host provides persistent writable storage. Many hosted app filesystems are ephemeral or have multiple replicas. For production use, set `QMML_REGISTRATIONS_CSV` to a durable private volume path and back it up securely, or replace this adapter with a managed database before enabling registration. The app does not upload registration records to a remote service.

The CSV is private operational data. Do not commit it, publish it, or add it to logs. Back it up to access-controlled storage and retain participant data only as long as needed.

## Event and production status

- The local site is configured with the 19 and 26 November 2026 in-person dates; venue details and prizes remain unannounced.
- This checkout did not contain `registrations.csv` when inspected. No existing CSV records were deleted or overwritten.
- Production deployment and production-data reset have not been performed. The configured Git remote does not match the repository URL in the original relaunch brief.
- The `out/` invitation drafts and email scripts are separate from the website registration store and may contain previous-event campaign details. They were not changed.

## Design and assets

The responsive site uses the navy, cream, and cobalt visual system in `styles.css`. Official BCG, CIRQL, and ENCODE logo assets were not present in the workspace; partner names are shown without implying event sponsorship or prize funding.
