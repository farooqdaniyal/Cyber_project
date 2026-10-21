# ============================================================
# RAG UTILS
# Small shared helpers used by:
#   - rebuild_playbook_db.py  (builds the vector DB)
#   - investigation_agent.py  (retrieves the right playbook)
#
# Keeping the embedding model name here means the DB builder and
# the agents can never accidentally use different embedding models.
# ============================================================

import re

# One embedding model for BOTH building and querying the DB.
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# The ML model predicts one of 7 classes. Each class has exactly one
# matching playbook in security_policy.txt (Slowloris and Slowhttptest
# share playbook 03).
CLASS_TO_PLAYBOOK_ID = {
    "DoS Hulk": "01",
    "DoS GoldenEye": "01b",
    "DDoS": "02",
    "DoS slowloris": "03",
    "DoS Slowhttptest": "03",
    "Heartbleed": "04",
    "BENIGN": "06",
}

# Real values measured from the traffic record that we show as
# "observed evidence" in the final report.
KEY_FEATURE_COLS = [
    "Destination Port",
    "Flow Duration",
    "Total Fwd Packets",
    "Total Backward Packets",
    "Total Length of Fwd Packets",
    "Total Length of Bwd Packets",
    "Flow Bytes/s",
    "Flow Packets/s",
]

# CICFlowMeter reports Flow Duration in microseconds.
FEATURE_DISPLAY_NAMES = {
    "Flow Duration": "Flow Duration (microseconds)",
}


def parse_playbooks(text: str) -> list:
    """
    Split security_policy.txt into ONE entry per playbook.

    Each playbook in the file looks like:
        ------------------------------------------------------------
        PLAYBOOK 03: DoS Slowloris / Slowhttptest
        ------------------------------------------------------------
        ...body...

    Returns a list of dicts: {"playbook_id", "title", "content"}.
    """
    parts = re.split(r"(?m)^-{20,}\n(?=PLAYBOOK )", text)
    playbooks = []
    for part in parts:
        part = part.strip()
        m = re.match(r"PLAYBOOK\s+(\w+):\s*(.+)", part)
        if not m:
            continue  # the document header / anything that is not a playbook
        playbooks.append({
            "playbook_id": m.group(1),
            "title": m.group(2).strip(),
            "content": part,
        })
    return playbooks


def extract_key_features(network_row) -> dict:
    """
    Pull a few real, measured values from the single-row DataFrame
    so the report can cite evidence that actually exists in the input.
    """
    features = {}
    for col in KEY_FEATURE_COLS:
        if col in network_row.columns:
            try:
                value = float(network_row[col].iloc[0])
            except (TypeError, ValueError):
                continue
            features[FEATURE_DISPLAY_NAMES.get(col, col)] = round(value, 2)
    return features