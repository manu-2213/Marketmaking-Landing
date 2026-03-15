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
    header = ws.row_values(1)
    if not header:
        ws.append_row(
            ["timestamp", "name", "email", "university", "degree",
             "team_name", "team_size", "experience", "interest",
             "open_for_joining", "open_spots"]
        )
    else:
        if "open_for_joining" not in header:
            ws.update_cell(1, len(header) + 1, "open_for_joining")
            header.append("open_for_joining")
        if "open_spots" not in header:
            ws.update_cell(1, len(header) + 1, "open_spots")
    return ws


def _save_registration(name, email, university, degree, team_name,
                        team_size, experience, interest):
    """Append a registration row to Google Sheets."""
    ws = _get_gsheet()
    ws.append_row([
        datetime.now(timezone.utc).isoformat(),
        name, email, university, degree,
        team_name, team_size, experience, interest,
        "",  # open_for_joining — empty by default
        "",  # open_spots — empty by default
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


# ── Team-formation helpers ────────────────────────────────────────────────────
# Column indices (0-based): 0=timestamp, 1=name, 2=email, 3=university,
# 4=degree, 5=team_name, 6=team_size, 7=experience, 8=interest,
# 9=open_for_joining

_SOLO_LABEL = "1 (looking for a team)"


def _get_all_rows():
    """Return (worksheet, all_values) from the main sheet."""
    ws = _get_gsheet()
    return ws, ws.get_all_values()


def _row_to_dict(header, row):
    return {h: row[i] if i < len(row) else "" for i, h in enumerate(header)}


def _col_index(header, name):
    """Return 1-based column index for a header name."""
    return header.index(name) + 1


def _verify_email(email: str):
    """Find any registrant by email. Returns (row_index_1based, row_dict) or None."""
    ws, rows = _get_all_rows()
    if len(rows) <= 1:
        return None
    header = rows[0]
    for idx, r in enumerate(rows[1:], start=2):
        if len(r) > 2 and r[2].strip().lower() == email.strip().lower():
            return idx, _row_to_dict(header, r)
    return None


def _update_team_name(email: str, team_name: str):
    """Set team_name for any registrant identified by email. Returns True on success."""
    ws, rows = _get_all_rows()
    if len(rows) <= 1:
        return False
    header = rows[0]
    col = _col_index(header, "team_name")
    for idx, r in enumerate(rows[1:], start=2):
        if len(r) > 2 and r[2].strip().lower() == email.strip().lower():
            ws.update_cell(idx, col, team_name)
            return True
    return False


def _rename_team_for_all_members(old_team_name: str, new_team_name: str):
    """Rename a team for all rows that currently use old_team_name."""
    ws, rows = _get_all_rows()
    if len(rows) <= 1:
        return 0
    header = rows[0]
    col = _col_index(header, "team_name")
    old_lower = old_team_name.strip().lower()
    changed = 0
    for idx, r in enumerate(rows[1:], start=2):
        existing = (r[5] if len(r) > 5 else "").strip().lower()
        if existing and existing == old_lower:
            ws.update_cell(idx, col, new_team_name)
            changed += 1
    return changed


def _team_name_taken_by_other_group(candidate_team_name: str, current_team_name: str = ""):
    """Check if a team name is already used by a different team.

    If current_team_name is provided, rows from that same team are ignored so a
    rename/update within the same team is allowed.
    """
    _, rows = _get_all_rows()
    if len(rows) <= 1:
        return False

    candidate = candidate_team_name.strip().lower()
    current = current_team_name.strip().lower()
    if not candidate:
        return False

    for r in rows[1:]:
        existing = (r[5] if len(r) > 5 else "").strip().lower()
        if not existing:
            continue
        if existing != candidate:
            continue
        if current and existing == current:
            continue
        return True
    return False


def _set_open_for_joining(email: str, value: str = "yes"):
    """Mark a registrant's row as open_for_joining."""
    ws, rows = _get_all_rows()
    if len(rows) <= 1:
        return False
    header = rows[0]
    col = _col_index(header, "open_for_joining")
    for idx, r in enumerate(rows[1:], start=2):
        if len(r) > 2 and r[2].strip().lower() == email.strip().lower():
            ws.update_cell(idx, col, value)
            return True
    return False


def _set_open_spots(email: str, max_team_size: int):
    """Set the maximum total team size (used to compute remaining spots)."""
    ws, rows = _get_all_rows()
    if len(rows) <= 1:
        return False
    header = rows[0]
    col = _col_index(header, "open_spots")
    for idx, r in enumerate(rows[1:], start=2):
        if len(r) > 2 and r[2].strip().lower() == email.strip().lower():
            ws.update_cell(idx, col, str(max_team_size))
            return True
    return False


def _clear_team_fields_for_email(email: str):
    """Clear team-related fields for a registrant identified by email.

    If this registrant is carrying open-team metadata (open_for_joining/open_spots)
    and teammates remain, transfer that metadata to one remaining teammate so the
    team can stay open.
    """
    ws, rows = _get_all_rows()
    if len(rows) <= 1:
        return False
    header = rows[0]
    team_col = _col_index(header, "team_name")
    ofj_col = _col_index(header, "open_for_joining")
    spots_col = _col_index(header, "open_spots")

    leaving_idx = None
    leaving_team = ""
    leaving_ofj = ""
    leaving_spots = ""

    for idx, r in enumerate(rows[1:], start=2):
        if len(r) > 2 and r[2].strip().lower() == email.strip().lower():
            leaving_idx = idx
            leaving_team = (r[5] if len(r) > 5 else "").strip()
            leaving_ofj = (r[9] if len(r) > 9 else "").strip().lower()
            leaving_spots = (r[10] if len(r) > 10 else "").strip()
            break

    if leaving_idx is None:
        return False

    # If the leaving member is carrying openness metadata, migrate it to a
    # remaining teammate before clearing this row.
    if leaving_team and leaving_ofj == "yes":
        team_lower = leaving_team.lower()
        teammate_idx = None
        max_team_size = 0

        for idx, r in enumerate(rows[1:], start=2):
            existing_team = (r[5] if len(r) > 5 else "").strip().lower()
            if existing_team != team_lower:
                continue
            if idx != leaving_idx and teammate_idx is None:
                teammate_idx = idx

            existing_spots = (r[10] if len(r) > 10 else "").strip()
            if existing_spots.isdigit():
                max_team_size = max(max_team_size, int(existing_spots))

        if leaving_spots.isdigit():
            max_team_size = max(max_team_size, int(leaving_spots))

        if teammate_idx is not None:
            ws.update_cell(teammate_idx, ofj_col, "yes")
            if max_team_size > 0:
                ws.update_cell(teammate_idx, spots_col, str(max_team_size))

    ws.update_cell(leaving_idx, team_col, "")
    ws.update_cell(leaving_idx, ofj_col, "")
    ws.update_cell(leaving_idx, spots_col, "")
    return True


def _clear_team_fields_for_team(team_name: str):
    """Clear team-related fields for all registrants in a named team."""
    ws, rows = _get_all_rows()
    if len(rows) <= 1:
        return 0
    header = rows[0]
    team_col = _col_index(header, "team_name")
    ofj_col = _col_index(header, "open_for_joining")
    spots_col = _col_index(header, "open_spots")
    team_lower = team_name.strip().lower()
    changed = 0
    for idx, r in enumerate(rows[1:], start=2):
        existing = (r[5] if len(r) > 5 else "").strip().lower()
        if existing and existing == team_lower:
            ws.update_cell(idx, team_col, "")
            ws.update_cell(idx, ofj_col, "")
            ws.update_cell(idx, spots_col, "")
            changed += 1
    return changed


def _get_open_teams():
    """Return {team_name: {"members": [member_dicts], "open_spots": int}}
    for teams where at least one member set open_for_joining == 'yes'.
    Uses the open_spots column (stored as max total team size) to compute
    remaining capacity; teams with no room left are excluded."""
    _, rows = _get_all_rows()
    if len(rows) <= 1:
        return {}
    header = rows[0]
    ofj_idx = header.index("open_for_joining") if "open_for_joining" in header else None
    os_idx = header.index("open_spots") if "open_spots" in header else None

    # First pass: find team names that are opted-in + their declared max size
    opted_in: dict[str, int] = {}   # team_name -> max_team_size
    if ofj_idx is not None:
        for r in rows[1:]:
            ofj = (r[ofj_idx] if len(r) > ofj_idx else "").strip().lower()
            tn = (r[5] if len(r) > 5 else "").strip()
            if ofj == "yes" and tn:
                max_size = 4  # default cap
                if os_idx is not None and len(r) > os_idx and r[os_idx].strip().isdigit():
                    max_size = int(r[os_idx].strip())
                # Keep the highest declared in the team
                if tn not in opted_in or max_size > opted_in[tn]:
                    opted_in[tn] = max_size

    # Second pass: collect all members of those teams
    teams: dict[str, list[dict]] = {}
    for r in rows[1:]:
        tn = (r[5] if len(r) > 5 else "").strip()
        if tn and tn in opted_in:
            teams.setdefault(tn, []).append(_row_to_dict(header, r))

    # Only return teams that still have room
    # Only solo participants can open teams, so member count = row count.
    result = {}
    for tn, members in teams.items():
        spots_left = opted_in[tn] - len(members)
        if spots_left > 0:
            result[tn] = {"members": members, "effective_size": len(members), "open_spots": spots_left}
    return result


def _get_all_named_teams():
    """Return {team_name: {"members": [member_dicts], "size": int}} for teams
    that should be displayed.

    Included:
    - Pre-formed teams: team_size in (2,3,4) with a team_name. Size comes from
      the team_size column (the registrant entered it for the whole team).
        - Solo teams: any solo registrant with a team_name should appear on the
            Registered Teams board, even if they stay solo.
        - Solo-formed groups: multiple solo registrants sharing the same team_name
            (formed via the Team Hub). Size = number of rows.
    """
    _, rows = _get_all_rows()
    if len(rows) <= 1:
        return {}
    header = rows[0]

    preformed: dict[str, dict] = {}   # team_size 2-4
    solo_groups: dict[str, list[dict]] = {}  # team_size == _SOLO_LABEL

    for r in rows[1:]:
        tn = (r[5] if len(r) > 5 else "").strip()
        ts = (r[6] if len(r) > 6 else "").strip()
        if not tn:
            continue
        d = _row_to_dict(header, r)
        if ts in ("2", "3", "4"):
            if tn not in preformed:
                preformed[tn] = {"members": [], "size": int(ts)}
            preformed[tn]["members"].append(d)
        elif ts == _SOLO_LABEL:
            solo_groups.setdefault(tn, []).append(d)

    result: dict[str, dict] = {}
    # Pre-formed teams: always show with their declared size.
    # Solo registrants who set the same team name are assumed to be the declared
    # teammates registering individually — do NOT add them on top.
    for tn, info in preformed.items():
        result[tn] = info
    # Pure solo teams/groups (no pre-formed entry): show as soon as a solo
    # participant picks a name. If more solo participants join later, the size
    # naturally increases with row count.
    for tn, members in solo_groups.items():
        if tn not in result:
            result[tn] = {"members": members, "size": len(members)}
    return result


def _get_teams_without_name():
    """Return unique team registrations (team_size 2-4) that have no team_name.
    Each row is one registration representing a whole team."""
    _, rows = _get_all_rows()
    if len(rows) <= 1:
        return []
    header = rows[0]
    results = []
    for r in rows[1:]:
        if len(r) > 6:
            tn = (r[5]).strip()
            ts = (r[6]).strip()
            if not tn and ts in ("2", "3", "4"):
                results.append(_row_to_dict(header, r))
    return results


def _get_teammates(team_name: str):
    """Return list of member dicts sharing the same team_name."""
    _, rows = _get_all_rows()
    if len(rows) <= 1:
        return []
    header = rows[0]
    return [
        _row_to_dict(header, r) for r in rows[1:]
        if len(r) > 5 and r[5].strip().lower() == team_name.strip().lower()
    ]


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
                    <div style="font-family:'Orbitron',sans-serif;font-size:1.5rem;font-weight:700;color:var(--accent);">1–4</div>
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
            Sign up to receive updates and secure your team's spot.<br>
            <span style="font-size:0.9rem;color:var(--text-muted);">
                <strong style="color:var(--accent);">Teams of 2&ndash;4: only one person needs to submit this form</strong>
                on behalf of the whole team &mdash; enter your team name and the number of people
                (including yourself).<br>
                <strong>Competing solo?</strong> Choose <em>"1 (solo team)"</em> and set your team name now &mdash;
                it will appear on the Registered Teams board immediately.<br>
                <strong>Looking for teammates?</strong> Choose <em>"1 (looking for a team)"</em> &mdash;
                team name is optional at registration and can be set later in the <strong>Team Hub</strong>.
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("registration_form", clear_on_submit=True):
        fc1, fc2 = st.columns(2, gap="medium")
        with fc1:
            reg_name = st.text_input("Full Name *")
            reg_uni = st.text_input("University *")
            reg_experience = st.selectbox(
                "ML Experience Level",
                ["Beginner", "Intermediate", "Advanced", "Expert"],
            )
        with fc2:
            reg_email = st.text_input("Email *")
            reg_degree = st.text_input("Degree / Background")
            reg_team_size = st.selectbox(
                "Team Size",
                ["1 (looking for a team)", "1 (solo team)", "2", "3", "4"],
                help=(
                    "Solo team: you are competing alone under your own team name (required). "
                    "Looking for a team: you want to be matched with others (team name optional now, set it in the Team Hub later). "
                    "2–4: register your whole pre-formed team — only one person needs to submit."
                ),
            )

        # Team name: mandatory for teams of 2+ and solo teams; optional for "looking for a team"
        _team_name_required = reg_team_size in ("1 (solo team)", "2", "3", "4")
        reg_team = st.text_input(
            "Team Name" + (" *" if _team_name_required else " (optional — set later in Team Hub)"),
            help=(
                "Required if you are a solo team or a pre-formed team of 2–4. "
                "If you are looking for a team you can leave this blank and set it later."
            ),
        )
        reg_interest = st.text_area("Why are you interested?", height=108)

        submitted = st.form_submit_button("Register Interest", use_container_width=True)

        if submitted:
            is_preformed_team = reg_team_size in ("2", "3", "4")
            is_solo_team = reg_team_size == "1 (solo team)"
            reg_team_clean = reg_team.strip()
            if not reg_name or not reg_email:
                st.warning("Please fill in at least your name and email.")
            elif is_preformed_team and not reg_team_clean:
                st.warning("Team name is required when registering as a pre-formed team of 2 or more.")
            elif is_solo_team and not reg_team_clean:
                st.warning("Team name is required for a solo team — it's how you'll appear on the leaderboard.")
            elif reg_team_clean and _team_name_taken_by_other_group(reg_team_clean):
                st.error("That team name is already taken. Please choose a unique team name.")
            else:
                try:
                    _save_registration(
                        reg_name, reg_email, reg_uni, reg_degree,
                        reg_team_clean, reg_team_size, reg_experience, reg_interest,
                    )
                    st.success("**You're in!** We'll send you updates soon.")
                    st.balloons()
                except Exception as exc:
                    st.error(f"Registration failed: {exc}")


def render_team_formation():
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown('<div id="find-team"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center;margin-bottom:40px;">
        <div class="section-tag">Team Hub</div>
        <div class="section-title">Find Your Team</div>
        <div class="section-subtitle" style="margin:0 auto;">
            Already registered? Set your team name, keep your solo team as-is,
            optionally open it to recruit more people, browse open teams and join one,
            or leave/delete your current team.
            Use the email you registered with.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Open teams showcase ───────────────────────────────────────────────────
    open_teams = _get_open_teams()

    if open_teams:
        st.markdown("""
        <div style="text-align:center;margin-bottom:24px;">
            <div class="tf-open-label">Open Teams &mdash; Looking for Members</div>
        </div>
        """, unsafe_allow_html=True)

        team_html = '<div class="tf-team-grid">'
        for name, info in open_teams.items():
            size = info["effective_size"]
            spots = info["open_spots"]
            team_html += (
                f'<div class="tf-team-card">'
                f'<div class="tf-team-name">{name}</div>'
                f'<div class="tf-team-members">\U0001f465 {size} member{"s" if size != 1 else ""}</div>'
                f'<div class="tf-team-spots">{spots} spot{"s" if spots != 1 else ""} open</div>'
                f'</div>'
            )
        team_html += '</div>'
        st.markdown(team_html, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align:center;margin-bottom:20px;color:var(--text-muted);font-size:1.05rem;">
            No open teams yet &mdash; open yours below!
        </div>
        """, unsafe_allow_html=True)

    # ── Step 1: Choose / Update Team Name ─────────────────────────────────────
    st.markdown("""
    <div style="text-align:center;margin-bottom:24px;">
        <div class="tf-form-header" style="justify-content:center;">
            <span class="tf-form-icon">\u270f\ufe0f</span>
            <span class="tf-form-title">Step 1 &mdash; Choose / Update Team Name</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center;margin-bottom:16px;color:var(--text-secondary);font-size:0.95rem;">
        Registered but didn't pick a team name, or want to change it? Enter your email and team name below.
    </div>
    """, unsafe_allow_html=True)

    with st.form("update_team_name_form", clear_on_submit=True):
        uc1, uc2 = st.columns(2, gap="medium")
        with uc1:
            un_email = st.text_input("Your registered email *", key="un_email")
        with uc2:
            un_team = st.text_input("Team name *", key="un_team")
        un_submitted = st.form_submit_button("Set Team Name", use_container_width=True)

        if un_submitted:
            un_email_clean = un_email.strip()
            un_team_clean = un_team.strip()
            if not un_email_clean or not un_team_clean:
                st.warning("Please fill in both fields.")
            else:
                result = _verify_email(un_email_clean)
                if result is None:
                    st.error("Email not found. Make sure you've registered first.")
                else:
                    _, row = result
                    current_team = (row.get("team_name") or "").strip()

                    if _team_name_taken_by_other_group(un_team_clean, current_team):
                        st.error("That team name is already used by another group. Try a different one.")
                    else:
                        # If the registrant is already in a team, rename the whole team so
                        # open-team joiners and existing teammates stay together.
                        if current_team:
                            changed = _rename_team_for_all_members(current_team, un_team_clean)
                            if changed > 0:
                                st.success(
                                    f"**Team renamed to \"{un_team_clean}\" for all {changed} member"
                                    f"{'s' if changed != 1 else ''}!**"
                                )
                            else:
                                st.error("Something went wrong. Please try again.")
                        else:
                            ok = _update_team_name(un_email_clean, un_team_clean)
                            if ok:
                                st.success(f"**Team name set to \"{un_team_clean}\"!**")
                            else:
                                st.error("Something went wrong. Please try again.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Step 4: Leave / Delete Team ─────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center;margin-bottom:16px;">
        <div class="tf-form-header" style="justify-content:center;">
            <span class="tf-form-icon">🗑️</span>
            <span class="tf-form-title">Manage Team &mdash; Leave / Delete</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center;margin-bottom:16px;color:var(--text-secondary);font-size:0.95rem;">
        If you are a solo participant in a team, this will remove only you from that team.<br>
        If you registered a pre-formed team (2&ndash;4), this will delete that team entry.
    </div>
    """, unsafe_allow_html=True)

    with st.form("leave_or_delete_team_form", clear_on_submit=True):
        ld_email = st.text_input("Your registered email *", key="ld_email")
        ld_confirm = st.checkbox(
            "I understand this action updates team assignments immediately",
            key="ld_confirm",
        )
        ld_submitted = st.form_submit_button("Leave / Delete Team", use_container_width=True)

        if ld_submitted:
            ld_email_clean = ld_email.strip()
            if not ld_email_clean:
                st.warning("Please enter your email.")
            elif not ld_confirm:
                st.warning("Please confirm before continuing.")
            else:
                result = _verify_email(ld_email_clean)
                if result is None:
                    st.error("Email not found. Make sure you've registered first.")
                else:
                    _, row = result
                    current_team = (row.get("team_name") or "").strip()
                    current_size = (row.get("team_size") or "").strip()

                    if not current_team:
                        st.warning("You are not currently in a named team.")
                    elif current_size == _SOLO_LABEL:
                        ok = _clear_team_fields_for_email(ld_email_clean)
                        if ok:
                            st.success(
                                f"**You left team \"{current_team}\".**"
                            )
                        else:
                            st.error("Something went wrong. Please try again.")
                    elif current_size in ("2", "3", "4"):
                        removed = _clear_team_fields_for_team(current_team)
                        if removed > 0:
                            st.success(
                                f"**Team \"{current_team}\" deleted.** "
                                f"Updated {removed} registration row{'s' if removed != 1 else ''}."
                            )
                        else:
                            st.error("Something went wrong. Please try again.")
                    else:
                        st.error("Your registration type is not supported for this action.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Step 2 & 3: Open Your Team / Join a Team ─────────────────────────────
    col_open, col_join = st.columns(2, gap="large")

    with col_open:
        st.markdown("""
        <div class="tf-form-header">
            <span class="tf-form-icon">\U0001f4e2</span>
            <span class="tf-form-title">Step 2 &mdash; Open Your Team</span>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div style="margin-bottom:12px;color:var(--text-secondary);font-size:0.9rem;">
            This step is optional. If you're a solo participant and want to recruit,
            make your named team public so others can find and join you.
        </div>
        """, unsafe_allow_html=True)

        with st.form("open_team_form", clear_on_submit=True):
            ot_email = st.text_input("Your registered email *", key="ot_email")
            ot_spots = st.selectbox(
                "How many people can join?",
                ["1", "2", "3"],
                index=0,
                key="ot_spots",
            )
            ot_submitted = st.form_submit_button("Open My Team", use_container_width=True)

            if ot_submitted:
                ot_email_clean = ot_email.strip()
                if not ot_email_clean:
                    st.warning("Please enter your email.")
                else:
                    result = _verify_email(ot_email_clean)
                    if result is None:
                        st.error("Email not found. Make sure you've registered first.")
                    else:
                        _, row = result
                        team_name = (row.get("team_name") or "").strip()
                        if not team_name:
                            st.error("You need a team name first. Use **Step 1** above "
                                     "to set one, then come back here.")
                        elif (row.get("team_size") or "").strip() in ("2", "3", "4"):
                            st.error("You registered as a pre-formed team — "
                                     "this feature is only for solo participants looking for teammates. "
                                     "Your team is already on the Registered Teams board.")
                        else:
                            current_members = len(_get_teammates(team_name)) or 1
                            max_team_size = min(current_members + int(ot_spots), 4)
                            if max_team_size <= current_members:
                                st.error(f"Your team already has {current_members} member{'s' if current_members != 1 else ''} — no room to add more (max team size is 4).")
                            else:
                                actual_spots = max_team_size - current_members
                                _set_open_for_joining(ot_email_clean, "yes")
                                _set_open_spots(ot_email_clean, max_team_size)
                                st.success(
                                    f"**Team \"{team_name}\" is now public** with "
                                    f"{actual_spots} open spot{'s' if actual_spots != 1 else ''}! "
                                    "Others can find and join it below."
                                )
                                st.balloons()

    with col_join:
        st.markdown("""
        <div class="tf-form-header">
            <span class="tf-form-icon">\U0001f91d</span>
            <span class="tf-form-title">Step 3 &mdash; Join a Team</span>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div style="margin-bottom:12px;color:var(--text-secondary);font-size:0.9rem;">
            Browse teams that are looking for members and hop on.
        </div>
        """, unsafe_allow_html=True)

        with st.form("join_team_form", clear_on_submit=True):
            jt_email = st.text_input("Your registered email *", key="jt_email")
            team_choices = list(open_teams.keys()) if open_teams else ["No open teams yet"]
            jt_team = st.selectbox("Select a team to join", team_choices, key="jt_team")
            jt_submitted = st.form_submit_button("Join Team", use_container_width=True)

            if jt_submitted:
                jt_email_clean = jt_email.strip()
                if not jt_email_clean:
                    st.warning("Please enter your email.")
                elif not open_teams:
                    st.warning("There are no open teams to join right now.")
                else:
                    result = _verify_email(jt_email_clean)
                    if result is None:
                        st.error("Email not found. Make sure you've registered first.")
                    else:
                        _, row = result
                        existing = (row.get("team_name") or "").strip()
                        if existing:
                            st.error(f"You already have a team name: **{existing}**.")
                        elif jt_team not in open_teams:
                            st.error("That team is no longer available.")
                        else:
                            ok = _update_team_name(jt_email_clean, jt_team)
                            if ok:
                                teammates = _get_teammates(jt_team)
                                names = [m.get("name", "?") for m in teammates
                                         if m.get("email", "").strip().lower() != jt_email_clean.lower()]
                                if names:
                                    st.success(f"**You joined team \"{jt_team}\"!** "
                                               f"Your teammates: {', '.join(names)} \U0001f389")
                                else:
                                    st.success(f"**You joined team \"{jt_team}\"!** Good luck \U0001f389")
                            else:
                                st.error("Something went wrong. Please try again.")


def render_registered_teams():
    """Showcase all teams that have a name."""
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center;margin-bottom:40px;">
        <div class="section-tag">The Competition</div>
        <div class="section-title">Registered Teams</div>
        <div class="section-subtitle" style="margin:0 auto;">
            These teams are locked in. Is yours on the board?
        </div>
    </div>
    """, unsafe_allow_html=True)

    all_teams = _get_all_named_teams()

    if not all_teams:
        st.markdown("""
        <div style="text-align:center;color:var(--text-muted);font-size:1.05rem;margin-bottom:20px;">
            No teams registered yet &mdash; be the first!
        </div>
        """, unsafe_allow_html=True)
        return

    html = '<div class="rt-grid">'
    for idx, (name, info) in enumerate(all_teams.items()):
        color_idx = idx % 4
        colors = [
            ("var(--accent)", "rgba(0,240,255,0.12)", "rgba(0,240,255,0.3)"),
            ("var(--accent2)", "rgba(167,139,250,0.12)", "rgba(167,139,250,0.3)"),
            ("var(--accent3)", "rgba(244,114,182,0.12)", "rgba(244,114,182,0.3)"),
            ("var(--gold)", "rgba(251,191,36,0.12)", "rgba(251,191,36,0.3)"),
        ]
        accent, bg, border = colors[color_idx]
        size = info["size"]
        html += (
            f'<div class="rt-card" style="border-color:{border};">'
            f'<div class="rt-accent-bar" style="background:linear-gradient(90deg,{accent},{border});"></div>'
            f'<div class="rt-name" style="color:{accent};">{name}</div>'
            f'<div class="rt-members">\U0001f465 {size} member{"s" if size != 1 else ""}</div>'
            f'</div>'
        )
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_faq():
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center;margin-bottom:40px;">
        <div class="section-tag">Questions</div>
        <div class="section-title">FAQ</div>
    </div>
    """, unsafe_allow_html=True)

    faqs = [
        ("Do I register individually or as a team?",
         "If you already have a team (2&ndash;4 people), <strong>only one person per team needs to register</strong> &mdash; enter your team name and the total team size. Everyone else on your team will be counted automatically. Solo participants register individually and can find or form a team later via the Team Hub."),
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
