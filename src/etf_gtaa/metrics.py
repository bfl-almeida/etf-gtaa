"""Performance metrics for monthly return / equity-curve series.

All functions assume monthly periodicity unless ``periods_per_year`` is overridden.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def cagr(returns: pd.Series, periods_per_year: int = 12) -> float:
    """Compound annual growth rate from a periodic return series.

    Args:
        returns: periodic return series (e.g. monthly).
        periods_per_year: number of periods per year (12 for monthly data).

    Returns:
        CAGR as a decimal (e.g. 0.07 means 7%).
    """
    n = len(returns)
    total_growth = float((1.0 + returns).prod())
    years = n / periods_per_year
    return float(total_growth ** (1.0 / years) - 1.0)


def annualized_vol(returns: pd.Series, periods_per_year: int = 12) -> float:
    """Annualized standard deviation of returns.

    Args:
        returns: periodic return series.
        periods_per_year: number of periods per year.

    Returns:
        Annualized volatility as a decimal.
    """
    return float(returns.std() * np.sqrt(periods_per_year))


def sharpe(
    returns: pd.Series,
    rf: float = 0.0,
    periods_per_year: int = 12,
) -> float:
    """Annualized Sharpe ratio.

    Computed as ``mean(returns - rf_per_period) / std(returns)`` scaled by
    ``sqrt(periods_per_year)``. ``rf`` is the annualized risk-free rate.

    Args:
        returns: periodic return series.
        rf: annualized risk-free rate.
        periods_per_year: number of periods per year.

    Returns:
        Annualized Sharpe ratio, or 0.0 when standard deviation is zero.
    """
    rf_per_period = (1.0 + rf) ** (1.0 / periods_per_year) - 1.0
    excess = returns - rf_per_period
    std = float(returns.std())
    if std == 0.0:
        return 0.0
    return float(excess.mean() / std * np.sqrt(periods_per_year))


def max_drawdown(equity_curve: pd.Series) -> float:
    """Maximum peak-to-trough drawdown as a negative fraction.

    Args:
        equity_curve: portfolio NAV series (any positive-valued index).

    Returns:
        Most negative drawdown observed (e.g. -0.30 for a 30% drawdown).
    """
    rolling_peak = equity_curve.cummax()
    drawdown = (equity_curve - rolling_peak) / rolling_peak
    return float(drawdown.min())


def calmar(returns: pd.Series, equity_curve: pd.Series) -> float:
    """CAGR divided by the absolute value of max drawdown.

    Args:
        returns: periodic return series.
        equity_curve: portfolio NAV series aligned with ``returns``.

    Returns:
        Calmar ratio (positive when CAGR > 0 and drawdown != 0).
    """
    mdd = max_drawdown(equity_curve)
    if mdd == 0.0:
        return float("inf")
    return cagr(returns) / abs(mdd)


def hit_ratio(returns: pd.Series) -> float:
    """Fraction of strictly positive return periods.

    Args:
        returns: periodic return series.

    Returns:
        Hit ratio in [0, 1].
    """
    return float((returns > 0).mean())


def summary(returns: pd.Series, equity_curve: pd.Series) -> pd.Series:
    """Labeled Series with CAGR, vol, Sharpe, max DD, Calmar, hit ratio.

    Args:
        returns: periodic return series.
        equity_curve: portfolio NAV series.

    Returns:
        Named Series of performance statistics.
    """
    return pd.Series(
        {
            "CAGR": cagr(returns),
            "Vol": annualized_vol(returns),
            "Sharpe": sharpe(returns),
            "Max Drawdown": max_drawdown(equity_curve),
            "Calmar": calmar(returns, equity_curve),
            "Hit Ratio": hit_ratio(returns),
        }
    )
