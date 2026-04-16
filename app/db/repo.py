from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List

from app.schemas import PaymentIntent


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "wallet_control.db"


def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                task TEXT NOT NULL,
                vendor TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                purpose TEXT NOT NULL,
                decision TEXT NOT NULL,
                risk_score REAL NOT NULL,
                reasons TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def save_transaction(intent: PaymentIntent, evaluation: Dict[str, Any]) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO transactions (
                agent_id, task, vendor, amount, category, purpose,
                decision, risk_score, reasons
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                intent.agent_id,
                intent.task,
                intent.vendor,
                intent.amount,
                intent.category,
                intent.purpose,
                evaluation["decision"],
                evaluation["risk_score"],
                json.dumps(evaluation["reasons"]),
            ),
        )
        conn.commit()
        return int(cursor.lastrowid)


def get_agent_history(agent_id: str) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT agent_id, vendor, amount, category, decision, created_at
            FROM transactions
            WHERE agent_id = ?
            ORDER BY created_at DESC
            """,
            (agent_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_dashboard_data() -> Dict[str, Any]:
    with get_connection() as conn:
        totals = conn.execute(
            """
            SELECT
                COALESCE(SUM(CASE WHEN decision = 'APPROVED' THEN amount ELSE 0 END), 0) AS approved_spend,
                COALESCE(SUM(CASE WHEN decision = 'BLOCKED' THEN amount ELSE 0 END), 0) AS prevented_loss,
                COALESCE(SUM(CASE WHEN decision = 'REVIEW_REQUIRED' THEN 1 ELSE 0 END), 0) AS pending_review_count,
                COALESCE(SUM(CASE WHEN decision = 'BLOCKED' THEN 1 ELSE 0 END), 0) AS blocked_count
            FROM transactions
            """
        ).fetchone()

        by_agent_rows = conn.execute(
            """
            SELECT agent_id, ROUND(SUM(CASE WHEN decision = 'APPROVED' THEN amount ELSE 0 END), 2) AS total
            FROM transactions
            GROUP BY agent_id
            ORDER BY total DESC
            """
        ).fetchall()

        by_vendor_rows = conn.execute(
            """
            SELECT vendor, ROUND(SUM(CASE WHEN decision = 'APPROVED' THEN amount ELSE 0 END), 2) AS total
            FROM transactions
            GROUP BY vendor
            ORDER BY total DESC
            """
        ).fetchall()

        recent_rows = conn.execute(
            """
            SELECT id, agent_id, task, vendor, amount, category, purpose, decision, risk_score, reasons, created_at
            FROM transactions
            ORDER BY created_at DESC, id DESC
            LIMIT 20
            """
        ).fetchall()

    return {
        "summary": dict(totals),
        "by_agent": [dict(row) for row in by_agent_rows],
        "by_vendor": [dict(row) for row in by_vendor_rows],
        "recent_transactions": [
            {**dict(row), "reasons": json.loads(row["reasons"])} for row in recent_rows
        ],
    }


def review_transaction(transaction_id: int, approved: bool) -> bool:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT reasons FROM transactions WHERE id = ?",
            (transaction_id,),
        ).fetchone()
        if row is None:
            return False

        reasons = json.loads(row["reasons"])
        reasons.append(
            "Reviewed by human: approved" if approved else "Reviewed by human: blocked"
        )
        conn.execute(
            """
            UPDATE transactions
            SET decision = ?, reasons = ?
            WHERE id = ?
            """,
            (
                "APPROVED" if approved else "BLOCKED",
                json.dumps(reasons),
                transaction_id,
            ),
        )
        conn.commit()
        return True
