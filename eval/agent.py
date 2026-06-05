"""ADK eval app agent.

Exposes a `root_agent` so `adk web` can show an `eval` app. The agent
registers a single tool `run_eval_tool` that calls the existing
`wealth_agent.eval_runner.run_evals` function and returns a summary.
"""
try:
    from google.adk.agents.llm_agent import Agent as ADKAgent
except Exception:  # pragma: no cover - ADK may not be installed in all envs
    ADKAgent = None

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
if os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]

DEFAULT_MODEL = os.getenv("MODEL", "gemini-3.1-flash-lite")

def run_eval_tool(limit: Optional[int] = None) -> dict:
    """Run the local eval runner and return a brief result summary."""
    try:
        from wealth_agent.eval_runner import run_evals
    except Exception as e:
        return {"status": "error", "error": str(e)}

    try:
        n = run_evals()
        return {"status": "ok", "ran": n, "results": "eval/results.jsonl"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


if ADKAgent is not None:
    root_agent = ADKAgent(
        model=DEFAULT_MODEL,
        name="eval",
        description="Eval runner for WealthTrack golden dataset",
        instruction=("Run the eval runner tool to execute golden examples "
                     "and produce results.jsonl"),
        tools=[run_eval_tool],
    )
else:
    root_agent = None
