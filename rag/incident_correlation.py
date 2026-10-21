# rag/incident_correlation.py
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any
import uuid

FAMILY = {
    "BENIGN": "BENIGN",
    "DoS Hulk": "DOS_APP",
    "DoS GoldenEye": "DOS_APP",
    "DoS slowloris": "DOS_APP",
    "DoS Slowhttptest": "DOS_APP",
    "DDoS": "DDOS",
    "Heartbleed": "EXPLOIT",
}

WINDOW = timedelta(minutes=5)

@dataclass
class Alert:
    alert_id: str
    prediction: str
    confidence: float
    risk_score: float
    risk_level: str
    asset: str
    ts: datetime
    report_snippet: str = ""

@dataclass
class Incident:
    incident_id: str
    family: str
    asset: str
    status: str  # OPEN / ESCALATED / CLOSED
    alerts: list[Alert] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    max_risk_score: float = 0.0
    max_risk_level: str = "None"
    primary_prediction: str = ""

    def recompute(self):
        if not self.alerts:
            return
        top = max(self.alerts, key=lambda a: a.risk_score)
        self.max_risk_score = top.risk_score
        self.max_risk_level = top.risk_level
        self.primary_prediction = top.prediction

class IncidentCorrelator:
    def __init__(self, window: timedelta = WINDOW):
        self.window = window
        self.incidents: list[Incident] = []

    def _family(self, prediction: str) -> str:
        return FAMILY.get(prediction, "OTHER")

    def ingest(self, alert_payload: dict[str, Any]) -> dict[str, Any]:
        """
        alert_payload keys from pipeline:
        prediction, confidence, risk_score, risk_level, asset, report (optional)
        """
        now = datetime.utcnow()
        alert = Alert(
            alert_id=str(uuid.uuid4())[:8],
            prediction=alert_payload["prediction"],
            confidence=float(alert_payload["confidence"]),
            risk_score=float(alert_payload.get("risk_score") or 0),
            risk_level=str(alert_payload.get("risk_level") or "None"),
            asset=str(alert_payload.get("asset") or "Web Server"),
            ts=now,
            report_snippet=(alert_payload.get("report") or "")[:200],
        )

        fam = self._family(alert.prediction)

        # BENIGN: usually don't merge into attack incidents
        if fam == "BENIGN":
            inc = Incident(
                incident_id=f"INC-{now.strftime('%H%M%S')}-{alert.alert_id}",
                family=fam,
                asset=alert.asset,
                status="CLOSED",
                alerts=[alert],
            )
            inc.recompute()
            self.incidents.append(inc)
            return self._result(inc, created=True, merged=False)

        # Find open incident to merge
        candidate = None
        for inc in reversed(self.incidents):
            if inc.status not in ("OPEN", "ESCALATED"):
                continue
            if inc.family != fam:
                continue
            # same asset makes stronger correlation (recommended for v1)
            if inc.asset != alert.asset:
                continue
            last_ts = max(a.ts for a in inc.alerts)
            if now - last_ts <= self.window:
                candidate = inc
                break

        if candidate is None:
            inc = Incident(
                incident_id=f"INC-{now.strftime('%H%M%S')}-{alert.alert_id}",
                family=fam,
                asset=alert.asset,
                status="OPEN",
                alerts=[alert],
            )
            inc.recompute()
            self.incidents.append(inc)
            return self._result(inc, created=True, merged=False)

        candidate.alerts.append(alert)
        candidate.recompute()
        return self._result(candidate, created=False, merged=True)

    def _result(self, inc: Incident, created: bool, merged: bool) -> dict:
        return {
            "incident_id": inc.incident_id,
            "incident_created": created,
            "incident_merged": merged,
            "incident_family": inc.family,
            "incident_alert_count": len(inc.alerts),
            "incident_max_risk_score": inc.max_risk_score,
            "incident_max_risk_level": inc.max_risk_level,
            "incident_primary_prediction": inc.primary_prediction,
            "incident_status": inc.status,
            "alert_ids": [a.alert_id for a in inc.alerts],
        }

# singleton for demo (process memory)
CORRELATOR = IncidentCorrelator()