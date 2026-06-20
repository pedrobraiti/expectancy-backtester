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


def _ci_table(bundles: list[RunBundle], pooled) -> Table:
    header = ["Instrument", "Trades", "Expectancy R", "95% CI (R)", "P(>0)", "Verdict"]
    rows = [header]
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), INK),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.4, MUTED),
        ("ALIGN", (1, 0), (-2, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    entries = [(b.config.ticker, b.expectancy_ci) for b in bundles]
    entries.append(("POOLED", pooled.ci))
    for i, (name, ci) in enumerate(entries, start=1):
        rows.append([
            name, f"{ci.n}", f"{ci.mean_r:+.3f}",
            f"[{ci.ci_low:+.3f}, {ci.ci_high:+.3f}]", f"{ci.prob_positive * 100:.0f}%",
            ci.verdict,
        ])
        color = MUTED if not ci.distinguishable_from_zero else (POSITIVE if ci.ci_low > 0 else NEGATIVE)
        style.append(("TEXTCOLOR", (5, i), (5, i), color))
        if name == "POOLED":
            style.append(("FONTNAME", (0, i), (-1, i), "Helvetica-Bold"))
            style.append(("LINEABOVE", (0, i), (-1, i), 1.0, INK))
    table = Table(rows, colWidths=[_CONTENT_WIDTH * w for w in (0.18, 0.1, 0.18, 0.26, 0.1, 0.18)])
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
    pooled=None,
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
    flow.append(Paragraph(
        "But none of these point estimates is established. With ~40 trades each, the spread of "
        "expectancies is exactly what pure chance produces even if the true edge were identical (or zero) "
        "everywhere. The next section tests that honestly.", st["body"]))
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

    # --- significance, pooling, cost ---
    if pooled is not None and pooled.n_trades > 0:
        sig_n = len(bundles) + 3
        flow.append(Paragraph(f"{sig_n}. Is the edge real? Significance, pooling and cost", st["h1"]))
        flow.append(Paragraph(
            "A point estimate without an interval is a guess with a confident voice. Bootstrapping the "
            "per-trade expectancy gives a 95% confidence interval; where it straddles zero, a small edge "
            "cannot be told apart from no edge at all.", st["body"]))
        flow.append(Spacer(1, 0.2 * cm))
        if "forest" in comparison_figures:
            flow.append(_image(comparison_figures["forest"]))
            flow.append(Paragraph(
                "Expectancy with its 95% bootstrap CI. A grey interval crosses zero — undecidable at this "
                "sample size.", st["caption"]))
        flow.append(_ci_table(bundles, pooled))
        flow.append(Spacer(1, 0.3 * cm))
        decisive = sum(1 for b in bundles if b.expectancy_ci.distinguishable_from_zero)
        flow.append(Paragraph(
            f"Of the {len(bundles)} instruments, <b>{len(bundles) - decisive}</b> have a confidence "
            "interval that includes zero: individually, the data cannot confirm an edge in either "
            "direction. This is the honest reading the headline scorecard hides.", st["body"]))
        flow.append(Spacer(1, 0.2 * cm))
        flow.append(Paragraph(
            "Two caveats make the picture even more sober. <b>QQQ sits exactly on the boundary</b> "
            "(P(edge &gt; 0) = 95%), so calling it positive would be a one-tailed knife-edge, not a "
            "finding. And <b>multiple comparisons</b> bite: testing five instruments, the chance that at "
            "least one clears a 95% one-sided bar by luck alone is 1 &minus; 0.95<super>5</super> &asymp; "
            "23%. Finding one borderline name among five is roughly what pure noise predicts — another "
            "reason not to single QQQ out.", st["body"]))
        flow.append(PageBreak())

        flow.append(Paragraph(f"{sig_n}.1 Pooling for power, and an out-of-sample split", st["h2"]))
        flow.append(Paragraph(
            f"Because R normalises each trade by its risk, the {pooled.n_trades} trades from all "
            "instruments can be pooled into one stream — finally crossing the ~100-trade threshold. The "
            f"pooled expectancy is <b>{pooled.expectancy_r:+.3f}R</b>. But these trades are <i>not</i> "
            "independent — US indices (~0.9 correlated) and the Brazilian names move together, so trades "
            "firing in the same period carry redundant information. An i.i.d. bootstrap would understate "
            "the uncertainty; a <b>calendar-quarter block bootstrap</b> keeps that correlation intact and "
            "gives the honest interval:",
            st["body"]))
        flow.append(Spacer(1, 0.15 * cm))
        flow.append(Paragraph(
            f"&bull; i.i.d. CI (optimistic): [{pooled.ci.ci_low:+.3f}, {pooled.ci.ci_high:+.3f}]R<br/>"
            f"&bull; block CI ({pooled.n_blocks} quarters, honest): "
            f"<b>[{pooled.ci_block.ci_low:+.3f}, {pooled.ci_block.ci_high:+.3f}]R</b> — "
            f"{'still includes zero' if not pooled.ci_block.distinguishable_from_zero else 'excludes zero'} "
            f"(P(edge &gt; 0) = {pooled.ci_block.prob_positive * 100:.0f}%)",
            st["body"]))
        flow.append(Spacer(1, 0.2 * cm))
        flow.append(Paragraph(
            "Splitting the pool chronologically into halves gives a genuine out-of-sample check:",
            st["body"]))
        flow.append(Spacer(1, 0.2 * cm))
        flow.append(Paragraph(
            f"&bull; In-sample (first {pooled.in_sample_n} trades): <b>{pooled.in_sample_expectancy_r:+.3f}R</b><br/>"
            f"&bull; Out-of-sample (last {pooled.out_sample_n} trades): <b>{pooled.out_sample_expectancy_r:+.3f}R</b>",
            st["body"]))
        flow.append(Spacer(1, 0.3 * cm))
        if "pooled_convergence" in comparison_figures:
            flow.append(_image(comparison_figures["pooled_convergence"]))
            flow.append(Paragraph(
                "Pooled running expectancy. Even at ~200 trades it is still settling; the shaded zone marks "
                "the sub-100 region where the estimate is noise.", st["caption"]))
        flow.append(PageBreak())

        flow.append(Paragraph(f"{sig_n}.2 The edge is thin: cost sensitivity", st["h2"]))
        flow.append(Paragraph(
            "Where expectancy is a fraction of an R, the cost assumption is a lever, not a footnote. "
            "Sweeping the slippage assumption shows how fast each instrument's edge crosses into the red.",
            st["body"]))
        if "cost" in comparison_figures:
            flow.append(_image(comparison_figures["cost"]))
            flow.append(Paragraph(
                "Expectancy vs slippage. Lines that dip below the dashed zero line have lost their edge to "
                "costs — for the marginal names, that happens with a small change in assumptions.",
                st["caption"]))
        flow.append(PageBreak())

    # --- recovery + disclaimer ---
    recovery_n = len(bundles) + 4 if (pooled is not None and pooled.n_trades > 0) else len(bundles) + 3
    flow.append(Paragraph(f"{recovery_n}. The recovery math — why protecting capital wins", st["h1"]))
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
