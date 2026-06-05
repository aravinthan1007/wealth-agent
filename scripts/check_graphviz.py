import shutil
from subprocess import Popen, PIPE
import os

print('cwd:', os.path.abspath(os.getcwd()))
dot = shutil.which('dot')
print('dot path:', dot)
if dot:
    try:
        p = Popen(['dot', '-V'], stdout=PIPE, stderr=PIPE)
        out, err = p.communicate(timeout=5)
        print('dot exitcode:', p.returncode)
        print('dot stdout:', out.decode('utf-8', errors='ignore'))
        print('dot stderr:', err.decode('utf-8', errors='ignore'))
    except Exception as e:
        print('dot invocation error:', e)
else:
    print('dot not found in PATH')

try:
    import graphviz
    print('python package graphviz version:', getattr(graphviz, '__version__', 'unknown'))
except Exception as e:
    print('import graphviz error:', e)
