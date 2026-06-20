"""Single-instrument backtest entry point (brief §12 acceptance criterion).

    python main.py                 # uses config.yaml
    python main.py --ticker SPY    # override the instrument
    python main.py --config my.yaml

Runs the strategy on one ticker, prints the full scorecard, and writes the
four core figures to output/figures/.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from expectancy.config import load_config
from expectancy.reporting import generate_figures, print_report
from expectancy.runner import run_backtest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run an expectancy backtest on one instrument.")
    parser.add_argument("--config", default="config.yaml", help="path to the YAML config")
    parser.add_argument("--ticker", default=None, help="override the ticker in the config")
    parser.add_argument("--no-cache", action="store_true", help="bypass the Parquet data cache")
    parser.add_argument("--no-figures", action="store_true", help="skip writing PNG figures")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    if args.ticker:
        config = config.with_ticker(args.ticker)

    bundle = run_backtest(config, use_cache=not args.no_cache)
    print_report(bundle)

    if not args.no_figures and bundle.result.n_trades > 0:
        out_dir = Path("output/figures")
        prefix = config.ticker.replace(".", "_")
        figures = generate_figures(bundle, out_dir, prefix)
        print(f"\nFigures written to {out_dir}/ ({len(figures)} files).")


if __name__ == "__main__":
    main()
