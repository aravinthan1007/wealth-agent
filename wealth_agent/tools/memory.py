"""Simple per-user memory store persisted to `data/memories.json`.

This is a lightweight local store used for Tier 0 and testing. It is not
intended to be production grade; later tiers will replace it with Firestore
or ADK session memory.
"""
from pathlib import Path
import json
from typing import Any

_STORE_PATH = Path(__file__).resolve().parents[1] / "data" / "memories.json"


def _load() -> dict:
    if _STORE_PATH.exists():
        try:
            with open(_STORE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save(data: dict) -> None:
    _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def remember(user_id: str, key: str, value: Any) -> bool:
    data = _load()
    user = data.setdefault(str(user_id), {})
    user[key] = value
    _save(data)
    return True


def recall(user_id: str, key: str):
    data = _load()
    return data.get(str(user_id), {}).get(key)


__all__ = ["remember", "recall"]
