import os

paths = [
    r"C:\Program Files\Graphviz\bin",
    r"C:\Program Files (x86)\Graphviz\bin",
    r"C:\ProgramData\chocolatey\lib\graphviz\tools",
    r"C:\ProgramData\chocolatey\lib",
    r"C:\Program Files",
    r"C:\Users\%USERNAME%\AppData\Local\Programs",
]

found = []
for base in paths:
    for root, dirs, files in os.walk(base):
        if 'dot.exe' in files:
            found.append(os.path.join(root, 'dot.exe'))
        # limit search depth by skipping deep dirs
        if len(root) > len(base) + 200:
            continue

if found:
    print('Found dot.exe at:')
    for f in found:
        print(f)
else:
    print('dot.exe not found under common locations')
