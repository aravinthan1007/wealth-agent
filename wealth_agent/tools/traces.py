"""Phoenix MCP trace query tool (Tier 2).

Allows Aurelius to self-reflect on past runs by querying Phoenix traces.
This integrates Phoenix MCP for trace introspection.
"""
from typing import List, Dict, Any
import json


def query_traces(
    filter_by_agent: str = None,
    filter_by_tool: str = None,
    limit: int = 10,
) -> Dict[str, Any]:
    """Query traces from Phoenix via MCP.

    In production, this connects to Phoenix Cloud or local Phoenix instance.
    For local dev, returns mock trace data to demonstrate the interface.

    Args:
        filter_by_agent: Filter traces by agent name (e.g., 'aurelius', 'markets_steward')
        filter_by_tool: Filter traces by tool name (e.g., 'get_networth')
        limit: Max number of traces to return

    Returns:
        Dict with trace summaries, latencies, and faithfulness scores.
    """
    # Mock traces for local dev (Tier 2 without Phoenix Cloud)
    mock_traces = [
        {
            "trace_id": "trace-001",
            "agent": "aurelius",
            "tool": "get_networth",
            "input": "What is my net worth?",
            "output": "-107000.0",
            "latency_ms": 245,
            "timestamp": "2026-06-04T15:40:00Z",
            "faithfulness_score": 0.95,
        },
        {
            "trace_id": "trace-002",
            "agent": "markets_steward",
            "tool": "get_stock_quotes",
            "input": "What is the price of AAPL?",
            "output": '{"AAPL": {"price": 42.0, "source": "mock"}}',
            "latency_ms": 312,
            "timestamp": "2026-06-04T15:40:30Z",
            "faithfulness_score": 0.88,
        },
        {
            "trace_id": "trace-003",
            "agent": "estate_steward",
            "tool": "get_income",
            "input": "What is my monthly income?",
            "output": '{"total_monthly": 5200.0, "breakdown": [...]}',
            "latency_ms": 198,
            "timestamp": "2026-06-04T15:41:00Z",
            "faithfulness_score": 0.99,
        },
    ]

    # Filter traces
    results = mock_traces
    if filter_by_agent:
        results = [t for t in results if t["agent"] == filter_by_agent]
    if filter_by_tool:
        results = [t for t in results if t["tool"] == filter_by_tool]
    results = results[:limit]

    return {
        "traces": results,
        "count": len(results),
        "avg_latency_ms": sum(t["latency_ms"] for t in results) / len(results) if results else 0,
        "avg_faithfulness": sum(t["faithfulness_score"] for t in results) / len(results) if results else 0,
    }


__all__ = ["query_traces"]
