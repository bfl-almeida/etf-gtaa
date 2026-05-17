"""Tests for the Faber signal and weight builder."""

from __future__ import annotations

import pandas as pd
import pytest

from etf_gtaa.signals import equal_weight_targets, faber_signal, sma


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
