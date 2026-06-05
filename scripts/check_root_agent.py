import os
import sys

# Ensure repo root importable
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

print('ENV MODEL=', os.getenv('MODEL'))
try:
    import wealth_agent.agent as wa
    print('has root_agent attr:', hasattr(wa, 'root_agent'))
    ra = getattr(wa, 'root_agent', None)
    print('root_agent type:', type(ra))
except Exception as e:
    print('wealth_agent import error', e)
    ra = None
try:
    from google.adk.agents import BaseAgent
    print('is BaseAgent:', isinstance(ra, BaseAgent))
except Exception as e:
    print('BaseAgent import error:', e)
try:
    from google.adk.agents.llm_agent import Agent as LlmAgent
    print('is LlmAgent:', isinstance(ra, LlmAgent))
except Exception as e:
    print('LlmAgent import error:', e)
