import streamlit as st

import theme
from data_utils import load_audit, last_report, empty_state


def render():
    theme.page_header("Reports", "Reports", "View and download incident reports.")

    d = load_audit()
    options = {}  # label -> report text

    latest = last_report()
    if latest:
        options["Latest (from Live Monitor)"] = latest

    # Agar audit log report text bhi save karta hai to purani reports bhi aa jayengi
    if not d.empty and "report" in d.columns:
        rep = d[d["report"].astype(str).str.strip().ne("") & d["report"].notna()]
        for _, r in rep.head(50).iterrows():
            label = f'{r.get("log_id", "—")} · {r.get("prediction", "—")} · {r.get("timestamp", "")}'
            options[label] = str(r["report"])

    if not options:
        return empty_state("No report yet. Run an analysis in Live Monitor "
                           "and the latest report will appear here.")

    choice = st.selectbox("Select a report", list(options))
    text = options[choice]

    with st.container(border=True):
        st.markdown(text)

    st.download_button(
        "Download report (.md)",
        text.encode("utf-8"),
        file_name="incident_report.md",
        mime="text/markdown",
    )
    if d.empty or "report" not in d.columns:
        st.caption("Older reports will appear once the audit log saves a `report` column. "
                   "For now only the latest session report is available.")