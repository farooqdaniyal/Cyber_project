# ============================================================
# RESPONSE AGENT
# Takes the Verification Agent's result and decides the final
# outcome: an automated action recommendation, or a human
# escalation alert. Does NOT execute real commands - it only
# RECOMMENDS actions in text/report form (safe, no real
# infrastructure risk).
#
# Place this file in your "rag" folder alongside
# investigation_agent.py and verification_agent.py
# ============================================================

import os
from dotenv import load_dotenv
load_dotenv()

# from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate

# Import the agents we already built
from investigation_agent import investigation_agent
from verification_agent import verification_agent

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(SCRIPT_DIR, "chroma_security_db")

# ---------- STEP A: Reuse the RAG Retriever (for exact action steps) ----------
# embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
vector_store = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)
retriever = vector_store.as_retriever(search_kwargs={"k": 2})

# ---------- STEP B: Set Up the LLM ----------
llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0.2)

# ---------- STEP C: Prompt for Automated Action Recommendation ----------
action_prompt = ChatPromptTemplate.from_template("""
You are a Response Agent in a cybersecurity system. An attack has been
VERIFIED and approved for automated response.

Attack Type: {prediction}
Confidence: {confidence}

Relevant Playbook (from company policy):
{policy_context}

Write a short, numbered ACTION PLAN (3-5 steps) in plain language,
based on the playbook above, as a RECOMMENDATION for the automation
system to execute. Do not include a long explanation - just the
action steps, clearly numbered.
""")

# ---------- STEP D: Prompt for Human Escalation Alert ----------
escalation_prompt = ChatPromptTemplate.from_template("""
You are a Response Agent in a cybersecurity system. A detection needs
HUMAN REVIEW before any action is taken (per policy).

Attack Type: {prediction}
Confidence: {confidence}
Reason for Escalation: {reason}

Write a short, urgent alert message (3-4 sentences) that would be sent
to the on-call security analyst, telling them what was detected and
why their review is needed before action is taken.
""")

# ---------- STEP E: Helper to Extract Clean Text ----------
def extract_text(response_content):
    if isinstance(response_content, str):
        return response_content
    elif isinstance(response_content, list):
        parts = [b.get("text", "") for b in response_content if isinstance(b, dict)]
        return "\n".join(parts)
    return str(response_content)

# ---------- STEP F: THE RESPONSE AGENT FUNCTION ----------

def response_agent(verification_result: dict):
    """
    THE RESPONSE AGENT.

    Input: the dictionary returned by verification_agent()
           (contains 'prediction', 'confidence', 'verification_status').

    What it does:
    - If BENIGN: returns a simple "no action" log message (no LLM call
      needed - saves time and API usage for the most common case).
    - If VERIFIED (and not BENIGN): retrieves the exact playbook steps
      and asks the LLM to produce a short automated action plan.
    - If NEEDS_HUMAN_REVIEW: asks the LLM to write an escalation alert
      for a human analyst instead of taking action.

    Output: a dictionary with the final outcome type and message.
    """
    prediction = verification_result["prediction"]
    confidence = verification_result["confidence"]
    status = verification_result["verification_status"]

    # --- Case 1: BENIGN - no LLM call needed, just log ---
    if prediction == "BENIGN":
        return {
            "outcome": "LOGGED",
            "message": "Normal traffic. Logged for routine audit. No action taken."
        }

    # --- Case 2: VERIFIED - produce automated action plan ---
    if status == "VERIFIED":
        detection_text = f"{prediction} ATTACK detected in network traffic"
        retrieved_docs = retriever.invoke(detection_text)
        policy_context = "\n\n".join([doc.page_content for doc in retrieved_docs])

        final_prompt = action_prompt.format(
            prediction=prediction,
            confidence=f"{confidence:.2%}",
            policy_context=policy_context
        )
        response = llm.invoke(final_prompt)
        action_plan = extract_text(response.content)

        return {
            "outcome": "AUTOMATED_ACTION_RECOMMENDED",
            "message": action_plan
        }

    # --- Case 3: NEEDS_HUMAN_REVIEW - produce escalation alert ---
    final_prompt = escalation_prompt.format(
        prediction=prediction,
        confidence=f"{confidence:.2%}",
        reason=verification_result["rule_decision"]
    )
    response = llm.invoke(final_prompt)
    alert_message = extract_text(response.content)

    return {
        "outcome": "ESCALATED_TO_HUMAN",
        "message": alert_message
    }

# ---------- STEP G: TEST THE RESPONSE AGENT ----------

if __name__ == "__main__":
    import pandas as pd

    DATA_PATH = os.path.join(SCRIPT_DIR, "sample_test_data.csv")
    df = pd.read_csv(DATA_PATH)

    print("\n" + "=" * 60)
    print("TESTING RESPONSE AGENT (FULL PIPELINE)")
    print("=" * 60)

    # --- Test 1: BENIGN (should just log, no LLM call) ---
    benign_row = df[df['Label'] == 'BENIGN'].drop(columns=['Label']).iloc[[0]]
    inv_1 = investigation_agent(benign_row)
    ver_1 = verification_agent(inv_1)
    resp_1 = response_agent(ver_1)

    print("\n--- TEST 1: BENIGN ---")
    print(f"Outcome: {resp_1['outcome']}")
    print(f"Message: {resp_1['message']}")

    # --- Test 2: DDoS (should escalate to human, per policy) ---
    ddos_row = df[df['Label'] == 'DDoS'].drop(columns=['Label']).iloc[[0]]
    inv_2 = investigation_agent(ddos_row)
    ver_2 = verification_agent(inv_2)
    resp_2 = response_agent(ver_2)

    print("\n--- TEST 2: DDoS ---")
    print(f"Outcome: {resp_2['outcome']}")
    print(f"Message: {resp_2['message']}")

    # --- Test 3: DoS Hulk (should be VERIFIED if confidence high - automated action) ---
    hulk_row = df[df['Label'] == 'DoS Hulk'].drop(columns=['Label']).iloc[[0]]
    inv_3 = investigation_agent(hulk_row)
    ver_3 = verification_agent(inv_3)
    resp_3 = response_agent(ver_3)

    print("\n--- TEST 3: DoS Hulk ---")
    print(f"Outcome: {resp_3['outcome']}")
    print(f"Message: {resp_3['message']}")

    print("\n" + "=" * 60)
    print("RESPONSE AGENT TEST COMPLETE!")
    print("Full pipeline tested: ML -> RAG -> Investigation -> Verification -> Response")
    print("=" * 60)