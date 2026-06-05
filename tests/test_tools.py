import pytest

from wealth_agent.tools.utils import calculate
from wealth_agent.tools.finance import get_networth, get_expenses
from wealth_agent.tools.actions import propose_rebalance


def test_calculate_basic():
    assert calculate("1+2*3") == 7.0


def test_get_networth_sample():
    nw = get_networth()
    assert nw == -107000.0


def test_get_expenses_month():
    total = get_expenses(month="2026-05")
    assert total == 1800.0


def test_propose_rebalance_simple():
    from google.adk.events import RequestInput

    portfolio = {"AAPL": 1000.0, "BND": 1000.0}
    target = {"AAPL": 0.6, "BND": 0.4}
    result = propose_rebalance(portfolio, target)

    # Result is a RequestInput that pauses for approval
    assert isinstance(result, RequestInput)
    assert "Approve" in result.message

    # Payload contains the proposal
    proposal = result.payload["proposal"]
    actions = {p["symbol"]: p for p in proposal}
    assert actions["AAPL"]["action"] == "buy"
    assert round(actions["AAPL"]["amount"], 2) == 200.0
    assert actions["BND"]["action"] == "sell"
    assert round(actions["BND"]["amount"], 2) == 200.0
