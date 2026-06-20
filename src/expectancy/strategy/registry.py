"""Map a strategy name + config onto a concrete Strategy instance.

Keeps `main.py` and the study scripts from importing concrete strategies
directly, so adding a strategy means registering it here and nowhere else.
"""

from __future__ import annotations

from expectancy.config import StrategyConfig
from expectancy.strategy.base import Strategy
from expectancy.strategy.ma_crossover import MACrossoverStrategy
from expectancy.strategy.rsi_reversion import RSIReversionStrategy


def build_strategy(cfg: StrategyConfig) -> Strategy:
    if cfg.name == "ma_crossover":
        return MACrossoverStrategy(
            fast_ma=cfg.fast_ma,
            slow_ma=cfg.slow_ma,
            atr_period=cfg.atr_period,
            stop_atr_mult=cfg.stop_atr_mult,
            target_atr_mult=cfg.target_atr_mult,
            direction=cfg.direction,
        )
    if cfg.name == "rsi_reversion":
        return RSIReversionStrategy(
            rsi_period=cfg.rsi_period,
            rsi_entry=cfg.rsi_entry,
            rsi_exit=cfg.rsi_exit,
            trend_filter_ma=cfg.trend_filter_ma,
            atr_period=cfg.atr_period,
            stop_atr_mult=cfg.stop_atr_mult,
        )
    raise ValueError(f"unknown strategy '{cfg.name}'")
