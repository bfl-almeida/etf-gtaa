"""Faber (2007) and Antonacci (2014) timing signals and target-weight builders.

Pure functions: no I/O, no side effects.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def sma(prices: pd.DataFrame, window: int) -> pd.DataFrame:
    """Simple moving average, computed column-wise.

    Args:
        prices: price DataFrame (rows = time, columns = tickers), sorted ascending.
        window: window length in rows.

    Returns:
        DataFrame with the same shape and index as ``prices``. The first
        ``window - 1`` rows are NaN.
    """
    return prices.rolling(window=window, min_periods=window).mean()


def faber_signal(monthly_prices: pd.DataFrame, window: int = 10) -> pd.DataFrame:
    """Faber 10-month SMA timing signal.

    For each ticker and each month-end, the signal is True when the close is
    strictly above its SMA(window), False otherwise. Pre-warm-up rows return False.

    Args:
        monthly_prices: month-end prices, sorted ascending, no missing values
            within each column's history.
        window: SMA lookback in months.

    Returns:
        Boolean DataFrame with the same shape and index as ``monthly_prices``.
    """
    moving_avg = sma(monthly_prices, window)
    # NaN comparisons evaluate to False, matching the pre-warm-up spec.
    signal: pd.DataFrame = monthly_prices > moving_avg
    return signal


def equal_weight_targets(signal: pd.DataFrame) -> pd.DataFrame:
    """Convert a boolean signal to equal-weight target positions with cash buffer.

    Each row distributes weight ``1/N`` across the ``N`` risky tickers, where
    ``N`` is the number of input columns. Tickers with a False signal have their
    weight moved into a synthetic ``CASH`` column. Row weights sum to 1.0.

    Args:
        signal: boolean DataFrame from :func:`faber_signal`.

    Returns:
        DataFrame of target weights with one extra ``CASH`` column. Each row
        sums to exactly 1.0.
    """
    n = signal.shape[1]
    risky_weights = signal.astype(float) / n
    cash_weights = 1.0 - risky_weights.sum(axis=1)
    targets = risky_weights.copy()
    targets["CASH"] = cash_weights
    return targets


def dual_momentum(
    monthly_prices: pd.DataFrame,
    lookback: int = 12,
    top_k: int = 2,
    cash_returns: pd.Series | float = 0.0,
) -> pd.DataFrame:
    """Antonacci (2014) dual momentum: relative ranking + absolute momentum filter.

    For each month after the warm-up period:

    1. Rank risky ETFs by their trailing ``lookback``-month total return
       (relative / cross-sectional momentum).
    2. Select the top ``top_k`` ranked ETFs.
    3. Keep only those whose ``lookback``-month return also exceeds the
       compounded cash return over the same window (absolute momentum filter).
    4. Equal-weight the survivors; the remainder goes to ``CASH``.

    Rows in the first ``lookback`` months (warm-up) are 100 % CASH.

    Args:
        monthly_prices: month-end prices (T rows × N cols), sorted ascending.
        lookback: return lookback in months (Antonacci uses 12).
        top_k: number of ETFs selected by relative ranking before the absolute
            filter is applied.
        cash_returns: monthly cash return as a constant float or a
            Series aligned to ``monthly_prices.index`` (e.g. BIL pct change).

    Returns:
        DataFrame of target weights with the same index as ``monthly_prices``
        plus a ``CASH`` column. Every row sums to exactly 1.0.
    """
    # ── trailing lookback-month total returns (relative momentum) ─────────────
    mom: pd.DataFrame = monthly_prices.pct_change(periods=lookback)  # NaN for warm-up

    # ── trailing lookback-month compounded cash return ────────────────────────
    cash_12m: pd.Series
    if isinstance(cash_returns, (int, float)):
        cash_12m = pd.Series(
            (1.0 + float(cash_returns)) ** lookback - 1.0,
            index=monthly_prices.index,
        )
    else:
        log_cash = np.log1p(
            cash_returns.reindex(monthly_prices.index, fill_value=0.0)
        )
        cash_12m = np.expm1(
            log_cash.rolling(lookback, min_periods=lookback).sum()
        )

    # ── relative momentum mask: top_k per row ─────────────────────────────────
    # na_option="keep" → NaN ranks stay NaN → comparison yields False (warm-up safe)
    ranks: pd.DataFrame = mom.rank(
        axis=1, ascending=False, method="first", na_option="keep"
    )
    relative_mask: pd.DataFrame = ranks <= top_k

    # ── absolute momentum mask: asset return exceeds cash return ─────────────
    abs_mask: pd.DataFrame = mom.gt(cash_12m, axis=0)

    # ── combined selection and equal-weight allocation ────────────────────────
    selected: pd.DataFrame = relative_mask & abs_mask
    n_sel: pd.Series = selected.sum(axis=1)
    # Divide by n_sel; where n_sel == 0, use NaN so fillna(0) gives zero weight.
    risky_weights: pd.DataFrame = (
        selected.astype(float)
        .div(n_sel.where(n_sel > 0), axis=0)
        .fillna(0.0)
    )
    targets = risky_weights.copy()
    targets["CASH"] = 1.0 - risky_weights.sum(axis=1)
    return targets
