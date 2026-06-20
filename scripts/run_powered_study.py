"""The powered study: a frequent strategy over a large basket.

    python scripts/run_powered_study.py

The crossover study is structurally underpowered (~40 trades/instrument). This
study swaps in the RSI(2) mean-reversion strategy — which fires dozens of times a
year — over a much larger basket, producing thousands of trades. The point is to
show the *same engine* finally reaching the sample size where the confidence
interval can actually resolve the question instead of shrugging.

Pickles the bundles to output/powered_study.pkl for the report builder.
"""

from __future__ import annotations

import pickle
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from expectancy.analysis import pool_trades  # noqa: E402
from expectancy.config import StrategyConfig, load_config  # noqa: E402
from expectancy.data.loader import DataError  # noqa: E402
from expectancy.runner import run_backtest  # noqa: E402

# A broad, liquid basket: US large caps + index ETFs and Brazilian blue chips.
BASKET = [
    "SPY", "QQQ", "IWM", "DIA", "AAPL", "MSFT", "JPM", "JNJ",
    "XOM", "KO", "PG", "WMT", "HD", "CVX",
    "PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA", "ABEV3.SA", "BBAS3.SA",
]

RSI_STRATEGY = StrategyConfig(
    name="rsi_reversion",
    rsi_period=2,
    rsi_entry=10.0,
    rsi_exit=60.0,
    trend_filter_ma=200,
    atr_period=14,
    stop_atr_mult=2.5,
    max_holding_bars=10,
)

OUTPUT = ROOT / "output"
POWERED_PICKLE = OUTPUT / "powered_study.pkl"


def main() -> None:
    base = replace(load_config(ROOT / "config.yaml"), strategy=RSI_STRATEGY)
    bundles = []

    for ticker in BASKET:
        config = base.with_ticker(ticker)
        try:
            bundle = run_backtest(config, use_cache=True)
        except DataError as exc:
            print(f"[powered] skipping {ticker}: {exc}")
            continue
        m = bundle.metrics
        ci = bundle.expectancy_ci
        print(f"  {ticker:<10} trades={m.n_trades:>4}  win%={m.win_rate * 100:5.1f}  "
              f"expR={m.expectancy_r:+.3f}  CI=[{ci.ci_low:+.3f},{ci.ci_high:+.3f}]  {ci.verdict}")
        bundles.append(bundle)

    if bundles:
        pooled = pool_trades([b.result for b in bundles], n_resamples=10_000, seed=42)
        print(f"\n{'=' * 70}\n POWERED POOL — {pooled.n_trades} trades across {len(bundles)} instruments\n{'=' * 70}")
        print(f"  Expectancy            {pooled.expectancy_r:+.4f} R")
        print(f"  95% CI (i.i.d.)       [{pooled.ci.ci_low:+.4f}, {pooled.ci.ci_high:+.4f}]")
        print(f"  95% CI (block, q={pooled.n_blocks})  [{pooled.ci_block.ci_low:+.4f}, "
              f"{pooled.ci_block.ci_high:+.4f}] -> {pooled.ci_block.verdict}")
        print(f"  P(expectancy > 0)     {pooled.ci_block.prob_positive * 100:.1f}% (block)")
        print(f"  In-sample  (first {pooled.in_sample_n}): {pooled.in_sample_expectancy_r:+.4f} R")
        print(f"  Out-sample (last  {pooled.out_sample_n}): {pooled.out_sample_expectancy_r:+.4f} R")

    OUTPUT.mkdir(parents=True, exist_ok=True)
    with open(POWERED_PICKLE, "wb") as fh:
        pickle.dump(bundles, fh)
    print(f"\nSaved {len(bundles)} instrument results to {POWERED_PICKLE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
