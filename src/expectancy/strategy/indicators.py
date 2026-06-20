"""Technical indicators used by strategies.

Every indicator is causal: the value at row ``t`` uses only data up to and
including ``t``. No centering, no forward fill from the future. This is what
keeps the strategy honest before the engine even runs.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def sma(series: pd.Series, period: int) -> pd.Series:
    """Simple moving average over `period` bars (NaN until the window fills)."""
    return series.rolling(window=period, min_periods=period).mean()


def rsi(series: pd.Series, period: int) -> pd.Series:
    """Wilder's RSI over `period` bars (0-100), causal.

    Fast RSI (period 2-3) is the engine of Connors-style mean reversion: a very
    low reading flags a short-term oversold pullback. NaN until the window fills.
    """
    delta = series.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)
    avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss
    out = 100.0 - 100.0 / (1.0 + rs)
    # All-gain windows give avg_loss 0 -> rs inf -> RSI 100 (handled by the limit).
    out[avg_loss == 0.0] = 100.0
    out[(avg_gain == 0.0) & (avg_loss == 0.0)] = 50.0
    return out


def average_true_range(df: pd.DataFrame, period: int) -> pd.Series:
    """Wilder's ATR.

    True Range = max(high-low, |high-prev_close|, |low-prev_close|), then a
    Wilder (RMA) smoothing. Used to size stops and targets in price units so the
    same multiples adapt to each instrument's volatility.
    """
    high = df["High"]
    low = df["Low"]
    prev_close = df["Close"].shift(1)

    true_range = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    # Wilder smoothing == EWMA with alpha = 1/period.
    atr = true_range.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    return atr.replace(0.0, np.nan)
