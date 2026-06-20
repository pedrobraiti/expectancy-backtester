"""Build the multi-page technical PDF report (reportlab).

Takes the study's :class:`RunBundle` list plus the already-rendered figure paths
and lays out a professional document: methodology, a per-instrument scorecard
with its charts, the cross-instrument comparison, and the variance / risk-of-ruin
/ recovery sections that are the whole point of the study.
"""

from __future__ import annotations

import math
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from expectancy.runner import RunBundle

INK = colors.HexColor("#1b1f24")
ACCENT = colors.HexColor("#1f6feb")
POSITIVE = colors.HexColor("#2da44e")
NEGATIVE = colors.HexColor("#cf222e")
LIGHT = colors.HexColor("#eef2f6")
MUTED = colors.HexColor("#8b949e")

_CONTENT_WIDTH = A4[0] - 4 * cm


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("title", parent=base["Title"], textColor=INK, fontSize=26, leading=30),
        "subtitle": ParagraphStyle("subtitle", parent=base["Normal"], textColor=MUTED, fontSize=12,
                                    alignment=TA_CENTER, leading=16),
        "h1": ParagraphStyle("h1", parent=base["Heading1"], textColor=ACCENT, fontSize=16, spaceBefore=10, spaceAfter=6),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], textColor=INK, fontSize=12.5, spaceBefore=8, spaceAfter=4),
        "body": ParagraphStyle("body", parent=base["Normal"], textColor=INK, fontSize=10, leading=15, alignment=TA_LEFT),
        "small": ParagraphStyle("small", parent=base["Normal"], textColor=MUTED, fontSize=8.5, leading=12),
        "caption": ParagraphStyle("caption", parent=base["Normal"], textColor=MUTED, fontSize=8.5,
                                  leading=11, alignment=TA_CENTER, spaceAfter=10),
    }


def _money(v: float) -> str:
    return f"{v:,.2f}"


def _pf(v: float) -> str:
    return "∞" if math.isinf(v) else f"{v:.2f}"


def _image(path: Path | None, width: float = _CONTENT_WIDTH) -> Image | Spacer:
    if path is None or not Path(path).exists():
        return Spacer(1, 0.1 * cm)
    img = Image(str(path))
    ratio = img.imageHeight / img.imageWidth
    img.drawWidth = width
    img.drawHeight = width * ratio
    return img


def _scorecard_table(bundle: RunBundle, st: dict) -> Table:
    m = bundle.metrics
    rows = [
        ["Metric", "Value", "Metric", "Value"],
        ["Trades", f"{m.n_trades}", "Profit factor", _pf(m.profit_factor)],
        ["Win rate", f"{m.win_rate * 100:.2f}%", "Payoff (R)", _pf(m.payoff_ratio)],
        ["Avg win", f"{_money(m.avg_win_money)} ({m.avg_win_r:+.2f}R)",
         "Avg loss", f"{_money(-m.avg_loss_money)} ({-m.avg_loss_r:+.2f}R)"],
        ["Expectancy $", f"{_money(m.expectancy_money)}", "Expectancy R", f"{m.expectancy_r:+.3f}"],
        ["Breakeven WR", f"{m.breakeven_win_rate * 100:.2f}%", "Actual WR", f"{m.win_rate * 100:.2f}%"],
        ["Total return", f"{m.total_return_pct:+.2f}%", "CAGR", f"{m.cagr_pct:+.2f}%"],
        ["Max drawdown", f"{m.max_drawdown_pct:.2f}%", "Sharpe / Sortino", f"{m.sharpe:.2f} / {m.sortino:.2f}"],
    ]
    table = Table(rows, colWidths=[_CONTENT_WIDTH * w for w in (0.22, 0.28, 0.22, 0.28)])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 1), (2, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
                ("GRID", (0, 0), (-1, -1), 0.4, MUTED),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def _comparison_table(bundles: list[RunBundle]) -> Table:
    header = ["Instrument", "Trades", "Win%", "Exp. R", "Exp. $", "Profit factor", "Max DD%", "Edge?"]
    rows = [header]
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), INK),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.4, MUTED),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for i, b in enumerate(bundles, start=1):
        m = b.metrics
        rows.append([
            b.config.ticker, f"{m.n_trades}", f"{m.win_rate * 100:.1f}",
            f"{m.expectancy_r:+.3f}", f"{m.expectancy_money:+.2f}",
            _pf(m.profit_factor), f"{m.max_drawdown_pct:.1f}",
            "YES" if m.has_edge else "no",
        ])
        cell_color = POSITIVE if m.has_edge else NEGATIVE
        style.append(("TEXTCOLOR", (3, i), (3, i), cell_color))
        style.append(("TEXTCOLOR", (7, i), (7, i), cell_color))
        style.append(("FONTNAME", (7, i), (7, i), "Helvetica-Bold"))
    table = Table(rows, colWidths=[_CONTENT_WIDTH * w for w in (0.18, 0.1, 0.1, 0.13, 0.14, 0.16, 0.11, 0.08)])
    table.setStyle(TableStyle(style))
    return table


def _recovery_table(bundle: RunBundle) -> Table:
    rows = [["Drawdown suffered", "Gain required to recover"]]
    for loss, gain in bundle.recovery:
        gain_str = "∞" if math.isinf(gain) else f"{gain * 100:.0f}%"
        rows.append([f"{loss * 100:.0f}%", gain_str])
    table = Table(rows, colWidths=[_CONTENT_WIDTH * 0.3, _CONTENT_WIDTH * 0.3])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NEGATIVE),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.4, MUTED),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def build_pdf_report(
    bundles: list[RunBundle],
    figures_by_ticker: dict[str, dict[str, Path]],
    comparison_figures: dict[str, Path],
    out_path: Path,
    *,
    generated_on: str,
) -> Path:
    st = _styles()
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(out_path), pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
        title="The Mathematics of a Trading System", author="Pedro Braiti",
    )
    flow: list = []

    # --- cover ---
    flow.append(Spacer(1, 3 * cm))
    flow.append(Paragraph("The Mathematics of a Trading System", st["title"]))
    flow.append(Spacer(1, 0.4 * cm))
    flow.append(Paragraph(
        "Expectancy, variance, the risk/reward tradeoff and the risk of ruin — "
        "measured, not assumed, on real OHLCV.", st["subtitle"]))
    flow.append(Spacer(1, 1.2 * cm))
    tickers = ", ".join(b.config.ticker for b in bundles)
    flow.append(Paragraph(
        f"A walk through what a rules-based backtester actually proves once costs, "
        f"position sizing and luck are taken seriously. Strategy: "
        f"<b>{bundles[0].config.strategy.name}</b>. Instruments: <b>{tickers}</b>.",
        st["body"]))
    flow.append(Spacer(1, 0.6 * cm))
    flow.append(Paragraph(f"Generated on {generated_on}", st["small"]))
    flow.append(PageBreak())

    # --- methodology ---
    flow.append(Paragraph("1. Method — where the numbers come from", st["h1"]))
    flow.append(Paragraph(
        "The win rate, expectancy and risk figures in this report are <b>not downloaded</b>. "
        "Yahoo Finance supplies only OHLCV; everything else is a <i>result</i> of simulating the "
        "strategy trade by trade. The engine is built to avoid the errors that flatter a backtest:",
        st["body"]))
    flow.append(Spacer(1, 0.2 * cm))
    for item in [
        "<b>No lookahead.</b> A signal at the close of bar t is executed at the open of bar t+1 — never at the price that produced it.",
        "<b>Costs on every trade.</b> Spread, commission and slippage are charged round-trip; without them, paper expectancy lies.",
        "<b>Fixed-fractional risk.</b> Each trade risks a constant percentage of equity; a wider stop means a smaller position.",
        "<b>Conservative fills.</b> If a bar touches both stop and target, the stop is assumed to fill first.",
        "<b>Reproducible variance.</b> The Monte-Carlo bootstrap uses a fixed seed, so every run is identical.",
    ]:
        flow.append(Paragraph(f"• {item}", st["body"]))
    flow.append(Spacer(1, 0.3 * cm))
    flow.append(Paragraph(
        "Result in R (the R-multiple) is the unit that connects everything: a system is described by its "
        "win rate and its average R. A loss at the stop is −1R; the breakeven win rate, 1/(R+1), is the bar "
        "the real win rate must clear.", st["body"]))

    flow.append(Spacer(1, 0.4 * cm))
    flow.append(Paragraph("2. Cross-instrument scorecard", st["h1"]))
    flow.append(Paragraph(
        "The same strategy, same parameters, run on every instrument. Where the expectancy is positive "
        "(after costs) the edge survives; where it is negative the geometry is just folklore on that market.",
        st["body"]))
    flow.append(Spacer(1, 0.2 * cm))
    flow.append(_comparison_table(bundles))
    flow.append(Spacer(1, 0.4 * cm))
    if "expectancy" in comparison_figures:
        flow.append(_image(comparison_figures["expectancy"]))
        flow.append(Paragraph("Per-trade expectancy in R, after costs. Green bars have a positive edge.", st["caption"]))
    if "winrate" in comparison_figures:
        flow.append(_image(comparison_figures["winrate"]))
        flow.append(Paragraph(
            "Actual win rate against the breakeven it must beat. A bar to the right of its grey twin is profitable.",
            st["caption"]))
    flow.append(PageBreak())

    # --- per instrument ---
    for idx, bundle in enumerate(bundles, start=3):
        figs = figures_by_ticker.get(bundle.config.ticker, {})
        flow.append(Paragraph(f"{idx}. {bundle.config.ticker} — the full fingerprint", st["h1"]))
        if bundle.metrics.n_trades == 0:
            flow.append(Paragraph("No trades were generated on this instrument for the configured period.", st["body"]))
            flow.append(PageBreak())
            continue
        flow.append(_scorecard_table(bundle, st))
        if not bundle.metrics.sample_is_reliable:
            flow.append(Spacer(1, 0.2 * cm))
            flow.append(Paragraph(
                f"⚠ Small sample ({bundle.metrics.n_trades} trades &lt; 100): expectancy is still noise-dominated. "
                "Treat with skepticism.", st["small"]))
        flow.append(Spacer(1, 0.3 * cm))
        flow.append(_image(figs.get("equity")))
        flow.append(Paragraph("Realized equity curve, costs included.", st["caption"]))
        flow.append(_image(figs.get("underwater")))
        flow.append(Paragraph("Underwater plot: time spent below the previous equity peak.", st["caption"]))
        flow.append(PageBreak())

        flow.append(Paragraph(f"{idx}.1 Variance — same edge, different luck", st["h2"]))
        flow.append(Paragraph(
            "Reshuffling the realized trades 5,000 times shows the range of outcomes the same system could have "
            "produced. The median is the honest expectation; the 5–95% band is the experience you must be able to sit through.",
            st["body"]))
        flow.append(_image(figs.get("mc_fan")))
        flow.append(Paragraph("Monte-Carlo fan: median path and 5–95% band vs the single realized run.", st["caption"]))
        flow.append(_image(figs.get("mc_hist")))
        flow.append(Paragraph("Distribution of final equity across the simulations.", st["caption"]))
        flow.append(PageBreak())

        flow.append(Paragraph(f"{idx}.2 Risk of ruin & sample size", st["h2"]))
        flow.append(_image(figs.get("ruin")))
        flow.append(Paragraph(
            "Probability of a deep drawdown by risk per trade — it climbs non-linearly as the risk dial turns up.",
            st["caption"]))
        flow.append(_image(figs.get("convergence")))
        flow.append(Paragraph(
            "Running expectancy vs trade count: one trade means nothing; the average only settles with sample size.",
            st["caption"]))
        flow.append(PageBreak())

    # --- recovery + disclaimer ---
    flow.append(Paragraph(f"{len(bundles) + 3}. The recovery math — why protecting capital wins", st["h1"]))
    flow.append(Paragraph(
        "Losses and the gains needed to undo them are asymmetric. A 50% drawdown does not need 50% to recover — "
        "it needs 100%. This is why risk of ruin, not raw return, is the metric that keeps a trader in the game.",
        st["body"]))
    flow.append(Spacer(1, 0.3 * cm))
    flow.append(_recovery_table(bundles[0]))
    flow.append(Spacer(1, 0.6 * cm))
    flow.append(Paragraph("Disclaimer", st["h2"]))
    flow.append(Paragraph(
        "This is an educational and research project. Nothing here is investment advice. The example strategy is a "
        "didactic moving-average crossover, not a system with a guaranteed edge. The backtester <i>measures</i> an "
        "edge; it does not create one. Past performance does not guarantee future results.", st["small"]))

    doc.build(flow)
    return out_path
