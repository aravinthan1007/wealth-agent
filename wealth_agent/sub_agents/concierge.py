"""Concierge Steward Sub-Agent (Tier 1).

Handles lifestyle and concierge services. Tools: propose_engagement (seal), send_alert (Tier 3).
"""
from google.adk.agents.llm_agent import LlmAgent
from wealth_agent.tools.actions import propose_engagement, send_alert


def create_concierge_agent(model: str) -> LlmAgent:
    return LlmAgent(
        model=model,
        name="concierge_steward",
        description="Concierge Steward: Lifestyle and concierge advisor. Books services, arranges engagements (requires confirmation).",
        instruction=(
            "You are the Concierge Steward. Help with lifestyle services, travel, maintenance arrangements, "
            "tax prep referrals, estate planning, and personal services. When asked to book a service, "
            "use propose_engagement and wait for confirmation. Never commit without approval."
        ),
        tools=[
            propose_engagement,
            send_alert,
        ],
    )


__all__ = ["create_concierge_agent"]
