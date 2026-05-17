"""Shared pytest fixtures. No network calls allowed in tests."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def synthetic_monthly_prices() -> pd.DataFrame:
    """Five years of deterministic monthly prices for three synthetic assets."""
    rng = np.random.default_rng(seed=42)
    n_months = 60
    dates = pd.date_range("2015-01-31", periods=n_months, freq="ME")

    annual_drifts = np.array([0.06, 0.04, 0.02])
    annual_vols = np.array([0.15, 0.10, 0.05])

    monthly_drifts = annual_drifts / 12
    monthly_vols = annual_vols / np.sqrt(12)

    shocks = rng.standard_normal((n_months, 3)) * monthly_vols
    log_rets = shocks + monthly_drifts
    prices = 100.0 * np.exp(log_rets.cumsum(axis=0))

    return pd.DataFrame(prices, index=dates, columns=["A", "B", "C"])


@pytest.fixture
def trending_up_series() -> pd.Series:
    """Monotonic upward series — always above its SMA after the warm-up."""
    return pd.Series(
        np.linspace(100.0, 200.0, 24),
        index=pd.date_range("2020-01-31", periods=24, freq="ME"),
        name="UP",
    )


@pytest.fixture
def trending_down_series() -> pd.Series:
    """Monotonic downward series — always below its SMA after the warm-up."""
    return pd.Series(
        np.linspace(200.0, 100.0, 24),
        index=pd.date_range("2020-01-31", periods=24, freq="ME"),
        name="DOWN",
    )
