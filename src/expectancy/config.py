"""Typed configuration loaded from `config.yaml`.

A small set of frozen dataclasses so the rest of the codebase never touches raw
dicts and every parameter has a name and a default. Field names mirror the
Portuguese keys in the brief's `config.yaml` to keep the YAML readable for the
user, while the Python attributes stay descriptive.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass(frozen=True)
class CostConfig:
    """Transaction-cost model. All values are charged round-trip per trade."""

    spread: float = 0.02
    commission: float = 0.0
    slippage_frac: float = 0.05


@dataclass(frozen=True)
class StrategyConfig:
    name: str = "ma_crossover"
    fast_ma: int = 20
    slow_ma: int = 50
    atr_period: int = 14
    stop_atr_mult: float = 1.5
    target_atr_mult: float = 3.0
    direction: str = "long_only"


@dataclass(frozen=True)
class MonteCarloConfig:
    n_simulations: int = 5000
    seed: int = 42
    drawdown_target_pct: float = 50.0
    risk_levels: tuple[float, ...] = (0.5, 1.0, 2.0, 5.0)


@dataclass(frozen=True)
class Config:
    ticker: str = "PETR4.SA"
    start: str = "2010-01-01"
    end: str = "2026-01-01"
    interval: str = "1d"
    initial_capital: float = 10_000.0
    risk_per_trade_pct: float = 0.5
    costs: CostConfig = field(default_factory=CostConfig)
    strategy: StrategyConfig = field(default_factory=StrategyConfig)
    montecarlo: MonteCarloConfig = field(default_factory=MonteCarloConfig)

    def with_ticker(self, ticker: str) -> "Config":
        """Return a copy pointed at a different instrument (used by the basket study)."""
        return Config(
            ticker=ticker,
            start=self.start,
            end=self.end,
            interval=self.interval,
            initial_capital=self.initial_capital,
            risk_per_trade_pct=self.risk_per_trade_pct,
            costs=self.costs,
            strategy=self.strategy,
            montecarlo=self.montecarlo,
        )


def load_config(path: str | Path = "config.yaml") -> Config:
    """Parse the YAML config into a typed :class:`Config`.

    The YAML uses the brief's Portuguese keys; this is the single place that
    maps them onto the English dataclass fields.
    """
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    costs_raw = raw.get("custos", {})
    strat_raw = raw.get("estrategia", {})
    mc_raw = raw.get("montecarlo", {})

    return Config(
        ticker=raw["ticker"],
        start=raw["start"],
        end=raw["end"],
        interval=raw.get("interval", "1d"),
        initial_capital=float(raw.get("capital_inicial", 10_000)),
        risk_per_trade_pct=float(raw.get("risco_por_trade_pct", 0.5)),
        costs=CostConfig(
            spread=float(costs_raw.get("spread", 0.0)),
            commission=float(costs_raw.get("comissao", 0.0)),
            slippage_frac=float(costs_raw.get("slippage_frac", 0.0)),
        ),
        strategy=StrategyConfig(
            name=strat_raw.get("nome", "ma_crossover"),
            fast_ma=int(strat_raw.get("ma_rapida", 20)),
            slow_ma=int(strat_raw.get("ma_lenta", 50)),
            atr_period=int(strat_raw.get("atr_periodo", 14)),
            stop_atr_mult=float(strat_raw.get("stop_atr_mult", 1.5)),
            target_atr_mult=float(strat_raw.get("alvo_atr_mult", 3.0)),
            direction=strat_raw.get("direction", "long_only"),
        ),
        montecarlo=MonteCarloConfig(
            n_simulations=int(mc_raw.get("n_simulacoes", 5000)),
            seed=int(mc_raw.get("seed", 42)),
            drawdown_target_pct=float(mc_raw.get("drawdown_alvo_pct", 50)),
            risk_levels=tuple(float(x) for x in mc_raw.get("niveis_risco", [0.5, 1.0, 2.0, 5.0])),
        ),
    )
