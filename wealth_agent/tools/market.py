"""Market tools: lightweight wrappers and mock fallbacks.

These are intentionally small to keep Tier 0 local-only. A live Yahoo
provider is used if `yfinance` is installed; otherwise a deterministic
mock price is returned and labeled as `source: mock`.
"""
from typing import List, Dict, Any

try:
    import yfinance as yf  # optional dependency
except Exception:
    yf = None


def get_stock_quotes(symbols: List[str], source: str = "yahoo") -> Dict[str, Dict[str, Any]]:
    """Return a mapping symbol -> {price, source}.

    If `yfinance` isn't available or a price lookup fails, return a labeled
    mock price so the agent can continue working offline.
    """
    if yf is not None and source == "yahoo":
        try:
            tickers = yf.Tickers(" ".join(symbols))
            out: Dict[str, Dict[str, Any]] = {}
            for s in symbols:
                try:
                    df = tickers.tickers[s].history(period="1d")
                    if not df.empty:
                        price = float(df["Close"].iloc[-1])
                        out[s] = {"price": price, "source": "yahoo"}
                        continue
                except Exception:
                    pass
                # fallback for this symbol
                out[s] = {"price": 0.0, "source": "mock"}
            return out
        except Exception:
            pass

    # deterministic mock fallback
    out = {}
    for s in symbols:
        price = float((abs(hash(s)) % 10000) / 100.0) + 1.0
        out[s] = {"price": price, "source": "mock"}
    return out


def fetch_url(url: str) -> str:
    try:
        import requests

        r = requests.get(url, timeout=5)
        r.raise_for_status()
        return r.text
    except Exception:
        from urllib.request import urlopen

        with urlopen(url, timeout=5) as resp:
            return resp.read().decode("utf-8", errors="ignore")


def search_web(query: str, num_results: int = 3) -> List[Dict[str, str]]:
    # Placeholder search results; intended to be wired to a real search tool.
    return [
        {"title": f"Result {i+1} for {query}", "url": f"https://example.com/search?q={query}&i={i}"}
        for i in range(num_results)
    ]


__all__ = ["get_stock_quotes", "fetch_url", "search_web"]
