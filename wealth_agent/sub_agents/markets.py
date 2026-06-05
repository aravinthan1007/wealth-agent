"""Markets Steward Sub-Agent (Tier 1).

Handles portfolio and market-related queries. Tools: get_stock_quotes, search_web,
fetch_url, propose_rebalance (seal).
"""
from google.adk.agents.llm_agent import LlmAgent
from wealth_agent.tools.market import get_stock_quotes, search_web, fetch_url
from wealth_agent.tools.actions import propose_rebalance


def create_markets_agent(model: str) -> LlmAgent:
    return LlmAgent(
        model=model,
        name="markets_steward",
        description="Markets Steward: Portfolio and market advisor. Analyzes stocks, proposes rebalancing (requires confirmation).",
        instruction=(
            "You are the Markets Steward. Help with portfolio analysis, stock quotes, market research, "
            "and rebalancing proposals. When asked to rebalance, use propose_rebalance and wait for confirmation. "
            "Never execute trades without approval."
        ),
        tools=[
            get_stock_quotes,
            search_web,
            fetch_url,
            propose_rebalance,
        ],
    )


__all__ = ["create_markets_agent"]
