import importlib
import traceback
import os
import sys

# Ensure repo root is on sys.path so `wealth_agent` package can be imported
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

try:
    m = importlib.import_module('wealth_agent.agent')
    root = getattr(m, 'root_agent', None)
    print('root_agent type:', type(root))
    if root is None:
        print('root_agent is None')
    else:
        tools = getattr(root, 'tools', None)
        print('tools attribute type:', type(tools))
        try:
            if tools is None:
                # attempt other common accessors
                alt = getattr(root, 'list_tools', None) or getattr(root, 'tool_names', None)
                print('alternate tool accessor:', alt)
            else:
                print('tools preview (names):', list(tools))
        except Exception as e:
            print('error listing tools:', e)
except Exception:
    traceback.print_exc()
