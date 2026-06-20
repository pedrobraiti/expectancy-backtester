# Expectancy — The Mathematics of a Trading System

[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-37%20passing-brightgreen.svg)](tests/)
[![Data](https://img.shields.io/badge/data-Yahoo%20Finance-orange.svg)](https://finance.yahoo.com/)
[![Report](https://img.shields.io/badge/report-22--page%20PDF-red.svg)](output/expectancy_study.pdf)

A rules-based backtester that measures the **mathematical fingerprint** of a trading system —
**win rate, expectancy, R-multiple, equity curve, max drawdown, variance and risk of ruin** — on real
OHLCV from Yahoo Finance. It is built around one non-negotiable principle: these numbers are **not
data you download**, they are **results of simulating a strategy** trade by trade, after costs, with
no lookahead.

The question this repo answers is not "what was the return?" but **"does this system have a real edge,
and could I survive the variance of trading it?"** It then runs the same example strategy across five
instruments and reports the answer without spin.

---

## TL;DR

- **The example strategy (MA20×MA50 crossover) shows no edge the data can confirm.** After costs,
  the per-trade expectancy *swings across instruments* — QQQ **+0.42R**, ITUB4 **+0.22R**, SPY
  **−0.09R**, PETR4 **−0.11R** — but with only ~40 trades each, that spread is exactly what pure chance
  produces even if the true edge were identical (or zero) everywhere.
- **Statistically, every instrument is a coin-flip.** The **95% bootstrap confidence interval on
  expectancy straddles zero for all five** — and even **pooling all 201 trades** into one stream leaves
  it at **[−0.11R, +0.30R]**, still including zero (P(edge > 0) ≈ 81%, short of the 95% bar). The honest
  verdict is not "no edge" but **"underpowered — a small edge cannot be told apart from none."**
- **Variance dominates the experience.** Bootstrapping QQQ's trades 5,000 times, the outcome runs
  from a **4.7% chance of ending in the red** (despite a positive point estimate) to ~**+17% at the
  95th percentile** — same trades, same expectancy, a very different ride from luck of sequence alone.
- **Risk of ruin explodes non-linearly, and the edge is thin to costs.** At ≤ 2% risk per trade a
  50% drawdown is ~0% likely; at **5% per trade** it jumps to **37–38%** on the weakest names. And a
  small bump in slippage flips the marginal instruments negative — the conclusion of "who wins" hangs
  on the cost assumption.
- **The recovery math is unforgiving:** a 50% drawdown needs a **100%** gain to undo. This is why the
  system measures *survival*, not just return.

> **One-sentence verdict:** the value here is not the strategy — it is a backtester honest enough to
> show that, at this sample size, the strategy's edge cannot be confirmed *or* ruled out, and that
> variance and position sizing dominate the outcome either way.

**Full 22-page technical report:** [`output/expectancy_study.pdf`](output/expectancy_study.pdf)

---

## Table of contents

- [The four pillars](#the-four-pillars)
- [Data & methodology](#data--methodology)
- [Results](#results)
  - [1. The cross-instrument scorecard](#1-the-cross-instrument-scorecard)
  - [2. Win rate vs the breakeven it must clear](#2-win-rate-vs-the-breakeven-it-must-clear)
  - [3. Is the edge real? The significance test](#3-is-the-edge-real-the-significance-test)
  - [4. Pooling for power & an out-of-sample split](#4-pooling-for-power--an-out-of-sample-split)
  - [5. The edge is thin: cost sensitivity](#5-the-edge-is-thin-cost-sensitivity)
  - [6. Variance changes everything](#6-variance-changes-everything)
  - [7. Risk of ruin & the risk dial](#7-risk-of-ruin--the-risk-dial)
  - [8. The recovery math](#8-the-recovery-math)
- [Conclusions](#conclusions)
- [Reproduce it](#reproduce-it)
- [Project structure](#project-structure)
- [Reference document](#reference-document)
- [Disclaimer](#disclaimer)

---

## The four pillars

The system measures the four things that actually describe a trading method:

| Pillar | What it answers | How it is measured here |
|---|---|---|
| **Expectancy** | Does each trade make money on average? | `WR × avg_win − LR × avg_loss`, in money **and** in R, validated against the realized mean |
| **Variance** | Could the same edge feel like a disaster? | 5,000-sample bootstrap of the realized trades — median path, 5–95% band, best/worst |
| **Risk / reward** | Is the payoff worth the hit rate? | R-multiples, payoff ratio, and the breakeven win rate `1/(R+1)` shown next to the real one |
| **Survival** | Could the account die before the edge pays? | Monte-Carlo risk of ruin by bet size, plus the loss → recovery asymmetry |

Everything downstream of the raw OHLCV is computed, never downloaded.

## Data & methodology

| | |
|---|---|
| **Source** | [Yahoo Finance](https://finance.yahoo.com/) via `yfinance`, downloaded once and cached as Parquet |
| **Instruments** | SPY, QQQ (US indices) · PETR4.SA, VALE3.SA, ITUB4.SA (Brazil / B3) |
| **History** | Daily, adjusted OHLCV, 2010-01-01 → 2026-01-01 (a common window for a fair comparison) |
| **Strategy** | MA20×MA50 crossover, long-only, with an ATR(14) stop (1.5×) and target (3.0×) — configurable |
| **King metric** | **Per-trade expectancy after costs**, in money and in R; plus PF, drawdown, Sharpe/Sortino |
| **Costs** | Spread + commission + slippage, charged round-trip on **every** trade |
| **Sizing** | Fixed-fractional: each trade risks **0.5% of equity**; a wider stop ⇒ a smaller position |
| **No lookahead** | A signal at the close of bar *t* is executed at the **open of bar t+1**, never at its own close |
| **Variance/ruin** | 5,000-sample bootstrap (with replacement) with a **fixed seed** (42) for reproducibility |
| **Significance** | 10,000-sample bootstrap **95% CI** on expectancy; **pooling** to ~200 trades; chronological **out-of-sample** split; **cost-sensitivity** sweep |

All figures and tables below come straight from the pipeline (`scripts/run_study.py` →
`scripts/build_report.py`); nothing is hand-edited.

## Results

### 1. The cross-instrument scorecard

The same strategy, same parameters, run on every instrument. The point estimates *look* like a result —
some markets positive, some negative — but hold that thought: with ~40 trades each, this spread is also
exactly what randomness would paint on top of a single, identical (even zero) edge. Section 3 puts error
bars on it.

![Per-trade expectancy by instrument](output/figures/00_expectancy_comparison.png)

| Instrument | Trades | Win rate | Expectancy (R) | Expectancy ($) | Profit factor | Max DD | Edge? |
|---|---|---|---|---|---|---|---|
| SPY | 39 | 30.8% | **−0.088** | −4.61 | 0.87 | 5.6% | ❌ |
| QQQ | 37 | 51.4% | **+0.422** | +21.63 | 1.83 | 1.9% | ✅ |
| PETR4.SA | 42 | 35.7% | **−0.109** | −5.63 | 0.84 | 3.7% | ❌ |
| VALE3.SA | 43 | 41.9% | **+0.039** | +1.70 | 1.06 | 3.6% | ⚠️ marginal |
| ITUB4.SA | 40 | 47.5% | **+0.222** | +11.09 | 1.40 | 4.7% | ✅ |

*Expectancy after costs. Three positive, two negative — but **every sample is under 100 trades**, so
read these as hypotheses, not facts. The expectancy sanity check (`formula == realized mean`) passes
for all five, confirming the arithmetic is right even where the conclusion is undecidable.*

### 2. Win rate vs the breakeven it must clear

A 3:1 payoff target only needs ~25% wins to break even, so a "low" win rate is not automatically bad —
what matters is the win rate **relative to its breakeven**. Plotting both makes the margin (or lack of
it) obvious.

![Actual win rate vs breakeven](output/figures/00_winrate_vs_breakeven.png)

*Where the blue bar clears the grey one, the system has positive expectancy (QQQ, ITUB4, VALE3); where
it falls short (SPY, PETR4), it bleeds. The gaps are thin — this is a marginal system, not a money
printer.*

### 3. Is the edge real? The significance test

A point estimate without an interval is a guess with a confident voice. Bootstrapping the per-trade
expectancy (resampling the realized R-multiples **with replacement** 10,000 times and taking the
2.5th–97.5th percentiles of the mean) gives a 95% confidence interval. Where it crosses zero, a small
edge cannot be told apart from no edge.

![Expectancy with 95% bootstrap CI](output/figures/00_significance_forest.png)

| Instrument | Trades | Expectancy (R) | 95% CI (R) | P(edge > 0) | Verdict |
|---|---|---|---|---|---|
| SPY | 39 | −0.088 | [−0.53, +0.40] | 34% | indistinguishable from zero |
| QQQ | 37 | +0.422 | [−0.07, +0.93] | 95% | indistinguishable from zero |
| PETR4.SA | 42 | −0.109 | [−0.51, +0.31] | 30% | indistinguishable from zero |
| VALE3.SA | 43 | +0.039 | [−0.37, +0.47] | 57% | indistinguishable from zero |
| ITUB4.SA | 40 | +0.222 | [−0.20, +0.65] | 85% | indistinguishable from zero |

*Every single interval straddles zero (all grey in the forest plot). Even QQQ — the best-looking name —
only reaches 95% probability of a positive mean, and its interval still includes zero. At ~40 trades,
the data cannot confirm an edge in **any** direction. This is the result the headline scorecard hides,
and the honest centre of the whole study.*

### 4. Pooling for power & an out-of-sample split

If no single instrument has enough trades, pool them. Because R normalises each trade by its risk, the
201 trades from all five instruments form one comparable stream — finally crossing the ~100-trade
threshold where expectancy begins to settle.

![Pooled expectancy convergence](output/figures/00_pooled_convergence.png)

The pooled expectancy is **+0.090R**, with a 95% CI of **[−0.11R, +0.30R]** — *still including zero*
(P(edge > 0) ≈ 81%). Splitting the pool chronologically gives a genuine out-of-sample check:

| Pool split | Trades | Expectancy (R) |
|---|---|---|
| In-sample (first half) | 100 | **−0.137** |
| Out-of-sample (second half) | 101 | **+0.316** |

*Two honest signals at once. First: even at 201 trades the running average is still wandering — the
shaded "noise zone" (< 100 trades) swings from −1R to +0.6R before calming. Second: the out-of-sample
half is **better** than the in-sample half, so this is **not** a classic over-fit; if anything the
positive trades cluster in the later (post-2020) regime — which is itself a warning that the "edge" may
be regime exposure, not skill. Either way, the pooled CI still includes zero.*

### 5. The edge is thin: cost sensitivity

Where expectancy is a fraction of an R, the cost assumption is a lever, not a footnote. Sweeping the
slippage assumption shows how fast each instrument's edge crosses into the red.

![Cost sensitivity](output/figures/00_cost_sensitivity.png)

*At the baseline 0.05 slippage, QQQ and ITUB4 look positive — but VALE3 is already breakeven, and a
modest rise in slippage drags ITUB4 negative and halves QQQ. The ranking of "who wins" is not robust to
a parameter nobody can pin down precisely. This is the cost warning from the source material, made
literal.*

### 6. Variance changes everything

Even taking the trades at face value, a single equity curve hides the role of luck. Bootstrap QQQ's
trades (resample **with replacement**) 5,000 times and rebuild the account each time — same trades,
same expectancy, very different journeys.

![QQQ Monte-Carlo fan](output/figures/QQQ_mc_fan.png)
![QQQ distribution of final equity](output/figures/QQQ_mc_hist.png)

*The realized run (dashed) is just one draw from the blue cone. Across the 5,000 simulations QQQ ends
below its starting capital **4.7%** of the time despite a positive point estimate, and because it risks
only 0.5% per trade over 37 trades the lucky 95th-percentile tail still only reaches ~+17%. (Note: a
mere reshuffle of the same trades would give an identical final equity under fixed-fractional sizing —
a product is commutative — so resampling **with replacement** is what disperses the destination, not
just the path.)*

### 7. Risk of ruin & the risk dial

The probability of a catastrophic drawdown is driven less by the strategy than by **how much you bet
per trade**. The same trade stream, replayed at different risk levels, shows the non-linear blow-up.

![SPY risk of ruin](output/figures/SPY_ruin.png)

| Risk per trade | SPY P(DD ≥ 50%) | PETR4 P(DD ≥ 50%) | ITUB4 P(DD ≥ 50%) |
|---|---|---|---|
| 0.5% | 0.0% | 0.0% | 0.0% |
| 1.0% | 0.0% | 0.0% | 0.0% |
| 2.0% | 0.0% | 0.0% | 0.0% |
| 5.0% | **37.2%** | **38.0%** | **3.6%** |

*Below 2% risk the deep-drawdown probability is effectively zero everywhere; at 5% it explodes — and it
explodes *fastest* on the negative-edge instruments. The lesson the maths forces: the risk dial ends
more accounts than the entry signal.*

### 8. The recovery math

Losses and the gains needed to undo them are asymmetric — which is why protecting capital beats
chasing return.

| Drawdown suffered | Gain required to recover |
|---|---|
| 10% | 11% |
| 20% | 25% |
| 30% | 43% |
| 40% | 67% |
| 50% | **100%** |

*A 50% loss does not need 50% back — it needs to *double*. Combined with the risk-of-ruin table, this
is the whole argument for sizing small.*

## Conclusions

1. **The strategy's edge cannot be confirmed — or ruled out — at this sample size.** Every per-trade
   expectancy CI straddles zero, and so does the pooled one (201 trades, [−0.11R, +0.30R]). The honest
   statement is "underpowered," not "no edge." With ~40 trades per instrument, the eye-catching spread
   from −0.11R to +0.42R is well within what noise alone would produce over a common true edge.
2. **A moving-average crossover on daily bars is structurally underpowered.** It fires ~2.5 times a
   year, so even 16 years cannot generate the trades needed to validate or invalidate it. That — more
   than the strategy being "good" or "bad" — is the concrete lesson here.
3. **Variance and position sizing dominate the outcome.** Bootstrapped, the same trades give very
   different equity paths, and the risk dial controls survival far more than the entry rule does. The
   thin edge is also fragile to the cost assumption.
4. **The deliverable is the method, not the money.** A backtester that refuses to lie — no lookahead,
   full costs, fixed-fractional risk, a forced expectancy sanity check, bootstrap confidence intervals,
   pooling, an out-of-sample split and reproducible Monte-Carlo — is what lets you separate a real edge
   from a lucky one. Here it says, precisely: *not enough evidence to call it.*

> The backtester *measures* an edge; it does not *create* one. Plug in a strategy that trades often
> enough to have genuine statistical power, and the same machinery will resolve the question — honestly,
> with its variance and its risk of ruin. The engine is already built for it; swap the strategy and the
> sample, not the motor.

## Reproduce it

The first run downloads and caches the data; later runs are offline. The figures and the PDF report are
committed, so you can read the study without running anything.

```powershell
# Windows / PowerShell (Python 3.12+)
py -3.12 -m venv .venv
& ".venv\Scripts\Activate.ps1"          # if blocked: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
pip install -r requirements.txt
pip install -e .

pytest -q                               # 37 tests
python main.py                          # single instrument from config.yaml (full scorecard + figures)
python scripts/run_study.py             # downloads + caches data, runs the US+BR basket
python scripts/build_report.py          # renders output/figures/*.png and the PDF report
```

```bash
# macOS / Linux
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt && pip install -e .
pytest -q
python main.py
python scripts/run_study.py && python scripts/build_report.py
```

Change the instrument, period, costs, risk and strategy parameters in [`config.yaml`](config.yaml);
nothing requires touching code.

## Project structure

```
src/expectancy/
  config.py        typed config loaded from config.yaml
  data/            yfinance download + Parquet cache + cleaning (the only networked layer)
  strategy/        pluggable Strategy base + MA-crossover with ATR stop/target; causal indicators
  engine/          trade-by-trade simulation (t→t+1 execution, costs, fixed-fractional sizing, R)
  metrics/         the scorecard: expectancy ($ & R), profit factor, breakeven WR, drawdown, Sharpe
  montecarlo/      bootstrap variance, risk of ruin by bet size, recovery math
  analysis/        significance (bootstrap CI), pooling + out-of-sample split, cost sensitivity
  reporting/       terminal report, matplotlib figures, and the reportlab PDF
  runner.py        wires the layers into one backtest run
scripts/           run_study.py (basket + cache) · build_report.py (figures + PDF)
main.py            single-instrument entry point (the brief's acceptance criterion)
tests/             37 tests: lookahead, R-multiples, expectancy sanity, sizing, Monte-Carlo, significance
output/figures/    the figures used in the report and this README (committed)
```

## Reference document

[`BACKTEST_BRIEF.md`](BACKTEST_BRIEF.md) — the full specification this project implements: the four
pillars, the no-lookahead rule, the cost and sizing model, the Monte-Carlo requirements and the
quality checklist.

## Disclaimer

This is an educational and research project. **Nothing here is investment advice.** The example
strategy is a didactic moving-average crossover, not a system with a guaranteed edge. Retail trading
has a negative base rate and leverage carries the risk of total loss. Past performance does not
guarantee future results.

Licensed under the [MIT License](LICENSE).
