"""Pool every instrument's trades into one stream to gain statistical power.

No single instrument here produces enough trades (~40) to validate or invalidate
anything. Pooling the realized trades across all instruments yields ~200, which
crosses the ~100-trade threshold where expectancy starts to stabilise. Because R
normalises each trade by the risk taken, R-multiples from different instruments
are directly comparable, so concatenating them is legitimate — this measures the
strategy *as a method across instruments*, not any single market.

The pool is ordered by exit date so it also supports an honest out-of-sample
check: the chronological first half (in-sample) versus the second half
(out-of-sample). If the edge were real it should persist out-of-sample; if it
collapses, the in-sample number was curve-fit to one regime.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from expectancy.analysis.significance import (
    ExpectancyCI,
    bootstrap_mean_ci,
    cluster_bootstrap_mean_ci,
)
from expectancy.engine.engine import BacktestResult


@dataclass(frozen=True)
class PooledResult:
    n_trades: int
    per_ticker: dict[str, int]
    r_multiples: np.ndarray          # ordered by exit date
    win_rate: float
    expectancy_r: float
    profit_factor: float
    avg_win_r: float
    avg_loss_r: float                # positive magnitude
    breakeven_win_rate: float
    ci: ExpectancyCI                 # i.i.d. bootstrap (optimistic — trades aren't independent)
    ci_block: ExpectancyCI           # calendar-quarter cluster bootstrap (the honest, wider CI)
    n_blocks: int                    # number of non-empty calendar quarters (effective sample)
    in_sample_n: int
    out_sample_n: int
    in_sample_expectancy_r: float
    out_sample_expectancy_r: float

    @property
    def edge_survives_oos(self) -> bool:
        return self.out_sample_expectancy_r > 0


def _collect_sorted(results: list[BacktestResult]) -> tuple[np.ndarray, list, dict[str, int]]:
    trades = []
    per_ticker: dict[str, int] = {}
    for result in results:
        per_ticker[result.ticker] = result.n_trades
        trades.extend(result.trades)
    trades.sort(key=lambda t: t.exit_date)
    r = np.array([t.r_multiple for t in trades], dtype=float)
    quarters = [f"{t.exit_date.year}Q{(t.exit_date.month - 1) // 3 + 1}" for t in trades]
    return r, quarters, per_ticker


def pool_trades(
    results: list[BacktestResult],
    *,
    n_resamples: int = 10_000,
    seed: int = 42,
) -> PooledResult:
    r, quarters, per_ticker = _collect_sorted(results)
    n = r.size
    if n == 0:
        empty_ci = bootstrap_mean_ci(r, n_resamples=n_resamples, seed=seed)
        return PooledResult(0, per_ticker, r, 0, 0, 0, 0, 0, 0, empty_ci, empty_ci, 0, 0, 0, 0, 0)

    wins = r[r > 0]
    losses = r[r < 0]
    win_rate = wins.size / n
    expectancy_r = float(r.mean())
    profit_factor = float(wins.sum() / -losses.sum()) if losses.size else math.inf
    avg_win_r = float(wins.mean()) if wins.size else 0.0
    avg_loss_r = float(-losses.mean()) if losses.size else 0.0
    payoff = avg_win_r / avg_loss_r if avg_loss_r > 0 else math.inf
    breakeven = 1.0 / (payoff + 1.0) if math.isfinite(payoff) else 0.0

    ci = bootstrap_mean_ci(r, n_resamples=n_resamples, seed=seed)
    ci_block = cluster_bootstrap_mean_ci(r, quarters, n_resamples=n_resamples, seed=seed)
    n_blocks = len(set(quarters))

    half = n // 2
    in_r, out_r = r[:half], r[half:]

    return PooledResult(
        n_trades=n,
        per_ticker=per_ticker,
        r_multiples=r,
        win_rate=win_rate,
        expectancy_r=expectancy_r,
        profit_factor=profit_factor,
        avg_win_r=avg_win_r,
        avg_loss_r=avg_loss_r,
        breakeven_win_rate=breakeven,
        ci=ci,
        ci_block=ci_block,
        n_blocks=n_blocks,
        in_sample_n=in_r.size,
        out_sample_n=out_r.size,
        in_sample_expectancy_r=float(in_r.mean()) if in_r.size else 0.0,
        out_sample_expectancy_r=float(out_r.mean()) if out_r.size else 0.0,
    )
