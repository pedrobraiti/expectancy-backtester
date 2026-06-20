"""expectancy — a rules-based backtester that measures the mathematical
fingerprint of a trading system: expectancy, variance, risk/reward tradeoff
and risk of ruin.

The package keeps four layers strictly separate, mirroring the brief:
    data       -> raw OHLCV from Yahoo Finance (the only thing that is *downloaded*)
    strategy   -> rules that turn OHLCV into entry signals, stops and targets
    engine     -> trade-by-trade simulation (costs, sizing, no lookahead)
    metrics    -> the "scorecard" computed *from the trades*
    montecarlo -> variance, risk of ruin and recovery math
    reporting  -> terminal summary, figures and the PDF report
"""

__version__ = "1.0.0"
