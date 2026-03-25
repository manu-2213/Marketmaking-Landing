#!/usr/bin/env python3
"""
Extract team names from Google Sheets and generate Discord channel setup information.

Usage:
    python extract_teams.py                    # Print team names
    python extract_teams.py --format-channels  # Generate channel creation list
    python extract_teams.py --members          # Show team members per team
"""

import sys
import tomllib
from pathlib import Path
from collections import defaultdict

import gspread
from google.oauth2.service_account import Credentials

_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
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


def get_registrants(ws):
    rows = ws.get_all_values()
    if len(rows) <= 1:
        return []
    header = rows[0]

    def row_to_dict(r):
        return {h: r[i] if i < len(r) else "" for i, h in enumerate(header)}

    # De-duplicate by email
    by_email = {}
    for r in rows[1:]:
        if len(r) < 3:
            continue
        email = (r[2] if len(r) > 2 else "").strip().lower()
        if not email:
            continue
        by_email[email] = row_to_dict(r)

    return list(by_email.values())


def sanitize_channel_name(name: str) -> str:
    """Convert team name to valid Discord channel name."""
    # Discord channel names: lowercase, no spaces (use hyphens), max 100 chars
    sanitized = name.lower().strip()
    # Replace spaces with hyphens
    sanitized = sanitized.replace(" ", "-")
    # Remove special characters except hyphens
    sanitized = "".join(c if c.isalnum() or c == "-" else "" for c in sanitized)
    # Remove consecutive hyphens
    while "--" in sanitized:
        sanitized = sanitized.replace("--", "-")
    # Remove leading/trailing hyphens
    sanitized = sanitized.strip("-")
    # Truncate to Discord's 100 char limit (leaving room for emoji prefix)
    if len(sanitized) > 90:
        sanitized = sanitized[:90]
    return sanitized


def extract_teams(registrants):
    """Extract unique teams and their members."""
    teams = defaultdict(list)
    solos_without_team = []

    for person in registrants:
        team_name = (person.get("team_name") or "").strip()
        if team_name:
            teams[team_name].append(person)
        else:
            solos_without_team.append(person)

    return teams, solos_without_team


def print_teams_list(teams):
    """Print all team names."""
    print(f"\n{'='*60}")
    print(f"📊 UNIQUE TEAMS ({len(teams)} total)")
    print(f"{'='*60}\n")

    for i, team_name in enumerate(sorted(teams.keys()), 1):
        count = len(teams[team_name])
        member_count = count  # Each entry is one member
        print(f"{i:2d}. {team_name!r}")
        print(f"    Members: {member_count}")
        for member in teams[team_name]:
            print(f"      • {member.get('name', 'Unknown')} ({member.get('email', 'N/A')})")
        print()


def print_channel_format(teams):
    """Print Discord channel creation info."""
    print(f"\n{'='*60}")
    print(f"🎯 DISCORD CHANNELS TO CREATE ({len(teams)} channels)")
    print(f"{'='*60}\n")

    print("Copy-paste format for Discord channel creation:\n")

    for team_name in sorted(teams.keys()):
        sanitized = sanitize_channel_name(team_name)
        channel_name = f"🎯-{sanitized}"

        # Show mapping
        print(f"Team: {team_name!r}")
        print(f"Channel: #{channel_name}")
        print(f"Members: {len(teams[team_name])}")
        print()

    # Generate Discord.py code
    print(f"\n{'─'*60}")
    print("Discord.py Bot Setup Code:")
    print(f"{'─'*60}\n")

    print("# Team channels to create:")
    print("TEAMS_TO_CREATE = {")
    for team_name in sorted(teams.keys()):
        sanitized = sanitize_channel_name(team_name)
        channel_name = f"🎯-{sanitized}"
        print(f"    '{team_name}': '{channel_name}',")
    print("}\n")


def print_members_table(teams, solos_without_team):
    """Print detailed team membership table."""
    print(f"\n{'='*60}")
    print(f"👥 TEAM MEMBERSHIP ({len(teams)} teams)")
    print(f"{'='*60}\n")

    for team_name in sorted(teams.keys()):
        members = teams[team_name]
        print(f"\n🎯 {team_name}")
        print(f"   ({len(members)} members)\n")

        # Print members
        for member in sorted(members, key=lambda p: p.get("name", "")):
            name = member.get("name", "Unknown").strip()
            email = member.get("email", "N/A")
            team_size = member.get("team_size", "N/A")
            print(f"   • {name:<30} | {email:<35} | Size: {team_size}")

        print()

    if solos_without_team:
        print(f"\n⚠️  SOLOS WITHOUT TEAM NAME ({len(solos_without_team)} participants)")
        print("   These participants need to set a team name on the website:")
        print("   https://qmml-hackathon.streamlit.app\n")
        for person in sorted(solos_without_team, key=lambda p: p.get("name", "")):
            name = person.get("name", "Unknown").strip()
            email = person.get("email", "N/A")
            print(f"   • {name:<30} | {email}")


def main():
    print("📊 Extracting teams from Google Sheets...")

    try:
        secrets = load_secrets()
        ws = get_sheet(secrets)
        registrants = get_registrants(ws)
        teams, solos_without_team = extract_teams(registrants)

        print(f"✓ Found {len(registrants)} registrants")
        print(f"✓ Found {len(teams)} teams")
        print(f"✓ Found {len(solos_without_team)} solos without team name\n")

        # Determine which output format to use
        if "--members" in sys.argv:
            print_members_table(teams, solos_without_team)
        elif "--format-channels" in sys.argv:
            print_channel_format(teams)
        else:
            # Default: print teams list
            print_teams_list(teams)

            # Also show the channel format as reference
            print(f"\n\n{'='*60}")
            print("Use --format-channels for Discord channel creation format")
            print("Use --members for detailed membership breakdown")
            print(f"{'='*60}\n")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nNote: Make sure you're running this from the 'landing website' directory")
        sys.exit(1)


if __name__ == "__main__":
    main()
