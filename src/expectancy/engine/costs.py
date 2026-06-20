"""Transaction-cost model.

The brief is explicit (§5.3): without costs, expectancy "on paper" lies. Three
components are charged on every fill:

* **spread** -- you buy at the ask and sell at the bid; modelled as half the
  spread moved against you on each side (so a round trip pays the full spread).
* **slippage** -- the fill drifts from the intended price by a fraction of the
  bar's range, always adverse (you get a worse price than you hoped).
* **commission** -- a flat cash charge per order (entry and exit are two orders),
  handled separately in money because it does not live in the price.

Folding spread + slippage into the *fill price* keeps the R-multiple honest:
a trade stopped out loses slightly more than 1R, exactly as in real life.
"""

from __future__ import annotations

from expectancy.config import CostConfig


class CostModel:
    def __init__(self, cfg: CostConfig) -> None:
        self.spread = cfg.spread
        self.commission = cfg.commission
        self.slippage_frac = cfg.slippage_frac

    def _price_penalty(self, bar_range: float) -> float:
        """Adverse price move applied to a fill: half-spread + slippage."""
        slippage = self.slippage_frac * max(bar_range, 0.0)
        return self.spread / 2.0 + slippage

    def entry_fill(self, side: int, raw_price: float, bar_range: float) -> float:
        """Realistic entry price. Longs pay up, shorts sell down."""
        return raw_price + side * self._price_penalty(bar_range)

    def exit_fill(self, side: int, raw_price: float, bar_range: float) -> float:
        """Realistic exit price. Closing a long sells down, closing a short buys up."""
        return raw_price - side * self._price_penalty(bar_range)

    def commission_per_order(self) -> float:
        return self.commission
