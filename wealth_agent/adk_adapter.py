"""Optional ADK adapter (best-effort).

This module attempts to detect an installed Google ADK Python package and,
if available, upgrade a local `RootAgent` instance into an ADK-backed agent
by registering the existing pure-python tools as ADK-callable functions.

The implementation is intentionally defensive: it does nothing if ADK is not
installed and makes only best-effort calls when library APIs vary between
versions. Install `google-adk` and consult https://adk.dev/get-started/python/
for the official usage patterns — this adapter is a thin shim so development
can continue locally without ADK present.
"""
from typing import Any
import importlib
import traceback


def _find_adk_module():
    candidates = [
        "google.adk",
        "google_adk",
        "google.adk.agent",
        "google_adk.agent",
    ]
    for name in candidates:
        try:
            mod = importlib.import_module(name)
            return mod
        except Exception:
            continue
    return None


def is_adk_available() -> bool:
    return _find_adk_module() is not None


def upgrade_agent_to_adk(agent: Any) -> Any:
    """Attempt to upgrade the given `agent` to an ADK-backed agent.

    Returns the ADK agent if successful, otherwise returns the original
    `agent`. This function makes no breaking assumptions about the ADK API
    surface and will silently fall back if anything fails.
    """
    mod = _find_adk_module()
    if mod is None:
        return agent

    try:
        # Try to find an Agent class or factory in the imported module.
        AgentClass = getattr(mod, "Agent", None) or getattr(mod, "agent", None)
        if AgentClass is None:
            # Some ADK releases may expose a submodule with agent types
            sub = getattr(mod, "agents", None)
            if sub is not None:
                AgentClass = getattr(sub, "Agent", None) or getattr(sub, "AgentClient", None)

        if AgentClass is None:
            # Unable to find a constructible Agent class — give up gracefully.
            return agent

        # Try to instantiate with no args (best-effort). If this fails,
        # attempt a common fallback by supplying a `name` argument which
        # recent ADK LlmAgent models require (Pydantic validation error
        # seen when `name` is missing). If that still fails, give up
        # and return the original `agent`.
        try:
            adk_agent = AgentClass()
        except Exception:
            try:
                # Some ADK LlmAgent models validate `name` as a Python
                # identifier — sanitize a default value to be safe.
                import re

                desired_name = "wealth-agent"
                safe_name = re.sub(r"[^0-9a-zA-Z_]", "_", desired_name)
                adk_agent = AgentClass(name=safe_name)
            except Exception:
                # Give debugging info for developers, but continue gracefully
                traceback.print_exc()
                return agent

        # Try to register existing tools on the ADK agent using commonly
        # named registration methods. Silent-ignore failures per-tool.
        register = (
            getattr(adk_agent, "register_tool", None)
            or getattr(adk_agent, "register", None)
            or getattr(adk_agent, "add_tool", None)
        )
        if register and hasattr(agent, "tools"):
            for name, func in getattr(agent, "tools", {}).items():
                try:
                    register(name, func)
                except Exception:
                    # Some ADK APIs require typed wrappers; skip if registration fails
                    continue

        return adk_agent
    except Exception:
        # Be explicit in logs for developers but do not raise.
        traceback.print_exc()
        return agent


__all__ = ["is_adk_available", "upgrade_agent_to_adk"]
