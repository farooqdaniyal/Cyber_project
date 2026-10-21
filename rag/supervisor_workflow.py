# ============================================================
# SUPERVISOR WORKFLOW (hub-and-spoke)
# Supervisor reads the state and decides the NEXT agent.
# Every worker returns to the supervisor. Includes a quality loop:
# if the report contradicts risk/decision, supervisor re-runs report once.
# Existing langgraph_workflow.py is NOT modified.
# ============================================================

import os
import pandas as pd
from typing import Optional
from langgraph.graph import StateGraph, END

from langgraph_workflow import (
    PipelineState,
    investigation_node, risk_scoring_node, incident_correlation_node,
    verification_node, report_node, automated_action_node,
    escalation_node, audit_log_node,
)

MAX_STEPS = 14          # safety limit against infinite loops
MAX_REPORT_RETRIES = 1


class SupervisorState(PipelineState):
    next_agent: Optional[str]
    step_count: Optional[int]
    report_retries: Optional[int]
    supervisor_log: Optional[list]


# ---------- Quality check used by the supervisor ----------
def report_is_consistent(state: dict) -> bool:
    report = (state.get("report") or "").lower()
    if not report:
        return False
    level = str(state.get("risk_level") or "").lower()
    if state.get("prediction") != "BENIGN" and level not in ("", "none") and level not in report:
        return False   # report must mention the same risk level
    if state.get("verification_status") == "NEEDS_HUMAN_REVIEW" and "human" not in report:
        return False   # report must mention human review
    return True


# ---------- Decision logic: what should run next? ----------
def decide(state: dict):
    if state.get("audit_log_id") is not None:
        return "FINISH", "audit saved, workflow complete"
    if state.get("prediction") is None:
        return "investigation", "no prediction yet"
    if state.get("risk_score") is None:
        return "risk_scoring", "risk not calculated"
    if state.get("incident_id") is None:
        return "incident_correlation", "incident not correlated"
    if state.get("verification_status") is None:
        return "verification", "no verification decision"
    if not state.get("report"):
        return "report", "final report missing"
    if not report_is_consistent(state) and (state.get("report_retries") or 0) < MAX_REPORT_RETRIES:
        return "report", "report inconsistent with risk/decision, regenerate"
    if state.get("outcome") is None:
        if state["verification_status"] == "VERIFIED":
            return "automated_action", "verified, recommend automated action"
        return "escalation", "needs human review, escalate"
    return "audit_log", "record the run"


def supervisor_node(state: SupervisorState) -> dict:
    steps = (state.get("step_count") or 0) + 1
    log = list(state.get("supervisor_log") or [])
    retries = state.get("report_retries") or 0

    nxt, reason = decide(state)

    # safety: too many steps -> jump to audit (or finish if already done)
    if steps > MAX_STEPS:
        nxt, reason = ("FINISH", "max steps reached") if state.get("audit_log_id") is not None \
            else ("audit_log", "max steps reached, force audit")

    if nxt == "report" and state.get("report"):
        retries += 1   # this is a retry

    log.append(f"step {steps}: {nxt} ({reason})")
    print(f"[SUPERVISOR] step {steps} -> {nxt} | {reason}")
    return {"next_agent": nxt, "step_count": steps,
            "report_retries": retries, "supervisor_log": log}


def route(state: SupervisorState) -> str:
    return END if state["next_agent"] == "FINISH" else state["next_agent"]


# ---------- Build the graph ----------
WORKERS = {
    "investigation": investigation_node,
    "risk_scoring": risk_scoring_node,
    "incident_correlation": incident_correlation_node,
    "verification": verification_node,
    "report": report_node,
    "automated_action": automated_action_node,
    "escalation": escalation_node,
    "audit_log": audit_log_node,
}

graph = StateGraph(SupervisorState)
graph.add_node("supervisor", supervisor_node)
for name, fn in WORKERS.items():
    graph.add_node(name, fn)
    graph.add_edge(name, "supervisor")      # every worker reports back

graph.set_entry_point("supervisor")
graph.add_conditional_edges(
    "supervisor", route, {**{n: n for n in WORKERS}, END: END}
)
supervisor_app = graph.compile()


# ---------- Test ----------
if __name__ == "__main__":
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    df = pd.read_csv(os.path.join(SCRIPT_DIR, "sample_test_data.csv"))

    for label, asset in [("DoS Slowhttptest", "Database Server"), ("BENIGN", "Web Server")]:
        row = df[df["Label"] == label].drop(columns=["Label"]).iloc[[0]]
        s = supervisor_app.invoke({"network_data": row, "asset": asset})
        print(f"\n=== {label} on {asset} ===")
        print("Verification:", s["verification_status"], "| Outcome:", s["outcome"])
        print("Supervisor log:")
        for line in s["supervisor_log"]:
            print("  ", line)