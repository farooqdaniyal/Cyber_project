"""Theme + reusable UI helpers. Colours badalne ke liye sirf neeche wali :root lines badlein."""
import pandas as pd
import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

:root {
  --bg: #000000;
  --card: #0a1230;
  --card2: #0d1738;
  --border: rgba(79,109,245,.22);
  --accent: #7ea6ff;
  --accent-soft: rgba(79,109,245,.12);
  --text: #e8edff;
  --muted: #8c9ac4;
  --red: #ff4d4d;
  --amber: #fbbf24;
  --blue: #38bdf8;
}

html, body, [class*="css"] { font-family: 'Inter', system-ui, sans-serif; }
.stApp { background: var(--bg); color: var(--text); }
#MainMenu, footer, [data-testid="stDecoration"], [data-testid="stAppDeployButton"] { display: none !important; }
[data-testid="stExpandSidebarButton"], [data-testid="stSidebarCollapsedControl"],
[data-testid="stSidebarCollapseButton"] { visibility: visible !important; opacity: 1 !important; }
[data-testid="stExpandSidebarButton"] svg, [data-testid="stSidebarCollapsedControl"] svg,
[data-testid="stSidebarCollapseButton"] svg { color: #7ea6ff !important; fill: #7ea6ff !important; }
header[data-testid="stHeader"] { background: transparent !important; }
.block-container { padding-top: 2rem; max-width: 1400px; }

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] {
  background: #060b22 !important;
  border-right: 1px solid var(--border);
}
section[data-testid="stSidebar"] .block-container { padding-top: 1.2rem; }
.brand { display:flex; align-items:center; gap:.7rem; margin-bottom:1.4rem; }
.brand-logo {
  width:38px; height:38px; border-radius:10px; display:grid; place-items:center;
  background: var(--accent-soft); border:1px solid var(--accent); font-size:1.1rem;
}
.brand-name { font-weight:700; font-size:1.05rem; color: var(--accent); letter-spacing:-.01em; }
.side-label {
  font-size:.68rem; letter-spacing:.18em; color:var(--muted); font-weight:600;
  margin: .3rem 0 .6rem .3rem;
}
/* nav buttons */
section[data-testid="stSidebar"] div.stButton > button {
  justify-content:flex-start; text-align:left; width:100%;
  background:transparent; border:1px solid transparent; box-shadow:none;
  padding:.6rem .85rem; border-radius:10px; color:#b4c0e6; font-weight:500;
}
section[data-testid="stSidebar"] div.stButton > button p { color:inherit; font-size:.92rem; }
section[data-testid="stSidebar"] div.stButton > button:hover {
  background:rgba(79,109,245,.08); border-color:transparent; color:#fff;
}
section[data-testid="stSidebar"] div.stButton > button[kind="primary"] {
  background:var(--accent-soft) !important; border:1px solid var(--accent) !important;
  color:#fff !important; box-shadow:none !important; font-weight:600;
}
.api-box {
  background: var(--card); border:1px solid var(--border); border-radius:12px;
  padding:.8rem .95rem; margin-top:1rem; font-size:.78rem; color:var(--muted);
}
.api-box b { color: var(--text); font-size:.85rem; }
.user-box { font-size:.82rem; color:#b4c0e6; margin:.8rem 0 .4rem .2rem; }

/* widget labels / radio text readable */
[data-testid="stWidgetLabel"] p, label p { color:#b4c0e6 !important; }
div[role="radiogroup"] label p { color:#e8edff !important; }

/* ---------- Header ---------- */
.crumb { font-size:.72rem; letter-spacing:.2em; color:var(--muted); font-weight:600; }
.crumb b { color: var(--accent); }
.page-title { font-size:2rem; font-weight:700; letter-spacing:-.02em; margin:.3rem 0 .2rem; }
.page-sub { color:var(--muted); font-size:.9rem; margin-bottom:1rem; }
.pill-ok {
  display:inline-flex; align-items:center; gap:.45rem; padding:.45rem .9rem; border-radius:10px;
  background: var(--accent-soft); border:1px solid var(--border); color: var(--accent);
  font-size:.82rem; font-weight:500;
}
.pill-ok:before { content:''; width:8px; height:8px; border-radius:50%; background:var(--accent); box-shadow:0 0 8px var(--accent); }
.hr { border:0; border-top:1px solid var(--border); margin:1rem 0 1.4rem; }
.section-title { font-size:1.1rem; font-weight:700; margin:1.6rem 0 .2rem; }
.section-sub { color:var(--muted); font-size:.85rem; margin-bottom:.9rem; }

/* ---------- KPI cards ---------- */
.kpi-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:1rem; }
@media (max-width:1100px){ .kpi-grid { grid-template-columns:repeat(2,1fr); } }
.kpi {
  background: linear-gradient(180deg, var(--card2), var(--card));
  border:1px solid var(--border); border-radius:16px; padding:1.2rem 1.3rem;
}
.kpi-top { display:flex; justify-content:space-between; align-items:center; }
.kpi-label { font-size:.85rem; color:#b4c0e6; }
.kpi-icon {
  width:38px; height:38px; border-radius:10px; display:grid; place-items:center; font-size:1rem;
  background: var(--accent-soft); color: var(--accent);
}
.kpi-icon.red { background: rgba(251,113,133,.14); color: var(--red); }
.kpi-icon.amber { background: rgba(251,191,36,.14); color: var(--amber); }
.kpi-value { font-size:2.2rem; font-weight:700; margin:.9rem 0 .2rem; }
.kpi-sub { font-size:.78rem; color: var(--muted); }

/* ---------- Bordered containers (chart cards) ---------- */
div[data-testid="stVerticalBlockBorderWrapper"] {
  background: linear-gradient(180deg, var(--card2), var(--card));
  border:1px solid var(--border) !important; border-radius:16px;
}

/* ---------- Metric / status / panels (Live monitor) ---------- */
.metric-grid { display:grid; grid-template-columns:repeat(5,1fr); gap:.85rem; margin:1rem 0 1.4rem; }
@media (max-width:1200px){ .metric-grid { grid-template-columns:repeat(2,1fr); } }
.metric-card {
  background: linear-gradient(180deg, var(--card2), var(--card));
  border:1px solid var(--border); border-radius:14px; padding:1.05rem 1.15rem;
}
.metric-label { font-size:.68rem; text-transform:uppercase; letter-spacing:.08em; color:var(--muted); font-weight:600; margin-bottom:.4rem; }
.metric-value { font-family:'JetBrains Mono',monospace; font-size:1.2rem; font-weight:600; word-break:break-word; }
.metric-sub { font-size:.72rem; color:var(--muted); margin-top:.35rem; }

.status-banner { border-radius:12px; padding:1rem 1.25rem; margin:1rem 0; border-left:4px solid; font-size:.95rem; }
.status-ok { background:rgba(6,78,59,.35); border-color:#7ea6ff; color:#a7f3d0; }
.status-warn { background:rgba(120,53,15,.35); border-color:#fbbf24; color:#fde68a; }
.status-info { background:rgba(30,58,138,.30); border-color:#60a5fa; color:#bfdbfe; }
.status-danger { background:rgba(127,29,29,.4); border-color:#f87171; color:#fecaca; }

.timeline { display:flex; gap:.5rem; flex-wrap:wrap; margin:1.2rem 0; }
.tl-step { flex:1; min-width:120px; background:var(--card); border:1px solid var(--border); border-radius:10px; padding:.75rem 1rem; }
.tl-step.done { border-color: var(--accent); }
.tl-num { font-family:'JetBrains Mono',monospace; font-size:.65rem; color:var(--accent); font-weight:600; }
.tl-title { font-weight:600; font-size:.85rem; margin-top:.2rem; }
.tl-desc { font-size:.72rem; color:var(--muted); margin-top:.15rem; }

.panel { background:var(--card); border:1px solid var(--border); border-radius:14px; padding:1.2rem 1.4rem; margin-bottom:1rem; }
.panel h3 { margin:0 0 .75rem; font-size:1rem; font-weight:600; }
.panel-body { color:#c7d2f2; font-size:.9rem; line-height:1.55; }
.mono { font-family:'JetBrains Mono',monospace; font-size:.8rem; }

.scan-bar {
  height:3px; border-radius:2px; margin:.5rem 0 1rem;
  background:linear-gradient(90deg,#7ea6ff,#22d3ee,#60a5fa,#7ea6ff); background-size:200% 100%;
  animation:scan 2s linear infinite;
}
@keyframes scan { 0%{background-position:100% 0} 100%{background-position:-100% 0} }

div.stButton > button[kind="primary"] {
  background: linear-gradient(90deg,#3b3fc9,#4f6df5) !important; border:none !important;
  border-radius:10px !important; font-weight:600 !important; color:#ffffff !important;
}
.coming {
  text-align:center; padding:4rem 1rem; border:1px dashed var(--border); border-radius:16px; color:var(--muted);
}

/* ======== TERMINAL / HACKER GREEN OVERRIDES ======== */
.stApp { background: radial-gradient(ellipse at 15% 0%, #0f1a45 0%, #040816 45%, #000 100%); }
section[data-testid="stSidebar"] { background:#060b22 !important; border-right:1px solid rgba(79,109,245,.28); }
.brand-logo { border-radius:10px; border:1px solid #7ea6ff; background:rgba(79,109,245,.08); box-shadow:0 0 14px rgba(79,109,245,.35); }
.brand-name { font-family:'JetBrains Mono',monospace; color:#e8edff; letter-spacing:.04em; font-size:.92rem; }
.brand-sub { font-size:.58rem; color:#8fa3e0; margin-top:2px; line-height:1.2; }
section[data-testid="stSidebar"] div.stButton > button { font-family:'JetBrains Mono',monospace; }
section[data-testid="stSidebar"] div.stButton > button[kind="primary"] {
  background:linear-gradient(90deg,#3b3fc9,#2f2a95) !important; border:1px solid #7ea6ff !important;
  box-shadow:0 0 14px rgba(79,109,245,.25) !important; color:#fff !important;
}
.sys-box { display:flex; gap:.7rem; align-items:center; background:#0a1230; border:1px solid var(--border);
  border-radius:12px; padding:.75rem .9rem; margin-top:1.2rem; }
.sys-dot { width:12px; height:12px; border-radius:50%; background:#7ea6ff; box-shadow:0 0 12px #7ea6ff; flex:none; }
.sys-t { color:#7ea6ff; font-weight:600; font-size:.8rem; }
.sys-s { color:var(--muted); font-size:.68rem; }
.user-chip { display:flex; align-items:center; justify-content:flex-end; gap:.6rem; }
.avatar { width:38px; height:38px; border-radius:50%; background:#2f2a95; border:1px solid #7ea6ff;
  display:grid; place-items:center; font-weight:700; color:#eef2ff; }
.uc-name { font-size:.85rem; font-weight:600; } .uc-role { font-size:.68rem; color:var(--muted); }
div[data-testid="stTextInput"] input { background:#0a1230 !important; border:1px solid rgba(79,109,245,.3) !important;
  color:#e8edff !important; border-radius:10px; font-size:.85rem; }
div[data-testid="stVerticalBlockBorderWrapper"] { background:#0a1230 !important; border:1px solid rgba(79,109,245,.25) !important; border-radius:12px; }
.greet-title { font-family:'JetBrains Mono',monospace; font-size:1.55rem; font-weight:700; color:#eef2ff; }
.greet-title b { color:#7ea6ff; }
.greet-sub { font-size:.8rem; color:var(--muted); margin-top:.3rem; }
.datebox { text-align:right; font-family:'JetBrains Mono',monospace; font-size:.8rem; color:#c7d2f2; }
.datebox b { display:block; font-size:1.1rem; color:#eef2ff; }
.card-title { font-family:'JetBrains Mono',monospace; font-weight:600; font-size:.88rem; color:#eef2ff; margin-bottom:.4rem; letter-spacing:.03em; }
.t-kpi-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:1rem; margin:1rem 0 1.2rem; }
@media (max-width:1100px){ .t-kpi-grid { grid-template-columns:repeat(2,1fr); } }
.t-kpi { display:flex; gap:.9rem; align-items:center; background:#0a1230; border:1px solid rgba(79,109,245,.28);
  border-radius:12px; padding:1rem 1.1rem; box-shadow:0 0 18px rgba(79,109,245,.05) inset; }
.t-ico { width:46px; height:46px; border-radius:50%; display:grid; place-items:center; font-size:1.2rem; flex:none; border:2px solid; }
.t-ico.red { color:#ff4d4d; border-color:#ff4d4d; background:rgba(255,77,77,.12); }
.t-ico.amber { color:#fbbf24; border-color:#fbbf24; background:rgba(251,191,36,.12); }
.t-ico.blue { color:#38bdf8; border-color:#38bdf8; background:rgba(56,189,248,.12); }
.t-ico.green { color:#7ea6ff; border-color:#7ea6ff; background:rgba(79,109,245,.12); }
.t-label { font-size:.75rem; color:#c7d2f2; }
.t-value { font-family:'JetBrains Mono',monospace; font-size:1.7rem; font-weight:700; color:#eef2ff; line-height:1.2; }
.t-delta { font-size:.7rem; color:var(--muted); } .t-delta b.red{color:#ff6b6b} .t-delta b.amber{color:#fbbf24}
.t-delta b.blue{color:#38bdf8} .t-delta b.green{color:#7ea6ff}
.alert-row { display:flex; align-items:center; gap:.7rem; padding:.55rem .2rem; border-bottom:1px solid rgba(79,109,245,.1);
  font-size:.8rem; }
.alert-row:last-child { border-bottom:0; }
.a-time { font-family:'JetBrains Mono',monospace; color:#8c9ac4; width:48px; flex:none; }
.a-text { flex:1; color:#d3dcf7; }
.chip { font-size:.65rem; padding:.15rem .55rem; border-radius:6px; font-weight:600; border:1px solid; }
.chip.crit { color:#ff6b6b; border-color:#ff6b6b; background:rgba(255,77,77,.12); }
.chip.high { color:#fb923c; border-color:#fb923c; background:rgba(251,146,60,.12); }
.chip.med { color:#fbbf24; border-color:#fbbf24; background:rgba(251,191,36,.12); }
.chip.low { color:#38bdf8; border-color:#38bdf8; background:rgba(56,189,248,.12); }
.a-status { color:var(--muted); width:92px; text-align:right; font-size:.72rem; }
.mitre { display:grid; grid-template-columns:repeat(6,1fr); gap:5px; }
.m-head { font-size:.58rem; color:#8fa3e0; text-align:center; min-height:2.2em; line-height:1.15; }
.m-cell { height:24px; border-radius:3px; background:#0c1634; border:1px solid rgba(79,109,245,.12); }
.m-cell.l1 { background:#1c2a66; } .m-cell.l2 { background:#3b50d8; }
.m-cell.l3 { background:#4f6df5; } .m-cell.l4 { background:#7ea6ff; box-shadow:0 0 8px rgba(79,109,245,.6); }

/* ======== ULTRAVIOLET touches ======== */
.sys-dot { background:#22d3ee !important; box-shadow:0 0 12px #22d3ee !important; }
.sys-t { color:#22d3ee !important; }
.pill-ok { color:#22d3ee !important; background:rgba(34,211,238,.10) !important; border-color:rgba(34,211,238,.35) !important; }
.pill-ok:before { background:#22d3ee !important; box-shadow:0 0 8px #22d3ee !important; }
.greet-title b, .brand-name {
  background:linear-gradient(90deg,#7ea6ff,#22d3ee); -webkit-background-clip:text; background-clip:text;
  -webkit-text-fill-color:transparent; color:transparent;
}
.t-ico.green { color:#f472b6 !important; border-color:#f472b6 !important; background:rgba(244,114,182,.12) !important; }
.t-delta b.green { color:#f472b6 !important; }
.scan-bar { background:linear-gradient(90deg,#4f6df5,#22d3ee,#f472b6,#4f6df5) !important; background-size:200% 100% !important; }
.stApp { background: radial-gradient(ellipse at 15% 0%, #0f1a45 0%, #050a1f 45%, #000 100%) !important; }

/* ======== PRO TABLE ======== */
.tbl-wrap { border:1px solid rgba(79,109,245,.28); border-radius:14px; overflow-x:auto;
  background:linear-gradient(180deg,#0c1634,#0a1230); box-shadow:0 0 24px rgba(79,109,245,.06) inset; }
table.tbl { width:100%; border-collapse:collapse; font-size:.82rem; }
.tbl th { text-align:left; padding:.85rem 1rem; font-size:.64rem; letter-spacing:.14em; text-transform:uppercase;
  color:#8c9ac4; background:rgba(79,109,245,.09); border-bottom:1px solid rgba(79,109,245,.28); font-weight:600; white-space:nowrap; }
.tbl td { padding:.78rem 1rem; border-bottom:1px solid rgba(79,109,245,.10); color:#d3dcf7; white-space:nowrap; }
.tbl tbody tr:hover td { background:rgba(79,109,245,.08); }
.tbl tbody tr:last-child td { border-bottom:0; }
.tbl .num { text-align:right; }
.idc { font-family:'JetBrains Mono',monospace; color:#9db4ff; font-size:.78rem; }
.ftag { background:rgba(79,109,245,.14); border:1px solid rgba(79,109,245,.35); color:#bcd0ff;
  border-radius:6px; padding:.14rem .55rem; font-size:.72rem; font-weight:500; }
.abadge { display:inline-grid; place-items:center; min-width:28px; height:22px; padding:0 .4rem; border-radius:11px;
  background:rgba(34,211,238,.12); color:#22d3ee; font-weight:700; font-size:.74rem; border:1px solid rgba(34,211,238,.3); }
.rbar { display:inline-block; width:74px; height:6px; border-radius:3px; background:rgba(255,255,255,.09);
  vertical-align:middle; margin-right:.55rem; overflow:hidden; }
.rfill { display:block; height:100%; border-radius:3px; }
.mono-b { font-family:'JetBrains Mono',monospace; font-size:.78rem; }
.st-chip { display:inline-flex; align-items:center; gap:.4rem; font-size:.74rem; font-weight:600; }
.st-dot { width:7px; height:7px; border-radius:50%; display:inline-block; box-shadow:0 0 8px currentColor; }
.dim { color:#8c9ac4; font-size:.74rem; }
.chip.none { color:#94a3b8; border-color:#64748b; background:rgba(100,116,139,.14); }
.tbl-foot { color:#8c9ac4; font-size:.76rem; margin:.5rem .2rem 0; }
.det-head { display:flex; align-items:center; gap:.7rem; flex-wrap:wrap; }
.det-id { font-family:'JetBrains Mono',monospace; font-size:1.05rem; color:#dbe5ff; font-weight:600; }

/* ======== Streamlit widgets: dark + violet (config.toml ke baghair bhi) ======== */
span[data-baseweb="tag"] { background:#2f2a95 !important; border-radius:6px !important; }
span[data-baseweb="tag"] span, span[data-baseweb="tag"] svg { color:#e8edff !important; fill:#e8edff !important; }
div[data-baseweb="select"] > div, div[data-baseweb="input"] > div, div[data-baseweb="base-input"] {
  background:#0a1230 !important; border-color:rgba(79,109,245,.32) !important; color:#e8edff !important; }
div[data-baseweb="select"] input, div[data-baseweb="select"] div { color:#e8edff; }
div[data-baseweb="popover"] > div, div[data-baseweb="popover"] ul { background:#0a1230 !important; border:1px solid rgba(79,109,245,.3); }
div[data-baseweb="popover"] li { background:#0a1230 !important; color:#e8edff !important; }
div[data-baseweb="popover"] li:hover { background:rgba(79,109,245,.22) !important; }
div[data-testid="stNumberInput"] input { color:#e8edff !important; }

/* ======== Sidebar nav: text left side par ======== */
section[data-testid="stSidebar"] div.stButton > button {
  justify-content:flex-start !important; text-align:left !important; padding-left:1.1rem !important;
}
section[data-testid="stSidebar"] div.stButton > button > div {
  width:100%; display:flex; justify-content:flex-start !important;
}
section[data-testid="stSidebar"] div.stButton > button [data-testid="stMarkdownContainer"] {
  width:100%; text-align:left !important;
}
section[data-testid="stSidebar"] div.stButton > button p {
  text-align:left !important; width:100%; margin:0;
}

/* ======== Main area buttons (Quick actions etc.) ======== */
div.stButton > button[kind="secondary"] {
  background:#0a1230; border:1px solid rgba(79,109,245,.35); color:#e8edff; border-radius:10px; font-weight:600;
}
div.stButton > button[kind="secondary"]:hover { border-color:#7ea6ff; background:rgba(79,109,245,.16); color:#fff; }

/* ======== LIVE MONITOR / WIDGET FIXES ======== */
.tl-step.wait { border-color:#fbbf24; } .tl-step.wait .tl-num { color:#fbbf24; }
.tl-step.fail { border-color:#fb7185; } .tl-step.fail .tl-num { color:#fb7185; }
.tl-step .tl-desc { white-space:normal; }
/* banners: green -> cyan, blue -> violet (poori theme se mel) */
.status-ok { background:rgba(34,211,238,.10); border-color:#22d3ee; color:#a5f3fc; }
.status-info { background:rgba(79,109,245,.12); border-color:#4f6df5; color:#dbe5ff; }
.status-warn { background:rgba(251,191,36,.10); border-color:#fbbf24; color:#fde68a; }
.status-danger { background:rgba(251,113,133,.12); border-color:#fb7185; color:#fecdd3; }
div[data-testid="stAlert"] { background:rgba(79,109,245,.10) !important; border:1px solid rgba(79,109,245,.35) !important;
  border-radius:10px; color:#e8edff !important; }
/* tabs */
button[data-baseweb="tab"] { color:#8c9ac4 !important; }
button[data-baseweb="tab"][aria-selected="true"] { color:#e8edff !important; }
div[data-baseweb="tab-highlight"] { background-color:#4f6df5 !important; }
/* select / multiselect (dark) */
div[data-baseweb="select"] > div { background-color:#0a1230 !important; border:1px solid rgba(79,109,245,.35) !important; }
div[data-baseweb="select"] div, div[data-baseweb="select"] span, div[data-baseweb="select"] input { color:#e8edff !important; }
div[data-baseweb="select"] svg { fill:#7ea6ff !important; }
/* checkbox / radio: red -> violet (best-effort; asli fix .streamlit/config.toml) */
label[data-baseweb="checkbox"] > span:first-child { border-color:rgba(79,109,245,.6) !important; }
label[data-baseweb="checkbox"]:has(input:checked) > span:first-child { background-color:#4f6df5 !important; border-color:#4f6df5 !important; }
label[data-baseweb="radio"] > div:first-child { background-color:#0a1230 !important; border-color:rgba(79,109,245,.6) !important; }
label[data-baseweb="radio"]:has(input:checked) > div:first-child { background-color:#4f6df5 !important; border-color:#4f6df5 !important; }


/* ======== SAB KUCH DARK: buttons, uploader, number box, expander, chat, json ======== */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button,
[data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-secondaryFormSubmit"],
[data-testid="stFileUploader"] button {
  background:#0a1230 !important; color:#e8edff !important; border:1px solid rgba(79,109,245,.4) !important;
  border-radius:10px !important; font-weight:600 !important; box-shadow:none !important; }
.stButton > button:hover, .stDownloadButton > button:hover, .stFormSubmitButton > button:hover,
[data-testid="stBaseButton-secondary"]:hover, [data-testid="stFileUploader"] button:hover {
  background:rgba(79,109,245,.22) !important; border-color:#7ea6ff !important; color:#fff !important; }
.stButton > button:disabled, .stDownloadButton > button:disabled { opacity:.4 !important; }
.stButton > button p, .stDownloadButton > button p, .stFormSubmitButton > button p,
[data-testid="stFileUploader"] button p, [data-testid="stFileUploader"] button span { color:inherit !important; }
.stButton > button[kind="primary"], [data-testid="stBaseButton-primary"] {
  background:linear-gradient(90deg,#3b3fc9,#4f6df5) !important; color:#fff !important;
  border:1px solid rgba(126,166,255,.5) !important; }
/* sidebar nav buttons apne alag (transparent) rahen */
section[data-testid="stSidebar"] div.stButton > button { background:transparent !important; border:1px solid transparent !important;
  color:#b4c0e6 !important; box-shadow:none !important; font-weight:500 !important; }
section[data-testid="stSidebar"] div.stButton > button:hover { background:rgba(79,109,245,.12) !important;
  border-color:transparent !important; color:#fff !important; }
section[data-testid="stSidebar"] div.stButton > button[kind="primary"] {
  background:linear-gradient(90deg,#2f2a95,#3b3fc9) !important; border:1px solid rgba(126,166,255,.35) !important;
  color:#fff !important; font-weight:600 !important; }
/* file uploader */
[data-testid="stFileUploader"] section, [data-testid="stFileUploaderDropzone"] {
  background:#0a1230 !important; border:1px dashed rgba(79,109,245,.45) !important; border-radius:12px !important; }
[data-testid="stFileUploaderDropzone"] * { color:#b4c0e6; }
/* number input */
div[data-testid="stNumberInput"] > div, div[data-testid="stNumberInput"] [data-baseweb="input"] {
  background:#0a1230 !important; border-color:rgba(79,109,245,.35) !important; }
button[data-testid="stNumberInputStepUp"], button[data-testid="stNumberInputStepDown"] {
  background:#0d1738 !important; color:#b4c0e6 !important; border:none !important; }
/* expander */
[data-testid="stExpander"] { background:#0a1230 !important; border:1px solid rgba(79,109,245,.25) !important; border-radius:10px !important; }
[data-testid="stExpander"] details, [data-testid="stExpander"] summary { background:transparent !important; color:#e8edff !important; }
[data-testid="stExpander"] summary:hover { background:rgba(79,109,245,.10) !important; }
/* json / code / textarea */
[data-testid="stJson"], .react-json-view { background:#0a1230 !important; border-radius:8px; padding:.5rem; }
code, pre { background:#0d1738 !important; color:#cfe0ff !important; }
textarea { background:#0a1230 !important; color:#e8edff !important; border:1px solid rgba(79,109,245,.3) !important; }
/* chat (AI Assistant) */
[data-testid="stChatInput"], [data-testid="stChatInput"] > div { background:#0a1230 !important;
  border:1px solid rgba(79,109,245,.35) !important; border-radius:12px !important; }
[data-testid="stChatInput"] textarea { background:transparent !important; border:none !important; }
[data-testid="stBottom"] > div, [data-testid="stBottomBlockContainer"] { background:transparent !important; }
[data-testid="stChatMessage"] { background:rgba(79,109,245,.07) !important; border-radius:12px; }

/* ======== NAVY DASHBOARD THEME (reference design) ======== */
:root { --nv-line: rgba(79,109,245,.22); }
.stApp { background: radial-gradient(1200px 600px at 20% -10%, #0e1a4a 0%, #070d28 45%, #050a1f 100%) !important; }
.block-container { padding-top: 1rem !important; padding-bottom: .6rem !important; max-width: 100% !important;
  padding-left: 1.6rem !important; padding-right: 1.6rem !important; }
[data-testid="stVerticalBlock"] { gap: .6rem !important; }
header[data-testid="stHeader"] { background: transparent !important; }
section[data-testid="stSidebar"] { background:#070c22 !important; border-right:1px solid rgba(79,109,245,.18) !important; }
section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap:.3rem !important; }
div[data-testid="stVerticalBlockBorderWrapper"] { background:linear-gradient(180deg,#0c1638,#0a1230) !important;
  border:1px solid var(--nv-line) !important; border-radius:12px !important; }

/* sidebar */
.brand2 { display:flex; align-items:center; gap:.7rem; margin:.2rem 0 .9rem; }
.logo2 { width:42px; height:42px; border-radius:11px; display:grid; place-items:center; flex:none;
  background:rgba(79,109,245,.16); border:1px solid rgba(126,166,255,.5); box-shadow:0 0 16px rgba(79,109,245,.35); }
.brand2 .t1 { font-weight:800; font-size:1rem; color:#fff; letter-spacing:.01em; }
.brand2 .t1 b { color:#22d3ee; }
.brand2 .t2 { font-size:.66rem; color:#b4c0e6; line-height:1.25; margin-top:.15rem; }
.sysbox { border:1px solid rgba(79,109,245,.35); background:rgba(14,30,80,.35); border-radius:10px;
  padding:.55rem .8rem; margin-bottom:.9rem; }
.sysbox .a { color:#22e5a0; font-weight:600; font-size:.82rem; display:flex; align-items:center; gap:.45rem; }
.sysbox .dot { width:9px; height:9px; border-radius:50%; background:#22c55e; box-shadow:0 0 8px #22c55e; display:inline-block; }
.sysbox .b { font-size:.68rem; color:#8c9ac4; margin-left:1.05rem; }
section[data-testid="stSidebar"] div.stButton > button {
  justify-content:flex-start !important; text-align:left !important; gap:.7rem; background:transparent; border:1px solid transparent;
  box-shadow:none; padding:.55rem .85rem !important; border-radius:10px; color:#b4c0e6; font-weight:500; font-family:inherit !important; }
section[data-testid="stSidebar"] div.stButton > button > div { width:100%; display:flex; justify-content:flex-start !important; gap:.7rem; }
section[data-testid="stSidebar"] div.stButton > button p { text-align:left !important; margin:0; font-size:.9rem; color:inherit; }
section[data-testid="stSidebar"] div.stButton > button:hover { background:rgba(79,109,245,.12); color:#fff; border-color:transparent; }
section[data-testid="stSidebar"] div.stButton > button[kind="primary"] {
  background:linear-gradient(90deg,#2f2a95,#3b3fc9) !important; border:1px solid rgba(126,166,255,.35) !important;
  color:#fff !important; box-shadow:0 0 14px rgba(59,63,201,.35) !important; font-weight:600; }
.side-card { margin-top:1.2rem; border:1px solid rgba(79,109,245,.2); border-radius:12px; padding:1rem; color:#c8d4ff;
  font-style:italic; line-height:1.6; font-size:.86rem; background:linear-gradient(180deg,rgba(20,40,110,.25),rgba(8,14,40,.4)); }
.side-card .sc-f { margin-top:1.1rem; font-style:normal; font-size:.66rem; color:#6f7fb0; }

/* top bar */
div[data-testid="stTextInput"] input { background:#0a1230 !important; border:1px solid rgba(79,109,245,.3) !important; color:#e8edff !important;
  border-radius:10px !important; font-size:.82rem; height:2.6rem; padding-left:2.4rem !important;
  background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%238c9ac4' stroke-width='2' stroke-linecap='round'><circle cx='11' cy='11' r='7'/><path d='m20 20-3.5-3.5'/></svg>") !important;
  background-repeat:no-repeat !important; background-position:.8rem center !important; }
.bell { position:relative; width:40px; height:40px; display:grid; place-items:center; margin:0 auto; }
.bell-b { position:absolute; top:2px; right:0; min-width:17px; height:17px; border-radius:9px; background:#f43f5e; color:#fff;
  font-size:.62rem; font-weight:700; display:grid; place-items:center; padding:0 4px; }
.uchip { display:flex; align-items:center; gap:.7rem; justify-content:flex-end; border-left:1px solid rgba(79,109,245,.2); padding-left:1rem; }
.uav { width:38px; height:38px; border-radius:50%; display:grid; place-items:center; font-weight:700; color:#e8edff;
  background:linear-gradient(135deg,#3b3fc9,#22d3ee); }
.uname { font-size:.84rem; font-weight:600; color:#e8edff; } .urole { font-size:.68rem; color:#8c9ac4; }

/* greeting */
.hello { font-size:1.75rem; font-weight:800; color:#fff; letter-spacing:-.01em; line-height:1.2; }
.hello .hl { color:#22b8f0; }
.hello-s { font-size:.84rem; color:#b4c0e6; margin-top:.2rem; }
.clock { text-align:right; font-size:.8rem; color:#b4c0e6; line-height:1.3; }
.clock b { display:block; font-size:1.6rem; color:#fff; line-height:1.15; }
.clock span { font-size:.68rem; color:#8c9ac4; }
.sdot { width:8px; height:8px; border-radius:50%; display:inline-block; margin-right:.4rem; }

/* queue banner */
.st-key-queue_box[data-testid="stVerticalBlockBorderWrapper"], .st-key-queue_box [data-testid="stVerticalBlockBorderWrapper"] {
  background:linear-gradient(90deg,rgba(245,158,11,.14),rgba(10,18,48,.7)) !important; border:1px solid rgba(245,158,11,.55) !important; }
.qb { display:flex; align-items:center; gap:.9rem; }
.qb-ico { width:40px; height:40px; border-radius:10px; border:1px solid; display:grid; place-items:center; flex:none; background:rgba(245,158,11,.08); }
.qb-t { font-weight:700; font-size:.95rem; } .qb-s { font-size:.78rem; color:#c7d2f2; }
.st-key-qa_queue button { background:transparent !important; border:1px solid #f59e0b !important; color:#fbbf24 !important; font-weight:600; }
.st-key-qa_queue button:hover { background:rgba(245,158,11,.15) !important; }

/* KPI cards */
.kp-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:.8rem; }
@media (max-width:1100px){ .kp-grid { grid-template-columns:repeat(2,1fr); } }
.kp { display:flex; gap:.9rem; align-items:center; background:linear-gradient(180deg,#0c1638,#0a1230); border:1px solid var(--nv-line);
  border-radius:12px; padding:.8rem 1rem; }
.kp-ico { width:54px; height:54px; border-radius:12px; display:grid; place-items:center; flex:none; }
.kp-t { font-size:.86rem; font-weight:600; color:#e8edff; }
.kp-v { font-size:1.9rem; font-weight:800; line-height:1.1; }
.kp-s { font-size:.74rem; color:#9fb0dc; } .kp-d { font-size:.72rem; margin-top:.15rem; }
.dim { color:#8c9ac4; font-size:.7rem; }

/* card headers + lists */
.ct { display:flex; align-items:center; gap:.65rem; }
.ct-ico { width:30px; height:30px; border-radius:8px; display:grid; place-items:center; background:rgba(79,109,245,.14); flex:none; }
.ct-t { font-size:.95rem; font-weight:700; color:#fff; } .ct-s { font-size:.7rem; color:#8c9ac4; }
.live-b { font-size:.66rem; font-weight:600; color:#22d3ee; border:1px solid rgba(34,211,238,.45); border-radius:6px; padding:.1rem .5rem; background:rgba(34,211,238,.08); }
.lgd { display:flex; gap:1rem; justify-content:center; font-size:.74rem; color:#b4c0e6; }
.lg-r { display:flex; align-items:center; padding:.3rem 0; font-size:.82rem; color:#d3dcf7; }
.lg-n { flex:1; } .lg-v { font-weight:700; color:#fff; }
.rt-h, .rt-r { display:grid; grid-template-columns:22px 52px 1.1fr 1.3fr 78px 1.05fr; gap:.55rem; align-items:center; }
.rt-h { font-size:.58rem; letter-spacing:.12em; color:#6f7fb0; padding:.4rem .2rem; border-bottom:1px solid var(--nv-line); margin-top:.3rem; }
.rt-r { padding:.46rem .2rem; border-bottom:1px solid rgba(79,109,245,.10); font-size:.76rem; color:#dbe5ff; }
.rt-r:last-child { border-bottom:0; }
.sevchip { display:inline-block; font-size:.66rem; font-weight:600; border-radius:6px; padding:.1rem .5rem; border:1px solid; }
.sr { display:grid; grid-template-columns:34px 1fr 86px 44px; gap:.7rem; align-items:center; padding:.4rem 0; border-bottom:1px solid rgba(79,109,245,.08); }
.sr:last-child { border-bottom:0; }
.ci { width:30px; height:30px; border-radius:50%; display:grid; place-items:center; background:rgba(79,109,245,.14); border:1px solid rgba(79,109,245,.3); }
.sr-t { font-size:.8rem; font-weight:600; color:#e8edff; } .sr-s { font-size:.64rem; color:#8c9ac4; }
.bar { height:6px; border-radius:3px; background:rgba(255,255,255,.08); overflow:hidden; }
.bar i { display:block; height:100%; border-radius:3px; }
.sr-v { text-align:right; display:flex; flex-direction:column; line-height:1.15; }
.sr-v b { font-size:.85rem; color:#fff; } .sr-v span { font-size:.62rem; color:#8c9ac4; }

/* ======== WIDGETS (testid-based: Streamlit version se mukt) ======== */
div[data-testid="stTextInput"] input { background-image:none !important; padding-left:.8rem !important; }
.st-key-dash_search div[data-testid="stTextInput"] input {
  padding-left:2.4rem !important; background-repeat:no-repeat !important; background-position:.8rem center !important;
  background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%238c9ac4' stroke-width='2' stroke-linecap='round'><circle cx='11' cy='11' r='7'/><path d='m20 20-3.5-3.5'/></svg>") !important; }
[data-testid="stSelectbox"] div, [data-testid="stMultiSelect"] div, [data-testid="stNumberInput"] div {
  background-color:#0a1230 !important; color:#e8edff !important; }
[data-testid="stSelectbox"] [data-testid="stWidgetLabel"] div, [data-testid="stMultiSelect"] [data-testid="stWidgetLabel"] div,
[data-testid="stNumberInput"] [data-testid="stWidgetLabel"] div { background-color:transparent !important; color:#b4c0e6 !important; }
[data-testid="stSelectbox"] input, [data-testid="stMultiSelect"] input, [data-testid="stNumberInput"] input {
  background-color:transparent !important; color:#e8edff !important; -webkit-text-fill-color:#e8edff !important; }
[data-testid="stSelectbox"] svg, [data-testid="stMultiSelect"] svg { fill:#9fb4ff !important; color:#9fb4ff !important; }
[data-testid="stMultiSelect"] span, [data-testid="stMultiSelect"] [data-baseweb="tag"] {
  background-color:#2f2a95 !important; color:#e8edff !important; }
[data-testid="stMultiSelect"] [data-baseweb="tag"] { border-radius:6px !important; }
[data-testid="stNumberInput"] button { background-color:#0d1738 !important; color:#b4c0e6 !important; border:none !important; }
/* dropdown list (portal mein khulta hai) */
[role="listbox"], [role="listbox"] li, [role="option"], [data-baseweb="popover"] ul, [data-baseweb="menu"] {
  background-color:#0a1230 !important; color:#e8edff !important; }
[role="option"]:hover, li[aria-selected="true"], [data-baseweb="menu"] li:hover { background-color:rgba(79,109,245,.28) !important; }
.tbl-bar { display:flex; align-items:center; }

/* ======== DASHBOARD SPACING (cards ke beech saaf gap) ======== */
.block-container { padding-top: 2rem !important; }
[data-testid="stVerticalBlock"] { gap: .85rem !important; }
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlock"] { gap: .55rem !important; }
[data-testid="stHorizontalBlock"] { gap: 1rem !important; }
.kp-grid { gap: 1rem; }
.kp { padding: .95rem 1.1rem; }
.uchip { padding-left: 1.2rem; min-height: 44px; }
.clock { padding-top: .2rem; }

/* ======== SIDEBAR BOTTOM: side card + user card + Sign out ======== */
.side-card { font-style:normal !important; margin-top:1.1rem !important; padding:.85rem 1rem !important; position:relative;
  border:1px solid rgba(79,109,245,.22) !important; border-radius:12px !important; line-height:1.5 !important; }
.side-card::before { content:""; position:absolute; left:0; top:12%; bottom:12%; width:3px; border-radius:3px;
  background:linear-gradient(180deg,#4f6df5,#22d3ee); }
.side-card .sc-l { font-size:.8rem; font-weight:600; color:#c8d4ff; letter-spacing:.01em; }
.side-card .sc-f { margin-top:.7rem !important; font-size:.62rem !important; color:#6f7fb0 !important; letter-spacing:.04em; }
.ucard { display:flex; align-items:center; gap:.75rem; margin-top:.9rem; padding:.7rem .8rem; border-radius:12px;
  border:1px solid rgba(79,109,245,.30); background:linear-gradient(180deg,rgba(20,40,110,.30),rgba(8,14,40,.55)); }
.uc-av { position:relative; width:38px; height:38px; border-radius:50%; display:grid; place-items:center; flex:none;
  font-weight:700; font-size:.85rem; color:#fff; background:linear-gradient(135deg,#3b3fc9,#22d3ee); }
.uc-av::after { content:""; position:absolute; right:-1px; bottom:-1px; width:10px; height:10px; border-radius:50%;
  background:#22c55e; border:2px solid #0a1230; }
.uc-n { font-weight:700; font-size:.86rem; color:#fff; line-height:1.2; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.uc-r { font-size:.68rem; color:#8c9ac4; }
section[data-testid="stSidebar"] .st-key-logout_btn div.stButton > button,
section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:last-child div.stButton > button {
  background:rgba(244,63,94,.10) !important; border:1px solid rgba(244,63,94,.55) !important; color:#ff8da1 !important;
  justify-content:center !important; font-weight:600 !important; border-radius:10px !important; margin-top:.15rem; }
section[data-testid="stSidebar"] .st-key-logout_btn div.stButton > button > div,
section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:last-child div.stButton > button > div {
  justify-content:center !important; }
section[data-testid="stSidebar"] .st-key-logout_btn div.stButton > button:hover,
section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:last-child div.stButton > button:hover {
  background:rgba(244,63,94,.24) !important; border-color:#f43f5e !important; color:#fff !important; }

/* ======== CHAT AVATARS + CHHOTI SCREEN ======== */
[data-testid="stChatMessageAvatarUser"] { background:linear-gradient(135deg,#3b3fc9,#4f6df5) !important; color:#fff !important; }
[data-testid="stChatMessageAvatarAssistant"] { background:linear-gradient(135deg,#0e7490,#22d3ee) !important; color:#04121f !important; }
[data-testid="stChatMessageAvatarUser"] svg, [data-testid="stChatMessageAvatarAssistant"] svg { color:inherit !important; fill:currentColor !important; }
[data-testid="stChatMessage"] { border:1px solid rgba(79,109,245,.18); }
/* chhoti screen (laptop 768px): sidebar ka sajawati card chhupao taake Sign out nazar aaye */
@media (max-height: 820px) {
  .side-card { display:none !important; }
  section[data-testid="stSidebar"] div.stButton > button { padding-top:.42rem !important; padding-bottom:.42rem !important; }
}
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def page_header(crumb: str, title: str, sub: str = ""):
    html = (
        f'<div class="crumb">SOC CONTROL ROOM / <b>{crumb.upper()}</b></div>'
        f'<div class="page-title">{title}</div>'
    )
    if sub:
        html += f'<div class="page-sub">{sub}</div>'
    st.markdown(html, unsafe_allow_html=True)


def section(title: str, sub: str = ""):
    st.markdown(
        f'<div class="section-title">{title}</div><div class="section-sub">{sub}</div>',
        unsafe_allow_html=True,
    )


def kpi_cards(items):
    """items: list of dicts: label, value, sub, icon, tone ('', 'red', 'amber')"""
    cards = ""
    for it in items:
        cards += (
            f'<div class="kpi"><div class="kpi-top"><span class="kpi-label">{it["label"]}</span>'
            f'<span class="kpi-icon {it.get("tone", "")}">{it["icon"]}</span></div>'
            f'<div class="kpi-value">{it["value"]}</div>'
            f'<div class="kpi-sub">{it["sub"]}</div></div>'
        )
    st.markdown(f'<div class="kpi-grid">{cards}</div>', unsafe_allow_html=True)


def plotly_layout(fig, height=340):
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#b4c0e6", family="Inter"),
        legend=dict(orientation="h", y=1.12, x=0.5, xanchor="center"),
    )
    fig.update_xaxes(gridcolor="rgba(79,109,245,.08)", zeroline=False)
    fig.update_yaxes(gridcolor="rgba(79,109,245,.08)", zeroline=False)
    return fig


# ============================================================
# Data helpers (pehle data_utils.py mein the; ab yahin hain)
# ============================================================
# Agar aap ka audit_log.py local time (datetime.now()) likhta hai to isay False kar dein.
AUDIT_TS_IS_UTC = True
LEVEL_ORDER = {"none": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}


def load_audit() -> pd.DataFrame:
    """Audit log ko saaf dataframe ki shakal mein deta hai (khali ho to empty df)."""
    from audit_log import AUDIT_LOGGER
    df = AUDIT_LOGGER.get_all_as_dataframe()
    if df.empty:
        return df
    d = df.copy()
    if "risk_level" in d.columns:
        d["risk_level"] = d["risk_level"].fillna("None").astype(str)
    if "risk_score" in d.columns:
        d["risk_score"] = pd.to_numeric(d["risk_score"], errors="coerce")
    if "timestamp" in d.columns:
        if AUDIT_TS_IS_UTC:
            # Audit log UTC mein likhta hai: apni local time mein badlo (warna "5h ago" jaisi ghalat cheezein aati hain)
            from datetime import datetime as _dt
            ts = pd.to_datetime(d["timestamp"], errors="coerce", utc=True)
            d["ts"] = ts.dt.tz_convert(_dt.now().astimezone().tzinfo).dt.tz_localize(None)
        else:
            d["ts"] = pd.to_datetime(d["timestamp"], errors="coerce")
    return d


def pick(d: pd.DataFrame, cols):
    return [c for c in cols if c in d.columns]


def last_report() -> str:
    """Live monitor ki sab se recent report (session se)."""
    saved = st.session_state.get("lm_result") or {}
    return (saved.get("result") or {}).get("report", "") or ""


def empty_state(msg="No data yet. Run an analysis in Live Monitor first."):
    st.markdown(f'<div class="coming">{msg}</div>', unsafe_allow_html=True)


def terminal_kpis(items):
    """items: dict(label, value, delta, icon, tone in red/amber/blue/green)"""
    cards = ""
    for it in items:
        tone = it.get("tone", "green")
        cards += (
            f'<div class="t-kpi"><div class="t-ico {tone}">{it["icon"]}</div><div>'
            f'<div class="t-label">{it["label"]}</div><div class="t-value">{it["value"]}</div>'
            f'<div class="t-delta">{it["delta"]}</div></div></div>'
        )
    st.markdown(f'<div class="t-kpi-grid">{cards}</div>', unsafe_allow_html=True)


# ============================================================
# Pro table helpers
# ============================================================
import html as _html

SEV_COLORS = {"critical": "#ff4d4d", "high": "#fb923c", "medium": "#fbbf24", "low": "#22d3ee", "none": "#64748b"}


def ago(ts) -> str:
    try:
        if ts is None or pd.isna(ts):
            return "—"
        s = (pd.Timestamp.now() - pd.Timestamp(ts)).total_seconds()
    except Exception:
        return "—"
    s = max(s, 0)
    if s < 60:
        return "just now"
    if s < 3600:
        return f"{int(s // 60)}m ago"
    if s < 86400:
        return f"{int(s // 3600)}h ago"
    return f"{int(s // 86400)}d ago"


def level_chip(level) -> str:
    cls = {"critical": "crit", "high": "high", "medium": "med", "low": "low"}.get(str(level).lower(), "none")
    return f'<span class="chip {cls}">{_html.escape(str(level))}</span>'


def risk_bar(score, level) -> str:
    try:
        v = max(0.0, min(100.0, float(score)))
    except Exception:
        return '<span class="dim">—</span>'
    c = SEV_COLORS.get(str(level).lower(), "#64748b")
    return (f'<span class="rbar"><span class="rfill" style="width:{v:.0f}%;background:{c}"></span></span>'
            f'<b class="mono-b">{v:.1f}</b>')


def status_chip(status) -> str:
    s = str(status)
    low = s.lower()
    color = "#fbbf24" if low in ("open", "new") else "#22d3ee" if low in ("resolved", "closed") else "#7ea6ff"
    return (f'<span class="st-chip" style="color:{color}"><span class="st-dot" style="background:{color}"></span>'
            f'{_html.escape(s.title())}</span>')


def html_table(headers, rows, row_colors=None, num_cols=()) -> str:
    """rows: list of list of (already escaped / html) strings. Single-line HTML (markdown-safe)."""
    th = "".join(f'<th class="{"num" if i in num_cols else ""}">{h}</th>' for i, h in enumerate(headers))
    body = ""
    for r, row in enumerate(rows):
        color = row_colors[r] if row_colors else "transparent"
        tds = ""
        for i, cell in enumerate(row):
            style = f' style="border-left:3px solid {color}"' if i == 0 else ""
            tds += f'<td class="{"num" if i in num_cols else ""}"{style}>{cell}</td>'
        body += f"<tr>{tds}</tr>"
    return f'<div class="tbl-wrap"><table class="tbl"><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div>'


def pill(text, color) -> str:
    """Chhota rangeen label (chip)."""
    return (f'<span class="sevchip" style="color:{color};border-color:{color};background:{color}22">'
            f'{_html.escape(str(text))}</span>')


def outcome_pill(o) -> str:
    s = str(o).upper()
    c = "#f59e0b" if "ESCALAT" in s else "#22c55e" if ("AUTOMATED" in s or "RECOMMENDED" in s) else "#4f6df5"
    return pill(str(o).replace("_", " ").title(), c)


def verify_pill(v) -> str:
    s = str(v).upper()
    c = "#22c55e" if s == "VERIFIED" else "#f59e0b" if "HUMAN" in s else "#4f6df5"
    return pill(str(v).replace("_", " ").title(), c)


def table_controls(n, per_page, key, csv_bytes=None, csv_name="data.csv", noun="records"):
    """Table ke upar ek line: 'Showing x-y of n' | Page box | CSV button. Returns (page, start, end)."""
    import math
    pages = max(1, math.ceil(n / per_page))
    try:
        c1, c2, c3 = st.columns([4, 1.1, 1.5], vertical_alignment="center")
    except TypeError:
        c1, c2, c3 = st.columns([4, 1.1, 1.5])
    page = 1
    if pages > 1:
        page = int(c2.number_input("Page", 1, pages, 1, key=key, label_visibility="collapsed"))
    start = (page - 1) * per_page
    end = min(start + per_page, n)
    c1.markdown(f'<div class="tbl-foot" style="margin:0">Showing <b>{start + 1}–{end}</b> of <b>{n}</b> {noun}'
                f' · page {page}/{pages}</div>', unsafe_allow_html=True)
    if csv_bytes is not None:
        c3.download_button("Download CSV", csv_bytes, file_name=csv_name, mime="text/csv",
                           use_container_width=True, key=key + "_dl")
    return page, start, end