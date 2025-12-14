# api/backtester.py
# Accept generated python code (string), execute it in a controlled namespace,
# run the strategy on sample data and return a backtest report.

import pandas as pd
import numpy as np
import traceback

# ✅ FIXED RELATIVE IMPORT
from .indicators import compute_sma, compute_rsi

SAMPLE_DATA = [
    ["2020-01-01", 100, 101, 99, 100.5, 100000],
    ["2020-01-02", 100.5, 102, 100, 101.0, 120000],
    ["2020-01-03", 101.0, 103, 100.5, 102.5, 150000],
    ["2020-01-04", 102.5, 104, 101.5, 103.0, 130000],
    ["2020-01-05", 103.0, 103.5, 100, 100.5, 200000],
    ["2020-01-06", 100.5, 101.5, 99.5, 100.0, 300000],
    ["2020-01-07", 100.0, 102.0, 99.0, 101.0, 500000],
    ["2020-01-08", 101.0, 103.5, 100.5, 103.0, 600000],
    ["2020-01-09", 103.0, 106.0, 102.0, 105.5, 700000],
]

def _make_sample_df():
    df = pd.DataFrame(
        SAMPLE_DATA,
        columns=["date","open","high","low","close","volume"]
    )
    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)
    return df

def _safe_exec_and_get_signals(py_code: str, df: pd.DataFrame):
    ns = {}
    ns["compute_sma"] = compute_sma
    ns["compute_rsi"] = compute_rsi
    ns["pd"] = pd

    try:
        exec(py_code, ns)
        if "apply_strategy" not in ns:
            return None, "Generated code does not define apply_strategy(df)"
        signals = ns["apply_strategy"](df.copy())
        signals["entry"] = signals["entry"].fillna(False).astype(bool)
        signals["exit"] = signals["exit"].fillna(False).astype(bool)
        return signals, None
    except Exception as e:
        return None, f"Execution error: {e}\n{traceback.format_exc()}"

def run_simple_backtest(df: pd.DataFrame, signals: pd.DataFrame):
    trades = []
    in_position = False
    entry_price = None
    entry_date = None

    for i in range(len(df)-1):
        if not in_position and signals["entry"].iloc[i]:
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

    if in_position:
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

    total_return = 1.0
    for t in trades:
        total_return *= (1 + t["pnl"])
    total_return = (total_return - 1) * 100

    equity = [1.0]
    for t in trades:
        equity.append(equity[-1] * (1 + t["pnl"]))

    peak = equity[0]
    max_dd = 0.0
    for e in equity:
        peak = max(peak, e)
        max_dd = max(max_dd, (peak - e) / peak)

    return {
        "trades": trades,
        "num_trades": len(trades),
        "total_return_pct": round(total_return, 4),
        "max_drawdown_pct": round(max_dd * 100, 4)
    }

def run_backtest_with_code(py_code: str):
    df = _make_sample_df()
    signals, err = _safe_exec_and_get_signals(py_code, df)
    if err:
        return {"error": err}
    return run_simple_backtest(df, signals)

