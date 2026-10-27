"""Presentation sections for the QMML 2026 hackathon landing page."""

from html import escape

import streamlit as st

from event_config import EVENT_CONFIG


def _section_heading(label: str, title: str, description: str = "") -> str:
    summary = (
        f'<p class="section-description">{escape(description)}</p>'
        if description
        else ""
    )
    return (
        '<div class="section-heading">'
        f'<p class="eyebrow">{escape(label)}</p>'
        f'<h2>{escape(title)}</h2>{summary}</div>'
    )


def render_hero():
    st.markdown(
        f"""
        <header class="site-nav">
            <a class="brand" href="#top" aria-label="QMML Hackathon home">
                <span class="brand-mark">QMML</span>
                <span>Machine Learning Society<br><small>Queen Mary University of London</small></span>
            </a>
            <nav aria-label="Main navigation">
                <a href="#challenge">The challenge</a>
                <a href="#how-it-works">How it works</a>
                <a href="#prizes">Prizes</a>
                <a href="#partners">Partners</a>
                <a class="nav-cta" href="#register">Take part</a>
            </nav>
        </header>
        <main id="top">
            <section class="hero" aria-labelledby="hero-title">
                <div class="hero-copy">
                    <p class="eyebrow hero-eyebrow">QMML · {EVENT_CONFIG["year"]}</p>
                    <h1 id="hero-title">Make the<br><span>Market.</span></h1>
                    <p class="hero-event">{escape(EVENT_CONFIG["title"])}</p>
                    <p class="hero-description">
                        Build a machine-learning model, quote a market and test your
                        decisions in a live, simulated competition.
                    </p>
                    <a class="button button-blue" href="#how-it-works">Explore the challenge <span aria-hidden="true">↘</span></a>
                </div>
                <aside class="hero-note">
                    <p class="eyebrow">Two dates · In person</p>
                    <div class="hero-date">
                        <span>OPENING CEREMONY</span>
                        <strong>{escape(EVENT_CONFIG["opening_date"])}</strong>
                    </div>
                    <div class="hero-date">
                        <span>LIVE COMPETITION + CLOSING</span>
                        <strong>{escape(EVENT_CONFIG["competition_date"])}</strong>
                    </div>
                    <p class="hero-venue">{escape(EVENT_CONFIG["venue"])}</p>
                </aside>
            </section>
        </main>
        """,
        unsafe_allow_html=True,
    )


def render_stats():
    st.markdown(
        f"""
        <section class="date-strip" aria-label="Event details">
            <div><span class="eyebrow">Who</span><strong>{escape(EVENT_CONFIG["eligibility"])}</strong></div>
            <div><span class="eyebrow">Teams</span><strong>{escape(EVENT_CONFIG["team_size"])}</strong></div>
            <div><span class="eyebrow">Where</span><strong>{escape(EVENT_CONFIG["venue"])}</strong></div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_features():
    st.markdown(
        _section_heading(
            "The challenge",
            "Machine learning meets market making.",
            "Use Python and machine learning to estimate value, then decide how to quote around it. "
            "No quantitative-finance background is required.",
        )
        + """
        <section id="challenge" class="intro-grid">
            <article class="editorial-card">
                <span class="card-index">01</span>
                <h3>Learn from data</h3>
                <p>Study training observations with features and a target. Build a model that estimates the target value.</p>
            </article>
            <article class="editorial-card">
                <span class="card-index">02</span>
                <h3>Make a market</h3>
                <p>For each test observation, submit a fair-value prediction and a bid and ask around that estimate.</p>
            </article>
            <article class="editorial-card">
                <span class="card-index">03</span>
                <h3>Manage the trade-off</h3>
                <p>A tighter spread may be more competitive, but a poor estimate or narrow quote can expose you to adverse outcomes.</p>
            </article>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_timeline():
    rounds = (
        f"About {EVENT_CONFIG['round_count_min']}–"
        f"{EVENT_CONFIG['round_count_max']} datasets or rounds"
    )
    st.markdown(
        _section_heading(
            "From model to market",
            "How the competition works",
            f"{rounds}; the final number is configurable for the event.",
        )
        + f"""
        <section id="how-it-works" class="process-list">
            <article class="process-step">
                <span class="card-index">01</span>
                <div><h3>Build a model</h3><p>Use historical or training data with features and a target variable to train a model.</p></div>
            </article>
            <article class="process-step">
                <span class="card-index">02</span>
                <div><h3>Estimate fair value</h3><p>For each round, receive a testing observation and submit your estimate of its underlying value.</p></div>
            </article>
            <article class="process-step">
                <span class="card-index">03</span>
                <div><h3>Quote bid and ask</h3><p><strong>Bid</strong> is the price at which you are willing to buy; <strong>ask</strong> is the price at which you are willing to sell. The spread is ask minus bid.</p></div>
            </article>
            <article class="process-step">
                <span class="card-index">04</span>
                <div><h3>Compete as market makers</h3><p>The team with the smallest eligible spread becomes market maker for the round, subject to the competition's allocation rules. Other teams trade against it in a live simulation.</p></div>
            </article>
            <article class="process-step">
                <span class="card-index">05</span>
                <div><h3>Adapt and compete</h3><p>Adjust predictions, spreads and strategy as the competition progresses and leaderboard information becomes available. Performance is assessed using the event's specified simulated-trading outcomes and metrics.</p></div>
            </article>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_code_terminal():
    st.markdown(
        """
        <section class="quote-explainer" aria-label="Bid, ask and spread definitions">
            <div>
                <p class="eyebrow">A simple example</p>
                <h2>Quote around your estimate.</h2>
                <p>Your fair-value estimate is the centre of your decision—not a guaranteed market price. Balance a competitive quote against the risk that your estimate is wrong.</p>
            </div>
            <div class="quote-terms">
                <p><span>BUY</span><strong>Bid</strong><small>Price at which your team is willing to buy.</small></p>
                <p><span>SELL</span><strong>Ask</strong><small>Price at which your team is willing to sell.</small></p>
                <p class="quote-spread"><span>ASK − BID</span><strong>Spread</strong><small>The distance between your ask and bid.</small></p>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_leaderboard():
    st.markdown(
        _section_heading(
            "Competition status",
            "The 2026 leaderboard starts empty.",
            "No previous-event rankings are carried into this competition. Results will be shown when the live competition and its data are available.",
        )
        + """
        <section class="empty-board" aria-live="polite">
            <span class="eyebrow">AI MARKET-MAKING HACKATHON · 2026</span>
            <strong>No 2026 results yet</strong>
            <span>Leaderboard entries will appear during the competition.</span>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_who():
    st.markdown(
        _section_heading(
            "Who can take part",
            "Bring your curiosity. Learn the market.",
            "Open to university students across universities. Teams of two to four participants are intended.",
        )
        + """
        <section id="who-can-join" class="participation-grid">
            <div><span class="card-index">A</span><h3>Python and ML</h3><p>Build and refine a model from data. You do not need prior quantitative-finance experience.</p></div>
            <div><span class="card-index">B</span><h3>Team strategy</h3><p>Work together to choose predictions and quotes, then adapt your approach as the simulated competition unfolds.</p></div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_prizes():
    st.markdown(
        _section_heading(
            "Prizes",
            EVENT_CONFIG["prize_details"],
            "The 2026 prize structure has not been confirmed. No cash amounts or awards are being advertised as guaranteed.",
        )
        + """
        <section id="prizes" class="prize-note">
            <span class="eyebrow">DETAILS TO FOLLOW</span>
            <p>Prize categories and any amounts will be published here once confirmed.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_hype():
    st.markdown(
        """
        <section class="simulation-note">
            <p class="eyebrow">A simulated competition</p>
            <h2>Compete on strategy, not capital.</h2>
            <p>This is a competitive, simulated, zero-sum trading game: under the simulation's accounting rules, one team's gains correspond to other teams' losses. No real capital is traded.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_partners():
    partners = "".join(
        f'<span class="partner-name">{escape(name)}</span>'
        for name in EVENT_CONFIG["partners"]
    )
    st.markdown(
        _section_heading(
            "QMML Society Partners",
            "Supported by our wider community.",
        )
        + f"""
        <section id="partners" class="partners-list" aria-label="QMML Society Partners">
            {partners}
        </section>
        <p class="partner-disclaimer">Society partner recognition does not confirm event sponsorship, prize funding or specific benefits for this hackathon.</p>
        """,
        unsafe_allow_html=True,
    )


def render_cta():
    call_to_action = (
        f'<a class="button button-blue" href="{escape(EVENT_CONFIG["registration_url"])}">Register interest</a>'
        if EVENT_CONFIG["registration_open"] and EVENT_CONFIG["registration_url"]
        else '<span class="registration-status">Registration details to be announced</span>'
    )
    st.markdown(
        f"""
        <section class="closing-cta">
            <p class="eyebrow">AI Market-Making Hackathon 2026</p>
            <h2>Ready to make the market?</h2>
            <p>Join students from universities across the UK for a hands-on, simulated market-making challenge.</p>
            {call_to_action}
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_footer():
    st.markdown(
        """
        <footer class="site-footer">
            <a class="brand" href="https://www.qmul.ac.uk/" target="_blank" rel="noreferrer">
                <span class="brand-mark">QMML</span>
                <span>Machine Learning Society<br><small>Queen Mary University of London</small></span>
            </a>
            <span>© 2026 Queen Mary University of London Machine Learning Society</span>
        </footer>
        """,
        unsafe_allow_html=True,
    )
