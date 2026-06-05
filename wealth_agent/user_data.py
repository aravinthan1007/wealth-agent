"""User data management - single source of truth.

All tools and API endpoints read/write through this module.
User data stored as JSON in wealth_agent/data/users/{user_id}/data.json
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional

DATA_DIR = Path(__file__).parent / "data" / "users"


def ensure_user_dir(user_id: str) -> Path:
    """Create user data directory if it doesn't exist."""
    user_dir = DATA_DIR / user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


def get_user_data_path(user_id: str) -> Path:
    """Get path to user's data.json file."""
    return ensure_user_dir(user_id) / "data.json"


def get_user_data(user_id: str) -> Dict[str, Any]:
    """Load user's financial data (or return empty template)."""
    data_path = get_user_data_path(user_id)

    if data_path.exists():
        try:
            with open(data_path, 'r') as f:
                return json.load(f)
        except:
            pass

    # Return empty template
    return {
        "assets": {},
        "liabilities": {},
        "expenses": [],
        "income": [],
        "credit_cards": [],
        "profile": {
            "risk_tolerance": "moderate",
            "retirement_age": 65,
            "goals": []
        }
    }


def save_user_data(user_id: str, data: Dict[str, Any]) -> bool:
    """Save user's financial data to JSON file."""
    try:
        data_path = get_user_data_path(user_id)
        with open(data_path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving user data: {e}")
        return False


def get_networth(user_id: str) -> float:
    """Calculate net worth from user data."""
    data = get_user_data(user_id)

    # Sum assets
    assets = 0
    if "assets" in data:
        for key, value in data["assets"].items():
            if isinstance(value, dict):
                assets += sum(value.values())
            else:
                assets += value

    # Sum liabilities
    liabilities = 0
    if "liabilities" in data:
        liabilities = sum(data["liabilities"].values())

    return assets - liabilities


def get_expenses_month(user_id: str, month: str = None) -> float:
    """Get expenses for a month (YYYY-MM format)."""
    data = get_user_data(user_id)

    if not month or "expenses" not in data:
        # Return total monthly expenses (average)
        if data.get("expenses"):
            return sum(e.get("amount", 0) for e in data["expenses"]) / max(len(data["expenses"]), 1)
        return 0.0

    # Filter by month
    month_total = 0
    for expense in data.get("expenses", []):
        date = expense.get("date", "")
        if date.startswith(month):
            month_total += expense.get("amount", 0)

    return float(month_total)


def get_accounts(user_id: str) -> Dict[str, Any]:
    """Get all accounts grouped by type."""
    data = get_user_data(user_id)
    return data.get("assets", {})


def get_income(user_id: str) -> Dict[str, Any]:
    """Get income sources."""
    data = get_user_data(user_id)
    total = sum(i.get("amount_monthly", 0) for i in data.get("income", []))
    return {
        "total_monthly": total,
        "sources": data.get("income", [])
    }


def get_credit_cards(user_id: str) -> list:
    """Get credit cards."""
    data = get_user_data(user_id)
    return data.get("credit_cards", [])


def get_profile(user_id: str) -> Dict[str, Any]:
    """Get user profile."""
    data = get_user_data(user_id)
    return data.get("profile", {})


__all__ = [
    "get_user_data",
    "save_user_data",
    "get_networth",
    "get_expenses_month",
    "get_accounts",
    "get_income",
    "get_credit_cards",
    "get_profile",
]
