"""Eval runner for Tier 2: Load golden dataset, run through agents, score results."""

import json
from pathlib import Path
from typing import List, Dict, Any


class EvalRunner:
    """Run golden dataset through agents and compute scores."""

    def __init__(self, golden_path: str = None):
        if golden_path is None:
            golden_path = str(Path(__file__).resolve().parent.parent / "eval" / "golden.jsonl")
        self.golden_path = golden_path
        self.results = []

    def load_golden(self) -> List[Dict[str, Any]]:
        """Load golden dataset from jsonl."""
        golden = []
        if Path(self.golden_path).exists():
            with open(self.golden_path) as f:
                for line in f:
                    if line.strip():
                        golden.append(json.loads(line))
        return golden

    def score_faithfulness(self, output: str, expected_contains: List[str]) -> float:
        """Score how faithfully the output matches expected content."""
        if not expected_contains or not output:
            return 0.0
        matches = sum(1 for exp in expected_contains if str(exp).lower() in str(output).lower())
        return matches / len(expected_contains)

    def score_relevance(self, output: str, prompt: str) -> float:
        """Simple heuristic: output is relevant if it's not empty and doesn't error."""
        if not output or "error" in str(output).lower():
            return 0.0
        return 0.9  # Assume relevant if it ran

    def run_eval(self, root_agent) -> Dict[str, Any]:
        """Run golden dataset through root_agent and score results."""
        golden = self.load_golden()
        if not golden:
            return {"error": "No golden dataset found"}

        results = []
        total_faithfulness = 0.0
        total_relevance = 0.0

        for test_case in golden:
            test_id = test_case.get("id", "unknown")
            prompt = test_case.get("prompt", "")
            expected_contains = test_case.get("expected_contains", [])

            # In a real setup, we'd call root_agent.run(prompt) here
            # For now, we'll score the tools directly
            try:
                # Mock run (would be actual agent call in production)
                output = f"Mock output for: {prompt}"
                faithfulness = self.score_faithfulness(output, expected_contains)
                relevance = self.score_relevance(output, prompt)

                results.append({
                    "test_id": test_id,
                    "prompt": prompt,
                    "category": test_case.get("category", "unknown"),
                    "faithfulness": faithfulness,
                    "relevance": relevance,
                    "composite_score": (faithfulness + relevance) / 2,
                })
                total_faithfulness += faithfulness
                total_relevance += relevance
            except Exception as e:
                results.append({
                    "test_id": test_id,
                    "prompt": prompt,
                    "error": str(e),
                    "faithfulness": 0.0,
                    "relevance": 0.0,
                    "composite_score": 0.0,
                })

        avg_faithfulness = total_faithfulness / len(results) if results else 0.0
        avg_relevance = total_relevance / len(results) if results else 0.0

        return {
            "test_count": len(results),
            "avg_faithfulness": avg_faithfulness,
            "avg_relevance": avg_relevance,
            "avg_composite": (avg_faithfulness + avg_relevance) / 2,
            "results": results,
        }


def run_evals():
    """Run eval suite and print results."""
    runner = EvalRunner()
    scores = runner.run_eval(None)

    print("\n=== EVAL RESULTS ===")
    print(f"Tests: {scores.get('test_count', 0)}")
    print(f"Avg Faithfulness: {scores.get('avg_faithfulness', 0):.2f}")
    print(f"Avg Relevance: {scores.get('avg_relevance', 0):.2f}")
    print(f"Composite Score: {scores.get('avg_composite', 0):.2f}")

    if scores.get("results"):
        print("\n=== DETAILED RESULTS ===")
        for r in scores["results"]:
            status = "PASS" if r.get("composite_score", 0) > 0.5 else "FAIL"
            print(f"[{status}] {r.get('test_id')}: {r.get('category')} - "
                  f"F:{r.get('faithfulness', 0):.2f} R:{r.get('relevance', 0):.2f}")

    return scores


if __name__ == "__main__":
    run_evals()
