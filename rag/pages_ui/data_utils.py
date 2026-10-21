import pandas as pd
import streamlit as st

from audit_log import AUDIT_LOGGER

LEVEL_ORDER = {"none": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}


def load_audit() -> pd.DataFrame:
    """Audit log ko saaf dataframe ki shakal mein deta hai (khali ho to empty df)."""
    df = AUDIT_LOGGER.get_all_as_dataframe()
    if df.empty:
        return df
    d = df.copy()
    if "risk_level" in d.columns:
        d["risk_level"] = d["risk_level"].fillna("None").astype(str)
    if "risk_score" in d.columns:
        d["risk_score"] = pd.to_numeric(d["risk_score"], errors="coerce")
    if "timestamp" in d.columns:
        d["ts"] = pd.to_datetime(d["timestamp"], errors="coerce")
    return d


def pick(d: pd.DataFrame, cols):
    return [c for c in cols if c in d.columns]


def last_report() -> str:
    """Live monitor ki sab se recent report (session se)."""
    saved = st.session_state.get("lm_result") or {}
    return (saved.get("result") or {}).get("report", "") or ""


def empty_state(msg="Abhi koi data nahi. Live monitor mein kuch analysis chalayein."):
    st.markdown(f'<div class="coming">{msg}</div>', unsafe_allow_html=True)