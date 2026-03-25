#!/usr/bin/env python3
"""Create demo teams in Supabase for testing invite links."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from config import STARTING_BUDGET


def load_app_secrets() -> dict:
    from tomllib import load
    
    with open(ROOT / "app" / ".streamlit" / "secrets.toml", "rb") as f:
        return load(f)


def main():
    from supabase import create_client
    
    app_secrets = load_app_secrets()
    sb = create_client(app_secrets["SUPABASE_URL"], app_secrets["SUPABASE_KEY"])
    
    demo_teams = [
        "Alpha Traders",
        "Beta Squad", 
        "Gamma Team",
    ]
    
    # Get existing teams
    existing_rows = sb.table("teams").select("name").execute().data or []
    existing = {r["name"] for r in existing_rows}
    
    print("Creating demo teams...")
    for team_name in demo_teams:
        if team_name in existing:
            print(f"  ✓ {team_name} (already exists)")
        else:
            sb.table("teams").insert({"name": team_name, "cash": STARTING_BUDGET}).execute()
            print(f"  ✓ {team_name} (created)")
    
    print("\nDone! Demo teams are ready for invite links.")


if __name__ == "__main__":
    main()
