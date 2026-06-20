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


def bootstrap_mean_ci(
    values: np.ndarray,
    *,
    n_resamples: int = 10_000,
    seed: int = 42,
    confidence: float = 0.95,
) -> ExpectancyCI:
    """95% bootstrap CI for the mean of `values` (the per-trade R-multiples)."""
    values = np.asarray(values, dtype=float)
    n = values.size
    if n == 0:
        return ExpectancyCI(0, 0.0, 0.0, 0.0, 0.5, confidence)

    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(n_resamples, n))
    means = values[idx].mean(axis=1)

    alpha = 1.0 - confidence
    ci_low = float(np.percentile(means, 100 * alpha / 2))
    ci_high = float(np.percentile(means, 100 * (1 - alpha / 2)))
    prob_positive = float(np.mean(means > 0.0))

    return ExpectancyCI(
        n=n,
        mean_r=float(values.mean()),
        ci_low=ci_low,
        ci_high=ci_high,
        prob_positive=prob_positive,
        confidence=confidence,
    )
