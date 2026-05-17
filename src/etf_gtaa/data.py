"""Data loading: yfinance with parquet cache, daily-to-monthly resampling.

All I/O lives here. Other modules must never call yfinance directly.
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pandas as pd

CACHE_DIR = Path(__file__).resolve().parents[2] / "data"


def _assert_no_nan(prices: pd.DataFrame, start: date) -> None:
    """Raise ValueError if any column still contains NaN after forward-fill.

    After ffill, only leading NaN (before a ticker's inception) can remain.
    Any such gap means the requested start date predates that ticker's data.

    Args:
        prices: price DataFrame returned by the loader.
        start: the requested start date, used in the error message.
    """
    nan_cols = [str(c) for c in prices.columns if prices[c].isna().any()]
    if nan_cols:
        details = "; ".join(
            f"{c} first trades {prices[c].first_valid_index().date()}"
            for c in nan_cols
        )
        raise ValueError(
            f"Prices contain NaN from {start} for: {details}. "
            "Use a later start date or swap to a fallback ticker."
        )


def load_prices(
    tickers: list[str],
    start: date,
    end: date | None = None,
    use_cache: bool = True,
) -> pd.DataFrame:
    """Load adjusted close prices for the given tickers.

    Reads from / writes to a parquet cache under ``data/`` to avoid re-hitting
    yfinance on every run.

    Args:
        tickers: ticker symbols (e.g. ["SPY", "EFA"]).
        start: start date, inclusive.
        end: end date, inclusive. None means today.
        use_cache: when True, read cached parquet if present and write the
            result back to cache after download.

    Returns:
        DataFrame with a DatetimeIndex (business days, ascending), columns
        equal to ``tickers`` (in input order), values = adjusted close prices.
        Missing dates are forward-filled within available history.
    """
    end_date = end if end is not None else date.today()

    ticker_key = "_".join(sorted(tickers))
    cache_path = CACHE_DIR / f"{ticker_key}_{start}_{end_date}.parquet"

    if use_cache and cache_path.exists():
        prices: pd.DataFrame = pd.read_parquet(cache_path)[tickers]
    else:
        import yfinance as yf  # local import: keeps I/O out of the engine modules

        # yfinance end is exclusive — add one day to include end_date
        raw = yf.download(
            tickers,
            start=str(start),
            end=str(end_date + timedelta(days=1)),
            auto_adjust=True,
            progress=False,
        )

        if isinstance(raw.columns, pd.MultiIndex):
            prices = raw["Close"]
            if isinstance(prices, pd.Series):
                prices = prices.to_frame(name=tickers[0])
            else:
                prices = prices[list(tickers)]
        else:
            prices = raw[["Close"]].rename(columns={"Close": tickers[0]})

        prices = prices.ffill()

        if use_cache:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            prices.to_parquet(cache_path)

    _assert_no_nan(prices, start)
    return prices[tickers]


def to_monthly(daily_prices: pd.DataFrame) -> pd.DataFrame:
    """Resample daily prices to month-end closes.

    Args:
        daily_prices: business-day-indexed price DataFrame.

    Returns:
        Month-end-indexed DataFrame with the last available close in each month.
    """
    return daily_prices.resample("ME").last()
