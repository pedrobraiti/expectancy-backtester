"""Position-sizing tests (brief §5.4)."""

from __future__ import annotations

import numpy as np

from expectancy.engine.sizing import lot_size, position_size


def test_position_size_is_risk_over_unit_risk():
    assert np.isclose(position_size(50.0, 2.0), 25.0)


def test_position_size_zero_when_unit_risk_nonpositive():
    assert position_size(50.0, 0.0) == 0.0
    assert position_size(50.0, -1.0) == 0.0


def test_lot_size_basic():
    # $10,000 balance, 1% risk = $100; 20 pip stop at $10/pip -> 0.5 lots
    assert np.isclose(lot_size(10_000, 1.0, 20, pip_value=10.0), 0.5)


def test_lot_size_zero_on_degenerate_stop():
    assert lot_size(10_000, 1.0, 0) == 0.0
