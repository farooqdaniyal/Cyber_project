# ============================================================
# SOC CONTROL ROOM — main entry (login + sidebar + router)
# Run (project root se):  python -m streamlit run rag/streamlit_app.py
# ============================================================
import os
import sys
import importlib
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# `streamlit run` aur `python -m streamlit run` dono mein imports chalen.
# rag/ SAB SE PEHLE (taake hamari theme.py, auth.py waghera hi uthein) aur project root AAKHIR mein
# (sirf isliye ke `from rag.risk_engine import ...` chal sake).
_RAG_DIR = Path(__file__).resolve().parent
_ROOT_DIR = _RAG_DIR.parent
if str(_RAG_DIR) in sys.path:
    sys.path.remove(str(_RAG_DIR))
sys.path.insert(0, str(_RAG_DIR))
if str(_ROOT_DIR) not in sys.path:
    sys.path.append(str(_ROOT_DIR))

load_dotenv()
load_dotenv(Path(__file__).resolve().parent / ".env")
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Safety net: agar .streamlit/config.toml load na ho rahi ho, to theme yahin se set karo
# (naye browser session / page reload par laagu hota hai).
try:
    for _k, _v in {"base": "dark", "primaryColor": "#4f6df5", "backgroundColor": "#050a1f",
                   "secondaryBackgroundColor": "#0a1230", "textColor": "#e8edff"}.items():
        st._config.set_option(f"theme.{_k}", _v)
except Exception:
    pass

st.set_page_config(
    page_title="SOC Control Room | AI Cyber Intelligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------- Theme ----------------
import theme
if not hasattr(theme, "load_audit"):
    st.error(f"Wrong theme.py loaded: {getattr(theme, '__file__', '?')}. "
             "Delete any old theme.py / data_utils.py copies in the project root and keep only the ones inside rag/.")
    st.stop()
sys.modules.setdefault("data_utils", theme)  # data_utils.py na ho tab bhi pages chalen
theme.inject_css()

# ---------------- LOGIN / SIGNUP (pehle yahan se guzarna parta hai) ----------------
import auth
auth.require_login()          # login nahi to login/signup page dikhata hai aur yahin ruk jata hai
current_user = st.session_state["user"]

N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "").strip()

# key, label, material icon
PAGES = [
    ("overview", "Dashboard", "dashboard"),
    ("live_monitor", "Live Monitor", "sensors"),
    ("incidents", "Incidents", "warning"),
    ("threat_intel", "Threat Intelligence", "public"),
    ("attack_graph", "Network Analysis", "hub"),
    ("copilot", "AI Assistant", "auto_awesome"),
    ("response_center", "Response Center", "shield"),
    ("reports", "Reports", "description"),
    ("audit_trail", "Audit Logs", "fact_check"),
]
LABELS = {k: label for k, label, _ in PAGES}


def open_incident_count() -> int:
    try:
        d = theme.load_audit()
        if d.empty or "incident_id" not in d.columns:
            return 0
        if "incident_status" in d.columns:
            d = d[~d["incident_status"].astype(str).str.lower().isin(["resolved", "closed"])]
        return d["incident_id"].replace("—", None).dropna().nunique()
    except Exception:
        return 0


SHIELD = (
    '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#7ea6ff" stroke-width="1.7" '
    'stroke-linecap="round" stroke-linejoin="round"><path d="M12 2 20 5v6c0 5-3.4 8.7-8 11-4.6-2.3-8-6-8-11V5l8-3Z"/>'
    '<path d="m8.5 12 2.2 2.2 4.8-5"/></svg>'
)

# ---------------- Sidebar ----------------
with st.sidebar:
    st.markdown(
        f'<div class="brand2"><div class="logo2">{SHIELD}</div><div>'
        '<div class="t1">SOC <b>CONTROL ROOM</b></div>'
        '<div class="t2">Autonomous Cyber<br/>Intelligence &amp; Response</div></div></div>',
        unsafe_allow_html=True,
    )
    n8n_txt = "n8n connected" if N8N_WEBHOOK_URL else "n8n not set"
    st.markdown(
        f'<div class="sysbox"><div class="a"><i class="dot"></i>System Online</div>'
        f'<div class="b">{n8n_txt} · pipeline ready</div></div>',
        unsafe_allow_html=True,
    )

    n_open = open_incident_count()
    if n_open:
        st.markdown(
            "<style>.st-key-nav_incidents button::after{content:'" + str(n_open) + "';margin-left:auto;"
            "background:rgba(244,63,94,.18);border:1px solid #f43f5e;color:#ff8da1;border-radius:999px;"
            "padding:.02rem .5rem;font-size:.68rem;font-weight:700}</style>",
            unsafe_allow_html=True,
        )

    st.session_state.setdefault("page", "overview")
    for _key, _label, _icon in PAGES:
        kw = dict(key=f"nav_{_key}", use_container_width=True,
                  type="primary" if st.session_state["page"] == _key else "secondary")
        try:
            clicked = st.button(_label, icon=f":material/{_icon}:", **kw)
        except TypeError:          # purana Streamlit: icon support nahi
            clicked = st.button(_label, **kw)
        if clicked:
            st.session_state["page"] = _key
            st.rerun()
    page = st.session_state["page"]

    st.markdown(
        '<div style="padding-bottom:.9rem"><div class="side-card"><div class="sc-l">Smarter Detection</div>'
        '<div class="sc-l">Faster Response</div><div class="sc-l">Safer Tomorrow</div>'
        '<div class="sc-f">Powered by AI · Built for SOC</div></div></div>',
        unsafe_allow_html=True,
    )
    _name = current_user["full_name"]
    _initials = "".join(w[0] for w in _name.split()[:2]).upper() or "U"
    st.markdown(
        f'<div style="padding-bottom:1rem"><div class="ucard" style="margin-top:0"><div class="uc-av">{_initials}</div>'
        f'<div style="min-width:0"><div class="uc-n">{_name}</div>'
        f'<div class="uc-r">{current_user.get("role", "SOC Analyst")} · Online</div></div></div></div>',
        unsafe_allow_html=True,
    )
    try:
        _out = st.button("Sign out", key="logout_btn", icon=":material/logout:", use_container_width=True)
    except TypeError:
        _out = st.button("Sign out", key="logout_btn", use_container_width=True)
    if _out:
        auth.logout()

# ---------------- Router ----------------
module_name = f"pages_ui.{page}"


def _show_load_error(e):
    """Page load na ho to Streamlit ka 'redacted' error nahi, balkay saaf wajah aur hal dikhao."""
    msg = f"{type(e).__name__}: {e}"
    low = msg.lower()
    hint = ""
    if isinstance(e, ModuleNotFoundError) and getattr(e, "name", None):
        hint = f"The package '{e.name}' is missing. Add it to requirements.txt and redeploy."
    elif "groq" in low or "api_key" in low or "api key" in low:
        hint = ("Set GROQ_API_KEY in your app Secrets (Streamlit Cloud: Manage app > Settings > Secrets), "
                "then reboot the app.")
    theme.page_header(page.replace("_", " "), LABELS.get(page, page))
    st.error("This page could not be loaded.\n\n`" + msg[:400] + "`" + (f"\n\n**Fix:** {hint}" if hint else ""))
    st.stop()


try:
    mod = importlib.import_module(module_name)
except ModuleNotFoundError as e:
    if e.name == module_name:
        theme.page_header(page.replace("_", " "), LABELS.get(page, page))
        st.markdown('<div class="coming">This page is not available yet.</div>', unsafe_allow_html=True)
        st.stop()
    _show_load_error(e)
except Exception as e:
    _show_load_error(e)

mod.render()
