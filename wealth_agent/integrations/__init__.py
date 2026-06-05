"""
Tier 4: Integration modules
Firestore: Data persistence
Memory Bank: Persistent user context via Vertex AI
"""

from .firestore_service import (
    store_user_profile,
    load_user_profile,
    store_user_goals,
    load_user_goals,
    update_goal_progress,
    store_session_memory,
    load_recent_sessions,
    get_user_context
)

from .memory_bank import (
    get_memory_service,
    seed_user_memory,
    create_preload_memory_tool,
    create_load_memory_tool,
    create_remember_tool,
    persist_session_outcomes,
    update_user_goals_from_memory
)

__all__ = [
    "store_user_profile",
    "load_user_profile",
    "store_user_goals",
    "load_user_goals",
    "update_goal_progress",
    "store_session_memory",
    "load_recent_sessions",
    "get_user_context",
    "get_memory_service",
    "seed_user_memory",
    "create_preload_memory_tool",
    "create_load_memory_tool",
    "create_remember_tool",
    "persist_session_outcomes",
    "update_user_goals_from_memory"
]
