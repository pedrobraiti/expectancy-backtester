"""Analysis-layer tests — significance CI, pooling and cost sensitivity."""

from __future__ import annotations

import numpy as np

from expectancy.analysis import (
    bootstrap_mean_ci,
    cluster_bootstrap_mean_ci,
    cost_sweep,
    pool_trades,
    pooled_cost_curve,
)
from expectancy.config import Config
from expectancy.engine import BacktestEngine
from expectancy.strategy import build_strategy


def test_ci_is_reproducible_and_ordered():
    rng = np.random.default_rng(0)
    values = rng.normal(0.2, 1.0, 200)
    a = bootstrap_mean_ci(values, n_resamples=5000, seed=42)
    b = bootstrap_mean_ci(values, n_resamples=5000, seed=42)
    assert a == b
    assert a.ci_low <= a.mean_r <= a.ci_high


def test_ci_straddles_zero_for_zero_mean_data():
    rng = np.random.default_rng(1)
    values = rng.normal(0.0, 1.0, 40)        # no edge, small sample
    ci = bootstrap_mean_ci(values, n_resamples=5000, seed=7)
    assert not ci.distinguishable_from_zero
    assert ci.verdict == "indistinguishable from zero"


def test_ci_excludes_zero_for_strong_positive_data():
    rng = np.random.default_rng(2)
    values = rng.normal(1.0, 0.5, 500)       # clear positive edge, big sample
    ci = bootstrap_mean_ci(values, n_resamples=5000, seed=7)
    assert ci.distinguishable_from_zero
    assert ci.ci_low > 0
    assert ci.prob_positive > 0.99


def test_empty_ci_is_safe():
    ci = bootstrap_mean_ci(np.array([]), n_resamples=100, seed=1)
    assert ci.n == 0 and not ci.distinguishable_from_zero


def test_cluster_bootstrap_is_reproducible():
    rng = np.random.default_rng(0)
    values = rng.normal(0.1, 1.0, 120)
    labels = np.repeat(np.arange(20), 6)
    a = cluster_bootstrap_mean_ci(values, labels, n_resamples=3000, seed=42)
    b = cluster_bootstrap_mean_ci(values, labels, n_resamples=3000, seed=42)
    assert a == b
    assert a.ci_low <= a.mean_r <= a.ci_high


def test_cluster_bootstrap_is_wider_when_within_cluster_correlation_is_high():
    """If observations inside a cluster are identical (max correlation), the
    cluster bootstrap must report a wider interval than the i.i.d. one, which
    wrongly assumes independence."""
    rng = np.random.default_rng(3)
    n_clusters, per = 15, 8
    cluster_means = rng.normal(0.1, 1.0, n_clusters)
    values = np.repeat(cluster_means, per)              # perfectly correlated within cluster
    labels = np.repeat(np.arange(n_clusters), per)

    iid = bootstrap_mean_ci(values, n_resamples=4000, seed=7)
    clustered = cluster_bootstrap_mean_ci(values, labels, n_resamples=4000, seed=7)
    iid_width = iid.ci_high - iid.ci_low
    clustered_width = clustered.ci_high - clustered.ci_low
    assert clustered_width > iid_width * 1.5            # markedly wider, not a rounding effect


def test_cluster_bootstrap_matches_iid_when_each_point_is_its_own_cluster():
    rng = np.random.default_rng(5)
    values = rng.normal(0.2, 1.0, 80)
    labels = np.arange(80)                              # one cluster per observation
    iid = bootstrap_mean_ci(values, n_resamples=6000, seed=11)
    clustered = cluster_bootstrap_mean_ci(values, labels, n_resamples=6000, seed=11)
    assert abs((clustered.ci_high - clustered.ci_low) - (iid.ci_high - iid.ci_low)) < 0.1


def test_pool_block_ci_is_wider_than_iid(synthetic_price):
    _, a, b = _two_results(synthetic_price)
    pooled = pool_trades([a, b], n_resamples=4000, seed=42)
    # Block CI should never be tighter than the (over-confident) i.i.d. one.
    assert (pooled.ci_block.ci_high - pooled.ci_block.ci_low) >= (pooled.ci.ci_high - pooled.ci.ci_low) - 1e-9
    assert pooled.n_blocks > 0


def _two_results(synthetic_price):
    cfg = Config()
    signals = build_strategy(cfg.strategy).generate_signals(synthetic_price)
    a = BacktestEngine(cfg).run(signals, ticker="AAA")
    b = BacktestEngine(cfg).run(signals, ticker="BBB")
    return cfg, a, b


def test_pool_sums_trades_and_means_match(synthetic_price):
    _, a, b = _two_results(synthetic_price)
    pooled = pool_trades([a, b], n_resamples=2000, seed=42)
    assert pooled.n_trades == a.n_trades + b.n_trades
    assert pooled.per_ticker == {"AAA": a.n_trades, "BBB": b.n_trades}
    expected_mean = np.concatenate([a.r_series(), b.r_series()]).mean()
    assert np.isclose(pooled.expectancy_r, expected_mean)
    assert pooled.in_sample_n + pooled.out_sample_n == pooled.n_trades


def test_pool_trades_sorted_by_exit_date(synthetic_price):
    _, a, b = _two_results(synthetic_price)
    pooled = pool_trades([a, b], n_resamples=500, seed=42)
    all_trades = sorted(a.trades + b.trades, key=lambda t: t.exit_date)
    expected = np.array([t.r_multiple for t in all_trades])
    assert np.allclose(pooled.r_multiples, expected)


def test_cost_sweep_expectancy_is_non_increasing(monkeypatch, synthetic_price):
    # Avoid the network: feed the sweep our synthetic OHLCV.
    import expectancy.analysis.cost_sensitivity as cs

    monkeypatch.setattr(cs, "load_ohlcv", lambda *a, **k: synthetic_price)
    points = cost_sweep(Config(), (0.0, 0.05, 0.1, 0.2, 0.3))
    expectancies = [p.expectancy_r for p in points]
    # More slippage can never improve expectancy.
    assert all(later <= earlier + 1e-9 for earlier, later in zip(expectancies, expectancies[1:]))
    # Signals are cost-independent, so the trade count is identical across levels.
    assert len({p.n_trades for p in points}) == 1


def test_pooled_cost_curve_is_monotonic_and_reports_gross(monkeypatch, synthetic_price):
    import expectancy.analysis.cost_sensitivity as cs

    monkeypatch.setattr(cs, "load_ohlcv", lambda *a, **k: synthetic_price)
    curve = pooled_cost_curve([Config(), Config()], (0.0, 0.05, 0.1, 0.2, 0.3))
    ys = [p.expectancy_r for p in curve.points]
    assert all(later <= earlier + 1e-9 for earlier, later in zip(ys, ys[1:]))
    # Gross (zero costs) is the most favourable point — no costs can only help.
    assert curve.gross_expectancy_r >= ys[0] - 1e-9
    # Pooling two identical configs doubles the trade count.
    assert curve.points[0].n_trades > 0
