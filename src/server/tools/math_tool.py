"""Deterministic arithmetic evaluator over a whitelisted AST subset.

Never uses ``eval()``, ``exec()``, or ``numexpr``: the input is parsed with
``ast.parse`` and evaluated by an explicit recursive walker that only handles
whitelisted node types. Anything else raises :class:`UnsafeExpression` and is
returned to the caller as a formatted error string.
"""

from __future__ import annotations

import ast
import math
import operator
from collections.abc import Callable

_MAX_POW_EXPONENT = 1_000

_BIN_OPS: dict[type, Callable[[float, float], float]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
}

_UNARY_OPS: dict[type, Callable[[float], float]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

_FUNCTIONS: dict[str, Callable] = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
}

_MATH_FUNCTIONS: dict[str, Callable] = {
    name: getattr(math, name)
    for name in (
        "sqrt", "ceil", "floor", "exp", "log", "log2", "log10",
        "sin", "cos", "tan", "asin", "acos", "atan", "hypot", "gcd",
    )
}

_CONSTANTS: dict[str, float] = {"pi": math.pi, "e": math.e, "tau": math.tau}


class UnsafeExpression(ValueError):
    """Raised when an expression contains a non-whitelisted AST element."""


def _resolve_callable(node: ast.AST) -> Callable:
    if isinstance(node, ast.Name) and node.id in _FUNCTIONS:
        return _FUNCTIONS[node.id]
    if (
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "math"
        and node.attr in _MATH_FUNCTIONS
    ):
        return _MATH_FUNCTIONS[node.attr]
    raise UnsafeExpression("only whitelisted functions may be called")


def _evaluate(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _evaluate(node.body)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise UnsafeExpression("only numeric literals are allowed")
        return node.value
    if isinstance(node, ast.BinOp):
        op = _BIN_OPS.get(type(node.op))
        if op is None:
            raise UnsafeExpression(f"operator {type(node.op).__name__} is not allowed")
        right = _evaluate(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > _MAX_POW_EXPONENT:
            raise UnsafeExpression("exponent too large")
        return op(_evaluate(node.left), right)
    if isinstance(node, ast.UnaryOp):
        op = _UNARY_OPS.get(type(node.op))
        if op is None:
            raise UnsafeExpression(f"operator {type(node.op).__name__} is not allowed")
        return op(_evaluate(node.operand))
    if isinstance(node, ast.Call):
        if node.keywords:
            raise UnsafeExpression("keyword arguments are not allowed")
        func = _resolve_callable(node.func)
        return func(*(_evaluate(arg) for arg in node.args))
    if isinstance(node, ast.Name):
        if node.id in _CONSTANTS:
            return _CONSTANTS[node.id]
        raise UnsafeExpression(f"name '{node.id}' is not allowed")
    if isinstance(node, ast.Attribute):
        if (
            isinstance(node.value, ast.Name)
            and node.value.id == "math"
            and node.attr in _CONSTANTS
        ):
            return _CONSTANTS[node.attr]
        raise UnsafeExpression(f"attribute '{node.attr}' is not allowed")
    raise UnsafeExpression(f"expression element {type(node).__name__} is not allowed")


def calculate_expression(expression: str) -> str:
    """Evaluate an arithmetic expression and return the result as a string.

    Supports ``+ - * / ** % //``, parentheses, ``abs``/``round``/``min``/``max``,
    whitelisted ``math.*`` functions, and the constants ``pi``/``e``/``tau``.
    Returns a ``"Error: ..."`` string for anything outside the whitelist —
    never raises to the caller.
    """
    try:
        tree = ast.parse(expression, mode="eval")
        result = _evaluate(tree)
    except UnsafeExpression as exc:
        return f"Error: {exc}"
    except (SyntaxError, ValueError, TypeError, ZeroDivisionError, OverflowError) as exc:
        return f"Error: invalid expression ({exc or type(exc).__name__})"
    if isinstance(result, float) and result.is_integer():
        result = int(result)
    return str(result)
