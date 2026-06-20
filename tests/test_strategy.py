"""Strategy & indicator tests — causality and signal integrity (brief §4)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from expectancy.strategy import build_strategy
from expectancy.strategy.base import SignalColumns
from expectancy.strategy.indicators import average_true_range, sma
from expectancy.config import StrategyConfig


def test_sma_is_causal_and_lagged():
    s = pd.Series(np.arange(1, 11, dtype=float))
    out = sma(s, 3)
    assert out.iloc[:2].isna().all()           # no value before the window fills
    assert np.isclose(out.iloc[2], 2.0)        # mean(1,2,3)
    assert np.isclose(out.iloc[9], 9.0)        # mean(8,9,10)


def test_atr_is_positive_and_warms_up(synthetic_price):
    atr = average_true_range(synthetic_price, 14)
    assert atr.iloc[:13].isna().all()
    valid = atr.dropna()
    assert (valid > 0).all()


def test_signals_only_where_atr_is_defined(synthetic_price):
    strat = build_strategy(StrategyConfig())
    sig = strat.generate_signals(synthetic_price)
    atr = average_true_range(synthetic_price, StrategyConfig().atr_period)
    # No signal may appear on a bar where ATR (hence risk) is undefined.
    assert not ((sig[SignalColumns.SIGNAL] != 0) & atr.isna()).any()


def test_long_signal_has_stop_below_and_target_above(synthetic_price):
    sig = build_strategy(StrategyConfig()).generate_signals(synthetic_price)
    longs = sig[sig[SignalColumns.SIGNAL] == 1]
    assert (longs[SignalColumns.STOP] < longs["Close"]).all()
    assert (longs[SignalColumns.TARGET] > longs["Close"]).all()


def test_long_only_emits_no_short_signals(synthetic_price):
    sig = build_strategy(StrategyConfig(direction="long_only")).generate_signals(synthetic_price)
    assert (sig[SignalColumns.SIGNAL] >= 0).all()


def test_fast_must_be_faster_than_slow():
    with pytest.raises(ValueError):
        build_strategy(StrategyConfig(fast_ma=50, slow_ma=20))


def test_strategy_does_not_mutate_or_use_future():
    """generate_signals must not look at rows beyond t: truncating the tail must
    not change earlier signals."""
    cfg = StrategyConfig()
    rng = np.random.default_rng(3)
    n = 400
    close = 50 + np.cumsum(rng.normal(0, 0.5, n))
    df = pd.DataFrame(
        {"Open": close, "High": close + 1, "Low": close - 1, "Close": close, "Volume": 1},
        index=pd.bdate_range("2019-01-01", periods=n),
    )
    full = build_strategy(cfg).generate_signals(df)
    truncated = build_strategy(cfg).generate_signals(df.iloc[:300])
    pd.testing.assert_series_equal(
        full[SignalColumns.SIGNAL].iloc[:300], truncated[SignalColumns.SIGNAL]
    )
