import html
import math

import pandas as pd
import streamlit as st

import theme
from theme import load_audit, empty_state, LEVEL_ORDER, pick

PER_PAGE = 10


def _top_level(s):
    s = s.dropna().astype(str)
    return max(s, key=lambda x: LEVEL_ORDER.get(x.lower(), 0)) if not s.empty else "—"


def _mode(s):
    s = s.dropna()
    return s.mode().iat[0] if not s.empty else "—"


def build_incidents(d: pd.DataFrame) -> pd.DataFrame:
    d = d[d["incident_id"].notna() & (d["incident_id"].astype(str) != "—")]
    g = d.groupby("incident_id")
    inc = pd.DataFrame({"alerts": g.size()})
    if "incident_alert_count" in d.columns:
        inc["alerts"] = pd.to_numeric(g["incident_alert_count"].max(), errors="coerce").fillna(inc["alerts"])
    if "prediction" in d.columns:
        inc["family"] = g["prediction"].agg(_mode)
    if "asset" in d.columns:
        inc["asset"] = g["asset"].last()
    if "risk_score" in d.columns:
        inc["max_risk"] = g["risk_score"].max().round(1)
    if "risk_level" in d.columns:
        inc["level"] = g["risk_level"].agg(_top_level)
    if "incident_status" in d.columns:
        inc["status"] = g["incident_status"].last()
    if "ts" in d.columns:
        inc["last_seen"] = g["ts"].max()
    return inc.reset_index()


def _table_html(page_df: pd.DataFrame) -> str:
    rows, colors = [], []
    for _, r in page_df.iterrows():
        level = r.get("level", "None")
        ts = r.get("last_seen")
        exact = ts.strftime("%Y-%m-%d %H:%M:%S") if pd.notna(ts) else ""
        rows.append([
            f'<span class="idc">{html.escape(str(r["incident_id"]))}</span>',
            f'<span class="ftag">{html.escape(str(r.get("family", "—")))}</span>',
            html.escape(str(r.get("asset", "—"))),
            f'<span class="abadge">{int(r.get("alerts", 0))}</span>',
            theme.risk_bar(r.get("max_risk"), level),
            theme.level_chip(level),
            theme.status_chip(r.get("status", "—")),
            f'<span title="{exact}">{theme.ago(ts)}</span>',
        ])
        colors.append(theme.SEV_COLORS.get(str(level).lower(), "#64748b"))
    return theme.html_table(
        ["Incident", "Family", "Asset", "Alerts", "Risk score", "Level", "Status", "Last seen"],
        rows, colors, num_cols=(3,),
    )


def _detail(d: pd.DataFrame, inc_row: pd.Series):
    rows = d[d["incident_id"] == inc_row["incident_id"]]
    if "ts" in rows.columns:
        rows = rows.sort_values("ts", ascending=False)
    level = inc_row.get("level", "None")
    st.markdown(
        f'<div class="panel"><div class="det-head"><span class="det-id">{html.escape(str(inc_row["incident_id"]))}</span>'
        f'<span class="ftag">{html.escape(str(inc_row.get("family", "—")))}</span>'
        f'{theme.level_chip(level)}{theme.status_chip(inc_row.get("status", "—"))}'
        f'<span class="dim">Asset: {html.escape(str(inc_row.get("asset", "—")))} · '
        f'{int(inc_row.get("alerts", 0))} alert(s)</span></div></div>',
        unsafe_allow_html=True,
    )
    body, colors = [], []
    for _, a in rows.iterrows():
        t = a["ts"].strftime("%m-%d %H:%M:%S") if "ts" in a and pd.notna(a["ts"]) else "—"
        lvl = a.get("risk_level", "None")
        body.append([
            f'<span class="idc">{t}</span>',
            f'<span class="ftag">{html.escape(str(a.get("prediction", "—")))}</span>',
            html.escape(str(a.get("asset", "—"))),
            theme.risk_bar(a.get("risk_score"), lvl),
            theme.level_chip(lvl),
            theme.outcome_pill(a.get("outcome") or a.get("verification_status") or "—"),
        ])
        colors.append(theme.SEV_COLORS.get(str(lvl).lower(), "#64748b"))
    st.markdown('<div class="card-title" style="margin-top:.4rem">Alert timeline</div>', unsafe_allow_html=True)
    st.markdown(theme.html_table(["Time", "Attack", "Asset", "Risk score", "Level", "Outcome"], body, colors),
                unsafe_allow_html=True)


def render():
    theme.page_header("Incidents", "Incidents", "Related alerts are grouped into a single incident.")
    d = load_audit()
    if d.empty or "incident_id" not in d.columns:
        return empty_state()

    inc = build_incidents(d)
    if inc.empty:
        return empty_state("No incidents have been created yet.")

    closed = (inc["status"].astype(str).str.lower().isin(["resolved", "closed"])
              if "status" in inc else pd.Series(False, index=inc.index))
    crit = (inc["level"].astype(str).str.lower() == "critical").sum() if "level" in inc else 0
    theme.kpi_cards([
        {"label": "Total incidents", "value": len(inc), "sub": "Unique incident IDs", "icon": "⚑"},
        {"label": "Open", "value": int((~closed).sum()), "sub": "Not yet resolved", "icon": "◔", "tone": "amber"},
        {"label": "Critical", "value": int(crit), "sub": "Highest severity", "icon": "!", "tone": "red"},
        {"label": "Resolved", "value": int(closed.sum()), "sub": "Closed so far", "icon": "✓"},
    ])

    theme.section("Incident list", "Search, filter and sort, then view the details below")
    f1, f2, f3, f4 = st.columns([1.4, 1.3, 1.5, 1])
    q = f1.text_input("Search", placeholder="Incident ID / asset", key="inc_q")
    levels = sorted(inc["level"].unique(), key=lambda x: -LEVEL_ORDER.get(str(x).lower(), 0)) if "level" in inc else []
    sel_levels = f2.multiselect("Risk level", levels, default=levels, key="inc_lvl")
    families = sorted(inc["family"].unique()) if "family" in inc else []
    sel_fam = f3.multiselect("Attack family", families, default=families, key="inc_fam")
    sort = f4.selectbox("Sort by", ["Newest", "Highest risk", "Most alerts"], key="inc_sort")

    view = inc.copy()
    if "level" in view:
        view = view[view["level"].isin(sel_levels)]
    if "family" in view:
        view = view[view["family"].isin(sel_fam)]
    if q:
        blob = view["incident_id"].astype(str) + " " + (view["asset"].astype(str) if "asset" in view else "")
        view = view[blob.str.contains(q, case=False, na=False)]

    if sort == "Highest risk" and "max_risk" in view:
        view = view.sort_values("max_risk", ascending=False)
    elif sort == "Most alerts":
        view = view.sort_values("alerts", ascending=False)
    elif "last_seen" in view:
        view = view.sort_values("last_seen", ascending=False)

    n = len(view)
    if n == 0:
        return empty_state("No incidents match this filter.")

    page, start, end = theme.table_controls(
        n, PER_PAGE, "inc_page", view.to_csv(index=False).encode("utf-8"), "incidents.csv", "incidents")
    st.markdown(_table_html(view.iloc[start:end]), unsafe_allow_html=True)
    st.markdown('<div style="height:.6rem"></div>', unsafe_allow_html=True)

    theme.section("Incident detail", "Select an incident to see its alert timeline")
    ids = view["incident_id"].tolist()
    chosen = st.selectbox("Incident", ids, key="inc_pick")
    _detail(d, view[view["incident_id"] == chosen].iloc[0])