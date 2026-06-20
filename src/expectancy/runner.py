"""Orchestration: glue the layers into a single backtest run.

This is the one place that wires data -> strategy -> engine -> metrics ->
Monte Carlo together. `main.py` and the study scripts call into here so the
sequencing lives in exactly one spot.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from expectancy.analysis.significance import ExpectancyCI, bootstrap_mean_ci
from expectancy.config import Config
from expectancy.data import load_ohlcv
from expectancy.engine import BacktestEngine, BacktestResult
from expectancy.metrics import Metrics, compute_metrics
from expectancy.montecarlo import (
    MonteCarloResult,
    RuinResult,
    recovery_table,
    risk_of_ruin_table,
    run_bootstrap,
)
from expectancy.strategy import build_strategy


@dataclass
class RunBundle:
    """Everything the reporting layer needs for one instrument."""

    config: Config
    result: BacktestResult
    metrics: Metrics
    montecarlo: MonteCarloResult
    ruin: list[RuinResult]
    recovery: list[tuple[float, float]]
    expectancy_ci: ExpectancyCI


def run_backtest(config: Config, *, use_cache: bool = True) -> RunBundle:
    df = load_ohlcv(
        config.ticker, config.start, config.end, config.interval, use_cache=use_cache
    )
    strategy = build_strategy(config.strategy)
    signals = strategy.generate_signals(df)

    engine = BacktestEngine(config)
    result = engine.run(signals, ticker=config.ticker)
    metrics = compute_metrics(result)

    mc_cfg = config.montecarlo
    r_multiples = result.r_series()
    montecarlo = run_bootstrap(
        r_multiples,
        n_simulations=mc_cfg.n_simulations,
        risk_fraction=config.risk_per_trade_pct / 100.0,
        initial_capital=config.initial_capital,
        seed=mc_cfg.seed,
    )
    ruin = risk_of_ruin_table(
        r_multiples,
        risk_levels_pct=mc_cfg.risk_levels,
        drawdown_target_pct=mc_cfg.drawdown_target_pct,
        n_simulations=mc_cfg.n_simulations,
        initial_capital=config.initial_capital,
        seed=mc_cfg.seed,
    )
    recovery = recovery_table()
    expectancy_ci = bootstrap_mean_ci(r_multiples, n_resamples=10_000, seed=mc_cfg.seed)

    return RunBundle(
        config=config,
        result=result,
        metrics=metrics,
        montecarlo=montecarlo,
        ruin=ruin,
        recovery=recovery,
        expectancy_ci=expectancy_ci,
    )
