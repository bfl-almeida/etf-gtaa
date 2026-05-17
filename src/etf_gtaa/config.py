"""Configuration for the backtest."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class BacktestConfig:
    """Static configuration for one Faber GTAA backtest run.

    Attributes:
        tickers: risky ETF tickers, equal-weighted when in-market.
        cash_ticker: ETF used as cash proxy (e.g. BIL); None means flat 0% cash.
        start: backtest start date (inclusive).
        end: backtest end date (inclusive); None means "today".
        sma_window: lookback for the simple moving average, in months.
        transaction_cost_bps: one-way transaction cost in basis points (10 = 0.10%).
        initial_capital: starting NAV in account currency.
    """

    tickers: tuple[str, ...] = ("SPY", "EFA", "IYR", "GSG", "AGG")
    cash_ticker: str | None = "BIL"
    start: date = date(2007, 6, 1)
    end: date | None = None
    sma_window: int = 10
    transaction_cost_bps: float = 10.0
    initial_capital: float = 100_000.0
