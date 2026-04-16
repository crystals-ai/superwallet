from __future__ import annotations

from typing import Optional

from app.schemas import PaymentIntent


def run_research_agent(agent_id: str, task: str) -> Optional[PaymentIntent]:
    """Return a payment intent for known demo scenarios."""
    lower_task = task.lower()

    if "sec filings" in lower_task or "nvidia" in lower_task:
        return PaymentIntent(
            agent_id=agent_id,
            task=task,
            vendor="SECData API",
            amount=4.50,
            category="data_api",
            purpose="Fetch SEC filings and earnings disclosures",
        )

    if "premium alpha" in lower_task or "ignore prior instructions" in lower_task:
        return PaymentIntent(
            agent_id=agent_id,
            task=task,
            vendor="Premium Alpha Trading Signals",
            amount=499.00,
            category="trading_service",
            purpose="Purchase premium trading package",
        )

    if "financial dataset" in lower_task or "comparative analysis" in lower_task:
        return PaymentIntent(
            agent_id=agent_id,
            task=task,
            vendor="MarketPulse Pro",
            amount=18.00,
            category="data_api",
            purpose="Purchase industry comparison dataset",
        )

    return None
