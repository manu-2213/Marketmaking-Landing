"""Editorial presentation for the QMML hackathon."""

from html import escape

import streamlit as st

from event_config import EVENT_CONFIG


def _section_heading(label, title, description=""):
    return (
        '<div class="section-heading">'
        f'<p class="eyebrow">{escape(label)}</p>'
        f'<h2>{escape(title)}</h2>'
        f'<p class="section-description">{escape(description)}</p></div>'
    )


def render_hero():
    registration_label = "Registration open" if EVENT_CONFIG["registration_open"] else "Coming soon"
    st.html(
        f"""
<nav class="site-nav" aria-label="Main navigation">
    <a class="brand" href="#top"><span class="brand-mark">QMML<span>/</span></span>
    <span class="brand-caption">Machine Learning Society<br>Queen Mary University of London</span></a>
    <div class="nav-links"><a href="#challenge">The challenge</a><a href="#how-it-works">How it works</a>
    <a class="nav-cta" href="#register">Register <span aria-hidden="true">↗</span></a></div>
</nav>
<section class="hero" id="top" aria-label="AI Market-Making Hackathon 2026">
    <div class="hero-copy">
        <p class="eyebrow"><span class="status-dot"></span> {registration_label} / November 2026</p>
        <p class="hero-event">{escape(EVENT_CONFIG["title"])}</p>
        <h1>Make the<br><span class="market-accent">Market.</span></h1>
        <p class="hero-description">Your model. Your market.<br>Turn machine learning into a competitive edge.</p>
        <div class="hero-actions"><a class="button button-blue" href="#register">Register now <span aria-hidden="true">↗</span></a>
        <a class="text-link" href="#challenge">Explore the challenge <span aria-hidden="true">↓</span></a></div>
    </div>
    <aside class="event-pass" aria-label="Event dates">
        <div class="pass-header"><span>THE 2026 EDITION</span><span>IN PERSON</span></div>
        <div class="pass-date"><span class="date-number">19</span><div><span class="date-month">NOVEMBER 2026</span>
        <h2>Opening<br>ceremony</h2><p>{escape(EVENT_CONFIG["opening_date"])}</p></div></div>
        <div class="pass-date"><span class="date-number">26</span><div><span class="date-month">NOVEMBER 2026</span>
        <h2>Live competition<br>&amp; closing</h2><p>{escape(EVENT_CONFIG["competition_date"])}</p></div></div>
        <div class="pass-footer"><span>QMML / LONDON</span><span>Venue to be announced</span></div>
    </aside>
</section>
""",
    )


def render_stats():
    st.markdown(
        f"""
<section class="detail-strip" aria-label="Participation at a glance">
    <div><span class="eyebrow">01 / The people</span><strong>All universities welcome</strong></div>
    <div><span class="eyebrow">02 / The team</span><strong>{escape(EVENT_CONFIG["team_size"])}</strong></div>
    <div><span class="eyebrow">03 / The starting point</span><strong>Python. ML. Curiosity.</strong></div>
</section>
""", unsafe_allow_html=True,
    )


def render_features():
    st.markdown(
        '<div id="challenge"></div>'
        + _section_heading(
            "01 / The challenge",
            "Build a model. Make a market.",
            "A machine-learning challenge with a strategic twist. Predict an underlying value, "
            "quote a buying and selling price, then put your decisions to the test.",
        )
        + """
<section class="intro-grid">
    <article class="editorial-card"><span class="card-index">01</span><h3>Find the signal.</h3>
    <p>Explore training data, identify useful features and train a model to estimate the target value.</p><span class="card-footer">DATA → PREDICTION</span></article>
    <article class="editorial-card"><span class="card-index">02</span><h3>Price the uncertainty.</h3>
    <p>Choose your bid and ask. A narrow spread is competitive, but leaves less room for a mistaken prediction.</p><span class="card-footer">PREDICTION → QUOTE</span></article>
    <article class="editorial-card"><span class="card-index">03</span><h3>Adapt your strategy.</h3>
    <p>Trade against other teams in a simulated market. Learn from each round and refine your approach.</p><span class="card-footer">QUOTE → COMPETITION</span></article>
</section>
""", unsafe_allow_html=True,
    )


def render_timeline():
    stages = [
        ("Build", "Train your model on historical observations with features and a target."),
        ("Predict", "Receive a testing observation and estimate its underlying fair value."),
        ("Quote", "Submit a bid (buy price) and ask (sell price). Spread = ask − bid."),
        ("Trade", "The smallest eligible spread wins market-maker allocation, subject to the competition's existing rules. Other teams trade against it."),
        ("Refine", "Adjust predictions and spreads as results become available. Performance follows the event's specified metrics."),
    ]
    cards = "".join(
        f'<article class="process-step"><span class="step-number">0{i}</span>'
        f'<h3>{escape(title)}</h3><p>{escape(body)}</p></article>'
        for i, (title, body) in enumerate(stages, 1)
    )
    st.markdown(
        '<div id="how-it-works"></div>'
        + _section_heading(
            "02 / From data to decisions", "Five steps. One competitive market.",
            f"Approximately {EVENT_CONFIG['round_count_min']}–{EVENT_CONFIG['round_count_max']} "
            "datasets or rounds. No quantitative-finance experience required.",
        )
        + f'<section class="process-list">{cards}</section>',
        unsafe_allow_html=True,
    )


def _quote_prices(estimate, spread):
    half_spread = spread / 2
    return estimate - half_spread, estimate + half_spread


def render_quote_lab():
    with st.container(border=True, key="quote_lab"):
        st.markdown(
            """
<div class="quote-lab-heading" id="quote-lab">
    <p class="eyebrow">Interactive sandbox / example only</p>
    <h2>Set your quote.</h2>
    <p>Choose an estimated fair value and spread. See how your bid and ask compare
    with a hypothetical team's spread—no live prices or competition data.</p>
</div>
""",
            unsafe_allow_html=True,
        )
        estimate_col, spread_col, comparison_col = st.columns(3)
        with estimate_col:
            estimate = st.slider(
                "Your estimated fair value",
                min_value=50.0,
                max_value=150.0,
                value=100.0,
                step=1.0,
                key="quote_lab_estimate",
                help="Your model's estimate of the underlying value.",
            )
        with spread_col:
            spread = st.slider(
                "Your spread",
                min_value=0.0,
                max_value=20.0,
                value=4.0,
                step=0.5,
                key="quote_lab_spread",
                help="Ask minus bid. A narrower spread is more competitive, but leaves less room for estimation error.",
            )
        with comparison_col:
            comparison_spread = st.slider(
                "Example comparison spread",
                min_value=0.0,
                max_value=20.0,
                value=5.0,
                step=0.5,
                key="quote_lab_comparison",
                help="Set a hypothetical competing team's spread to compare against.",
            )

        bid, ask = _quote_prices(estimate, spread)
        bid_col, estimate_result_col, ask_col = st.columns(3)
        bid_col.metric("BID / BUY", f"{bid:.1f}")
        estimate_result_col.metric("YOUR ESTIMATE", f"{estimate:.1f}")
        ask_col.metric("ASK / SELL", f"{ask:.1f}")
        if spread < comparison_spread:
            status = "Your example spread is narrower than the comparison."
        elif spread > comparison_spread:
            status = "Your example spread is wider than the comparison."
        else:
            status = "Your example spread matches the comparison."
        st.markdown(
            f'<p class="quote-lab-result"><strong>Spread: {spread:.1f}</strong>'
            f' <span>vs. {comparison_spread:.1f} comparison</span></p>'
            f'<p class="quote-lab-status">{status} A narrower eligible spread may receive '
            "market-maker allocation, subject to the event's competition rules.</p>",
            unsafe_allow_html=True,
        )


def render_who():
    st.markdown(
        """
<section class="participation-grid">
    <div><p class="eyebrow">03 / Made for curious minds</p><h2>You bring the model.<br>Bring your team, too.</h2></div>
    <div><p>Open to university students across universities. A working knowledge of Python
    and machine learning is a great starting point. Finance experience isn't required.</p>
    <p>Already have a team? One representative can register your group of 2–4.
    Coming on your own? Register as looking for teammates and use the Team Hub.</p></div>
</section>
""", unsafe_allow_html=True,
    )


def render_prizes():
    st.markdown(
        f"""
<section class="prize-note" id="prizes"><div><p class="eyebrow">The rewards</p>
    <h3>{escape(EVENT_CONFIG["prize_details"])}</h3></div>
    <p>Confirmed categories and awards will be published here.<br>No prize amounts are confirmed yet.</p></section>
""", unsafe_allow_html=True,
    )


def render_partners():
    names = "".join(f'<span>{escape(name)}</span>' for name in EVENT_CONFIG["partners"])
    st.markdown(
        f"""
<section class="partners-section" id="partners"><p class="eyebrow">QMML Society Partners</p>
    <div class="partners-list">{names}</div>
    <p class="partner-disclaimer">Society partnerships do not imply hackathon sponsorship or prize funding.</p></section>
""", unsafe_allow_html=True,
    )


def render_footer():
    st.markdown(
        f"""
<footer class="site-footer"><div><a class="brand" href="#top">QMML</a>
<p>Queen Mary University of London<br>Machine Learning Society</p></div>
<div class="footer-links"><a href="https://www.qmsu.org/groups/qmml/">The society ↗</a>
<a href="#register">Registration ↗</a><span>© {EVENT_CONFIG["year"]} QMML</span></div></footer>
<p class="simulation-disclaimer">A simulated, zero-sum competition. Under the simulation's accounting rules,
one team's gains correspond to other teams' losses. No real capital is traded.</p>
""", unsafe_allow_html=True,
    )
