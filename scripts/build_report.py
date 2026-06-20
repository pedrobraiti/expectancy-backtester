"""Render all figures and the PDF report from the cached study.

    python scripts/build_report.py

Reads output/study.pkl, writes the per-instrument and comparison figures to
output/figures/, and builds output/expectancy_study.pdf. Figures and the PDF are
committed so the study renders on GitHub without running the pipeline.
"""

from __future__ import annotations

import pickle
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from expectancy.analysis import cost_sweep, pool_trades  # noqa: E402
from expectancy.reporting import build_pdf_report, generate_figures  # noqa: E402
from expectancy.reporting.figures import (  # noqa: E402
    fig_cost_sensitivity,
    fig_expectancy_comparison,
    fig_pooled_convergence,
    fig_significance_forest,
    fig_winrate_vs_breakeven,
)

# Slippage levels swept for the cost-sensitivity figure (fraction of candle range).
SLIPPAGE_LEVELS = (0.0, 0.025, 0.05, 0.10, 0.15, 0.20, 0.30)

OUTPUT = ROOT / "output"
FIGURES = OUTPUT / "figures"
STUDY_PICKLE = OUTPUT / "study.pkl"
PDF_PATH = OUTPUT / "expectancy_study.pdf"


def main() -> None:
    if not STUDY_PICKLE.exists():
        raise SystemExit("output/study.pkl not found — run scripts/run_study.py first.")

    with open(STUDY_PICKLE, "rb") as fh:
        bundles = pickle.load(fh)

    bundles = [b for b in bundles if b.result.n_trades > 0]
    if not bundles:
        raise SystemExit("No instrument produced trades; nothing to report.")

    FIGURES.mkdir(parents=True, exist_ok=True)

    figures_by_ticker: dict[str, dict[str, Path]] = {}
    for bundle in bundles:
        prefix = bundle.config.ticker.replace(".", "_")
        figures_by_ticker[bundle.config.ticker] = generate_figures(bundle, FIGURES, prefix)
        print(f"[report] figures for {bundle.config.ticker}")

    # Significance + pooling + cost sensitivity (the "is the edge real?" block).
    pooled = pool_trades([b.result for b in bundles], n_resamples=10_000, seed=42)
    sweeps = {b.config.ticker: cost_sweep(b.config, SLIPPAGE_LEVELS) for b in bundles}
    print("[report] pooled + cost sweeps")

    comparison_figures = {
        "expectancy": fig_expectancy_comparison(bundles, FIGURES / "00_expectancy_comparison.png"),
        "winrate": fig_winrate_vs_breakeven(bundles, FIGURES / "00_winrate_vs_breakeven.png"),
        "forest": fig_significance_forest(bundles, pooled, FIGURES / "00_significance_forest.png"),
        "pooled_convergence": fig_pooled_convergence(pooled, FIGURES / "00_pooled_convergence.png"),
        "cost": fig_cost_sensitivity(sweeps, FIGURES / "00_cost_sensitivity.png"),
    }
    print("[report] comparison figures")

    build_pdf_report(
        bundles,
        figures_by_ticker,
        comparison_figures,
        PDF_PATH,
        generated_on=date.today().isoformat(),
        pooled=pooled,
    )
    print(f"[report] PDF written to {PDF_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
