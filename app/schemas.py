from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class RunRequest(BaseModel):
    agent_id: str = Field(..., description="Unique agent identifier")
    task: str = Field(..., description="Task assigned to the agent")


class PaymentIntent(BaseModel):
    agent_id: str
    task: str
    vendor: str
    amount: float
    category: str
    purpose: str


class EvaluationResult(BaseModel):
    decision: str
    reasons: List[str]
    risk_score: float


class RunResponse(BaseModel):
    payment_intent: Optional[PaymentIntent]
    decision: str
    reasons: List[str]
    risk_score: Optional[float] = None

