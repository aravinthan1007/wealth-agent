import requests

endpoints = [
    'http://127.0.0.1:8000/dev/build_graph_image/wealth_agent',
    'http://127.0.0.1:8000/dev/build_graph_image/eval',
    'http://127.0.0.1:8000/dev/build_graph_image/scripts',
    'http://127.0.0.1:8000/dev/build_graph/wealth_agent',
    'http://127.0.0.1:8000/dev/build_graph/eval',
    'http://127.0.0.1:8000/dev/build_graph/scripts',
]

for url in endpoints:
    try:
        r = requests.get(url, timeout=10)
        print(url, r.status_code, r.headers.get('Content-Type'), len(r.content))
    except Exception as e:
        print(url, 'error', e)
