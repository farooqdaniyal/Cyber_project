import html
import math

import pandas as pd
import streamlit as st

import theme
from theme import load_audit, empty_state

PER_PAGE = 12
GREEN, RED, AMBER, BLUE = "#22c55e", "#f43f5e", "#f59e0b", "#4f6df5"


def _nice(x) -> str:
    return str(x).replace("_", " ").title()


def _verify_pill(v) -> str:
    s = str(v).upper()
    c = GREEN if s == "VERIFIED" else AMBER if "HUMAN" in s else BLUE
    return theme.pill(_nice(v), c)


def _outcome_pill(o) -> str:
    s = str(o).upper()
    c = AMBER if "ESCALAT" in s else GREEN if ("AUTOMATED" in s or "RECOMMENDED" in s) else BLUE
    return theme.pill(_nice(o), c)


def _table_html(rows_df: pd.DataFrame) -> str:
    rows, colors = [], []
    for _, r in rows_df.iterrows():
        ts = r.get("ts")
        when = ts.strftime("%Y-%m-%d %H:%M:%S") if pd.notna(ts) else str(r.get("timestamp", "—"))
        level = r.get("risk_level", "None")
        inc = r.get("incident_id")
        inc_html = f'<span class="idc">{html.escape(str(inc))}</span>' if pd.notna(inc) and str(inc) != "—" else '<span class="dim">—</span>'
        rows.append([
            f'<span class="idc">#{html.escape(str(r.get("log_id", "—")))}</span>',
            f'<span class="mono-b">{when}</span>',
            f'<span class="ftag">{html.escape(str(r.get("prediction", "—")))}</span>',
            html.escape(str(r.get("asset", "—"))),
            theme.risk_bar(r.get("risk_score"), level),
            theme.level_chip(level),
            inc_html,
            _verify_pill(r.get("verification_status", "—")),
            _outcome_pill(r.get("outcome", "—")),
        ])
        colors.append(theme.SEV_COLORS.get(str(level).lower(), "#64748b"))
    return theme.html_table(
        ["ID", "Time", "Attack", "Asset", "Risk score", "Level", "Incident", "Verification", "Outcome"],
        rows, colors)


def render():
    theme.page_header("Audit logs", "Audit logs",
                      "A record of every analysis (kept even after a restart).")
    d = load_audit()
    if d.empty:
        return empty_state()

    ver = d["verification_status"].astype(str).str.upper() if "verification_status" in d else pd.Series("", index=d.index)
    crit = int((d["risk_level"].str.lower() == "critical").sum()) if "risk_level" in d else 0
    theme.kpi_cards([
        {"label": "Total records", "value": len(d), "sub": "Full history", "icon": "≡"},
        {"label": "Critical", "value": crit, "sub": "Highest severity", "icon": "!", "tone": "red"},
        {"label": "Needs review", "value": int(ver.str.contains("HUMAN").sum()), "sub": "Waiting for an analyst",
         "icon": "◔", "tone": "amber"},
        {"label": "Verified", "value": int((ver == "VERIFIED").sum()), "sub": "Automatically verified", "icon": "✓"},
    ])

    theme.section("Records", "Filter, search and download as CSV")
    f1, f2, f3, f4 = st.columns([1.6, 1.3, 1.5, 1.2])
    q = f1.text_input("Search", placeholder="Incident ID / asset / attack", key="al_q")
    view = d
    if "risk_level" in d.columns:
        levels = sorted(d["risk_level"].unique())
        sel = f2.multiselect("Risk level", levels, default=levels, key="al_lvl")
        view = view[view["risk_level"].isin(sel)]
    if "prediction" in d.columns:
        preds = sorted(d["prediction"].astype(str).unique())
        selp = f3.multiselect("Prediction", preds, default=preds, key="al_pred")
        view = view[view["prediction"].astype(str).isin(selp)]
    order = f4.selectbox("Sort by", ["Newest", "Oldest", "Highest risk"], key="al_sort")

    if q:
        def _c(name):
            return view[name].astype(str) if name in view.columns else ""
        blob = (_c("incident_id") + " " + _c("asset") + " " + _c("prediction")).str.lower()
        view = view[blob.str.contains(q.lower(), na=False)]
    if order == "Highest risk" and "risk_score" in view:
        view = view.sort_values("risk_score", ascending=False)
    elif "ts" in view.columns:
        view = view.sort_values("ts", ascending=(order == "Oldest"))

    n = len(view)
    if n == 0:
        return empty_state("No records match this filter.")
    keep = [c for c in ["log_id", "timestamp", "prediction", "asset", "risk_score", "risk_level", "incident_id",
                        "incident_status", "incident_alert_count", "verification_status", "outcome"] if c in view.columns]
    page, start, end = theme.table_controls(
        n, PER_PAGE, "al_page", view[keep].to_csv(index=False).encode("utf-8"), "audit_log.csv", "records")
    st.markdown(_table_html(view.iloc[start:end]), unsafe_allow_html=True)
    st.markdown('<div style="height:.6rem"></div>', unsafe_allow_html=True)