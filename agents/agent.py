import os
import sys

from dotenv import load_dotenv

# Ensure repo root importable.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

load_dotenv(os.path.join(ROOT, ".env"), override=False)
if os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]

DEFAULT_MODEL = os.getenv("MODEL", "gemini-3.1-flash-lite")

try:
    from google.adk.agents.llm_agent import Agent as ADKAgent
except Exception:
    ADKAgent = None

try:
    from wealth_agent.agent import root_agent as wealth_root_agent
except Exception:
    wealth_root_agent = None

try:
    from eval.agent import root_agent as eval_root_agent
except Exception:
    eval_root_agent = None

try:
    from scripts.agent import root_agent as scripts_root_agent
except Exception:
    scripts_root_agent = None


def list_available_apps() -> dict:
    apps = []
    if wealth_root_agent is not None:
        apps.append("wealth_agent")
    if eval_root_agent is not None:
        apps.append("eval")
    if scripts_root_agent is not None:
        apps.append("scripts")
    return {"apps": apps}


if ADKAgent is not None:
    sub_agents = [a for a in [wealth_root_agent, eval_root_agent, scripts_root_agent] if a is not None]
    root_agent = ADKAgent(
        model=DEFAULT_MODEL,
        name="agents",
        description="Top-level ADK app wrapper for Wealth Management workspace",
        instruction=(
            "You are a router for this workspace. Use tools to inspect available apps. "
            "Delegate to sub-agents when available."
        ),
        tools=[list_available_apps],
        sub_agents=sub_agents,
    )
else:
    root_agent = None
