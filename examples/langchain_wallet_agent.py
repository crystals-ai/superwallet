from __future__ import annotations

import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from langchain.agents import create_agent
    from langchain.tools import tool
    from langchain_openai import ChatOpenAI
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "LangChain dependencies are not installed. "
        "Use a Python 3.10+ environment and run: pip install -r requirements-langchain.txt"
    ) from exc

from app.langchain_bridge import evaluate_payment_via_api_json


API_URL = os.getenv("SPENDSHIELD_API_URL", "http://127.0.0.1:8000")
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")


@tool
def request_payment(
    agent_id: str,
    task: str,
    vendor: str,
    amount: float,
    category: str,
    purpose: str,
) -> str:
    """Request approval before any paid vendor or external service is used."""
    return evaluate_payment_via_api_json(
        api_url=API_URL,
        agent_id=agent_id,
        task=task,
        vendor=vendor,
        amount=amount,
        category=category,
        purpose=purpose,
    )


def build_agent():
    model = ChatOpenAI(model=MODEL_NAME)
    return create_agent(
        model=model,
        tools=[request_payment],
        system_prompt=(
            "You are an enterprise AI agent. "
            "Never directly use paid vendors or subscriptions. "
            "Before using any paid API, terminal, dataset, or service, call request_payment exactly once. "
            "If the response is BLOCKED or REVIEW_REQUIRED, explain the result and stop."
        ),
    )


def main() -> None:
    agent = build_agent()
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "You are the trading-agent. "
                        "Task: Open Bloomberg Terminal market data for TSLA options and get approval "
                        "before using any paid service."
                    ),
                }
            ]
        }
    )
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
