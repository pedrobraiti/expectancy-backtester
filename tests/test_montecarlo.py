"""Monte-Carlo tests — reproducibility and the risk-of-ruin shape (brief §7)."""

from __future__ import annotations

import numpy as np

from expectancy.montecarlo import recovery_table, risk_of_ruin_table, run_bootstrap


def _sample_r_stream() -> np.ndarray:
    # A positive-expectancy stream: many small losses, fewer larger wins.
    rng = np.random.default_rng(123)
    wins = rng.normal(2.5, 0.5, 300)
    losses = -np.abs(rng.normal(1.0, 0.1, 500))
    stream = np.concatenate([wins, losses])
    rng.shuffle(stream)
    return stream


def test_bootstrap_is_reproducible_with_fixed_seed():
    r = _sample_r_stream()
    a = run_bootstrap(r, n_simulations=2000, risk_fraction=0.01, initial_capital=10_000, seed=42)
    b = run_bootstrap(r, n_simulations=2000, risk_fraction=0.01, initial_capital=10_000, seed=42)
    assert np.allclose(a.final_equities, b.final_equities)
    assert a.median_final == b.median_final


def test_bootstrap_changes_with_different_seed():
    r = _sample_r_stream()
    a = run_bootstrap(r, n_simulations=2000, risk_fraction=0.01, initial_capital=10_000, seed=1)
    b = run_bootstrap(r, n_simulations=2000, risk_fraction=0.01, initial_capital=10_000, seed=2)
    assert not np.allclose(a.final_equities, b.final_equities)


def test_percentile_band_is_ordered():
    r = _sample_r_stream()
    mc = run_bootstrap(r, n_simulations=3000, risk_fraction=0.01, initial_capital=10_000, seed=7)
    assert mc.worst_final <= mc.p5_final <= mc.median_final <= mc.p95_final <= mc.best_final


def test_risk_of_ruin_increases_with_risk_per_trade():
    """Higher per-trade risk must not lower the probability of a deep drawdown."""
    r = _sample_r_stream()
    table = risk_of_ruin_table(
        r, risk_levels_pct=(0.5, 1.0, 2.0, 5.0), drawdown_target_pct=50,
        n_simulations=3000, initial_capital=10_000, seed=42,
    )
    probs = [row.probability for row in table]
    assert probs == sorted(probs)        # monotonic non-decreasing in risk
    assert probs[-1] >= probs[0]


def test_recovery_table_values():
    table = dict(recovery_table())
    assert np.isclose(table[0.5], 1.0)
    assert np.isclose(table[0.1], 1.0 / 0.9 - 1.0)
