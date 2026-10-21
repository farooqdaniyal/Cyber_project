import html
import json
import math
import os
from datetime import datetime

import pandas as pd
import streamlit as st

import theme
from theme import load_audit, empty_state

DECISIONS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                              "response_decisions.json")
PER_PAGE = 8
GREEN, RED, AMBER = "#22c55e", "#f43f5e", "#f59e0b"


def _cols(spec):
    try:
        return st.columns(spec, vertical_alignment="center")
    except TypeError:
        return st.columns(spec)


def _nice(x) -> str:
    return str(x).replace("_", " ").title()


def _load():
    if os.path.exists(DECISIONS_FILE):
        try:
            with open(DECISIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save(dec):
    with open(DECISIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(dec, f, indent=2, ensure_ascii=False)


def _case_html(r) -> str:
    lvl = r.get("risk_level", "None")
    ts = r.get("ts")
    when = theme.ago(ts) if ts is not None else "—"
    inc = html.escape(str(r.get("incident_id", "—")))
    return (
        '<div style="display:flex;align-items:center;gap:.9rem;flex-wrap:wrap">'
        f'{theme.level_chip(lvl)}<div>'
        f'<div style="font-weight:700;color:#fff">{html.escape(str(r.get("prediction", "—")))} '
        f'<span style="color:#8c9ac4;font-weight:500">on {html.escape(str(r.get("asset", "—")))}</span></div>'
        f'<div style="font-size:.72rem;color:#8c9ac4"><span class="idc">{inc}</span> · {when}</div></div>'
        f'<div style="margin-left:auto">{theme.risk_bar(r.get("risk_score"), lvl)}</div></div>'
    )


def _history_html(dec: dict, d: pd.DataFrame, page: int):
    lookup = {}
    if "log_id" in d.columns:
        lookup = {str(r["log_id"]): r for r in d.to_dict("records")}
    items = sorted(dec.items(), key=lambda kv: kv[1].get("at", ""), reverse=True)
    chunk = items[(page - 1) * PER_PAGE: page * PER_PAGE]
    rows, colors = [], []
    for key, v in chunk:
        r = lookup.get(key, {})
        decision = v.get("decision", "—")
        c = GREEN if decision == "APPROVED" else RED if decision == "REJECTED" else AMBER
        at = v.get("at", "")
        try:
            when = f'<span title="{html.escape(at)}">{theme.ago(pd.Timestamp(at))}</span>'
        except Exception:
            when = html.escape(at) or "—"
        reason = (v.get("reason") or "").strip()
        reason_html = (f'<span style="display:inline-block;max-width:260px;overflow:hidden;text-overflow:ellipsis;'
                       f'vertical-align:bottom" title="{html.escape(reason)}">{html.escape(reason)}</span>'
                       if reason else '<span class="dim">—</span>')
        rows.append([
            f'<span class="idc">#{html.escape(str(key))}</span>',
            theme.pill(_nice(decision), c),
            f'<span class="ftag">{html.escape(str(r.get("prediction", "—")))}</span>' if r else '<span class="dim">—</span>',
            html.escape(str(r.get("asset", "—"))) if r else '<span class="dim">—</span>',
            theme.level_chip(r.get("risk_level", "None")) if r else '<span class="dim">—</span>',
            html.escape(str(v.get("by", "—"))),
            when,
            reason_html,
        ])
        colors.append(c)
    return theme.html_table(["Case", "Decision", "Attack", "Asset", "Level", "Decided by", "When", "Reason"],
                            rows, colors)


def render():
    theme.page_header("Response center", "Response center",
                      "Approve or reject the cases that need a human decision.")
    d = load_audit()
    if d.empty:
        return empty_state()

    ver = d["verification_status"].astype(str).str.upper() if "verification_status" in d else pd.Series("", index=d.index)
    out = d["outcome"].astype(str).str.upper() if "outcome" in d else pd.Series("", index=d.index)
    esc = d[(ver != "VERIFIED") | out.str.contains("ESCALAT")].copy()
    dec = _load()

    if esc.empty and not dec:
        return empty_state("No cases were escalated. Everything was verified automatically.")

    esc["case_key"] = esc["log_id"].astype(str) if "log_id" in esc else esc.index.astype(str)
    pending = esc[~esc["case_key"].isin(dec)]
    approved = sum(1 for k in esc["case_key"] if dec.get(k, {}).get("decision") == "APPROVED")
    rejected = sum(1 for k in esc["case_key"] if dec.get(k, {}).get("decision") == "REJECTED")

    theme.kpi_cards([
        {"label": "Escalated cases", "value": len(esc), "sub": "Needs human review", "icon": "⛨"},
        {"label": "Pending", "value": len(pending), "sub": "Awaiting a decision", "icon": "◔", "tone": "amber"},
        {"label": "Approved", "value": approved, "sub": "Response approved", "icon": "✓"},
        {"label": "Rejected", "value": rejected, "sub": "Response rejected", "icon": "✕", "tone": "red"},
    ])

    # ---------------- pending cases ----------------
    theme.section("Pending cases", "The 10 newest cases. Each decision is saved in the audit record.")
    if pending.empty:
        st.markdown('<div class="coming">No pending cases. All decisions have been made.</div>', unsafe_allow_html=True)
    if "ts" in pending.columns:
        pending = pending.sort_values("ts", ascending=False)
    for _, r in pending.head(10).iterrows():
        key = r["case_key"]
        with st.container(border=True):
            c_info, c_reason, c_ok, c_no = _cols([4.2, 2.2, 1, 1])
            c_info.markdown(_case_html(r), unsafe_allow_html=True)
            reason = c_reason.text_input("Reason", key=f"rc_reason_{key}", placeholder="Reason (optional)",
                                         label_visibility="collapsed")
            for label, value, col, kind in (("Approve", "APPROVED", c_ok, "primary"),
                                            ("Reject", "REJECTED", c_no, "secondary")):
                if col.button(label, key=f"{value}_{key}", type=kind, use_container_width=True):
                    dec[key] = {
                        "decision": value,
                        "by": st.session_state.get("user", {}).get("email", "unknown"),
                        "at": datetime.now().isoformat(timespec="seconds"),
                        "reason": (reason or "").strip(),
                    }
                    _save(dec)
                    st.rerun()

    # ---------------- decision history ----------------
    theme.section("Decision history", "All decisions so far, newest first")
    if not dec:
        st.markdown('<div class="coming">No decisions have been made yet.</div>', unsafe_allow_html=True)
        return
    hist = pd.DataFrame([{"case": k, **v} for k, v in dec.items()]).sort_values("at", ascending=False)
    page, start, end = theme.table_controls(
        len(dec), PER_PAGE, "rc_page", hist.to_csv(index=False).encode("utf-8"), "decision_history.csv", "decisions")
    st.markdown(_history_html(dec, d, page), unsafe_allow_html=True)
    st.markdown('<div style="height:.6rem"></div>', unsafe_allow_html=True)