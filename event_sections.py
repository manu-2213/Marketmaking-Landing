"""Editorial presentation for the QMML hackathon."""

from html import escape
import random

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


TRADER_QUESTIONS = (
    {
        "difficulty": "Easy", "prompt": "How many minutes are in 24 hours?",
        "answer": 1_440, "unit": "minutes", "estimate": 1_200,
        "maximum": 3_000, "step": 10, "source": "Calculation",
    },
    {
        "difficulty": "Easy", "prompt": "How many faces does a common die have?",
        "answer": 6, "unit": "sides", "estimate": 5,
        "maximum": 12, "step": 1, "source": "Standard die",
    },
    {
        "difficulty": "Medium", "prompt": "How long is Earth's circumference around the equator?",
        "answer": 40_075, "unit": "km", "estimate": 38_000,
        "maximum": 80_000, "step": 500, "source": "NASA Earth fact sheet",
        "url": "https://nssdc.gsfc.nasa.gov/planetary/factsheet/earthfact.html",
    },
    {
        "difficulty": "Medium", "prompt": "How many people lived in Vanuatu in 2023?",
        "answer": 320_409, "unit": "people", "estimate": 300_000,
        "maximum": 600_000, "step": 5_000,
        "source": "World Bank population data · 2023",
        "url": "https://api.worldbank.org/v2/country/VUT/indicator/SP.POP.TOTL?date=2023&format=json",
    },
    {
        "difficulty": "Hard", "prompt": "What is the average distance from Earth to the Moon?",
        "answer": 384_400, "unit": "km", "estimate": 350_000,
        "maximum": 700_000, "step": 5_000, "source": "NASA Moon facts",
        "url": "https://science.nasa.gov/moon/facts/",
    },
    {
        "difficulty": "Hard", "prompt": "How high is Mount Everest above sea level?",
        "answer": 8_849, "unit": "m", "estimate": 8_000,
        "maximum": 15_000, "step": 100,
        "source": "Encyclopaedia Britannica · Mount Everest",
        "url": "https://www.britannica.com/place/Mount-Everest",
    },
)

MAKER_QUESTIONS = (
    {
        "difficulty": "Easy", "prompt": "How many planets are in our Solar System?",
        "answer": 8, "unit": "planets", "estimate": 7,
        "maximum": 16, "step": 1, "source": "NASA · Solar System planets",
        "url": "https://science.nasa.gov/solar-system/planets/",
    },
    {
        "difficulty": "Easy", "prompt": "How many cards are in a standard deck without jokers?",
        "answer": 52, "unit": "cards", "estimate": 48,
        "maximum": 100, "step": 1, "source": "Standard playing-card deck",
    },
    {
        "difficulty": "Medium", "prompt": "How tall is the Eiffel Tower, including its antenna?",
        "answer": 330, "unit": "m", "estimate": 300,
        "maximum": 600, "step": 5, "source": "Eiffel Tower · key figures",
        "url": "https://www.toureiffel.paris/en/the-monument/key-figures",
    },
    {
        "difficulty": "Medium", "prompt": "What is the Moon's circumference?",
        "answer": 10_921, "unit": "km", "estimate": 10_000,
        "maximum": 22_000, "step": 100, "source": "NASA Moon facts",
        "url": "https://science.nasa.gov/moon/facts/",
    },
    {
        "difficulty": "Hard",
        "prompt": "What is the speed of light in a vacuum, in kilometres per second?",
        "answer": 299_792.458, "unit": "km/s", "estimate": 280_000,
        "maximum": 500_000, "step": 1_000, "source": "NIST · speed of light",
        "url": "https://physics.nist.gov/cgi-bin/cuu/Value?c",
    },
    {
        "difficulty": "Hard", "prompt": "How many confirmed moons did Saturn have in March 2025?",
        "answer": 274, "unit": "moons", "estimate": 200,
        "maximum": 500, "step": 5, "source": "NASA · Saturn's moons (March 2025)",
        "url": "https://science.nasa.gov/saturn/moons/",
    },
)


def _quote_prices(estimate, spread):
    half_spread = spread / 2
    return estimate - half_spread, estimate + half_spread


def _maker_quote_result(bid, ask, answer):
    if answer < bid:
        return "below", bid - answer
    if answer > ask:
        return "above", answer - ask
    return "inside", min(answer - bid, ask - answer)


def _session_scenarios(key):
    if key not in st.session_state:
        if key == "trader_scenarios":
            on_target_rounds = [True, True, True, False, False, False]
            random.shuffle(on_target_rounds)
            directions = [random.choice((-1, 1)) for _ in range(6)]
            st.session_state[key] = list(zip(on_target_rounds, directions))
        else:
            actions = ["Buy at ask"] * 3 + ["Sell at bid"] * 3
            random.shuffle(actions)
            st.session_state[key] = actions
    return st.session_state[key]


def _trade_credits(action, bid, ask, answer, shares):
    move_per_share = answer - ask if action == "Buy at ask" else bid - answer
    return round(move_per_share / answer * 100 * shares, 1)


def _display_value(value):
    return f"{value:,.2f}" if not float(value).is_integer() else f"{value:,.0f}"


def _display_round(question, round_index, total, revealed, show_question=True):
    st.progress(
        (round_index + int(revealed)) / total,
        text=f"Round {round_index + 1} of {total}  ·  {question['difficulty']}",
    )
    if show_question:
        st.markdown(
            f'<div class="game-question"><span>{question["difficulty"].upper()} '
            f'QUESTION {round_index + 1:02d} / {total:02d}</span>'
            f'<p>{escape(question["prompt"])}</p></div>',
            unsafe_allow_html=True,
        )


def _display_answer(question):
    st.markdown(
        f'**Answer:** {_display_value(question["answer"])} {question["unit"]}'
    )
    if question.get("url"):
        st.caption(f'Reference: [{question["source"]}]({question["url"]})')
    else:
        st.caption(f'Reference: {question["source"]}')


def _display_round_pnl(role, opponent, user_pnl, opponent_pnl):
    if user_pnl > 0:
        st.success(
            f"You made {user_pnl:+.1f} simulation credits as {role}; "
            f"{opponent} lost {abs(opponent_pnl):.1f}."
        )
    elif user_pnl < 0:
        st.warning(
            f"You lost {abs(user_pnl):.1f} simulation credits as {role}; "
            f"{opponent} made {opponent_pnl:+.1f}."
        )
    else:
        st.info("No P&L this round.")


def _display_running_pnl(results, role, opponent):
    user_total = round(sum(result["user_pnl"] for result in results), 1)
    opponent_total = round(sum(result["opponent_pnl"] for result in results), 1)
    user_col, opponent_col = st.columns(2)
    user_col.metric(f"YOUR P&L · {role.upper()}", f"{user_total:+.1f} credits")
    opponent_col.metric(f"{opponent.upper()} P&L", f"{opponent_total:+.1f} credits")


def _start_game(role):
    for key in list(st.session_state.keys()):
        if key.startswith(f"{role}_"):
            del st.session_state[key]
    st.session_state["quote_lab_role"] = role
    st.session_state[f"{role}_round"] = 0
    st.session_state[f"{role}_results"] = []
    st.session_state[f"{role}_revealed"] = False
    st.rerun()


def _display_game_summary(key, results, role, opponent, other_role):
    _display_running_pnl(results, role, opponent)
    for index, result in enumerate(results):
        with st.expander(
            f'Round {index + 1} · {result["difficulty"]} · {result["prompt"]}'
        ):
            st.markdown(
                f'**Answer:** {_display_value(result["answer"])} {result["unit"]}  ·  '
                f'**Your P&L:** {result["user_pnl"]:+.1f} credits  ·  '
                f'**{opponent} P&L:** {result["opponent_pnl"]:+.1f} credits'
            )
    st.caption("P&L is measured in simulation credits. No real money is involved.")
    replay_col, other_role_col = st.columns(2)
    if replay_col.button(f"Play again as {role}", key=f"{key}_restart"):
        _start_game(key)
    if other_role_col.button(f"Play as {other_role}", key=f"{key}_other_role"):
        _start_game("maker" if key == "trader" else "trader")


def _render_trader_game():
    key = "trader"
    questions = TRADER_QUESTIONS
    round_index = st.session_state.setdefault(f"{key}_round", 0)
    results = st.session_state.setdefault(f"{key}_results", [])
    revealed = st.session_state.setdefault(f"{key}_revealed", False)
    if round_index == len(questions):
        _display_game_summary(
            key, results, "Trader", "Sample market maker", "Market Maker"
        )
        return

    question = questions[round_index]
    _display_running_pnl(results, "Trader", "Sample market maker")
    _display_round(
        question, round_index, len(questions), revealed, show_question=revealed
    )
    if revealed:
        result = results[-1]
        _display_round_pnl(
            "trader", "the sample market maker",
            result["user_pnl"], result["opponent_pnl"],
        )
        st.markdown(
            f'**Trade:** {result["action"]}  ·  **Shares:** {result["shares"]}'
        )
        _display_answer(question)
        if st.button("Next question", key=f"{key}_next_{round_index}"):
            st.session_state[f"{key}_round"] += 1
            st.session_state[f"{key}_revealed"] = False
            st.rerun()
        return

    maker_on_target, direction = _session_scenarios("trader_scenarios")[round_index]
    answer = question["answer"]
    spread = answer * 0.1
    center = answer if maker_on_target else answer + direction * 2 * spread
    bid, ask = _quote_prices(center, spread)
    bid_col, ask_col = st.columns(2)
    bid_col.metric("BID · SELL", _display_value(bid))
    ask_col.metric("ASK · BUY", _display_value(ask))
    action = st.radio(
        "Your trade",
        ("Buy at ask", "Sell at bid"),
        horizontal=True,
        key=f"{key}_action_{round_index}",
    )
    shares = st.slider(
        "Number of shares",
        min_value=1,
        max_value=5,
        value=2,
        help="Choose fewer shares when unsure and more when confident.",
        key=f"{key}_shares_{round_index}",
    )
    if st.button("Place trade", key=f"{key}_lock_{round_index}"):
        user_pnl = _trade_credits(action, bid, ask, answer, shares)
        results.append(
            {
                "prompt": question["prompt"],
                "difficulty": question["difficulty"],
                "answer": answer,
                "unit": question["unit"],
                "action": action,
                "shares": shares,
                "user_pnl": user_pnl,
                "opponent_pnl": -user_pnl,
                "maker_on_target": maker_on_target,
            }
        )
        st.session_state[f"{key}_revealed"] = True
        st.rerun()


def _render_maker_game():
    key = "maker"
    questions = MAKER_QUESTIONS
    round_index = st.session_state.setdefault(f"{key}_round", 0)
    results = st.session_state.setdefault(f"{key}_results", [])
    revealed = st.session_state.setdefault(f"{key}_revealed", False)
    if round_index == len(questions):
        _display_game_summary(
            key, results, "Market maker", "Sample trader", "Trader"
        )
        return

    question = questions[round_index]
    _display_running_pnl(results, "Market maker", "Sample trader")
    _display_round(question, round_index, len(questions), revealed)
    if revealed:
        result = results[-1]
        position, distance = _maker_quote_result(
            result["bid"], result["ask"], result["answer"]
        )
        if position == "inside":
            st.success(
                f"Inside your spread. The answer was "
                f"{_display_value(distance)} {question['unit']} from the nearest edge."
            )
        else:
            side = "below your bid" if position == "below" else "above your ask"
            st.warning(
                f"Outside your spread. The answer was "
                f"{_display_value(distance)} {question['unit']} {side}."
            )
        _display_round_pnl(
            "market maker", "the sample trader",
            result["user_pnl"], result["opponent_pnl"],
        )
        st.markdown(
            f'**Sample trader:** {result["action"]}  ·  '
            f'**Your quote:** {_display_value(result["bid"])} bid / '
            f'{_display_value(result["ask"])} ask'
        )
        _display_answer(question)
        if st.button("Next question", key=f"{key}_next_{round_index}"):
            st.session_state[f"{key}_round"] += 1
            st.session_state[f"{key}_revealed"] = False
            st.rerun()
        return

    step = question["step"]
    minimum = max(step, int(question["answer"] * 0.5 // step) * step)
    maximum = int((question["answer"] * 1.5 + step - 1) // step) * step
    estimate = st.slider(
        "Your fair-value estimate",
        min_value=minimum,
        max_value=maximum,
        value=question["estimate"],
        step=step,
        key=f"{key}_estimate_{round_index}",
    )
    spread_pct = st.slider(
        "Your spread",
        min_value=2,
        max_value=30,
        value=10,
        step=1,
        help="The total bid-to-ask gap as a percentage of your estimate.",
        key=f"{key}_spread_{round_index}",
    )
    bid, ask = _quote_prices(estimate, estimate * spread_pct / 100)
    bid_col, ask_col = st.columns(2)
    bid_col.metric("YOUR BID", f'{_display_value(bid)} {question["unit"]}')
    ask_col.metric("YOUR ASK", f'{_display_value(ask)} {question["unit"]}')
    if st.button("Lock quote & reveal answer", key=f"{key}_lock_{round_index}"):
        action = _session_scenarios("maker_scenarios")[round_index]
        trader_pnl = _trade_credits(action, bid, ask, question["answer"], 1)
        maker_pnl = round(-trader_pnl, 1)
        results.append(
            {
                "prompt": question["prompt"],
                "difficulty": question["difficulty"],
                "answer": question["answer"],
                "unit": question["unit"],
                "bid": bid,
                "ask": ask,
                "action": action,
                "user_pnl": maker_pnl,
                "opponent_pnl": trader_pnl,
            }
        )
        st.session_state[f"{key}_revealed"] = True
        st.rerun()


def render_quote_lab():
    with st.container(border=True, key="quote_lab"):
        st.markdown(
            """
<div class="quote-lab-heading" id="quote-lab">
    <p class="eyebrow">A six-round market simulation</p>
    <h2>Step into the market.</h2>
    <p>Choose your role, make a decision each round, and watch your P&amp;L update.</p>
</div>
""",
            unsafe_allow_html=True,
        )
        role = st.session_state.get("quote_lab_role")
        if role is None:
            st.markdown(
                '<div class="game-role-intro"><p>Choose how you want to play.</p>'
                '<span>Both roles run for six rounds.</span></div>',
                unsafe_allow_html=True,
            )
            trader_col, maker_col = st.columns(2)
            with trader_col:
                st.markdown(
                    '<div class="game-role-card"><span>01 / TRADER</span>'
                    '<p>See the bid and ask. Choose a side and share count.</p></div>',
                    unsafe_allow_html=True,
                )
                if st.button("Play as Trader", key="quote_lab_start_trader"):
                    _start_game("trader")
            with maker_col:
                st.markdown(
                    '<div class="game-role-card"><span>02 / MARKET MAKER</span>'
                    '<p>Set your estimate and spread against a sample trader.</p></div>',
                    unsafe_allow_html=True,
                )
                if st.button("Play as Market Maker", key="quote_lab_start_maker"):
                    _start_game("maker")
        elif role == "trader":
            st.markdown(
                "Each round, choose whether to buy at the ask or sell at the bid, "
                "then set your share count."
            )
            _render_trader_game()
        elif role == "maker":
            st.markdown(
                "Set a fair-value estimate and spread. A sample trader will take one side."
            )
            _render_maker_game()
        st.caption(
            "P&L uses simulation credits (percentage price move × shares). "
            "No real money or live market data."
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
