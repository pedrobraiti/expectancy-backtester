"""Moving-average crossover with ATR-based stop and target.

The "factory default" strategy from the brief (§4). Rules:

* A **fast** SMA crossing **above** a **slow** SMA at the close of bar ``t`` is a
  long signal; crossing below is a short signal (or a no-op when long-only).
* The stop sits ``stop_atr_mult`` ATRs away from the close, the target
  ``target_atr_mult`` ATRs away — so the risk/reward geometry adapts to each
  instrument's volatility instead of using fixed cents.

It is deliberately simple and *not* assumed to have an edge: its job is to give
the engine and the maths something real to chew on. The crossover is detected by
comparing the current fast-vs-slow relationship to the previous bar's, both of
which are known at ``t`` — no lookahead.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from expectancy.strategy.base import SignalColumns, Strategy
from expectancy.strategy.indicators import average_true_range, sma


class MACrossoverStrategy(Strategy):
    name = "ma_crossover"

    def __init__(
        self,
        fast_ma: int = 20,
        slow_ma: int = 50,
        atr_period: int = 14,
        stop_atr_mult: float = 1.5,
        target_atr_mult: float = 3.0,
        direction: str = "long_only",
    ) -> None:
        if fast_ma >= slow_ma:
            raise ValueError(f"fast_ma ({fast_ma}) must be < slow_ma ({slow_ma})")
        self.fast_ma = fast_ma
        self.slow_ma = slow_ma
        self.atr_period = atr_period
        self.stop_atr_mult = stop_atr_mult
        self.target_atr_mult = target_atr_mult
        self.direction = direction

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        out = self._empty_signal_frame(df)

        fast = sma(out["Close"], self.fast_ma)
        slow = sma(out["Close"], self.slow_ma)
        atr = average_true_range(out, self.atr_period)

        # `fast > slow` yields False wherever either MA is NaN, so the boolean
        # series stays clean. `valid` then suppresses the first comparable bar,
        # where no previous relationship exists to cross.
        fast_above = fast > slow
        prev_fast_above = fast_above.shift(1, fill_value=False)
        valid = fast.notna() & slow.notna() & fast.shift(1).notna() & slow.shift(1).notna()

        cross_up = fast_above & ~prev_fast_above & valid
        cross_down = ~fast_above & prev_fast_above & valid

        long_short = self.direction == "long_short"
        signal = np.where(cross_up, 1, np.where(cross_down & long_short, -1, 0))
        signal = pd.Series(signal, index=out.index)
        # No ATR yet -> cannot define risk -> not a tradeable signal.
        signal = signal.where(atr.notna(), 0)

        close = out["Close"]
        long_stop = close - self.stop_atr_mult * atr
        long_target = close + self.target_atr_mult * atr
        short_stop = close + self.stop_atr_mult * atr
        short_target = close - self.target_atr_mult * atr

        stop = pd.Series(np.nan, index=out.index)
        target = pd.Series(np.nan, index=out.index)
        stop = stop.mask(signal == 1, long_stop).mask(signal == -1, short_stop)
        target = target.mask(signal == 1, long_target).mask(signal == -1, short_target)

        out[SignalColumns.SIGNAL] = signal.astype(int)
        out[SignalColumns.STOP] = stop
        out[SignalColumns.TARGET] = target
        return out
