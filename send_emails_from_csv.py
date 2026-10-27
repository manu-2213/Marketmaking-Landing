"""
Send emails from email_drafts.csv

Usage:
    python send_emails_from_csv.py <path_to_csv>                # sends real emails
    python send_emails_from_csv.py <path_to_csv> --dry-run      # prints emails, sends nothing

Example:
    python send_emails_from_csv.py out/team_invites_20260325_144224/email_drafts.csv
    python send_emails_from_csv.py out/team_invites_20260325_144224/email_drafts.csv --dry-run
"""

import sys
import csv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

# ── CONFIG ─────────────────────────────────────────────────────────────────────
SMTP_HOST      = "smtp.gmail.com"
SMTP_PORT      = 587
SENDER_EMAIL   = "manuel.teres356356@gmail.com"        # ← Gmail account
SENDER_PASSWORD = "lhub llsx zotf byhp"                # ← Gmail app password
SENDER_NAME    = "QMUL AI Hackathon"
# ───────────────────────────────────────────────────────────────────────────────

DRY_RUN = "--dry-run" in sys.argv


def load_emails_from_csv(csv_path):
    """Load email data from CSV file."""
    emails = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            emails.append(row)
    return emails


def send_email(recipient_email, recipient_name, subject, body):
    """Send a single email."""
    if DRY_RUN:
        print(f"\n{'='*70}")
        print(f"DRY RUN: Would send email to {recipient_email}")
        print(f"{'='*70}")
        print(f"To: {recipient_email}")
        print(f"From: {SENDER_NAME} <{SENDER_EMAIL}>")
        print(f"Subject: {subject}")
        print(f"\n{body}")
        print(f"{'='*70}\n")
        return True
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
        msg['To'] = recipient_email
        
        # Attach plain text version
        msg.attach(MIMEText(body, 'plain'))
        
        # Connect and send
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
    if len(sys.argv) < 2:
        print("Usage: python send_emails_from_csv.py <csv_path> [--dry-run]")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    csv_file = Path(csv_path)
    
    if not csv_file.exists():
        print(f"Error: CSV file not found: {csv_path}")
        sys.exit(1)
    
    print(f"Loading emails from {csv_path}...")
    emails = load_emails_from_csv(csv_path)
    
    if not emails:
        print("No emails found in CSV file.")
        sys.exit(1)
    
    print(f"Found {len(emails)} email(s) to send.\n")
    
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
    
    for email_data in emails:
        recipient_email = email_data.get('recipient_email', '').strip()
        recipient_name = email_data.get('recipient_name', '').strip()
        subject = email_data.get('subject', '').strip()
        body = email_data.get('body', '').strip()
        
        # Validate required fields
        if not recipient_email:
            print(f"⚠ Skipping row: missing recipient_email")
            continue
        
        if not subject or not body:
            print(f"⚠ Skipping {recipient_email}: missing subject or body")
            continue
        
        # Check for multiple emails in one cell (from user memory - common issue)
        if ' - ' in recipient_email:
            print(f"⚠ Skipping {recipient_email}: contains multiple emails separated by ' - '")
            continue
        
        if send_email(recipient_email, recipient_name, subject, body):
            sent_count += 1
        else:
            failed_count += 1
    
    print(f"\n{'='*70}")
    print(f"Summary: {sent_count} sent, {failed_count} failed")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
