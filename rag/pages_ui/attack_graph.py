import plotly.graph_objects as go
import streamlit as st

import theme
from data_utils import load_audit, empty_state

LAYER_COLORS = ["#fb7185", "#fbbf24", "#22d3ee"]
LAYER_NAMES = ["Attack family", "Asset", "Incident"]


def _positions(nodes):
    n = len(nodes)
    return {name: 1 - (i + 0.5) / max(n, 1) for i, name in enumerate(nodes)}


def render():
    theme.page_header("Attack graph", "Attack graph",
                      "How attack families, assets and incidents are connected.")
    d = load_audit()
    need = {"prediction", "asset", "incident_id"}
    if d.empty or not need.issubset(d.columns):
        return empty_state()

    d = d[d["prediction"].astype(str).str.upper() != "BENIGN"]
    d = d[d["incident_id"].notna() & (d["incident_id"].astype(str) != "—")]
    if d.empty:
        return empty_state("No attack or incident data for the graph yet (only BENIGN runs so far).")

    if "ts" in d.columns:
        d = d.sort_values("ts")
    last_inc = list(dict.fromkeys(d["incident_id"].astype(str)))[-12:]
    d = d[d["incident_id"].astype(str).isin(last_inc)]

    fams = sorted(d["prediction"].astype(str).unique())
    assets = sorted(d["asset"].astype(str).unique())
    incs = last_inc
    layers = [fams, assets, incs]
    pos = [_positions(L) for L in layers]

    def xy(layer, name):
        return layer, pos[layer][name]

    edges = set()
    for _, r in d.iterrows():
        f, a, i = str(r["prediction"]), str(r["asset"]), str(r["incident_id"])
        edges.add(((0, f), (1, a)))
        edges.add(((1, a), (2, i)))

    ex, ey = [], []
    for (l1, n1), (l2, n2) in edges:
        x1, y1 = xy(l1, n1)
        x2, y2 = xy(l2, n2)
        ex += [x1, x2, None]
        ey += [y1, y2, None]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ex, y=ey, mode="lines", hoverinfo="skip",
                             line=dict(color="rgba(79,109,245,.35)", width=1.5), showlegend=False))
    for li, L in enumerate(layers):
        fig.add_trace(go.Scatter(
            x=[li] * len(L), y=[pos[li][n] for n in L], mode="markers+text",
            text=L, textposition="middle right" if li < 2 else "middle left",
            marker=dict(size=22, color=LAYER_COLORS[li], line=dict(color="#050a1f", width=2)),
            name=LAYER_NAMES[li], hoverinfo="text",
        ))
    fig.update_xaxes(visible=False, range=[-0.5, 2.5])
    fig.update_yaxes(visible=False, range=[-0.05, 1.05])
    theme.plotly_layout(fig, 520)
    fig.update_layout(legend=dict(orientation="h", y=1.05, x=0.5, xanchor="center"))

    with st.container(border=True):
        st.plotly_chart(fig, use_container_width=True)
    st.caption(f"Latest {len(incs)} incidents shown.")