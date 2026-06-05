"""
Tier 4: Goal-Agent Factory
Creates per-user goal agents from templates + personalization via Memory Bank
Never generates agent code per user - only instantiates from templates
"""

from typing import List, Optional, Dict, Any
from google.adk import LlmAgent, FunctionTool
from dataclasses import dataclass
from wealth_agent.tools.finance import (
    get_networth, get_accounts, get_credit_cards, get_income, get_profile
)
from wealth_agent.tools.market import get_stock_quotes, search_web
from wealth_agent.tools.actions import propose_rebalance, propose_engagement
from wealth_agent.tools.utils import calculate
from wealth_agent.tools.memory import remember, recall

@dataclass
class GoalAgentConfig:
    """Configuration for a goal agent instance"""
    goal_id: str
    goal_type: str  # retirement, education, wealth_preservation, etc.
    goal_name: str
    user_id: str
    horizon: str
    target_amount: float
    priority: str
    tools: List[str]
    instructions: str

# Goal-specific instructions (templates)
GOAL_INSTRUCTIONS = {
    "retirement": """You are a Retirement Planning Agent. Your mission: ensure sustainable retirement income.
    Focus on:
    - Current net worth and income streams
    - Projected retirement needs
    - Asset allocation for the {horizon} horizon
    - Withdrawal strategies and tax efficiency

    User's Goal: ${target_amount} retirement fund within {horizon}
    Priority: {priority}

    When asked about retirement, analyze their current assets/income and propose rebalancing
    toward conservative, income-generating investments. Always propose changes via propose_rebalance
    and require user approval.
    """,

    "education": """You are an Education Funding Agent. Your mission: secure education financing.
    Focus on:
    - Number of beneficiaries and education types
    - Time horizon until education expenses
    - Current education savings
    - Tax-advantaged education accounts

    User's Goal: Fund education with ${target_amount} within {horizon}
    Priority: {priority}

    Analyze their liquid assets and propose strategies like 529 plans, investment growth,
    or rebalancing. Always propose changes via propose_rebalance and require approval.
    """,

    "wealth_preservation": """You are a Wealth Preservation Agent. Your mission: protect and maintain wealth.
    Focus on:
    - Asset diversification across classes
    - Risk mitigation strategies
    - Tax-efficient wealth transfer
    - Estate planning considerations

    User's Goal: Preserve ${target_amount} wealth over {horizon}
    Priority: {priority}

    Monitor asset allocation for excessive concentration. Propose diversification and
    rebalancing to reduce risk. Always require approval before any changes.
    """,

    "tax_optimization": """You are a Tax Optimization Agent. Your mission: minimize tax liability.
    Focus on:
    - Current year tax situation
    - Loss harvesting opportunities
    - Tax-advantaged accounts utilization
    - Deduction and credit maximization

    User's Goal: Optimize taxes targeting ${target_amount} in savings within {horizon}
    Priority: {priority}

    Calculate potential tax savings and propose strategic actions like rebalancing into
    tax-loss harvesting positions. Always require user approval for financial changes.
    """,

    "real_estate": """You are a Real Estate Strategy Agent. Your mission: optimize real estate portfolio.
    Focus on:
    - Current property holdings and values
    - Geographic diversification
    - Income vs. appreciation orientation
    - Leverage and financing strategies

    User's Goal: Real estate strategy targeting ${target_amount} with {horizon} horizon
    Priority: {priority}

    Analyze their current holdings and net worth to determine capacity for acquisition.
    Propose rebalancing to fund down payments or optimize existing portfolio.
    """,

    "wealth_growth": """You are a Wealth Growth Agent. Your mission: grow portfolio value.
    Focus on:
    - Historical returns across asset classes
    - Current market conditions
    - Growth vs. value strategies
    - Rebalancing for market cycles

    User's Goal: Grow wealth to ${target_amount} within {horizon}
    Priority: {priority}

    Monitor market conditions and portfolio performance. When opportunities arise,
    propose rebalancing toward growth assets. Always require user approval.
    """
}

def make_goal_agent(
    goal_id: str,
    goal_type: str,
    goal_name: str,
    user_id: str,
    horizon: str,
    target_amount: float,
    priority: str,
    profile: Optional[Dict[str, Any]] = None
) -> LlmAgent:
    """
    Factory function: Create a goal-specific LlmAgent

    Args:
        goal_id: Unique goal identifier
        goal_type: Type of goal (retirement, education, etc.)
        goal_name: Human-readable goal name
        user_id: Owner of the goal
        horizon: Time horizon (e.g., "10-20 years")
        target_amount: Target amount in USD
        priority: Priority level (low, medium, high)
        profile: Optional user profile for context

    Returns:
        Configured LlmAgent for this specific goal
    """

    # Select tools relevant to this goal
    tools = get_goal_tools(goal_type)

    # Personalize instructions with goal details
    base_instructions = GOAL_INSTRUCTIONS.get(goal_type, GOAL_INSTRUCTIONS["wealth_growth"])
    personalized_instructions = base_instructions.format(
        target_amount=f"{target_amount:,.0f}",
        horizon=horizon,
        priority=priority
    )

    # Add user context if available
    if profile:
        personalized_instructions += f"\n\nUser Context:\n"
        personalized_instructions += f"- Current Net Worth: ${profile.get('netWorth', 0):,.0f}\n"
        personalized_instructions += f"- Investment Experience: {profile.get('investmentExperience', 'moderate')}\n"
        personalized_instructions += f"- Residency: {profile.get('residency', 'US')}\n"
        personalized_instructions += f"- Risk Tolerance: {profile.get('riskTolerance', 'medium')}\n"

    # Add Memory Bank recall instruction
    personalized_instructions += f"""

IMPORTANT: At the start of each conversation, use the recall tool to remember:
- Past conversations about this goal
- Previous recommendations and outcomes
- User preferences and constraints

After conversations, use the remember tool to persist:
- Key decisions made
- Recommendations given
- User responses and preferences
- Progress toward the goal
"""

    # Create agent
    agent = LlmAgent(
        name=f"goal_agent_{goal_type}_{user_id}",
        description=f"{goal_name} - {goal_type.replace('_', ' ').title()} Agent for {user_id}",
        model="gemini-3.1-flash-lite",
        tools=tools,
        instructions=personalized_instructions,
        user_id=user_id,  # Tag agent with user for multi-tenancy
        metadata={
            "goal_id": goal_id,
            "goal_type": goal_type,
            "horizon": horizon,
            "target_amount": target_amount,
            "priority": priority
        }
    )

    return agent

def get_goal_tools(goal_type: str) -> List[FunctionTool]:
    """
    Return tools relevant to a specific goal type

    Args:
        goal_type: Type of goal

    Returns:
        List of FunctionTools for this goal
    """
    # Base tools available to all goal agents
    base_tools = [
        FunctionTool(
            func=get_networth,
            description="Get current net worth (assets minus liabilities)"
        ),
        FunctionTool(
            func=get_accounts,
            description="Get breakdown of assets by account type and category"
        ),
        FunctionTool(
            func=get_income,
            description="Get monthly income breakdown by source"
        ),
        FunctionTool(
            func=calculate,
            description="Safe mathematical calculator using AST evaluation"
        ),
        FunctionTool(
            func=remember,
            description="Remember important facts about this user for future reference"
        ),
        FunctionTool(
            func=recall,
            description="Recall previously remembered facts about this user"
        )
    ]

    # Goal-specific tool additions
    goal_specific_tools = {
        "retirement": [
            FunctionTool(
                func=get_stock_quotes,
                description="Get current stock prices for portfolio monitoring"
            ),
            FunctionTool(
                func=propose_rebalance,
                description="Propose portfolio rebalancing toward retirement-ready allocation (requires approval)"
            ),
            FunctionTool(
                func=search_web,
                description="Search for retirement planning strategies and updates"
            )
        ],
        "education": [
            FunctionTool(
                func=propose_rebalance,
                description="Propose rebalancing to fund education goals (requires approval)"
            ),
            FunctionTool(
                func=calculate,
                description="Calculate education costs and funding needs"
            )
        ],
        "wealth_preservation": [
            FunctionTool(
                func=get_credit_cards,
                description="Review liabilities and debt for wealth preservation"
            ),
            FunctionTool(
                func=propose_rebalance,
                description="Propose diversification and rebalancing for preservation (requires approval)"
            ),
            FunctionTool(
                func=get_stock_quotes,
                description="Monitor portfolio concentration and risk"
            )
        ],
        "tax_optimization": [
            FunctionTool(
                func=calculate,
                description="Calculate tax savings and optimization strategies"
            ),
            FunctionTool(
                func=propose_rebalance,
                description="Propose tax-loss harvesting and optimization moves (requires approval)"
            ),
            FunctionTool(
                func=search_web,
                description="Search for current tax law changes and planning strategies"
            )
        ],
        "real_estate": [
            FunctionTool(
                func=get_accounts,
                description="Review assets available for real estate investment"
            ),
            FunctionTool(
                func=propose_rebalance,
                description="Propose rebalancing to fund real estate acquisition (requires approval)"
            ),
            FunctionTool(
                func=calculate,
                description="Calculate mortgage capacity and investment returns"
            )
        ],
        "wealth_growth": [
            FunctionTool(
                func=get_stock_quotes,
                description="Get market data for growth opportunity identification"
            ),
            FunctionTool(
                func=propose_rebalance,
                description="Propose aggressive rebalancing for growth (requires approval)"
            ),
            FunctionTool(
                func=search_web,
                description="Search for growth opportunities and market trends"
            )
        ]
    }

    # Combine base + goal-specific tools
    tools = base_tools.copy()
    tools.extend(goal_specific_tools.get(goal_type, []))

    return tools

def instantiate_goal_agents(user_id: str, goals: List[Dict[str, Any]], profile: Dict[str, Any]) -> List[LlmAgent]:
    """
    Instantiate goal agents for a user based on their active goals
    Called at session start to populate coordinator's sub_agents

    Args:
        user_id: User identifier
        goals: List of user's active goals
        profile: User's financial profile

    Returns:
        List of instantiated goal agents (capped at ~3 for latency/cost)
    """
    agents = []

    # Sort goals by priority (high > medium > low) and cap at 3 to manage cost
    sorted_goals = sorted(
        goals,
        key=lambda g: {"high": 0, "medium": 1, "low": 2}.get(g.get("priority"), 2)
    )
    active_goals = sorted_goals[:3]  # Cap at 3 goal agents per session

    for goal in active_goals:
        try:
            agent = make_goal_agent(
                goal_id=goal.get("id"),
                goal_type=goal.get("type"),
                goal_name=goal.get("name"),
                user_id=user_id,
                horizon=goal.get("horizon"),
                target_amount=goal.get("target_amount", 0),
                priority=goal.get("priority"),
                profile=profile
            )
            agents.append(agent)
        except Exception as e:
            print(f"[ERROR] Failed to instantiate goal agent {goal.get('id')}: {e}")

    print(f"[INFO] Instantiated {len(agents)} goal agents for {user_id}")
    return agents
