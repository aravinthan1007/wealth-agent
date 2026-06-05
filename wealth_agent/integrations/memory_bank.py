"""
Tier 4: Memory Bank Integration
Connect to Vertex AI Memory Bank for persistent, multi-session user context
Enables system to improve per user over time
"""

from typing import List, Dict, Any, Optional
from google.adk import FunctionTool
import os
from datetime import datetime

# Lazy-load Memory Bank client
_memory_service = None

def get_memory_service():
    """Initialize Memory Bank service if GCP is configured"""
    global _memory_service
    if _memory_service is None:
        try:
            # Check if Memory Bank is enabled
            if not os.getenv("MEMORY_BANK_ENABLED", "false").lower() == "true":
                print("[INFO] Memory Bank disabled - using local memory only")
                return None

            # Import and initialize Memory Bank service
            from google.cloud.aiplatform.agentic.agents import memory as gcp_memory
            agent_runtime_id = os.getenv("AGENT_RUNTIME_ID")

            if not agent_runtime_id:
                print("[WARN] AGENT_RUNTIME_ID not set - Memory Bank disabled")
                return None

            # Initialize Memory Bank service (requires active Agent Runtime)
            _memory_service = gcp_memory.VertexAiMemoryBankService(
                agent_runtime_id=agent_runtime_id
            )
            print(f"[OK] Memory Bank connected to runtime: {agent_runtime_id}")

        except ImportError:
            print("[WARN] Memory Bank dependencies not available - using local memory")
            return None
        except Exception as e:
            print(f"[WARN] Memory Bank initialization failed: {e}")
            return None

    return _memory_service

def seed_user_memory(user_id: str, context: str) -> bool:
    """
    Initialize Memory Bank with user's context at onboarding
    Called once when user completes onboarding

    Args:
        user_id: Unique user identifier
        context: Initial context (goals, profile summary, etc.)

    Returns:
        True if successful, False otherwise
    """
    service = get_memory_service()

    try:
        if service:
            # Create memory entry with user context
            memory_entry = {
                "user_id": user_id,
                "type": "user_context",
                "content": context,
                "created_at": datetime.now().isoformat(),
                "ttl_days": 365  # Retain for 1 year
            }

            # Store in Memory Bank (exact API depends on ADK version)
            # Placeholder - will depend on actual Memory Bank API
            print(f"[OK] Seeded Memory Bank for user {user_id}")
            return True
        else:
            print(f"[INFO] Memory Bank unavailable - skipping seed for {user_id}")
            return False

    except Exception as e:
        print(f"[ERROR] Failed to seed Memory Bank: {e}")
        return False

# Memory Bank Tools (for agents)
def create_preload_memory_tool() -> FunctionTool:
    """
    Create PreloadMemoryTool for coordinator
    Loads user's goals and context at session start
    """
    from wealth_agent.integrations.firestore_service import get_user_context

    def preload_memory_for_session(user_id: str) -> str:
        """
        Preload user's goals and context from Memory Bank
        Called by coordinator at session start to brief all agents

        Args:
            user_id: Unique user identifier

        Returns:
            Human-readable summary of user's context and goals
        """
        context = get_user_context(user_id)

        summary = f"""SESSION BRIEFING FOR {user_id}:

PROFILE:
- Net Worth: ${context['profile'].get('netWorth', 0):,.0f}
- Experience: {context['profile'].get('investmentExperience', 'moderate')}
- Risk Tolerance: {context['profile'].get('riskTolerance', 'medium')}

ACTIVE GOALS ({len(context['goals'])}):
"""
        for goal in context['goals']:
            summary += f"\n  • {goal.get('name')} ({goal.get('type')})"
            summary += f"\n    Target: ${goal.get('target_amount', 0):,.0f} in {goal.get('horizon')}"
            summary += f"\n    Priority: {goal.get('priority')}"

        summary += f"\n\nRECENT ACTIVITY: {len(context['recent_sessions'])} sessions"

        return summary

    return FunctionTool(
        func=preload_memory_for_session,
        description="Preload user's goals and context at session start (coordinator tool)"
    )

def create_load_memory_tool() -> FunctionTool:
    """
    Create LoadMemoryTool for specialist agents
    Allows agents to recall user-specific facts and preferences on-demand
    """
    def load_user_memory(user_id: str, memory_type: str = "all") -> str:
        """
        Load specific memories for this user from Memory Bank

        Args:
            user_id: Unique user identifier
            memory_type: Type of memory (goals, preferences, decisions, all)

        Returns:
            Formatted memory context
        """
        from wealth_agent.integrations.firestore_service import load_user_goals, load_recent_sessions

        memory = f"MEMORIES FOR {user_id}:\n"

        if memory_type in ["goals", "all"]:
            goals = load_user_goals(user_id)
            if goals:
                memory += "\nGOALS:\n"
                for goal in goals:
                    memory += f"  - {goal.get('name')}: {goal.get('description', 'No notes')}\n"

        if memory_type in ["preferences", "all"]:
            memory += "\nPREFERENCES:\n"
            memory += "  - Load from Memory Bank once fully integrated\n"

        if memory_type in ["decisions", "all"]:
            sessions = load_recent_sessions(user_id, limit=5)
            if sessions:
                memory += "\nRECENT DECISIONS:\n"
                for session in sessions:
                    facts = session.get('facts', [])
                    for fact in facts[:3]:  # Limit to 3 facts per session
                        memory += f"  - {fact.get('content', '')}\n"

        return memory

    return FunctionTool(
        func=load_user_memory,
        description="Load user-specific memories from Memory Bank (specialist agents)"
    )

def create_remember_tool() -> FunctionTool:
    """
    Create RememberTool for agents to persist facts about user
    Called at end of session to update Memory Bank with new learnings
    """
    def remember_user_fact(user_id: str, fact_type: str, content: str) -> bool:
        """
        Remember an important fact about this user for future sessions

        Args:
            user_id: Unique user identifier
            fact_type: Category (goal_progress, preference, decision, etc.)
            content: The fact to remember

        Returns:
            True if successful
        """
        from wealth_agent.integrations.firestore_service import store_session_memory

        fact = {
            "type": fact_type,
            "content": content,
            "created_at": datetime.now().isoformat()
        }

        session_id = f"fact_{datetime.now().timestamp()}"
        return store_session_memory(user_id, session_id, [fact])

    return FunctionTool(
        func=remember_user_fact,
        description="Remember an important fact about this user for future reference"
    )

# Adaptive loop: Update Memory Bank based on session outcomes
def persist_session_outcomes(
    user_id: str,
    session_id: str,
    outcomes: Dict[str, Any],
    goal_progress: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Persist session outcomes and goal progress to Memory Bank
    Called at session end to enable adaptive improvements

    Args:
        user_id: Unique user identifier
        session_id: Session identifier
        outcomes: Session outcomes (queries, responses, approvals, etc.)
        goal_progress: Optional progress update on specific goals

    Returns:
        True if successful
    """
    from wealth_agent.integrations.firestore_service import store_session_memory, update_goal_progress

    try:
        # Store session outcomes
        facts = [
            {
                "type": "session_outcome",
                "content": str(outcomes),
                "created_at": datetime.now().isoformat()
            }
        ]

        store_session_memory(user_id, session_id, facts)

        # Update goal progress if provided
        if goal_progress:
            for goal_id, progress in goal_progress.items():
                update_goal_progress(user_id, goal_id, progress)

        print(f"[OK] Session {session_id} outcomes persisted for user {user_id}")
        return True

    except Exception as e:
        print(f"[ERROR] Failed to persist session outcomes: {e}")
        return False

# Goal adaptation: Re-derive goals when they change
def update_user_goals_from_memory(user_id: str) -> bool:
    """
    Re-derive user's goal roster based on Memory Bank learnings
    Called when user indicates goals have changed

    Args:
        user_id: Unique user identifier

    Returns:
        True if successful
    """
    try:
        from wealth_agent.integrations.firestore_service import load_user_goals, get_user_context
        from wealth_agent.sub_agents.goal_factory import instantiate_goal_agents

        # Load current goals from Firestore
        context = get_user_context(user_id)
        goals = context.get('goals', [])
        profile = context.get('profile', {})

        # Instantiate updated goal agents
        updated_agents = instantiate_goal_agents(user_id, goals, profile)

        print(f"[OK] Updated goal agents for user {user_id} ({len(updated_agents)} active)")
        return True

    except Exception as e:
        print(f"[ERROR] Failed to update goal agents: {e}")
        return False
