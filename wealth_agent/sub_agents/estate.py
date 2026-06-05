"""Estate Steward Sub-Agent (Tier 1).

Handles assets, liabilities, accounts, and income. Tools: get_accounts, get_credit_cards,
get_income (from finance module).
"""
from google.adk.agents.llm_agent import LlmAgent
from wealth_agent.tools.finance import get_accounts, get_credit_cards, get_income


def create_estate_agent(model: str) -> LlmAgent:
    return LlmAgent(
        model=model,
        name="estate_steward",
        description="Estate Steward: Asset, liability, and income advisor. Manages accounts, credit cards, and income streams.",
        instruction=(
            "You are the Estate Steward. Help with asset management, account information, "
            "credit card oversight, and income planning. Provide actionable counsel on liability management "
            "and debt optimization."
        ),
        tools=[
            get_accounts,
            get_credit_cards,
            get_income,
        ],
    )


__all__ = ["create_estate_agent"]
