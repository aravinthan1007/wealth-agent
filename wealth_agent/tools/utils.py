"""Utility helpers: safe math expression evaluator used by the agent.

Implements a small, safe evaluator based on Python's AST that supports numeric
constants, binary operators (+, -, *, /, **, //, %), and unary +/-. No function
calls or name lookups are allowed.
"""
import ast
import operator
from typing import Any

_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
}

_UNARY_OPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def _eval(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _eval(node.body)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return float(node.value)
        raise ValueError("Only numeric constants are allowed")
    if isinstance(node, ast.Num):  # type: ignore - for older Pythons
        return float(node.n)
    if isinstance(node, ast.BinOp):
        left = _eval(node.left)
        right = _eval(node.right)
        op = type(node.op)
        if op in _OPS:
            return _OPS[op](left, right)
        raise ValueError(f"Unsupported binary operator: {op}")
    if isinstance(node, ast.UnaryOp):
        op = type(node.op)
        if op in _UNARY_OPS:
            return _UNARY_OPS[op](_eval(node.operand))
        raise ValueError(f"Unsupported unary operator: {op}")
    raise ValueError(f"Unsupported expression: {node!r}")


def calculate(expression: str) -> float:
    """Safely evaluate a simple arithmetic expression and return a float."""
    node = ast.parse(expression, mode="eval")
    return float(_eval(node))


__all__ = ["calculate"]
