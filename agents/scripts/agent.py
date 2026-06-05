import os
import sys

# Ensure repo root on sys.path so we can import the real scripts agent
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

try:
    from scripts.agent import root_agent  # type: ignore
except Exception:
    root_agent = None
