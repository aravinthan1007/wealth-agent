"""Aurelius Callbacks - Hooks for agent and tool execution.

Callbacks for tracking, auditing, and enriching agent/tool execution.
- after_agent: Called after agent responds
- after_tool: Called after tool executes
- add_session_to_memory: Persist session to Memory Bank
"""

from typing import Any, Dict, Optional
from datetime import datetime


async def after_agent_callback(
    response: str,
    agent_name: str,
    context: Optional[Dict[str, Any]] = None,
    **kwargs
) -> None:
    """Called after agent produces a response.

    Use cases:
    - Log response for audit trail
    - Add response to memory bank
    - Track conversation for long-term memory
    - Compute faithfulness score

    Args:
        response: Agent's text response
        agent_name: Name of agent that produced response
        context: Execution context with session_id, user_id, etc.
    """
    if not context:
        context = {}

    session_id = context.get("session_id", "unknown")
    user_id = context.get("user_id", "unknown")

    # Log to audit trail
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "type": "agent_response",
        "agent_name": agent_name,
        "user_id": user_id,
        "session_id": session_id,
        "response_length": len(response),
        "response_preview": response[:100] + "..." if len(response) > 100 else response,
    }

    # Could save to database, memory bank, or logging service
    print(f"[AUDIT] Agent response: {event}")


async def after_tool_callback(
    tool_name: str,
    params: Dict[str, Any],
    result: Any,
    context: Optional[Dict[str, Any]] = None,
    **kwargs
) -> None:
    """Called after tool executes.

    Use cases:
    - Track tool usage for provenance
    - Add tool call to execution trace
    - Audit sensitive operations
    - Capture execution latency

    Args:
        tool_name: Name of tool that executed
        params: Parameters passed to tool
        result: Return value from tool
        context: Execution context with session_id, user_id, etc.
    """
    if not context:
        context = {}

    session_id = context.get("session_id", "unknown")
    user_id = context.get("user_id", "unknown")

    # Log to audit trail with provenance
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "type": "tool_execution",
        "tool_name": tool_name,
        "user_id": user_id,
        "session_id": session_id,
        "params_keys": list(params.keys()),
        "result_type": type(result).__name__,
        "result_preview": str(result)[:50] + "..." if len(str(result)) > 50 else str(result),
    }

    # Could save to database for traceability
    print(f"[AUDIT] Tool call: {event}")


async def add_session_to_memory(
    session_id: str,
    user_id: str,
    app_name: str,
    messages: list,
    **kwargs
) -> None:
    """Add session to Memory Bank for long-term context.

    Use cases:
    - Store session in vector database
    - Extract key facts for future reference
    - Build user knowledge base
    - Enable cross-session continuity

    Args:
        session_id: Unique session identifier
        user_id: User identifier
        app_name: Application name (e.g., "wealth_agent")
        messages: List of message exchanges
    """
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "type": "session_memory",
        "session_id": session_id,
        "user_id": user_id,
        "app_name": app_name,
        "message_count": len(messages),
    }

    print(f"[MEMORY] Session added: {event}")

    # In production, would:
    # 1. Extract key facts from messages
    # 2. Compute embeddings
    # 3. Store in vector database (Firestore, Pinecone, etc.)
    # 4. Make available for future sessions


__all__ = [
    "after_agent_callback",
    "after_tool_callback",
    "add_session_to_memory",
]
