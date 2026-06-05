"""TIER 2: Aurelius Coordinator Agent + Sub-Agents + Self-Reflection.

Aurelius coordinates Markets, Estate, and Concierge specialists via LLM-driven delegation.
Each specialist has its own tools. Seals (propose_rebalance, propose_engagement) require confirmation.
Aurelius can self-reflect via query_traces (Phoenix MCP) on past runs.
"""
import os
from pathlib import Path
from dotenv import load_dotenv


def _load_repo_env() -> str:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    load_dotenv(env_path, override=False)
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if gemini_api_key and not os.getenv("GOOGLE_API_KEY"):
        os.environ["GOOGLE_API_KEY"] = gemini_api_key
    return os.getenv("MODEL", "gemini-3.1-flash-lite")


MODEL = _load_repo_env()


root_agent = None

try:
    from google.adk.agents.llm_agent import LlmAgent
    from .instrumentation import init_tracing
    from .tools.finance import (
        get_networth,
        get_expenses,
        get_credit_cards,
        get_income,
        get_profile,
    )
    from .tools.memory import remember, recall
    from .tools.utils import calculate
    from .tools.traces import query_traces
    from .sub_agents.markets import create_markets_agent
    from .sub_agents.estate import create_estate_agent
    from .sub_agents.concierge import create_concierge_agent

    init_tracing()

    markets_agent = create_markets_agent(MODEL)
    estate_agent = create_estate_agent(MODEL)
    concierge_agent = create_concierge_agent(MODEL)

    from .safety import safety_before_tool_callback, compliance_before_tool_callback

    root_agent = LlmAgent(
        model=MODEL,
        name="Aurelius",
        description="Aurelius Coordinator: wealth management advisor (Tier 1, command→sub-agent)",
        instruction=(
            "You are Aurelius, the wealth management coordinator. You delegate to three specialists: "
            "Markets Steward (portfolio, stocks, rebalancing), "
            "Estate Steward (accounts, assets, liabilities, income), and "
            "Concierge Steward (lifestyle, services, engagements). "
            "\n\nDelegation rules: "
            "- For portfolio/market questions → Markets Steward "
            "- For asset/liability/income questions → Estate Steward "
            "- For lifestyle/services → Concierge Steward "
            "\n\nFor general questions (net worth, expenses, profile, memory), use your direct tools. "
            "Always require confirmation before any proposal is accepted. Seals (propose_rebalance, propose_engagement) halt for approval."
        ),
        tools=[
            get_networth,
            get_expenses,
            get_credit_cards,
            get_income,
            get_profile,
            remember,
            recall,
            calculate,
            query_traces,
        ],
        sub_agents=[markets_agent, estate_agent, concierge_agent],
        before_tool_callback=[safety_before_tool_callback, compliance_before_tool_callback],
    )
except Exception as e:
    print(f"Warning: Could not initialize ADK LlmAgent: {e}")
    root_agent = None
