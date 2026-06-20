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

from expectancy.config import Config
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
