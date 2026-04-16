from __future__ import annotations

from typing import Any, Dict, List

from app.schemas import PaymentIntent


def _is_new_vendor(intent: PaymentIntent, history: List[Dict[str, Any]]) -> bool:
    known_vendors = {row["vendor"] for row in history}
    return intent.vendor not in known_vendors


def _spend_today(agent_id: str, history: List[Dict[str, Any]]) -> float:
    return sum(
        row["amount"]
        for row in history
        if row["agent_id"] == agent_id and row["decision"] == "APPROVED"
    )


def _task_matches_payment(task: str, intent: PaymentIntent) -> bool:
    task_l = task.lower()
    vendor_l = intent.vendor.lower()

    if "sec filings" in task_l and "secdata" in vendor_l:
        return True

    if ("dataset" in task_l or "comparative analysis" in task_l) and intent.category == "data_api":
        return True

    if "premium alpha" in vendor_l and "sec filings" in task_l:
        return False

    if "ignore prior instructions" in task_l:
        return False

    return intent.category in {"data_api", "web_search"}


def evaluate_payment(
    intent: PaymentIntent,
    policy: Dict[str, Any],
    history: List[Dict[str, Any]],
) -> Dict[str, Any]:
    reasons: List[str] = []
    risk_score = 0.0

    agent_policy = policy["agents"][intent.agent_id]
    current_spend = _spend_today(intent.agent_id, history)

    if intent.vendor in agent_policy.get("blocked_vendors", []):
        reasons.append("Vendor is blocklisted")
        risk_score += 0.70

    if intent.amount > float(agent_policy["per_transaction_limit"]):
        reasons.append("Amount exceeds per-transaction limit")
        risk_score += 0.50

    if current_spend + intent.amount > float(agent_policy["daily_limit"]):
        reasons.append("Daily budget would be exceeded")
        risk_score += 0.40

    if intent.category not in agent_policy.get("allowed_categories", []):
        reasons.append("Category is not allowed for this agent")
        risk_score += 0.40

    if not _task_matches_payment(intent.task, intent):
        reasons.append("Payment does not match the current task context")
        risk_score += 0.50

    is_new_vendor = _is_new_vendor(intent, history)
    if is_new_vendor:
        reasons.append("Vendor is new for this agent")
        risk_score += 0.20

    if intent.vendor not in agent_policy.get("allowed_vendors", []):
        reasons.append("Vendor is not on the allowlist")
        risk_score += 0.20

    risk_score = min(risk_score, 0.99)

    if policy["block_rules"]["blocklisted_vendor_blocks"] and "Vendor is blocklisted" in reasons:
        return _decision("BLOCKED", reasons, risk_score)

    if policy["block_rules"]["over_limit_blocks"] and (
        "Amount exceeds per-transaction limit" in reasons
        or "Daily budget would be exceeded" in reasons
    ):
        return _decision("BLOCKED", reasons, risk_score)

    if policy["block_rules"]["semantic_mismatch_blocks"] and (
        "Payment does not match the current task context" in reasons
    ):
        return _decision("BLOCKED", reasons, risk_score)

    if (
        policy["review_rules"]["new_vendor_requires_review"]
        and is_new_vendor
        and intent.vendor not in agent_policy.get("allowed_vendors", [])
    ):
        return _decision("REVIEW_REQUIRED", reasons, max(risk_score, 0.55))

    if risk_score >= float(policy["review_rules"]["risk_score_review_threshold"]):
        return _decision("REVIEW_REQUIRED", reasons, risk_score)

    return _decision(
        "APPROVED",
        reasons or ["Within budget, vendor allowed, and task-aligned"],
        risk_score,
    )


def _decision(decision: str, reasons: List[str], risk_score: float) -> Dict[str, Any]:
    return {
        "decision": decision,
        "reasons": reasons,
        "risk_score": round(risk_score, 2),
    }
