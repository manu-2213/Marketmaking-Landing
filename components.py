"""Section components for the Market-Making AI Hackathon landing page."""

from html import escape
import streamlit as st
import random
import re
from datetime import datetime, timezone
from event_config import EVENT_CONFIG

from sheets_store import get_registration_store, STORAGE_ERRORS


REGISTRATION_OPEN = EVENT_CONFIG["registration_open"]

def _get_registration_store():
    return get_registration_store()


def _save_registration(name, student_id, email, university, degree, team_name,
                        team_size, experience, interest):
    """Save a registration to the organiser's Google Sheet."""
    ws = _get_registration_store()
    ws.append_row([
        datetime.now(timezone.utc).isoformat(),
        name, email, university, degree,
        team_name, team_size, experience, interest,
        "",  # open_for_joining — empty by default
        "",  # open_spots — empty by default
        student_id,
    ])


def get_team_count():
    """Count total registrations (rows after the header)."""
    all_rows = _get_registration_store().get_all_values()
    return max(len(all_rows) - 1, 0)  # subtract header row


# ── Team-formation helpers ────────────────────────────────────────────────────
# Column indices (0-based): 0=timestamp, 1=name, 2=email, 3=university,
# 4=degree, 5=team_name, 6=team_size, 7=experience, 8=interest,
# 9=open_for_joining

_SOLO_LABEL = "1 (looking for a team)"


def _get_all_rows():
    """Return the account-backed store and current-event registrations."""
    ws = _get_registration_store()
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


def _verify_student_id(student_id: str):
    """Find a registrant by student ID, case-insensitively."""
    _, rows = _get_all_rows()
    if len(rows) <= 1:
        return None
    header = rows[0]
    student_id_index = header.index("student_id")
    for idx, row in enumerate(rows[1:], start=2):
        if (
            len(row) > student_id_index
            and row[student_id_index].strip().casefold() == student_id.strip().casefold()
        ):
            return idx, _row_to_dict(header, row)
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
        - Forming teams: individuals sharing a team_name are shown once at least
            two people have joined through the Team Hub.
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
    # Individuals forming a team are not displayed as a competition team until
    # at least two people have joined.
    for tn, members in solo_groups.items():
        if tn not in result and len(members) >= 2:
            result[tn] = {"members": members, "size": len(members)}
    return result


def get_registration_stats():
    """Return registered team count and represented people for the current event."""
    _, rows = _get_all_rows()
    if len(rows) <= 1:
        return 0, 0

    header = rows[0]
    preformed_teams = {}
    unnamed_team_count = 0
    unnamed_team_members = 0
    solo_groups = {}
    solo_people = 0

    for row in rows[1:]:
        record = _row_to_dict(header, row)
        team_name = (record.get("team_name") or "").strip().casefold()
        team_size = (record.get("team_size") or "").strip()
        if team_size in ("2", "3", "4"):
            if team_name:
                preformed_teams.setdefault(team_name, int(team_size))
            else:
                unnamed_team_count += 1
                unnamed_team_members += int(team_size)
        elif team_size == _SOLO_LABEL and team_name:
            solo_groups[team_name] = solo_groups.get(team_name, 0) + 1
        else:
            solo_people += 1

    formed_solo_teams = {
        name: count
        for name, count in solo_groups.items()
        if name not in preformed_teams and count >= 2
    }
    solo_people += sum(
        count
        for name, count in solo_groups.items()
        if name not in preformed_teams and count < 2
    )
    team_count = len(preformed_teams) + unnamed_team_count + len(formed_solo_teams)
    member_count = (
        sum(preformed_teams.values())
        + unnamed_team_members
        + sum(formed_solo_teams.values())
        + solo_people
    )
    return team_count, member_count


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
                    <a href="#register" class="btn-primary">Registrations Closed</a>
                    <a href="#register" class="btn-secondary">Join Waitlist Updates</a>
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
            <div class="step-date step-date-1">19 NOV 2026</div>
            <div class="step-title">Opening ceremony</div>
            <div class="step-sub">In person</div>
        </div>
        <div class="step">
            <div class="step-icon step-icon-2">🧠</div>
            <div class="step-date step-date-2">BUILD &amp; PREPARE</div>
            <div class="step-title">Develop your model</div>
            <div class="step-sub">Work with your team</div>
        </div>
        <div class="step">
            <div class="step-icon step-icon-3">📈</div>
            <div class="step-date step-date-3">26 NOV 2026</div>
            <div class="step-title">Live competition</div>
            <div class="step-sub">Simulated market</div>
        </div>
        <div class="step">
            <div class="step-icon step-icon-4">🏆</div>
            <div class="step-date step-date-4">26 NOV 2026</div>
            <div class="step-title">Closing ceremony</div>
            <div class="step-sub">In person</div>
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
    st.markdown('<div id="register"></div>', unsafe_allow_html=True)

    if not REGISTRATION_OPEN:
        st.info("Registration is not open yet. Check back for sign-up details.")
        return

    info, form_column = st.columns([0.85, 1.4], gap="large")
    with info:
        st.markdown("""
<div class="registration-intro">
    <p class="eyebrow"><span class="status-dot"></span> 05 / Early interest open</p>
    <h2>Join the<br>early-interest<br>list.</h2>
    <p>This is not a ticket purchase. We’ll email you when tickets go on sale.</p>
    <div class="registration-facts">
        <div><span>01</span><p><strong>Early interest only</strong><br>No ticket or payment is required now.</p></div>
        <div><span>02</span><p><strong>Ticket updates by email</strong><br>We’ll contact you when tickets are released.</p></div>
        <div><span>03</span><p><strong>Team or solo</strong><br>Register your team or look for teammates.</p></div>
    </div>
    <p class="privacy-note">Student IDs and email addresses are kept private.
    Only team names and team sizes appear on the public board.</p>
</div>
""", unsafe_allow_html=True)
    with form_column:
        if st.session_state.get("registration_saved_2026"):
            st.success(
                "You're on the early-interest list. We'll email you when tickets are released."
            )
            st.write("Your details have been saved to the organiser's Google Sheet.")
            if st.session_state.get(_HUB_IDENTITY_KEY):
                st.button(
                    "Find teammates in the Team Hub  ↓", key="open_team_hub", type="primary",
                    on_click=lambda: st.session_state.update(show_team_hub=True),
                )
            if st.button("Register another participant", key="register_another"):
                st.session_state.pop("registration_saved_2026", None)
                st.session_state.pop(_HUB_IDENTITY_KEY, None)
                for key in list(st.session_state):
                    if key.startswith("signup_"):
                        del st.session_state[key]
                st.rerun()
            return

        with st.form("registration_form", clear_on_submit=False):
            st.markdown('<div class="form-title"><h3>Register your interest</h3>'
                        '<p>This is not a ticket purchase. Required fields are marked with an asterisk.</p></div>',
                        unsafe_allow_html=True)
            st.markdown('<p class="form-section-label">01 / Your details</p>', unsafe_allow_html=True)
            a, b = st.columns(2)
            with a:
                reg_name = st.text_input("Full name *", placeholder="First and last name", key="signup_name")
                reg_student_email = st.text_input("Student email *", placeholder="you@university.ac.uk", key="signup_email")
                reg_uni = st.text_input("University *", placeholder="Your university", key="signup_university")
            with b:
                reg_student_id = st.text_input("Student ID *", placeholder="Your student number", key="signup_id")
                reg_degree = st.text_input("Degree / subject", placeholder="e.g. Computer Science", key="signup_degree")
                reg_experience = st.selectbox(
                    "ML experience", ["Beginner", "Intermediate", "Advanced", "Expert"], key="signup_experience"
                )
            st.markdown('<p class="form-section-label">02 / Your team</p>', unsafe_allow_html=True)
            a, b = st.columns(2)
            with a:
                team_size_choice = st.selectbox(
                    "How are you joining? *",
                    ["Looking for a team", "Team of 2", "Team of 3", "Team of 4"],
                    key="signup_team_size",
                )
            with b:
                reg_team = st.text_input("Team name", placeholder="Leave blank if looking", key="signup_team")
            st.caption("For an existing team, one person registers on behalf of the group. Team name is required.")
            with st.expander("Anything else? (optional)"):
                reg_interest = st.text_area("A note for the organisers", key="signup_note", height=80)
            submitted = st.form_submit_button(
                "Register interest  ↗", use_container_width=True, type="primary"
            )
            st.caption("Your details are used to organise this event and coordinate teams.")

        if submitted:
            _is_looking_for_team = team_size_choice == "Looking for a team"
            reg_team_size = _SOLO_LABEL if _is_looking_for_team else team_size_choice[-1]
            reg_team_clean = reg_team.strip()
            reg_email_clean = reg_student_email.strip().lower()
            reg_student_id_clean = reg_student_id.strip()
            if not all(
                (reg_name.strip(), reg_student_id_clean, reg_email_clean, reg_uni.strip())
            ):
                st.warning(
                    "Please fill in your name, student ID, student email and university."
                )
            elif not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", reg_email_clean):
                st.warning("Enter a valid student email address.")
            elif not reg_team_clean and not _is_looking_for_team:
                st.warning("Please enter a team name.")
            else:
                try:
                    if _verify_email(reg_email_clean):
                        st.error("That student email is already registered.")
                    elif _verify_student_id(reg_student_id_clean):
                        st.error("That student ID is already registered.")
                    elif reg_team_clean and _team_name_taken_by_other_group(reg_team_clean):
                        st.error("That team name is already taken. Please choose a unique team name.")
                    else:
                        _save_registration(
                            reg_name.strip(), reg_student_id_clean, reg_email_clean,
                            reg_uni.strip(), reg_degree.strip(),
                            reg_team_clean, reg_team_size, reg_experience, reg_interest,
                        )
                        st.session_state["registration_saved_2026"] = True
                        if _is_looking_for_team and not reg_team_clean:
                            # Sign the new registrant straight into the Team Hub.
                            st.session_state[_HUB_IDENTITY_KEY] = reg_email_clean
                        st.rerun()
                except STORAGE_ERRORS:
                    st.error(
                        "We couldn't confirm your registration with Google Sheets. "
                        "Your form details are still here. Please try again; if the "
                        "problem continues, contact the organisers."
                    )


_MAX_TEAM_SIZE = 4
_HUB_IDENTITY_KEY = "team_hub_email"
_HUB_FLASH_KEY = "team_hub_flash"


def _plural(count, word):
    return f"{count} {word}{'s' if count != 1 else ''}"


def _set_team_openness(team_name: str, max_team_size: int | None):
    """List a Team Hub team publicly up to max_team_size members, or make it
    private when max_team_size is None. Applies to every member's row."""
    ws, rows = _get_all_rows()
    if len(rows) <= 1:
        return 0
    header = rows[0]
    ofj_col = _col_index(header, "open_for_joining")
    spots_col = _col_index(header, "open_spots")
    team_lower = team_name.strip().lower()
    changed = 0
    for idx, r in enumerate(rows[1:], start=2):
        if (r[5] if len(r) > 5 else "").strip().lower() == team_lower:
            ws.update_cell(idx, ofj_col, "yes" if max_team_size else "")
            ws.update_cell(idx, spots_col, str(max_team_size) if max_team_size else "")
            changed += 1
    return changed


def _find_hub_team(team_name: str):
    """Return (team_name, members) for a team formed through the Team Hub.

    Pre-formed team registrations (one row for 2-4 people) cannot be joined.
    """
    members = _get_teammates(team_name)
    if not members or any(
        (m.get("team_size") or "").strip() != _SOLO_LABEL for m in members
    ):
        return None
    return members[0]["team_name"].strip(), members


def _join_team(email: str, team_name: str):
    """Add a registrant without a team to a Team Hub team. Returns (ok, message)."""
    found = _find_hub_team(team_name)
    if found is None:
        return False, "No team with that name is accepting members. Check the exact spelling with your teammate."
    name, members = found
    if len(members) >= _MAX_TEAM_SIZE:
        return False, f'Team "{name}" is already full ({_MAX_TEAM_SIZE} members).'
    if not _update_team_name(email, name):
        return False, "Something went wrong. Please try again."
    others = [m.get("name", "").strip() for m in members if m.get("name", "").strip()]
    if not others:
        return True, f'You joined "{name}". Good luck!'
    return True, f'You joined "{name}". Your teammates: {", ".join(others)}.'


def _start_team(email: str, team_name: str, target_size: int, listed: bool):
    """Create a Team Hub team for a registrant. Returns (ok, message)."""
    if _team_name_taken_by_other_group(team_name):
        return False, "That team name is already taken. Please choose another."
    if not _update_team_name(email, team_name):
        return False, "Something went wrong. Please try again."
    if listed:
        _set_team_openness(team_name, target_size)
        return True, (
            f'Team "{team_name}" created and listed with '
            f"{_plural(target_size - 1, 'open spot')}."
        )
    return True, f'Team "{team_name}" created. Share the exact name with friends so they can join.'


def _count_people_looking():
    """Count current registrants looking for a team who have not joined one."""
    _, rows = _get_all_rows()
    return sum(
        1 for r in rows[1:]
        if (r[6] if len(r) > 6 else "").strip() == _SOLO_LABEL
        and not (r[5] if len(r) > 5 else "").strip()
    )


def _hub_done(message, kind="success"):
    """Show a message after the next full rerun so all counts and boards refresh."""
    st.session_state[_HUB_FLASH_KEY] = (kind, message)
    st.rerun()


def _sign_in_to_team_hub(email: str, student_id: str):
    result = _verify_email(email)
    if result is None:
        return False
    stored_id = (result[1].get("student_id") or "").strip()
    # Registrations made before student IDs were collected match on email alone.
    return not stored_id or stored_id.casefold() == student_id.strip().casefold()


def _open_team_cards_html(open_teams):
    html = '<div class="tf-team-grid">'
    for name, info in open_teams.items():
        html += (
            '<div class="tf-team-card">'
            f'<div class="tf-team-name">{escape(name)}</div>'
            f'<div class="tf-team-members">{_plural(info["effective_size"], "member")}</div>'
            f'<div class="tf-team-spots">{_plural(info["open_spots"], "spot")} open</div>'
            '</div>'
        )
    return html + '</div>'


def _render_hub_sign_in():
    with st.form("team_hub_sign_in"):
        st.markdown(
            '<div class="form-title"><h3>Sign in to the Team Hub</h3>'
            '<p>Use the student email and student ID you registered with.</p></div>',
            unsafe_allow_html=True,
        )
        a, b = st.columns(2)
        email = a.text_input("Student email", key="hub_email_input")
        student_id = b.text_input("Student ID", key="hub_id_input")
        submitted = st.form_submit_button("Continue  ↗", use_container_width=True)
    if submitted:
        if not email.strip() or not student_id.strip():
            st.warning("Please enter both your student email and student ID.")
        elif _sign_in_to_team_hub(email, student_id):
            st.session_state[_HUB_IDENTITY_KEY] = email.strip().lower()
            st.rerun()
        else:
            st.error(
                "We couldn't find a registration with that email and student ID. "
                "Not registered yet? Use the form above."
            )


def _render_find_team(email):
    st.markdown(
        '<p class="hub-status">You are not in a team yet. Choose one of the options below.</p>',
        unsafe_allow_html=True,
    )
    join_tab, friend_tab, start_tab = st.tabs(
        ["Join an open team", "Join a friend's team", "Start a new team"]
    )

    with join_tab:
        open_teams = _get_open_teams()
        if not open_teams:
            st.info(
                "No teams are recruiting right now. Start a new team and list it "
                "so others can find you."
            )
        for i, (name, info) in enumerate(open_teams.items()):
            card, action = st.columns([3, 1], vertical_alignment="center")
            card.markdown(
                f'<div class="hub-team-row"><strong>{escape(name)}</strong>'
                f'<span>{_plural(info["effective_size"], "member")} · '
                f'{_plural(info["open_spots"], "spot")} open</span></div>',
                unsafe_allow_html=True,
            )
            if action.button("Join", key=f"hub_join_{i}", use_container_width=True):
                if name not in _get_open_teams():
                    st.error(f'"{name}" has just filled up or closed. Please pick another team.')
                else:
                    ok, message = _join_team(email, name)
                    if ok:
                        _hub_done(message)
                    st.error(message)

    with friend_tab:
        with st.form("hub_join_by_name", clear_on_submit=False):
            st.caption("Ask your friend for their exact team name. Teams can have up to 4 members.")
            team_name = st.text_input("Team name", key="hub_friend_team")
            submitted = st.form_submit_button("Join team", use_container_width=True)
        if submitted:
            if not team_name.strip():
                st.warning("Please enter a team name.")
            else:
                ok, message = _join_team(email, team_name.strip())
                if ok:
                    _hub_done(message)
                st.error(message)

    with start_tab:
        with st.form("hub_start_team", clear_on_submit=False):
            team_name = st.text_input("Team name", key="hub_new_team")
            a, b = st.columns(2)
            target_size = a.selectbox(
                "Target team size", [4, 3, 2], key="hub_new_team_size",
                format_func=lambda n: f"{n} people",
            )
            listed = b.radio(
                "Visibility", ["Public: others can join", "Private: invite friends by name"],
                key="hub_new_team_visibility",
            ).startswith("Public")
            submitted = st.form_submit_button("Create team", use_container_width=True)
        if submitted:
            if not team_name.strip():
                st.warning("Please enter a team name.")
            else:
                ok, message = _start_team(email, team_name.strip(), target_size, listed)
                if ok:
                    _hub_done(message)
                st.error(message)


def _render_my_hub_team(email, team_name):
    members = _get_teammates(team_name)
    count = len(members)
    max_size = max(
        (int(m["open_spots"]) for m in members
         if (m.get("open_for_joining") or "").strip().lower() == "yes"
         and (m.get("open_spots") or "").strip().isdigit()),
        default=0,
    )
    is_listed = max_size > count
    status = (
        f"Public · {_plural(max_size - count, 'spot')} open" if is_listed
        else "Full" if count >= _MAX_TEAM_SIZE
        else "Private · join by exact team name"
    )
    roster = "".join(
        f'<li>{escape(m.get("name", "").strip() or "Registrant")}'
        f'{" (you)" if m.get("email", "").strip().lower() == email else ""}</li>'
        for m in members
    )
    st.markdown(
        f'<div class="hub-team-card"><p class="eyebrow">Your team</p>'
        f'<h3>{escape(team_name)}</h3>'
        f'<p class="hub-team-meta">{count} of {_MAX_TEAM_SIZE} members · {escape(status)}</p>'
        f'<ul class="hub-roster">{roster}</ul></div>',
        unsafe_allow_html=True,
    )

    with st.expander("Team settings"):
        with st.form("hub_team_settings"):
            new_name = st.text_input("Team name", value=team_name, key="hub_settings_name")
            a, b = st.columns(2)
            size_options = [n for n in (2, 3, 4) if n > count] or [_MAX_TEAM_SIZE]
            target = a.selectbox(
                "Target team size", size_options,
                index=size_options.index(max_size) if max_size in size_options else len(size_options) - 1,
                format_func=lambda n: f"{n} people", key="hub_settings_size",
                disabled=count >= _MAX_TEAM_SIZE,
            )
            listed = b.radio(
                "Visibility", ["Public: others can join", "Private: invite friends by name"],
                index=0 if is_listed else 1, key="hub_settings_visibility",
                disabled=count >= _MAX_TEAM_SIZE,
            ).startswith("Public")
            saved = st.form_submit_button("Save changes", use_container_width=True)
        if saved:
            new_name = new_name.strip()
            if not new_name:
                st.warning("Team name can't be empty.")
            elif new_name != team_name and _team_name_taken_by_other_group(new_name, team_name):
                st.error("That team name is already used by another team.")
            else:
                if new_name != team_name:
                    _rename_team_for_all_members(team_name, new_name)
                if count < _MAX_TEAM_SIZE:
                    _set_team_openness(new_name, target if listed else None)
                _hub_done("Team settings saved.")

    with st.expander("Leave team"):
        st.caption("You'll go back to looking for a team. Your teammates stay together.")
        if st.button("Leave this team", key="hub_leave"):
            if _clear_team_fields_for_email(email):
                _hub_done(f'You left "{team_name}".')
            st.error("Something went wrong. Please try again.")


def _render_preformed_team(email, me):
    team_name = (me.get("team_name") or "").strip()
    size = (me.get("team_size") or "").strip()
    st.markdown(
        f'<div class="hub-team-card"><p class="eyebrow">Your registered team</p>'
        f'<h3>{escape(team_name or "Unnamed team")}</h3>'
        f'<p class="hub-team-meta">{size} members · registered by you on behalf of the team</p></div>',
        unsafe_allow_html=True,
    )
    with st.form("hub_preformed_name"):
        new_name = st.text_input("Team name", value=team_name, key="hub_preformed_name_input")
        saved = st.form_submit_button("Save team name", use_container_width=True)
    if saved:
        new_name = new_name.strip()
        if not new_name:
            st.warning("Team name can't be empty.")
        elif _team_name_taken_by_other_group(new_name, team_name):
            st.error("That team name is already used by another team.")
        elif team_name:
            _rename_team_for_all_members(team_name, new_name)
            _hub_done(f'Team renamed to "{new_name}".')
        elif _update_team_name(email, new_name):
            _hub_done(f'Team name set to "{new_name}".')
        else:
            st.error("Something went wrong. Please try again.")

    if team_name:
        with st.expander("Remove team from the board"):
            st.caption(
                "Your registration stays on the early-interest list, but the team "
                "name is removed and it no longer appears on the public board."
            )
            if st.button("Remove team", key="hub_remove_preformed"):
                _clear_team_fields_for_team(team_name)
                _hub_done(f'Team "{team_name}" removed from the board.')


def _render_team_hub():
    flash = st.session_state.pop(_HUB_FLASH_KEY, None)
    if flash:
        getattr(st, flash[0])(flash[1])

    email = st.session_state.get(_HUB_IDENTITY_KEY)
    result = _verify_email(email) if email else None
    if result is None:
        st.session_state.pop(_HUB_IDENTITY_KEY, None)
        open_teams = _get_open_teams()
        looking = _count_people_looking()
        st.markdown(
            f'<p class="hub-status">{_plural(len(open_teams), "team")} recruiting · '
            f'{looking} {"person" if looking == 1 else "people"} looking for a team</p>',
            unsafe_allow_html=True,
        )
        if open_teams:
            st.markdown(_open_team_cards_html(open_teams), unsafe_allow_html=True)
        _render_hub_sign_in()
        return

    _, me = result
    first_name = (me.get("name") or "").strip().split(" ")[0]
    greeting, sign_out = st.columns([4, 1], vertical_alignment="center")
    greeting.markdown(
        f'<p class="hub-greeting">Signed in as <strong>{escape(first_name or email)}</strong></p>',
        unsafe_allow_html=True,
    )
    if sign_out.button("Sign out", key="hub_sign_out", use_container_width=True):
        st.session_state.pop(_HUB_IDENTITY_KEY, None)
        st.rerun()

    team_name = (me.get("team_name") or "").strip()
    if (me.get("team_size") or "").strip() in ("2", "3", "4"):
        _render_preformed_team(email, me)
    elif team_name:
        _render_my_hub_team(email, team_name)
    else:
        _render_find_team(email)


@st.fragment
def render_team_formation():
    st.markdown('<div id="find-team"></div>', unsafe_allow_html=True)
    st.markdown(
        """
<div class="section-heading"><p class="eyebrow">Team Hub</p>
<h2>Find your team.</h2>
<p class="section-description">Sign in once with your registration details, then join a team
that is recruiting, join a friend's team by name, or start your own.</p></div>
<div class="hub-steps">
    <div><span>01</span><p><strong>Sign in</strong><br>Student email and student ID.</p></div>
    <div><span>02</span><p><strong>Join or start</strong><br>Open teams, friends' teams or your own.</p></div>
    <div><span>03</span><p><strong>Manage anytime</strong><br>Rename, recruit, or leave.</p></div>
</div>
""",
        unsafe_allow_html=True,
    )
    with st.container(key="team_hub"):
        try:
            _render_team_hub()
        except STORAGE_ERRORS:
            st.error("The Team Hub cannot reach registration storage. Please try again later.")


def render_registered_teams():
    """Showcase all teams that have a name."""
    st.markdown("""
<div class="section-heading board-heading"><p class="eyebrow">Early interest</p>
<h2>Teams interested.</h2>
<p class="section-description">These teams have registered interest. Ticket details will follow by email.</p></div>
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
            f'<div class="rt-name" style="color:{accent};">{escape(name)}</div>'
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
        ("Can I sign up before I have a team?",
         "Yes. Register as looking for a team, then use the Team Hub to find teammates. Competition teams are intended to have 2–4 participants."),
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
        <div class="cta-sub">Registrations are closed. Follow updates and watch the teams compete.</div>
        <div style="display:flex;justify-content:center;gap:16px;flex-wrap:wrap;">
            <a href="#register" class="btn-primary">Registrations Closed</a>
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
