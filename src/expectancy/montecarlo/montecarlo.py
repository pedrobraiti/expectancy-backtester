"""Variance, risk of ruin and recovery maths (brief §7).

A single backtest is one draw from a distribution. The same system, with the
same expectancy, produces wildly different experiences depending on the *order*
of wins and losses. This module makes that distribution visible:

* **Bootstrap fan** (§7.1) -- reshuffle the realized R-multiples N times,
  rebuild the equity curve each time, and report the median path with a 5-95%
  band plus best/worst cases. The seed is fixed for reproducibility.
* **Risk of ruin** (§7.2) -- via the same resampling, estimate the probability of
  hitting an X% drawdown at several per-trade risk levels, exposing how that
  probability explodes non-linearly as risk rises.
* **Recovery table** (§7.3) -- the asymmetry between a loss and the gain needed
  to undo it.

Equity compounds per trade as ``equity *= 1 + R * risk_fraction``, because a
trade risking fraction ``f`` of equity and returning ``R`` changes equity by
``R * f * equity``. R-multiples are sizing-independent, which is exactly why the
same trade stream can be replayed at any risk level.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from expectancy.metrics.metrics import recovery_required


@dataclass(frozen=True)
class MonteCarloResult:
    n_simulations: int
    risk_fraction: float
    initial_capital: float
    final_equities: np.ndarray         # shape (n_sims,)
    equity_paths_percentiles: dict[int, np.ndarray]  # percentile -> path over trades
    median_final: float
    p5_final: float
    p95_final: float
    best_final: float
    worst_final: float
    prob_loss: float                   # P(final < initial)


@dataclass(frozen=True)
class RuinResult:
    risk_level_pct: float
    drawdown_target_pct: float
    probability: float


def _equity_paths(r_samples: np.ndarray, risk_fraction: float, initial_capital: float) -> np.ndarray:
    """Vectorised compounding of equity for a matrix of R-sequences.

    `r_samples` has shape (n_sims, n_trades); returns (n_sims, n_trades+1) equity
    paths including the starting capital column.
    """
    multipliers = 1.0 + r_samples * risk_fraction
    multipliers = np.clip(multipliers, 0.0, None)  # equity cannot go negative
    cumulative = np.cumprod(multipliers, axis=1)
    start = np.full((r_samples.shape[0], 1), initial_capital)
    return np.concatenate([start, start * cumulative], axis=1)


def run_bootstrap(
    r_multiples: np.ndarray,
    *,
    n_simulations: int,
    risk_fraction: float,
    initial_capital: float,
    seed: int,
    percentiles: tuple[int, ...] = (5, 50, 95),
) -> MonteCarloResult:
    """Reshuffle the realized R-multiples and rebuild the equity curve N times."""
    r_multiples = np.asarray(r_multiples, dtype=float)
    n_trades = r_multiples.size
    if n_trades == 0:
        empty = np.array([initial_capital])
        return MonteCarloResult(
            n_simulations=0,
            risk_fraction=risk_fraction,
            initial_capital=initial_capital,
            final_equities=empty,
            equity_paths_percentiles={p: empty for p in percentiles},
            median_final=initial_capital,
            p5_final=initial_capital,
            p95_final=initial_capital,
            best_final=initial_capital,
            worst_final=initial_capital,
            prob_loss=0.0,
        )

    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n_trades, size=(n_simulations, n_trades))
    r_samples = r_multiples[idx]

    paths = _equity_paths(r_samples, risk_fraction, initial_capital)
    final_equities = paths[:, -1]

    pct_paths = {p: np.percentile(paths, p, axis=0) for p in percentiles}

    return MonteCarloResult(
        n_simulations=n_simulations,
        risk_fraction=risk_fraction,
        initial_capital=initial_capital,
        final_equities=final_equities,
        equity_paths_percentiles=pct_paths,
        median_final=float(np.median(final_equities)),
        p5_final=float(np.percentile(final_equities, 5)),
        p95_final=float(np.percentile(final_equities, 95)),
        best_final=float(final_equities.max()),
        worst_final=float(final_equities.min()),
        prob_loss=float(np.mean(final_equities < initial_capital)),
    )


def _max_drawdown_fraction(paths: np.ndarray) -> np.ndarray:
    """Max peak-to-trough drawdown fraction for each path (row)."""
    running_peak = np.maximum.accumulate(paths, axis=1)
    drawdowns = (running_peak - paths) / running_peak
    return drawdowns.max(axis=1)


def risk_of_ruin_table(
    r_multiples: np.ndarray,
    *,
    risk_levels_pct: tuple[float, ...],
    drawdown_target_pct: float,
    n_simulations: int,
    initial_capital: float,
    seed: int,
) -> list[RuinResult]:
    """Probability of hitting an X% drawdown at each per-trade risk level.

    Uses the same bootstrap engine: the realized R-stream is replayed at each
    risk fraction, and we count how often the equity path draws down past the
    target. The non-linear blow-up as risk rises is the whole point.
    """
    r_multiples = np.asarray(r_multiples, dtype=float)
    target_fraction = drawdown_target_pct / 100.0
    results: list[RuinResult] = []

    if r_multiples.size == 0:
        return [RuinResult(level, drawdown_target_pct, 0.0) for level in risk_levels_pct]

    rng = np.random.default_rng(seed)
    n_trades = r_multiples.size
    # Same resampled index matrix across levels -> differences are purely the risk dial.
    idx = rng.integers(0, n_trades, size=(n_simulations, n_trades))
    r_samples = r_multiples[idx]

    for level in risk_levels_pct:
        paths = _equity_paths(r_samples, level / 100.0, initial_capital)
        max_dd = _max_drawdown_fraction(paths)
        probability = float(np.mean(max_dd >= target_fraction))
        results.append(RuinResult(level, drawdown_target_pct, probability))
    return results


def recovery_table(loss_fractions: tuple[float, ...] = (0.1, 0.2, 0.3, 0.4, 0.5)) -> list[tuple[float, float]]:
    """The loss -> gain-to-recover asymmetry (brief §7.3)."""
    return [(loss, recovery_required(loss)) for loss in loss_fractions]
