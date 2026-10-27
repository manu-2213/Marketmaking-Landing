"""Single source of truth for the 2026 hackathon landing page."""

import os
from pathlib import Path


EVENT_CONFIG = {
    "title": "AI Market-Making Hackathon 2026",
    "year": 2026,
    "organiser": "Queen Mary University of London Machine Learning Society (QMML)",
    "opening_date": "19 November 2026",
    "competition_date": "26 November 2026",
    "venue": "In person; venue details to be announced",
    "eligibility": "University students across universities",
    "team_size": "2–4 participants",
    "round_count_min": 9,
    "round_count_max": 10,
    "status": "upcoming",
    "registration_open": True,
    "registration_csv": os.environ.get(
        "QMML_REGISTRATIONS_CSV",
        str(Path(__file__).parent / "registrations.csv"),
    ),
    "prize_details": "Prize details to be announced",
    "partners": ("BCG", "CIRQL", "ENCODE"),
}
