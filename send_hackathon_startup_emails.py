"""
Send hackathon startup emails to all people with assigned teams from Google Sheets.

Uses their personal invite URLs from the latest email_drafts.csv

Usage:
    python send_hackathon_startup_emails.py             # sends real emails
    python send_hackathon_startup_emails.py --dry-run   # prints emails, sends nothing

Requirements:
  • Run from the 'landing website' directory so it can find .streamlit/secrets.toml
"""

import sys
import csv
import smtplib
import tomllib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

# ── CONFIG ─────────────────────────────────────────────────────────────────────
SMTP_HOST      = "smtp.gmail.com"
SMTP_PORT      = 587
SENDER_EMAIL   = "manuel.teres356356@gmail.com"
SENDER_PASSWORD = "lhub llsx zotf byhp"
SENDER_NAME    = "QMUL AI Hackathon"

STREAMLIT_BASE_URL = "https://market-making-qmml.streamlit.app"
YOUTUBE_URL    = "https://www.youtube.com/@QMMLS"
DISCORD_URL    = "https://discord.gg/MTtuQJDX"

DRY_RUN = "--dry-run" in sys.argv

_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def load_secrets():
    secrets_path = Path(".streamlit/secrets.toml")
    if not secrets_path.exists():
        raise FileNotFoundError(
            "Could not find .streamlit/secrets.toml — "
            "run this script from the 'landing website' directory."
        )
    with open(secrets_path, "rb") as f:
        return tomllib.load(f)


def get_sheet(secrets):
    creds = Credentials.from_service_account_info(
        secrets["gcp_service_account"], scopes=_SCOPES
    )
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(secrets["sheets"]["spreadsheet_id"])
    return sh.sheet1


def find_latest_invite_csv():
    """Find the most recent email_drafts.csv file in out/team_invites_*"""
    out_dir = Path("out")
    if not out_dir.exists():
        raise FileNotFoundError("No 'out' directory found")
    
    csv_files = sorted(out_dir.glob("team_invites_*/email_drafts.csv"), reverse=True)
    if not csv_files:
        raise FileNotFoundError("No email_drafts.csv files found")
    
    latest = csv_files[0]
    print(f"Using invite codes from: {latest}")
    return latest


def load_invite_codes(csv_path):
    """Load invite codes and URLs from email_drafts.csv"""
    invite_map = {}  # email -> {team_name, invite_code, invite_url}
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row.get('recipient_email', '').strip().lower()
            team_name = row.get('team_name', '').strip()
            invite_code = row.get('invite_code', '').strip()
            old_url = row.get('invite_url', '').strip()
            
            if email and team_name and invite_code:
                # Construct correct URL with base domain
                new_url = f"{STREAMLIT_BASE_URL}/?invite={invite_code}&team={team_name.replace(' ', '+')}"
                invite_map[email] = {
                    'team_name': team_name,
                    'invite_code': invite_code,
                    'invite_url': new_url
                }
    
    return invite_map


def get_team_members(ws, invite_map):
    """Get all people with assigned team names from the sheet, matched with invite codes"""
    rows = ws.get_all_values()
    if len(rows) <= 1:
        return []
    
    header = rows[0]
    
    # Find column indices - use lowercase versions
    name_idx = header.index("name") if "name" in header else -1
    email_idx = header.index("email") if "email" in header else -1
    team_idx = header.index("team_name") if "team_name" in header else -1
    
    if name_idx == -1 or email_idx == -1 or team_idx == -1:
        print(f"Error: Could not find required columns. Headers: {header}")
        return []
    
    members = []
    seen_emails = set()
    
    for r in rows[1:]:
        if len(r) <= max(email_idx, team_idx):
            continue
        
        email = r[email_idx].strip().lower() if email_idx >= 0 and email_idx < len(r) else ""
        name = r[name_idx].strip() if name_idx >= 0 and name_idx < len(r) else ""
        team_name = r[team_idx].strip() if team_idx >= 0 and team_idx < len(r) else ""
        
        # Only include if email and team_name are present and in invite_map
        if email and team_name and email not in seen_emails and email in invite_map:
            invite_data = invite_map[email]
            members.append({
                'name': name,
                'email': email,
                'team_name': invite_data['team_name'],
                'invite_code': invite_data['invite_code'],
                'invite_url': invite_data['invite_url']
            })
            seen_emails.add(email)
    
    return members


def startup_email(name: str, team_name: str, invite_code: str, invite_url: str) -> tuple[str, str]:
    """Email for hackathon startup - includes personal team link, YouTube, and Discord"""
    subject = f"🚀 Your Market-Making Hackathon Team Link ({team_name})"
    body = f"""\
Hi {name},

Your team "{team_name}" is all set for the Market-Making Hackathon!

🔗 YOUR TEAM LINK
{invite_url}

⚠️ IMPORTANT: DO NOT USE THIS LINK YET!
Wait for the hackathon to officially start. You will be notified when to join.

🎬 WATCH THE LIVESTREAM
The hackathon kick-off will be streamed live on YouTube:
{YOUTUBE_URL}

You can also find past events and recordings on the QMMLS channel.

💬 JOIN THE DISCORD
Connect with other participants and get live support:
{DISCORD_URL}

📱 WHEN TO JOIN
Once the hackathon officially starts, use your team link above to access the app.

Your team name "{team_name}" is confirmed in the system.

🎯 WHAT TO EXPECT
• Live kickoff on the YouTube stream
• Real-time trading platform
• Competition with 70+ other teams
• Leaderboard updates throughout the event
• Get help on Discord if needed

Thanks for being part of this! We're excited to see Team "{team_name}" in action.

The QMUL AI Hackathon Team
"""
    return subject, body


def send_email(recipient_email, recipient_name, subject, body):
    """Send a single email."""
    if DRY_RUN:
        print(f"\n{'='*70}")
        print(f"DRY RUN: Would send email to {recipient_email}")
        print(f"{'='*70}")
        print(f"To: {recipient_email}")
        print(f"From: {SENDER_NAME} <{SENDER_EMAIL}>")
        print(f"Subject: {subject}\n")
        print(body)
        print(f"{'='*70}\n")
        return True
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
        msg['To'] = recipient_email
        
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
        
        print(f"✓ Sent to {recipient_email}")
        return True
    except Exception as e:
        print(f"✗ Failed to send to {recipient_email}: {e}")
        return False


def main():
    print("Loading invite codes from CSV...")
    try:
        csv_path = find_latest_invite_csv()
        invite_map = load_invite_codes(csv_path)
        print(f"Loaded {len(invite_map)} invite codes\n")
    except Exception as e:
        print(f"Error loading invite codes: {e}")
        sys.exit(1)
    
    print("Loading from Google Sheets...")
    
    try:
        secrets = load_secrets()
        ws = get_sheet(secrets)
        members = get_team_members(ws, invite_map)
    except Exception as e:
        print(f"Error loading from Google Sheets: {e}")
        sys.exit(1)
    
    if not members:
        print("No team members found (with matching invite codes).")
        sys.exit(1)
    
    print(f"Found {len(members)} people with assigned teams.\n")
    
    if DRY_RUN:
        print("DRY RUN MODE: No emails will actually be sent.\n")
    else:
        response = input("Ready to send real emails. Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled.")
            sys.exit(0)
        print()
    
    sent_count = 0
    failed_count = 0
    
    for member in members:
        name = member.get('name', '').strip()
        email = member.get('email', '').strip()
        team_name = member.get('team_name', '').strip()
        invite_code = member.get('invite_code', '').strip()
        invite_url = member.get('invite_url', '').strip()
        
        # Check for multiple emails (from user memory - common issue)
        if ' - ' in email:
            print(f"⚠ Skipping {email}: contains multiple emails separated by ' - '")
            continue
        
        subject, body = startup_email(name, team_name, invite_code, invite_url)
        
        if send_email(email, name, subject, body):
            sent_count += 1
        else:
            failed_count += 1
    
    print(f"\n{'='*70}")
    print(f"Summary: {sent_count} sent, {failed_count} failed")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
