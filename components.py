"""Section components for the Market-Making AI Hackathon landing page."""

import streamlit as st
import random
from datetime import datetime, timezone

import gspread
from google.oauth2.service_account import Credentials


# ── Google Sheets persistence ─────────────────────────────────────────────────

_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

@st.cache_resource(ttl=300)
def _get_gsheet():
    """Return the first worksheet of the configured Google Sheet."""
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=_SCOPES
    )
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(st.secrets["sheets"]["spreadsheet_id"])
    ws = sh.sheet1
    # Ensure header row exists
    if not ws.row_values(1):
        ws.append_row(
            ["timestamp", "name", "email", "university", "degree",
             "team_name", "team_size", "experience", "interest"]
        )
    return ws


def _save_registration(name, email, university, degree, team_name,
                        team_size, experience, interest):
    """Append a registration row to Google Sheets."""
    ws = _get_gsheet()
    ws.append_row([
        datetime.now(timezone.utc).isoformat(),
        name, email, university, degree,
        team_name, team_size, experience, interest,
    ])


@st.cache_data(ttl=120)
def get_team_count():
    """Count total registrations (rows after the header)."""
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=_SCOPES
        )
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(st.secrets["sheets"]["spreadsheet_id"])
        ws = sh.sheet1
        all_rows = ws.get_all_values()
        return max(len(all_rows) - 1, 0)  # subtract header row
    except Exception:
        return 0


# ── Helpers ────────────────────────────────────────────────────────────────────

def _generate_candlestick_html():
    random.seed(42)
    candles = ""
    for i in range(25):
        is_green = random.random() > 0.45
        body_h = random.randint(8, 35)
        wick_top = random.randint(3, 15)
        wick_bot = random.randint(3, 12)
        color_class = "candle-green" if is_green else "candle-red"
        delay = round(i * 0.12, 2)
        candles += (
            f'<div class="candle {color_class}" style="animation-delay:{delay}s">'
            f'<div class="candle-wick" style="height:{wick_top}px"></div>'
            f'<div class="candle-body" style="height:{body_h}px"></div>'
            f'<div class="candle-wick" style="height:{wick_bot}px"></div>'
            f"</div>"
        )
    return candles


def _generate_pnl_svg():
    random.seed(7)
    points = []
    y = 20.0
    for x in range(0, 300, 6):
        y += random.uniform(-3, 3.5)
        y = max(5, min(38, y))
        points.append(f"{x},{40 - y:.1f}")
    path = "M" + " L".join(points)
    return f"""
    <svg class="pnl-svg" viewBox="0 0 300 40" preserveAspectRatio="none">
        <defs>
            <linearGradient id="pnlGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" style="stop-color:#00f0ff;stop-opacity:0.8"/>
                <stop offset="100%" style="stop-color:#34d399;stop-opacity:0.8"/>
            </linearGradient>
            <linearGradient id="pnlFill" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" style="stop-color:#00f0ff;stop-opacity:0.15"/>
                <stop offset="100%" style="stop-color:#00f0ff;stop-opacity:0"/>
            </linearGradient>
        </defs>
        <path d="{path} L300,40 L0,40 Z" fill="url(#pnlFill)" />
        <path d="{path}" fill="none" stroke="url(#pnlGrad)" stroke-width="1.5"/>
    </svg>"""


# ── Sections ──────────────────────────────────────────────────────────────────


def render_hero():
    hero_left, hero_right = st.columns([1.15, 0.85], gap="large")

    with hero_left:
        st.markdown("""
        <div class="hero-container">
            <div class="hero-bg"></div>
            <div class="hero-content">
                <div class="hero-badge">Machine Learning Society &times; Queen Mary University of London</div>
                <div class="hero-title">THE MARKET-MAKING<br>AI HACKATHON</div>
                <div class="hero-subtitle">Build AI trading agents. Compete live. Win big.</div>
                <div class="hero-desc">
                    Design a machine learning market-making algorithm that battles other teams
                    in a live simulated financial market. One week. Real strategies. One leaderboard.
                </div>
                <div style="display:flex;flex-wrap:wrap;gap:14px;margin-top:8px;">
                    <a href="#register" class="btn-primary">Register Your Team</a>
                    <a href="#register" class="btn-secondary">Show Interest</a>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with hero_right:
        candles = _generate_candlestick_html()
        pnl = _generate_pnl_svg()
        st.markdown(f"""
        <div style="padding-top:12vh;">
        <div class="trading-dash">
            <div class="dash-header">
                <div class="dash-title">AI Trading Arena</div>
                <div class="dash-live"><div class="live-dot"></div> LIVE</div>
            </div>
            <div class="candlestick-chart">{candles}</div>
            <div class="order-book">
                <div class="ob-side ob-bid">
                    <div class="ob-label">Best Bid</div>
                    <div class="ob-price">&pound;102.45</div>
                    <div style="font-size:0.6rem;color:var(--text-muted);margin-top:2px;">Size: 2,340</div>
                </div>
                <div class="ob-side ob-ask">
                    <div class="ob-label">Best Ask</div>
                    <div class="ob-price">&pound;102.52</div>
                    <div style="font-size:0.6rem;color:var(--text-muted);margin-top:2px;">Size: 1,890</div>
                </div>
            </div>
            <div class="pnl-line">{pnl}</div>
            <div class="pnl-label">
                <span>P&amp;L CURVE</span>
                <span class="pnl-value">+&pound;8,240</span>
            </div>
        </div>
        </div>
        """, unsafe_allow_html=True)


def render_stats():
    _count = get_team_count()
    _teams_text = str(_count)
    st.markdown(f"""
    <div class="stats-banner">
        <div class="stat-card">
            <div class="stat-number">&pound;300</div>
            <div class="stat-label">Prize Pool</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{_teams_text}</div>
            <div class="stat-label">Teams Signed Up</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">LIVE</div>
            <div class="stat-label">AI vs AI Trading Arena</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">QMUL</div>
            <div class="stat-label">Machine Learning Society</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_features():
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center;margin-bottom:50px;">
        <div class="section-tag">What Makes Us Different</div>
        <div class="section-title">Not Your Typical Hackathon</div>
        <div class="section-subtitle" style="margin:0 auto;">
            This isn't about building apps in 24 hours. Your AI trades against other AIs
            in a live simulated market for one week.
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3, gap="medium")

    with c1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon feature-icon-1">📈</div>
            <div class="feature-title">Live AI Trading Arena</div>
            <div class="feature-desc">
                Your ML agent acts as a market maker, quoting bids and asks in real time.
                During the finals, all agents trade head-to-head in a simulated financial market.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon feature-icon-2">🎤</div>
            <div class="feature-title">Real Quant Inspiration</div>
            <div class="feature-desc">
                The closing ceremony features a talk by a <strong>Quant / ML Researcher</strong> on ML applications in real-world trading and finance.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon feature-icon-3">🏅</div>
            <div class="feature-title">Real-Time Leaderboard</div>
            <div class="feature-desc">
                A live leaderboard tracks every agent's P&amp;L as they trade.
                Watch your algorithm climb the rankings in real time during the finals.
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_timeline():
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center;margin-bottom:30px;">
        <div class="section-tag">The Journey</div>
        <div class="section-title">How It Works</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="timeline-stepper">
        <div class="step">
            <div class="step-icon step-icon-1">⚡</div>
            <div class="step-date step-date-1">MAR 25</div>
            <div class="step-title">Kickoff</div>
            <div class="step-sub">Opening ceremony at QMUL</div>
        </div>
        <div class="step">
            <div class="step-icon step-icon-2">🧠</div>
            <div class="step-date step-date-2">MAR 26 – 31</div>
            <div class="step-title">Build Week</div>
            <div class="step-sub">Design &amp; train your agent</div>
        </div>
        <div class="step">
            <div class="step-icon step-icon-3">📈</div>
            <div class="step-date step-date-3">APR 1</div>
            <div class="step-title">Live Finals</div>
            <div class="step-sub">Agents trade head-to-head</div>
        </div>
        <div class="step">
            <div class="step-icon step-icon-4">🎤</div>
            <div class="step-date step-date-4">APR 1</div>
            <div class="step-title">Quant Talk</div>
            <div class="step-sub">Quant / ML Researcher talk</div>
        </div>
        <div class="step">
            <div class="step-icon step-icon-5">🏆</div>
            <div class="step-date step-date-5">APR 1</div>
            <div class="step-title">Awards</div>
            <div class="step-sub">Winners announced live</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_code_terminal():
    st.markdown("<br>", unsafe_allow_html=True)
    left, right = st.columns([1, 1.2], gap="large")

    with left:
        st.markdown("""
        <div style="padding:40px 0;">
            <div class="section-tag">Your Code, Your Strategy</div>
            <div class="section-title" style="font-size:2.6rem;">Build Your<br>Trading Agent</div>
            <div style="font-size:1.15rem;color:var(--text-secondary);line-height:1.7;margin-top:16px;margin-bottom:28px;">
                Write a Python class that quotes bid and ask prices.
                We handle the exchange simulation &mdash; you bring the strategy.
            </div>
            <div style="display:flex;flex-direction:column;gap:14px;">
                <div style="display:flex;align-items:center;gap:12px;">
                    <div style="width:8px;height:8px;border-radius:50%;background:var(--accent);flex-shrink:0;"></div>
                    <span style="font-size:1.05rem;color:var(--text-secondary);">Starter code &amp; datasets provided</span>
                </div>
                <div style="display:flex;align-items:center;gap:12px;">
                    <div style="width:8px;height:8px;border-radius:50%;background:var(--accent2);flex-shrink:0;"></div>
                    <span style="font-size:1.05rem;color:var(--text-secondary);">Use any ML library you want</span>
                </div>
                <div style="display:flex;align-items:center;gap:12px;">
                    <div style="width:8px;height:8px;border-radius:50%;background:var(--accent3);flex-shrink:0;"></div>
                    <span style="font-size:1.05rem;color:var(--text-secondary);">Test locally, deploy to the arena</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with right:
        st.markdown("""
        <div class="terminal">
            <div class="terminal-bar">
                <div class="terminal-dot dot-red"></div>
                <div class="terminal-dot dot-yellow"></div>
                <div class="terminal-dot dot-green"></div>
                <div class="terminal-title">agent.py</div>
            </div>
            <div class="terminal-body">
                <div class="code-line"><span class="code-keyword">class</span> <span class="code-class">MarketMaker</span><span class="code-op">:</span></div>
                <div class="code-line">    <span class="code-keyword">def</span> <span class="code-func">__init__</span><span class="code-op">(</span><span class="code-self">self</span><span class="code-op">,</span> <span class="code-param">spread</span><span class="code-op">=</span><span class="code-number">0.02</span><span class="code-op">):</span></div>
                <div class="code-line">        <span class="code-self">self</span><span class="code-op">.</span>spread <span class="code-op">=</span> spread</div>
                <div class="code-line">        <span class="code-self">self</span><span class="code-op">.</span>position <span class="code-op">=</span> <span class="code-number">0</span></div>
                <div class="code-line">&nbsp;</div>
                <div class="code-line">    <span class="code-keyword">def</span> <span class="code-func">get_quotes</span><span class="code-op">(</span><span class="code-self">self</span><span class="code-op">,</span> <span class="code-param">mid_price</span><span class="code-op">):</span></div>
                <div class="code-line">        bid <span class="code-op">=</span> mid_price <span class="code-op">*</span> <span class="code-op">(</span><span class="code-number">1</span> <span class="code-op">-</span> <span class="code-self">self</span><span class="code-op">.</span>spread<span class="code-op">)</span></div>
                <div class="code-line">        ask <span class="code-op">=</span> mid_price <span class="code-op">*</span> <span class="code-op">(</span><span class="code-number">1</span> <span class="code-op">+</span> <span class="code-self">self</span><span class="code-op">.</span>spread<span class="code-op">)</span></div>
                <div class="code-line">        <span class="code-keyword">return</span> <span class="code-op">{</span><span class="code-string">"bid"</span><span class="code-op">:</span> bid<span class="code-op">,</span> <span class="code-string">"ask"</span><span class="code-op">:</span> ask<span class="code-op">}</span></div>
                <div class="code-line">&nbsp;</div>
                <div class="code-line">    <span class="code-keyword">def</span> <span class="code-func">on_trade</span><span class="code-op">(</span><span class="code-self">self</span><span class="code-op">,</span> <span class="code-param">side</span><span class="code-op">,</span> <span class="code-param">price</span><span class="code-op">,</span> <span class="code-param">size</span><span class="code-op">):</span></div>
                <div class="code-line">        <span class="code-keyword">if</span> side <span class="code-op">==</span> <span class="code-string">"buy"</span><span class="code-op">:</span></div>
                <div class="code-line">            <span class="code-self">self</span><span class="code-op">.</span>position <span class="code-op">+=</span> size</div>
                <div class="code-line">&nbsp;</div>
                <div class="code-line"><span class="code-comment"># Deploy to the arena</span></div>
                <div class="code-line">agent <span class="code-op">=</span> <span class="code-class">MarketMaker</span><span class="code-op">(</span><span class="code-param">spread</span><span class="code-op">=</span><span class="code-number">0.015</span><span class="code-op">)</span><span class="cursor-blink"></span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_leaderboard():
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center;margin-bottom:40px;">
        <div class="section-tag">Leaderboard</div>
        <div class="section-title">Your Algorithm vs The Market</div>
        <div class="section-subtitle" style="margin:0 auto;">
            A live leaderboard tracks every agent's performance. Can your AI reach the top?
        </div>
    </div>
    """, unsafe_allow_html=True)

    top_rows = [
        ("🥇", "1", "var(--gold)", "Alpha Traders", "Adaptive Spread", "+£8,240", "rgba(251,191,36,0.2)"),
        ("🥈", "2", "#c0c0c0", "Neural Liquidity", "Deep RL Market Maker", "+£7,910", "rgba(192,192,192,0.15)"),
        ("🥉", "3", "#cd7f32", "Quantum Makers", "Mean-Reversion MM", "+£6,870", "rgba(205,127,50,0.15)"),
    ]
    faded_rows = [
        ("4", "ByteTraders", "Inventory Optimiser", "+£5,430", "0.6"),
        ("5", "Sigma Flow", "Statistical Arbitrage", "+£4,820", "0.45"),
    ]

    html = '<div style="max-width:800px;margin:0 auto;">'
    html += '<div class="lb-header"><div>Rank</div><div>Team</div><div>Strategy</div><div style="text-align:right;">Profit</div></div>'

    for emoji, rank, color, team, strat, profit, border in top_rows:
        html += (
            f'<div class="lb-row" style="border:1px solid {border};">'
            f'<div class="lb-rank" style="color:{color};">{emoji} {rank}</div>'
            f'<div class="lb-team">{team}</div>'
            f'<div class="lb-strategy">{strat}</div>'
            f'<div class="lb-profit">{profit}</div>'
            f"</div>"
        )

    for rank, team, strat, profit, opacity in faded_rows:
        html += (
            f'<div class="lb-row" style="border:1px solid var(--border);opacity:{opacity};">'
            f'<div style="font-family:\'JetBrains Mono\',monospace;color:var(--text-muted);">{rank}</div>'
            f'<div class="lb-team">{team}</div>'
            f'<div class="lb-strategy" style="color:var(--text-muted);">{strat}</div>'
            f'<div class="lb-profit">{profit}</div>'
            f"</div>"
        )

    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def render_who():
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center;margin-bottom:40px;">
        <div class="section-tag">Open to All</div>
        <div class="section-title">Who Should Join?</div>
    </div>
    """, unsafe_allow_html=True)

    wl, wr = st.columns([1, 1], gap="large")

    with wl:
        st.markdown("""
        <div style="display:flex;flex-wrap:wrap;gap:8px;justify-content:center;padding:20px 0;">
            <span class="who-tag">🧠 ML Enthusiasts</span>
            <span class="who-tag">💻 CS Students</span>
            <span class="who-tag">📊 Aspiring Quants</span>
            <span class="who-tag">🔬 Data Scientists</span>
            <span class="who-tag">📈 Finance Students</span>
            <span class="who-tag">🎯 Algo Trading Curious</span>
            <span class="who-tag">🐍 Python Devs</span>
            <span class="who-tag">🤖 AI Enthusiasts</span>
        </div>
        """, unsafe_allow_html=True)

    with wr:
        st.markdown("""
        <div style="padding:28px 32px;background:var(--surface);border:1px solid var(--border);border-radius:20px;">
            <div style="font-size:1.3rem;font-weight:700;color:var(--text);margin-bottom:14px;">
                No finance background needed.
            </div>
            <div style="font-size:1.05rem;color:var(--text-secondary);line-height:1.65;margin-bottom:20px;">
                We provide starter code, datasets, and everything you need.
                If you can write Python, you can compete.
            </div>
            <div style="display:flex;gap:16px;">
                <div style="padding:14px 20px;background:var(--surface2);border:1px solid var(--border);border-radius:12px;text-align:center;flex:1;">
                    <div style="font-family:'Orbitron',sans-serif;font-size:1.5rem;font-weight:700;color:var(--accent);">2–4</div>
                    <div style="font-size:0.85rem;color:var(--text-muted);margin-top:4px;">Per Team</div>
                </div>
                <div style="padding:14px 20px;background:var(--surface2);border:1px solid var(--border);border-radius:12px;text-align:center;flex:1;">
                    <div style="font-family:'Orbitron',sans-serif;font-size:1.5rem;font-weight:700;color:var(--accent2);">7</div>
                    <div style="font-size:0.85rem;color:var(--text-muted);margin-top:4px;">Days to Build</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_prizes():
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center;margin-bottom:40px;">
        <div class="section-tag">Rewards</div>
        <div class="section-title">Prizes</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="prize-banner">
        <div style="font-size:3.5rem;margin-bottom:16px;">🏆</div>
        <div class="prize-title">&pound;300 PRIZE POOL</div>
        <div class="prize-sub">Cash prizes, special awards, and bragging rights.</div>
        <div class="prize-categories">
            <span class="prize-cat" style="background:rgba(0,240,255,0.08);border:1px solid rgba(0,240,255,0.25);color:#67e8f9;">Top 3 Teams</span>
            <span class="prize-cat" style="background:rgba(167,139,250,0.08);border:1px solid rgba(167,139,250,0.25);color:#c4b5fd;">Best Strategy</span>
            <span class="prize-cat" style="background:rgba(244,114,182,0.08);border:1px solid rgba(244,114,182,0.25);color:#f9a8d4;">Most Creative</span>
            <span class="prize-cat" style="background:rgba(251,191,36,0.08);border:1px solid rgba(251,191,36,0.25);color:#fde68a;">Rookie Team</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_hype():
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div class="hype-section">
        <div class="hype-title">The Ultimate AI Trading Challenge</div>
        <div class="hype-sub">
            Your algorithm. Dozens of opponents. A live financial market.<br>
            The market decides who wins.
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_registration():
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div id="register"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center;margin-bottom:40px;">
        <div class="section-tag">Join Now</div>
        <div class="section-title">Register Interest</div>
        <div class="section-subtitle" style="margin:0 auto;">
            Sign up to receive updates and secure your team's spot.
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("registration_form", clear_on_submit=True):
        fc1, fc2 = st.columns(2, gap="medium")
        with fc1:
            reg_name = st.text_input("Full Name *")
            reg_uni = st.text_input("University *")
            reg_team = st.text_input("Team Name (optional)")
            reg_experience = st.selectbox(
                "ML Experience Level",
                ["Beginner", "Intermediate", "Advanced", "Expert"],
            )
        with fc2:
            reg_email = st.text_input("Email *")
            reg_degree = st.text_input("Degree / Background")
            reg_team_size = st.selectbox("Team Size", ["1 (looking for a team)", "2", "3", "4"])
            reg_interest = st.text_area("Why are you interested?", height=108)

        submitted = st.form_submit_button("Register Interest", use_container_width=True)

        if submitted:
            if reg_name and reg_email:
                try:
                    _save_registration(
                        reg_name, reg_email, reg_uni, reg_degree,
                        reg_team, reg_team_size, reg_experience, reg_interest,
                    )
                    st.success("**You're in!** We'll send you updates soon.")
                    st.balloons()
                except Exception as exc:
                    st.error(f"Registration failed: {exc}")
            else:
                st.warning("Please fill in at least your name and email.")


def render_faq():
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center;margin-bottom:40px;">
        <div class="section-tag">Questions</div>
        <div class="section-title">FAQ</div>
    </div>
    """, unsafe_allow_html=True)

    faqs = [
        ("Do I need finance experience?",
         "Not at all. We provide all resources, starter code, and datasets. If you can write Python, you're good."),
        ("Can I participate solo?",
         "Yes! Solo participants welcome &mdash; we'll help you find a team. Teams of 2&ndash;4 recommended."),
        ("What tools can I use?",
         "Python is primary. Any ML library (scikit-learn, PyTorch, TensorFlow, etc.) is fine. We provide the trading API."),
        ("Will there be starter code?",
         "Yes. Full starter kit with example agents, datasets, API docs, and a local testing environment."),
        ("What is market making?",
         "Quoting buy and sell prices continuously. You profit from the bid-ask spread while managing inventory risk."),
        ("Where is the event?",
         "Kickoff and closing ceremony at QMUL. The competition week is remote &mdash; build from anywhere."),
        ("Is there a fee?",
         "No. Completely free to enter. However, you must be a member of the Machine Learning Society at QMUL to participate."),
    ]

    for q, a in faqs:
        st.markdown(f"""
        <div class="faq-item">
            <div class="faq-q"><span style="color:var(--accent);">▸</span> {q}</div>
            <div class="faq-a">{a}</div>
        </div>
        """, unsafe_allow_html=True)


def render_cta():
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div class="cta-banner">
        <div class="cta-title">Think your AI can beat the market?</div>
        <div class="cta-sub">Join the Market-Making AI Hackathon and find out.</div>
        <div style="display:flex;justify-content:center;gap:16px;flex-wrap:wrap;">
            <a href="#register" class="btn-primary">Register Now</a>
            <a href="#register" class="btn-secondary">Join the Discord</a>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_footer():
    st.markdown("""
    <div class="footer">
        <div style="margin-bottom:10px;">
            Hosted by the <strong style="color:var(--text);">Machine Learning Society</strong> at
        </div>
        <div style="font-size:1.05rem;font-weight:600;color:var(--text);">
            Queen Mary University of London
        </div>
        <div style="margin-top:16px;font-size:0.75rem;color:var(--text-muted);">
            &copy; 2025 ML Society QMUL
        </div>
    </div>
    """, unsafe_allow_html=True)
