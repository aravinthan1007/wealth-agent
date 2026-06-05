"""Simple eval runner to iterate the golden dataset and collect responses.

This runner is intentionally minimal: it runs the local `create_agent()` and
records the agent output for each example in `eval/results.jsonl`.
"""
import json
from pathlib import Path
from typing import Any

from .agent import create_agent


def run_evals(golden_path: str = None, out_path: str = None) -> int:
    golden_path = golden_path or Path(__file__).resolve().parents[1] / "eval" / "golden.jsonl"
    out_path = out_path or Path(__file__).resolve().parents[1] / "eval" / "results.jsonl"

    agent = create_agent()
    results = []
    with open(golden_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            ex = json.loads(line)
            prompt = ex.get("prompt")
            resp = agent.handle(prompt)
            record = {"id": ex.get("id"), "prompt": prompt, "response": resp, "expected": ex.get("expected")}
            results.append(record)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r))
            f.write("\n")

    return len(results)


if __name__ == "__main__":
    n = run_evals()
    print(f"Ran {n} evals; wrote eval/results.jsonl")
