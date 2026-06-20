"""How fast the thin edge dies as transaction costs rise.

When expectancy is a fraction of an R on ~40 trades, the conclusion about which
instruments "win" hangs on the cost assumption. This sweep re-runs the engine at
a range of slippage levels and watches expectancy cross zero — making the
fragility explicit instead of hiding it behind one cost number.

Signals are cost-independent, so they are generated once; only the engine (which
folds costs into the fills) is re-run per cost level.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

from expectancy.config import Config, CostConfig
from expectancy.data import load_ohlcv
from expectancy.engine import BacktestEngine
from expectancy.metrics import compute_metrics
from expectancy.strategy import build_strategy


@dataclass(frozen=True)
class CostPoint:
    slippage_frac: float
    expectancy_r: float
    profit_factor: float
    n_trades: int


@dataclass(frozen=True)
class PooledCostPoint:
    slippage_frac: float
    expectancy_r: float          # pooled mean R across the whole basket at this slippage
    n_trades: int


@dataclass(frozen=True)
class PooledCostCurve:
    points: list[PooledCostPoint]
    gross_expectancy_r: float    # all costs zeroed — the raw signal before frictions
    breakeven_slippage: float | None   # slippage where pooled expectancy crosses zero (None if never)


def cost_sweep(
    config: Config,
    slippage_fracs: tuple[float, ...],
    *,
    use_cache: bool = True,
) -> list[CostPoint]:
    """Re-run the backtest across slippage levels, holding everything else fixed."""
    df = load_ohlcv(config.ticker, config.start, config.end, config.interval, use_cache=use_cache)
    signals = build_strategy(config.strategy).generate_signals(df)

    points: list[CostPoint] = []
    for slippage in slippage_fracs:
        cfg = replace(config, costs=replace(config.costs, slippage_frac=slippage))
        result = BacktestEngine(cfg).run(signals, ticker=config.ticker)
        metrics = compute_metrics(result)
        points.append(
            CostPoint(
                slippage_frac=slippage,
                expectancy_r=metrics.expectancy_r,
                profit_factor=metrics.profit_factor,
                n_trades=result.n_trades,
            )
        )
    return points


def _interp_breakeven(points: list[PooledCostPoint]) -> float | None:
    """Linear-interpolate the slippage where pooled expectancy crosses zero."""
    for a, b in zip(points, points[1:]):
        if (a.expectancy_r > 0) != (b.expectancy_r > 0) and a.expectancy_r != b.expectancy_r:
            t = a.expectancy_r / (a.expectancy_r - b.expectancy_r)
            return a.slippage_frac + t * (b.slippage_frac - a.slippage_frac)
    return None


def pooled_cost_curve(
    configs: list[Config],
    slippage_fracs: tuple[float, ...],
    *,
    use_cache: bool = True,
) -> PooledCostCurve:
    """Sweep slippage across a whole basket and pool the R-multiples at each level.

    This is the cost-sensitivity test that matters for the powered study: the
    "zero after costs" claim rests on one slippage assumption, so we vary it and
    pool all instruments' trades to find where the *aggregate* edge crosses zero.
    Signals are cost-independent, so they are generated once per instrument and
    only the engine is re-run per cost level. Also reports the fully **gross**
    expectancy (all costs zeroed) — the raw signal before any friction.
    """
    prepared = []
    for cfg in configs:
        df = load_ohlcv(cfg.ticker, cfg.start, cfg.end, cfg.interval, use_cache=use_cache)
        signals = build_strategy(cfg.strategy).generate_signals(df)
        prepared.append((cfg, signals))

    points: list[PooledCostPoint] = []
    for slippage in slippage_fracs:
        all_r: list[float] = []
        for cfg, signals in prepared:
            cfg2 = replace(cfg, costs=replace(cfg.costs, slippage_frac=slippage))
            result = BacktestEngine(cfg2).run(signals, ticker=cfg.ticker)
            all_r.extend(result.r_series().tolist())
        r = np.asarray(all_r, dtype=float)
        points.append(PooledCostPoint(slippage, float(r.mean()) if r.size else 0.0, r.size))

    gross_r: list[float] = []
    for cfg, signals in prepared:
        cfg_gross = replace(cfg, costs=CostConfig(spread=0.0, commission=0.0, slippage_frac=0.0))
        result = BacktestEngine(cfg_gross).run(signals, ticker=cfg.ticker)
        gross_r.extend(result.r_series().tolist())
    gross = float(np.mean(gross_r)) if gross_r else 0.0

    return PooledCostCurve(points=points, gross_expectancy_r=gross,
                           breakeven_slippage=_interp_breakeven(points))
