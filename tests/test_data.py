"""Tests for the data layer. No network calls."""

from __future__ import annotations

import pandas as pd

from etf_gtaa.data import to_monthly


def test_to_monthly_returns_last_observation_per_month() -> None:
    idx = pd.date_range("2024-01-01", "2024-03-31", freq="B")
    daily = pd.DataFrame({"X": range(len(idx))}, index=idx, dtype=float)

    monthly = to_monthly(daily)

    assert len(monthly) == 3
    # Last business day of January 2024 is 2024-01-31
    assert monthly.loc["2024-01-31", "X"] == daily.loc["2024-01-31", "X"]
