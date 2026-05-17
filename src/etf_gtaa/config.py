"""Configuration for the backtest."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class BacktestConfig:
    """Static configuration for one Faber / dual-momentum backtest run.

    Attributes:
        tickers: risky ETF tickers, equal-weighted when in-market.
        cash_ticker: ETF used as cash proxy (e.g. BIL); None means flat 0% cash.
        start: backtest start date (inclusive).
        end: backtest end date (inclusive); None means "today". Default pins to
            2024-12-31 for reproducibility — override to run live.
        sma_window: lookback for the Faber SMA signal, in months.
        transaction_cost_bps: one-way transaction cost in basis points (10 = 0.10%).
        initial_capital: starting NAV in account currency.
        top_k: number of ETFs selected by relative momentum before the absolute
            filter (dual momentum only).
        momentum_lookback: return lookback in months for dual momentum (Antonacci
            uses 12).
    """

    tickers: tuple[str, ...] = ("SPY", "EFA", "IYR", "GSG", "AGG")
    cash_ticker: str | None = "BIL"
    start: date = date(2007, 6, 1)
    end: date | None = date(2024, 12, 31)
    sma_window: int = 10
    transaction_cost_bps: float = 10.0
    initial_capital: float = 100_000.0
    top_k: int = 2
    momentum_lookback: int = 12
