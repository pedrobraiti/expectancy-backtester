"""Analysis layer: does the measured edge survive statistical scrutiny?

The metrics layer reports point estimates; this layer asks whether those
estimates mean anything given the sample size. It is the honest counterweight to
the scorecard:

* ``significance`` -- bootstrap confidence interval on the per-trade expectancy,
  so a positive point estimate that is indistinguishable from zero is exposed.
* ``pooled``       -- aggregate every instrument's trades into one stream to gain
  the sample size no single instrument has, plus an out-of-sample time split.
* ``cost_sensitivity`` -- how fast the thin edge dies as transaction costs rise.
"""

from expectancy.analysis.significance import ExpectancyCI, bootstrap_mean_ci
from expectancy.analysis.pooled import PooledResult, pool_trades
from expectancy.analysis.cost_sensitivity import CostPoint, cost_sweep

__all__ = [
    "ExpectancyCI",
    "bootstrap_mean_ci",
    "PooledResult",
    "pool_trades",
    "CostPoint",
    "cost_sweep",
]
