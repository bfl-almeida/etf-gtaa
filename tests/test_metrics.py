"""Tests for performance metrics with closed-form expected values."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from etf_gtaa.metrics import annualized_vol, cagr, max_drawdown, sharpe


def test_cagr_with_constant_monthly_return() -> None:
    monthly = pd.Series([0.01] * 12)
    # (1.01)^12 - 1 ≈ 0.12683
    assert cagr(monthly) == pytest.approx(0.12683, abs=1e-4)


def test_annualized_vol_scales_by_sqrt_12() -> None:
    rng = np.random.default_rng(0)
    monthly = pd.Series(rng.normal(0.0, 0.05, 10_000))
    # 5% monthly stdev → ~17.3% annualized
    assert annualized_vol(monthly) == pytest.approx(0.05 * np.sqrt(12), abs=0.01)


def test_max_drawdown_known_path() -> None:
    equity = pd.Series([100.0, 110.0, 121.0, 100.0, 90.0, 95.0])
    # Peak 121 → trough 90 → drawdown = (90 - 121) / 121 ≈ -0.2562
    assert max_drawdown(equity) == pytest.approx(-0.2562, abs=1e-4)


def test_sharpe_zero_for_zero_returns() -> None:
    monthly = pd.Series([0.0] * 60)
    # Convention: 0 / 0 returns 0 (or NaN — both acceptable, but be explicit).
    result = sharpe(monthly, rf=0.0)
    assert result == 0.0 or pd.isna(result)


def test_sharpe_positive_when_mean_exceeds_rf() -> None:
    rng = np.random.default_rng(0)
    monthly = pd.Series(rng.normal(0.01, 0.04, 240))
    assert sharpe(monthly, rf=0.0) > 0
