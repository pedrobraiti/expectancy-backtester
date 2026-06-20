"""Simulation layer: turn signals into a list of closed trades and an equity curve."""

from expectancy.engine.trade import Trade
from expectancy.engine.costs import CostModel
from expectancy.engine.sizing import position_size, lot_size
from expectancy.engine.engine import BacktestEngine, BacktestResult

__all__ = [
    "Trade",
    "CostModel",
    "position_size",
    "lot_size",
    "BacktestEngine",
    "BacktestResult",
]
