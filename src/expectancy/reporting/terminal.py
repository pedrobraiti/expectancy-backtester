"""Render the full "scorecard" as a clean terminal report (brief §9).

Pure formatting: it reads a :class:`RunBundle` and returns a string. No I/O
beyond the optional print, so it is trivially testable.
"""

from __future__ import annotations

import math
import sys

from expectancy.metrics.metrics import MIN_RELIABLE_TRADES
from expectancy.runner import RunBundle

_WIDTH = 64


def _rule(char: str = "─") -> str:
    return char * _WIDTH


def _money(value: float) -> str:
    return f"{value:,.2f}"


def _pf(value: float) -> str:
    return "inf" if math.isinf(value) else f"{value:.2f}"


def format_report(bundle: RunBundle) -> str:
    m = bundle.metrics
    cfg = bundle.config
    lines: list[str] = []
    add = lines.append

    add(_rule("═"))
    add(f" EXPECTANCY BACKTEST — {cfg.ticker}")
    add(f" {cfg.strategy.name}  |  {cfg.start} → {cfg.end}  |  {cfg.interval}")
    add(_rule("═"))

    if m.n_trades == 0:
        add(" No trades were generated for this configuration.")
        add(_rule("═"))
        return "\n".join(lines)

    add("")
    add(" THE SCORECARD")
    add(_rule())
    add(f"  Trades                    {m.n_trades}")
    add(f"  Win rate                  {m.win_rate * 100:6.2f}%   (loss {m.loss_rate * 100:.2f}%)")
    add(f"  Avg win                   {_money(m.avg_win_money):>12}  ({m.avg_win_r:+.2f} R)")
    add(f"  Avg loss                  {_money(-m.avg_loss_money):>12}  ({-m.avg_loss_r:+.2f} R)")
    add(f"  Payoff (avg win/loss R)   {_pf(m.payoff_ratio):>12}")
    add(_rule())
    add(f"  EXPECTANCY / trade        {_money(m.expectancy_money):>12}  ({m.expectancy_r:+.3f} R)")
    ci = bundle.expectancy_ci
    add(f"  95% CI on expectancy R    [{ci.ci_low:+.3f}, {ci.ci_high:+.3f}]  → {ci.verdict}")
    add(f"  Profit factor             {_pf(m.profit_factor):>12}")
    add(_rule())
    add(f"  Breakeven win rate        {m.breakeven_win_rate * 100:6.2f}%   (need this to not lose)")
    add(f"  Actual win rate           {m.win_rate * 100:6.2f}%   "
        f"({'margin ✓' if m.win_rate > m.breakeven_win_rate else 'below ✗'})")
    add(_rule())
    add(f"  Initial → final capital   {_money(m.initial_capital)} → {_money(m.final_equity)}")
    add(f"  Total return              {m.total_return_pct:+.2f}%   (CAGR {m.cagr_pct:+.2f}%)")
    add(f"  Max drawdown              {m.max_drawdown_pct:.2f}%   ({_money(m.max_drawdown_money)})")
    add(f"  Sharpe / Sortino          {m.sharpe:.2f} / {m.sortino:.2f}")
    add(_rule())
    add(f"  Expectancy sanity check   {'PASS ✓' if m.expectancy_check_ok else 'FAIL ✗'}  "
        f"(formula == realized mean)")

    add("")
    add(" VARIANCE — same edge, different luck (5,000 bootstraps)")
    add(_rule())
    mc = bundle.montecarlo
    add(f"  Median final equity       {_money(mc.median_final)}")
    add(f"  5th – 95th percentile     {_money(mc.p5_final)}  …  {_money(mc.p95_final)}")
    add(f"  Worst / best case         {_money(mc.worst_final)}  /  {_money(mc.best_final)}")
    add(f"  P(end below start)        {mc.prob_loss * 100:.1f}%")

    add("")
    add(f" RISK OF RUIN — P(drawdown ≥ {int(bundle.ruin[0].drawdown_target_pct)}%) by risk per trade")
    add(_rule())
    for row in bundle.ruin:
        bar = "█" * int(round(row.probability * 30))
        add(f"  {row.risk_level_pct:>4.2f}% risk   {row.probability * 100:6.2f}%  {bar}")
    add("  (watch how it explodes non-linearly as risk rises)")

    add("")
    add(" THE RECOVERY MATH — why protecting capital wins")
    add(_rule())
    add("  Drawdown      Gain needed to recover")
    for loss, gain in bundle.recovery:
        gain_str = "∞" if math.isinf(gain) else f"{gain * 100:.0f}%"
        add(f"   {loss * 100:>3.0f}%            {gain_str:>5}")

    if not m.sample_is_reliable:
        add("")
        add(_rule("!"))
        add(f"  ⚠  SMALL SAMPLE: only {m.n_trades} trades (< {MIN_RELIABLE_TRADES}).")
        add("     The expectancy estimate is noise-dominated and its 95% CI above")
        add(f"     {'straddles zero — a small edge cannot be told apart from none.' if not bundle.expectancy_ci.distinguishable_from_zero else 'is one-sided, but the sample is still thin — stay skeptical.'}")
        add("     One trade means nothing; a hundred start to mean something.")
        add(_rule("!"))

    add(_rule("═"))
    return "\n".join(lines)


def print_report(bundle: RunBundle) -> None:
    # The report uses Unicode box-drawing glyphs; Windows consoles default to
    # cp1252 and would crash on them. Switch stdout to UTF-8 when we can.
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass
    print(format_report(bundle))
