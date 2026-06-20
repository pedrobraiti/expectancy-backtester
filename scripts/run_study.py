"""Run the full basket study (US + Brazil) and cache the results.

    python scripts/run_study.py

Downloads (and caches) OHLCV for every instrument, backtests the same strategy
on each, runs the Monte-Carlo block, and pickles the list of RunBundles to
output/study.pkl for the report builder to consume. The first run hits the
network; later runs are offline.
"""

from __future__ import annotations

import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from expectancy.config import load_config  # noqa: E402
from expectancy.data.loader import DataError  # noqa: E402
from expectancy.reporting import print_report  # noqa: E402
from expectancy.runner import run_backtest  # noqa: E402

# The basket: liquid US indices vs trending Brazilian single names.
BASKET = ["SPY", "QQQ", "PETR4.SA", "VALE3.SA", "ITUB4.SA"]

OUTPUT = ROOT / "output"
STUDY_PICKLE = OUTPUT / "study.pkl"


def main() -> None:
    base_config = load_config(ROOT / "config.yaml")
    bundles = []

    for ticker in BASKET:
        print(f"\n{'#' * 64}\n# {ticker}\n{'#' * 64}")
        config = base_config.with_ticker(ticker)
        try:
            bundle = run_backtest(config, use_cache=True)
        except DataError as exc:
            print(f"[study] skipping {ticker}: {exc}")
            continue
        print_report(bundle)
        bundles.append(bundle)

    OUTPUT.mkdir(parents=True, exist_ok=True)
    with open(STUDY_PICKLE, "wb") as fh:
        pickle.dump(bundles, fh)
    print(f"\nSaved {len(bundles)} instrument results to {STUDY_PICKLE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
