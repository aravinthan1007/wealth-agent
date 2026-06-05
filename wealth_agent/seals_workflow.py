"""Seals as real Workflow + RequestInput pauses (ADK 2.1 HITL pattern).

Implements human-in-the-loop approval gates for financial actions.
Pattern: Workflow nodes that pause for RequestInput, then resume based on user approval.
"""

from typing import Any, Dict
from pydantic import BaseModel
from google.adk import Workflow
from google.adk.workflow import node, START
from google.adk.events import RequestInput


# --- Data models ---
class RebalanceProposal(BaseModel):
    """Proposed portfolio rebalancing."""
    proposal: list[Dict[str, Any]]
    message: str


class EngagementProposal(BaseModel):
    """Proposed concierge engagement."""
    proposal: Dict[str, str]
    message: str


class ApprovalResponse(BaseModel):
    """User's approval/decline response."""
    decision: str  # "Approve" or "Decline"
    notes: str = ""


# --- Workflow Nodes ---


@node
def propose_rebalance_node(
    portfolio: Dict[str, float],
    target_allocation: Dict[str, float],
) -> RebalanceProposal:
    """Propose rebalancing (Tier 1 node)."""
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

    return RebalanceProposal(
        proposal=proposal,
        message="Rebalancing proposal ready. Awaiting your approval.",
    )


@node
def request_rebalance_approval(proposal: RebalanceProposal) -> RequestInput:
    """Pause and request user approval for rebalancing (HITL gate).

    ADK 2.1 workflow will pause execution here and emit RequestInput event.
    User responds via RequestInput callback → resume with approval_response.
    """
    return RequestInput(
        message=f"Approve rebalancing: {proposal.proposal}?",
        responseSchema={
            "type": "object",
            "properties": {
                "decision": {
                    "type": "string",
                    "enum": ["Approve", "Decline"],
                    "description": "Approval decision",
                },
                "notes": {
                    "type": "string",
                    "description": "Optional notes",
                },
            },
            "required": ["decision"],
        },
        payload=proposal.dict(),
    )


@node
def execute_rebalance_if_approved(
    proposal: RebalanceProposal,
    approval_response: Dict[str, Any],
) -> Dict[str, Any]:
    """Execute rebalancing if approved. Otherwise return status."""
    decision = approval_response.get("decision", "Decline")

    if decision.lower() == "approve":
        return {
            "status": "executed",
            "proposal": proposal.proposal,
            "message": "Rebalancing executed successfully.",
        }
    else:
        return {
            "status": "declined",
            "proposal": proposal.proposal,
            "message": f"Rebalancing declined. Notes: {approval_response.get('notes', '')}",
        }


@node
def propose_engagement_node(service_type: str, description: str) -> EngagementProposal:
    """Propose concierge engagement (Tier 1 node)."""
    return EngagementProposal(
        proposal={
            "service_type": service_type,
            "description": description,
            "estimated_cost": "TBD",
            "timeline": "To be discussed",
        },
        message="Concierge engagement ready. Awaiting your approval.",
    )


@node
def request_engagement_approval(proposal: EngagementProposal) -> RequestInput:
    """Pause and request user approval for engagement (HITL gate)."""
    return RequestInput(
        message=f"Approve engagement: {proposal.proposal['service_type']}?",
        responseSchema={
            "type": "object",
            "properties": {
                "decision": {
                    "type": "string",
                    "enum": ["Approve", "Decline"],
                    "description": "Approval decision",
                },
                "notes": {
                    "type": "string",
                    "description": "Optional notes",
                },
            },
            "required": ["decision"],
        },
        payload=proposal.dict(),
    )


@node
def execute_engagement_if_approved(
    proposal: EngagementProposal,
    approval_response: Dict[str, Any],
) -> Dict[str, Any]:
    """Execute engagement if approved."""
    decision = approval_response.get("decision", "Decline")

    if decision.lower() == "approve":
        return {
            "status": "engaged",
            "proposal": proposal.proposal,
            "message": f"Engagement scheduled: {proposal.proposal['service_type']}",
        }
    else:
        return {
            "status": "declined",
            "proposal": proposal.proposal,
            "message": f"Engagement declined. Notes: {approval_response.get('notes', '')}",
        }


# --- Workflow Definitions ---


def create_rebalance_workflow() -> Workflow:
    """Create rebalance workflow with HITL approval gate.

    Flow: propose → request_approval (pause) → execute_if_approved
    """
    return Workflow(
        name="rebalance_workflow",
        description="Propose and execute portfolio rebalancing with user approval",
        input_schema={
            "type": "object",
            "properties": {
                "portfolio": {
                    "type": "object",
                    "description": "Current holdings {symbol: amount}",
                },
                "target_allocation": {
                    "type": "object",
                    "description": "Target allocation {symbol: percentage}",
                },
            },
            "required": ["portfolio", "target_allocation"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "proposal": {"type": "array"},
                "message": {"type": "string"},
            },
        },
        edges=[
            # propose → request_approval
            (START, propose_rebalance_node, request_rebalance_approval),
            # request_approval → execute (pause for user input)
            (request_rebalance_approval, execute_rebalance_if_approved),
        ],
    )


def create_engagement_workflow() -> Workflow:
    """Create engagement workflow with HITL approval gate."""
    return Workflow(
        name="engagement_workflow",
        description="Propose and execute concierge engagement with user approval",
        input_schema={
            "type": "object",
            "properties": {
                "service_type": {"type": "string"},
                "description": {"type": "string"},
            },
            "required": ["service_type", "description"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "proposal": {"type": "object"},
                "message": {"type": "string"},
            },
        },
        edges=[
            (START, propose_engagement_node, request_engagement_approval),
            (request_engagement_approval, execute_engagement_if_approved),
        ],
    )


__all__ = [
    "RebalanceProposal",
    "EngagementProposal",
    "ApprovalResponse",
    "create_rebalance_workflow",
    "create_engagement_workflow",
]
