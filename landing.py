"""QMML AI Market-Making Hackathon 2026 landing page."""

import streamlit as st
from pathlib import Path
from event_config import EVENT_CONFIG

# ── Page Config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title=f"{EVENT_CONFIG['title']} | QMML",
    layout="wide",
    page_icon="M",
    initial_sidebar_state="collapsed",
)

# ── Load CSS ──────────────────────────────────────────────────────────────────

css_path = Path(__file__).parent / "styles.css"
st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

# ── Import & Render Sections ─────────────────────────────────────────────────

from event_sections import (
    render_hero,
    render_stats,
    render_features,
    render_timeline,
    render_quote_lab,
    render_who,
    render_prizes,
    render_partners,
    render_footer,
)
from components import render_registration, render_team_formation, render_registered_teams

render_hero()
render_stats()
render_features()
render_timeline()
render_quote_lab()
render_who()
render_prizes()
render_registration()
if EVENT_CONFIG["registration_open"]:
    if st.toggle("Already registered? Find or manage your team", key="show_team_hub"):
        from sheets_store import STORAGE_ERRORS

        try:
            render_team_formation()
            render_registered_teams()
        except STORAGE_ERRORS:
            st.error("The Team Hub cannot reach registration storage. Please try again later.")
render_partners()
render_footer()
