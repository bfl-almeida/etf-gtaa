"""Command-line entry point: ``etf-gtaa backtest ...``.

Wires the data → signals → backtest → metrics pipeline together. The only
side-effecting module besides ``data.py``.
"""

from __future__ import annotations

import argparse
from datetime import date

import pandas as pd


def main() -> None:
    """Console entry point declared in pyproject.toml ([project.scripts])."""
    parser = argparse.ArgumentParser(
        prog="etf-gtaa",
        description="Faber (2007) GTAA backtest on ETFs.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    bt = sub.add_parser("backtest", help="Run the baseline Faber backtest.")
    bt.add_argument("--start", type=date.fromisoformat, default=date(2003, 9, 1))
    bt.add_argument("--end", type=date.fromisoformat, default=None)
    bt.add_argument(
        "--tickers",
        nargs="+",
        default=["SPY", "EFA", "IYR", "GSG", "AGG"],
        help="Risky ETF tickers (equal-weight when in-market).",
    )
    bt.add_argument("--cash-ticker", default="BIL")
    bt.add_argument("--sma-window", type=int, default=10)
    bt.add_argument("--cost-bps", type=float, default=10.0)
    bt.add_argument("--initial-capital", type=float, default=100_000.0)

    args = parser.parse_args()
    if args.cmd == "backtest":
        _run_backtest_cli(args)


def _run_backtest_cli(args: argparse.Namespace) -> None:
    """Execute the data → signal → backtest → metrics pipeline and print results."""
    from etf_gtaa.backtest import run_backtest
    from etf_gtaa.config import BacktestConfig
    from etf_gtaa.data import load_prices, to_monthly
    from etf_gtaa.metrics import summary
    from etf_gtaa.signals import equal_weight_targets, faber_signal

    config = BacktestConfig(
        tickers=tuple(args.tickers),
        cash_ticker=args.cash_ticker,
        start=args.start,
        end=args.end,
        sma_window=args.sma_window,
        transaction_cost_bps=args.cost_bps,
        initial_capital=args.initial_capital,
    )

    all_tickers = list(config.tickers)
    if config.cash_ticker is not None:
        all_tickers.append(config.cash_ticker)

    daily = load_prices(all_tickers, config.start, config.end)
    monthly = to_monthly(daily)

    risky = monthly[list(config.tickers)]

    cash_return: float | pd.Series
    if config.cash_ticker is not None and config.cash_ticker in monthly.columns:
        cash_return = monthly[config.cash_ticker].pct_change()
    else:
        cash_return = 0.0

    signal = faber_signal(risky, window=config.sma_window)
    targets = equal_weight_targets(signal)

    result = run_backtest(
        risky,
        targets,
        cash_return=cash_return,
        transaction_cost_bps=config.transaction_cost_bps,
        initial_capital=config.initial_capital,
    )

    metrics = summary(result.monthly_returns, result.equity_curve)
    print(metrics.to_string())

