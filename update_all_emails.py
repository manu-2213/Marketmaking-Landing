"""
Update all emails in email_drafts.csv with YouTube livestream and Discord info
"""

import csv
from pathlib import Path

def update_emails_csv(csv_path):
    """Update all email bodies with YouTube and Discord info"""
    
    # Read all rows
    rows = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # Update each row's body
    for row in rows:
        old_body = row['body']
        
        # Create new body with YouTube and Discord info
        new_body = f"""{old_body.split('Please do not share')[0].rstrip()}
⚠️ IMPORTANT: DO NOT USE THIS LINK YET!
Wait for the hackathon to officially start. You will be given the go-ahead signal when to join.

🎬 WATCH THE LIVESTREAM
The hackathon kick-off will be streamed live on YouTube:
https://www.youtube.com/@QMMLS

💬 JOIN THE DISCORD
Connect with other participants and get live support:
https://discord.gg/MTtuQJDX

Please do not share this link outside your team."""
        
        row['body'] = new_body
    
    # Write back
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        fieldnames = rows[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"✓ Updated {len(rows)} emails in {csv_path}")

if __name__ == "__main__":
    csv_path = Path("/Users/manu13/Desktop/PHD/Hackathons/MarketMaking/landing website/out/team_invites_20260325_150704/email_drafts.csv")
    update_emails_csv(csv_path)
