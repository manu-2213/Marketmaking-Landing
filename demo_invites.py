#!/usr/bin/env python3
"""Demo: Generate team invites + draft emails without requiring secrets or external APIs."""

import csv
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "app"
sys.path.insert(0, str(APP_DIR))

from invites import make_team_invite_code, normalize_team_name

# Demo team data (simulating registrations from Google Sheets)
DEMO_TEAMS = {
    "Alpha Traders": ["alice@qmul.ac.uk", "bob@qmul.ac.uk"],
    "Beta Squad": ["charlie@qmul.ac.uk"],
    "Gamma Team": ["diana@qmul.ac.uk", "eve@qmul.ac.uk", "frank@qmul.ac.uk"],
}

APP_URL = "https://market-making-hackathon.streamlit.app"


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
        "Please do not share this link outside your team.\n"
    )
    return subject, body


def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(__file__).parent / "out" / f"team_invites_{timestamp}"
    out_dir.mkdir(parents=True, exist_ok=True)

    team_csv = out_dir / "team_invites.csv"
    email_csv = out_dir / "email_drafts.csv"
    email_txt = out_dir / "email_drafts.txt"

    print(f"Generating invites for {len(DEMO_TEAMS)} teams...")

    # Write team summary
    with team_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["team_name", "member_count", "invite_code", "invite_url", "status"])
        for team_name in sorted(DEMO_TEAMS.keys()):
            code = make_team_invite_code(team_name)
            url = f"{APP_URL.rstrip('/')}/?invite={code}"
            w.writerow([team_name, len(DEMO_TEAMS[team_name]), code, url, "ready"])

    # Write email drafts (CSV)
    with email_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "recipient_name", "recipient_email", "team_name", "invite_code", "invite_url", "subject", "body"
        ])
        for team_name in sorted(DEMO_TEAMS.keys()):
            code = make_team_invite_code(team_name)
            url = f"{APP_URL.rstrip('/')}/?invite={code}"
            for i, email in enumerate(DEMO_TEAMS[team_name], 1):
                name = f"Team Member {i}"
                subject, body = compose_email(name, team_name, code, url)
                w.writerow([name, email, team_name, code, url, subject, body])

    # Write email drafts (text file)
    with email_txt.open("w", encoding="utf-8") as f:
        for team_name in sorted(DEMO_TEAMS.keys()):
            code = make_team_invite_code(team_name)
            url = f"{APP_URL.rstrip('/')}/?invite={code}"
            f.write(f"=== TEAM: {team_name} | CODE: {code} ===\n")
            for i, email in enumerate(DEMO_TEAMS[team_name], 1):
                name = f"Team Member {i}"
                subject, body = compose_email(name, team_name, code, url)
                f.write(f"TO: {name} <{email}>\n")
                f.write(f"SUBJECT: {subject}\n")
                f.write(body)
                f.write("\n---\n\n")

    print(f"✅ Wrote: {team_csv}")
    print(f"✅ Wrote: {email_csv}")
    print(f"✅ Wrote: {email_txt}")
    print(f"\n📊 Summary: {len(DEMO_TEAMS)} teams | {sum(len(m) for m in DEMO_TEAMS.values())} members")
    print(f"📁 Output: {out_dir}\n")

    # Show sample
    print("Sample invite code and URL:")
    team = list(DEMO_TEAMS.keys())[0]
    code = make_team_invite_code(team)
    url = f"{APP_URL.rstrip('/')}/?invite={code}"
    print(f"  Team: {team}")
    print(f"  Code: {code}")
    print(f"  URL:  {url}")


if __name__ == "__main__":
    main()
