"""Aurelius Data Models - Pydantic entities for type safety.

All core data structures: Account, Goal, Proposal, Engagement, Profile, etc.
Used by agent, tools, and onboarding for data validation and serialization.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class Profile(BaseModel):
    """User wealth profile."""
    risk_tolerance: str = Field(..., description="conservative, moderate, aggressive")
    retirement_age: int = Field(65, description="Target retirement age")
    goals: List[str] = Field(default_factory=list, description="User wealth goals")
    full_name: Optional[str] = None
    residency: Optional[str] = None
    citizenship: Optional[str] = None


class Account(BaseModel):
    """Financial account."""
    name: str
    type: str  # checking, savings, investment, credit_card, loan, etc.
    balance: float
    limit: Optional[float] = None
    currency: str = "USD"


class Asset(BaseModel):
    """Physical or financial asset."""
    name: str
    category: str  # real_estate, vehicle, collectible, etc.
    value: float
    acquisition_date: Optional[str] = None


class Liability(BaseModel):
    """Financial liability/debt."""
    name: str
    principal: float
    interest_rate: float
    monthly_payment: Optional[float] = None
    due_date: Optional[str] = None


class IncomeSource(BaseModel):
    """Income stream."""
    source: str
    amount_monthly: float
    frequency: str = "monthly"


class Expense(BaseModel):
    """Expense record."""
    date: str
    category: str
    amount: float
    description: Optional[str] = None


class Goal(BaseModel):
    """Wealth goal."""
    name: str
    target_amount: float
    target_date: Optional[str] = None
    priority: str = "medium"  # low, medium, high
    status: str = "active"  # active, completed, paused


class Proposal(BaseModel):
    """Action proposal (rebalance, engagement, etc)."""
    type: str  # rebalance, engagement, service, etc.
    title: str
    description: str
    details: Dict[str, Any]
    requires_approval: bool = True
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class Engagement(BaseModel):
    """Service engagement."""
    type: str  # concierge, advisor, tax, legal, etc.
    service: str
    provider: Optional[str] = None
    scheduled_date: Optional[str] = None
    status: str = "proposed"  # proposed, confirmed, completed
    cost: Optional[float] = None


class Session(BaseModel):
    """User session for tracking."""
    session_id: str
    user_id: str
    app_name: str
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TraceEvent(BaseModel):
    """Trace event for execution tracing."""
    event_id: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    event_type: str  # function_call, tool_call, agent_decision, etc.
    agent_name: str
    tool_name: Optional[str] = None
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    latency_ms: Optional[int] = None
    status: str = "success"  # success, error, pending


__all__ = [
    "Profile",
    "Account",
    "Asset",
    "Liability",
    "IncomeSource",
    "Expense",
    "Goal",
    "Proposal",
    "Engagement",
    "Session",
    "TraceEvent",
]
