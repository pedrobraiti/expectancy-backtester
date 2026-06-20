"""Position sizing — the heart of risk management (brief §5.4).

The cash risked per trade is *fixed* (a percentage of equity); the position size
is whatever makes the distance to the stop equal that risk. A wider stop means a
smaller position, a tighter stop a larger one — the percentage risked stays
constant. This is the opposite of trading a fixed number of shares.
"""

from __future__ import annotations

STANDARD_LOT_UNITS = 100_000
"""One standard forex lot = 100,000 units of the base currency."""


def position_size(risk_money: float, risk_per_unit: float) -> float:
    """Units to trade so that hitting the stop loses exactly `risk_money`.

    ``size = risk_money / risk_per_unit``. Returns 0 when the per-unit risk is
    non-positive (degenerate signal), so the engine simply skips the trade.
    """
    if risk_per_unit <= 0:
        return 0.0
    return risk_money / risk_per_unit


def lot_size(balance: float, risk_pct: float, stop_pips: float, pip_value: float = 10.0) -> float:
    """Forex lot calculator (brief §5.4).

    Given account `balance`, the `risk_pct` you accept, the stop distance in
    `stop_pips` and the cash value of one pip per standard lot (`pip_value`,
    ~$10 for most USD-quoted pairs), return the number of standard lots.
    """
    if stop_pips <= 0 or pip_value <= 0:
        return 0.0
    risk_money = balance * (risk_pct / 100.0)
    return risk_money / (stop_pips * pip_value)
