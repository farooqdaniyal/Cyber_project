import html
import json
import os
import re
import time
from datetime import datetime

import pandas as pd
import requests
import streamlit as st

import theme
from supervisor_workflow import supervisor_app as pipeline_app

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE_PATH = os.path.join(ROOT, "sample_test_data.csv")
DECISIONS_FILE = os.path.join(ROOT, "response_decisions.json")   # Response center ke sath shared
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "").strip()

ASSET_OPTIONS = [
    "Web Server",
    "Database Server",
    "Employee Workstation",
    "Domain Controller / DNS",
]


# ---------------- small helpers ----------------
def _fmt_at(at) -> str:
    try:
        return pd.Timestamp(at).strftime("%d %b %Y, %H:%M")
    except Exception:
        return str(at)


def _pct(conf: float) -> str:
    """99.9991% ko '100.00%' dikhana model ko zyada yaqeen wala dikhata hai."""
    p = conf * 100
    return f"{p:.4f}%" if p < 100 and round(p, 2) == 100.0 else f"{conf:.2%}"


def _nice(x) -> str:
    return str(x).replace("_", " ").title()


def _rich(text: str) -> str:
    """Escape + **bold** ko <b> mein badlo (LLM text mein asterisks nazar na aayen)."""
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", html.escape(str(text or "")))


def outcome_banner_class(outcome: str) -> str:
    o = (outcome or "").upper()
    if "ESCALAT" in o:
        return "status-warn"
    if "AUTOMATED" in o or "RECOMMENDED" in o:
        return "status-ok"
    return "status-info"


def conf_color(c: float) -> str:
    return "#22d3ee" if c >= 0.9 else "#fbbf24" if c >= 0.7 else "#fb7185"


def risk_color(level: str) -> str:
    return {"critical": "#fb7185", "high": "#fb923c", "medium": "#fbbf24",
            "low": "#22d3ee", "none": "#94a3b8", "": "#94a3b8"}.get((level or "").lower(), "#e8edff")


def risk_banner_class(level: str) -> str:
    lv = (level or "").lower()
    if lv == "critical":
        return "status-danger"
    if lv == "high":
        return "status-warn"
    return "status-info" if lv in ("medium", "low") else "status-ok"


def is_escalated(result: dict) -> bool:
    out = str(result.get("outcome", "")).upper()
    ver = str(result.get("verification_status", "")).upper()
    return "ESCALAT" in out or "HUMAN" in ver


def case_key(result: dict) -> str:
    k = result.get("audit_log_id")
    return str(k if k is not None else result.get("incident_id", "unknown"))


# ---------------- decisions (shared with Response center) ----------------
def load_decisions() -> dict:
    if os.path.exists(DECISIONS_FILE):
        try:
            with open(DECISIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_decision(key: str, decision: str, reason: str):
    dec = load_decisions()
    dec[key] = {
        "decision": decision,
        "by": st.session_state.get("user", {}).get("email", "unknown"),
        "at": datetime.now().isoformat(timespec="seconds"),
        "reason": reason.strip(),
    }
    with open(DECISIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(dec, f, indent=2, ensure_ascii=False)


# ---------------- n8n ----------------
def send_to_n8n(payload: dict):
    if not N8N_WEBHOOK_URL:
        return False, "N8N_WEBHOOK_URL is not set"
    if "webhook-test" in N8N_WEBHOOK_URL:
        return False, "Use the production URL, not webhook-test"
    try:
        r = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=15)
        if r.status_code in (200, 201):
            return True, f"HTTP {r.status_code}"
        return False, f"HTTP {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return False, str(e)


def n8n_banner(saved: dict):
    n8n = saved.get("n8n")
    if not n8n:
        return
    ok, info = n8n
    at = saved.get("n8n_at", "")
    if ok:
        st.markdown(
            f'<div class="status-banner status-info"><strong>Sent to n8n</strong> ({html.escape(info)}, {at}). '
            f'The n8n workflow writes the Google Sheet entry, so please confirm it there.</div>',
            unsafe_allow_html=True)
    else:
        st.markdown(
            f'<div class="status-banner status-danger"><strong>n8n failed</strong> ({at}): {html.escape(info)}. '
            f'The investigation result is safe; only the Sheet logging failed.</div>',
            unsafe_allow_html=True)
        if st.button("Retry n8n", key="n8n_retry"):
            saved["n8n"] = send_to_n8n(saved["payload"])
            saved["n8n_at"] = datetime.now().strftime("%H:%M:%S")
            st.rerun()


# ---------------- input panel ----------------
def input_panel():
    network_row, true_label = None, None
    with st.container(border=True):
        c1, c2, c3 = st.columns([1.3, 1, 1])
        with c1:
            mode = st.radio("Traffic source", ["Sample traffic (demo)", "Upload CSV"],
                            horizontal=True, key="lm_mode")
            if mode == "Sample traffic (demo)":
                if not os.path.exists(SAMPLE_PATH):
                    st.error("sample_test_data.csv was not found in rag/.")
                else:
                    sdf = pd.read_csv(SAMPLE_PATH)
                    sdf.columns = sdf.columns.str.strip()
                    if "Label" not in sdf.columns:
                        st.error("The CSV must contain a **Label** column.")
                    else:
                        chosen = st.selectbox("Attack / traffic class",
                                              sdf["Label"].astype(str).tolist(), key="lm_class")
                        row = sdf[sdf["Label"].astype(str) == chosen].iloc[[0]]
                        true_label = chosen
                        network_row = row.drop(columns=["Label"])
            else:
                up = st.file_uploader("CSV (CICIDS-style features)", type=["csv"], key="lm_upload")
                if up is not None:
                    udf = pd.read_csv(up)
                    udf.columns = udf.columns.str.strip()
                    if "Label" in udf.columns:
                        true_label = str(udf["Label"].iloc[0]) if len(udf) else None
                        udf = udf.drop(columns=["Label"])
                    idx = st.number_input("Row index", 0, max(len(udf) - 1, 0), 0, key="lm_idx")
                    network_row = udf.iloc[[int(idx)]]
                    n_feat = network_row.select_dtypes(include="number").shape[1]
                    st.caption(f"{len(udf)} rows · {n_feat} features")
                    if n_feat < 50:
                        st.error("Too few features — the model expects about 78.")
                        network_row = None
        with c2:
            asset = st.selectbox("Affected asset", ASSET_OPTIONS, key="lm_asset",
                                 help="The same attack is more serious on a Database / DC than on a workstation.")
            st.caption("Risk = base × confidence × asset weight")
        with c3:
            notify = st.checkbox("Send result to n8n / Sheets", value=True, key="lm_n8n")
            if not N8N_WEBHOOK_URL:
                st.caption("Set N8N_WEBHOOK_URL in .env")
            run = st.button("Run full analysis", type="primary",
                            use_container_width=True, disabled=network_row is None, key="lm_run")
    return network_row, true_label, asset, notify, run


def run_analysis(network_row, true_label, asset, notify):
    bar = st.empty()
    bar.markdown('<div class="scan-bar"></div>', unsafe_allow_html=True)
    t0 = time.time()
    result = pipeline_app.invoke({"network_data": network_row, "asset": asset})
    elapsed = time.time() - t0
    bar.empty()

    payload = {
        "attack": result.get("prediction"),
        "confidence": float(result.get("confidence") or 0),
        "risk_score": result.get("risk_score"),
        "risk_level": result.get("risk_level"),
        "target": asset,
        "incident_id": result.get("incident_id"),
        "verification_status": result.get("verification_status"),
        "outcome": result.get("outcome"),
        "audit_log_id": result.get("audit_log_id"),
        "analyst": st.session_state.get("user", {}).get("email", "unknown"),
    }
    saved = {"result": result, "elapsed": elapsed, "asset": asset, "true_label": true_label,
             "payload": payload, "n8n": None, "n8n_at": ""}
    if notify:
        saved["n8n"] = send_to_n8n(payload)
        saved["n8n_at"] = datetime.now().strftime("%H:%M:%S")
    st.session_state["lm_result"] = saved


# ---------------- pieces of the result view ----------------
def stages_html(result: dict, decision) -> str:
    created = result.get("incident_created")
    ver = str(result.get("verification_status", "")).upper()
    iid = result.get("incident_id")

    s1 = ("done", "Complete") if result.get("prediction") else ("fail", "No prediction")
    s2 = ("done", "Scored") if result.get("risk_score") is not None else ("fail", "Not scored")
    s3 = (("done", "New incident" if created else "Merged") if iid not in (None, "—", "")
          else ("fail", "No incident"))
    if ver == "VERIFIED":
        s4 = ("done", "Verified")
    elif "HUMAN" in ver:
        s4 = ("wait", "Human review required")
    else:
        s4 = ("wait", _nice(ver) or "Pending")
    if not is_escalated(result):
        s5 = ("done", "Response done")
    elif decision:
        s5 = ("done", f'{_nice(decision["decision"])} (recorded)')
    else:
        s5 = ("wait", "Awaiting approval")

    names = ["Investigation", "Risk Engine", "Incident", "Verification", "Response"]
    marks = {"done": "✓", "wait": "…", "fail": "✕"}
    cards = ""
    for i, ((cls, text), name) in enumerate(zip([s1, s2, s3, s4, s5], names), 1):
        cards += (f'<div class="tl-step {cls}"><div class="tl-num">0{i} {marks[cls]}</div>'
                  f'<div class="tl-title">{name}</div><div class="tl-desc">{html.escape(text)}</div></div>')
    return f'<div class="timeline">{cards}</div>'


def raw_risk(bd: dict):
    try:
        return float(bd["severity_base"]) * float(bd["model_confidence"]) * float(bd["asset_weight"])
    except Exception:
        return None


def decision_panel(result: dict, decision):
    key = case_key(result)
    if decision:
        cls = "status-ok" if decision["decision"] == "APPROVED" else "status-warn"
        reason = f' · Reason: {html.escape(decision["reason"])}' if decision.get("reason") else ""
        st.markdown(
            f'<div class="status-banner {cls}"><strong>Analyst decision recorded: {_nice(decision["decision"])}</strong>'
            f'<div style="margin-top:.4rem;font-size:.88rem">By {html.escape(str(decision.get("by", "—")))} '
            f'on {html.escape(_fmt_at(decision.get("at", "—")))}{reason}</div></div>', unsafe_allow_html=True)
        return
    if not is_escalated(result):
        return
    with st.container(border=True):
        st.markdown('<div class="card-title">Analyst decision</div>'
                    '<div style="color:#8c9ac4;font-size:.76rem;margin:-.15rem 0 .6rem">'
                    'This case needs a human decision. The decision is saved in the audit record.</div>',
                    unsafe_allow_html=True)
        reason = st.text_input("Reason (optional)", key=f"lm_reason_{key}", placeholder="Enter the reason for your decision")
        a, b, _ = st.columns([1, 1, 2])
        if a.button("Approve response", key=f"lm_ok_{key}", type="primary", use_container_width=True):
            save_decision(key, "APPROVED", reason)
            st.rerun()
        if b.button("Reject response", key=f"lm_no_{key}", use_container_width=True):
            save_decision(key, "REJECTED", reason)
            st.rerun()
        st.caption("Note: this system does not execute any mitigation by itself. Approval is only the analyst's "
                   "recorded decision, not proof that the attack was blocked.")


def incident_tab(result: dict):
    iid = result.get("incident_id") or "—"
    action = "NEW" if result.get("incident_created") else "MERGED"
    first = last = "—"
    rows_html = ""
    try:
        d = theme.load_audit()
        rows = d[d["incident_id"].astype(str) == str(iid)] if "incident_id" in d.columns else d.iloc[0:0]
        if not rows.empty:
            if "ts" in rows.columns and rows["ts"].notna().any():
                first = rows["ts"].min().strftime("%Y-%m-%d %H:%M:%S")
                last = rows["ts"].max().strftime("%Y-%m-%d %H:%M:%S")
                rows = rows.sort_values("ts", ascending=False)
            body = []
            for _, r in rows.head(10).iterrows():
                t = r["ts"].strftime("%H:%M:%S") if "ts" in r and pd.notna(r["ts"]) else "—"
                body.append([
                    f'<span class="idc">{t}</span>',
                    f'<span class="ftag">{html.escape(str(r.get("prediction", "—")))}</span>',
                    html.escape(str(r.get("asset", "—"))),
                    theme.risk_bar(r.get("risk_score"), r.get("risk_level", "None")),
                    theme.level_chip(r.get("risk_level", "None")),
                    html.escape(_nice(r.get("outcome", "—"))),
                ])
            rows_html = theme.html_table(["Time", "Attack", "Asset", "Score", "Level", "Outcome"], body)
    except Exception:
        rows_html = ""
    st.markdown(f"""<div class="panel"><h3>Incident correlation</h3><div class="panel-body mono">
      id: {html.escape(str(iid))}<br/>action: {action}<br/>family: {html.escape(str(result.get("incident_family") or "—"))}<br/>
      status: {html.escape(str(result.get("incident_status") or "—"))}<br/>
      alerts (pipeline): {result.get("incident_alert_count") or 0}<br/>
      first seen: {first}<br/>last seen: {last}<br/>
      <span style="color:#7ea6ff">rule: family + asset + 5 min window</span></div></div>""",
                unsafe_allow_html=True)
    if rows_html:
        st.markdown('<div class="card-title">Related alerts (audit log)</div>', unsafe_allow_html=True)
        st.markdown(rows_html, unsafe_allow_html=True)
    else:
        st.caption("No audit log record found for this incident.")


# ---------------- result view ----------------
def show_result(saved: dict):
    result, elapsed, asset = saved["result"], saved["elapsed"], saved["asset"]
    true_label = saved["true_label"]

    pred = result.get("prediction", "—")
    conf = float(result.get("confidence") or 0)
    ver = result.get("verification_status", "—")
    outcome = result.get("outcome", "—")
    rule = result.get("rule_decision", "—")
    explanation = result.get("explanation", "")
    report = result.get("report", "")
    message = result.get("message", "")
    risk_score = result.get("risk_score")
    risk_level = result.get("risk_level") or "—"
    bd = result.get("risk_breakdown") or {}
    incident_id = result.get("incident_id") or "—"
    alert_count = result.get("incident_alert_count") or 0
    action = "NEW" if result.get("incident_created") else "MERGED"
    score_txt = "—" if risk_score is None else f"{float(risk_score):.1f}"
    rc = risk_color(str(risk_level))
    raw = raw_risk(bd)
    decision = load_decisions().get(case_key(result))

    n8n_banner(saved)
    st.markdown(stages_html(result, decision), unsafe_allow_html=True)

    match_html = ""
    if true_label is not None:
        matched = true_label == pred
        match_html = (f'<div class="metric-sub" style="color:{"#22d3ee" if matched else "#fbbf24"}">'
                      f'{"Match vs ground truth" if matched else f"Ground truth: {true_label}"}</div>')
    risk_sub = (f"Raw {raw:.1f}, capped at 100" if raw is not None and raw > 100
                else "base × confidence × asset weight")

    st.markdown(f"""
    <div class="metric-grid">
      <div class="metric-card"><div class="metric-label">Model prediction</div>
        <div class="metric-value">{html.escape(str(pred))}</div>{match_html}</div>
      <div class="metric-card"><div class="metric-label">Model confidence</div>
        <div class="metric-value" style="color:{conf_color(conf)}">{_pct(conf)}</div>
        <div class="metric-sub">How sure the model is, not proof the attack is real</div></div>
      <div class="metric-card"><div class="metric-label">Calculated risk</div>
        <div class="metric-value" style="color:{rc}">{score_txt}</div>
        <div class="metric-sub">{risk_sub}</div></div>
      <div class="metric-card"><div class="metric-label">Risk level</div>
        <div class="metric-value" style="color:{rc};font-size:1.1rem">{html.escape(str(risk_level))}</div>
        <div class="metric-sub">Asset: {html.escape(asset)}</div></div>
      <div class="metric-card"><div class="metric-label">Verification</div>
        <div class="metric-value" style="font-size:.95rem">{html.escape(_nice(ver))}</div>
        <div class="metric-sub">{elapsed:.1f}s end-to-end</div></div>
    </div>""", unsafe_allow_html=True)

    st.markdown(f"""
    <div class="status-banner {risk_banner_class(str(risk_level))}">
      <strong>Risk assessment: {html.escape(str(risk_level))} ({score_txt}/100)</strong>
      <div style="margin-top:.4rem;font-size:.88rem">Attack severity × model confidence × asset weight.</div></div>
    <div class="status-banner {outcome_banner_class(str(outcome))}">
      <strong>Outcome: {html.escape(_nice(outcome))}</strong>
      <div style="margin-top:.5rem">{_rich(message)}</div></div>""", unsafe_allow_html=True)

    decision_panel(result, decision)

    t_an, t_inc, t_rep, t_dbg = st.tabs(["Analysis", "Incident", "Report", "Debug"])

    with t_an:
        a, b, c = st.columns(3)
        path_label = "Automated action" if str(ver).upper() == "VERIFIED" else "Human escalation"
        a.markdown(f"""<div class="panel"><h3>Verification rationale</h3><div class="panel-body">
          <p class="mono" style="color:#22d3ee">{html.escape(str(rule))}</p>
          <p style="margin:0">{_rich(explanation)}</p></div></div>""", unsafe_allow_html=True)
        b.markdown(f"""<div class="panel"><h3>Pipeline path</h3><div class="panel-body mono">
          Investigation<br/>→ Risk ({html.escape(str(risk_level))} / {score_txt})<br/>
          → Incident ({action}, {alert_count})<br/>→ Verification ({html.escape(_nice(ver))})<br/>
          → {path_label}<br/>→ {html.escape(_nice(outcome))}<br/>→ n8n / Audit</div></div>""",
                   unsafe_allow_html=True)
        raw_line = (f'raw: {bd.get("severity_base")} × {bd.get("model_confidence")} × {bd.get("asset_weight")} = {raw:.1f}<br/>'
                    f'final: min(100, raw) = {score_txt}') if raw is not None else f"final: {score_txt}"
        c.markdown(f"""<div class="panel"><h3>Risk breakdown</h3><div class="panel-body mono">
          type: {html.escape(str(bd.get("attack_type", "—")))}<br/>severity_base: {bd.get("severity_base", "—")}<br/>
          model_confidence: {bd.get("model_confidence", "—")}<br/>asset: {html.escape(str(bd.get("asset", asset)))}<br/>
          asset_weight: {bd.get("asset_weight", "—")}<br/>
          <span style="color:#7ea6ff">{raw_line}</span></div></div>""", unsafe_allow_html=True)

    with t_inc:
        incident_tab(result)

    with t_rep:
        if report:
            st.markdown(report)
        else:
            st.caption("No report was generated for this run.")

    with t_dbg:
        st.markdown("**Supervisor decisions (which agent ran, and why)**")
        for line in result.get("supervisor_log") or []:
            st.markdown(f"- `{line}`")
        st.markdown("**Raw pipeline state**")
        st.json({
            "prediction": pred, "confidence": conf, "asset": asset,
            "risk_score": risk_score, "risk_level": risk_level, "risk_breakdown": bd,
            "incident_id": incident_id, "incident_status": result.get("incident_status"),
            "incident_alert_count": alert_count, "verification_status": ver,
            "rule_decision": rule, "outcome": outcome,
            "audit_log_id": result.get("audit_log_id"),
            "supervisor_steps": result.get("step_count"),
            "report_retries": result.get("report_retries"),
            "latency_sec": round(elapsed, 2),
            "n8n_webhook_configured": bool(N8N_WEBHOOK_URL),
        })


# ---------------- page entry ----------------
def render():
    theme.page_header("Live monitor", "Live monitor",
                      "Choose traffic and an asset, then run the full pipeline.")
    network_row, true_label, asset, notify, run = input_panel()

    if run and network_row is not None:
        run_analysis(network_row, true_label, asset, notify)

    saved = st.session_state.get("lm_result")
    if saved:
        show_result(saved)
    else:
        st.markdown("""
        <div class="timeline">
          <div class="tl-step"><div class="tl-num">01</div><div class="tl-title">Investigation</div><div class="tl-desc">ML + RAG + LLM</div></div>
          <div class="tl-step"><div class="tl-num">02</div><div class="tl-title">Risk Engine</div><div class="tl-desc">Score + level</div></div>
          <div class="tl-step"><div class="tl-num">03</div><div class="tl-title">Incident</div><div class="tl-desc">Group alerts</div></div>
          <div class="tl-step"><div class="tl-num">04</div><div class="tl-title">Verification</div><div class="tl-desc">Policy gate</div></div>
          <div class="tl-step"><div class="tl-num">05</div><div class="tl-title">Response</div><div class="tl-desc">Approve / log</div></div>
        </div>""", unsafe_allow_html=True)