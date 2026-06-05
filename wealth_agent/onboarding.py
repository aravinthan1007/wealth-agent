"""
Tier 4: Onboarding Goal Extraction Agent
Extracts structured goals from user profile + intake questionnaire
Validates and stores to Firestore + Memory Bank
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from google.adk import LlmAgent, FunctionTool
import json
from datetime import datetime

# Goal data structure
@dataclass
class Goal:
    id: str
    name: str
    type: str  # retirement, education, preservation, tax_optimization, real_estate, custom
    horizon: str  # "1-3 years", "3-10 years", "10-20 years", "20+ years"
    target_amount: float  # USD
    priority: str  # low, medium, high
    description: str
    created_at: str
    tools_needed: List[str]  # Tools this goal agent needs

# Predefined goal templates
GOAL_TEMPLATES = {
    "retirement": {
        "description": "Plan for retirement income and sustainability",
        "horizons": ["10-20 years", "20+ years"],
        "tools": ["get_networth", "get_income", "calculate", "propose_rebalance", "get_accounts"],
        "extraction_prompt": "Extract retirement goals: target age, desired annual income, lifestyle assumptions."
    },
    "education": {
        "description": "Fund education for children or family",
        "horizons": ["1-10 years", "10-20 years"],
        "tools": ["calculate", "propose_rebalance", "get_accounts"],
        "extraction_prompt": "Extract education goals: number of beneficiaries, school type, estimated costs."
    },
    "wealth_preservation": {
        "description": "Protect and preserve existing wealth",
        "horizons": ["10-20 years", "20+ years"],
        "tools": ["get_networth", "get_accounts", "propose_rebalance"],
        "extraction_prompt": "Extract preservation goals: risk tolerance, income needs, inheritance plans."
    },
    "tax_optimization": {
        "description": "Minimize tax liability through strategic planning",
        "horizons": ["1-3 years", "3-10 years"],
        "tools": ["calculate", "get_income", "get_accounts"],
        "extraction_prompt": "Extract tax goals: annual tax burden, loss harvesting opportunities, deduction maximization."
    },
    "real_estate": {
        "description": "Acquire or optimize real estate portfolio",
        "horizons": ["1-3 years", "3-10 years"],
        "tools": ["calculate", "get_networth", "propose_rebalance"],
        "extraction_prompt": "Extract real estate goals: property type, location, number of properties, acquisition timeline."
    },
    "wealth_growth": {
        "description": "Grow wealth through strategic investments",
        "horizons": ["3-10 years", "10-20 years"],
        "tools": ["get_stock_quotes", "propose_rebalance", "calculate"],
        "extraction_prompt": "Extract growth goals: target growth rate, risk tolerance, investment focus areas."
    }
}

def extract_goals_from_profile(profile: Dict[str, Any], intake: Dict[str, Any]) -> List[Goal]:
    """
    Extract structured goals from user profile + intake questionnaire

    Args:
        profile: User onboarding profile (name, residency, investment experience, etc.)
        intake: Goal intake responses (selected goals, horizons, targets)

    Returns:
        List of validated Goal objects
    """
    goals = []

    # Parse intake goal selections
    selected_goal_types = intake.get("goal_types", [])

    for goal_type in selected_goal_types:
        if goal_type not in GOAL_TEMPLATES:
            continue

        goal_template = GOAL_TEMPLATES[goal_type]

        # Build goal from template + user input
        goal = Goal(
            id=f"goal-{goal_type}-{datetime.now().timestamp()}",
            name=goal_template["description"],
            type=goal_type,
            horizon=intake.get(f"{goal_type}_horizon", "3-10 years"),
            target_amount=float(intake.get(f"{goal_type}_target", 0)),
            priority=intake.get(f"{goal_type}_priority", "medium"),
            description=intake.get(f"{goal_type}_description", ""),
            created_at=datetime.now().isoformat(),
            tools_needed=goal_template["tools"]
        )

        # Validate goal
        if validate_goal(goal, profile):
            goals.append(goal)

    return goals

def validate_goal(goal: Goal, profile: Dict[str, Any]) -> bool:
    """
    Validate goal against user profile and guardrails
    Prevents poisoning attacks on goal extraction

    Args:
        goal: Goal to validate
        profile: User profile for context

    Returns:
        True if goal is valid, False otherwise
    """
    # Validate target amount is reasonable for user's net worth
    net_worth = float(profile.get("netWorth", 0))
    if goal.target_amount > net_worth * 5:  # Target shouldn't exceed 5x net worth
        print(f"[WARN] Goal {goal.id} target exceeds reasonable threshold")
        return False

    # Validate horizon matches goal type
    valid_horizons = GOAL_TEMPLATES.get(goal.type, {}).get("horizons", [])
    if goal.horizon not in valid_horizons:
        print(f"[WARN] Goal {goal.id} horizon {goal.horizon} invalid for type {goal.type}")
        return False

    # Validate priority is valid
    if goal.priority not in ["low", "medium", "high"]:
        print(f"[WARN] Goal {goal.id} priority {goal.priority} invalid")
        return False

    # Validate tools exist
    from wealth_agent.agent import root_agent
    valid_tools = [tool.__name__ if hasattr(tool, '__name__') else str(tool) for tool in root_agent.tools] if root_agent else []
    for tool in goal.tools_needed:
        if tool not in valid_tools and tool not in ["propose_rebalance", "propose_engagement"]:
            print(f"[WARN] Goal {goal.id} references unknown tool {tool}")
            # Don't fail here - tools might not be registered yet

    return True

def sanitize_goals(goals: List[Goal]) -> List[Goal]:
    """
    Remove duplicate goals and conflicting goals
    Ensure goal list is coherent

    Args:
        goals: Raw extracted goals

    Returns:
        Sanitized goal list
    """
    # Remove exact duplicates by type
    seen_types = set()
    sanitized = []

    for goal in goals:
        if goal.type not in seen_types:
            sanitized.append(goal)
            seen_types.add(goal.type)
        else:
            print(f"[INFO] Removed duplicate goal type: {goal.type}")

    # Sort by priority (high, medium, low)
    priority_order = {"high": 0, "medium": 1, "low": 2}
    sanitized.sort(key=lambda g: priority_order.get(g.priority, 2))

    return sanitized

def goals_to_memory_context(goals: List[Goal]) -> str:
    """
    Convert goals to human-readable context for Memory Bank preloading

    Args:
        goals: List of goals

    Returns:
        Formatted string for Memory Bank
    """
    if not goals:
        return "No goals defined. User is exploring options."

    context = "User's Active Goals:\n"
    for i, goal in enumerate(goals, 1):
        context += f"\n{i}. {goal.name} (Priority: {goal.priority})\n"
        context += f"   - Horizon: {goal.horizon}\n"
        context += f"   - Target: ${goal.target_amount:,.0f}\n"
        if goal.description:
            context += f"   - Notes: {goal.description}\n"

    return context

# Onboarding Agent (uses existing tools to extract goals)
def create_onboarding_agent() -> LlmAgent:
    """Create a specialized agent for goal extraction during onboarding"""
    from wealth_agent.tools.finance import get_profile

    tools = [
        FunctionTool(
            func=get_profile,
            description="Get user's financial profile to inform goal extraction"
        )
    ]

    agent = LlmAgent(
        name="onboarding_agent",
        description="Extract and validate user financial goals during onboarding",
        model="gemini-3.1-flash-lite",
        tools=tools,
        instructions="""You are an expert financial goal extraction agent.
        When a user completes onboarding, your job is to:
        1. Analyze their profile (net worth, experience, residency)
        2. Ask clarifying questions about their financial goals
        3. Extract structured goals (retirement, education, preservation, etc.)
        4. Validate each goal is realistic given their profile
        5. Return a JSON list of validated goals

        Always be conservative - if a goal seems unrealistic, ask the user to clarify.
        Never assume goals; always ask first.
        Return goals in JSON format with fields: type, horizon, target_amount, priority, description
        """
    )

    return agent

# API functions for integration with Flask
def onboard_user_goals(user_id: str, profile: Dict[str, Any], intake: Dict[str, Any]) -> Dict[str, Any]:
    """
    Complete goal extraction and storage for a new user

    Args:
        user_id: Unique user identifier
        profile: User onboarding profile
        intake: Goal intake responses

    Returns:
        Dict with goals and Memory Bank initialization status
    """
    # Extract goals
    goals = extract_goals_from_profile(profile, intake)

    # Validate and sanitize
    validated_goals = sanitize_goals(goals)

    # Store to Firestore
    from wealth_agent.integrations.firestore_service import store_user_goals, store_user_profile
    store_user_profile(user_id, profile)
    store_user_goals(user_id, validated_goals)

    # Seed Memory Bank
    from wealth_agent.integrations.memory_bank import seed_user_memory
    memory_context = goals_to_memory_context(validated_goals)
    seed_user_memory(user_id, memory_context)

    return {
        "user_id": user_id,
        "goals": [asdict(g) for g in validated_goals],
        "goal_count": len(validated_goals),
        "memory_seeded": True,
        "created_at": datetime.now().isoformat()
    }

def load_user_goals(user_id: str) -> List[Goal]:
    """Load user's goals from Firestore"""
    from wealth_agent.integrations.firestore_service import load_user_goals as fs_load
    return fs_load(user_id)
