# ============================================================
# VERIFICATION AGENT (with Risk Level check)
# Takes the Investigation Agent's result (prediction + confidence)
# AND the Risk Engine's risk_level, and decides: is this verified
# enough for automated action, or does it need human review?
#
# Place this file in your "rag" folder alongside investigation_agent.py
# ============================================================

import os
from dotenv import load_dotenv
load_dotenv()

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

# Import the Investigation Agent we already built
from investigation_agent import investigation_agent

# ---------- STEP A: Set Up the LLM (reuse Groq) ----------
llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0.2)

# ---------- STEP B: Define Verification Rules ----------

# Confidence threshold: below this, we don't fully trust the ML
# model's prediction without a human double-checking it.
CONFIDENCE_THRESHOLD = 0.90

# Some attack types are so severe (per our security policy) that
# they ALWAYS require human review before any automated action,
# no matter how confident the model is. This matches the
# [DECISION MATRIX FOR AGENTS] rules in security_policy.txt.
ALWAYS_ESCALATE_TYPES = ["Heartbleed", "DDoS"]

# Risk levels that ALWAYS require human review, regardless of the
# attack type or confidence. This closes the gap where a normally
# "automatable" attack (e.g. DoS Hulk) becomes very dangerous
# because of WHICH asset it hit (e.g. a Database Server).
ALWAYS_ESCALATE_RISK_LEVELS = ["Critical"]

# ---------- STEP C: Verification Prompt ----------
verification_prompt = ChatPromptTemplate.from_template("""
You are a Verification Agent in a cybersecurity system. Your job is to
double-check a detection result before any action is taken, to avoid
false alarms.

Detection: {prediction}
Model Confidence: {confidence}
Risk Level: {risk_level}
Rule-Based Decision: {rule_decision}

In 2-3 short sentences, explain to a security analyst WHY this
detection is either safe to act on automatically, or why it needs
human review, based on the confidence score, detection type, and
risk level. Be concise and factual, not dramatic.
""")

# ---------- STEP D: THE VERIFICATION AGENT FUNCTION ----------

def verification_agent(investigation_result: dict):
    """
    Input dict can contain:
      - prediction (str)
      - confidence (float)
      - risk_level (str, optional - e.g. "Low"/"Medium"/"High"/"Critical")
    """
    prediction = investigation_result.get("prediction", "UNKNOWN")
    confidence = investigation_result.get("confidence", 0.0)
    risk_level = investigation_result.get("risk_level", "Unknown")

    pred_clean = str(prediction).strip().upper()
    risk_clean = str(risk_level).strip().upper()
    always_escalate_clean = [t.upper() for t in ALWAYS_ESCALATE_TYPES]
    always_escalate_risk_clean = [r.upper() for r in ALWAYS_ESCALATE_RISK_LEVELS]

    # --- Rule Logic (checked in priority order) ---
    if pred_clean == "BENIGN":
        rule_decision = "NO ACTION NEEDED - NORMAL TRAFFIC"
        status = "VERIFIED"
    elif pred_clean in always_escalate_clean:
        rule_decision = "MANDATORY HUMAN ESCALATION (high-severity attack type)"
        status = "NEEDS_HUMAN_REVIEW"
    elif risk_clean in always_escalate_risk_clean:
        rule_decision = f"MANDATORY HUMAN ESCALATION (risk level is {risk_level})"
        status = "NEEDS_HUMAN_REVIEW"
    elif confidence >= CONFIDENCE_THRESHOLD:
        rule_decision = "AUTOMATED ACTION APPROVED (high confidence)"
        status = "VERIFIED"
    else:
        rule_decision = "HUMAN REVIEW REQUIRED (confidence below threshold)"
        status = "NEEDS_HUMAN_REVIEW"

    # --- LLM Explanation with Error Handling ---
    try:
        final_prompt = verification_prompt.format(
            prediction=prediction,
            confidence=f"{confidence:.2%}",
            risk_level=risk_level,
            rule_decision=rule_decision
        )
        response = llm.invoke(final_prompt)

        if isinstance(response.content, str):
            explanation = response.content
        elif isinstance(response.content, list):
            explanation = "\n".join([b.get("text", "") for b in response.content if isinstance(b, dict)])
        else:
            explanation = str(response.content)
    except Exception as e:
        explanation = f"LLM explanation unavailable due to an error ({str(e)}). Rule decision applied: {rule_decision}."

    return {
        "prediction": prediction,
        "confidence": confidence,
        "risk_level": risk_level,
        "verification_status": status,
        "rule_decision": rule_decision,
        "explanation": explanation
    }

# ---------- STEP E: TEST THE VERIFICATION AGENT ----------

if __name__ == "__main__":
    import pandas as pd

    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_PATH = os.path.join(SCRIPT_DIR, "sample_test_data.csv")
    df = pd.read_csv(DATA_PATH)

    print("\n" + "=" * 60)
    print("TESTING VERIFICATION AGENT (WITH RISK LEVEL)")
    print("=" * 60)

    # --- Test 1: BENIGN (should be auto-verified, no escalation) ---
    benign_row = df[df['Label'] == 'BENIGN'].drop(columns=['Label']).iloc[[0]]
    inv_1 = investigation_agent(benign_row)
    inv_1["risk_level"] = "None"
    ver_1 = verification_agent(inv_1)
    print("\n--- TEST 1: BENIGN (risk=None) ---")
    print(f"Status: {ver_1['verification_status']} | Rule: {ver_1['rule_decision']}")

    # --- Test 2: DoS Hulk with Medium risk (should be auto-verified) ---
    hulk_row = df[df['Label'] == 'DoS Hulk'].drop(columns=['Label']).iloc[[0]]
    inv_2 = investigation_agent(hulk_row)
    inv_2["risk_level"] = "Medium"
    ver_2 = verification_agent(inv_2)
    print("\n--- TEST 2: DoS Hulk (risk=Medium) ---")
    print(f"Status: {ver_2['verification_status']} | Rule: {ver_2['rule_decision']}")

    # --- Test 3: DoS Hulk with CRITICAL risk (should NOW escalate, even though Hulk is not in ALWAYS_ESCALATE_TYPES) ---
    inv_3 = investigation_agent(hulk_row)
    inv_3["risk_level"] = "Critical"
    ver_3 = verification_agent(inv_3)
    print("\n--- TEST 3: DoS Hulk (risk=Critical, e.g. hit a Database Server) ---")
    print(f"Status: {ver_3['verification_status']} | Rule: {ver_3['rule_decision']}")
    print(f"Explanation: {ver_3['explanation']}")

    print("\n" + "=" * 60)
    print("VERIFICATION AGENT TEST COMPLETE!")
    print("=" * 60)