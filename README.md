# QMML AI Market-Making Hackathon 2026

This repository contains the Streamlit landing page and team-registration workflow. It does not contain the live market simulator, trading engine, datasets, or leaderboard service.

## Run locally

Install the dependencies in `requirements.txt`, configure `.streamlit/secrets.toml` from `.streamlit/secrets.toml.example`, then run:

```sh
streamlit run landing.py
```

The public event details and registration controls are maintained in `event_config.py`. Registration is closed by default. Update the venue, registration URL, status, rounds, and confirmed prize details there as they become available.

## Registration data isolation

The former application read registrations from the first worksheet (`sheet1`) of the spreadsheet configured as `sheets.spreadsheet_id`. The 2026 application does not read that setting or that worksheet. It requires `sheets.spreadsheet_id_2026` and uses the `Registrations` worksheet in that dedicated spreadsheet. If the worksheet is missing, the app creates it with the registration header. There is no Streamlit session-state registration store.

Before enabling registration in a deployment:

1. In Google Drive, create a new, empty spreadsheet exclusively for the 2026 event. Do not reuse the spreadsheet used by an earlier event.
2. Share it with the configured Google service account and set its ID as `sheets.spreadsheet_id_2026` in the deployment secrets.
3. Verify that the spreadsheet is new/empty and that the deployment service account can access it. The app creates its `Registrations` worksheet when first needed.
4. Set `registration_open` to `True` in `event_config.py` only when registrations are ready to open, then restart/redeploy the Streamlit app.

The prior spreadsheet and its contents have intentionally not been deleted or modified. If an operator chooses to clear or retire that source later, first create and verify a timestamped Google Drive copy/export and document its ID and location. Do not clear the old spreadsheet as part of routine deployment.

## Reset and deployment status

- **Local changes:** the landing page no longer reads or renders earlier registrations, team records, or results while registration is closed. No files containing registration or competition records were deleted.
- **Local backup:** none was created because no local competition-state files were modified or removed.
- **Production backup/reset:** not performed. This workspace has no verified access to the deployed Google Sheet or deployment secrets, so its identity, contents, and backup location could not be verified.
- **Competition state:** this repository contains no trade, order, balance, submission, or scoring store to reset. Those systems must be audited separately in the repository/service that owns the competition engine.
- **Deployment:** not performed. The configured Git remote is not the repository URL supplied in the relaunch brief; reconcile the deployment repository before publishing these changes.

The `out/` invitation drafts and email utilities are not loaded by the Streamlit application. They were left untouched, including pre-existing local worktree changes. They should be reviewed separately before reuse for the November event.

## Design and assets

The page uses the 2026 event palette in `styles.css`. The workspace did not contain official BCG, CIRQL, or ENCODE logo files; partner names are shown as plain text with a note that partner recognition does not confirm sponsorship or prize funding.
