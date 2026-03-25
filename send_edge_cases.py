"""
Send emails to edge case registrants with invalid email formats in the signup sheet.
These are team registrants whose emails were combined in a single cell.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SENDER_EMAIL = "manuel.teres356356@gmail.com"
SENDER_PASSWORD = "lhub llsx zotf byhp"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

# Edge case emails extracted from malformed registration entries
EDGE_CASES = [
    # From: ecemgoksenina@gmail.com - arinkaptan06@gmail.com - alinazshah@outlook.com
    "ecemgoksenina@gmail.com",
    "arinkaptan06@gmail.com",
    "alinazshah@outlook.com",
    # From: te23315@qmul.ac.uk, oscar.gladysz@gwmail.gwu.edu
    "te23315@qmul.ac.uk",
    "oscar.gladysz@gwmail.gwu.edu",
]

def team_email_template(recipient_email: str) -> tuple[str, str]:
    """Email template for team registrants."""
    subject = "🚀 Market-Making AI Hackathon — In 2 Days! Set Your Team Name Now"
    
    body = """🚀 THE MARKET-MAKING AI HACKATHON STARTS IN 2 DAYS! 🚀

But we need one thing from you first: **a team name!**

🎯 WHY IS THIS CRITICAL?
Every team gets a unique URL for the game. Without a team name, you won't get yours.

You have 3 options:
    1. Solo play (keep a team name for yourself)
    2. Open your team so others can join
    3. Join an existing open team

⚡ SET YOUR TEAM NAME NOW
Visit the website and use "Choose / Update Team Name":
https://qmml-hackathon.streamlit.app/

(Only one person per team needs to submit this — use the same email you registered with)

📍 EVENT DETAILS
    Date: March 25th (Tomorrow!)
    Time: 6:00 PM (arrive 15 min early for a seat!)
    Location: David Sizer Lecture Theatre, Queen Mary University of London

🎯 WHAT'S HAPPENING
At kickoff, we'll cover:
    • How the hackathon week will run
    • What market making is in practice
    • The trading environment and rules
    • Strategy insights to help your agent shine

💻 WHAT TO BRING
    • Your laptop (fully charged!)
    • Your competitive spirit
    • Fresh ideas for algorithmic trading

⚠️ IMPORTANT REMINDERS
    ✅ You MUST be a Queen Mary student
    ✅ You MUST have a QMML membership: https://www.qmsu.org/groups/qmml/
       (This membership helps us fund big events and prizes!)
    ✅ Show up 15 minutes early — seats are limited and this event is very popular!
    ✅ **NO TEAM NAME? YOU WON'T GET A GAME URL!** Set it on the website above.

🎮 JOIN THE COMMUNITY
Connect with other hackers and get live support throughout the event on Discord:
https://discord.gg/MTtuQJDX
(Full autonomy for all members by end of day!)

See you tomorrow! 🔥

The QMUL AI Hackathon Team"""
    
    return subject, body

def send_email(to_email: str, subject: str, body: str) -> bool:
    """Send an email via Gmail SMTP."""
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = SENDER_EMAIL
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        
        return True
    except Exception as e:
        print(f"  ✗ Failed to send to {to_email}: {e}")
        return False

def main():
    print(f"Sending emails to {len(EDGE_CASES)} edge case registrants...\n")
    
    sent = 0
    failed = 0
    
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            
            for email in EDGE_CASES:
                subject, body = team_email_template(email)
                msg = MIMEMultipart("alternative")
                msg["From"] = SENDER_EMAIL
                msg["To"] = email
                msg["Subject"] = subject
                msg.attach(MIMEText(body, "plain"))
                
                try:
                    server.sendmail(SENDER_EMAIL, email, msg.as_string())
                    print(f"  ✓ Sent to {email}")
                    sent += 1
                except Exception as e:
                    print(f"  ✗ Failed for {email}: {e}")
                    failed += 1
    
    except Exception as e:
        print(f"Failed to connect to SMTP server: {e}")
        return
    
    print(f"\nDone. {sent} sent, {failed} failed.")

if __name__ == "__main__":
    main()
