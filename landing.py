"""Market-Making AI Hackathon — Landing Page"""

import streamlit as st
from pathlib import Path

# ── Page Config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Market-Making AI Hackathon",
    layout="wide",
    page_icon="📈",
    initial_sidebar_state="collapsed",
)

# ── Load CSS ──────────────────────────────────────────────────────────────────

css_path = Path(__file__).parent / "styles.css"
st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

# ── Import & Render Sections ─────────────────────────────────────────────────

from components import (
    render_hero,
    render_stats,
    render_features,
    render_timeline,
    render_code_terminal,
    render_leaderboard,
    render_who,
    render_prizes,
    render_hype,
    render_registration,
    render_faq,
    render_cta,
    render_footer,
)

render_hero()
render_stats()
render_features()
render_timeline()
render_code_terminal()
render_leaderboard()
render_who()
render_prizes()
render_hype()
render_registration()
render_faq()
render_cta()
render_footer()
