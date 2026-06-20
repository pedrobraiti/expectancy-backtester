"""A single closed trade — the atomic output of the engine.

Each trade carries enough to rebuild every metric and the equity curve: the
prices it was filled at, the costs it paid, its result in money *and* in R, and
the equity right after it closed.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Trade:
    entry_date: datetime
    exit_date: datetime
    side: int                 # +1 long, -1 short
    entry_price: float        # realistic fill, costs folded in
    exit_price: float         # realistic fill, costs folded in
    stop_price: float
    target_price: float
    size: float               # units/shares
    risk_per_unit: float      # |entry_intended - stop|, price units
    risk_money: float         # cash put at risk on this trade
    gross_pnl: float          # before commission
    commission_paid: float
    pnl_money: float          # net result in cash
    r_multiple: float         # net result expressed in R
    exit_reason: str          # "stop" | "target" | "end_of_data"
    equity_after: float       # account equity right after this trade closed

    @property
    def is_win(self) -> bool:
        return self.pnl_money > 0
