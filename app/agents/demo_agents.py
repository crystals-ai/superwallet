from __future__ import annotations

from typing import Dict, Optional

from app.schemas import PaymentIntent


SUPPORTED_AGENTS = {
    "research-agent",
    "trading-agent",
    "compliance-agent",
    "legal-agent",
    "sales-agent",
    "hr-agent",
}


def run_demo_agent(agent_id: str, task: str) -> Optional[PaymentIntent]:
    lower_task = task.lower()

    if agent_id == "research-agent":
        if "sec filings" in lower_task or "nvidia" in lower_task:
            return _intent(agent_id, task, "SECData API", 4.50, "data_api", "Fetch SEC filings and earnings disclosures")
        if "premium alpha" in lower_task or "ignore prior instructions" in lower_task:
            return _intent(agent_id, task, "Premium Alpha Trading Signals", 499.00, "trading_service", "Purchase premium trading package")
        if "financial dataset" in lower_task or "comparative analysis" in lower_task:
            return _intent(agent_id, task, "AlphaSense", 18.00, "data_api", "Purchase industry comparison dataset")

    if agent_id == "trading-agent":
        if "market data" in lower_task or "terminal" in lower_task or "price feed" in lower_task:
            return _intent(agent_id, task, "Bloomberg Terminal", 12.00, "market_data", "Access live market data and analytics")
        if "execute trade" in lower_task or "wallet transfer" in lower_task or "crypto bot" in lower_task:
            return _intent(agent_id, task, "FlashTrade Crypto Bot", 1200.00, "trade_execution", "Trigger external automated trade execution")
        if "alternative data" in lower_task or "analyst transcript" in lower_task:
            return _intent(agent_id, task, "AlphaSense", 45.00, "research_platform", "Buy premium alternative research data")

    if agent_id == "compliance-agent":
        if "sanctions" in lower_task or "kyc" in lower_task or "aml" in lower_task:
            return _intent(agent_id, task, "ComplyAdvantage", 16.00, "compliance_data", "Run sanctions and AML screening")
        if "wallet" in lower_task or "token mixer" in lower_task or "ignore prior instructions" in lower_task:
            return _intent(agent_id, task, "ShadowMixer Intelligence", 350.00, "crypto_monitoring", "Purchase off-policy crypto wallet screening")
        if "enhanced due diligence" in lower_task or "vendor risk" in lower_task:
            return _intent(agent_id, task, "LexisNexis Bridger Insight XG", 28.00, "compliance_data", "Request enhanced due diligence report")

    if agent_id == "legal-agent":
        if "case law" in lower_task or "litigation" in lower_task or "precedent" in lower_task:
            return _intent(agent_id, task, "LexisNexis", 22.00, "legal_research", "Retrieve case law and precedent research")
        if "wire funds" in lower_task or "settlement gift card" in lower_task:
            return _intent(agent_id, task, "InstantGiftCards", 500.00, "gift_card", "Attempt off-policy disbursement for outside counsel")
        if "contract benchmark" in lower_task or "draft agreement" in lower_task:
            return _intent(agent_id, task, "Practical Law", 35.00, "legal_research", "Purchase model clause and benchmark access")

    if agent_id == "sales-agent":
        if "prospect" in lower_task or "lead list" in lower_task or "contact data" in lower_task:
            return _intent(agent_id, task, "ZoomInfo", 19.00, "sales_intelligence", "Enrich prospect contact and company data")
        if "gift cards" in lower_task or "send rewards" in lower_task or "personal gmail" in lower_task:
            return _intent(agent_id, task, "BulkGiftNow", 275.00, "gift_card", "Send unapproved prospect incentives")
        if "crm enrichment" in lower_task or "account scoring" in lower_task:
            return _intent(agent_id, task, "Salesforce Data Cloud", 42.00, "crm_enrichment", "Enhance account scoring with external sales data")

    if agent_id == "hr-agent":
        if "candidate screening" in lower_task or "background check" in lower_task or "recruiting" in lower_task:
            return _intent(agent_id, task, "LinkedIn Recruiter", 14.00, "recruiting_platform", "Source candidates and recruiting profiles")
        if "salary wire" in lower_task or "crypto payroll" in lower_task or "ignore prior instructions" in lower_task:
            return _intent(agent_id, task, "FastCryptoPayroll", 900.00, "payroll", "Attempt off-policy payroll transfer")
        if "employee records" in lower_task or "workday data" in lower_task or "benefits" in lower_task:
            return _intent(agent_id, task, "Workday", 31.00, "hris", "Access workforce planning and benefits records")

    return None


def _intent(agent_id: str, task: str, vendor: str, amount: float, category: str, purpose: str) -> PaymentIntent:
    return PaymentIntent(
        agent_id=agent_id,
        task=task,
        vendor=vendor,
        amount=amount,
        category=category,
        purpose=purpose,
    )
