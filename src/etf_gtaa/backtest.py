"""Vectorized monthly backtest engine.

The engine enforces no-lookahead: targets at month ``t`` apply to returns from
``t`` to ``t+1``, with the realized weight drift between rebalances baked in.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt
import pandas as pd


@dataclass
class BacktestResult:
    """Output container for a single backtest run.

    Attributes:
        equity_curve: portfolio NAV indexed by month-end.
        monthly_returns: net-of-cost monthly returns aligned with equity_curve.
        weights: realized weights per ticker per month (post-drift, pre-rebalance).
        turnover: one-way turnover per rebalance (sum of |delta weights| / 2).
    """

    equity_curve: pd.Series
    monthly_returns: pd.Series
    weights: pd.DataFrame
    turnover: pd.Series


def run_backtest(
    monthly_prices: pd.DataFrame,
    target_weights: pd.DataFrame,
    cash_return: pd.Series | float = 0.0,
    transaction_cost_bps: float = 10.0,
    initial_capital: float = 100_000.0,
) -> BacktestResult:
    """Run a monthly-rebalanced, vectorized backtest.

    The position decided at month ``t`` is applied from ``t`` to ``t+1``. Cost
    is charged at rebalance as ``cost_bps / 10_000 * one_way_turnover``.

    Args:
        monthly_prices: month-end prices for the risky tickers (T rows x N cols).
        target_weights: month-end target weights including a ``CASH`` column
            (T rows x (N+1) cols). Rows must sum to 1.0.
        cash_return: per-month cash return; constant or aligned Series.
        transaction_cost_bps: one-way transaction cost in basis points.
        initial_capital: starting NAV.

    Returns:
        :class:`BacktestResult` with equity curve, returns, realized weights,
        and turnover.

    Raises:
        ValueError: if ``monthly_prices`` and ``target_weights`` are not aligned,
            or if any row of ``target_weights`` does not sum to 1.0 (within tol).
    """
    if not monthly_prices.index.equals(target_weights.index):
        raise ValueError(
            "monthly_prices and target_weights must share the same index."
        )
    row_sums = target_weights.sum(axis=1)
    if not (row_sums - 1.0).abs().lt(1e-8).all():
        raise ValueError("Each row of target_weights must sum to 1.0 (within 1e-8).")

    risky_cols = monthly_prices.columns.tolist()

    # Risky returns: (T-1) x N, indexed by prices.index[1:]
    risky_rets: pd.DataFrame = monthly_prices.pct_change().iloc[1:]

    # Targets that govern each return period (0..T-2)
    w_period = target_weights.iloc[:-1]  # (T-1) x (N+1)

    # Gross portfolio return contributions
    w_risky: npt.NDArray[np.float64] = w_period[risky_cols].values  # (T-1) x N
    gross_risky: npt.NDArray[np.float64] = (w_risky * risky_rets.values).sum(axis=1)  # (T-1,)

    w_cash: npt.NDArray[np.float64] = w_period["CASH"].values  # (T-1,)
    if isinstance(cash_return, (int, float)):
        cash_ret_arr: npt.NDArray[np.float64] = np.full(len(risky_rets), float(cash_return))
    else:
        cash_ret_arr = cash_return.reindex(risky_rets.index, fill_value=0.0).values

    gross_return: npt.NDArray[np.float64] = gross_risky + w_cash * cash_ret_arr  # (T-1,)

    # One-way turnover: |target[t] - target[t-1]|.sum() / 2
    # Implicit prior position before the backtest is all-zero.
    w_all: npt.NDArray[np.float64] = w_period.values  # (T-1) x (N+1)
    prior = np.zeros((1, target_weights.shape[1]))
    w_prev = np.vstack([prior, w_all[:-1]])  # (T-1) x (N+1)
    one_way_turnover: npt.NDArray[np.float64] = np.abs(w_all - w_prev).sum(axis=1) / 2.0
    cost_frac: npt.NDArray[np.float64] = one_way_turnover * transaction_cost_bps / 10_000.0

    net_rets: npt.NDArray[np.float64] = gross_return - cost_frac
    net_rets_series = pd.Series(net_rets, index=risky_rets.index)

    # Equity curve: initial_capital at t=0, then compounded
    cum = (1.0 + net_rets_series).cumprod() * initial_capital
    equity_curve = pd.concat(
        [pd.Series([initial_capital], index=[monthly_prices.index[0]]), cum]
    )

    return BacktestResult(
        equity_curve=equity_curve,
        monthly_returns=net_rets_series,
        weights=w_period.copy(),
        turnover=pd.Series(one_way_turnover, index=risky_rets.index),
    )
