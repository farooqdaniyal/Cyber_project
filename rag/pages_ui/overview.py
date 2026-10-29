import html
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo


import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import theme
import briefing

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DECISIONS_FILE = os.path.join(ROOT, "response_decisions.json")

LEVELS = ["Critical", "High", "Medium", "Low", "Info"]
LV_COLOR = {"Critical": "#f43f5e", "High": "#f59e0b", "Medium": "#0ea5e9", "Low": "#8b5cf6", "Info": "#64748b"}
LV_ORDER = {"Info": 0, "Low": 1, "Medium": 2, "High": 3, "Critical": 4}
RANGES = {"Last 24 hours": pd.Timedelta(days=1), "Last 7 days": pd.Timedelta(days=7),
          "Last 30 days": pd.Timedelta(days=30), "All time": None}
MUTE = "#8c9ac4"
APP_TZ = ZoneInfo("Asia/Karachi")

# ---- simple line icons (inline SVG) ----
ICONS = {
    "shield": '<path d="M12 2 20 5v6c0 5-3.4 8.7-8 11-4.6-2.3-8-6-8-11V5l8-3Z"/><path d="M12 8v4M12 16h.01"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "link": '<path d="M10 14a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1"/><path d="M14 10a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1"/>',
    "check": '<circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/>',
    "bell": '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.7 21a2 2 0 0 1-3.4 0"/>',
    "user": '<circle cx="12" cy="8" r="4"/><path d="M4 21v-2a8 8 0 0 1 16 0v2"/>',
    "key": '<circle cx="8" cy="15" r="4"/><path d="m10.8 12.2 8.2-8.2M16 7l3 3"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "radio": '<circle cx="12" cy="12" r="2"/><path d="M16.2 7.8a6 6 0 0 1 0 8.4M7.8 16.2a6 6 0 0 1 0-8.4"/>',
    "zap": '<path d="M13 2 4 14h7l-1 8 9-12h-7l1-8Z"/>',
    "server": '<rect x="3" y="4" width="18" height="6" rx="1"/><rect x="3" y="14" width="18" height="6" rx="1"/><path d="M7 7h.01M7 17h.01"/>',
    "db": '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/>',
    "monitor": '<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>',
    "alert": '<path d="M12 3 2 20h20L12 3Z"/><path d="M12 10v4M12 17h.01"/>',
    "list": '<path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>',
    "grid": '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
}


def _svg(name, color=MUTE, size=18):
    return (f'<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color}" stroke-width="1.8" '
            f'stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</svg>')


# (tactic, icon, technique id, technique name)
STAGES = [
    ("Initial Access", "user", "T1190", "Exploit Public-Facing Application"),
    ("Credential Access", "key", "T1110", "Brute Force"),
    ("Discovery", "search", "T1046", "Network Service Discovery"),
    ("Lateral Movement", "arrow", "T1021", "Remote Services"),
    ("Command & Control", "radio", "T1071", "Application Layer Protocol"),
    ("Impact", "zap", "T1498", "Network Denial of Service"),
]


def _tactic(attack: str):
    a = str(attack).lower()
    if "dos" in a:
        return "Impact"
    if "scan" in a:
        return "Discovery"
    if "bot" in a:
        return "Command & Control"
    if any(k in a for k in ("heartbleed", "web", "sql", "xss")):
        return "Initial Access"
    if any(k in a for k in ("patator", "brute")):
        return "Credential Access"
    if "infiltr" in a:
        return "Lateral Movement"
    return None


def _asset_meta(name: str):
    n = name.lower()
    if "domain" in n or "dns" in n:
        return "globe", "Critical Asset"
    if "web" in n:
        return "server", "Web Application"
    if "database" in n or "db" in n:
        return "db", "Database"
    if "workstation" in n or "employee" in n:
        return "monitor", "Endpoint"
    return "server", "Asset"


# ---------------- layout helpers (purane Streamlit par bhi chalen) ----------------
def _cols(spec, va="center"):
    try:
        return st.columns(spec, vertical_alignment=va)
    except TypeError:
        return st.columns(spec)


def _box(key):
    try:
        return st.container(border=True, key=key)
    except TypeError:
        return st.container(border=True)


def _gap(px=12):
    st.markdown(f'<div style="height:{px}px"></div>', unsafe_allow_html=True)


def _go(page_key):
    st.session_state["page"] = page_key
    st.rerun()


# ---------------- data ----------------
def _prep(raw):
    d = raw.copy()
    if "ts" not in d.columns:
        d["ts"] = pd.to_datetime(d.get("timestamp"), errors="coerce")
    rl = d.get("risk_level", pd.Series("None", index=d.index)).fillna("None").astype(str).str.capitalize()
    d["lvl"] = rl.where(rl.isin(["Critical", "High", "Medium", "Low"]), "Info")
    if "incident_id" in d.columns:
        d["incident_id"] = d["incident_id"].replace("—", pd.NA)
    d["pred_s"] = d.get("prediction", pd.Series("—", index=d.index)).astype(str)
    d["attack"] = d["pred_s"].str.upper() != "BENIGN"
    out = d.get("outcome", pd.Series("", index=d.index)).astype(str).str.upper()
    ver = d.get("verification_status", pd.Series("", index=d.index)).astype(str).str.upper()
    d["ver"] = ver
    d["review"] = d["attack"] & (out.str.contains("ESCALAT") | ver.str.contains("HUMAN"))
    return d


def _load_decisions():
    if os.path.exists(DECISIONS_FILE):
        try:
            with open(DECISIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _incidents(d):
    if "incident_id" not in d.columns:
        return pd.DataFrame(columns=["incident_id", "alerts", "lvl", "first", "last", "status"])
    x = d[d["incident_id"].notna()]
    if x.empty:
        return pd.DataFrame(columns=["incident_id", "alerts", "lvl", "first", "last", "status"])
    x = x.assign(_o=x["lvl"].map(LV_ORDER))
    g = x.groupby("incident_id")
    status = (g["incident_status"].last().astype(str) if "incident_status" in x.columns
              else pd.Series("OPEN", index=g.size().index))
    inc = pd.DataFrame({"alerts": g.size(), "o": g["_o"].max(), "first": g["ts"].min(),
                        "last": g["ts"].max(), "status": status})
    inv = {v: k for k, v in LV_ORDER.items()}
    inc["lvl"] = inc["o"].map(inv)
    return inc.reset_index()


def _pending(d):
    """Response center jaisi tareef: verified nahi / escalated, aur abhi faisla nahi hua."""
    out = d["outcome"].astype(str).str.upper() if "outcome" in d.columns else pd.Series("", index=d.index)
    esc = d[(d["ver"] != "VERIFIED") | out.str.contains("ESCALAT")]
    keys = (esc["log_id"].astype(str) if "log_id" in esc.columns
            else pd.Series(esc.index.astype(str), index=esc.index))
    decided = set(_load_decisions().keys())
    pend = esc[~keys.isin(decided)]
    return len(pend), int((pend["lvl"] == "Critical").sum()), pend["ts"]


def _day_counts(ts, anchor):
    ts = pd.Series(ts).dropna()
    if ts.empty:
        return 0, 0
    day = anchor.normalize()
    n = ts.dt.normalize()
    return int((n == day).sum()), int((n == day - pd.Timedelta(days=1)).sum())


def _delta_html(cur, prev, good="down"):
    if prev == 0:
        return f'<span style="color:{MUTE}">{"new" if cur > 0 else "—"}</span> <span class="dim">vs prev day</span>'
    pct = (cur - prev) / prev * 100
    up = pct >= 0
    color = MUTE if pct == 0 else ("#22c55e" if up == (good == "up") else "#f43f5e")
    return (f'<span style="color:{color};font-weight:700">{"↑" if up else "↓"} {abs(pct):.0f}%</span> '
            f'<span class="dim">vs prev day</span>')


def _window(d, rng):
    delta = RANGES[rng]
    if delta is None or d["ts"].dropna().empty:
        return d, None
    start = d["ts"].max() - delta
    return d[d["ts"] >= start], start


# ---------------- html pieces ----------------
def _head(icon, title, sub, badge=""):
    b = f'<span class="live-b">{badge}</span>' if badge else ""
    return (f'<div class="ct"><div class="ct-ico">{_svg(icon, "#7ea6ff", 17)}</div><div style="flex:1">'
            f'<div class="ct-t">{title}</div><div class="ct-s">{sub}</div></div>{b}</div>')


def _kpi_cards(items):
    cards = ""
    for it in items:
        c = it["color"]
        cards += (
            f'<div class="kp"><div class="kp-ico" style="background:{c}22;border:1px solid {c}66">{_svg(it["icon"], c, 24)}</div>'
            f'<div><div class="kp-t">{it["title"]}</div>'
            f'<div class="kp-v" style="color:{it.get("vc", "#e8edff")}">{it["value"]}</div>'
            f'<div class="kp-s">{it["sub"]}</div><div class="kp-d">{it["delta"]}</div></div></div>'
        )
    return f'<div class="kp-grid">{cards}</div>'


def _telemetry_fig(w, rng, anchor):
    """Hamesha bars (stacked) dikhata hai: kam data ho ya zyada, chart saaf rehta hai.
    X-axis selected range ka hota hai aur dono taraf thodi jagah chhodi jati hai."""
    c = w.dropna(subset=["ts"])
    if c.empty:
        return None

    delta = RANGES[rng]
    start = (anchor - delta) if delta is not None else c["ts"].min()
    span = anchor - start

    # span ke hisab se bucket size
    if span <= pd.Timedelta(minutes=30):
        freq, fmt = "1min", "%H:%M"
        start = anchor - pd.Timedelta(minutes=30)
    elif span <= pd.Timedelta(hours=6):
        freq, fmt = "10min", "%H:%M"
    elif span <= pd.Timedelta(days=2):
        freq, fmt = "h", "%H:%M"
    elif span <= pd.Timedelta(days=120):
        freq, fmt = "D", "%d %b"
    else:
        freq, fmt = "7D", "%d %b"          # bahut lamba data ho to hafta-war buckets

    c = c.assign(b=c["ts"].dt.floor(freq))
    pv = c.groupby(["b", "lvl"]).size().unstack(fill_value=0).reindex(columns=LEVELS[:4], fill_value=0)
    full = pd.date_range(min(start.floor(freq), pv.index.min()), anchor.floor(freq), freq=freq)
    if len(full) < 2:
        full = pd.date_range(end=anchor.floor(freq), periods=2, freq=freq)
    pv = pv.reindex(full, fill_value=0)

    fig = go.Figure()
    for lv in ["Low", "Medium", "High", "Critical"]:
        fig.add_trace(go.Bar(x=pv.index, y=pv[lv], name=lv, marker_color=LV_COLOR[lv],
                             hovertemplate="%{y}<extra>" + lv + "</extra>"))

    step = full[1] - full[0]
    theme.plotly_layout(fig, 215)
    fig.update_layout(showlegend=False, margin=dict(l=28, r=8, t=4, b=22), hovermode="x unified",
                      barmode="stack", bargap=0.35,
                      hoverlabel=dict(bgcolor="#0a1230", bordercolor="#4f6df5", font=dict(color="#e8edff")),
                      font=dict(color=MUTE, size=10))
    fig.update_xaxes(tickformat=fmt, title=None,
                     range=[full[0] - step / 2, full[-1] + step / 2],
                     hoverformat="%d %b" if freq in ("D", "7D") else "%d %b %H:%M",
                     gridcolor="rgba(120,140,220,.06)")
    fig.update_yaxes(rangemode="tozero", title=None, gridcolor="rgba(120,140,220,.12)")
    return fig


def _donut_fig(counts, total):
    labels = [k for k in LEVELS if counts.get(k, 0) > 0]
    fig = go.Figure(go.Pie(
        labels=labels, values=[counts[k] for k in labels], sort=False, direction="clockwise", hole=0.62,
        marker=dict(colors=[LV_COLOR[k] for k in labels], line=dict(color="#0a1230", width=3)),
        textinfo="percent", textposition="inside", textfont=dict(color="#fff", size=10),
        hovertemplate="%{label}: %{value} incidents<extra></extra>"))
    fig.add_annotation(text=f"<b>{total}</b><br><span style='font-size:10px;color:{MUTE}'>total incidents</span>",
                       x=0.5, y=0.5, showarrow=False, font=dict(size=22, color="#e8edff"))
    theme.plotly_layout(fig, 200)
    fig.update_layout(showlegend=False, margin=dict(l=4, r=4, t=4, b=4))
    return fig


def _legend_rows(counts):
    rows = ""
    for k in LEVELS:
        rows += (f'<div class="lg-r"><span class="sdot" style="background:{LV_COLOR[k]}"></span>'
                 f'<span class="lg-n">{k}</span><span class="lg-v">{counts.get(k, 0)}</span></div>')
    return f'<div style="padding-top:.4rem">{rows}</div>'


def _alert_rows(d, q):
    a = d[d["attack"]].copy()
    if q:
        def _c(n):
            return a[n].astype(str) if n in a.columns else ""
        blob = (a["pred_s"] + " " + _c("asset") + " " + _c("incident_id") + " " + _c("outcome")).str.lower()
        a = a[blob.str.contains(q.lower(), na=False)]
    a = a.sort_values("ts", ascending=False).head(5)
    head = ('<div class="rt-h"><span></span><span>TIME</span><span>TYPE</span><span>ASSET</span>'
            '<span>SEVERITY</span><span>STATUS</span></div>')
    if a.empty:
        return head + f'<div style="color:{MUTE};font-size:.8rem;padding:.9rem .2rem">No alerts found.</div>'
    decided = set(_load_decisions().keys())
    rows = ""
    for _, r in a.iterrows():
        col = LV_COLOR[r["lvl"]]
        t = r["ts"].strftime("%H:%M") if pd.notna(r["ts"]) else "--:--"
        key = str(r["log_id"]) if "log_id" in r.index else None
        sts = str(r.get("incident_status", "")).lower()
        if sts in ("resolved", "closed"):
            label, sc = "Resolved", "#22c55e"
        elif key in decided:
            label, sc = "Reviewed", "#22d3ee"
        elif r["review"]:
            label, sc = "Needs review", "#f59e0b"
        else:
            label, sc = "Open", "#f43f5e"
        rows += (
            f'<div class="rt-r"><span>{_svg("alert", col, 15)}</span><span class="mono-b" style="color:{MUTE}">{t}</span>'
            f'<span>{html.escape(r["pred_s"])}</span><span>{html.escape(str(r.get("asset", "—")))}</span>'
            f'<span><span class="sevchip" style="color:{col};border-color:{col};background:{col}22">{r["lvl"]}</span></span>'
            f'<span><span class="sdot" style="background:{sc}"></span>{label}</span></div>')
    return head + rows


def _stage_rows(w):
    info = {t: [0, None] for t, *_ in STAGES}
    for _, r in w[w["attack"]].iterrows():
        t = _tactic(r["pred_s"])
        if t:
            info[t][0] += 1
            if pd.notna(r["ts"]) and (info[t][1] is None or r["ts"] > info[t][1]):
                info[t][1] = r["ts"]
    act = [(t, ic, tid, tn, *info[t]) for t, ic, tid, tn in STAGES if info[t][0] > 0]
    act.sort(key=lambda x: -x[4])
    if not act:
        return f'<div style="color:{MUTE};font-size:.8rem;padding:.9rem 0">No attack stages in this range.</div>'
    mx = act[0][4]
    rows = ""
    for t, ic, tid, tn, n, last in act[:5]:
        ago = theme.ago(last).replace(" ago", "")
        rows += (
            f'<div class="sr"><div class="ci">{_svg(ic, "#7ea6ff", 16)}</div>'
            f'<div><div class="sr-t">{t}</div><div class="sr-s">{tid} – {tn}</div></div>'
            f'<div class="bar"><i style="width:{n / mx * 100:.0f}%;background:linear-gradient(90deg,#22d3ee,#60a5fa)"></i></div>'
            f'<div class="sr-v"><b>{n}</b><span>{ago}</span></div></div>')
    return rows


def _asset_rows(w):
    a = w[w["attack"]]
    if a.empty or "asset" not in a.columns:
        return f'<div style="color:{MUTE};font-size:.8rem;padding:.9rem 0">No attacks in this range.</div>'
    top = a["asset"].astype(str).value_counts().head(5)
    mx = int(top.iloc[0])
    colors = ["#f43f5e", "#f59e0b", "#0ea5e9", "#8b5cf6", "#64748b"]
    rows = ""
    for i, (name, n) in enumerate(top.items()):
        ic, sub = _asset_meta(name)
        rows += (
            f'<div class="sr"><div class="ci">{_svg(ic, "#7ea6ff", 16)}</div>'
            f'<div><div class="sr-t">{html.escape(name)}</div><div class="sr-s">{sub}</div></div>'
            f'<div class="bar"><i style="width:{n / mx * 100:.0f}%;background:{colors[i]}"></i></div>'
            f'<div class="sr-v"><b>{int(n)}</b></div></div>')
    return rows


def _brief_facts(d, pend_n, pend_crit, pend_ts, now):
    att = d[d["attack"]]
    anchor = d["ts"].max()
    recent = att[att["ts"] >= anchor - pd.Timedelta(hours=24)] if pd.notna(anchor) else att.iloc[0:0]
    if len(recent):
        base = recent
        fresh = pd.notna(anchor) and (pd.Timestamp(now) - anchor) <= pd.Timedelta(hours=24)
        scope = ("in the last 24 hours" if fresh
                 else f"in the most recent 24 hours of activity, up to {anchor.strftime('%d %b')}")
    else:
        base, scope = att, "overall"
    assets = base["asset"].astype(str).value_counts() if "asset" in base.columns else pd.Series(dtype=int)
    attacks = base["pred_s"].value_counts()
    oldest = pend_ts.dropna().min() if len(pend_ts) else None
    return dict(
        pend_n=pend_n, pend_crit=pend_crit, oldest_ts=oldest, scope=scope,
        asset=assets.index[0] if len(assets) else None, asset_n=int(assets.iloc[0]) if len(assets) else 0,
        attack=attacks.index[0] if len(attacks) else None, attack_n=int(attacks.iloc[0]) if len(attacks) else 0,
    )


def _btn(col, label, key, icon=None):
    try:
        return col.button(label, key=key, icon=icon, use_container_width=True)
    except TypeError:
        return col.button(label, key=key, use_container_width=True)


def _render_briefing(n_now):
    br = st.session_state.get("briefing")
    if not br:
        return
    autoplay = br.pop("fresh", False)      # awaaz sirf pehli baar khud chale, har rerun par nahi
    with st.container(border=True):
        c1, c2 = _cols([6, 1])
        c1.markdown(_head("radio", "Shift Briefing", f"Generated at {br['at']} from the audit log"), unsafe_allow_html=True)
        if c2.button("Close", key="brief_close", use_container_width=True):
            st.session_state.pop("briefing", None)
            st.rerun()
        st.markdown(f'<div style="border-left:3px solid #22d3ee;padding:.55rem 1rem;color:#d3dcf7;font-size:.92rem;'
                    f'line-height:1.65;background:rgba(34,211,238,.05);border-radius:0 8px 8px 0">'
                    f'{html.escape(br["text"])}</div>', unsafe_allow_html=True)
        new = n_now - br.get("n", n_now)
        if new > 0:
            st.markdown(f'<div class="status-banner status-warn" style="margin:.4rem 0"><strong>{new} new record'
                        f'{"" if new == 1 else "s"} since this briefing.</strong> Press Shift briefing to refresh it.</div>',
                        unsafe_allow_html=True)
        if br.get("audio"):
            try:
                st.audio(br["audio"], format="audio/mp3", autoplay=autoplay)
            except TypeError:
                st.audio(br["audio"], format="audio/mp3")
        else:
            st.caption("Audio is not available right now (internet and gTTS are required). The text briefing is shown above.")


# ---------------- page ----------------
def render():
    user = st.session_state.get("user", {"full_name": "Analyst"})
    name = user.get("full_name", "Analyst")
    first = name.split()[0] if name.split() else "Analyst"
    initials = "".join(w[0] for w in name.split()[:2]).upper() or "A"
    now = datetime.now(APP_TZ).replace(tzinfo=None)

    raw = theme.load_audit()
    d = _prep(raw) if not raw.empty else None
    pend_n, pend_crit, pend_ts = (_pending(d) if d is not None else (0, 0, pd.Series(dtype="datetime64[ns]")))

    # ---- top bar ----
    c1, c2, c3 = _cols([5, 0.45, 1.7])
    with c1:
        q = st.text_input("search", placeholder="Search alerts (attack, asset, incident ID)...",
                          label_visibility="collapsed", key="dash_search")
    badge = f'<span class="bell-b">{min(pend_n, 99)}</span>' if pend_n else ""
    c2.markdown(f'<div class="bell">{_svg("bell", "#b4c0e6", 20)}{badge}</div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="uchip"><div class="uav">{initials}</div><div><div class="uname">{html.escape(name)}</div>'
                f'<div class="urole">SOC Analyst</div></div></div>', unsafe_allow_html=True)

    _gap(10)

    # ---- greeting ----
    part = "Morning" if now.hour < 12 else "Afternoon" if now.hour < 18 else "Evening"
    g1, g2 = _cols([4, 1.3], va="top")
    g1.markdown(f'<div class="hello">Good {part}, <span class="hl">{html.escape(first)}</span></div>'
                f'<div class="hello-s">Here\'s what\'s happening in your SOC control room.</div>', unsafe_allow_html=True)
    g2.markdown(f'<div class="clock">{now.strftime("%a, %d %b %Y")}<b>{now.strftime("%H:%M")}</b>'
                f'<span><i class="sdot" style="background:#22c55e"></i>Updated {now.strftime("%H:%M:%S")}</span></div>',
                unsafe_allow_html=True)

    if d is None:
        theme.empty_state("No data yet. Run an analysis in <b>Live Monitor</b> and "
                          "everything will appear here.")
        if st.button("Run analysis", key="qa_empty"):
            _go("live_monitor")
        return

    _gap(8)

    # ---- analyst review queue ----
    with _box("queue_box"):
        b1, bb, b2 = _cols([5, 1.25, 1.1])
        if pend_n:
            title, sub, tone = "Analyst Review Queue", f"{pend_n} cases are awaiting human approval for response actions" \
                                                       f"{f' ({pend_crit} critical)' if pend_crit else ''}.", "#f59e0b"
        else:
            title, sub, tone = "Analyst Review Queue", "All clear — no cases are waiting for an analyst.", "#22d3ee"
        b1.markdown(f'<div class="qb"><div class="qb-ico" style="border-color:{tone}88;color:{tone}">{_svg("user", tone, 22)}</div>'
                    f'<div><div class="qb-t" style="color:{tone}">{title}</div><div class="qb-s">{sub}</div></div></div>',
                    unsafe_allow_html=True)
        if _btn(bb, "Shift briefing", "qa_brief", ":material/volume_up:"):
            with st.spinner("Preparing briefing..."):
                b = briefing.build(first, now, **_brief_facts(d, pend_n, pend_crit, pend_ts, now))
                audio, err = briefing.synthesize(b["speech"])
            st.session_state["briefing"] = {"text": b["text"], "audio": audio, "err": err,
                                            "at": now.strftime("%H:%M"), "fresh": True, "n": len(raw)}
        if b2.button("View Queue →", key="qa_queue", use_container_width=True):
            _go("response_center")

    _render_briefing(len(raw))

    _gap(10)

    # ---- KPI cards ----
    anchor = d["ts"].max() if d["ts"].notna().any() else pd.Timestamp(now)
    inc = _incidents(d)
    total_inc = len(inc)
    done = inc["status"].astype(str).str.lower().isin(["resolved", "closed"])
    oc = inc[(inc["lvl"] == "Critical") & ~done]
    corr = inc[inc["alerts"] >= 2]
    ver_rows = d[d["ver"] == "VERIFIED"]
    approved = sum(1 for v in _load_decisions().values() if v.get("decision") == "APPROVED")
    oc_c, oc_p = _day_counts(oc["last"], anchor)
    pe_c, pe_p = _day_counts(pend_ts, anchor)
    co_c, co_p = _day_counts(corr["last"], anchor)
    ve_c, ve_p = _day_counts(ver_rows["ts"], anchor)
    st.markdown(_kpi_cards([
        {"title": "Open Critical", "value": len(oc), "vc": "#fb7185", "sub": f"of {total_inc} incidents",
         "icon": "shield", "color": "#f43f5e", "delta": _delta_html(oc_c, oc_p, "down")},
        {"title": "Pending Review", "value": pend_n, "sub": "awaiting analyst decision",
         "icon": "clock", "color": "#f59e0b", "delta": _delta_html(pe_c, pe_p, "down")},
        {"title": "Correlated Incidents", "value": len(corr), "sub": f"from {int(corr['alerts'].sum())} related alerts",
         "icon": "link", "color": "#8b5cf6", "delta": _delta_html(co_c, co_p, "down")},
        {"title": "Verified Responses", "value": len(ver_rows) + approved, "sub": "automated / approved",
         "icon": "check", "color": "#22d3ee", "delta": _delta_html(ve_c, ve_p, "up")},
    ]), unsafe_allow_html=True)

    _gap(14)

    # ---- Event telemetry + severity distribution ----
    left, right = _cols([1.9, 1], va="top")
    with left:
        with st.container(border=True):
            h1, h2, h3 = _cols([2.2, 2.1, 1.5])
            h1.markdown(_head("grid", "Event Telemetry", "Severity trends and latest ingested activity"), unsafe_allow_html=True)
            h2.markdown('<div class="lgd">' + "".join(
                f'<span><i class="sdot" style="background:{LV_COLOR[k]}"></i>{k}</span>' for k in LEVELS[:4]) + '</div>',
                unsafe_allow_html=True)
            # default "All time": KPI cards aur graph ek hi data dikhayen
            rng = h3.selectbox("Range", list(RANGES), index=3, label_visibility="collapsed", key="dash_range")
            w, start = _window(d, rng)
            fig = _telemetry_fig(w, rng, anchor)
            if fig is None:
                st.caption("No events in this range.")
            else:
                st.plotly_chart(fig, use_container_width=True)
    with right:
        with st.container(border=True):
            st.markdown(_head("shield", "Attack Severity Distribution", "Incidents by highest severity"),
                        unsafe_allow_html=True)
            iw = inc if start is None else inc[inc["last"] >= start]
            counts = iw["lvl"].value_counts().to_dict()
            dc1, dc2 = _cols([1.05, 1])
            if len(iw):
                dc1.plotly_chart(_donut_fig(counts, len(iw)), use_container_width=True)
            else:
                dc1.caption("No incidents in this range.")
            dc2.markdown(_legend_rows(counts), unsafe_allow_html=True)

    _gap(14)

    # ---- bottom row ----
    b1, b2, b3 = _cols([1.25, 1, 1], va="top")
    with b1:
        with st.container(border=True):
            hh1, hh2 = _cols([3, 1])
            hh1.markdown(_head("alert", "Recent Alerts", "Latest detections from your environment"), unsafe_allow_html=True)
            if hh2.button("View all →", key="dash_viewall", use_container_width=True):
                _go("incidents")
            st.markdown(_alert_rows(d, q), unsafe_allow_html=True)
    with b2:
        with st.container(border=True):
            st.markdown(_head("radio", "MITRE ATT&amp;CK Stages", "Attack flow and technique mapping (approximate)", "Live"),
                        unsafe_allow_html=True)
            st.markdown(_stage_rows(w), unsafe_allow_html=True)
    with b3:
        with st.container(border=True):
            st.markdown(_head("server", "Top Targeted Assets", "Most attacked systems in the selected range"),
                        unsafe_allow_html=True)
            st.markdown(_asset_rows(w), unsafe_allow_html=True)
