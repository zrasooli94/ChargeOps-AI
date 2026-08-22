import os
from uuid import uuid4

import httpx
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv(
    "CHARGEOPS_API_URL",
    "http://127.0.0.1:8000",
)

st.set_page_config(
    page_title="ChargeOps AI",
    page_icon="⚡",
    layout="wide",
)

DEMO_EMAIL = os.getenv(
    "CHARGEOPS_DEMO_EMAIL",
    "demo@chargeops.ai",
)

DEMO_PASSWORD = os.getenv(
    "CHARGEOPS_DEMO_PASSWORD",
    "",
)

def inject_chargeops_theme() -> None:
    """Apply the ChargeOps/CXOps-inspired visual system."""
    st.markdown(
        """
        <style>
        :root {
            --chargeops-bg: #f8f7ff;
            --chargeops-surface: rgba(255, 255, 255, 0.88);
            --chargeops-card: #ffffff;
            --chargeops-line: #e9e5ff;
            --chargeops-line-strong: #d9d1ff;
            --chargeops-ink: #17172a;
            --chargeops-muted: #6e6b83;
            --chargeops-purple: #6d4aff;
            --chargeops-purple-2: #8b5cf6;
            --chargeops-blue: #6366f1;
            --chargeops-cyan: #5eead4;
            --chargeops-green: #16a34a;
            --chargeops-shadow: 0 18px 55px rgba(87, 70, 180, 0.10);
        }

        html, body, [class*="css"] {
            font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont,
                "Segoe UI", sans-serif;
            color: var(--chargeops-ink);
        }

        .stApp {
            background:
                radial-gradient(circle at 76% 5%, rgba(124, 92, 255, .16), transparent 24rem),
                radial-gradient(circle at 15% 30%, rgba(99, 102, 241, .08), transparent 30rem),
                linear-gradient(180deg, #fcfbff 0%, #f7f6ff 48%, #f4f6ff 100%);
        }

        [data-testid="stAppViewContainer"] > .main {
            background: transparent;
        }

        [data-testid="stHeader"], #MainMenu, footer {
            visibility: hidden;
            height: 0;
        }

        .block-container {
            max-width: 1500px;
            padding-top: 1.15rem;
            padding-bottom: 4rem;
        }

        /* Sidebar = calm control rail */
        section[data-testid="stSidebar"] {
            background:
                radial-gradient(circle at 30% 0%, rgba(124, 92, 255, .20), transparent 16rem),
                linear-gradient(180deg, #fbfaff 0%, #f4f1ff 100%);
            border-right: 1px solid var(--chargeops-line);
        }

        section[data-testid="stSidebar"] > div {
            padding-top: 1.2rem;
        }

        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {
            color: #202033;
            letter-spacing: -0.02em;
        }

        /* Inputs */
        [data-testid="stTextInput"] input,
        [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
        [data-testid="stNumberInput"] input,
        textarea {
            background: rgba(255,255,255,.96) !important;
            border: 1px solid #e6e1ff !important;
            border-radius: 13px !important;
            box-shadow: 0 5px 18px rgba(87, 70, 180, .05) !important;
        }

        [data-testid="stTextInput"] input:focus,
        textarea:focus {
            border-color: #8b5cf6 !important;
            box-shadow: 0 0 0 3px rgba(139, 92, 246, .12) !important;
        }

        /* Buttons */
        .stButton > button,
        .stFormSubmitButton > button {
            min-height: 2.75rem;
            border-radius: 12px;
            border: 1px solid #7657ff;
            background: linear-gradient(135deg, #7252ff 0%, #633cff 55%, #7c3aed 100%);
            color: white;
            font-weight: 700;
            box-shadow: 0 10px 24px rgba(109, 74, 255, .22);
            transition: transform .16s ease, box-shadow .16s ease, opacity .16s ease;
        }

        .stButton > button:hover,
        .stFormSubmitButton > button:hover {
            color: white;
            border-color: #5b35f0;
            transform: translateY(-1px);
            box-shadow: 0 14px 30px rgba(109, 74, 255, .30);
        }

        .stButton > button:active,
        .stFormSubmitButton > button:active {
            transform: translateY(0);
        }

        /* Forms / cards */
        [data-testid="stForm"] {
            background: rgba(255,255,255,.90);
            border: 1px solid var(--chargeops-line);
            border-radius: 20px;
            padding: 1.1rem 1.15rem 1.15rem;
            box-shadow: var(--chargeops-shadow);
            backdrop-filter: blur(18px);
        }

        [data-testid="stMetric"] {
            background: rgba(255,255,255,.92);
            border: 1px solid var(--chargeops-line);
            border-radius: 18px;
            padding: 1rem 1.05rem;
            box-shadow: 0 12px 34px rgba(87, 70, 180, .075);
        }

        [data-testid="stMetricLabel"] {
            color: var(--chargeops-muted);
            font-weight: 650;
        }

        [data-testid="stMetricValue"] {
            color: #19192d;
            letter-spacing: -0.03em;
        }

        /* Tabs styled like CXOps top navigation */
        [data-testid="stTabs"] {
            margin-top: .8rem;
        }

        [data-testid="stTabs"] [data-baseweb="tab-list"] {
            gap: .35rem;
            padding: .45rem;
            background: rgba(255,255,255,.88);
            border: 1px solid var(--chargeops-line);
            border-radius: 16px;
            box-shadow: 0 12px 34px rgba(87, 70, 180, .075);
            backdrop-filter: blur(14px);
            overflow-x: auto;
        }

        [data-testid="stTabs"] button[role="tab"] {
            border-radius: 11px;
            padding: .6rem .9rem;
            color: #615e72;
            font-weight: 700;
            white-space: nowrap;
        }

        [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
            color: #5f3df3;
            background: linear-gradient(135deg, rgba(109,74,255,.12), rgba(99,102,241,.08));
        }

        [data-testid="stTabs"] [data-baseweb="tab-highlight"] {
            background-color: #6d4aff;
            height: 2px;
        }

        /* Expanders / notices / data */
        [data-testid="stExpander"] {
            background: rgba(255,255,255,.88);
            border: 1px solid var(--chargeops-line) !important;
            border-radius: 15px !important;
            overflow: hidden;
            box-shadow: 0 8px 25px rgba(87,70,180,.055);
        }

        [data-testid="stAlert"] {
            border-radius: 14px;
            border-width: 1px;
        }

        [data-testid="stDataFrame"],
        [data-testid="stTable"] {
            border: 1px solid var(--chargeops-line);
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 10px 28px rgba(87,70,180,.05);
        }

        [data-testid="stChatMessage"] {
            background: rgba(255,255,255,.88);
            border: 1px solid var(--chargeops-line);
            border-radius: 18px;
            padding: .45rem .65rem;
            box-shadow: 0 9px 24px rgba(87,70,180,.05);
        }

        [data-testid="stChatInput"] textarea {
            border-radius: 16px !important;
        }

        /* Custom surfaces */
        .co-topbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            padding: .82rem 1rem;
            margin-bottom: 1.1rem;
            background: rgba(255,255,255,.78);
            border: 1px solid var(--chargeops-line);
            border-radius: 18px;
            box-shadow: 0 12px 36px rgba(87,70,180,.07);
            backdrop-filter: blur(16px);
        }

        .co-brand {
            display: flex;
            align-items: center;
            gap: .7rem;
            font-weight: 850;
            letter-spacing: -0.035em;
            font-size: 1.25rem;
        }

        .co-logo {
            width: 38px;
            height: 38px;
            display: grid;
            place-items: center;
            border-radius: 12px;
            color: white;
            font-size: 1.15rem;
            background: linear-gradient(145deg, #9b72ff, #6541f2);
            box-shadow: 0 9px 20px rgba(109,74,255,.28), inset 0 1px 0 rgba(255,255,255,.35);
        }

        .co-ai {
            color: #6d4aff;
        }

        .co-status {
            display: inline-flex;
            align-items: center;
            gap: .45rem;
            color: #4a475b;
            font-size: .88rem;
            font-weight: 700;
            padding: .45rem .7rem;
            border: 1px solid #dfdafb;
            border-radius: 999px;
            background: rgba(255,255,255,.9);
        }

        .co-status-dot {
            width: 8px;
            height: 8px;
            background: #22c55e;
            border-radius: 999px;
            box-shadow: 0 0 0 4px rgba(34,197,94,.10);
        }

        .co-hero {
            position: relative;
            overflow: hidden;
            min-height: 480px;
            padding: clamp(1.5rem, 4vw, 3.3rem);
            background:
                radial-gradient(circle at 85% 20%, rgba(124,92,255,.22), transparent 22rem),
                radial-gradient(circle at 10% 85%, rgba(99,102,241,.10), transparent 22rem),
                linear-gradient(145deg, rgba(255,255,255,.98), rgba(247,245,255,.94));
            border: 1px solid var(--chargeops-line);
            border-radius: 30px;
            box-shadow: 0 28px 80px rgba(87,70,180,.12);
        }

        .co-eyebrow {
            display: inline-flex;
            align-items: center;
            gap: .45rem;
            padding: .45rem .72rem;
            background: rgba(109,74,255,.08);
            color: #6442ed;
            border: 1px solid rgba(109,74,255,.15);
            border-radius: 999px;
            font-weight: 750;
            font-size: .82rem;
        }

        .co-hero h1 {
            margin: 1rem 0 .55rem;
            max-width: 850px;
            font-size: clamp(3rem, 7vw, 6.2rem);
            line-height: .93;
            letter-spacing: -.065em;
            color: #151528;
        }

        .co-gradient-text {
            background: linear-gradient(90deg, #6842f2 0%, #8b5cf6 50%, #5b6df5 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .co-hero-copy {
            max-width: 760px;
            font-size: clamp(1.05rem, 1.8vw, 1.28rem);
            line-height: 1.65;
            color: #625f75;
        }

        .co-chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: .55rem;
            margin-top: 1.3rem;
        }

        .co-chip {
            padding: .5rem .68rem;
            background: rgba(255,255,255,.88);
            border: 1px solid #e5e0ff;
            border-radius: 11px;
            color: #4f4b61;
            font-weight: 650;
            font-size: .84rem;
            box-shadow: 0 6px 18px rgba(87,70,180,.045);
        }

        .co-workspace {
            margin-top: 1.6rem;
            border-radius: 24px;
            border: 1px solid #e5e0ff;
            background: linear-gradient(145deg, rgba(255,255,255,.72), rgba(239,235,255,.82));
            overflow: hidden;
            min-height: 220px;
        }

        .co-login-title {
            margin: 0 0 .2rem;
            font-size: 1.55rem;
            line-height: 1.15;
            letter-spacing: -.03em;
        }

        .co-login-copy {
            margin: 0 0 .9rem;
            color: #777286;
            line-height: 1.55;
        }

        .co-demo-note {
            display: flex;
            gap: .55rem;
            align-items: flex-start;
            margin-top: .7rem;
            padding: .72rem .85rem;
            border-radius: 12px;
            background: #f6f3ff;
            border: 1px solid #e8e2ff;
            color: #645f77;
            font-size: .82rem;
            line-height: 1.45;
        }

        .co-dashboard-hero {
            display: grid;
            grid-template-columns: minmax(0, 1.35fr) minmax(300px, .65fr);
            gap: 1rem;
            margin: 1.1rem 0 1.25rem;
        }

        .co-dashboard-main,
        .co-robot-panel {
            position: relative;
            overflow: hidden;
            border: 1px solid var(--chargeops-line);
            border-radius: 24px;
            background: rgba(255,255,255,.90);
            box-shadow: 0 18px 50px rgba(87,70,180,.09);
        }

        .co-dashboard-main {
            padding: 1.45rem 1.55rem;
        }

        .co-dashboard-main h2 {
            margin: 0 0 .4rem;
            font-size: clamp(1.65rem, 2.8vw, 2.35rem);
            letter-spacing: -.045em;
            color: #19192d;
        }

        .co-dashboard-main p {
            margin: 0;
            color: #706c80;
        }

        .co-dashboard-meta {
            display: flex;
            flex-wrap: wrap;
            gap: .55rem;
            margin-top: 1rem;
        }

        .co-meta-card {
            min-width: 150px;
            padding: .75rem .85rem;
            border-radius: 13px;
            background: #faf9ff;
            border: 1px solid #ece8ff;
        }

        .co-meta-label {
            color: #8b8797;
            font-size: .75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: .055em;
        }

        .co-meta-value {
            margin-top: .15rem;
            color: #27263a;
            font-size: .95rem;
            font-weight: 760;
        }

        .co-robot-panel {
            min-height: 195px;
            background:
                radial-gradient(circle at 50% 38%, rgba(126, 87, 255, .18), transparent 45%),
                linear-gradient(145deg, #f7f5ff, #eeeaff);
        }

        .co-robot-panel svg,
        .co-workspace svg {
            width: 100%;
            height: 100%;
            display: block;
        }

        .co-section-title {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin: 1.25rem 0 .55rem;
        }

        .co-section-title h3 {
            margin: 0;
            font-size: 1.05rem;
            color: #333044;
            letter-spacing: -.02em;
        }

        @media (max-width: 1000px) {
            .co-dashboard-hero {
                grid-template-columns: 1fr;
            }
            .co-robot-panel {
                min-height: 170px;
            }
        }

        @media (max-width: 760px) {
            .block-container {
                padding-left: .8rem;
                padding-right: .8rem;
            }
            .co-topbar {
                padding: .72rem .8rem;
            }
            .co-status {
                font-size: .76rem;
            }
            .co-hero {
                min-height: unset;
                padding: 1.25rem;
                border-radius: 22px;
            }
            .co-hero h1 {
                font-size: clamp(2.8rem, 16vw, 4.5rem);
            }
            .co-workspace {
                min-height: 170px;
            }
            [data-testid="stTabs"] [data-baseweb="tab-list"] {
                border-radius: 13px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def robot_workspace_svg() -> str:
    """Small inline SVG so the robotic-workspace look ships in app.py."""
    return """
    <svg viewBox="0 0 760 300" role="img" aria-label="Robotic EV operations workspace">
      <defs>
        <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stop-color="#fcfbff"/>
          <stop offset="1" stop-color="#e9e4ff"/>
        </linearGradient>
        <linearGradient id="purple" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stop-color="#9b7cff"/>
          <stop offset="1" stop-color="#5e3bf3"/>
        </linearGradient>
        <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="6" result="b"/>
          <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
        </filter>
      </defs>
      <rect width="760" height="300" fill="url(#bg)"/>
      <g opacity=".55" stroke="#c9c0ff" stroke-width="1">
        <path d="M0 245H760M0 268H760"/>
        <path d="M90 210V300M180 210V300M270 210V300M360 210V300M450 210V300M540 210V300M630 210V300"/>
      </g>
      <g transform="translate(42 42)">
        <rect x="0" y="0" width="318" height="170" rx="18" fill="#fff" opacity=".92" stroke="#ddd6fe"/>
        <rect x="20" y="20" width="78" height="54" rx="12" fill="#f6f3ff" stroke="#e9e2ff"/>
        <rect x="112" y="20" width="78" height="54" rx="12" fill="#f6f3ff" stroke="#e9e2ff"/>
        <rect x="204" y="20" width="94" height="54" rx="12" fill="#f6f3ff" stroke="#e9e2ff"/>
        <circle cx="44" cy="45" r="10" fill="#8b5cf6" opacity=".2"/>
        <path d="M42 50l12-16v10h8L48 61V50z" fill="#6d4aff"/>
        <path d="M24 131 C65 116 88 140 124 117 S192 125 222 94 S270 103 292 78" fill="none" stroke="#6d4aff" stroke-width="5" stroke-linecap="round"/>
        <path d="M24 146H292" stroke="#ebe7ff" stroke-width="2"/>
        <circle cx="292" cy="78" r="5" fill="#6d4aff"/>
      </g>
      <g transform="translate(470 26)">
        <ellipse cx="118" cy="232" rx="115" ry="18" fill="#8b5cf6" opacity=".10"/>
        <ellipse cx="118" cy="224" rx="72" ry="12" fill="none" stroke="#8b5cf6" stroke-width="3" opacity=".55"/>
        <ellipse cx="118" cy="224" rx="42" ry="7" fill="none" stroke="#6d4aff" stroke-width="2" filter="url(#glow)"/>
        <rect x="82" y="184" width="78" height="45" rx="18" fill="#f8f7ff" stroke="#bfb4ff" stroke-width="4"/>
        <circle cx="120" cy="184" r="23" fill="#fff" stroke="#b9adff" stroke-width="7"/>
        <g transform="rotate(-30 120 184)">
          <rect x="111" y="95" width="20" height="92" rx="10" fill="#fff" stroke="#b9adff" stroke-width="6"/>
          <circle cx="121" cy="94" r="19" fill="#fff" stroke="#b9adff" stroke-width="7"/>
          <rect x="113" y="41" width="16" height="62" rx="8" fill="#fff" stroke="#b9adff" stroke-width="6"/>
          <circle cx="121" cy="40" r="16" fill="#fff" stroke="#b9adff" stroke-width="6"/>
          <rect x="116" y="12" width="10" height="31" rx="5" fill="url(#purple)"/>
        </g>
        <path d="M121 15 C120 42 96 50 85 63" fill="none" stroke="#6d4aff" stroke-width="3" stroke-dasharray="5 6" opacity=".55"/>
      </g>
      <g transform="translate(646 72)">
        <rect x="0" y="0" width="54" height="132" rx="18" fill="#222038"/>
        <rect x="7" y="8" width="40" height="116" rx="13" fill="#faf9ff" stroke="#8b5cf6" stroke-width="3"/>
        <circle cx="27" cy="41" r="13" fill="url(#purple)"/>
        <path d="M24 49l10-15v9h7L28 58v-9z" fill="#fff" transform="scale(.72) translate(10 16)"/>
        <path d="M45 91 C77 102 60 134 38 145" fill="none" stroke="#353247" stroke-width="6" stroke-linecap="round"/>
      </g>
      <g opacity=".72">
        <rect x="375" y="56" width="100" height="54" rx="13" fill="#fff" stroke="#d8d0ff"/>
        <path d="M392 91h65" stroke="#ddd7ff" stroke-width="4" stroke-linecap="round"/>
        <path d="M392 78h38" stroke="#8b5cf6" stroke-width="5" stroke-linecap="round"/>
        <circle cx="448" cy="78" r="7" fill="#22c55e" opacity=".75"/>
      </g>
    </svg>
    """


def render_topbar() -> None:
    st.markdown(
        """
        <div class="co-topbar">
          <div class="co-brand">
            <span class="co-logo">ϟ</span>
            <span>ChargeOps <span class="co-ai">AI</span></span>
          </div>
          <div class="co-status"><span class="co-status-dot"></span> All systems operational</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_login_hero() -> None:
    st.markdown(
        f"""
        <div class="co-hero">
          <span class="co-eyebrow">✦ Production agentic EV operations</span>
          <h1>AI operations,<br><span class="co-gradient-text">under control.</span></h1>
          <div class="co-hero-copy">
            One bright control plane for EV charging operations, RAG knowledge,
            demand forecasting, incident response, human approvals and production observability.
          </div>
          <div class="co-chip-row">
            <span class="co-chip">⚡ Station intelligence</span>
            <span class="co-chip">🤖 Agentic workflows</span>
            <span class="co-chip">◈ RAG knowledge</span>
            <span class="co-chip">↗ Demand forecasting</span>
            <span class="co-chip">◎ Observability</span>
          </div>
          <div class="co-workspace">{robot_workspace_svg()}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_dashboard_header(
    current_user: dict,
    user_role: str,
    station_id: str,
    station_name: str,
    charger_model: str,
    location: str,
    station_status: str,
) -> None:
    status_text = station_status.title()
    email = current_user.get("email", "Unknown user")
    st.markdown(
        f"""
        <div class="co-dashboard-hero">
          <div class="co-dashboard-main">
            <span class="co-eyebrow">✦ Intelligent EV operations</span>
            <h2>ChargeOps <span class="co-gradient-text">Control Plane</span></h2>
            <p>Forecast demand, investigate incidents, retrieve RAG knowledge and supervise AI actions from one operational workspace.</p>
            <div class="co-dashboard-meta">
              <div class="co-meta-card"><div class="co-meta-label">Station</div><div class="co-meta-value">{station_id} — {station_name}</div></div>
              <div class="co-meta-card"><div class="co-meta-label">Charger</div><div class="co-meta-value">{charger_model}</div></div>
              <div class="co-meta-card"><div class="co-meta-label">Location</div><div class="co-meta-value">{location}</div></div>
              <div class="co-meta-card"><div class="co-meta-label">Status</div><div class="co-meta-value">{status_text}</div></div>
              <div class="co-meta-card"><div class="co-meta-label">Signed in</div><div class="co-meta-value">{email} · {user_role.title()}</div></div>
            </div>
          </div>
          <div class="co-robot-panel">{robot_workspace_svg()}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


inject_chargeops_theme()


# =================================================
# Backend API functions
# =================================================


def check_backend() -> bool:
    try:
        response = httpx.get(
            f"{API_BASE_URL}/health",
            timeout=3.0,
        )

        return response.status_code == 200

    except httpx.HTTPError:
        return False


def clear_auth_session() -> None:
    keys_to_clear = (
        "access_token",
        "current_user",
        "agent_thread_ids",
        "pending_approvals",
        "chat_histories",
    )

    for key in keys_to_clear:
        st.session_state.pop(
            key,
            None,
        )


def login_user(
    email: str,
    password: str,
) -> str:
    response = httpx.post(
        f"{API_BASE_URL}/auth/login",
        data={
            "username": email,
            "password": password,
        },
        timeout=10.0,
    )

    response.raise_for_status()

    payload = response.json()

    return str(
        payload["access_token"]
    )


def get_current_user(
    access_token: str,
) -> dict:
    response = httpx.get(
        f"{API_BASE_URL}/auth/me",
        headers={
            "Authorization": (
                f"Bearer {access_token}"
            ),
        },
        timeout=10.0,
    )

    response.raise_for_status()

    return response.json()


def authenticated_request(
    method: str,
    path: str,
    access_token: str,
    timeout: float,
    **kwargs,
) -> httpx.Response:
    headers = dict(
        kwargs.pop(
            "headers",
            {},
        )
    )

    headers["Authorization"] = (
        f"Bearer {access_token}"
    )

    response = httpx.request(
        method=method,
        url=f"{API_BASE_URL}{path}",
        headers=headers,
        timeout=timeout,
        **kwargs,
    )

    if response.status_code == 401:
        clear_auth_session()
        st.cache_data.clear()

        st.warning(
            "Your ChargeOps session expired. "
            "Please sign in again."
        )

        st.rerun()

    response.raise_for_status()

    return response


@st.cache_data(
    ttl=10
)
def get_agent_runs(
    access_token: str,
    station_id: str | None = None,
    limit: int = 100,
) -> list[dict]:
    params: dict[
        str,
        str | int,
    ] = {
        "limit": limit,
    }

    if station_id:
        params[
            "station_id"
        ] = station_id

    response = authenticated_request(
        method="GET",
        path="/observability/runs",
        access_token=access_token,
        params=params,
        timeout=10.0,
    )

    return response.json()


@st.cache_data(ttl=300)
def get_station_forecast(
    access_token: str,
    station_id: str,
    hours: int = 24,
) -> dict:
    response = authenticated_request(
        method="GET",
        path=(
            "/forecast/stations/"
            f"{station_id}"
        ),
        access_token=(
            access_token
        ),
        params={
            "hours": hours,
        },
        timeout=20.0,
    )

    return response.json()

@st.cache_data(ttl=30)
def get_stations(
    access_token: str,
) -> list[dict]:
    response = authenticated_request(
        method="GET",
        path="/stations",
        access_token=access_token,
        timeout=5.0,
    )

    return response.json()


@st.cache_data(ttl=10)
def get_incidents(
    access_token: str,
    station_id: str,
) -> list[dict]:
    response = authenticated_request(
        method="GET",
        path="/incidents",
        access_token=access_token,
        params={
            "station_id": station_id,
            "limit": 100,
        },
        timeout=5.0,
    )

    return response.json()


def run_agent(
    access_token: str,
    station_id: str,
    message: str,
    thread_id: str,
) -> dict:
    response = authenticated_request(
        method="POST",
        path="/agent/run",
        access_token=access_token,
        json={
            "station_id": station_id,
            "message": message,
            "thread_id": thread_id,
        },
        timeout=90.0,
    )

    return response.json()


def resume_agent(
    access_token: str,
    thread_id: str,
    approved: bool,
) -> dict:
    response = authenticated_request(
        method="POST",
        path="/agent/resume",
        access_token=access_token,
        json={
            "thread_id": thread_id,
            "approved": approved,
        },
        timeout=90.0,
    )

    return response.json()


@st.cache_data(ttl=15)
def get_knowledge_documents(
    access_token: str,
) -> list[dict]:
    response = authenticated_request(
        method="GET",
        path="/knowledge/documents",
        access_token=access_token,
        timeout=10.0,
    )

    return response.json()


def update_incident_status(
    access_token: str,
    incident_id: int,
    status: str,
) -> dict:
    response = authenticated_request(
        method="PATCH",
        path=(
            f"/incidents/{incident_id}"
        ),
        access_token=access_token,
        json={
            "status": status,
        },
        timeout=5.0,
    )

    return response.json()


def upload_knowledge_document(
    access_token: str,
    file_name: str,
    file_type: str,
    file_content: bytes,
    title: str,
    category: str,
) -> dict:
    response = authenticated_request(
        method="POST",
        path=(
            "/knowledge/documents/upload"
        ),
        access_token=access_token,
        files={
            "file": (
                file_name,
                file_content,
                file_type,
            ),
        },
        data={
            "title": title,
            "category": category,
        },
        timeout=120.0,
    )

    return response.json()


def delete_knowledge_document(
    access_token: str,
    document_id: int,
) -> None:
    authenticated_request(
        method="DELETE",
        path=(
            "/knowledge/documents/"
            f"{document_id}"
        ),
        access_token=access_token,
        timeout=10.0,
    )


def search_knowledge(
    access_token: str,
    query: str,
    limit: int,
) -> dict:
    response = authenticated_request(
        method="POST",
        path="/knowledge/search",
        access_token=access_token,
        json={
            "query": query,
            "limit": limit,
        },
        timeout=60.0,
    )

    return response.json()


@st.cache_data(ttl=10)
def get_users(
    access_token: str,
) -> list[dict]:
    response = authenticated_request(
        method="GET",
        path="/users",
        access_token=access_token,
        timeout=10.0,
    )

    return response.json()


def create_chargeops_user(
    access_token: str,
    email: str,
    password: str,
    role: str,
) -> dict:
    response = authenticated_request(
        method="POST",
        path="/users",
        access_token=access_token,
        json={
            "email": email,
            "password": password,
            "role": role,
        },
        timeout=10.0,
    )

    return response.json()


def change_user_role(
    access_token: str,
    user_id: str,
    role: str,
) -> dict:
    response = authenticated_request(
        method="PATCH",
        path=(
            f"/users/{user_id}/role"
        ),
        access_token=access_token,
        json={
            "role": role,
        },
        timeout=10.0,
    )

    return response.json()


def change_user_status(
    access_token: str,
    user_id: str,
    is_active: bool,
) -> dict:
    response = authenticated_request(
        method="PATCH",
        path=(
            f"/users/{user_id}/status"
        ),
        access_token=access_token,
        json={
            "is_active": is_active,
        },
        timeout=10.0,
    )

    return response.json()


# =================================================
# UI helper functions
# =================================================


def show_tool_activity(
    tools: list[str],
    trace: list[dict],
) -> None:
    if not tools:
        st.caption(
            "💬 No external tools required"
        )
        return

    st.caption(
        "🔧 Tools used: "
        + ", ".join(tools)
    )

    with st.expander(
        "🔍 Agent Activity",
        expanded=True,
    ):
        for event in trace:
            tool_name = event.get(
                "tool",
                "unknown_tool",
            )

            summary = event.get(
                "summary",
                "Completed.",
            )

            status = event.get(
                "status",
                "success",
            )

            if status == "error":
                st.error(
                    f"{tool_name}: {summary}"
                )

            else:
                st.success(
                    f"{tool_name}: {summary}"
                )


def show_severity(
    severity: str,
) -> None:
    severity_lower = severity.lower()

    if severity_lower == "critical":
        st.error(
            "🔴 Critical"
        )

    elif severity_lower == "high":
        st.warning(
            "🟠 High"
        )

    elif severity_lower == "medium":
        st.info(
            "🟡 Medium"
        )

    else:
        st.success(
            "🟢 Low"
        )


def show_http_error(
    error: httpx.HTTPStatusError,
) -> None:
    try:
        payload = error.response.json()

        detail = payload.get(
            "detail",
            "Unknown backend error",
        )

    except ValueError:
        detail = error.response.text

    st.error(
        f"Backend error "
        f"({error.response.status_code}): "
        f"{detail}"
    )


# =================================================
# Main shell / health
# =================================================


render_topbar()


# =================================================
# Backend health
# =================================================


if not check_backend():
    st.error(
        "ChargeOps backend is unavailable."
    )

    st.info(
        "Start FastAPI with "
        "`uvicorn app.main:app --reload`"
    )

    st.stop()


# =================================================
# Authentication
# =================================================


access_token = st.session_state.get(
    "access_token"
)

if not access_token:
    hero_col, login_col = st.columns(
        [1.35, 0.65],
        gap="large",
    )

    with hero_col:
        render_login_hero()

    with login_col:
        st.markdown(
            """
            <h2 class="co-login-title">Experience ChargeOps AI</h2>
            <p class="co-login-copy">
                Demo access is prepared for portfolio visitors. The fields are pre-filled;
                just click <strong>Enter ChargeOps</strong>.
            </p>
            """,
            unsafe_allow_html=True,
        )

        with st.form(
            "chargeops_login_form"
        ):
            email = st.text_input(
                "Email",
                value=DEMO_EMAIL,
            )

            password = st.text_input(
                "Password",
                value=DEMO_PASSWORD,
                type="password",
            )

            login_submitted = (
                st.form_submit_button(
                    "Enter ChargeOps →",
                    use_container_width=True,
                )
            )

        st.markdown(
            """
            <div class="co-demo-note">
              <span>🛡️</span>
              <span>Public demo credentials are loaded from environment variables, so the password does not need to live in your source code.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if login_submitted:
        if not email.strip() or not password:
            st.warning(
                "Enter your email and password."
            )

        else:
            try:
                token = login_user(
                    email=email.strip(),
                    password=password,
                )

                user = get_current_user(
                    token
                )

                st.session_state[
                    "access_token"
                ] = token

                st.session_state[
                    "current_user"
                ] = user

                st.cache_data.clear()
                st.rerun()

            except (
                httpx.HTTPStatusError
            ) as error:
                if (
                    error.response.status_code
                    == 401
                ):
                    st.error(
                        "Incorrect email or password."
                    )

                else:
                    show_http_error(
                        error
                    )

            except httpx.HTTPError as error:
                st.error(
                    "Could not connect to the "
                    "ChargeOps authentication service."
                )

                st.caption(
                    str(error)
                )

    st.stop()


try:
    current_user = get_current_user(
        access_token
    )

    st.session_state[
        "current_user"
    ] = current_user

except httpx.HTTPStatusError as error:
    if error.response.status_code == 401:
        clear_auth_session()
        st.cache_data.clear()

        st.warning(
            "Your ChargeOps session expired. "
            "Please sign in again."
        )

        st.rerun()

    show_http_error(
        error
    )
    st.stop()

except httpx.HTTPError as error:
    st.error(
        "Could not validate your ChargeOps session."
    )

    st.caption(
        str(error)
    )

    st.stop()


user_role = str(
    current_user.get(
        "role",
        "viewer",
    )
)

is_operator = user_role in {
    "operator",
    "admin",
}

is_admin = user_role == "admin"


# =================================================
# Load stations
# =================================================


try:
    stations = get_stations(
        access_token
    )

except httpx.HTTPError as error:
    st.error(
        "Could not retrieve charging stations."
    )

    st.caption(
        str(error)
    )

    st.stop()


if not stations:
    st.warning(
        "No charging stations are available."
    )

    st.stop()


# =================================================
# Sidebar
# =================================================


with st.sidebar:
    st.header(
        "👤 Signed In"
    )

    st.write(
        current_user.get(
            "email",
            "Unknown user",
        )
    )

    st.caption(
        f"Role: {user_role.title()}"
    )

    if st.button(
        "🚪 Log out",
        use_container_width=True,
    ):
        clear_auth_session()
        st.cache_data.clear()
        st.rerun()

    st.divider()

    st.header(
        "⚡ Station Context"
    )

    st.success(
        "Backend connected"
    )

    station_lookup = {
        (
            f"{station['station_id']} — "
            f"{station['name']}"
        ): station
        for station in stations
    }

    selected_station_label = st.selectbox(
        "Charging Station",
        options=list(
            station_lookup.keys()
        ),
    )

    selected_station = station_lookup[
        selected_station_label
    ]

    station_id = selected_station[
        "station_id"
    ]

    station_name = selected_station[
        "name"
    ]

    charger_model = selected_station[
        "charger_model"
    ]

    location = selected_station[
        "location"
    ]

    latitude = selected_station[
        "latitude"
    ]

    longitude = selected_station[
        "longitude"
    ]

    station_status = selected_station[
        "status"
    ]

    st.divider()

    st.subheader(
        "Station Details"
    )

    st.write(
        f"**ID:** {station_id}"
    )

    st.write(
        f"**Name:** {station_name}"
    )

    st.write(
        f"**Model:** {charger_model}"
    )

    st.write(
        f"**Location:** {location}"
    )

    st.caption(
        f"{latitude:.6f}, "
        f"{longitude:.6f}"
    )

    if station_status.lower() == "active":
        st.success(
            "● Active"
        )

    elif (
        station_status.lower()
        == "maintenance"
    ):
        st.warning(
            "● Maintenance"
        )

    else:
        st.info(
            f"● {station_status.title()}"
        )

    st.divider()

    if st.button(
        "🔄 Refresh Data",
        use_container_width=True,
    ):
        st.cache_data.clear()

        st.rerun()




render_dashboard_header(
    current_user=current_user,
    user_role=user_role,
    station_id=station_id,
    station_name=station_name,
    charger_model=charger_model,
    location=location,
    station_status=station_status,
)


# =================================================
# Load operational data
# =================================================


try:
    incidents = get_incidents(
        access_token,
        station_id,
    )

except httpx.HTTPError:
    incidents = []


try:
    knowledge_documents = (
        get_knowledge_documents(
            access_token
        )
    )

except httpx.HTTPError:
    knowledge_documents = []


# =================================================
# Top metrics
# =================================================


total_incidents = len(
    incidents
)

open_incidents = sum(
    incident["status"] == "open"
    for incident in incidents
)

investigating_incidents = sum(
    incident["status"] == "investigating"
    for incident in incidents
)

resolved_incidents = sum(
    incident["status"] == "resolved"
    for incident in incidents
)


metric1, metric2, metric3, metric4 = (
    st.columns(4)
)

with metric1:
    st.metric(
        "Total Incidents",
        total_incidents,
    )

with metric2:
    st.metric(
        "Open",
        open_incidents,
    )

with metric3:
    st.metric(
        "Investigating",
        investigating_incidents,
    )

with metric4:
    st.metric(
        "Resolved",
        resolved_incidents,
    )


st.divider()


# =================================================
# Main tabs
# =================================================


tab_labels = [
    "AI Agent",
    "Demand Forecast",
    "Incidents",
    "Knowledge",
    "Observability",
]

if is_admin:
    tab_labels.append(
        "Users"
    )

tab_labels.append(
    "System"
)

tabs = st.tabs(
    tab_labels
)


tab_agent = tabs[0]
tab_forecast = tabs[1]
tab_incidents = tabs[2]
tab_knowledge = tabs[3]
tab_observability = tabs[4]

if is_admin:
    tab_users = tabs[5]
    tab_system = tabs[6]

else:
    tab_users = None
    tab_system = tabs[5]


# =================================================
# Agent tab
# =================================================


with tab_agent:
    st.subheader(
        "ChargeOps Operations Agent"
    )

    st.write(
        "Ask questions about the selected charging "
        "station, diagnose faults using the technical "
        "knowledge base, check current weather, "
        "or retrieve previous incident history."
    )

    st.info(
        f"Selected station: "
        f"**{station_id} — {station_name}**"
    )

    if not is_operator:
        st.caption(
            "Viewer mode: safe read-only agent queries "
            "are available. Operational diagnosis and "
            "status-changing actions are blocked by RBAC."
        )
    
    if (
        "agent_thread_ids"
        not in st.session_state
    ):
        st.session_state.agent_thread_ids = {}


    if (
        station_id
        not in st.session_state.agent_thread_ids
    ):
        st.session_state.agent_thread_ids[
            station_id
        ] = str(
            uuid4()
        )


    thread_id = (
        st.session_state.agent_thread_ids[
            station_id
        ]
    )

    if (
        "pending_approvals"
        not in st.session_state
    ):
        st.session_state.pending_approvals = {}

    st.caption(
        "Conversation thread: "
        f"`{thread_id}`"
    )
    if st.button(
        "➕ New Conversation",
        key=(
            f"new_conversation_"
            f"{station_id}"
        ),
    ):
        new_thread_id = str(
            uuid4()
        )

        st.session_state.agent_thread_ids[
            station_id
        ] = new_thread_id

        st.session_state.chat_histories[
            new_thread_id
        ] = []

        st.rerun()


    if (
        "chat_histories"
        not in st.session_state
    ):
        st.session_state.chat_histories = {}

    if (
        thread_id
        not in st.session_state.chat_histories
    ):
        st.session_state.chat_histories[
            thread_id
        ] = []


    messages = (
        st.session_state.chat_histories[
            thread_id
        ]
    )

    for message in messages:
        with st.chat_message(
            message["role"]
        ):
            st.markdown(
                message["content"]
            )

            if (
                message["role"]
                == "assistant"
            ):
                show_tool_activity(
                    message.get(
                        "tools",
                        [],
                    ),
                    message.get(
                        "trace",
                        [],
                    ),
                )


    pending_approval = (
        st.session_state
        .pending_approvals
        .get(
            thread_id
        )
    )
    
    
    if pending_approval and is_operator:
        st.warning(
            "⚠️ Protected Operation "
            "Requires Approval"
        )
    
        st.write(
            "**Action:** "
            f"{pending_approval['action']}"
        )
    
        st.write(
            "**Station:** "
            f"{pending_approval['station_id']} — "
            f"{pending_approval['station_name']}"
        )
    
        st.write(
            "**Current status:** "
            f"{pending_approval['current_status']}"
        )
    
        st.write(
            "**Requested status:** "
            f"{pending_approval['requested_status']}"
        )
    
        st.caption(
            pending_approval[
                "warning"
            ]
        )
    
        approve_col, reject_col = (
            st.columns(2)
        )
    
        with approve_col:
            if st.button(
                "✅ Approve",
                key=(
                    f"approve_"
                    f"{thread_id}"
                ),
                use_container_width=True,
            ):
                with st.spinner(
                    "Resuming approved workflow..."
                ):
                    result = resume_agent(
                        access_token=access_token,
                        thread_id=thread_id,
                        approved=True,
                    )
    
                st.session_state.pending_approvals.pop(
                    thread_id,
                    None,
                )
    
                if result.get(
                    "approval_required"
                ):
                    st.session_state.pending_approvals[
                        thread_id
                    ] = result[
                        "approval_request"
                    ]
    
                elif result.get(
                    "answer"
                ):
                    messages.append(
                        {
                            "role": "assistant",
                            "content": (
                                result["answer"]
                            ),
                            "tools": result.get(
                                "used_tools",
                                [],
                            ),
                            "trace": result.get(
                                "trace",
                                [],
                            ),
                        }
                    )
    
                st.cache_data.clear()
    
                st.rerun()
    
        with reject_col:
            if st.button(
                "❌ Reject",
                key=(
                    f"reject_"
                    f"{thread_id}"
                ),
                use_container_width=True,
            ):
                with st.spinner(
                    "Cancelling protected action..."
                ):
                    result = resume_agent(
                        access_token=access_token,
                        thread_id=thread_id,
                        approved=False,
                    )
    
                st.session_state.pending_approvals.pop(
                    thread_id,
                    None,
                )
    
                if result.get(
                    "answer"
                ):
                    messages.append(
                        {
                            "role": "assistant",
                            "content": (
                                result["answer"]
                            ),
                            "tools": result.get(
                                "used_tools",
                                [],
                            ),
                            "trace": result.get(
                                "trace",
                                [],
                            ),
                        }
                    )
    
                st.rerun()

    prompt = st.chat_input(
        "Ask ChargeOps about this station..."
    )
    
    if prompt:
        messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )
    
        with st.chat_message(
            "user"
        ):
            st.markdown(
                prompt
            )
    
        with st.chat_message(
            "assistant"
        ), st.spinner(
            "ChargeOps AI is analyzing..."
        ):
            try:
                result = run_agent(
                    access_token=access_token,
                    station_id=station_id,
                    message=prompt,
                    thread_id=thread_id,
                )
    
                # =================================
                # HUMAN APPROVAL CHECK
                # =================================
    
                if result.get(
                    "approval_required"
                ):
                    st.session_state.pending_approvals[
                        thread_id
                    ] = result[
                        "approval_request"
                    ]
    
                    # Clear cached station data
                    # before rerendering the page.
                    st.cache_data.clear()
    
                    # Rerun Streamlit so the
                    # approval card appears.
                    st.rerun()
    
                # =================================
                # NORMAL COMPLETED RESPONSE
                # =================================
    
                answer = result.get(
                    "answer",
                    "No response returned.",
                )
    
                tools = result.get(
                    "used_tools",
                    [],
                )
    
                trace = result.get(
                    "trace",
                    [],
                )
    
                st.markdown(
                    answer
                )
    
                show_tool_activity(
                    tools,
                    trace,
                )
    
                messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "tools": tools,
                        "trace": trace,
                    }
                )
    
                st.cache_data.clear()
    
            except (
                httpx.HTTPStatusError
            ) as error:
                show_http_error(
                    error
                )
    
            except httpx.HTTPError as error:
                st.error(
                    "Could not connect to "
                    "ChargeOps backend."
                )
    
                st.caption(
                    str(error)
                )


# =================================================
# Demand Forecast tab
# =================================================


with tab_forecast:
    st.subheader(
        "EV Charging Demand Forecast"
    )

    st.caption(
        "Machine-learning forecast using "
        "historical charging demand, temporal "
        "patterns, weather, spatial station "
        "features, and mobility signals."
    )

    forecast_hours = st.selectbox(
        "Forecast horizon",
        options=[
            12,
            24,
            48,
        ],
        index=1,
    )

    try:
        with st.spinner(
            "Generating demand forecast..."
        ):
            forecast = (
                get_station_forecast(
                    access_token,
                    station_id,
                    forecast_hours,
                )
            )

        summary = (
            forecast[
                "summary"
            ]
        )

        metric1, metric2, metric3, metric4 = (
            st.columns(
                4
            )
        )

        with metric1:
            st.metric(
                "Peak Demand",
                (
                    f"{summary['peak_energy_kwh']:.1f} "
                    "kWh"
                ),
            )

        with metric2:
            st.metric(
                "Total Forecast",
                (
                    f"{summary['total_predicted_energy_kwh']:.1f} "
                    "kWh"
                ),
            )

        with metric3:
            st.metric(
                "Average / Hour",
                (
                    f"{summary['average_hourly_energy_kwh']:.1f} "
                    "kWh"
                ),
            )

        with metric4:
            risk = (
                forecast[
                    "peak_risk"
                ]
            )

            if risk == "high":
                st.error(
                    "Peak risk: HIGH"
                )

            elif risk == "medium":
                st.warning(
                    "Peak risk: MEDIUM"
                )

            else:
                st.success(
                    "Peak risk: LOW"
                )

        st.caption(
            "Peak expected at "
            f"{summary['peak_timestamp']}"
        )

        points = pd.DataFrame(
            forecast[
                "points"
            ]
        )

        points[
            "timestamp"
        ] = pd.to_datetime(
            points[
                "timestamp"
            ]
        )

        st.markdown(
            "### Predicted hourly demand"
        )

        st.line_chart(
            points,
            x="timestamp",
            y=(
                "predicted_energy_kwh"
            ),
        )

        st.markdown(
            "### Forecast details"
        )

        st.dataframe(
            points[
                [
                    "timestamp",
                    "predicted_energy_kwh",
                    "risk_level",
                    "temperature_c",
                    "precipitation_mm",
                    "mobility_index",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

        st.divider()

        st.write(
            "**Model:**",
            forecast[
                "model_version"
            ],
        )

        st.write(
            "**History source:**",
            forecast[
                "history_source"
            ],
        )

        st.write(
            "**Weather source:**",
            forecast[
                "weather_source"
            ],
        )

        if (
            forecast[
                "history_source"
            ]
            == "demo_simulation"
        ):
            st.warning(
                "This forecasting demo currently "
                "uses simulated charging history. "
                "It must not be interpreted as "
                "measured ChargeOps operational data."
            )

    except httpx.HTTPStatusError as error:
        show_http_error(
            error
        )

    except httpx.HTTPError as error:
        st.error(
            "Could not connect to the "
            "ChargeOps forecasting service."
        )

        st.caption(
            str(
                error
            )
        )


# =================================================
# Incidents tab
# =================================================


with tab_incidents:
    st.subheader(
        "Incident Management"
    )

    st.write(
        f"Operational incident history for "
        f"**{station_id} — {station_name}**."
    )

    if not incidents:
        st.info(
            "No incidents have been recorded "
            "for this station yet."
        )

    else:
        status_filter = st.selectbox(
            "Filter by status",
            [
                "All",
                "Open",
                "Investigating",
                "Resolved",
            ],
        )

        if status_filter == "All":
            filtered_incidents = incidents

        else:
            filtered_incidents = [
                incident
                for incident in incidents
                if incident["status"]
                == status_filter.lower()
            ]

        st.caption(
            f"Showing "
            f"{len(filtered_incidents)} "
            f"incident(s)"
        )

        for incident in filtered_incidents:
            incident_id = incident["id"]

            severity = incident[
                "severity"
            ]

            status = incident[
                "status"
            ]

            title = (
                f"Incident #{incident_id} — "
                f"{severity.upper()} — "
                f"{status.upper()}"
            )

            with st.expander(
                title,
                expanded=False,
            ):
                col1, col2, col3, col4 = (
                    st.columns(4)
                )

                with col1:
                    st.metric(
                        "Incident ID",
                        f"#{incident_id}",
                    )

                with col2:
                    st.metric(
                        "Category",
                        incident[
                            "category"
                        ].title(),
                    )

                with col3:
                    st.metric(
                        "Confidence",
                        (
                            f"{incident['confidence']:.0%}"
                        ),
                    )

                with col4:
                    st.metric(
                        "Status",
                        status.title(),
                    )

                show_severity(
                    severity
                )

                st.markdown(
                    "### Reported Issue"
                )

                st.write(
                    incident["issue"]
                )

                st.markdown(
                    "### AI Diagnostic Summary"
                )

                st.write(
                    incident["summary"]
                )

                st.markdown(
                    "### Likely Causes"
                )

                causes = incident.get(
                    "likely_causes",
                    [],
                )

                if causes:
                    for cause in causes:
                        st.write(
                            f"- {cause}"
                        )

                else:
                    st.caption(
                        "No likely causes recorded."
                    )

                st.markdown(
                    "### Diagnostic Steps"
                )

                steps = incident.get(
                    "diagnostic_steps",
                    [],
                )

                if steps:
                    for step in steps:
                        step_number = step.get(
                            "step",
                            "?",
                        )

                        action = step.get(
                            "action",
                            "",
                        )

                        st.write(
                            f"**{step_number}.** "
                            f"{action}"
                        )

                else:
                    st.caption(
                        "No diagnostic steps recorded."
                    )

                if incident.get(
                    "needs_human_escalation"
                ):
                    st.warning(
                        "⚠️ Human escalation recommended"
                    )

                created_at = incident.get(
                    "created_at"
                )

                if created_at:
                    st.caption(
                        f"Created: {created_at}"
                    )

                st.divider()

                if is_operator:
                    st.markdown(
                        "### Incident Lifecycle"
                    )

                    valid_statuses = [
                        "open",
                        "investigating",
                        "resolved",
                    ]

                    current_index = (
                        valid_statuses.index(
                            status
                        )
                        if status
                        in valid_statuses
                        else 0
                    )

                    new_status = st.selectbox(
                        "Status",
                        valid_statuses,
                        index=current_index,
                        format_func=lambda value: (
                            value.title()
                        ),
                        key=(
                            f"incident_status_"
                            f"{incident_id}"
                        ),
                    )

                    if st.button(
                        "Update Status",
                        key=(
                            f"update_incident_"
                            f"{incident_id}"
                        ),
                    ):
                        if (
                            new_status
                            == status
                        ):
                            st.info(
                                "Incident already has "
                                "this status."
                            )

                        else:
                            try:
                                update_incident_status(
                                    access_token=access_token,
                                    incident_id=incident_id,
                                    status=new_status,
                                )

                                st.cache_data.clear()

                                st.success(
                                    f"Incident "
                                    f"#{incident_id} "
                                    f"updated."
                                )

                                st.rerun()

                            except (
                                httpx.HTTPStatusError
                            ) as error:
                                show_http_error(
                                    error
                                )

                            except httpx.HTTPError as error:
                                st.error(
                                    "Could not update "
                                    "incident status."
                                )

                                st.caption(
                                    str(error)
                                )

                else:
                    st.caption(
                        "Read-only incident view. "
                        "Operator or admin access is required "
                        "to change incident status."
                    )

# =================================================
# Knowledge Base tab
# =================================================


with tab_knowledge:
    st.subheader(
        
            "Knowledge Base Management"
            if is_admin
            else "Knowledge Base"
        
    )

    if is_admin:
        st.write(
            "Upload technical manuals and operational "
            "documents. ChargeOps automatically extracts "
            "the text, chunks it, creates embeddings, "
            "and stores the vectors in PostgreSQL."
        )

    else:
        st.write(
            "Search and review the ChargeOps technical "
            "knowledge base. Document upload and deletion "
            "are restricted to administrators."
        )

    total_documents = len(
        knowledge_documents
    )

    total_chunks = sum(
        document.get(
            "chunk_count",
            0,
        )
        for document
        in knowledge_documents
    )

    knowledge_metric1, knowledge_metric2 = (
        st.columns(2)
    )

    with knowledge_metric1:
        st.metric(
            "Indexed Documents",
            total_documents,
        )

    with knowledge_metric2:
        st.metric(
            "Document Chunks",
            total_chunks,
        )

    st.divider()

    if is_admin:
        # ---------------------------------------------
        # Upload
        # ---------------------------------------------

        st.markdown(
            "### 📤 Upload Document"
        )

        st.caption(
            "Supported formats: PDF, TXT and Markdown. "
            "Maximum file size: 10 MB."
        )

        with st.form(
            "knowledge_upload_form",
            clear_on_submit=True,
        ):
            uploaded_file = st.file_uploader(
                "Choose technical document",
                type=[
                    "pdf",
                    "txt",
                    "md",
                ],
            )

            upload_title = st.text_input(
                "Document title",
                placeholder=(
                    "Example: ABB Terra 54 "
                    "Installation Manual"
                ),
            )

            upload_category = st.text_input(
                "Category",
                value="manual",
                placeholder=(
                    "manual, networking, hardware..."
                ),
            )

            upload_submitted = (
                st.form_submit_button(
                    "Upload and Index",
                    use_container_width=True,
                )
            )

        if upload_submitted:
            if uploaded_file is None:
                st.warning(
                    "Choose a document first."
                )

            else:
                file_title = (
                    upload_title.strip()
                    or uploaded_file.name
                )

                category = (
                    upload_category.strip()
                    or "manual"
                )

                with st.spinner(
                    "Extracting text, creating chunks "
                    "and generating embeddings..."
                ):
                    try:
                        result = (
                            upload_knowledge_document(
                                access_token=access_token,
                                file_name=(
                                    uploaded_file.name
                                ),
                                file_type=(
                                    uploaded_file.type
                                    or (
                                        "application/"
                                        "octet-stream"
                                    )
                                ),
                                file_content=(
                                    uploaded_file
                                    .getvalue()
                                ),
                                title=file_title,
                                category=category,
                            )
                        )

                        st.success(
                            f"Indexed "
                            f"'{result['title']}' "
                            f"with "
                            f"{result['chunk_count']} "
                            f"chunk(s)."
                        )

                        st.cache_data.clear()

                        st.rerun()

                    except (
                        httpx.HTTPStatusError
                    ) as error:
                        if (
                            error.response.status_code
                            == 409
                        ):
                            st.warning(
                                "This document is already "
                                "in the knowledge base."
                            )

                        else:
                            show_http_error(
                                error
                            )

                    except httpx.HTTPError as error:
                        st.error(
                            "Document upload failed."
                        )

                        st.caption(
                            str(error)
                        )

        st.divider()


    else:
        st.info(
            "🔒 Uploading and indexing knowledge documents "
            "requires the admin role."
        )

    # ---------------------------------------------
    # Semantic Search
    # ---------------------------------------------

    st.markdown(
        "### 🔎 Semantic Search"
    )

    st.write(
        "Search the knowledge base by meaning, "
        "not only by exact keywords."
    )

    with st.form(
        "knowledge_search_form"
    ):
        knowledge_query = (
            st.text_input(
                "Search query",
                placeholder=(
                    "Example: charger cable "
                    "becomes extremely hot"
                ),
            )
        )

        search_limit = st.slider(
            "Number of results",
            min_value=1,
            max_value=10,
            value=5,
        )

        search_submitted = (
            st.form_submit_button(
                "Search Knowledge Base"
            )
        )

    if search_submitted:
        if len(
            knowledge_query.strip()
        ) < 3:
            st.warning(
                "Enter a longer search query."
            )

        else:
            with st.spinner(
                "Creating query embedding "
                "and searching pgvector..."
            ):
                try:
                    search_response = (
                        search_knowledge(
                            access_token=access_token,
                            query=(
                                knowledge_query
                                .strip()
                            ),
                            limit=search_limit,
                        )
                    )

                    search_results = (
                        search_response.get(
                            "results",
                            [],
                        )
                    )

                    if not search_results:
                        st.info(
                            "No matching knowledge "
                            "was found."
                        )

                    else:
                        st.success(
                            f"Found "
                            f"{len(search_results)} "
                            f"semantic result(s)."
                        )

                        for index, result in enumerate(
                            search_results,
                            start=1,
                        ):
                            similarity = result.get(
                                "similarity",
                                0.0,
                            )

                            result_title = (
                                result.get(
                                    "title",
                                    "Untitled",
                                )
                            )

                            with st.expander(
                                (
                                    f"{index}. "
                                    f"{result_title} "
                                    f"— "
                                    f"{similarity:.0%}"
                                ),
                                expanded=(
                                    index == 1
                                ),
                            ):
                                meta1, meta2 = (
                                    st.columns(2)
                                )

                                with meta1:
                                    st.write(
                                        "**Category:** "
                                        f"{result.get('category')}"
                                    )

                                with meta2:
                                    st.write(
                                        "**Source:** "
                                        f"{result.get('source')}"
                                    )

                                st.caption(
                                    "Semantic similarity: "
                                    f"{similarity:.4f}"
                                )

                                st.markdown(
                                    "#### Retrieved Chunk"
                                )

                                st.write(
                                    result.get(
                                        "content",
                                        "",
                                    )
                                )

                except (
                    httpx.HTTPStatusError
                ) as error:
                    show_http_error(
                        error
                    )

                except httpx.HTTPError as error:
                    st.error(
                        "Knowledge search failed."
                    )

                    st.caption(
                        str(error)
                    )

    st.divider()

    # ---------------------------------------------
    # Document library
    # ---------------------------------------------

    st.markdown(
        "### 📚 Indexed Documents"
    )

    if not knowledge_documents:
        st.info(
            "No uploaded documents are currently "
            "indexed."
        )

    else:
        for document in knowledge_documents:
            document_id = document[
                "id"
            ]

            title = document[
                "title"
            ]

            chunk_count = document[
                "chunk_count"
            ]

            with st.expander(
                
                    f"{title} — "
                    f"{chunk_count} chunk(s)"
                
            ):
                document_col1, document_col2 = (
                    st.columns(2)
                )

                with document_col1:
                    st.write(
                        "**Category:** "
                        f"{document['category']}"
                    )

                    st.write(
                        "**Status:** "
                        f"{document['status'].title()}"
                    )

                with document_col2:
                    st.write(
                        "**File:** "
                        f"{document['source_filename']}"
                    )

                    st.write(
                        "**Media type:** "
                        f"{document['media_type']}"
                    )

                st.write(
                    "**Document key:** "
                    f"`{document['document_key']}`"
                )

                st.caption(
                    "Created: "
                    f"{document['created_at']}"
                )

                st.divider()

                if is_admin:
                    st.warning(
                        "Deleting this document also "
                        "removes all of its vector chunks."
                    )

                    if st.button(
                        "🗑 Delete Document",
                        key=(
                            f"delete_document_"
                            f"{document_id}"
                        ),
                    ):
                        try:
                            delete_knowledge_document(
                                access_token=access_token,
                                document_id=document_id,
                            )

                            st.cache_data.clear()

                            st.success(
                                f"Deleted '{title}'."
                            )

                            st.rerun()

                        except (
                            httpx.HTTPStatusError
                        ) as error:
                            show_http_error(
                                error
                            )

                        except httpx.HTTPError as error:
                            st.error(
                                "Could not delete "
                                "the document."
                            )

                            st.caption(
                                str(error)
                            )

                else:
                    st.caption(
                        "Document deletion is restricted "
                        "to administrators."
                    )


# =================================================
# User Management tab
# =================================================


if is_admin and tab_users is not None:
    with tab_users:
        st.subheader(
            "User Management"
        )

        st.write(
            "Create ChargeOps accounts, assign roles, "
            "and activate or deactivate access."
        )

        st.caption(
            "User administration is protected by the "
            "backend AdminUser authorization dependency."
        )

        try:
            users = get_users(
                access_token
            )

        except (
            httpx.HTTPStatusError
        ) as error:
            show_http_error(
                error
            )
            users = []

        except httpx.HTTPError as error:
            st.error(
                "Could not load ChargeOps users."
            )

            st.caption(
                str(error)
            )
            users = []

        total_users = len(
            users
        )

        active_users = sum(
            bool(
                user.get(
                    "is_active"
                )
            )
            for user in users
        )

        admin_users = sum(
            user.get(
                "role"
            )
            == "admin"
            for user in users
        )

        user_metric1, user_metric2, user_metric3 = (
            st.columns(3)
        )

        with user_metric1:
            st.metric(
                "Total Users",
                total_users,
            )

        with user_metric2:
            st.metric(
                "Active Users",
                active_users,
            )

        with user_metric3:
            st.metric(
                "Administrators",
                admin_users,
            )

        st.divider()

        # -----------------------------------------
        # Create user
        # -----------------------------------------

        st.markdown(
            "### ➕ Create User"
        )

        with st.form(
            "create_user_form",
            clear_on_submit=True,
        ):
            new_user_email = (
                st.text_input(
                    "Email",
                    placeholder=(
                        "operator@chargeops.local"
                    ),
                )
            )

            new_user_password = (
                st.text_input(
                    "Temporary password",
                    type="password",
                    help=(
                        "Minimum 15 characters. Long passphrases are encouraged."
                    ),
                )
            )

            new_user_role = (
                st.selectbox(
                    "Role",
                    options=[
                        "viewer",
                        "operator",
                        "admin",
                    ],
                    format_func=lambda value: (
                        value.title()
                    ),
                    key="new_user_role",
                )
            )

            create_user_submitted = (
                st.form_submit_button(
                    "Create User",
                    use_container_width=True,
                )
            )

        if create_user_submitted:
            email_value = (
                new_user_email
                .strip()
                .lower()
            )

            if not email_value:
                st.warning(
                    "Enter an email address."
                )

            elif len(
                new_user_password
            ) < 15:
                st.warning(
                    "Password must contain at "
                    "least 15 characters."
                )

            else:
                try:
                    created_user = (
                        create_chargeops_user(
                            access_token=(
                                access_token
                            ),
                            email=email_value,
                            password=(
                                new_user_password
                            ),
                            role=new_user_role,
                        )
                    )

                    st.cache_data.clear()

                    st.success(
                        "Created "
                        f"{created_user['email']} "
                        f"as "
                        f"{created_user['role'].title()}."
                    )

                    st.rerun()

                except (
                    httpx.HTTPStatusError
                ) as error:
                    if (
                        error.response.status_code
                        == 409
                    ):
                        st.warning(
                            "A user with this email "
                            "already exists."
                        )

                    else:
                        show_http_error(
                            error
                        )

                except httpx.HTTPError as error:
                    st.error(
                        "Could not create user."
                    )

                    st.caption(
                        str(error)
                    )

        st.divider()

        # -----------------------------------------
        # User directory
        # -----------------------------------------

        st.markdown(
            "### 👥 User Directory"
        )

        if not users:
            st.info(
                "No users are available."
            )

        else:
            table_rows = [
                {
                    "Email": user[
                        "email"
                    ],
                    "Role": (
                        user["role"]
                        .title()
                    ),
                    "Status": (
                        "Active"
                        if user[
                            "is_active"
                        ]
                        else "Inactive"
                    ),
                    "Created": user[
                        "created_at"
                    ],
                }
                for user in users
            ]

            st.dataframe(
                table_rows,
                use_container_width=True,
                hide_index=True,
            )

            st.divider()

            # -------------------------------------
            # Manage selected user
            # -------------------------------------

            st.markdown(
                "### 🛠 Manage Account"
            )

            user_options = {
                (
                    f"{user['email']} — "
                    f"{user['role'].title()} — "
                    f"{'Active' if user['is_active'] else 'Inactive'}"
                ): user
                for user in users
            }

            selected_user_label = (
                st.selectbox(
                    "Select user",
                    options=list(
                        user_options.keys()
                    ),
                    key=(
                        "manage_user_select"
                    ),
                )
            )

            selected_user = (
                user_options[
                    selected_user_label
                ]
            )

            selected_user_id = str(
                selected_user[
                    "id"
                ]
            )

            current_user_id = str(
                current_user.get(
                    "id",
                    "",
                )
            )

            managing_self = (
                selected_user_id
                == current_user_id
            )

            detail_col1, detail_col2 = (
                st.columns(2)
            )

            with detail_col1:
                st.write(
                    "**Email:** "
                    f"{selected_user['email']}"
                )

                st.write(
                    "**Current role:** "
                    f"{selected_user['role'].title()}"
                )

            with detail_col2:
                st.write(
                    "**Status:** "
                    + (
                        "Active"
                        if selected_user[
                            "is_active"
                        ]
                        else "Inactive"
                    )
                )

                st.write(
                    "**Created:** "
                    f"{selected_user['created_at']}"
                )

            if managing_self:
                st.info(
                    "This is your current admin account. "
                    "ChargeOps prevents you from removing "
                    "your own admin role or deactivating "
                    "your own account."
                )

            st.markdown(
                "#### Change Role"
            )

            roles = [
                "viewer",
                "operator",
                "admin",
            ]

            role_index = roles.index(
                selected_user[
                    "role"
                ]
            )

            requested_role = (
                st.selectbox(
                    "New role",
                    options=roles,
                    index=role_index,
                    format_func=lambda value: (
                        value.title()
                    ),
                    key=(
                        "selected_user_role"
                    ),
                )
            )

            role_change_blocked = (
                managing_self
                and requested_role
                != "admin"
            )

            if st.button(
                "Update Role",
                use_container_width=True,
                disabled=(
                    requested_role
                    == selected_user[
                        "role"
                    ]
                    or role_change_blocked
                ),
                key="update_user_role",
            ):
                try:
                    updated_user = (
                        change_user_role(
                            access_token=(
                                access_token
                            ),
                            user_id=(
                                selected_user_id
                            ),
                            role=requested_role,
                        )
                    )

                    st.cache_data.clear()

                    st.success(
                        f"{updated_user['email']} "
                        f"is now "
                        f"{updated_user['role'].title()}."
                    )

                    st.rerun()

                except (
                    httpx.HTTPStatusError
                ) as error:
                    show_http_error(
                        error
                    )

                except httpx.HTTPError as error:
                    st.error(
                        "Could not update user role."
                    )

                    st.caption(
                        str(error)
                    )

            st.markdown(
                "#### Account Access"
            )

            if managing_self:
                st.caption(
                    "Your own account cannot be "
                    "deactivated from this interface."
                )

            elif selected_user[
                "is_active"
            ]:
                if st.button(
                    "Deactivate User",
                    type="secondary",
                    use_container_width=True,
                    key=(
                        "deactivate_user"
                    ),
                ):
                    try:
                        updated_user = (
                            change_user_status(
                                access_token=(
                                    access_token
                                ),
                                user_id=(
                                    selected_user_id
                                ),
                                is_active=False,
                            )
                        )

                        st.cache_data.clear()

                        st.success(
                            f"{updated_user['email']} "
                            "has been deactivated."
                        )

                        st.rerun()

                    except (
                        httpx.HTTPStatusError
                    ) as error:
                        show_http_error(
                            error
                        )

                    except httpx.HTTPError as error:
                        st.error(
                            "Could not deactivate user."
                        )

                        st.caption(
                            str(error)
                        )

            else:
                if st.button(
                    "Activate User",
                    type="primary",
                    use_container_width=True,
                    key=(
                        "activate_user"
                    ),
                ):
                    try:
                        updated_user = (
                            change_user_status(
                                access_token=(
                                    access_token
                                ),
                                user_id=(
                                    selected_user_id
                                ),
                                is_active=True,
                            )
                        )

                        st.cache_data.clear()

                        st.success(
                            f"{updated_user['email']} "
                            "has been activated."
                        )

                        st.rerun()

                    except (
                        httpx.HTTPStatusError
                    ) as error:
                        show_http_error(
                            error
                        )

                    except httpx.HTTPError as error:
                        st.error(
                            "Could not activate user."
                        )

                        st.caption(
                            str(error)
                        )


# =================================================
# Observability tab
# =================================================

with tab_observability:
    if not is_operator:
        st.info(
            "🔒 Observability is available to "
            "operators and administrators."
        )

    else:
        st.subheader(
            "Agent Observability"
        )

        st.caption(
            "Persistent execution telemetry "
            "for ChargeOps AI."
        )

        try:
            runs = get_agent_runs(
                access_token=access_token,
                station_id=station_id,
                limit=100,
            )

            if not runs:
                st.info(
                    "No agent runs recorded "
                    "for this station yet."
                )

            else:
                total_runs = len(
                    runs
                )

                completed_runs = sum(
                    1
                    for run in runs
                    if run["status"]
                    == "completed"
                )

                approval_runs = sum(
                    1
                    for run in runs
                    if run[
                        "approval_required"
                    ]
                )

                latencies = [
                    run["latency_ms"]
                    for run in runs
                ]

                average_latency = (
                    sum(latencies)
                    / len(latencies)
                )

                total_tool_calls = sum(
                    len(
                        run[
                            "used_tools"
                        ]
                    )
                    for run in runs
                )

                (
                    metric1,
                    metric2,
                    metric3,
                    metric4,
                ) = st.columns(4)

                metric1.metric(
                    "Runs",
                    total_runs,
                )

                metric2.metric(
                    "Completed",
                    completed_runs,
                )

                metric3.metric(
                    "Avg Latency",
                    (
                        f"{average_latency:,.0f} ms"
                    ),
                )

                metric4.metric(
                    "Tool Calls",
                    total_tool_calls,
                )

                st.markdown(
                    "### Human Approval"
                )

                st.metric(
                    "Protected Runs",
                    approval_runs,
                )

                st.markdown(
                    "### Recent Agent Runs"
                )

                table_rows = []

                for run in runs:
                    approval = "—"

                    if (
                        run[
                            "approval_decision"
                        ]
                        is True
                    ):
                        approval = (
                            "Approved"
                        )

                    elif (
                        run[
                            "approval_decision"
                        ]
                        is False
                    ):
                        approval = (
                            "Rejected"
                        )

                    elif run[
                        "approval_required"
                    ]:
                        approval = (
                            "Pending"
                        )

                    table_rows.append(
                        {
                            "Run ID": str(
                                run["id"]
                            )[:8],
                            "Status": (
                                run[
                                    "status"
                                ]
                            ),
                            "Latency": (
                                f"{run['latency_ms']} ms"
                            ),
                            "Tools": ", ".join(
                                run[
                                    "used_tools"
                                ]
                            )
                            or "None",
                            "Approval": (
                                approval
                            ),
                            "Started": (
                                run[
                                    "started_at"
                                ]
                            ),
                        }
                    )

                st.dataframe(
                    table_rows,
                    use_container_width=True,
                    hide_index=True,
                )

                st.markdown(
                    "### Run Inspector"
                )

                run_options = {
                    (
                        f"{str(run['id'])[:8]}"
                        " — "
                        f"{run['status']}"
                        " — "
                        f"{run['latency_ms']} ms"
                    ): run
                    for run in runs
                }

                selected_label = (
                    st.selectbox(
                        "Select execution",
                        options=list(
                            run_options.keys()
                        ),
                    )
                )

                selected_run = (
                    run_options[
                        selected_label
                    ]
                )

                st.write(
                    "**Run ID:**",
                    selected_run["id"],
                )

                st.write(
                    "**Thread ID:**",
                    selected_run[
                        "thread_id"
                    ],
                )

                st.write(
                    "**Model:**",
                    selected_run[
                        "model"
                    ],
                )

                st.write(
                    "**User request:**"
                )

                st.code(
                    selected_run[
                        "user_message"
                    ]
                )

                st.write(
                    "**Used tools:**",
                    selected_run[
                        "used_tools"
                    ],
                )

                st.write(
                    "**Agent answer:**"
                )

                st.write(
                    selected_run[
                        "answer"
                    ]
                    or "Workflow has not "
                    "completed yet."
                )

                with st.expander(
                    "Execution trace"
                ):
                    st.json(
                        selected_run[
                            "trace"
                        ]
                    )

        except httpx.HTTPError as error:
            st.error(
                "Could not load "
                "observability data."
            )

            st.caption(
                str(error)
            )

with tab_system:
    st.subheader(
        "ChargeOps Architecture"
    )

    st.code(
        """
User
  ↓
Streamlit Operations Dashboard
  │
  ├── Station Inventory
  │       ↓
  │    PostgreSQL
  │
  ├── Incident Management
  │       ↓
  │    PostgreSQL
  │
  ├── Knowledge Management
  │       │
  │       ├── PDF / TXT / MD
  │       ├── Text Extraction
  │       ├── Chunking
  │       ├── OpenAI Embeddings
  │       └── pgvector
  │
  └── ChargeOps Agent — LangGraph
          │
          ├── PostgreSQL Checkpointer
          │       ↓
          │    thread_id
          │       ↓
          │    Conversation State
          │
          ↓
      call_model
          │
      tool call?
       /      \
     yes       no
      ↓         ↓
execute_tools   END
      │
      └────────→ call_model
        """
    )

    st.subheader(
        "Station Inventory"
    )

    st.dataframe(
        stations,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.subheader(
        "Current Technology Stack"
    )

    stack1, stack2, stack3, stack4 = (
        st.columns(4)
    )

    with stack1:
        st.markdown(
            """
### AI

- OpenAI Responses API
- Structured Outputs
- Function Calling
- Multi-tool Agent
- LangGraph StateGraph
- Conditional Routing
- Runtime Context
- RAG
- Embeddings
- PostgreSQL Checkpointing
- Thread-scoped Memory
- Persistent Conversation State
            """
        )

    with stack2:
        st.markdown(
            """
### Backend

- Python
- FastAPI
- Pydantic
- SQLAlchemy Async
- Alembic
            """
        )

    with stack3:
        st.markdown(
            """
### Data

- PostgreSQL
- pgvector
- HNSW
- Semantic Search
- Incident Memory
            """
        )

    with stack4:
        st.markdown(
            """
### Platform

- Streamlit
- Docker
- Pytest
- Ruff
- Git / GitHub
            """
        )

    st.divider()

    st.subheader(
        "Agent Tools"
    )

    st.markdown(
        """
**1. `get_station_details`**  
Retrieves trusted station metadata from PostgreSQL.

**2. `get_recent_incidents`**  
Retrieves historical operational incidents.

**3. `get_station_weather`**  
Retrieves live external weather conditions.

**4. `search_knowledge_base`**  
Performs semantic retrieval across EV charging manuals and technical knowledge using embeddings and pgvector.

**5. `diagnose_charging_issue`**  
Performs structured, knowledge-grounded fault analysis and records the resulting incident.
        """
    )
