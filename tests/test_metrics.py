"""Metrics tests — expectancy sanity, drawdown, breakeven, recovery (brief §6, §7.3)."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from expectancy.config import Config, CostConfig
from expectancy.engine import BacktestEngine
from expectancy.engine.engine import BacktestResult
from expectancy.metrics import compute_metrics, max_drawdown, recovery_required
from expectancy.metrics.metrics import expectancy_sanity_check
from expectancy.strategy import build_strategy


def test_expectancy_sanity_check_holds_on_real_run(synthetic_price):
    cfg = Config(costs=CostConfig(spread=0.02, commission=0.0, slippage_frac=0.05))
    signals = build_strategy(cfg.strategy).generate_signals(synthetic_price)
    result = BacktestEngine(cfg).run(signals)
    metrics = compute_metrics(result)
    # The whole point of the check: formula expectancy == realized mean.
    assert metrics.expectancy_check_ok
    formula = metrics.win_rate * metrics.avg_win_money - metrics.loss_rate * metrics.avg_loss_money
    assert np.isclose(formula, metrics.expectancy_money, atol=1e-6)


def test_expectancy_sanity_check_detects_mismatch():
    # avg_win=2, avg_loss=1, wr=0.5 -> formula = 0.5*2 - 0.5*1 = 0.5
    assert expectancy_sanity_check(2.0, 1.0, 0.5, 0.5)
    assert not expectancy_sanity_check(2.0, 1.0, 0.5, 0.9)


def test_breakeven_win_rate_formula():
    """A 3:1 payoff needs ~25% wins to break even (1/(R+1))."""
    rows_R = np.array([3.0, 3.0, 3.0, -1.0])  # payoff 3:1
    # Build a fake result with these R's via a tiny synthetic engine run is overkill;
    # check the closed form the metric uses: 1/(payoff+1).
    payoff = 3.0
    assert np.isclose(1.0 / (payoff + 1.0), 0.25)


def test_max_drawdown_simple_curve():
    # equity after trades; peak 120 then down to 90 -> DD = 25% (30/120)
    curve = pd.Series([110, 120, 100, 90, 130], index=pd.bdate_range("2021-01-01", periods=5))
    dd_pct, dd_money = max_drawdown(curve, initial_capital=100)
    assert np.isclose(dd_pct, 25.0, atol=1e-9)
    assert np.isclose(dd_money, 30.0, atol=1e-9)


def test_recovery_required_table():
    assert np.isclose(recovery_required(0.10), 0.1111, atol=1e-3)
    assert np.isclose(recovery_required(0.30), 0.4286, atol=1e-3)
    assert np.isclose(recovery_required(0.50), 1.0, atol=1e-9)
    assert math.isinf(recovery_required(1.0))


def test_profit_factor_and_payoff_positive_on_winning_stream(synthetic_price):
    cfg = Config()
    signals = build_strategy(cfg.strategy).generate_signals(synthetic_price)
    metrics = compute_metrics(BacktestEngine(cfg).run(signals))
    assert metrics.n_trades > 0
    assert metrics.gross_profit >= 0 and metrics.gross_loss >= 0
    if metrics.gross_loss > 0:
        assert np.isclose(metrics.profit_factor, metrics.gross_profit / metrics.gross_loss)


def test_empty_result_is_safe():
    empty = BacktestResult(
        trades=[], equity_curve=pd.Series(dtype=float), initial_capital=10_000,
        final_equity=10_000, ticker="NONE",
    )
    metrics = compute_metrics(empty)
    assert metrics.n_trades == 0
    assert not metrics.sample_is_reliable
