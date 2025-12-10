
# backend/api/backtester.py
# Accept generated python code (string), execute it in a controlled namespace,
# run the strategy on sample data and return a backtest report.

import pandas as pd
import numpy as np
import traceback
from indicators import compute_sma, compute_rsi

SAMPLE_DATA = [
    # date, open, high, low, close, volume
    ["2020-01-01", 100, 101, 99, 100.5, 100000],
    ["2020-01-02", 100.5, 102, 100, 101.0, 120000],
    ["2020-01-03", 101.0, 103, 100.5, 102.5, 150000],
    ["2020-01-04", 102.5, 104, 101.5, 103.0, 130000],
    ["2020-01-05", 103.0, 103.5, 100, 100.5, 200000],
    # Add a few more rows for demo
    ["2020-01-06", 100.5, 101.5, 99.5, 100.0, 300000],
    ["2020-01-07", 100.0, 102.0, 99.0, 101.0, 500000],
    ["2020-01-08", 101.0, 103.5, 100.5, 103.0, 600000],
    ["2020-01-09", 103.0, 106.0, 102.0, 105.5, 700000],
]

def _make_sample_df():
    df = pd.DataFrame(SAMPLE_DATA, columns=["date","open","high","low","close","volume"])
    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)
    return df

def _safe_exec_and_get_signals(py_code: str, df: pd.DataFrame):
    """
    Execute generated code; expect function apply_strategy(df) to be defined.
    We supply compute_sma, compute_rsi in the global namespace.
    """
    ns = {}
    # Provide safe helper functions and pandas in ns
    ns["compute_sma"] = compute_sma
    ns["compute_rsi"] = compute_rsi
    ns["pd"] = pd
    try:
        exec(py_code, ns)
        if "apply_strategy" not in ns:
            return None, "Generated code does not define apply_strategy(df)"
        signals = ns["apply_strategy"](df.copy())
        # ensure boolean columns
        signals["entry"] = signals["entry"].fillna(False).astype(bool)
        signals["exit"] = signals["exit"].fillna(False).astype(bool)
        return signals, None
    except Exception as e:
        return None, f"Execution error: {e}\\n{traceback.format_exc()}"

def run_simple_backtest(df: pd.DataFrame, signals: pd.DataFrame):
    """
    Very simplified backtest:
    - Single position at a time (long only)
    - Entry price = next row's 'open' (slippage avoided for simplicity)
    - Exit price = next row's 'open'
    """
    trades = []
    in_position = False
    entry_price = None
    entry_date = None

    # iterate rows
    for i in range(len(df)-1):  # last row cannot open a trade because we need next open for fill
        date = df.index[i]
        if not in_position and signals["entry"].iloc[i]:
            # enter at next row open (i+1)
            entry_price = df["open"].iloc[i+1]
            entry_date = df.index[i+1]
            in_position = True
        elif in_position and signals["exit"].iloc[i]:
            exit_price = df["open"].iloc[i+1]
            exit_date = df.index[i+1]
            pnl = (exit_price - entry_price) / entry_price
            trades.append({
                "entry_date": str(entry_date.date()),
                "exit_date": str(exit_date.date()),
                "entry_price": float(entry_price),
                "exit_price": float(exit_price),
                "pnl": float(pnl)
            })
            in_position = False
            entry_price = None
            entry_date = None

    # If still in position at end, exit at last close
    if in_position and entry_price is not None:
        exit_price = df["close"].iloc[-1]
        exit_date = df.index[-1]
        pnl = (exit_price - entry_price) / entry_price
        trades.append({
            "entry_date": str(entry_date.date()),
            "exit_date": str(exit_date.date()),
            "entry_price": float(entry_price),
            "exit_price": float(exit_price),
            "pnl": float(pnl)
        })
    # compute stats
    total_return = 1.0
    for t in trades:
        total_return *= (1 + t["pnl"])
    total_return = (total_return - 1) * 100  # percentage
    num_trades = len(trades)
    # simple max drawdown approximation using equity curve
    equity = [1.0]
    for t in trades:
        equity.append(equity[-1] * (1 + t["pnl"]))
    import math
    max_dd = 0.0
    peak = equity[0]
    for e in equity:
        if e > peak:
            peak = e
        dd = (peak - e) / peak
        if dd > max_dd:
            max_dd = dd
    max_drawdown_pct = max_dd * 100
    return {
        "trades": trades,
        "num_trades": num_trades,
        "total_return_pct": round(total_return, 4),
        "max_drawdown_pct": round(max_drawdown_pct, 4)
    }

def run_backtest_with_code(py_code: str):
    try:
        df = _make_sample_df()
        signals, err = _safe_exec_and_get_signals(py_code, df)
        if err:
            return {"error": err}
        report = run_simple_backtest(df, signals)
        return report
    except Exception as e:
        return {"error": str(e)}
