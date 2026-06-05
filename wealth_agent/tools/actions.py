"""Action tools: propose_rebalance (human-confirmed) and placeholders.

Seals pattern: returns proposals with requires_confirmation=True for LlmAgent.
For Workflow+RequestInput HITL pattern, see seals_workflow.py.
Safety checks via before_tool_callback block risky tool parameters.
"""
from typing import Dict, Any


def propose_rebalance(portfolio: Dict[str, float], target_allocation: Dict[str, float]) -> Dict[str, Any]:
    """Propose portfolio rebalancing with RequestInput HITL pause.

    Returns a RequestInput event that pauses the SSE stream and waits for user approval.
    This is the real Seal pattern in ADK 2.1 — not requires_confirmation flag.

    Gated by before_tool_callback safety checks (runs before this returns):
    - Blocks leverage > 2.0x
    - Blocks risky language keywords

    Args:
        portfolio: Current holdings {symbol: amount}
        target_allocation: Target allocation {symbol: percentage}

    Returns:
        RequestInput that pauses the stream for user approval/decline
    """
    from google.adk.events import RequestInput

    total = float(sum(portfolio.values())) or 1.0
    proposal = []
    for symbol, pct in target_allocation.items():
        current = float(portfolio.get(symbol, 0.0))
        desired = pct * total
        diff = round(desired - current, 2)
        if abs(diff) < 0.01:
            continue
        action = "buy" if diff > 0 else "sell"
        proposal.append({"symbol": symbol, "action": action, "amount": abs(diff)})

    # Return RequestInput to PAUSE the stream and request user approval
    return RequestInput(
        message=f"Portfolio Rebalance Proposal:\n{proposal}\n\nApprove this rebalancing?",
        responseSchema={
            "type": "object",
            "properties": {
                "decision": {
                    "type": "string",
                    "enum": ["Approve", "Decline"],
                    "description": "User approval decision"
                },
                "notes": {
                    "type": "string",
                    "description": "Optional notes"
                }
            },
            "required": ["decision"]
        },
        payload={"proposal": proposal}
    )


def propose_engagement(service_type: str, description: str) -> Dict[str, Any]:
    """Propose concierge engagement with seal gate (requires_confirmation: true).

    Gated by before_tool_callback safety checks.
    """
    return {
        "proposal": {
            "service_type": service_type,
            "description": description,
            "estimated_cost": "TBD",
            "timeline": "To be discussed"
        },
        "requires_confirmation": True,
        "message": f"Engagement proposal: {service_type}. Awaiting your approval."
    }


def send_alert(user_id: str, message: str) -> Dict[str, str]:
    # Placeholder for Tier 3; does not actually send anything in Tier 0.
    return {"status": "queued", "user_id": user_id, "message": message}


__all__ = ["propose_rebalance", "propose_engagement", "send_alert"]
