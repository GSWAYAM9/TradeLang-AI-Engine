
# backend/api/indicators.py
# Helper indicator implementations: compute_sma, compute_rsi

import pandas as pd
import numpy as np

def compute_sma(series: pd.Series, window: int):
    return series.rolling(window, min_periods=1).mean()

def compute_rsi(series: pd.Series, window: int = 14):
    # Classic RSI implementation
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ma_up = up.rolling(window=window, min_periods=1).mean()
    ma_down = down.rolling(window=window, min_periods=1).mean()
    rs = ma_up / (ma_down.replace(0, 1e-9))
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)
