"""Tests for the sensitivity grid analysis helper."""

from __future__ import annotations

import pandas as pd
import pytest

from etf_gtaa.analysis import sensitivity_grid


def test_sensitivity_grid_shape(synthetic_monthly_prices: pd.DataFrame) -> None:
    result = sensitivity_grid(
        synthetic_monthly_prices,
        sma_windows=[6, 10],
        cost_bps_list=[5.0, 25.0],
    )
    assert result.shape[0] == 4  # 2 windows × 2 costs
    assert result.index.names == ["sma_window", "cost_bps"]


def test_sensitivity_grid_all_metrics_present(synthetic_monthly_prices: pd.DataFrame) -> None:
    result = sensitivity_grid(
        synthetic_monthly_prices,
        sma_windows=[10],
        cost_bps_list=[10.0],
    )
    expected = {"CAGR", "Vol", "Sharpe", "Max Drawdown", "Calmar", "Hit Ratio"}
    assert expected.issubset(set(result.columns))


def test_sensitivity_grid_higher_cost_reduces_cagr(synthetic_monthly_prices: pd.DataFrame) -> None:
    result = sensitivity_grid(
        synthetic_monthly_prices,
        sma_windows=[10],
        cost_bps_list=[5.0, 25.0],
    )
    assert result.loc[(10, 5.0), "CAGR"] >= result.loc[(10, 25.0), "CAGR"]
