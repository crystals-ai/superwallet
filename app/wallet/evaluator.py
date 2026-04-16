from __future__ import annotations

from datetime import datetime, timezone
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


def _transaction_count_today(agent_id: str, history: List[Dict[str, Any]]) -> int:
    today = datetime.now(timezone.utc).date()
    count = 0
    for row in history:
        if row["agent_id"] != agent_id:
            continue
        raw = row.get("created_at")
        if raw is None:
            continue
        try:
            text = raw if isinstance(raw, str) else str(raw)
            if "T" in text:
                day = datetime.fromisoformat(text.replace("Z", "+00:00")).date()
            else:
                day = datetime.strptime(text[:10], "%Y-%m-%d").date()
        except (TypeError, ValueError):
            continue
        if day == today:
            count += 1
    return count


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

    if policy["block_rules"].get("disallowed_category_blocks") and (
        "Category is not allowed for this agent" in reasons
    ):
        return _decision("BLOCKED", reasons, risk_score)

    if policy["block_rules"].get("non_allowlisted_vendor_blocks") and (
        "Vendor is not on the allowlist" in reasons
    ):
        return _decision("BLOCKED", reasons, risk_score)

    review_rules = policy["review_rules"]
    amt_review = float(review_rules.get("amount_review_threshold") or 0)
    if amt_review > 0 and intent.amount >= amt_review:
        return _decision("REVIEW_REQUIRED", reasons, max(risk_score, 0.55))

    velocity_cap = int(review_rules.get("daily_payment_count_review_threshold") or 0)
    if velocity_cap > 0 and _transaction_count_today(intent.agent_id, history) >= velocity_cap:
        return _decision("REVIEW_REQUIRED", reasons, max(risk_score, 0.55))

    if (
        review_rules["new_vendor_requires_review"]
        and is_new_vendor
        and intent.vendor not in agent_policy.get("allowed_vendors", [])
    ):
        return _decision("REVIEW_REQUIRED", reasons, max(risk_score, 0.55))

    if risk_score >= float(review_rules["risk_score_review_threshold"]):
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
