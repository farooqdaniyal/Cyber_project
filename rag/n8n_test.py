# Send final analysis result to n8n

import os
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")

n8n_data = {
    "attack": pred,
    "confidence": conf,
    "risk_score": risk_score,
    "risk_level": risk_level,
    "target": asset,
    "incident_id": incident_id,
    "verification_status": ver,
    "outcome": outcome,
    "audit_log_id": result.get("audit_log_id"),
}

try:
    response = requests.post(
        N8N_WEBHOOK_URL,
        json=n8n_data,
        timeout=10
    )

    if response.status_code == 200:
        st.success("✅ Result automatically saved to n8n / Google Sheets")
    else:
        st.warning(f"⚠️ n8n error: {response.status_code} - {response.text}")

except Exception as e:
    st.warning(f"⚠️ Could not send result to n8n: {e}")