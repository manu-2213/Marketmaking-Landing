"""Single source of truth for the 2026 hackathon landing page."""

EVENT_CONFIG = {
    "title": "AI Market-Making Hackathon 2026",
    "year": 2026,
    "organiser": "Queen Mary University of London Machine Learning Society (QMML)",
    "opening_date": "19 November 2026",
    "competition_date": "26 November 2026",
    "event_time": "6 pm",
    "venue": "In person at the Mason Lecture Theatre, Bancroft Building, Queen Mary University of London (Mile End), and online",
    "venue_name": "Mason Lecture Theatre, Bancroft Building",
    "eligibility": "University students across universities",
    "team_size": "1–4 participants",
    # Registrants still without a team after this date are matched by the organisers.
    "team_match_deadline": "18 November 2026",
    # Members of allocated teams can remove an unresponsive teammate from this time (London).
    "teammate_removal_opens": "2026-11-19T19:00",
    "round_count_min": 9,
    "round_count_max": 10,
    "status": "registration open",
    "registration_open": True,
    "tickets_url": "https://www.qmsu.org/groups/qmml/",
    # Who you are, which ticket to buy on QMSU, and a short note.
    "ticket_options": (
        ("Queen Mary member", "Early bird ticket", "For Queen Mary students who are QMML members."),
        ("Queen Mary, not a member", "Non-member ticket", "For Queen Mary students who are not QMML members."),
        ("Another university or outside QMUL", "External ticket", "£8 per person. Register as a guest on QMSU to buy it."),
        ("Attending online", "Online ticket", "For anyone taking part remotely instead of in person."),
    ),
    # Current pot in GBP. All ticket revenue is added to it; shown as "£N+".
    "prize_pot_gbp": 400,
    "prize_categories": (
        ("Best overall P&L", ("1st place", "2nd place", "3rd place")),
        ("Best Sortino ratio", ("1st place", "2nd place", "3rd place")),
        ("Special awards", (
            "Best undergraduate team", "Best postgraduate team", "Random team prize",
        )),
    ),
    "partners": ("BCG", "CIRQL", "ENCODE"),
}
