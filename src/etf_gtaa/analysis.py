"""Robustness and sensitivity analysis for the Faber GTAA strategy.

Runs the backtest engine across a parameter grid and returns a tidy DataFrame
suitable for heatmap visualisation. No I/O — pure computation.
"""

from __future__ import annotations

from itertools import product

import pandas as pd

from etf_gtaa.backtest import run_backtest
from etf_gtaa.metrics import summary
from etf_gtaa.signals import equal_weight_targets, faber_signal


def sensitivity_grid(
    monthly_prices: pd.DataFrame,
    cash_return: pd.Series | float = 0.0,
    sma_windows: list[int] | None = None,
    cost_bps_list: list[float] | None = None,
    initial_capital: float = 100_000.0,
) -> pd.DataFrame:
    """Run the Faber strategy across a (sma_window × cost_bps) parameter grid.

    Args:
        monthly_prices: month-end prices for the risky tickers.
        cash_return: monthly cash return as a constant float or a Series
            aligned to ``monthly_prices.index``.
        sma_windows: SMA lookback values in months to test
            (default: ``[6, 8, 10, 12]``).
        cost_bps_list: one-way transaction costs in basis points to test
            (default: ``[5.0, 10.0, 25.0]``).
        initial_capital: starting NAV passed through to the backtest engine.

    Returns:
        DataFrame indexed by ``(sma_window, cost_bps)`` with one column per
        metric returned by :func:`~etf_gtaa.metrics.summary` (CAGR, Vol,
        Sharpe, Max Drawdown, Calmar, Hit Ratio).
    """
    if sma_windows is None:
        sma_windows = [6, 8, 10, 12]
    if cost_bps_list is None:
        cost_bps_list = [5.0, 10.0, 25.0]

    rows: list[dict[str, object]] = []
    for window, cost in product(sma_windows, cost_bps_list):
        signal = faber_signal(monthly_prices, window=window)
        targets = equal_weight_targets(signal)
        result = run_backtest(
            monthly_prices,
            targets,
            cash_return=cash_return,
            transaction_cost_bps=cost,
            initial_capital=initial_capital,
        )
        row: dict[str, object] = summary(result.monthly_returns, result.equity_curve).to_dict()
        row["sma_window"] = window
        row["cost_bps"] = cost
        rows.append(row)

    return pd.DataFrame(rows).set_index(["sma_window", "cost_bps"])
