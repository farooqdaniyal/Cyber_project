"""
Login / Signup for SOC Control Room.

  - Accounts ek hi jagah save hote hain:  rag/users.db  (SQLite)
  - Password kabhi plain text mein save nahi hota: salted PBKDF2-SHA256 hash
  - 5 galat koshishon ke baad account 5 minute ke liye lock
  - streamlit_app.py ke shuru mein:  auth.require_login()
"""
import hashlib
import hmac
import html
import os
import re
import secrets
import sqlite3
import time
from contextlib import contextmanager
from datetime import datetime, timedelta

import streamlit as st

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.db")
ITERATIONS = 240_000
MAX_FAILS = 5
LOCK_MINUTES = 5
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
_DUMMY_HASH = None


# =====================================================================
#  Database
# =====================================================================
@contextmanager
def _db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with _db() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name       TEXT    NOT NULL,
                email           TEXT    NOT NULL UNIQUE,
                password_hash   TEXT    NOT NULL,
                role            TEXT    NOT NULL DEFAULT 'SOC Analyst',
                created_at      TEXT    NOT NULL,
                last_login      TEXT,
                failed_attempts INTEGER NOT NULL DEFAULT 0,
                locked_until    TEXT
            )
        """)


def count_users() -> int:
    with _db() as c:
        return c.execute("SELECT COUNT(*) FROM users").fetchone()[0]


def _get_user(email: str):
    with _db() as c:
        return c.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()


# =====================================================================
#  Passwords
# =====================================================================
def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iters, salt_hex, hash_hex = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iters))
        return hmac.compare_digest(dk.hex(), hash_hex)
    except Exception:
        return False


def password_problems(pw: str) -> list:
    problems = []
    if len(pw) < 8:
        problems.append("at least 8 characters")
    if not re.search(r"[a-z]", pw):
        problems.append("a lowercase letter")
    if not re.search(r"[A-Z]", pw):
        problems.append("an uppercase letter")
    if not re.search(r"\d", pw):
        problems.append("a number")
    return problems


# =====================================================================
#  Create account / authenticate
# =====================================================================
def create_user(full_name: str, email: str, password: str, confirm: str):
    """Returns (ok, message)."""
    full_name, email = full_name.strip(), email.strip().lower()
    if len(full_name) < 2:
        return False, "Please enter your full name."
    if not EMAIL_RE.match(email):
        return False, "Please enter a valid email address."
    problems = password_problems(password)
    if problems:
        return False, "Password needs " + ", ".join(problems) + "."
    if password != confirm:
        return False, "Passwords do not match."
    try:
        with _db() as c:
            c.execute(
                "INSERT INTO users (full_name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
                (full_name, email, hash_password(password), datetime.now().isoformat(timespec="seconds")),
            )
    except sqlite3.IntegrityError:
        return False, "An account with this email already exists. Please sign in."
    return True, "Account created successfully. Please sign in."


def authenticate(email: str, password: str):
    """Returns (user_dict | None, error_message | None)."""
    global _DUMMY_HASH
    email = email.strip().lower()
    generic = "Invalid email or password."
    row = _get_user(email) if EMAIL_RE.match(email) else None

    if row is None:
        # waqt barabar rakho taake pata na chale ke email maujood hai ya nahi
        if _DUMMY_HASH is None:
            _DUMMY_HASH = hash_password("dummy-password-for-timing")
        verify_password(password, _DUMMY_HASH)
        return None, generic

    now = datetime.now()
    if row["locked_until"]:
        until = datetime.fromisoformat(row["locked_until"])
        if until > now:
            mins = int((until - now).total_seconds() // 60) + 1
            return None, f"Too many failed attempts. Account locked for about {mins} more minute(s)."

    if verify_password(password, row["password_hash"]):
        with _db() as c:
            c.execute("UPDATE users SET failed_attempts = 0, locked_until = NULL, last_login = ? WHERE id = ?",
                      (now.isoformat(timespec="seconds"), row["id"]))
        return {"id": row["id"], "full_name": row["full_name"], "email": row["email"], "role": row["role"]}, None

    fails = row["failed_attempts"] + 1
    locked = None
    if fails >= MAX_FAILS:
        locked = (now + timedelta(minutes=LOCK_MINUTES)).isoformat(timespec="seconds")
        fails = 0
    with _db() as c:
        c.execute("UPDATE users SET failed_attempts = ?, locked_until = ? WHERE id = ?", (fails, locked, row["id"]))
    time.sleep(0.6)   # brute-force ko dheema karo
    if locked:
        return None, f"Too many failed attempts. Account locked for {LOCK_MINUTES} minutes."
    return None, generic


# =====================================================================
#  UI
# =====================================================================
LOGO = (
    '<svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="#7ea6ff" stroke-width="1.7" '
    'stroke-linecap="round" stroke-linejoin="round"><path d="M12 2 20 5v6c0 5-3.4 8.7-8 11-4.6-2.3-8-6-8-11V5l8-3Z"/>'
    '<path d="m8.5 12 2.2 2.2 4.8-5"/></svg>'
)


def _ico(path, color="#22d3ee"):
    return (f'<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.8" '
            f'stroke-linecap="round" stroke-linejoin="round">{path}</svg>')


ICON_AI = '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M5 19l2-2M17 7l2-2"/>'
ICON_GRAPH = '<circle cx="6" cy="6" r="2.5"/><circle cx="18" cy="6" r="2.5"/><circle cx="12" cy="18" r="2.5"/><path d="M8 7l3 9M16 7l-3 9M8.5 6h7"/>'
ICON_USER = '<circle cx="12" cy="8" r="4"/><path d="M4 21v-2a8 8 0 0 1 16 0v2"/><path d="m16 11 2 2 3-3" />'

CSS = """
<style>
/* ---------- sirf login page: sidebar/header chhupao ---------- */
section[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="stExpandSidebarButton"],
header[data-testid="stHeader"] { display:none !important; }
.block-container { max-width:1240px !important; padding-top:2.2rem !important; position:relative; z-index:2; }
[data-testid="InputInstructions"] { display:none !important; }

/* ---------- animated cyber background ---------- */
.stApp { background:radial-gradient(1100px 600px at 12% -5%, #10206b 0%, #070d28 45%, #03060f 100%) !important; }
.stApp::before { content:""; position:fixed; inset:0; z-index:0; pointer-events:none;
  background-image:linear-gradient(rgba(79,109,245,.08) 1px,transparent 1px),linear-gradient(90deg,rgba(79,109,245,.08) 1px,transparent 1px);
  background-size:52px 52px; animation:gridmove 22s linear infinite;
  -webkit-mask-image:radial-gradient(ellipse at 40% 40%,#000 25%,transparent 78%); mask-image:radial-gradient(ellipse at 40% 40%,#000 25%,transparent 78%); }
.stApp::after { content:""; position:fixed; inset:0; z-index:1; pointer-events:none;
  background:radial-gradient(500px 340px at 85% 90%,rgba(34,211,238,.10),transparent 70%),radial-gradient(420px 300px at 8% 70%,rgba(79,109,245,.14),transparent 70%); }
@keyframes gridmove { from { background-position:0 0,0 0; } to { background-position:52px 52px,52px 52px; } }

/* ---------- hero (left) ---------- */
.au-brand { display:flex; align-items:center; gap:.8rem; margin-bottom:2.2rem; }
.au-logo { width:48px; height:48px; border-radius:13px; display:grid; place-items:center; background:rgba(79,109,245,.16);
  border:1px solid rgba(126,166,255,.55); box-shadow:0 0 22px rgba(79,109,245,.4); }
.au-name { font-weight:800; font-size:1.15rem; color:#fff; letter-spacing:.03em; } .au-name b { color:#22d3ee; }
.au-sub { font-size:.72rem; color:#9fb0dc; letter-spacing:.04em; }
.au-h1 { font-size:3.1rem; line-height:1.08; font-weight:800; color:#fff; letter-spacing:-.02em; margin:0 0 1rem; }
.au-h1 span { background:linear-gradient(90deg,#4f6df5,#22d3ee); -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent; }
.au-p { color:#b4c0e6; font-size:.98rem; line-height:1.65; max-width:520px; margin-bottom:1.6rem; }
.au-feat { display:flex; gap:.85rem; align-items:flex-start; margin-bottom:1rem; }
.au-fi { width:40px; height:40px; border-radius:11px; display:grid; place-items:center; flex:none;
  background:rgba(34,211,238,.08); border:1px solid rgba(34,211,238,.3); }
.au-ft { font-weight:700; color:#e8edff; font-size:.92rem; } .au-fs { color:#8c9ac4; font-size:.8rem; }
.au-chips { display:flex; flex-wrap:wrap; gap:.5rem; margin-top:1.4rem; }
.au-chip { font-size:.7rem; color:#9fc4ff; border:1px solid rgba(79,109,245,.4); background:rgba(79,109,245,.1);
  border-radius:999px; padding:.28rem .75rem; letter-spacing:.04em; }
.radar { position:absolute; right:2%; top:4%; width:190px; height:190px; border-radius:50%; opacity:.9;
  border:1px solid rgba(34,211,238,.35); background:radial-gradient(circle,rgba(34,211,238,.10),transparent 70%); }
.radar::before, .radar::after { content:""; position:absolute; border-radius:50%; border:1px solid rgba(34,211,238,.22); }
.radar::before { inset:18%; } .radar::after { inset:38%; }
.sweep { position:absolute; inset:0; border-radius:50%; background:conic-gradient(from 0deg,rgba(34,211,238,.45),transparent 70deg);
  animation:spin 4.5s linear infinite; }
.blip { position:absolute; width:7px; height:7px; border-radius:50%; background:#f43f5e; box-shadow:0 0 10px #f43f5e; animation:pulse 2.2s ease-in-out infinite; }
@keyframes spin { to { transform:rotate(360deg); } }
@keyframes pulse { 0%,100% { opacity:.25; transform:scale(.7); } 50% { opacity:1; transform:scale(1.2); } }
@media (max-width:900px) { .radar { display:none; } .au-h1 { font-size:2.2rem; } }

/* ---------- form card (right) ---------- */
.st-key-auth_card { background:linear-gradient(180deg,rgba(14,24,64,.82),rgba(8,14,40,.86)); backdrop-filter:blur(16px);
  border:1px solid rgba(79,109,245,.38); border-radius:20px; padding:1.9rem 2rem 1.5rem;
  box-shadow:0 26px 70px rgba(0,0,0,.55),0 0 40px rgba(79,109,245,.12); position:relative; overflow:hidden; }
.st-key-auth_card::before { content:""; position:absolute; left:0; right:0; top:0; height:2px;
  background:linear-gradient(90deg,transparent,#4f6df5,#22d3ee,transparent); }
.au-eyebrow { display:flex; align-items:center; gap:.5rem; color:#22d3ee; font-size:.68rem; font-weight:700; letter-spacing:.2em; }
.au-dot { width:7px; height:7px; border-radius:50%; background:#22c55e; box-shadow:0 0 10px #22c55e; animation:pulse 2s infinite; }
.au-title { font-size:1.9rem; font-weight:800; color:#fff; margin:.7rem 0 .25rem; letter-spacing:-.02em; }
.au-lead { color:#9fb0dc; font-size:.86rem; margin-bottom:1.1rem; }
.au-hint { color:#7f8fbd; font-size:.74rem; margin:-.2rem 0 .8rem; }
.au-msg { border-radius:10px; padding:.65rem .9rem; font-size:.82rem; margin:.2rem 0 .9rem; border:1px solid; }
.au-msg.err { background:rgba(244,63,94,.10); border-color:rgba(244,63,94,.5); color:#fecdd3; }
.au-msg.ok { background:rgba(34,197,94,.10); border-color:rgba(34,197,94,.45); color:#bbf7d0; }
.au-msg.info { background:rgba(79,109,245,.12); border-color:rgba(79,109,245,.5); color:#dbe5ff; }
.au-foot { display:flex; gap:.55rem; align-items:flex-start; color:#7f8fbd; font-size:.7rem; line-height:1.5; margin-top:1rem;
  padding-top:.9rem; border-top:1px solid rgba(79,109,245,.18); }
.st-key-auth_card [data-testid="stForm"] { border:none !important; padding:0 !important; background:transparent !important; }
.st-key-auth_card div[data-testid="stTextInput"] input { height:2.9rem; font-size:.9rem; border-radius:11px !important;
  background:rgba(5,10,31,.75) !important; border:1px solid rgba(79,109,245,.35) !important; padding-left:.9rem !important; }
.st-key-auth_card div[data-testid="stTextInput"] input:focus { border-color:#22d3ee !important; box-shadow:0 0 0 3px rgba(34,211,238,.16) !important; }
.st-key-auth_card [data-testid="stWidgetLabel"] p { font-size:.74rem !important; letter-spacing:.06em; color:#b4c0e6 !important; font-weight:600; }
.st-key-auth_card [data-testid="stFormSubmitButton"] button { height:2.9rem; font-size:.92rem; letter-spacing:.04em;
  background:linear-gradient(90deg,#3b3fc9,#4f6df5 55%,#22b8f0) !important; border:none !important; color:#fff !important;
  box-shadow:0 8px 26px rgba(79,109,245,.4) !important; margin-top:.4rem; }
.st-key-auth_card [data-testid="stFormSubmitButton"] button:hover { filter:brightness(1.12); transform:translateY(-1px); }
.st-key-auth_switch button { background:transparent !important; border:none !important; box-shadow:none !important;
  color:#7ea6ff !important; font-weight:500 !important; text-decoration:underline; padding:0 !important; justify-content:center !important; }
.st-key-auth_switch button:hover { color:#22d3ee !important; background:transparent !important; }
</style>
"""


def _one_line(s: str) -> str:
    """Markdown HTML ko code-block banne se bachao: saari lines ek mein jod do."""
    return "".join(line.strip() for line in s.splitlines())


def _hero_html() -> str:
    def feat(icon, title, sub):
        return (f'<div class="au-feat"><div class="au-fi">{_ico(icon)}</div>'
                f'<div><div class="au-ft">{title}</div><div class="au-fs">{sub}</div></div></div>')
    return _one_line(f"""
    <div style="position:relative;padding-top:.4rem">
      <div class="radar"><div class="sweep"></div>
        <span class="blip" style="top:28%;left:62%"></span><span class="blip" style="top:64%;left:30%;animation-delay:.9s"></span>
        <span class="blip" style="top:50%;left:74%;animation-delay:1.5s"></span></div>
      <div class="au-brand"><div class="au-logo">{LOGO}</div>
        <div><div class="au-name">SOC <b>CONTROL ROOM</b></div><div class="au-sub">Autonomous Cyber Intelligence &amp; Response</div></div></div>
      <div class="au-h1">Detect. Correlate.<br/><span>Respond.</span></div>
      <div class="au-p">An AI-powered Security Operations Center that classifies network attacks with machine learning,
        scores their risk, groups alerts into incidents and keeps a human analyst in control of every critical decision.</div>
      {feat(ICON_AI, "Machine-learning threat detection", "Random Forest classifier trained on CICIDS-style network traffic")}
      {feat(ICON_GRAPH, "Agentic investigation", "LangGraph supervisor with RAG playbooks and LLM-written reports")}
      {feat(ICON_USER, "Human-in-the-loop response", "Critical attacks always wait for an analyst's approval")}
      <div class="au-chips"><span class="au-chip">ML</span><span class="au-chip">RAG</span><span class="au-chip">LangGraph</span>
        <span class="au-chip">Incident correlation</span><span class="au-chip">Audit trail</span><span class="au-chip">n8n automation</span></div>
    </div>""")


def _msg(kind: str, text: str):
    st.markdown(f'<div class="au-msg {kind}">{html.escape(text)}</div>', unsafe_allow_html=True)


def _card_header(eyebrow, title, lead):
    st.markdown(_one_line(f"""
        <div class="au-eyebrow"><span class="au-dot"></span>{eyebrow}</div>
        <div class="au-title">{title}</div><div class="au-lead">{lead}</div>"""), unsafe_allow_html=True)


def _login_view():
    _card_header("SECURE ACCESS PORTAL", "Welcome back", "Sign in to access your security operations dashboard.")
    flash = st.session_state.pop("auth_flash", None)
    if flash:
        _msg("ok", flash)
    if "auth_prefill" in st.session_state:
        st.session_state["login_email"] = st.session_state.pop("auth_prefill")

    error = None
    with st.form("login_form", clear_on_submit=False):
        email = st.text_input("WORK EMAIL", key="login_email", placeholder="you@company.com")
        pw = st.text_input("PASSWORD", type="password", key="login_pw", placeholder="Enter your password")
        go = st.form_submit_button("SIGN IN  →", type="primary", use_container_width=True)
    if go:
        if not email.strip() or not pw:
            error = "Please enter your email and password."
        else:
            user, error = authenticate(email, pw)
            if user:
                st.session_state["user"] = user
                st.rerun()
    if error:
        _msg("err", error)

    if st.button("New analyst? Create an account", key="auth_switch", use_container_width=True):
        st.session_state["auth_view"] = "signup"
        st.rerun()


def _signup_view(first_run: bool):
    _card_header("CREATE ACCOUNT", "Join the control room",
                 "Register as an analyst to access the SOC Control Room.")
    if first_run:
        _msg("info", "First-time setup: create the first analyst account to get started.")
    error = None
    with st.form("signup_form", clear_on_submit=False):
        name = st.text_input("FULL NAME", key="su_name", placeholder="Your full name")
        email = st.text_input("WORK EMAIL", key="su_email", placeholder="you@company.com")
        pw = st.text_input("PASSWORD", type="password", key="su_pw", placeholder="Create a strong password")
        st.markdown('<div class="au-hint">Use 8+ characters with upper & lower case letters and a number.</div>',
                    unsafe_allow_html=True)
        pw2 = st.text_input("CONFIRM PASSWORD", type="password", key="su_pw2", placeholder="Re-enter your password")
        go = st.form_submit_button("CREATE ACCOUNT  →", type="primary", use_container_width=True)
    if go:
        ok, message = create_user(name, email, pw, pw2)
        if ok:
            st.session_state["auth_view"] = "login"
            st.session_state["auth_flash"] = message
            st.session_state["auth_prefill"] = email.strip().lower()
            st.rerun()
        error = message
    if error:
        _msg("err", error)

    if not first_run and st.button("Already have an account? Sign in", key="auth_switch", use_container_width=True):
        st.session_state["auth_view"] = "login"
        st.rerun()


def _render_page():
    st.markdown(CSS, unsafe_allow_html=True)
    first_run = count_users() == 0
    if "auth_view" not in st.session_state:
        st.session_state["auth_view"] = "signup" if first_run else "login"
    view = "signup" if first_run else st.session_state["auth_view"]

    left, right = st.columns([1.2, 1], gap="large")
    with left:
        st.markdown(_hero_html(), unsafe_allow_html=True)
    with right:
        st.markdown('<div style="height:5vh"></div>', unsafe_allow_html=True)
        try:
            card = st.container(key="auth_card")
        except TypeError:
            card = st.container(border=True)
        with card:
            if view == "signup":
                _signup_view(first_run)
            else:
                _login_view()
            st.markdown(_one_line("""
                <div class="au-foot"><span>🔒</span><span>Passwords are salted and hashed (PBKDF2-SHA256) and never stored in plain text.
                After 5 failed attempts an account is locked for 5 minutes.</span></div>"""), unsafe_allow_html=True)


def require_login():
    """App ke shuru mein chalayein. Login nahi hua to login/signup page dikhata hai aur script rok deta hai."""
    if os.getenv("AUTH_ENABLED", "true").strip().lower() != "true":
        st.session_state.setdefault("user", {"id": 0, "full_name": "Demo Analyst", "email": "demo@local", "role": "SOC Analyst"})
        return st.session_state["user"]
    init_db()
    if st.session_state.get("user"):
        return st.session_state["user"]
    _render_page()
    st.stop()


def logout():
    for k in ("user", "auth_view", "auth_flash", "auth_prefill", "lm_result", "copilot_chat"):
        st.session_state.pop(k, None)
    st.rerun()