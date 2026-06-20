"""The event-driven simulation engine — the most delicate part of the system.

What it guarantees (brief §5):

* **No lookahead.** A signal printed at the close of bar ``t`` is executed at the
  **open of bar ``t+1``**. The engine literally cannot fill at the price that
  produced the signal.
* **Conservative intrabar fills.** If a bar's range touches both the stop and the
  target, the stop is assumed to fill first (worst case). No optimistic guessing.
* **Costs on every fill** and **fixed-fractional risk** sizing.
* Each closed trade stores its result in **money and in R**, plus the running
  equity, so the metrics and Monte-Carlo layers need nothing else.

The engine is strategy-agnostic: it only reads ``signal``, ``stop`` and
``target`` columns and the OHLC.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from expectancy.config import Config
from expectancy.engine.costs import CostModel
from expectancy.engine.sizing import position_size
from expectancy.engine.trade import Trade
from expectancy.strategy.base import SignalColumns


@dataclass
class BacktestResult:
    trades: list[Trade]
    equity_curve: pd.Series        # equity after each closed trade, indexed by exit date
    initial_capital: float
    final_equity: float
    ticker: str

    @property
    def n_trades(self) -> int:
        return len(self.trades)

    def r_series(self) -> np.ndarray:
        return np.array([t.r_multiple for t in self.trades], dtype=float)

    def pnl_series(self) -> np.ndarray:
        return np.array([t.pnl_money for t in self.trades], dtype=float)


class BacktestEngine:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.costs = CostModel(config.costs)

    def run(self, signals: pd.DataFrame, ticker: str | None = None) -> BacktestResult:
        cfg = self.config
        risk_fraction = cfg.risk_per_trade_pct / 100.0

        dates = signals.index.to_numpy()
        open_ = signals["Open"].to_numpy(dtype=float)
        high = signals["High"].to_numpy(dtype=float)
        low = signals["Low"].to_numpy(dtype=float)
        close = signals["Close"].to_numpy(dtype=float)
        signal = signals[SignalColumns.SIGNAL].to_numpy(dtype=float)
        stop_col = signals[SignalColumns.STOP].to_numpy(dtype=float)
        target_col = signals[SignalColumns.TARGET].to_numpy(dtype=float)
        if SignalColumns.EXIT in signals.columns:
            exit_col = signals[SignalColumns.EXIT].to_numpy(dtype=float)
        else:
            exit_col = np.zeros(len(signals), dtype=float)
        max_holding = cfg.strategy.max_holding_bars

        n = len(signals)
        equity = cfg.initial_capital
        trades: list[Trade] = []
        equity_dates: list = []
        equity_values: list[float] = []

        in_position = False
        i = 0
        # State for the currently open trade.
        side = 0
        entry_idx = 0
        entry_fill = 0.0
        stop_price = 0.0
        target_price = 0.0
        size = 0.0
        risk_per_unit = 0.0
        risk_money = 0.0
        commission_entry = 0.0
        pending_exit = False    # an exit signal / max-hold fired last bar -> fill at this open
        bars_held = 0

        while i < n:
            if not in_position:
                sig = signal[i]
                # Need a real signal, a defined stop, and a next bar to execute on.
                if sig != 0 and not np.isnan(stop_col[i]) and i + 1 < n:
                    j = i + 1  # execution bar (t+1)
                    bar_range = high[j] - low[j]
                    side = int(sig)
                    entry_fill = self.costs.entry_fill(side, open_[j], bar_range)
                    stop_price = float(stop_col[i])
                    target_price = float(target_col[i])
                    risk_per_unit = abs(entry_fill - stop_price)

                    risk_money = equity * risk_fraction
                    size = position_size(risk_money, risk_per_unit)
                    if size <= 0:
                        i += 1
                        continue

                    commission_entry = self.costs.commission_per_order()
                    entry_idx = j
                    in_position = True
                    pending_exit = False
                    bars_held = 0
                    i = j  # the entry bar itself can hit stop/target
                    continue
                i += 1
                continue

            # --- managing an open position ---
            bar_range = high[i] - low[i]
            exit_reason = None
            raw_exit = None

            # A signal/max-hold exit raised on the previous bar fills at THIS open,
            # which happens before any intrabar stop/target on this bar.
            if pending_exit:
                exit_reason, raw_exit = "signal", open_[i]
            else:
                if side == 1:
                    hit_stop = low[i] <= stop_price
                    hit_target = high[i] >= target_price
                else:
                    hit_stop = high[i] >= stop_price
                    hit_target = low[i] <= target_price

                if hit_stop and hit_target:
                    # Conservative: assume the stop filled first (worst case).
                    exit_reason, raw_exit = "stop", stop_price
                elif hit_stop:
                    exit_reason, raw_exit = "stop", stop_price
                elif hit_target:
                    exit_reason, raw_exit = "target", target_price
                elif i == n - 1:
                    exit_reason, raw_exit = "end_of_data", close[i]

            if exit_reason is None:
                # Still in the trade: decide whether to schedule an exit for next open.
                bars_held += 1
                exit_signal_fired = exit_col[i] != 0
                max_hold_hit = max_holding > 0 and bars_held >= max_holding
                if exit_signal_fired or max_hold_hit:
                    pending_exit = True
                i += 1
                continue

            exit_fill = self.costs.exit_fill(side, raw_exit, bar_range)
            commission_exit = self.costs.commission_per_order()
            commission_paid = commission_entry + commission_exit

            gross_pnl = side * (exit_fill - entry_fill) * size
            pnl_money = gross_pnl - commission_paid
            r_multiple = pnl_money / risk_money if risk_money > 0 else 0.0
            equity += pnl_money

            trades.append(
                Trade(
                    entry_date=pd.Timestamp(dates[entry_idx]).to_pydatetime(),
                    exit_date=pd.Timestamp(dates[i]).to_pydatetime(),
                    side=side,
                    entry_price=entry_fill,
                    exit_price=exit_fill,
                    stop_price=stop_price,
                    target_price=target_price,
                    size=size,
                    risk_per_unit=risk_per_unit,
                    risk_money=risk_money,
                    gross_pnl=gross_pnl,
                    commission_paid=commission_paid,
                    pnl_money=pnl_money,
                    r_multiple=r_multiple,
                    exit_reason=exit_reason,
                    equity_after=equity,
                )
            )
            equity_dates.append(dates[i])
            equity_values.append(equity)

            in_position = False
            pending_exit = False
            bars_held = 0
            # Re-evaluate the *same* bar for a fresh entry signal next loop.
            i += 1

        equity_curve = pd.Series(equity_values, index=pd.to_datetime(equity_dates), name="equity")
        return BacktestResult(
            trades=trades,
            equity_curve=equity_curve,
            initial_capital=cfg.initial_capital,
            final_equity=equity,
            ticker=ticker or cfg.ticker,
        )
