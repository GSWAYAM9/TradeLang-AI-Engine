# api/ast_to_python.py
# Convert AST (dict) into a Python code string

from typing import Dict, Any
import textwrap

# ✅ REQUIRED: RELATIVE IMPORTS
from .indicators import compute_sma, compute_rsi


def _expr_to_code(expr):
    if expr is None:
        return "False"

    t = expr.get("type")

    if t == "comparison":
        left_code = _operand_to_code(expr["left"])
        right_code = _operand_to_code(expr["right"])
        return f"({left_code} {expr['op']} {right_code})"

    if t == "indicator":
        name = expr["name"].lower()
        params = expr.get("params", [])
        series = params[0]
        window = params[1] if len(params) > 1 else (14 if name == "rsi" else 20)

        if name == "sma":
            return f"compute_sma(df['{series}'], {window})"
        if name == "rsi":
            return f"compute_rsi(df['{series}'], {window})"

        return "False"

    if t == "and":
        return "(" + " & ".join(_expr_to_code(p) for p in expr.get("items", [])) + ")"

    if t == "or":
        return "(" + " | ".join(_expr_to_code(p) for p in expr.get("items", [])) + ")"

    return "False"


def _operand_to_code(op):
    if isinstance(op, dict):
        return _expr_to_code(op)
    if isinstance(op, (int, float)):
        return str(op)
    if isinstance(op, str):
        return f"df['{op}']"
    return "False"


def generate_python_code(ast: Dict[str, Any]) -> str:
    entry_expr = _expr_to_code(ast.get("entry"))
    exit_expr = _expr_to_code(ast.get("exit"))

    code = f"""
# Generated strategy code

def apply_strategy(df):
    import pandas as pd

    signals = pd.DataFrame(index=df.index)
    signals['entry'] = {entry_expr}
    signals['exit'] = {exit_expr}

    return signals
"""
    return textwrap.dedent(code)

