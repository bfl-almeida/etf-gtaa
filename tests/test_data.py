"""Tests for the data layer. No network calls."""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import pytest

from etf_gtaa.data import _assert_no_nan, to_monthly


def test_to_monthly_returns_last_observation_per_month() -> None:
    idx = pd.date_range("2024-01-01", "2024-03-31", freq="B")
    daily = pd.DataFrame({"X": range(len(idx))}, index=idx, dtype=float)

    monthly = to_monthly(daily)

    assert len(monthly) == 3
    # Last business day of January 2024 is 2024-01-31
    assert monthly.loc["2024-01-31", "X"] == daily.loc["2024-01-31", "X"]


def test_assert_no_nan_raises_on_leading_nan() -> None:
    idx = pd.date_range("2020-01-01", periods=5, freq="B")
    prices = pd.DataFrame({"A": [1.0, 2.0, 3.0, 4.0, 5.0], "B": [np.nan, 2.0, 3.0, 4.0, 5.0]}, index=idx)
    with pytest.raises(ValueError, match="NaN"):
        _assert_no_nan(prices, date(2020, 1, 1))


def test_assert_no_nan_passes_clean_data() -> None:
    idx = pd.date_range("2020-01-01", periods=3, freq="B")
    prices = pd.DataFrame({"A": [1.0, 2.0, 3.0]}, index=idx)
    _assert_no_nan(prices, date(2020, 1, 1))  # must not raise
