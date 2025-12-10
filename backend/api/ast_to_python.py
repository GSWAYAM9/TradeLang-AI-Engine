
# backend/api/ast_to_python.py
# Convert AST (dict) into a Python code string that:
# - computes indicators (calls helpers)
# - produces `signals` DataFrame with boolean columns 'entry' and 'exit'

from typing import Dict, Any
import textwrap
import json

def _expr_to_code(expr):
    """
    Convert a single AST expression node to a pandas expression (string).
    We assume a DataFrame named `df` exists.
    """
    if expr is None:
        return "False"
    t = expr.get("type")
    if t == "comparison":
        left = expr["left"]
        op = expr["op"]
        right = expr["right"]
        left_code = _operand_to_code(left)
        right_code = _operand_to_code(right)
        return f"({left_code} {op} {right_code})"
    if t == "indicator":
        name = expr["name"]
        params = expr.get("params", [])
        # name e.g., 'sma', params like ['close', 20]
        if name == "sma":
            series = params[0]
            window = params[1] if len(params) > 1 else 20
            return f"compute_sma(df['{series}'], {window})"
        if name == "rsi":
            series = params[0]
            window = params[1] if len(params) > 1 else 14
            return f"compute_rsi(df['{series}'], {window})"
        # fallback
        return "False"
    if t == "and":
        parts = [_expr_to_code(p) for p in expr.get("items", [])]
        return "(" + " & ".join(parts) + ")"
    if t == "or":
        parts = [_expr_to_code(p) for p in expr.get("items", [])]
        return "(" + " | ".join(parts) + ")"
    if t == "cross":
        direction = expr.get("direction")
        target = expr.get("target")
        # offer a simple cross implementation: price crosses above yesterday's high
        if "yesterday" in target:
            if "high" in target:
                if direction == "above":
                    return "(df['close'].shift(1) <= df['high'].shift(1)) & (df['close'] > df['high'].shift(1))"
                else:
                    return "(df['close'].shift(1) >= df['low'].shift(1)) & (df['close'] < df['low'].shift(1))"
        return "False"
    # if expr is raw boolean or series name
    return "False"

def _operand_to_code(op):
    # op can be a string like 'close', numeric, or an indicator dict
    if isinstance(op, dict):
        if op.get("type") == "indicator" or "indicator" in op:
            # unify shapes
            if "indicator" in op:
                name = op["indicator"]
                params = op.get("params", [])
                if name.lower() == "sma":
                    series = params[0]
                    window = params[1] if len(params) > 1 else 20
                    return f"compute_sma(df['{series}'], {window})"
                if name.lower() == "rsi":
                    series = params[0]
                    window = params[1] if len(params) > 1 else 14
                    return f"compute_rsi(df['{series}'], {window})"
            else:
                # AST style: {'type':'indicator', 'name':..., 'params':...}
                name = op.get("name")
                params = op.get("params", [])
                if name.lower() == "sma":
                    series = params[0]
                    window = params[1] if len(params) > 1 else 20
                    return f"compute_sma(df['{series}'], {window})"
                if name.lower() == "rsi":
                    series = params[0]
                    window = params[1] if len(params) > 1 else 14
                    return f"compute_rsi(df['{series}'], {window})"
    if isinstance(op, (int, float)):
        return str(op)
    if isinstance(op, str):
        # assume column name like 'close', 'volume'
        return f"df['{op}']"
    return "False"

def generate_python_code(ast: Dict[str, Any]) -> str:
    """
    Build a Python module string which:
    - assumes 'df' exists (pandas DataFrame with columns open, high, low, close, volume)
    - computes indicator helper columns via compute_sma and compute_rsi functions
    - produces `signals` DataFrame with 'entry' and 'exit' boolean columns
    """
    entry_expr = "False"
    exit_expr = "False"
    if ast.get("entry"):
        entry_expr = _expr_to_code(ast["entry"])
    if ast.get("exit"):
        exit_expr = _expr_to_code(ast["exit"])

    code = f"""
# Generated strategy code
# Assumes pandas as pd and df is available

def apply_strategy(df):
    # compute indicators where needed using helper functions: compute_sma, compute_rsi
    # compute signals (boolean Series)
    import pandas as pd
    signals = pd.DataFrame(index=df.index)
    signals['entry'] = {entry_expr}
    signals['exit'] = {exit_expr}
    return signals
"""
    return textwrap.dedent(code)
