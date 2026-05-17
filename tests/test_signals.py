"""Tests for the Faber signal and weight builder."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from etf_gtaa.signals import dual_momentum, equal_weight_targets, faber_signal, sma


def test_sma_simple_window() -> None:
    prices = pd.DataFrame({"X": [1.0, 2.0, 3.0, 4.0, 5.0]})
    result = sma(prices, window=3)
    assert pd.isna(result["X"].iloc[0])
    assert pd.isna(result["X"].iloc[1])
    assert result["X"].iloc[2] == pytest.approx(2.0)
    assert result["X"].iloc[4] == pytest.approx(4.0)


def test_faber_signal_uptrend_is_true(trending_up_series: pd.Series) -> None:
    prices = trending_up_series.to_frame()
    sig = faber_signal(prices, window=10)
    # After warm-up an always-rising series is always above its trailing SMA
    assert sig.iloc[10:].all().all()


def test_faber_signal_downtrend_is_false(trending_down_series: pd.Series) -> None:
    prices = trending_down_series.to_frame()
    sig = faber_signal(prices, window=10)
    assert not sig.iloc[10:].any().any()


def test_equal_weight_targets_rows_sum_to_one(synthetic_monthly_prices: pd.DataFrame) -> None:
    sig = faber_signal(synthetic_monthly_prices, window=10)
    weights = equal_weight_targets(sig)
    assert "CASH" in weights.columns
    assert (weights.sum(axis=1).round(8) == 1.0).all()


def test_equal_weight_targets_all_false_means_all_cash(
    synthetic_monthly_prices: pd.DataFrame,
) -> None:
    sig = pd.DataFrame(False, index=synthetic_monthly_prices.index, columns=["A", "B", "C"])
    weights = equal_weight_targets(sig)
    assert (weights["CASH"] == 1.0).all()


# ── dual_momentum tests ───────────────────────────────────────────────────────


def test_dual_momentum_rows_sum_to_one(synthetic_monthly_prices: pd.DataFrame) -> None:
    weights = dual_momentum(synthetic_monthly_prices, lookback=12, top_k=2, cash_returns=0.0)
    assert "CASH" in weights.columns
    assert (weights.sum(axis=1).round(8) == 1.0).all()


def test_dual_momentum_warmup_is_all_cash(synthetic_monthly_prices: pd.DataFrame) -> None:
    lookback = 12
    weights = dual_momentum(synthetic_monthly_prices, lookback=lookback, top_k=2, cash_returns=0.0)
    assert (weights["CASH"].iloc[:lookback] == 1.0).all()


def test_dual_momentum_all_falling_is_all_cash() -> None:
    """Every asset has a negative 12-month return → fails the absolute filter → 100% CASH."""
    idx = pd.date_range("2020-01-31", periods=24, freq="ME")
    prices = pd.DataFrame(
        {
            "A": np.linspace(200.0, 100.0, 24),
            "B": np.linspace(200.0, 80.0, 24),
            "C": np.linspace(200.0, 120.0, 24),
        },
        index=idx,
    )
    weights = dual_momentum(prices, lookback=12, top_k=2, cash_returns=0.0)
    assert (weights["CASH"].iloc[12:] == 1.0).all()


def test_dual_momentum_top_k_limits_risky_positions() -> None:
    """With top_k=2 and all assets above cash, exactly 2 risky names hold weight."""
    idx = pd.date_range("2020-01-31", periods=24, freq="ME")
    prices = pd.DataFrame(
        {
            "A": np.linspace(100.0, 200.0, 24),  # strongest momentum
            "B": np.linspace(100.0, 150.0, 24),  # medium momentum
            "C": np.linspace(100.0, 110.0, 24),  # weakest momentum
        },
        index=idx,
    )
    weights = dual_momentum(prices, lookback=12, top_k=2, cash_returns=0.0)
    risky_cols = ["A", "B", "C"]
    n_nonzero = (weights[risky_cols].iloc[12:] > 0).sum(axis=1)
    assert (n_nonzero == 2).all()
