"""Faber (2007) timing signal and equal-weight target builder.

Pure functions: no I/O, no side effects.
"""

from __future__ import annotations

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
