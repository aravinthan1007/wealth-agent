"""Minimal ADK agent for the `scripts` helper folder.

This prevents the ADK web UI from treating `scripts/` as a broken app.
It registers a no-op `health` tool to surface a valid `root_agent`.
"""
try:
    from google.adk.agents.llm_agent import Agent as ADKAgent
except Exception:  # pragma: no cover
    ADKAgent = None

import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
if os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]

DEFAULT_MODEL = os.getenv("MODEL", "gemini-3.1-flash-lite")


def health() -> dict:
    return {"status": "ok", "note": "scripts helper"}


if ADKAgent is not None:
    root_agent = ADKAgent(
        model=DEFAULT_MODEL,
        name="scripts",
        description="Helper scripts app (no-op)",
        instruction="Utility scripts app used during development.",
        tools=[health],
    )
else:
    root_agent = None
