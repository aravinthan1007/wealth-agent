import importlib, sys, os
# Ensure repo root is on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

apps = ['eval.agent', 'scripts.agent', 'wealth_agent.agent']
for modname in apps:
    try:
        m = importlib.import_module(modname)
        print(modname, '-> root_agent type:', type(getattr(m, 'root_agent', None)))
    except Exception as e:
        print(modname, 'import error', e)
