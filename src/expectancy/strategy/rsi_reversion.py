"""RSI(2) mean-reversion — a Connors-style strategy that trades *often*.

The whole point of adding this strategy is statistical power. A moving-average
crossover fires ~2.5 times a year, far too rarely to validate anything. A short
pullback strategy fires whenever the market dips while in an uptrend — dozens of
times a year per instrument — so a basket produces thousands of trades, enough
for the confidence interval to actually exclude (or tightly bound) zero.

Rules (long-only):

* **Trend filter** -- only trade when the close is above its long SMA (default
  200), so we buy dips inside uptrends, not falling knives.
* **Entry** -- the fast RSI (default period 2) drops below an oversold threshold
  (default 10): a short-term washout.
* **Exit** -- the fast RSI recovers above an exit threshold (default 60); the
  engine closes the position at the next open. A wide ATR stop bounds the risk
  (and defines R); a max-holding cap prevents a trade from lingering forever.

Every value at bar t uses only data through t; the engine still executes entries
and signalled exits at t+1's open, so there is no lookahead.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from expectancy.strategy.base import SignalColumns, Strategy
from expectancy.strategy.indicators import average_true_range, rsi, sma


class RSIReversionStrategy(Strategy):
    name = "rsi_reversion"

    def __init__(
        self,
        rsi_period: int = 2,
        rsi_entry: float = 10.0,
        rsi_exit: float = 60.0,
        trend_filter_ma: int = 200,
        atr_period: int = 14,
        stop_atr_mult: float = 2.5,
    ) -> None:
        self.rsi_period = rsi_period
        self.rsi_entry = rsi_entry
        self.rsi_exit = rsi_exit
        self.trend_filter_ma = trend_filter_ma
        self.atr_period = atr_period
        self.stop_atr_mult = stop_atr_mult

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        out = self._empty_signal_frame(df)
        close = out["Close"]

        fast_rsi = rsi(close, self.rsi_period)
        trend = sma(close, self.trend_filter_ma)
        atr = average_true_range(out, self.atr_period)

        in_uptrend = close > trend
        oversold = fast_rsi < self.rsi_entry
        entry = in_uptrend & oversold & atr.notna() & trend.notna()

        signal = np.where(entry, 1, 0)
        stop = pd.Series(np.nan, index=out.index)
        stop = stop.mask(entry, close - self.stop_atr_mult * atr)

        # Exit when the short-term oversold condition has unwound.
        exit_signal = (fast_rsi > self.rsi_exit).astype(int)

        out[SignalColumns.SIGNAL] = signal.astype(int)
        out[SignalColumns.STOP] = stop
        out[SignalColumns.TARGET] = np.nan      # no fixed target; exit is signal-driven
        out[SignalColumns.EXIT] = exit_signal
        return out
