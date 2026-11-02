"""
Send emails from email_drafts.csv

Usage:
    python send_emails_from_csv.py <path_to_csv>                # sends real emails
    python send_emails_from_csv.py <path_to_csv> --dry-run      # prints emails, sends nothing
    python send_emails_from_csv.py --check-login                # tests the Gmail login, sends nothing

The password comes from GMAIL_APP_PASSWORD, or is asked for when not set. Addresses
already emailed are recorded in <path_to_csv>.sent and skipped on a rerun.

Example:
    python send_emails_from_csv.py out/team_invites_20260325_144224/email_drafts.csv
    python send_emails_from_csv.py out/team_invites_20260325_144224/email_drafts.csv --dry-run
"""

import os
import sys
import csv
import smtplib
import time
from getpass import getpass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

# ── CONFIG ─────────────────────────────────────────────────────────────────────
SMTP_HOST      = "smtp.gmail.com"
SMTP_PORT      = 587
SENDER_EMAIL   = "manuel.teres356356@gmail.com"        # ← Gmail account
SENDER_NAME    = "QMUL AI Hackathon"
# ───────────────────────────────────────────────────────────────────────────────

DRY_RUN = "--dry-run" in sys.argv
SECONDS_BETWEEN_EMAILS = 1


def load_emails_from_csv(csv_path):
    """Load email data from CSV file."""
    emails = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            emails.append(row)
    return emails


def get_password():
    """Read the app password; Gmail displays it with spaces, which are not part of it."""
    password = os.environ.get("GMAIL_APP_PASSWORD") or getpass(f"App password for {SENDER_EMAIL}: ")
    return password.replace(" ", "").strip()


def connect(password):
    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30)
    server.starttls()
    server.login(SENDER_EMAIL, password)
    return server


def connect_or_exit(password):
    """Log in once before sending; repeated bad logins make Gmail drop connections."""
    try:
        return connect(password)
    except smtplib.SMTPAuthenticationError as e:
        print(f"Gmail rejected the login for {SENDER_EMAIL}: {e.smtp_code}")
        print("Use a 16-character app password created while signed in to that account.")
    except (smtplib.SMTPException, OSError) as e:
        print(f"Could not log in to Gmail: {e}")
        print("Gmail may be limiting logins after failed attempts. Wait 15 minutes and try again.")
    print("Nothing was sent.")
    sys.exit(1)


def build_message(recipient_email, subject, body):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
    msg['To'] = recipient_email
    msg.attach(MIMEText(body, 'plain'))
    return msg.as_string()


def print_dry_run(recipient_email, subject, body):
    print(f"\n{'='*70}")
    print(f"DRY RUN: Would send email to {recipient_email}")
    print(f"{'='*70}")
    print(f"To: {recipient_email}")
    print(f"From: {SENDER_NAME} <{SENDER_EMAIL}>")
    print(f"Subject: {subject}")
    print(f"\n{body}")
    print(f"{'='*70}\n")


def load_sent(sent_path):
    if not sent_path.exists():
        return set()
    return {line.strip() for line in sent_path.read_text(encoding="utf-8").splitlines() if line.strip()}


def main():
    if "--check-login" in sys.argv:
        connect_or_exit(get_password()).quit()
        print(f"Login OK for {SENDER_EMAIL}. Nothing was sent.")
        return

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

    sent_path = Path(f"{csv_path}.sent")
    already_sent = load_sent(sent_path)
    print(f"Found {len(emails)} email(s), {len(already_sent)} already sent.\n")

    server = None
    if DRY_RUN:
        print("DRY RUN MODE: No emails will actually be sent.\n")
    else:
        password = get_password()
        server = connect_or_exit(password)
        print(f"Login OK for {SENDER_EMAIL}.")
        response = input("Ready to send real emails. Continue? (yes/no): ")
        if response.lower() != 'yes':
            server.quit()
            print("Cancelled.")
            sys.exit(0)
        print()

    sent_count = 0
    failed_count = 0

    for email_data in emails:
        recipient_email = email_data.get('recipient_email', '').strip()
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

        if recipient_email in already_sent:
            continue

        if DRY_RUN:
            print_dry_run(recipient_email, subject, body)
            sent_count += 1
            continue

        message = build_message(recipient_email, subject, body)
        try:
            try:
                server.sendmail(SENDER_EMAIL, recipient_email, message)
            except smtplib.SMTPServerDisconnected:
                server = connect(password)
                server.sendmail(SENDER_EMAIL, recipient_email, message)
        except (smtplib.SMTPRecipientsRefused, smtplib.SMTPDataError) as e:
            print(f"✗ Failed to send to {recipient_email}: {e}")
            failed_count += 1
            continue
        except (smtplib.SMTPException, OSError) as e:
            print(f"✗ Stopped at {recipient_email}: {e}")
            print(f"Rerun the same command later; sent addresses are skipped.")
            failed_count += 1
            break

        with sent_path.open("a", encoding="utf-8") as f:
            f.write(recipient_email + "\n")
        print(f"✓ Sent to {recipient_email}")
        sent_count += 1
        time.sleep(SECONDS_BETWEEN_EMAILS)

    if server is not None:
        try:
            server.quit()
        except smtplib.SMTPException:
            pass

    print(f"\n{'='*70}")
    print(f"Summary: {sent_count} sent, {failed_count} failed")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
