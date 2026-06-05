"""Seals: Human-in-the-loop approval gates for financial actions.

Pattern from: workflows-HITL_concierge ADK sample
- Returns proposals with requires_confirmation=true (Tier 1 LlmAgent)
- Ready to upgrade to WorkflowAgent + RequestInput when available (Tier 2+)
- Never auto-executes; always halts for approval

Current implementation (ADK 1.34.3):
  - Proposals return requires_confirmation=true
  - Frontend/UI implements approval gate

Future upgrade (when WorkflowAgent available):
  - Use RequestInput to halt workflow
  - Use WorkflowAgent edges to chain proposal → approval → execution
  - Full end-to-end human-in-the-loop in agent
"""

from typing import Dict, Any
from pydantic import BaseModel


# --- Data models ---
class ApprovalRequest(BaseModel):
    """User's approval response (Approve or Decline)."""
    decision: str  # "Approve" or "Decline"
    notes: str = ""  # Optional reason


class RebalanceProposal(BaseModel):
    """Proposed portfolio rebalancing."""
    proposal: list[Dict[str, Any]]
    requires_confirmation: bool


class EngagementProposal(BaseModel):
    """Proposed concierge engagement."""
    proposal: Dict[str, str]
    requires_confirmation: bool


# --- Future: Async approval handlers for WorkflowAgent ---
# When WorkflowAgent + RequestInput become available in ADK,
# these functions will be used in workflow edges:
#
# async def request_rebalance_approval(proposal: RebalanceProposal):
#     """Async approval request using RequestInput."""
#     from google.adk.agents.workflow.events.request_input import RequestInput
#     yield RequestInput(message=..., response_schema=..., payload=proposal.dict())
#
# Then in WorkflowAgent edges:
#   edges=[
#       ("START", propose_rebalance_func, request_rebalance_approval),
#       (request_rebalance_approval, execute_rebalance_if_approved),
#   ]


# --- Seal enforcement: return halted proposals with requires_confirmation flag ---


def seal_rebalance(portfolio: Dict[str, float], target_allocation: Dict[str, float]) -> Dict[str, Any]:
    """Propose rebalancing. Returns proposal with seal gate.

    The seal gate halts execution in:
    - LlmAgent context (Tier 1): Frontend UI implements approval gate
    - WorkflowAgent context (Tier 2+, when available): RequestInput halts workflow

    Args:
        portfolio: Current holdings {symbol: amount}
        target_allocation: Target {symbol: percentage}

    Returns:
        Proposal dict with requires_confirmation=true
        Frontend must implement approval UI before executing
    """
    total = float(sum(portfolio.values()))
    proposal = []
    for symbol, pct in target_allocation.items():
        current = float(portfolio.get(symbol, 0.0))
        desired = pct * total
        diff = round(desired - current, 2)
        if abs(diff) < 0.01:
            continue
        action = "buy" if diff > 0 else "sell"
        proposal.append({"symbol": symbol, "action": action, "amount": abs(diff)})

    return {
        "proposal": proposal,
        "requires_confirmation": True,
        "message": "Rebalancing proposal ready for your approval (see Review Proposal card)"
    }


def seal_engagement(service_type: str, description: str) -> Dict[str, Any]:
    """Propose service engagement. Returns proposal with seal gate.

    Args:
        service_type: Type of service (tax prep, estate, etc.)
        description: Service details

    Returns:
        Proposal dict with requires_confirmation=true
        Frontend must implement approval UI before executing
    """
    return {
        "proposal": {
            "service_type": service_type,
            "description": description,
            "estimated_cost": "TBD",
            "timeline": "To be discussed",
        },
        "requires_confirmation": True,
        "message": "Concierge engagement ready for your approval (see Concierge Alert card)"
    }


__all__ = [
    "ApprovalRequest",
    "RebalanceProposal",
    "EngagementProposal",
    "seal_rebalance",
    "seal_engagement",
]
