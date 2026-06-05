"""Phoenix MCP query tool (best-effort HTTP wrapper).

This is a lightweight helper that tries to query a locally-running Phoenix MCP
server (commonly launched via `docker run -p 6006:6006 arizephoenix/phoenix`).
If the server or network is unavailable this function returns a helpful
diagnostic dictionary instead of raising.
"""
import os
import json
from typing import Any, Dict


def query_traces(query: str, limit: int = 10, phoenix_url: str | None = None, api_key: str | None = None) -> Dict[str, Any]:
    """Query Phoenix MCP and return parsed JSON results or an error dict.

    The function will try a few likely endpoints on the provided `phoenix_url`.
    """
    try:
        import requests
    except Exception:
        requests = None

    phoenix_url = phoenix_url or os.environ.get("PHOENIX_MCP_URL", "http://localhost:6006")
    candidates = [
        f"{phoenix_url}/mcp/query",
        f"{phoenix_url}/api/mcp/query",
        f"{phoenix_url}/api/v1/mcp/query",
    ]

    payload = {"query": query, "limit": limit}

    last_err = None
    for url in candidates:
        try:
            if requests:
                headers = {}
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"
                r = requests.post(url, json=payload, headers=headers, timeout=5)
                if r.ok:
                    try:
                        return r.json()
                    except Exception:
                        return {"error": "invalid_json", "text": r.text}
            else:
                # Minimal urllib fallback (POST with JSON body)
                from urllib.request import Request, urlopen
                req = Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
                with urlopen(req, timeout=5) as resp:
                    b = resp.read()
                    return json.loads(b.decode("utf-8"))
        except Exception as e:
            last_err = e
            continue

    return {"error": "mcp_unavailable", "details": str(last_err)}


__all__ = ["query_traces"]
