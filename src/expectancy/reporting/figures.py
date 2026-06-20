"""Matplotlib figures for the report and the README (brief §9).

Every figure is generated straight from a :class:`RunBundle` (or a list of them
for the cross-instrument comparisons) — nothing is hand-drawn. A single house
style keeps the whole report visually consistent.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from expectancy.runner import RunBundle

# House palette — calm, professional, colour-blind friendly enough.
INK = "#1b1f24"
GRID = "#d7dde3"
ACCENT = "#1f6feb"      # blue   — primary series
POSITIVE = "#2da44e"    # green  — gains / good
NEGATIVE = "#cf222e"    # red    — losses / risk
MUTED = "#8b949e"       # grey   — context
BAND = "#9ec5ff"        # light blue — uncertainty band


def set_style() -> None:
    plt.rcParams.update(
        {
            "figure.dpi": 120,
            "savefig.dpi": 150,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": INK,
            "axes.labelcolor": INK,
            "axes.titlecolor": INK,
            "axes.titlesize": 13,
            "axes.titleweight": "bold",
            "axes.labelsize": 10,
            "axes.grid": True,
            "grid.color": GRID,
            "grid.linewidth": 0.8,
            "xtick.color": INK,
            "ytick.color": INK,
            "font.size": 10,
            "legend.frameon": False,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )


def _equity_with_start(bundle: RunBundle) -> pd.Series:
    curve = bundle.result.equity_curve
    start_idx = pd.Timestamp(bundle.result.trades[0].entry_date)
    start = pd.Series([bundle.result.initial_capital], index=[start_idx])
    return pd.concat([start, curve])


def fig_equity_curve(bundle: RunBundle, path: Path) -> Path:
    set_style()
    curve = _equity_with_start(bundle)
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(curve.index, curve.values, color=ACCENT, linewidth=1.8)
    ax.axhline(bundle.result.initial_capital, color=MUTED, linewidth=1.0, linestyle="--")
    ax.fill_between(
        curve.index, bundle.result.initial_capital, curve.values,
        where=curve.values >= bundle.result.initial_capital, color=POSITIVE, alpha=0.10,
    )
    ax.fill_between(
        curve.index, bundle.result.initial_capital, curve.values,
        where=curve.values < bundle.result.initial_capital, color=NEGATIVE, alpha=0.10,
    )
    ax.set_title(f"Equity curve — {bundle.config.ticker}")
    ax.set_ylabel("Account equity")
    ax.set_xlabel("Date")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def fig_underwater(bundle: RunBundle, path: Path) -> Path:
    set_style()
    curve = _equity_with_start(bundle)
    running_peak = curve.cummax()
    drawdown = (curve - running_peak) / running_peak * 100.0

    fig, ax = plt.subplots(figsize=(9, 3.6))
    ax.fill_between(drawdown.index, drawdown.values, 0, color=NEGATIVE, alpha=0.25)
    ax.plot(drawdown.index, drawdown.values, color=NEGATIVE, linewidth=1.2)
    ax.set_title(f"Underwater plot (drawdown) — {bundle.config.ticker}")
    ax.set_ylabel("Drawdown (%)")
    ax.set_xlabel("Date")
    ax.set_ylim(min(drawdown.min() * 1.1, -1), 1)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def fig_montecarlo_fan(bundle: RunBundle, path: Path) -> Path:
    set_style()
    mc = bundle.montecarlo
    pct = mc.equity_paths_percentiles
    x = np.arange(len(pct[50]))

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.fill_between(x, pct[5], pct[95], color=BAND, alpha=0.55, label="5–95% band")
    ax.plot(x, pct[50], color=ACCENT, linewidth=2.0, label="Median path")

    real = [bundle.result.initial_capital] + [t.equity_after for t in bundle.result.trades]
    ax.plot(np.arange(len(real)), real, color=INK, linewidth=1.3, linestyle="--", label="Realized path")

    ax.axhline(bundle.result.initial_capital, color=MUTED, linewidth=1.0, linestyle=":")
    ax.set_title(f"Monte-Carlo fan — variance changes everything ({bundle.config.ticker})")
    ax.set_ylabel("Account equity")
    ax.set_xlabel("Trade number")
    ax.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def fig_montecarlo_histogram(bundle: RunBundle, path: Path) -> Path:
    set_style()
    mc = bundle.montecarlo
    fig, ax = plt.subplots(figsize=(9, 4.0))
    ax.hist(mc.final_equities, bins=60, color=ACCENT, alpha=0.75, edgecolor="white", linewidth=0.4)
    ax.axvline(bundle.result.initial_capital, color=NEGATIVE, linewidth=1.6, linestyle="--", label="Start")
    ax.axvline(mc.median_final, color=POSITIVE, linewidth=1.6, label="Median")
    ax.axvline(mc.p5_final, color=MUTED, linewidth=1.2, linestyle=":", label="5th / 95th pct")
    ax.axvline(mc.p95_final, color=MUTED, linewidth=1.2, linestyle=":")
    ax.set_title(f"Distribution of final equity across {mc.n_simulations:,} simulations ({bundle.config.ticker})")
    ax.set_ylabel("Frequency")
    ax.set_xlabel("Final equity")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def fig_expectancy_convergence(bundle: RunBundle, path: Path) -> Path:
    """Cumulative expectancy in R vs trade count — 'one trade means nothing' (§8)."""
    set_style()
    r = bundle.result.r_series()
    if r.size == 0:
        return path
    cumulative = np.cumsum(r) / np.arange(1, r.size + 1)

    fig, ax = plt.subplots(figsize=(9, 4.0))
    ax.plot(np.arange(1, r.size + 1), cumulative, color=ACCENT, linewidth=1.6)
    ax.axhline(bundle.metrics.expectancy_r, color=POSITIVE, linewidth=1.2, linestyle="--",
               label=f"Final {bundle.metrics.expectancy_r:+.3f} R")
    ax.axhline(0, color=MUTED, linewidth=1.0, linestyle=":")
    ax.set_title(f"Running expectancy stabilises with sample size ({bundle.config.ticker})")
    ax.set_ylabel("Cumulative expectancy (R)")
    ax.set_xlabel("Number of trades")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def fig_risk_of_ruin(bundle: RunBundle, path: Path) -> Path:
    set_style()
    levels = [f"{row.risk_level_pct:g}%" for row in bundle.ruin]
    probs = [row.probability * 100 for row in bundle.ruin]
    colors = [POSITIVE if p < 5 else (ACCENT if p < 25 else NEGATIVE) for p in probs]

    fig, ax = plt.subplots(figsize=(7.5, 4.0))
    bars = ax.bar(levels, probs, color=colors, alpha=0.85, edgecolor="white")
    headroom = max(max(probs), 1.0) * 0.12
    ax.set_ylim(0, max(max(probs), 1.0) * 1.18 + headroom)
    for bar, p in zip(bars, probs):
        ax.text(bar.get_x() + bar.get_width() / 2, p + headroom, f"{p:.1f}%", ha="center", fontsize=9)
    target = int(bundle.ruin[0].drawdown_target_pct)
    ax.set_title(f"Risk of ruin: P(drawdown ≥ {target}%) by risk per trade ({bundle.config.ticker})")
    ax.set_ylabel("Probability (%)")
    ax.set_xlabel("Risk per trade")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def generate_figures(bundle: RunBundle, out_dir: Path, prefix: str) -> dict[str, Path]:
    """Generate the per-instrument figure set; returns a name -> path map."""
    out_dir.mkdir(parents=True, exist_ok=True)
    if bundle.result.n_trades == 0:
        return {}
    figures = {
        "equity": fig_equity_curve(bundle, out_dir / f"{prefix}_equity.png"),
        "underwater": fig_underwater(bundle, out_dir / f"{prefix}_underwater.png"),
        "mc_fan": fig_montecarlo_fan(bundle, out_dir / f"{prefix}_mc_fan.png"),
        "mc_hist": fig_montecarlo_histogram(bundle, out_dir / f"{prefix}_mc_hist.png"),
        "convergence": fig_expectancy_convergence(bundle, out_dir / f"{prefix}_convergence.png"),
        "ruin": fig_risk_of_ruin(bundle, out_dir / f"{prefix}_ruin.png"),
    }
    return figures


# --- cross-instrument comparison figures (used by the study report) ---

def fig_expectancy_comparison(bundles: list[RunBundle], path: Path) -> Path:
    set_style()
    labels = [b.config.ticker for b in bundles]
    exp_r = [b.metrics.expectancy_r for b in bundles]
    colors = [POSITIVE if e > 0 else NEGATIVE for e in exp_r]

    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    bars = ax.bar(labels, exp_r, color=colors, alpha=0.85, edgecolor="white")
    for bar, e in zip(bars, exp_r):
        offset = 0.005 if e >= 0 else -0.012
        ax.text(bar.get_x() + bar.get_width() / 2, e + offset, f"{e:+.3f}", ha="center", fontsize=9)
    ax.axhline(0, color=INK, linewidth=1.0)
    ax.set_title("Per-trade expectancy by instrument (in R, after costs)")
    ax.set_ylabel("Expectancy (R)")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def fig_significance_forest(bundles: list[RunBundle], pooled, path: Path) -> Path:
    """Forest plot: expectancy in R with 95% bootstrap CI per instrument + pool."""
    set_style()
    # The pooled bar uses the block (cluster) CI — the honest, correlation-aware one.
    labels = [b.config.ticker for b in bundles] + ["POOLED*"]
    means = [b.expectancy_ci.mean_r for b in bundles] + [pooled.expectancy_r]
    lows = [b.expectancy_ci.ci_low for b in bundles] + [pooled.ci_block.ci_low]
    highs = [b.expectancy_ci.ci_high for b in bundles] + [pooled.ci_block.ci_high]

    y = np.arange(len(labels))[::-1]
    fig, ax = plt.subplots(figsize=(8.5, max(4.6, 0.42 * len(labels) + 1.4)))
    for yi, mean, lo, hi in zip(y, means, lows, highs):
        crosses_zero = lo <= 0 <= hi
        color = MUTED if crosses_zero else (POSITIVE if lo > 0 else NEGATIVE)
        ax.plot([lo, hi], [yi, yi], color=color, linewidth=2.4, solid_capstyle="round")
        ax.plot(mean, yi, "o", color=color, markersize=7)
    ax.axvline(0, color=INK, linewidth=1.2, linestyle="--")
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Per-trade expectancy (R) with 95% bootstrap CI\n"
                  "*POOLED uses a calendar-quarter block bootstrap (trades aren't independent)")
    ax.set_title("Can the edge be told apart from zero? (grey CI = no)")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def fig_pooled_convergence(pooled, path: Path) -> Path:
    """Cumulative expectancy of the pooled trade stream vs trade count."""
    set_style()
    r = pooled.r_multiples
    cumulative = np.cumsum(r) / np.arange(1, r.size + 1)

    fig, ax = plt.subplots(figsize=(9, 4.2))
    ax.axvspan(0, min(100, r.size), color=NEGATIVE, alpha=0.06)
    ax.plot(np.arange(1, r.size + 1), cumulative, color=ACCENT, linewidth=1.8)
    ax.axhline(pooled.expectancy_r, color=POSITIVE, linewidth=1.2, linestyle="--",
               label=f"Final {pooled.expectancy_r:+.3f} R")
    ax.axhline(0, color=MUTED, linewidth=1.0, linestyle=":")
    ax.text(min(100, r.size) / 2, ax.get_ylim()[1], "noise zone (<100)", color=NEGATIVE,
            fontsize=8, ha="center", va="top")
    ax.set_title(f"Pooled expectancy across all instruments ({r.size} trades)")
    ax.set_ylabel("Cumulative expectancy (R)")
    ax.set_xlabel("Number of trades (ordered by date)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def fig_cost_sensitivity(sweeps: dict[str, list], path: Path) -> Path:
    """Expectancy in R vs slippage assumption, one line per instrument."""
    set_style()
    palette = [ACCENT, POSITIVE, NEGATIVE, "#8250df", "#bf8700"]
    fig, ax = plt.subplots(figsize=(9, 4.6))
    for (ticker, points), color in zip(sweeps.items(), palette):
        xs = [p.slippage_frac for p in points]
        ys = [p.expectancy_r for p in points]
        ax.plot(xs, ys, marker="o", markersize=4, linewidth=1.6, color=color, label=ticker)
    ax.axhline(0, color=INK, linewidth=1.2, linestyle="--")
    ax.set_title("Cost sensitivity: expectancy vs slippage (fraction of candle range)")
    ax.set_ylabel("Expectancy (R)")
    ax.set_xlabel("Slippage fraction per fill")
    ax.legend(title="Instrument")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def fig_powered_cost_curve(curve, baseline_slippage: float, path: Path) -> Path:
    """Pooled expectancy of the powered study vs slippage — the gross-vs-net story."""
    set_style()
    xs = [p.slippage_frac for p in curve.points]
    ys = [p.expectancy_r for p in curve.points]

    fig, ax = plt.subplots(figsize=(9, 4.6))
    ax.plot(xs, ys, marker="o", markersize=5, linewidth=1.8, color=ACCENT, label="Net pooled expectancy")
    ax.axhline(0, color=INK, linewidth=1.2, linestyle="--")

    # Gross (all costs zeroed) as a reference at the left edge.
    ax.plot(0, curve.gross_expectancy_r, marker="*", markersize=15, color=POSITIVE, zorder=5)
    ax.annotate(f"gross (no costs)\n{curve.gross_expectancy_r:+.3f}R",
                (0, curve.gross_expectancy_r), textcoords="offset points", xytext=(12, 4),
                fontsize=8.5, color=POSITIVE)

    if curve.breakeven_slippage is not None:
        ax.axvline(curve.breakeven_slippage, color=NEGATIVE, linewidth=1.2, linestyle=":")
        ax.annotate(f"break-even\nslippage ≈ {curve.breakeven_slippage:.3f}",
                    (curve.breakeven_slippage, 0), textcoords="offset points", xytext=(6, 28),
                    fontsize=8.5, color=NEGATIVE)

    ax.axvline(baseline_slippage, color=MUTED, linewidth=1.0, linestyle="-")
    ax.annotate("baseline", (baseline_slippage, min(ys)), textcoords="offset points",
                xytext=(4, 2), fontsize=8, color=MUTED)

    ax.fill_between(xs, ys, 0, where=[y > 0 for y in ys], color=POSITIVE, alpha=0.10)
    ax.fill_between(xs, ys, 0, where=[y <= 0 for y in ys], color=NEGATIVE, alpha=0.10)
    ax.set_title("Powered study: the edge is real gross, but costs eat it (2,313 trades)")
    ax.set_ylabel("Pooled expectancy (R)")
    ax.set_xlabel("Slippage fraction per fill")
    ax.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def fig_resolution_comparison(crossover_pooled, powered_pooled, path: Path) -> Path:
    """The headline of v2: the pooled CI collapsing once the sample has power."""
    set_style()
    rows = [
        (f"Crossover\n({crossover_pooled.n_trades} trades)", crossover_pooled),
        (f"RSI reversion\n({powered_pooled.n_trades} trades)", powered_pooled),
    ]
    y = [1, 0]
    fig, ax = plt.subplots(figsize=(8.5, 3.4))
    for yi, (label, pooled) in zip(y, rows):
        lo, hi, mean = pooled.ci_block.ci_low, pooled.ci_block.ci_high, pooled.expectancy_r
        crosses_zero = lo <= 0 <= hi
        color = MUTED if crosses_zero else (POSITIVE if lo > 0 else NEGATIVE)
        ax.plot([lo, hi], [yi, yi], color=color, linewidth=3.0, solid_capstyle="round")
        ax.plot(mean, yi, "o", color=color, markersize=8)
        ax.text(hi + 0.01, yi, f"  width {hi - lo:.2f}R", va="center", fontsize=9, color=MUTED)
    ax.axvline(0, color=INK, linewidth=1.2, linestyle="--")
    ax.set_yticks(y)
    ax.set_yticklabels([r[0] for r in rows])
    ax.set_ylim(-0.6, 1.6)
    ax.set_xlabel("Pooled per-trade expectancy (R), 95% block-bootstrap CI")
    ax.set_title("Give the machine enough trades and the question resolves")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def fig_winrate_vs_breakeven(bundles: list[RunBundle], path: Path) -> Path:
    set_style()
    labels = [b.config.ticker for b in bundles]
    actual = [b.metrics.win_rate * 100 for b in bundles]
    breakeven = [b.metrics.breakeven_win_rate * 100 for b in bundles]

    x = np.arange(len(labels))
    width = 0.38
    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    ax.bar(x - width / 2, breakeven, width, label="Breakeven win rate", color=MUTED, alpha=0.8)
    ax.bar(x + width / 2, actual, width, label="Actual win rate", color=ACCENT, alpha=0.85)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_title("Actual win rate vs the breakeven it must clear")
    ax.set_ylabel("Win rate (%)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path
