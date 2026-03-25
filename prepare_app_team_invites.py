#!/usr/bin/env python3
"""Prepare app team invite links from landing registrations.

What this does:
1. Reads registrations from Google Sheets.
2. Extracts unique non-empty team names.
3. Creates missing teams in the app Supabase `teams` table.
4. Generates invite codes + invite URLs.
5. Writes email drafts to files (does NOT send any email).

Usage:
    python prepare_app_team_invites.py
    python prepare_app_team_invites.py --app-url https://your-app-url.streamlit.app
    python prepare_app_team_invites.py --apply
    python prepare_app_team_invites.py --skip-app-sync
"""

from __future__ import annotations

import argparse
import csv
import re
import tomllib
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from config import STARTING_BUDGET  # noqa: E402
from invites import make_team_invite_code, normalize_team_name  # noqa: E402


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
]
DEFAULT_APP_URL = "https://market-making-qmml.streamlit.app"
EMAIL_RE = re.compile(r"^[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}$", re.IGNORECASE)


@dataclass
class Registrant:
    name: str
    email: str
    team_name: str


def _load_toml(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    with path.open("rb") as f:
        return tomllib.load(f)


def load_landing_secrets() -> dict:
    return _load_toml(Path(__file__).parent / ".streamlit" / "secrets.toml")


def load_app_secrets() -> dict:
    return _load_toml(ROOT / "app" / ".streamlit" / "secrets.toml")


def split_emails(raw: str) -> list[str]:
    """Split potentially combined email cells into clean addresses."""
    if not raw:
        return []
    chunks = re.split(r"\s*(?:,|;|/|\||\s-\s|\s+)\s*", raw.strip())
    emails = []
    for c in chunks:
        item = c.strip().strip("<>()[]{}\"'")
        if item and EMAIL_RE.match(item):
            emails.append(item.lower())
    return list(dict.fromkeys(emails))


def get_registration_rows() -> list[dict]:
    import gspread
    from google.oauth2.service_account import Credentials

    secrets = load_landing_secrets()
    creds = Credentials.from_service_account_info(
        secrets["gcp_service_account"], scopes=SCOPES
    )
    gc = gspread.authorize(creds)
    ws = gc.open_by_key(secrets["sheets"]["spreadsheet_id"]).sheet1
    rows = ws.get_all_values()
    if len(rows) <= 1:
        return []
    header = rows[0]
    out = []
    for r in rows[1:]:
        out.append({h: r[i] if i < len(r) else "" for i, h in enumerate(header)})
    return out


def extract_team_members(rows: list[dict]) -> tuple[dict[str, list[Registrant]], list[str]]:
    """Return team->members map and duplicate-normalization warnings."""
    by_team_norm: dict[str, list[Registrant]] = defaultdict(list)
    canonical_team_name: dict[str, str] = {}
    warnings: list[str] = []

    for row in rows:
        team_raw = (row.get("team_name") or "").strip()
        if not team_raw:
            continue

        team_norm = normalize_team_name(team_raw).lower()
        if not team_norm:
            continue

        if team_norm in canonical_team_name and canonical_team_name[team_norm] != team_raw:
            warnings.append(
                f"Merged team name variants: '{canonical_team_name[team_norm]}' + '{team_raw}'"
            )
        else:
            canonical_team_name[team_norm] = team_raw

        name = (row.get("name") or "Participant").strip() or "Participant"
        email_raw = (row.get("email") or "").strip()
        for email in split_emails(email_raw):
            by_team_norm[team_norm].append(
                Registrant(name=name, email=email, team_name=canonical_team_name[team_norm])
            )

    deduped: dict[str, list[Registrant]] = {}
    for team_norm, members in by_team_norm.items():
        canonical = canonical_team_name[team_norm]
        uniq = {}
        for m in members:
            uniq[m.email] = m
        deduped[canonical] = sorted(uniq.values(), key=lambda x: (x.name.lower(), x.email))

    return dict(sorted(deduped.items())), sorted(set(warnings))


def get_supabase_client():
    from supabase import create_client

    app_secrets = load_app_secrets()
    return create_client(app_secrets["SUPABASE_URL"], app_secrets["SUPABASE_KEY"])


def sync_teams_to_app(
    teams: dict[str, list[Registrant]],
    apply_changes: bool,
) -> tuple[set[str], set[str], set[str]]:
    """Return (already_existing, created_now, would_create)."""
    sb = get_supabase_client()
    existing_rows = sb.table("teams").select("name").execute().data or []
    existing = {r["name"] for r in existing_rows}

    created = set()
    would_create = set()
    for team_name in teams.keys():
        if team_name in existing:
            continue
        if apply_changes:
            sb.table("teams").insert({"name": team_name, "cash": STARTING_BUDGET}).execute()
            created.add(team_name)
        else:
            would_create.add(team_name)

    return existing, created, would_create


def compose_email(name: str, team_name: str, invite_code: str, invite_url: str) -> tuple[str, str]:
    subject = f"Your Market-Making Hackathon Team Link ({team_name})"
    body = (
        f"Hi {name},\n\n"
        "Your team has been set up for the Market-Making Hackathon app.\n\n"
        f"Team name: {team_name}\n"
        f"Join code: {invite_code}\n"
        f"Join link: {invite_url}\n\n"
        "How to join:\n"
        "1. Open the join link.\n"
        "2. Confirm your team name on the login screen.\n"
        "3. Click 'Join Game'.\n\n"
        "Please do not share this link outside your team.\n\n"
        "This is a draft message generated for organiser review only.\n"
    )
    return subject, body


def write_outputs(
    teams: dict[str, list[Registrant]],
    existing: set[str],
    created: set[str],
    would_create: set[str],
    app_url: str,
) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(__file__).parent / "out" / f"team_invites_{timestamp}"
    out_dir.mkdir(parents=True, exist_ok=True)

    team_csv = out_dir / "team_invites.csv"
    email_csv = out_dir / "email_drafts.csv"
    email_txt = out_dir / "email_drafts.txt"

    with team_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "team_name", "member_count", "invite_code", "invite_url", "status"
        ])
        for team_name, members in teams.items():
            code = make_team_invite_code(team_name)
            url = f"{app_url.rstrip('/')}/?invite={code}"
            if team_name in created:
                status = "created"
            elif team_name in would_create:
                status = "would_create"
            else:
                status = "already_exists"
            w.writerow([team_name, len(members), code, url, status])

    with email_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "recipient_name", "recipient_email", "team_name", "invite_code", "invite_url", "subject", "body"
        ])
        for team_name, members in teams.items():
            code = make_team_invite_code(team_name)
            url = f"{app_url.rstrip('/')}/?invite={code}"
            for m in members:
                subject, body = compose_email(m.name, team_name, code, url)
                w.writerow([m.name, m.email, team_name, code, url, subject, body])

    with email_txt.open("w", encoding="utf-8") as f:
        for team_name, members in teams.items():
            code = make_team_invite_code(team_name)
            url = f"{app_url.rstrip('/')}/?invite={code}"
            f.write(f"=== TEAM: {team_name} | CODE: {code} ===\n")
            for m in members:
                subject, body = compose_email(m.name, team_name, code, url)
                f.write(f"TO: {m.name} <{m.email}>\n")
                f.write(f"SUBJECT: {subject}\n")
                f.write(body)
                f.write("\n---\n\n")

    print(f"Wrote: {team_csv}")
    print(f"Wrote: {email_csv}")
    print(f"Wrote: {email_txt}")
    print(
        f"\nSummary: {len(teams)} teams | {len(created)} created | "
        f"{len(would_create)} would_create | {len(existing & set(teams.keys()))} already existed"
    )

    return out_dir


def main():
    parser = argparse.ArgumentParser(description="Prepare team invites and draft emails")
    parser.add_argument("--app-url", default=DEFAULT_APP_URL, help="Base URL of the game app")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually create missing teams in Supabase (default is dry run).",
    )
    parser.add_argument(
        "--skip-app-sync",
        action="store_true",
        help="Skip reading/writing app teams in Supabase and only build draft outputs.",
    )
    args = parser.parse_args()

    print("Loading registrations from Google Sheets...")
    rows = get_registration_rows()
    teams, warnings = extract_team_members(rows)
    if not teams:
        print("No named teams found in registrations. Nothing to do.")
        return

    if args.skip_app_sync:
        print("Skipping app sync (--skip-app-sync).")
        existing, created, would_create = set(), set(), set(teams.keys())
    else:
        print("Checking app teams in Supabase...")
        existing, created, would_create = sync_teams_to_app(teams, apply_changes=args.apply)

    print("Writing draft outputs...")
    out_dir = write_outputs(teams, existing, created, would_create, args.app_url)

    if warnings:
        warning_file = out_dir / "warnings.txt"
        warning_file.write_text("\n".join(warnings), encoding="utf-8")
        print(f"Wrote: {warning_file}")

    if args.skip_app_sync:
        print("\nDone. App sync skipped and no emails were sent.")
    elif args.apply:
        print("\nDone. Teams were synced and no emails were sent.")
    else:
        print("\nDone (dry run). No database writes and no emails were sent.")


if __name__ == "__main__":
    main()