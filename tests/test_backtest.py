"""Tests for the backtest engine. Focus on no-lookahead and cash invariants."""

from __future__ import annotations

import pandas as pd
import pytest

from etf_gtaa.backtest import run_backtest


def test_all_cash_grows_at_cash_rate(synthetic_monthly_prices: pd.DataFrame) -> None:
    """100% cash every month should compound at exactly the cash rate."""
    cols = [*synthetic_monthly_prices.columns, "CASH"]
    weights = pd.DataFrame(0.0, index=synthetic_monthly_prices.index, columns=cols)
    weights["CASH"] = 1.0

    cash_rate = 0.002  # ~2.4% annualized
    result = run_backtest(
        synthetic_monthly_prices,
        weights,
        cash_return=cash_rate,
        transaction_cost_bps=0.0,
    )

    expected_growth = (1.0 + cash_rate) ** (len(synthetic_monthly_prices) - 1)
    realized_growth = result.equity_curve.iloc[-1] / result.equity_curve.iloc[0]
    assert realized_growth == pytest.approx(expected_growth, rel=1e-6)


def test_no_lookahead(synthetic_monthly_prices: pd.DataFrame) -> None:
    """Mutating the last row of targets must not change any earlier return."""
    cols = [*synthetic_monthly_prices.columns, "CASH"]
    w1 = pd.DataFrame(
        1.0 / len(cols), index=synthetic_monthly_prices.index, columns=cols
    )
    w2 = w1.copy()
    w2.iloc[-1] = 0.0
    w2.iloc[-1, w2.columns.get_loc("CASH")] = 1.0

    r1 = run_backtest(synthetic_monthly_prices, w1, transaction_cost_bps=0.0).monthly_returns
    r2 = run_backtest(synthetic_monthly_prices, w2, transaction_cost_bps=0.0).monthly_returns

    pd.testing.assert_series_equal(r1.iloc[:-1], r2.iloc[:-1])


def test_costs_reduce_return(synthetic_monthly_prices: pd.DataFrame) -> None:
    """A high-turnover strategy with positive cost must underperform the zero-cost case."""
    cols = [*synthetic_monthly_prices.columns, "CASH"]
    rng_idx = synthetic_monthly_prices.index
    # Alternate full risk / full cash every month → maximum turnover
    w_risk = pd.DataFrame(0.0, index=rng_idx, columns=cols)
    w_risk.iloc[::2, :-1] = 1.0 / (len(cols) - 1)
    w_risk.iloc[1::2, w_risk.columns.get_loc("CASH")] = 1.0

    r_zero = run_backtest(synthetic_monthly_prices, w_risk, transaction_cost_bps=0.0)
    r_cost = run_backtest(synthetic_monthly_prices, w_risk, transaction_cost_bps=50.0)

    assert r_cost.equity_curve.iloc[-1] < r_zero.equity_curve.iloc[-1]


def test_rejects_misaligned_inputs(synthetic_monthly_prices: pd.DataFrame) -> None:
    cols = [*synthetic_monthly_prices.columns, "CASH"]
    bad_weights = pd.DataFrame(
        1.0 / len(cols),
        index=synthetic_monthly_prices.index[:-5],  # wrong length
        columns=cols,
    )
    with pytest.raises(ValueError):
        run_backtest(synthetic_monthly_prices, bad_weights)
