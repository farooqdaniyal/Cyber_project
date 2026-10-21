# ============================================================
# LANGGRAPH WORKFLOW (with Risk Scoring + Incident Correlation + Audit Log)
# Investigation -> Risk Scoring -> Incident Correlation -> Verification
#   -> Final Report -> (conditional routing)
#   -> Automated Action OR Human Escalation -> Audit Log -> END
#
# The final report is generated AFTER verification, so it always
# matches the rule decision and the risk level.
# ============================================================

import os
import pandas as pd
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

from investigation_agent import investigation_agent, final_report_agent
from verification_agent import verification_agent
from response_agent import response_agent
from risk_engine import calculate_risk, DEFAULT_ASSET
from incident_correlation import CORRELATOR
from audit_log import AUDIT_LOGGER

# ---------- STEP A: Define the State ----------
 
class PipelineState(TypedDict):
    network_data: pd.DataFrame
    asset: Optional[str]
    prediction: Optional[str]
    confidence: Optional[float]
    report: Optional[str]               # filled by the Report node (after verification)
    risk_score: Optional[float]
    risk_level: Optional[str]
    risk_breakdown: Optional[dict]
    # --- Incident Correlation node ---
    incident_id: Optional[str]
    incident_created: Optional[bool]
    incident_merged: Optional[bool]
    incident_family: Optional[str]
    incident_alert_count: Optional[int]
    incident_max_risk_score: Optional[float]
    incident_max_risk_level: Optional[str]
    incident_primary_prediction: Optional[str]
    incident_status: Optional[str]
    incident_alert_ids: Optional[list]
    # --- Verification node ---
    verification_status: Optional[str]
    rule_decision: Optional[str]
    explanation: Optional[str]
    # --- Response node ---
    outcome: Optional[str]
    message: Optional[str]
    # --- Audit Log node ---
    audit_log_id: Optional[int]

# ---------- STEP B: Nodes ----------

def investigation_node(state: PipelineState) -> dict:
    print("\n[NODE] Investigation Agent running...")
    result = investigation_agent(state["network_data"])
    return {
        "prediction": result["prediction"],
        "confidence": result["confidence"],
        "report": result["report"],   # empty for now, real report comes later
    }

def risk_scoring_node(state: PipelineState) -> dict:
    print("[NODE] Risk Scoring Engine running...")
    asset = state.get("asset") or DEFAULT_ASSET
    risk = calculate_risk(state["prediction"], state["confidence"], asset)
    print(f"[Risk Engine] {risk['risk_score']} / 100 -> {risk['risk_level']} (asset: {asset})")
    return {
        "asset": asset,
        "risk_score": risk["risk_score"],
        "risk_level": risk["risk_level"],
        "risk_breakdown": risk["risk_breakdown"],
    }

def incident_correlation_node(state: PipelineState) -> dict:
    print("[NODE] Incident Correlation running...")
    result = CORRELATOR.ingest({
        "prediction": state["prediction"],
        "confidence": state["confidence"],
        "risk_score": state["risk_score"],
        "risk_level": state["risk_level"],
        "asset": state["asset"],
        "report": state.get("report"),
    })
    action = "NEW" if result["incident_created"] else "MERGED"
    print(f"[Incident Correlator] {result['incident_id']} ({action}) "
          f"- {result['incident_alert_count']} alert(s), "
          f"status={result['incident_status']}")
    return {
        "incident_id": result["incident_id"],
        "incident_created": result["incident_created"],
        "incident_merged": result["incident_merged"],
        "incident_family": result["incident_family"],
        "incident_alert_count": result["incident_alert_count"],
        "incident_max_risk_score": result["incident_max_risk_score"],
        "incident_max_risk_level": result["incident_max_risk_level"],
        "incident_primary_prediction": result["incident_primary_prediction"],
        "incident_status": result["incident_status"],
        "incident_alert_ids": result["alert_ids"],
    }

def verification_node(state: PipelineState) -> dict:
    print("[NODE] Verification Agent running...")
    result = verification_agent({
        "prediction": state["prediction"],
        "confidence": state["confidence"],
        "risk_level": state["risk_level"],
    })

    # Repeated alerts in the same incident -> force human escalation
    if state.get("incident_alert_count", 0) >= 3 and result["verification_status"] != "NEEDS_HUMAN_REVIEW":
        result["verification_status"] = "NEEDS_HUMAN_REVIEW"
        result["rule_decision"] = "MANDATORY HUMAN ESCALATION (repeated alerts in same incident)"
        result["explanation"] += " | Auto-escalated: this incident has multiple repeated alerts."

    return {
        "verification_status": result["verification_status"],
        "rule_decision": result["rule_decision"],
        "explanation": result["explanation"],
    }

def report_node(state: PipelineState) -> dict:
    """NEW: final report is written AFTER verification, so it matches the decision."""
    print("[NODE] Final Report running...")
    report = final_report_agent({
        "prediction": state["prediction"],
        "confidence": state["confidence"],
        "risk_score": state["risk_score"],
        "risk_level": state["risk_level"],
        "asset": state["asset"],
        "verification_status": state["verification_status"],
        "rule_decision": state["rule_decision"],
    })
    return {"report": report}

def automated_action_node(state: PipelineState) -> dict:
    print("[NODE] Response Agent (Automated Action Path) running...")
    result = response_agent({
        "prediction": state["prediction"],
        "confidence": state["confidence"],
        "verification_status": state["verification_status"],
        "rule_decision": state["rule_decision"],
    })
    return {"outcome": result["outcome"], "message": result["message"]}

def escalation_node(state: PipelineState) -> dict:
    print("[NODE] Response Agent (Human Escalation Path) running...")
    result = response_agent({
        "prediction": state["prediction"],
        "confidence": state["confidence"],
        "verification_status": state["verification_status"],
        "rule_decision": state["rule_decision"],
    })
    return {"outcome": result["outcome"], "message": result["message"]}

def audit_log_node(state: PipelineState) -> dict:
    print("[NODE] Audit Log running...")
    log_id = AUDIT_LOGGER.log({
        "prediction": state.get("prediction"),
        "confidence": state.get("confidence"),
        "asset": state.get("asset"),
        "risk_score": state.get("risk_score"),
        "risk_level": state.get("risk_level"),
        "incident_id": state.get("incident_id"),
        "incident_status": state.get("incident_status"),
        "incident_alert_count": state.get("incident_alert_count"),
        "incident_created": state.get("incident_created"),
        "incident_merged": state.get("incident_merged"),
        "verification_status": state.get("verification_status"),
        "rule_decision": state.get("rule_decision"),
        "outcome": state.get("outcome"),
        "message": state.get("message"),
    })
    print(f"[Audit Log] Saved as record #{log_id}")
    return {"audit_log_id": log_id}

# ---------- STEP C: Conditional Router ----------

def route_after_verification(state: PipelineState) -> str:
    if state["verification_status"] == "VERIFIED":
        return "automated_action"
    return "escalation"

# ---------- STEP D: Build the Graph ----------

graph = StateGraph(PipelineState)

graph.add_node("investigation", investigation_node)
graph.add_node("risk_scoring", risk_scoring_node)
graph.add_node("incident_correlation", incident_correlation_node)
graph.add_node("verification", verification_node)
graph.add_node("report", report_node)                      # NEW
graph.add_node("automated_action", automated_action_node)
graph.add_node("escalation", escalation_node)
graph.add_node("audit_log", audit_log_node)

graph.set_entry_point("investigation")

# Fixed edges
graph.add_edge("investigation", "risk_scoring")
graph.add_edge("risk_scoring", "incident_correlation")
graph.add_edge("incident_correlation", "verification")
graph.add_edge("verification", "report")                   # NEW

# Conditional edge now starts from "report"
graph.add_conditional_edges(
    "report",
    route_after_verification,
    {
        "automated_action": "automated_action",
        "escalation": "escalation",
    },
)

graph.add_edge("automated_action", "audit_log")
graph.add_edge("escalation", "audit_log")
graph.add_edge("audit_log", END)

app = graph.compile()

# ---------- STEP E: TEST THE FULL PIPELINE ----------

if __name__ == "__main__":
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_PATH = os.path.join(SCRIPT_DIR, "sample_test_data.csv")
    df = pd.read_csv(DATA_PATH)

    print("\n" + "=" * 60)
    print("TESTING FULL LANGGRAPH PIPELINE")
    print("=" * 60)

    def run_case(label, asset):
        row = df[df['Label'] == label].drop(columns=['Label']).iloc[[0]]
        state = app.invoke({"network_data": row, "asset": asset})
        print(f"\n--- FINAL RESULT: {label} on {asset} ---")
        print(f"Prediction:   {state['prediction']} ({state['confidence']:.2%})")
        print(f"Risk:         {state['risk_score']} / 100 -> {state['risk_level']}")
        print(f"Incident:     {state['incident_id']} "
              f"({'NEW' if state['incident_created'] else 'MERGED'}, "
              f"{state['incident_alert_count']} alert(s), status={state['incident_status']})")
        print(f"Verification: {state['verification_status']}")
        print(f"Outcome:      {state['outcome']}")
        print(f"Audit Log:    record #{state['audit_log_id']}")
        print("Report preview:", (state.get("report") or "")[:300].replace("\n", " "))

    run_case("DoS Slowhttptest", "Database Server")
    run_case("BENIGN", "Web Server")

    print("\n" + "=" * 60)
    print("PIPELINE TEST COMPLETE!")
    print("=" * 60)