"""Finance tools (Tier 0): pure-python helpers used by the agent.

These are intentionally simple, deterministic, and testable without external
dependencies so Tier 0 can run fully locally.

Tools read from user_data (single source of truth: wealth_agent/data/users/{user_id}/data.json).
Backward compatibility maintained for tests using data_path / data dict.
"""
from pathlib import Path
import json
from typing import Any, Dict, List, Optional

from .. import user_data


def _data_path():
    return Path(__file__).resolve().parents[1] / "data" / "sample_data.json"


def _load_data(path: str = None) -> Dict[str, Any]:
    p = Path(path) if path else _data_path()
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def _sum_recursive(obj: Any) -> float:
    total = 0.0
    if isinstance(obj, dict):
        for v in obj.values():
            total += _sum_recursive(v)
    elif isinstance(obj, list):
        for item in obj:
            total += _sum_recursive(item)
    elif isinstance(obj, (int, float)):
        total += float(obj)
    return total


def get_networth(user_id: Optional[str] = None, data: Dict[str, Any] = None, data_path: str = None) -> float:
    """Return assets minus liabilities from user data, provided dict, or sample file.

    Priority: user_id (user_data store) > data dict > data_path > sample_data.json
    """
    if user_id:
        return user_data.get_networth(user_id)
    if data is None:
        data = _load_data(data_path)
    assets = data.get("assets", {})
    liabilities = data.get("liabilities", {})
    total_assets = _sum_recursive(assets)
    total_liabilities = _sum_recursive(liabilities)
    return total_assets - total_liabilities


def get_expenses(user_id: Optional[str] = None, month: str = None, by_category: bool = False, data: Dict[str, Any] = None, data_path: str = None):
    """Aggregate expenses. If `month` provided (YYYY-MM), filter to that month.

    Priority: user_id (user_data store) > data dict > data_path > sample_data.json
    """
    if user_id:
        if by_category:
            # user_data doesn't support by_category yet; fall through to dict logic
            data = user_data.get_user_data(user_id)
        else:
            return user_data.get_expenses_month(user_id, month)
    if data is None:
        data = _load_data(data_path)
    expenses = data.get("expenses", [])
    total = 0.0
    categories: Dict[str, float] = {}
    for e in expenses:
        amt = float(e.get("amount", 0))
        date = e.get("date", "")
        if month and not date.startswith(month):
            continue
        total += amt
        if by_category:
            categories.setdefault(e.get("category", "uncategorized"), 0.0)
            categories[e.get("category", "uncategorized")] += amt
    return categories if by_category else total


def get_credit_cards(user_id: Optional[str] = None, data: Dict[str, Any] = None, data_path: str = None) -> List[Dict[str, Any]]:
    """Get credit cards from user data, provided dict, or sample file.

    Priority: user_id (user_data store) > data dict > data_path > sample_data.json
    """
    if user_id:
        return user_data.get_credit_cards(user_id)
    if data is None:
        data = _load_data(data_path)
    return data.get("credit_cards", [])


def get_income(user_id: Optional[str] = None, period: str = "monthly", data: Dict[str, Any] = None, data_path: str = None) -> Dict[str, Any]:
    """Get income sources from user data, provided dict, or sample file.

    Priority: user_id (user_data store) > data dict > data_path > sample_data.json
    """
    if user_id:
        income_data = user_data.get_income(user_id)
        if period == "annual":
            return {
                "total_annual": income_data["total_monthly"] * 12,
                "breakdown": income_data["sources"]
            }
        return income_data
    if data is None:
        data = _load_data(data_path)
    incomes = data.get("income", [])
    total_monthly = sum(float(i.get("amount_monthly", 0)) for i in incomes)
    if period == "monthly":
        return {"total_monthly": total_monthly, "breakdown": incomes}
    if period == "annual":
        return {"total_annual": total_monthly * 12, "breakdown": incomes}
    return {"total_monthly": total_monthly, "breakdown": incomes}


def get_profile(user_id: Optional[str] = None, data: Dict[str, Any] = None, data_path: str = None) -> Dict[str, Any]:
    """Get profile from user data, provided dict, or sample file.

    Priority: user_id (user_data store) > data dict > data_path > sample_data.json
    """
    if user_id:
        return user_data.get_profile(user_id)
    if data is None:
        data = _load_data(data_path)
    return data.get("profile", {})


def get_accounts(user_id: Optional[str] = None, asset_class: str = None, data: Dict[str, Any] = None, data_path: str = None) -> Dict[str, Any]:
    """Return accounts grouped by asset class (checking, savings, investments, etc.).

    Priority: user_id (user_data store) > data dict > data_path > sample_data.json
    """
    if user_id:
        accounts = user_data.get_accounts(user_id)
    else:
        if data is None:
            data = _load_data(data_path)
        accounts = data.get("assets", {})

    if asset_class:
        return {asset_class: accounts.get(asset_class, {})}
    return accounts


__all__ = [
    "get_networth",
    "get_expenses",
    "get_credit_cards",
    "get_income",
    "get_profile",
    "get_accounts",
]
