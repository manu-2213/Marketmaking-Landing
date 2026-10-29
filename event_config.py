"""Single source of truth for the 2026 hackathon landing page."""

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
    "status": "registration open",
    "registration_open": True,
    # Current pot in GBP. All ticket revenue is added to it; shown as "£N+".
    "prize_pot_gbp": 300,
    "prize_categories": (
        ("Best overall P&L", ("1st place", "2nd place", "3rd place")),
        ("Best Sortino ratio", ("1st place", "2nd place", "3rd place")),
        ("Special awards", (
            "Best undergraduate team", "Best postgraduate team", "Random team prize",
        )),
    ),
    "partners": ("BCG", "CIRQL", "ENCODE"),
}
