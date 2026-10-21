# ============================================================
# INVESTIGATION AGENT (FINAL)
# - Predicts attack + confidence (ML)
# - Fetches the EXACT playbook using metadata filter
# - Final report is generated AFTER verification (final_report_agent)
# ============================================================

import os
import joblib
import pandas as pd
import numpy as np
from dotenv import load_dotenv
load_dotenv()

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(SCRIPT_DIR, "chroma_security_db")

# ---------- Load ML artifacts ----------
ML_MODEL_PATH = os.path.join(SCRIPT_DIR, "..", "ml_models", "cyber_multiclass_model.pkl")
SCALER_PATH = os.path.join(SCRIPT_DIR, "..", "ml_models", "cyber_multiclass_scaler.pkl")
ENCODER_PATH = os.path.join(SCRIPT_DIR, "..", "ml_models", "cyber_multiclass_label_encoder.pkl")

print("Loading ML model, scaler, and label encoder...")
ml_model = joblib.load(ML_MODEL_PATH)
scaler = joblib.load(SCALER_PATH)
label_encoder = joblib.load(ENCODER_PATH)
print("ML artifacts loaded successfully.")

# ---------- Load RAG ----------
print("Loading existing ChromaDB...")
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vector_store = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)
retriever = vector_store.as_retriever(search_kwargs={"k": 2})
print("ChromaDB loaded successfully.")

# ---------- LLM ----------
llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0.3)
print("LLM ready (using Groq).")

# ---------- Helper ----------
def extract_text(response_content):
    if isinstance(response_content, str):
        return response_content
    elif isinstance(response_content, list):
        text_parts = []
        for block in response_content:
            if isinstance(block, dict) and block.get("type") == "text":
                text_parts.append(block.get("text", ""))
            elif isinstance(block, str):
                text_parts.append(block)
        return "\n".join(text_parts)
    return str(response_content)

# ---------- Exact playbook lookup ----------
PLAYBOOK_ID = {
    "DoS Hulk": "01",
    "DoS GoldenEye": "01b",
    "DDoS": "02",
    "DoS slowloris": "03",
    "DoS Slowhttptest": "03",
    "Heartbleed": "04",
    "PortScan": "05",
    "BENIGN": "06",
}

def get_playbook(prediction: str) -> str:
    """Return the exact playbook text for the predicted class."""
    pid = PLAYBOOK_ID.get(prediction)
    if pid:
        r = vector_store.as_retriever(
            search_kwargs={"k": 1, "filter": {"playbook_id": pid}}
        )
    else:
        r = retriever  # unknown class -> fallback to semantic search
    query = f"{prediction} ATTACK detected in network traffic"
    return "\n\n".join(d.page_content for d in r.invoke(query))

# ---------- THE INVESTIGATION AGENT ----------
def investigation_agent(network_data_row: pd.DataFrame):
    """
    Input: one row of network traffic (78 numeric features).
    Output: prediction + confidence. The report is generated later,
    AFTER verification, by final_report_agent().
    """
    numeric_data = network_data_row.select_dtypes(include=[np.number])
    scaled_data = scaler.transform(numeric_data)

    prediction_encoded = ml_model.predict(scaled_data)
    prediction_label = label_encoder.inverse_transform(prediction_encoded)[0]

    probabilities = ml_model.predict_proba(scaled_data)[0]
    confidence = float(np.max(probabilities))

    print(f"\n[Investigation Agent] ML Prediction: {prediction_label} (confidence: {confidence:.2%})")

    return {
        "prediction": prediction_label,
        "confidence": confidence,
        "report": ""   # filled later by final_report_agent
    }

# ---------- FINAL REPORT (runs AFTER verification) ----------
final_prompt_tmpl = ChatPromptTemplate.from_template("""
You are a Cyber Security Analyst AI. Write the FINAL incident report.

IMPORTANT EVIDENCE RULES:
- Use only the facts listed below and the retrieved playbook.
- The playbook's technical indicators are TYPICAL reference thresholds
  for this attack type, NOT confirmed measurements of this incident.
- Never claim that specific socket counts, traffic rates, connection
  durations, IP addresses, or server software (Nginx/Apache) were
  observed. Never invent time deadlines.
- No action has been executed. All response steps are RECOMMENDATIONS
  awaiting execution or approval. Never say an action "was executed"
  or "was applied".
- Clearly separate confirmed facts from recommended checks.

Detection: {prediction} (model confidence {confidence})
Risk: {risk_score}/100 ({risk_level}) on asset: {asset}
Verification decision: {verification_status}
Rule applied: {rule_decision}

Relevant Playbook:
{policy_context}

Sections:
1. Incident Overview (only confirmed facts above)
2. Severity Assessment (must match the risk level above)
3. Decision (state clearly: automated action recommended OR human review required, and why)
4. Typical Indicators to Check (from the playbook, labelled as typical)
5. Recommended Response Steps (from the playbook)
6. Escalation Note
Keep it short for a non-technical manager.
""")

def final_report_agent(d: dict) -> str:
    msg = final_prompt_tmpl.format(
        prediction=d["prediction"],
        confidence=f"{d['confidence']:.2%}",
        risk_score=d["risk_score"],
        risk_level=d["risk_level"],
        asset=d["asset"],
        verification_status=d["verification_status"],
        rule_decision=d["rule_decision"],
        policy_context=get_playbook(d["prediction"]),
    )
    return extract_text(llm.invoke(msg).content)

# ---------- QUICK TEST ----------
if __name__ == "__main__":
    DATA_PATH = os.path.join(SCRIPT_DIR, "sample_test_data.csv")
    df = pd.read_csv(DATA_PATH)

    row = df[df["Label"] == "DoS Slowhttptest"].drop(columns=["Label"]).iloc[[0]]
    res = investigation_agent(row)
    print("Prediction:", res["prediction"], "| Confidence:", f"{res['confidence']:.2%}")

    print("\n--- Playbook fetched for this prediction ---")
    print(get_playbook(res["prediction"])[:300])