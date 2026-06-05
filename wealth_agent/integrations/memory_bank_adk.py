"""
Enhanced Memory Bank Integration using ADK patterns

Patterns from: memory-bank ADK sample
- PreloadMemoryTool for automatic context injection
- LoadMemoryTool for on-demand memory retrieval
- CallbackContext for memory generation after turns
- Managed memory topics (USER_PERSONAL_INFO, USER_PREFERENCES, etc.)
"""

import logging
from typing import Optional, Dict, Any
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.adk.tools.load_memory_tool import LoadMemoryTool
from vertexai._genai.types import (
    ManagedTopicEnum,
    MemoryBankCustomizationConfig as CustomizationConfig,
    MemoryBankCustomizationConfigMemoryTopic as MemoryTopic,
    MemoryBankCustomizationConfigMemoryTopicManagedMemoryTopic as ManagedMemoryTopic,
    ReasoningEngineContextSpecMemoryBankConfig as MemoryBankConfig,
)

logger = logging.getLogger(__name__)


# --- Memory Bank Configuration ---
# Defines which topics to extract and persist across sessions
#
# Available managed topics:
#   USER_PERSONAL_INFO     - names, relationships, financial goals
#   USER_PREFERENCES       - investment style, risk tolerance, communication style
#   KEY_CONVERSATION_DETAILS - portfolio decisions, progress on goals
#   EXPLICIT_INSTRUCTIONS  - rules to remember/forget about user
#
# Extended for wealth management:
#   - Financial goals and constraints
#   - Investment preferences
#   - Risk tolerance profile
#   - Previous portfolio decisions
MEMORY_BANK_CONFIG = MemoryBankConfig(
    customization_configs=[
        CustomizationConfig(
            memory_topics=[
                MemoryTopic(
                    managed_memory_topic=ManagedMemoryTopic(
                        managed_topic_enum=ManagedTopicEnum.USER_PERSONAL_INFO,
                    ),
                ),
                MemoryTopic(
                    managed_memory_topic=ManagedMemoryTopic(
                        managed_topic_enum=ManagedTopicEnum.USER_PREFERENCES,
                    ),
                ),
                MemoryTopic(
                    managed_memory_topic=ManagedMemoryTopic(
                        managed_topic_enum=ManagedTopicEnum.KEY_CONVERSATION_DETAILS,
                    ),
                ),
                MemoryTopic(
                    managed_memory_topic=ManagedMemoryTopic(
                        managed_topic_enum=ManagedTopicEnum.EXPLICIT_INSTRUCTIONS,
                    ),
                ),
            ],
        ),
    ],
)


def create_preload_memory_tool() -> PreloadMemoryTool:
    """Create PreloadMemoryTool for automatic context injection at session start.

    This tool automatically:
    1. Retrieves user's memories from prior sessions
    2. Injects them into the system instruction
    3. Makes model aware of past preferences/goals without explicit tool call

    Returns:
        PreloadMemoryTool instance for agent tools

    Usage:
        # Add to agent's tools list
        tools = [
            PreloadMemoryTool(),
            other_tools...
        ]
    """
    logger.info("Creating PreloadMemoryTool")
    return PreloadMemoryTool()


def create_load_memory_tool() -> LoadMemoryTool:
    """Create LoadMemoryTool for on-demand memory retrieval during conversation.

    This tool allows model to:
    1. Call explicitly when it needs past context
    2. Ask for specific types of memories
    3. Make decisions about when to use memory

    Returns:
        LoadMemoryTool instance for agent tools

    Usage:
        # Add to agent's tools list
        tools = [
            LoadMemoryTool(),  # Model calls this on-demand
            other_tools...
        ]
    """
    logger.info("Creating LoadMemoryTool")
    return LoadMemoryTool()


async def generate_memories_callback(callback_context: CallbackContext) -> None:
    """Callback executed after each agent turn to generate memories.

    This pattern:
    1. Captures session events after each turn
    2. Sends to Memory Bank for extraction/analysis
    3. Stores user preferences, goals, decisions for future sessions
    4. Enables adaptive behavior across conversations

    Args:
        callback_context: ADK CallbackContext with memory support

    Usage:
        # Attach to agent
        root_agent = Agent(
            name="aurelius",
            ...,
            after_agent_callback=generate_memories_callback,
        )
    """
    try:
        logger.info("Generating memories from session")
        # Add entire session to Memory Bank for extraction
        await callback_context.add_session_to_memory()
        logger.debug("Session memories generated successfully")
    except Exception as e:
        logger.error(f"Error generating memories: {e}")
        # Fail gracefully - don't disrupt agent flow
        return None


async def add_events_to_memory(
    callback_context: CallbackContext, events: list[Dict[str, Any]]
) -> None:
    """Selectively add specific events to Memory Bank.

    Useful for incremental memory generation without full session replay.

    Args:
        callback_context: ADK CallbackContext
        events: List of session events to persist

    Usage:
        # In sub-agent after important decision
        await add_events_to_memory(
            callback_context,
            events=[
                {
                    "type": "portfolio_decision",
                    "decision": "rebalanced to 60/40",
                    "reason": "risk tolerance increased",
                }
            ],
        )
    """
    try:
        logger.info(f"Adding {len(events)} events to Memory Bank")
        await callback_context.add_events_to_memory(events=events)
        logger.debug("Events added successfully")
    except Exception as e:
        logger.error(f"Error adding events to memory: {e}")


# --- Memory Context Templates ---
# Used to structure goal/preference information for Memory Bank


def format_financial_goal_for_memory(goal: Dict[str, Any]) -> str:
    """Format a financial goal for memory injection.

    Args:
        goal: Goal dict with name, type, horizon, target_amount, priority

    Returns:
        Formatted string for memory context

    Example:
        "User wants to retire with $5M in 20+ years (High priority)"
    """
    return (
        f"User goal: {goal.get('name')} "
        f"({goal.get('type')}) "
        f"- Target: ${goal.get('target_amount', 0):,} "
        f"in {goal.get('horizon')} "
        f"(Priority: {goal.get('priority', 'Medium')})"
    )


def format_profile_for_memory(profile: Dict[str, Any]) -> str:
    """Format user profile for memory injection.

    Args:
        profile: Profile dict with netWorth, investmentExperience, riskTolerance

    Returns:
        Formatted string for memory context

    Example:
        "User has $1M net worth, 10+ years experience, moderate risk tolerance"
    """
    net_worth = profile.get("netWorth", 0)
    experience = profile.get("investmentExperience", "Unknown")
    risk = profile.get("riskTolerance", "Moderate")

    return (
        f"User profile: ${net_worth:,} net worth, "
        f"{experience} investment experience, "
        f"{risk} risk tolerance"
    )


# --- Integration Checklist for ADK Memory Bank ---
#
# This module provides the ADK-native Memory Bank patterns that should
# replace the custom implementation in memory_bank.py for production.
#
# Steps to integrate:
# 1. Add PreloadMemoryTool() to agent's tools list
# 2. Add LoadMemoryTool() to specialist agents as needed
# 3. Attach generate_memories_callback to agent.after_agent_callback
# 4. Pass MEMORY_BANK_CONFIG to Agent Engine context_spec
# 5. Set MEMORY_BANK_ENABLED=true and AGENT_RUNTIME_ID in .env
#
# For local development (without Memory Bank):
# - Skip steps 1-4, use custom memory_bank.py instead
# - Use Firestore for persistence
# - Memory Bank upgrade available post-hackathon
