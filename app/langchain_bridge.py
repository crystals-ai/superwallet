from __future__ import annotations

import json
from typing import Any, Dict

import requests


def evaluate_payment_via_api(
    api_url: str,
    agent_id: str,
    task: str,
    vendor: str,
    amount: float,
    category: str,
    purpose: str,
    timeout: int = 15,
) -> Dict[str, Any]:
    response = requests.post(
        f"{api_url.rstrip('/')}/api/payments/evaluate",
        json={
            "agent_id": agent_id,
            "task": task,
            "vendor": vendor,
            "amount": amount,
            "category": category,
            "purpose": purpose,
        },
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()


def evaluate_payment_via_api_json(
    api_url: str,
    agent_id: str,
    task: str,
    vendor: str,
    amount: float,
    category: str,
    purpose: str,
    timeout: int = 15,
) -> str:
    return json.dumps(
        evaluate_payment_via_api(
            api_url=api_url,
            agent_id=agent_id,
            task=task,
            vendor=vendor,
            amount=amount,
            category=category,
            purpose=purpose,
            timeout=timeout,
        ),
        indent=2,
    )
