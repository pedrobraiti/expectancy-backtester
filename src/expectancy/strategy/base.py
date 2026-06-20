"""The pluggable Strategy interface.

A strategy receives OHLCV and returns the *same* frame with three extra columns
(:data:`SignalColumns`). The golden rule (brief §4): row ``t`` may only use data
up to row ``t`` — never the future. The engine enforces the t -> t+1 execution
delay on top of this, so even a correct strategy cannot peek.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from types import SimpleNamespace

import pandas as pd

SignalColumns = SimpleNamespace(SIGNAL="signal", STOP="stop", TARGET="target", EXIT="exit")
"""Names of the columns a strategy adds.

``signal``/``stop``/``target`` are required; ``exit`` is optional. An ``exit``
of 1 at a bar's close asks the engine to close the open position at the **next**
bar's open (lookahead-safe), which is how mean-reversion strategies that revert
on a condition (rather than hitting a fixed target) get out.
"""


class Strategy(ABC):
    """Base class for all strategies.

    Subclasses implement :meth:`generate_signals`, returning the input frame with:

    * ``signal``  -- 1 (go long), -1 (go short), 0 (do nothing) at this bar's close
    * ``stop``    -- stop-loss price for an entry taken on this signal
    * ``target``  -- take-profit price for that entry
    """

    name: str = "strategy"

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError

    @staticmethod
    def _empty_signal_frame(df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        out[SignalColumns.SIGNAL] = 0
        out[SignalColumns.STOP] = float("nan")
        out[SignalColumns.TARGET] = float("nan")
        out[SignalColumns.EXIT] = 0
        return out
