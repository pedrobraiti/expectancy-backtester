"""Engine tests — the no-lookahead and R-multiple guarantees (brief §5)."""

from __future__ import annotations

import numpy as np

from expectancy.config import Config, CostConfig
from expectancy.engine import BacktestEngine
from expectancy.strategy.base import SignalColumns
from tests.conftest import make_ohlcv

S, ST, TG = SignalColumns.SIGNAL, SignalColumns.STOP, SignalColumns.TARGET


def _zero_cost_config() -> Config:
    return Config(initial_capital=10_000, risk_per_trade_pct=0.5, costs=CostConfig(0, 0, 0))


def test_execution_happens_on_next_bar_open_not_signal_close():
    """A signal at bar t must fill at the OPEN of bar t+1, never bar t's close."""
    rows = [
        {"Open": 100, "High": 101, "Low": 99, "Close": 100},
        {"Open": 100, "High": 101, "Low": 99, "Close": 100, S: 1, ST: 98, TG: 106},
        {"Open": 100, "High": 103, "Low": 99, "Close": 102},   # entry bar (t+1)
        {"Open": 102, "High": 107, "Low": 101, "Close": 106},  # target 106 hit here
        {"Open": 106, "High": 108, "Low": 104, "Close": 107},
    ]
    df = make_ohlcv(rows)
    result = BacktestEngine(_zero_cost_config()).run(df)

    assert result.n_trades == 1
    trade = result.trades[0]
    assert trade.entry_date == df.index[2]      # t+1, not the signal bar (index 1)
    assert trade.entry_price == 100.0           # open[t+1]
    assert trade.exit_reason == "target"
    assert trade.exit_date == df.index[3]


def test_r_multiple_matches_target_distance():
    """Target at 3x risk must produce ~+3R with zero costs."""
    rows = [
        {"Open": 100, "High": 101, "Low": 99, "Close": 100},
        {"Open": 100, "High": 101, "Low": 99, "Close": 100, S: 1, ST: 98, TG: 106},
        {"Open": 100, "High": 103, "Low": 99, "Close": 102},
        {"Open": 102, "High": 107, "Low": 101, "Close": 106},
    ]
    result = BacktestEngine(_zero_cost_config()).run(make_ohlcv(rows))
    trade = result.trades[0]
    # entry 100, stop 98 -> risk 2/unit; exit 106 -> +6/unit = 3R
    assert np.isclose(trade.r_multiple, 3.0, atol=1e-9)
    assert np.isclose(trade.pnl_money, 3.0 * trade.risk_money, atol=1e-9)


def test_stop_loss_is_one_R_loss():
    rows = [
        {"Open": 100, "High": 101, "Low": 99, "Close": 100},
        {"Open": 100, "High": 101, "Low": 99, "Close": 100, S: 1, ST: 98, TG: 106},
        {"Open": 100, "High": 101, "Low": 97, "Close": 98},   # stop 98 hit
    ]
    result = BacktestEngine(_zero_cost_config()).run(make_ohlcv(rows))
    trade = result.trades[0]
    assert trade.exit_reason == "stop"
    assert np.isclose(trade.r_multiple, -1.0, atol=1e-9)


def test_stop_assumed_first_when_bar_hits_both():
    """If one bar's range touches stop AND target, the stop fills (worst case)."""
    rows = [
        {"Open": 100, "High": 101, "Low": 99, "Close": 100},
        {"Open": 100, "High": 101, "Low": 99, "Close": 100, S: 1, ST: 98, TG: 106},
        {"Open": 100, "High": 107, "Low": 97, "Close": 103},  # both 98 and 106 inside range
    ]
    result = BacktestEngine(_zero_cost_config()).run(make_ohlcv(rows))
    assert result.trades[0].exit_reason == "stop"


def test_no_trade_without_a_next_bar_to_execute_on():
    rows = [
        {"Open": 100, "High": 101, "Low": 99, "Close": 100},
        {"Open": 100, "High": 101, "Low": 99, "Close": 100, S: 1, ST: 98, TG: 106},  # last bar
    ]
    result = BacktestEngine(_zero_cost_config()).run(make_ohlcv(rows))
    assert result.n_trades == 0


def test_costs_make_a_winner_smaller():
    rows = [
        {"Open": 100, "High": 101, "Low": 99, "Close": 100},
        {"Open": 100, "High": 101, "Low": 99, "Close": 100, S: 1, ST: 98, TG: 106},
        {"Open": 100, "High": 103, "Low": 99, "Close": 102},
        {"Open": 102, "High": 107, "Low": 101, "Close": 106},
    ]
    df = make_ohlcv(rows)
    no_cost = BacktestEngine(_zero_cost_config()).run(df).trades[0]
    with_cost = BacktestEngine(
        Config(initial_capital=10_000, risk_per_trade_pct=0.5, costs=CostConfig(spread=0.1, commission=1.0, slippage_frac=0.05))
    ).run(df).trades[0]
    assert with_cost.pnl_money < no_cost.pnl_money
    assert with_cost.r_multiple < no_cost.r_multiple


def test_position_size_scales_inversely_with_stop_distance():
    """Wider stop -> smaller size, same cash at risk (fixed-fractional sizing)."""
    tight = [
        {"Open": 100, "High": 101, "Low": 99, "Close": 100},
        {"Open": 100, "High": 101, "Low": 99, "Close": 100, S: 1, ST: 99, TG: 106},
        {"Open": 100, "High": 103, "Low": 99.5, "Close": 102},
        {"Open": 102, "High": 108, "Low": 101, "Close": 107},
    ]
    wide = [
        {"Open": 100, "High": 101, "Low": 99, "Close": 100},
        {"Open": 100, "High": 101, "Low": 99, "Close": 100, S: 1, ST: 96, TG: 106},
        {"Open": 100, "High": 103, "Low": 99, "Close": 102},
        {"Open": 102, "High": 108, "Low": 101, "Close": 107},
    ]
    cfg = _zero_cost_config()
    tight_trade = BacktestEngine(cfg).run(make_ohlcv(tight)).trades[0]
    wide_trade = BacktestEngine(cfg).run(make_ohlcv(wide)).trades[0]
    assert tight_trade.size > wide_trade.size
    assert np.isclose(tight_trade.risk_money, wide_trade.risk_money)
