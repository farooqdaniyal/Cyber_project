import html

import pandas as pd
import plotly.express as px
import streamlit as st

import theme
from data_utils import load_audit

# General guidance. You can replace this with your RAG playbooks.
KNOWLEDGE = {
    "DDOS": ("Sending traffic from many machines at once to take a service down.",
             "Rate limiting, upstream scrubbing/CDN, and blocking attacker IP ranges."),
    "DOS HULK": ("HTTP flood: sending unique URLs to overload the web server.",
                 "WAF rules, request rate limits, and checking server capacity."),
    "DOS GOLDENEYE": ("Exhausting server resources using HTTP keep-alive and cache bypass.",
                      "Lower connection timeouts, and use a WAF and rate limiting."),
    "DOS SLOWLORIS": ("Holding half-open connections to fill up the server's connection slots.",
                      "Header/body timeouts, per-IP connection limits, and a reverse proxy."),
    "PORTSCAN": ("Probing for open ports and services (reconnaissance).",
                 "Block or monitor the source IP, and close unused ports on the firewall."),
    "BOT": ("A compromised machine that obeys commands from a C2 server.",
            "Isolate the machine, block C2 domains/IPs, and run a malware scan."),
    "HEARTBLEED": ("An OpenSSL flaw that can leak server memory (keys, passwords).",
                   "Patch OpenSSL, rotate certificates and keys, and invalidate sessions."),
    "INFILTRATION": ("Getting inside the network and trying to spread further.",
                     "Isolate the affected host, reset credentials, and check for lateral movement."),
    "WEB ATTACK": ("Web application attacks such as SQL injection and XSS.",
                   "WAF rules, input validation, and checking logs for payloads."),
    "FTP-PATATOR": ("Brute-force login attempts against FTP.",
                    "Account lockout, MFA, and blocking the source IP."),
    "SSH-PATATOR": ("Brute-force login attempts against SSH.",
                    "Key-based authentication, fail2ban, and blocking the source IP."),
    "BENIGN": ("Normal, harmless traffic.", "No action needed, logging only."),
}


def _summary_html(att, counts):
    mx = counts["Count"].max() or 1
    has_score = "risk_score" in att.columns
    has_level = "risk_level" in att.columns
    avg = att.groupby("prediction")["risk_score"].mean() if has_score else None
    lvl = (att.groupby("prediction")["risk_level"]
           .agg(lambda s: s.mode().iat[0] if not s.dropna().empty else "None")) if has_level else None
    rows, colors = [], []
    for _, r in counts.iterrows():
        name, n = r["Attack"], int(r["Count"])
        a = avg.get(name) if avg is not None else None
        level = lvl.get(name, "None") if lvl is not None else "None"
        rows.append([
            f'<span class="ftag">{html.escape(str(name))}</span>',
            f'<span class="rbar"><span class="rfill" style="width:{n / mx * 100:.0f}%;background:#4f6df5"></span></span>'
            f'<b class="mono-b">{n}</b>',
            theme.risk_bar(a, level) if a is not None and pd.notna(a) else '<span class="dim">—</span>',
            theme.level_chip(level),
        ])
        colors.append(theme.SEV_COLORS.get(str(level).lower(), "#64748b"))
    return theme.html_table(["Attack", "Events", "Avg risk", "Typical level"], rows, colors)


def render():
    theme.page_header("Threat intelligence", "Threat intelligence",
                      "Which attacks are most frequent, and how to respond to them.")
    d = load_audit()

    if not d.empty and "prediction" in d.columns:
        att = d[d["prediction"].astype(str).str.upper() != "BENIGN"]
        theme.section("Attack breakdown", "Attacks detected according to the audit log")
        if att.empty:
            st.caption("No non-benign attacks have been detected yet.")
        else:
            c1, c2 = st.columns([1.3, 1])
            counts = att["prediction"].value_counts().reset_index()
            counts.columns = ["Attack", "Count"]
            with c1:
                with st.container(border=True):
                    fig = px.bar(counts, x="Count", y="Attack", orientation="h",
                                 color_discrete_sequence=["#7ea6ff"])
                    fig.update_layout(yaxis=dict(autorange="reversed"), xaxis_title=None, yaxis_title=None)
                    st.plotly_chart(theme.plotly_layout(fig, 320), use_container_width=True)
            with c2:
                with st.container(border=True):
                    st.markdown('<div class="card-title">Attack summary</div>', unsafe_allow_html=True)
                    st.markdown(_summary_html(att, counts), unsafe_allow_html=True)
    else:
        st.caption("No audit data yet, but you can browse the knowledge base below.")

    theme.section("Attack knowledge base", "What each attack is and what to do about it")
    seen = []
    if not d.empty and "prediction" in d.columns:
        seen = [str(x) for x in d["prediction"].dropna().unique()]
    names = sorted(set(seen) | {k.title() for k in KNOWLEDGE})
    choice = st.selectbox("Select an attack", names)
    desc, action = KNOWLEDGE.get(choice.upper(), ("No description is available for this attack yet.",
                                                    "Check the RAG playbook or contact an analyst."))
    a, b = st.columns(2)
    a.markdown(f'<div class="panel"><h3>📖 What it is</h3><div class="panel-body">{desc}</div></div>',
               unsafe_allow_html=True)
    b.markdown(f'<div class="panel"><h3>🛠️ Recommended response</h3><div class="panel-body">{action}</div></div>',
               unsafe_allow_html=True)
