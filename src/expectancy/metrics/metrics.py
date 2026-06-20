"""All the metrics from the brief's "scorecard" (§6), computed from the trades.

The cardinal rule: these are *results of the simulation*, never downloaded
numbers. Expectancy is reported both in money and in R, and a sanity check
asserts the per-trade mean equals the textbook ``WR*avg_win - LR*avg_loss``
formula — if it does not, there is a bug.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

from expectancy.engine.engine import BacktestResult

MIN_RELIABLE_TRADES = 100
"""Below this, expectancy is dominated by noise (brief §8) — caller should warn."""

TRADING_DAYS_PER_YEAR = 252


@dataclass(frozen=True)
class Metrics:
    n_trades: int
    win_rate: float
    loss_rate: float
    avg_win_money: float
    avg_loss_money: float          # stored as a positive magnitude
    avg_win_r: float
    avg_loss_r: float              # positive magnitude
    expectancy_money: float
    expectancy_r: float
    profit_factor: float
    breakeven_win_rate: float      # 1 / (R + 1), R = avg_win_r / avg_loss_r
    avg_r_per_trade: float
    payoff_ratio: float            # avg_win_r / avg_loss_r
    gross_profit: float
    gross_loss: float              # positive magnitude
    initial_capital: float
    final_equity: float
    total_return_pct: float
    cagr_pct: float
    max_drawdown_pct: float
    max_drawdown_money: float
    sharpe: float
    sortino: float
    expectancy_check_ok: bool
    sample_is_reliable: bool

    @property
    def has_edge(self) -> bool:
        return self.expectancy_r > 0


def max_drawdown(equity_curve: pd.Series, initial_capital: float) -> tuple[float, float]:
    """Largest peak-to-trough drop. Returns ``(pct, money)`` as positive numbers."""
    if equity_curve.empty:
        return 0.0, 0.0
    curve = pd.concat([pd.Series([initial_capital]), equity_curve.reset_index(drop=True)])
    running_peak = curve.cummax()
    drawdown_money = running_peak - curve
    drawdown_pct = drawdown_money / running_peak
    return float(drawdown_pct.max() * 100.0), float(drawdown_money.max())


def expectancy_sanity_check(
    avg_win: float, avg_loss_magnitude: float, win_rate: float, realized_mean: float, tol: float = 1e-6
) -> bool:
    """The formula ``WR*avg_win - LR*avg_loss`` must equal the realized mean."""
    formula = win_rate * avg_win - (1.0 - win_rate) * avg_loss_magnitude
    return abs(formula - realized_mean) <= tol * max(1.0, abs(realized_mean))


def recovery_required(loss_fraction: float) -> float:
    """Gain needed to recover a given drawdown: ``1/(1-loss) - 1`` (brief §7.3)."""
    if loss_fraction >= 1.0:
        return math.inf
    return 1.0 / (1.0 - loss_fraction) - 1.0


def _annualization_factor(result: BacktestResult) -> float:
    """Years spanned by the trade sequence, for CAGR/Sharpe annualization."""
    if result.n_trades < 2:
        return 1.0
    span = result.trades[-1].exit_date - result.trades[0].entry_date
    years = span.days / 365.25
    return max(years, 1e-9)


def compute_metrics(result: BacktestResult) -> Metrics:
    r = result.r_series()
    pnl = result.pnl_series()
    n = len(r)

    if n == 0:
        return _empty_metrics(result)

    wins_mask = pnl > 0
    losses_mask = pnl < 0
    n_wins = int(wins_mask.sum())

    win_rate = n_wins / n
    loss_rate = 1.0 - win_rate

    win_pnl = pnl[wins_mask]
    loss_pnl = pnl[losses_mask]
    win_r = r[wins_mask]
    loss_r = r[losses_mask]

    avg_win_money = float(win_pnl.mean()) if win_pnl.size else 0.0
    avg_loss_money = float(-loss_pnl.mean()) if loss_pnl.size else 0.0
    avg_win_r = float(win_r.mean()) if win_r.size else 0.0
    avg_loss_r = float(-loss_r.mean()) if loss_r.size else 0.0

    expectancy_money = float(pnl.mean())
    expectancy_r = float(r.mean())

    gross_profit = float(win_pnl.sum()) if win_pnl.size else 0.0
    gross_loss = float(-loss_pnl.sum()) if loss_pnl.size else 0.0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else math.inf

    payoff_ratio = avg_win_r / avg_loss_r if avg_loss_r > 0 else math.inf
    breakeven_win_rate = 1.0 / (payoff_ratio + 1.0) if math.isfinite(payoff_ratio) else 0.0

    dd_pct, dd_money = max_drawdown(result.equity_curve, result.initial_capital)

    total_return_pct = (result.final_equity / result.initial_capital - 1.0) * 100.0
    years = _annualization_factor(result)
    growth = result.final_equity / result.initial_capital
    cagr_pct = ((growth ** (1.0 / years)) - 1.0) * 100.0 if growth > 0 else -100.0

    sharpe, sortino = _per_trade_ratios(pnl, n, years)

    check_ok = expectancy_sanity_check(avg_win_money, avg_loss_money, win_rate, expectancy_money)

    return Metrics(
        n_trades=n,
        win_rate=win_rate,
        loss_rate=loss_rate,
        avg_win_money=avg_win_money,
        avg_loss_money=avg_loss_money,
        avg_win_r=avg_win_r,
        avg_loss_r=avg_loss_r,
        expectancy_money=expectancy_money,
        expectancy_r=expectancy_r,
        profit_factor=profit_factor,
        breakeven_win_rate=breakeven_win_rate,
        avg_r_per_trade=expectancy_r,
        payoff_ratio=payoff_ratio,
        gross_profit=gross_profit,
        gross_loss=gross_loss,
        initial_capital=result.initial_capital,
        final_equity=result.final_equity,
        total_return_pct=total_return_pct,
        cagr_pct=cagr_pct,
        max_drawdown_pct=dd_pct,
        max_drawdown_money=dd_money,
        sharpe=sharpe,
        sortino=sortino,
        expectancy_check_ok=check_ok,
        sample_is_reliable=n >= MIN_RELIABLE_TRADES,
    )


def _per_trade_ratios(pnl: np.ndarray, n: int, years: float) -> tuple[float, float]:
    """Sharpe and Sortino on the per-trade return stream, annualized by trade frequency."""
    returns = pnl / np.abs(pnl).mean() if np.abs(pnl).mean() > 0 else pnl
    std = returns.std(ddof=1) if n > 1 else 0.0
    mean = returns.mean()
    trades_per_year = n / years if years > 0 else n

    sharpe = (mean / std) * math.sqrt(trades_per_year) if std > 0 else 0.0

    downside = returns[returns < 0]
    downside_std = downside.std(ddof=1) if downside.size > 1 else 0.0
    sortino = (mean / downside_std) * math.sqrt(trades_per_year) if downside_std > 0 else 0.0
    return float(sharpe), float(sortino)


def _empty_metrics(result: BacktestResult) -> Metrics:
    return Metrics(
        n_trades=0,
        win_rate=0.0,
        loss_rate=0.0,
        avg_win_money=0.0,
        avg_loss_money=0.0,
        avg_win_r=0.0,
        avg_loss_r=0.0,
        expectancy_money=0.0,
        expectancy_r=0.0,
        profit_factor=0.0,
        breakeven_win_rate=0.0,
        avg_r_per_trade=0.0,
        payoff_ratio=0.0,
        gross_profit=0.0,
        gross_loss=0.0,
        initial_capital=result.initial_capital,
        final_equity=result.final_equity,
        total_return_pct=0.0,
        cagr_pct=0.0,
        max_drawdown_pct=0.0,
        max_drawdown_money=0.0,
        sharpe=0.0,
        sortino=0.0,
        expectancy_check_ok=True,
        sample_is_reliable=False,
    )
