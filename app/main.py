from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from app.agents.research_agent import run_research_agent
from app.db.repo import (
    get_agent_history,
    get_dashboard_data,
    init_db,
    review_transaction,
    save_transaction,
)
from app.schemas import RunRequest, RunResponse
from app.wallet.evaluator import evaluate_payment
from app.wallet.policy_loader import load_policy


BASE_DIR = Path(__file__).resolve().parents[1]
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Agent Wallet Control Demo")


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/")
def serve_dashboard() -> FileResponse:
    return FileResponse(STATIC_DIR / "dashboard.html")


@app.get("/api/dashboard")
def dashboard_data() -> dict:
    return get_dashboard_data()


@app.post("/run", response_model=RunResponse)
def run_agent(request: RunRequest) -> RunResponse:
    if request.agent_id != "research-agent":
        raise HTTPException(status_code=404, detail="Unknown agent")

    payment_intent = run_research_agent(request.agent_id, request.task)
    if payment_intent is None:
        return RunResponse(
            payment_intent=None,
            decision="NO_PAYMENT_NEEDED",
            reasons=["Task completed without requiring a paid action"],
            risk_score=0.0,
        )

    policy = load_policy()
    history = get_agent_history(request.agent_id)
    evaluation = evaluate_payment(payment_intent, policy, history)
    save_transaction(payment_intent, evaluation)

    return RunResponse(
        payment_intent=payment_intent,
        decision=evaluation["decision"],
        reasons=evaluation["reasons"],
        risk_score=evaluation["risk_score"],
    )


@app.post("/api/review/{transaction_id}")
def resolve_review(transaction_id: int, approved: bool) -> dict:
    updated = review_transaction(transaction_id, approved=approved)
    if not updated:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"ok": True}
