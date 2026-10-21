import html

import pandas as pd
import plotly.express as px
import streamlit as st

import theme
from data_utils import load_audit

# Aam (general) guidance. Aap apne RAG playbooks se iski jagah le sakte hain.
KNOWLEDGE = {
    "DDOS": ("Bohat saari machines se ek saath traffic bhej kar service ko down karna.",
             "Rate limiting, upstream scrubbing/CDN, attacker IP ranges block karna."),
    "DOS HULK": ("HTTP flood: unique URLs bhej kar web server ko overload karna.",
                 "WAF rules, request rate limits, server capacity check karna."),
    "DOS GOLDENEYE": ("HTTP keep-alive/cache bypass se server resources khatam karna.",
                      "Connection timeouts kam karein, WAF aur rate limiting lagayein."),
    "DOS SLOWLORIS": ("Aadhe adhoore connections khule rakh kar server ke slots bhar dena.",
                      "Header/body timeouts, per-IP connection limits, reverse proxy."),
    "PORTSCAN": ("Khule ports aur services dhoondne ki koshish (reconnaissance).",
                 "Source IP block/monitor karein, firewall se unused ports band karein."),
    "BOT": ("Compromised machine jo C2 server ke hukm par chalti hai.",
            "Machine isolate karein, C2 domains/IPs block karein, malware scan chalayein."),
    "HEARTBLEED": ("OpenSSL ki khami jis se server memory (keys, passwords) leak ho sakti hai.",
                   "OpenSSL patch karein, certificates aur keys badlein, sessions invalidate karein."),
    "INFILTRATION": ("Network ke andar ghus kar aage phailne ki koshish.",
                     "Affected host isolate karein, credentials reset karein, lateral movement check karein."),
    "WEB ATTACK": ("SQL injection / XSS jaise web application hamlay.",
                   "WAF rules, input validation, logs mein payloads check karein."),
    "FTP-PATATOR": ("FTP par brute-force login attempts.",
                    "Account lockout, MFA, source IP block karein."),
    "SSH-PATATOR": ("SSH par brute-force login attempts.",
                    "Key-based auth, fail2ban, source IP block karein."),
    "BENIGN": ("Normal, bina khatre wala traffic.", "Koi action nahi, sirf logging."),
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

    theme.section("Attack knowledge base", "Har attack kya hai aur kya karna chahiye")
    seen = []
    if not d.empty and "prediction" in d.columns:
        seen = [str(x) for x in d["prediction"].dropna().unique()]
    names = sorted(set(seen) | {k.title() for k in KNOWLEDGE})
    choice = st.selectbox("Attack chunein", names)
    desc, action = KNOWLEDGE.get(choice.upper(), ("Is attack ke liye abhi description nahi hai.",
                                                    "RAG playbook / analyst se rabta karein."))
    a, b = st.columns(2)
    a.markdown(f'<div class="panel"><h3>📖 Yeh kya hai</h3><div class="panel-body">{desc}</div></div>',
               unsafe_allow_html=True)
    b.markdown(f'<div class="panel"><h3>🛠️ Recommended response</h3><div class="panel-body">{action}</div></div>',
               unsafe_allow_html=True)