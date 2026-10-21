"""
AI Assistant ka dimaagh:
  - load_context()   : audit data se numbers
  - quick_answer()   : aam sawalon ka jawab seedha data se (LLM ke baghair, isliye galat nahi hota)
  - facts_text()     : baaqi sawalon ke liye LLM ko dene wala data summary
"""
import re
from datetime import datetime

import pandas as pd

import briefing
import theme
from pages_ui import overview as ov


def load_context():
    raw = theme.load_audit()
    if raw.empty:
        return None
    d = ov._prep(raw)
    pend_n, pend_crit, pend_ts = ov._pending(d)
    return {"d": d, "inc": ov._incidents(d), "pend_n": pend_n, "pend_crit": pend_crit, "pend_ts": pend_ts}


def _top(series, n=3):
    vc = series.astype(str).value_counts().head(n)
    return [(k, int(v)) for k, v in vc.items()]


def _join(pairs):
    return ", ".join(f"{k} ({v})" for k, v in pairs)


def _latest(d, n=3):
    a = d[d["attack"]].sort_values("ts", ascending=False).head(n)
    rows = []
    for _, r in a.iterrows():
        t = r["ts"].strftime("%d %b %H:%M") if pd.notna(r["ts"]) else "—"
        rows.append(f"{t}: {r['pred_s']} on {r.get('asset', '—')} ({r['lvl']})")
    return rows


def quick_answer(question: str, ctx):
    """Aam sawalon ka seedha jawab. Samajh na aaye to None (phir LLM jawab dega)."""
    q = question.lower()
    pending = re.search(r"pending|awaiting|waiting|review queue|need(s)? review|human review|approval", q)
    critical = re.search(r"critical", q)
    asset = re.search(r"asset|target|server|workstation|domain controller|database", q)
    kinds = re.search(r"common|type|kind|which attack|what attack|attacks? (is|are)|most attack", q)
    latest = re.search(r"latest|recent|newest|last (alert|attack|incident)|summari[sz]e the latest", q)
    totals = re.search(r"how many (incidents|events|records|alerts|attacks)|total", q)
    resolved = re.search(r"resolved|closed", q)
    if not any([pending, critical, asset, kinds, latest, totals, resolved]):
        return None
    if ctx is None:
        return "There is no audit data yet. Run an analysis in Live Monitor first."

    d, inc = ctx["d"], ctx["inc"]
    att = d[d["attack"]]
    if pending:
        n, c = ctx["pend_n"], ctx["pend_crit"]
        if n == 0:
            return "No cases are awaiting analyst review."
        oldest = ctx["pend_ts"].dropna().min() if len(ctx["pend_ts"]) else None
        age = f" The oldest has been waiting for {briefing.fmt_age(pd.Timestamp(datetime.now()) - oldest)}." if pd.notna(oldest) else ""
        return f"{n} cases are awaiting analyst review, {c} of them critical.{age}"
    if resolved:
        done = inc["status"].astype(str).str.lower().isin(["resolved", "closed"]) if len(inc) else pd.Series(dtype=bool)
        return f"{int(done.sum())} of {len(inc)} incidents are resolved; {int((~done).sum())} are still open."
    if critical:
        ev = int((d["lvl"] == "Critical").sum())
        open_c = 0
        if len(inc):
            done = inc["status"].astype(str).str.lower().isin(["resolved", "closed"])
            open_c = int(((inc["lvl"] == "Critical") & ~done).sum())
        return f"{ev} events are rated Critical. {open_c} critical incidents are still open."
    if latest:
        rows = _latest(d)
        return "Latest attacks: " + "; ".join(rows) + "." if rows else "No attacks have been detected yet."
    if asset:
        pairs = _top(att["asset"]) if "asset" in att.columns and len(att) else []
        return ("Most targeted assets: " + _join(pairs) + " attacks.") if pairs else "No attacks have been detected yet."
    if kinds:
        pairs = _top(att["pred_s"]) if len(att) else []
        return ("Most common attacks: " + _join(pairs) + " detections.") if pairs else "No attacks have been detected yet."
    if totals:
        return (f"The audit log holds {len(d)} records: {len(att)} attacks and {len(d) - len(att)} benign. "
                f"They form {len(inc)} incidents.")
    return None


def facts_text(ctx, report: str = "") -> str:
    """LLM ko dene ke liye data summary. LLM ko kehna hai ke sirf isi se jawab de."""
    lines = ["SOC DATA SNAPSHOT (answer ONLY from this data; if it is not here, say you do not know)",
             f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"]
    if ctx is None:
        lines.append("The audit log is empty.")
    else:
        d, inc = ctx["d"], ctx["inc"]
        att = d[d["attack"]]
        done = inc["status"].astype(str).str.lower().isin(["resolved", "closed"]) if len(inc) else pd.Series(dtype=bool)
        lines += [
            f"Audit records: {len(d)} (attacks: {len(att)}, benign: {len(d) - len(att)})",
            f"Incidents: {len(inc)} (open: {int((~done).sum())}, resolved: {int(done.sum())})",
            f"Pending analyst review: {ctx['pend_n']} (critical: {ctx['pend_crit']})",
            "Events by severity: " + ", ".join(f"{k}: {int((d['lvl'] == k).sum())}" for k in ov.LEVELS),
            "Top attack types: " + _join(_top(att["pred_s"], 5)) if len(att) else "Top attack types: none",
            "Top targeted assets: " + _join(_top(att["asset"], 5)) if len(att) and "asset" in att.columns else "Top targeted assets: none",
            "RECENT ATTACKS (newest first):",
        ]
        lines += _latest(d, 15)
    if report:
        lines += ["", "LATEST INCIDENT REPORT:", report[:3500]]
    return "\n".join(lines)


def speakable(text: str, limit: int = 650) -> str:
    """Awaaz ke liye text saaf karo (markdown hatao, lamba ho to chhota karo)."""
    t = re.sub(r"[*#`>|_]", "", text).replace(" / ", " and ")
    t = re.sub(r"\s+", " ", t).strip()
    if len(t) > limit:
        cut = t[:limit]
        t = cut[: cut.rfind(".") + 1] or cut
    return t