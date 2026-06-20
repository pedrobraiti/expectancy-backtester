"""Bootstrap confidence interval on the per-trade expectancy.

A point estimate of expectancy (e.g. +0.42R) means little without knowing how
wide its uncertainty is. With only ~40 trades, that uncertainty is enormous: the
interval almost always straddles zero, which is the honest way to say "we cannot
tell a small edge from no edge at this sample size."

The method resamples the realized R-multiples *with replacement* and recomputes
the mean each time; the 2.5th–97.5th percentiles of those means form a 95%
confidence interval. The same caveat the reviewer raised applies and is stated in
the report: this captures sampling variance *within the observed trades*, treating
them as representative — it does not capture the deeper uncertainty of whether 40
trades represent the strategy at all. The true uncertainty is therefore at least
this wide, never narrower.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ExpectancyCI:
    n: int
    mean_r: float
    ci_low: float
    ci_high: float
    prob_positive: float     # fraction of bootstrap means above zero
    confidence: float

    @property
    def distinguishable_from_zero(self) -> bool:
        """True only if the whole interval sits on one side of zero."""
        return self.ci_low > 0.0 or self.ci_high < 0.0

    @property
    def verdict(self) -> str:
        if self.n == 0:
            return "no trades"
        if not self.distinguishable_from_zero:
            return "indistinguishable from zero"
        return "positive" if self.ci_low > 0 else "negative"


def _ci_from_means(values: np.ndarray, means: np.ndarray, confidence: float) -> ExpectancyCI:
    alpha = 1.0 - confidence
    return ExpectancyCI(
        n=values.size,
        mean_r=float(values.mean()),
        ci_low=float(np.percentile(means, 100 * alpha / 2)),
        ci_high=float(np.percentile(means, 100 * (1 - alpha / 2))),
        prob_positive=float(np.mean(means > 0.0)),
        confidence=confidence,
    )


def bootstrap_mean_ci(
    values: np.ndarray,
    *,
    n_resamples: int = 10_000,
    seed: int = 42,
    confidence: float = 0.95,
) -> ExpectancyCI:
    """95% bootstrap CI for the mean of `values`, resampling trades i.i.d.

    Valid only when the observations are independent. For trades pooled across
    correlated instruments they are not, so use :func:`cluster_bootstrap_mean_ci`
    there — this i.i.d. version understates the uncertainty.
    """
    values = np.asarray(values, dtype=float)
    n = values.size
    if n == 0:
        return ExpectancyCI(0, 0.0, 0.0, 0.0, 0.5, confidence)

    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(n_resamples, n))
    means = values[idx].mean(axis=1)
    return _ci_from_means(values, means, confidence)


def cluster_bootstrap_mean_ci(
    values: np.ndarray,
    cluster_labels,
    *,
    n_resamples: int = 10_000,
    seed: int = 42,
    confidence: float = 0.95,
) -> ExpectancyCI:
    """95% CL bootstrap CI for the mean, resampling whole **clusters** with replacement.

    When observations are correlated *within* a cluster (e.g. trades from the same
    calendar quarter, where US indices and Brazilian names move together), an
    i.i.d. bootstrap shreds that correlation and reports a falsely tight interval.
    Resampling clusters keeps the dependence intact, so the effective sample size
    drops to roughly the number of clusters and the interval widens to the honest
    width. The mean statistic is exact: for a draw of clusters it equals
    ``sum(selected cluster sums) / sum(selected cluster sizes)``.
    """
    values = np.asarray(values, dtype=float)
    labels = np.asarray(cluster_labels)
    n = values.size
    if n == 0:
        return ExpectancyCI(0, 0.0, 0.0, 0.0, 0.5, confidence)

    unique = np.unique(labels)
    sums = np.array([values[labels == lab].sum() for lab in unique])
    counts = np.array([np.count_nonzero(labels == lab) for lab in unique])
    k = unique.size

    rng = np.random.default_rng(seed)
    idx = rng.integers(0, k, size=(n_resamples, k))
    means = sums[idx].sum(axis=1) / counts[idx].sum(axis=1)
    return _ci_from_means(values, means, confidence)
