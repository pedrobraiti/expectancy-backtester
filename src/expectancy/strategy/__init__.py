"""Strategy layer: turn OHLCV into entry signals, stops and targets.

Strategies are pluggable — the engine never imports a concrete strategy, only
the :class:`Strategy` interface. Add a new strategy by subclassing it.
"""

from expectancy.strategy.base import Strategy, SignalColumns
from expectancy.strategy.ma_crossover import MACrossoverStrategy
from expectancy.strategy.rsi_reversion import RSIReversionStrategy
from expectancy.strategy.registry import build_strategy

__all__ = [
    "Strategy",
    "SignalColumns",
    "MACrossoverStrategy",
    "RSIReversionStrategy",
    "build_strategy",
]
