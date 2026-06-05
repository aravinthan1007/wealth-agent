"""Safety guardrails with before_tool_callback (ADK 2.1 HardStop pattern).

Implements actual blocking callbacks for financial safety in LlmAgent.
Pattern: Use before_tool_callback to validate/block risky tool calls before execution.

Integration: Pass safety_before_tool_callback to LlmAgent(before_tool_callback=...)
"""

from typing import Any, Dict, Optional
from google.adk.tools.base_tool import BaseTool
from google.adk.agents.context import Context


# --- Safety limits ---
MAX_LEVERAGE = 2.0
LARGE_TRANSACTION_THRESHOLD = 100000
RISKY_KEYWORDS = {"emergency", "urgent", "immediately", "now", "asap"}


class SafetyViolation(Exception):
    """Safety guardrail violation—blocks tool execution."""
    pass


async def safety_before_tool_callback(
    tool: BaseTool,
    params: Dict[str, Any],
    context: Context,
    **kwargs
) -> Optional[Dict[str, Any]]:
    """Block risky tool calls before execution.

    ADK 2.1 before_tool_callback pattern:
    - Receives: tool (BaseTool), params (dict), context (Context)
    - Returns: None to proceed with tool, or dict to skip tool
    - Raises: Exception to block and error

    This function ACTUALLY BLOCKS execution, not just logs.
    """
    tool_name = tool.name.lower()

    # Block high-leverage rebalancing
    if "rebalance" in tool_name or "portfolio" in tool_name:
        if "target_allocation" in params:
            target = params.get("target_allocation", {})
            # Check if any asset class exceeds leverage
            for asset, weight in target.items():
                if isinstance(weight, (int, float)) and weight > MAX_LEVERAGE:
                    raise SafetyViolation(
                        f"Leverage {weight}x exceeds maximum {MAX_LEVERAGE}x for {asset}. "
                        f"Rebalancing blocked by safety guardrail."
                    )

    # Flag and log large transactions (audit, don't block)
    if "amount" in params or "total" in params:
        amount = params.get("amount") or params.get("total", 0)
        if isinstance(amount, (int, float)) and amount > LARGE_TRANSACTION_THRESHOLD:
            # Set metadata for audit trail but proceed
            try:
                context.set_callback_metadata({
                    "compliance_flag": "large_transaction",
                    "amount": amount,
                    "tool": tool_name,
                })
            except:
                pass  # Context metadata not available in all versions

    # Block risky language in proposals
    if "message" in params or "description" in params:
        text = (params.get("message", "") or params.get("description", "")).lower()
        risky_found = [k for k in RISKY_KEYWORDS if k in text]
        if risky_found:
            raise SafetyViolation(
                f"Risky language detected: {risky_found}. "
                f"Financial decisions require deliberate approval, not urgency. Proposal blocked."
            )

    # Allow tool execution (return None = proceed)
    return None


async def compliance_before_tool_callback(
    tool: BaseTool,
    params: Dict[str, Any],
    context: Context,
    **kwargs
) -> Optional[Dict[str, Any]]:
    """Log all tool calls for compliance audit (non-blocking).

    Records what tools are being called, when, and with what parameters.
    """
    from datetime import datetime

    audit_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "tool_name": tool.name,
        "params_keys": list(params.keys()),
    }

    # Try to log to context (may not be available)
    try:
        context.set_callback_metadata({"compliance_audit": audit_entry})
    except:
        pass  # Context not available, skip

    # Don't block—return None to let tool execute
    return None


__all__ = [
    "safety_before_tool_callback",
    "compliance_before_tool_callback",
    "SafetyViolation",
    "MAX_LEVERAGE",
    "LARGE_TRANSACTION_THRESHOLD",
    "RISKY_KEYWORDS",
]
