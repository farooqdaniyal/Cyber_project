# rag/audit_log.py
# ============================================================
# AUDIT LOG
# Records every pipeline run (timestamp, prediction, risk,
# incident info, verification decision, final outcome) into a
# SQLite database that PERSISTS across restarts - unlike the
# in-memory IncidentCorrelator, this data survives even if the
# Streamlit app or Python process is restarted.
#
# Place this file in your "rag" folder alongside the other
# agent files.
# ============================================================

from __future__ import annotations
import os
import sqlite3
from datetime import datetime
from typing import Any

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "audit_log.sqlite3")


class AuditLogger:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                prediction TEXT,
                confidence REAL,
                asset TEXT,
                risk_score REAL,
                risk_level TEXT,
                incident_id TEXT,
                incident_status TEXT,
                incident_alert_count INTEGER,
                incident_created INTEGER,
                incident_merged INTEGER,
                verification_status TEXT,
                rule_decision TEXT,
                outcome TEXT,
                message TEXT
            )
        """)
        conn.commit()
        conn.close()

    def log(self, entry: dict[str, Any]) -> int:
        """
        entry keys expected (all optional, missing ones stored as NULL):
        prediction, confidence, asset, risk_score, risk_level,
        incident_id, incident_status, incident_alert_count,
        incident_created, incident_merged,
        verification_status, rule_decision, outcome, message
        """
        conn = sqlite3.connect(self.db_path)
        cur = conn.execute("""
            INSERT INTO audit_log (
                timestamp, prediction, confidence, asset,
                risk_score, risk_level,
                incident_id, incident_status, incident_alert_count,
                incident_created, incident_merged,
                verification_status, rule_decision,
                outcome, message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.utcnow().isoformat(timespec="seconds"),
            entry.get("prediction"),
            entry.get("confidence"),
            entry.get("asset"),
            entry.get("risk_score"),
            entry.get("risk_level"),
            entry.get("incident_id"),
            entry.get("incident_status"),
            entry.get("incident_alert_count"),
            int(bool(entry.get("incident_created"))) if entry.get("incident_created") is not None else None,
            int(bool(entry.get("incident_merged"))) if entry.get("incident_merged") is not None else None,
            entry.get("verification_status"),
            entry.get("rule_decision"),
            entry.get("outcome"),
            entry.get("message"),
        ))
        conn.commit()
        log_id = cur.lastrowid
        conn.close()
        return log_id

    def get_recent(self, limit: int = 100) -> list[dict]:
        """Returns the most recent runs, newest first."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM audit_log ORDER BY log_id DESC LIMIT ?", (limit,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_all_as_dataframe(self):
        """Convenience helper for Streamlit - returns a pandas DataFrame."""
        import pandas as pd
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query(
            "SELECT * FROM audit_log ORDER BY log_id DESC", conn
        )
        conn.close()
        return df


# singleton - reused across the app so every run writes to the same DB
AUDIT_LOGGER = AuditLogger()