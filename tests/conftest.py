"""Shared test fixtures and helpers."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from expectancy.strategy.base import SignalColumns


def make_ohlcv(rows: list[dict], start: str = "2020-01-01") -> pd.DataFrame:
    """Build an OHLCV (+ optional signal/stop/target) frame from explicit rows."""
    dates = pd.bdate_range(start, periods=len(rows))
    df = pd.DataFrame(rows, index=dates)
    for col in (SignalColumns.SIGNAL, SignalColumns.STOP, SignalColumns.TARGET):
        if col not in df.columns:
            df[col] = 0 if col == SignalColumns.SIGNAL else np.nan
    return df


@pytest.fixture
def synthetic_price() -> pd.DataFrame:
    """A long, regime-switching synthetic series that produces real crossovers."""
    rng = np.random.default_rng(7)
    n = 1200
    dates = pd.bdate_range("2015-01-01", periods=n)
    drift = np.concatenate([np.full(200, d) for d in [0.0012, -0.0013, 0.0016, -0.0011, 0.0013, 0.0]])[:n]
    ret = drift + rng.normal(0, 0.014, n)
    close = 50 * np.exp(np.cumsum(ret))
    open_ = close * (1 + rng.normal(0, 0.004, n))
    high = np.maximum.reduce([close, open_, close * (1 + np.abs(rng.normal(0, 0.008, n)))])
    low = np.minimum.reduce([close, open_, close * (1 - np.abs(rng.normal(0, 0.008, n)))])
    volume = rng.integers(1_000_000, 5_000_000, n)
    return pd.DataFrame(
        {"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume},
        index=dates,
    )
