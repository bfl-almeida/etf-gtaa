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
    bt.add_argument("--start", type=date.fromisoformat, default=date(2007, 6, 1))
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
    bt.add_argument(
        "--strategy",
        choices=["faber", "dual_momentum"],
        default="faber",
        help="Timing strategy to run (default: faber).",
    )
    bt.add_argument("--top-k", type=int, default=2, help="Dual momentum: assets selected by relative ranking.")
    bt.add_argument("--momentum-lookback", type=int, default=12, help="Dual momentum: return lookback in months.")

    args = parser.parse_args()
    if args.cmd == "backtest":
        _run_backtest_cli(args)


def _run_backtest_cli(args: argparse.Namespace) -> None:
    """Execute the data → signal → backtest → metrics pipeline and print results."""
    from etf_gtaa.backtest import run_backtest
    from etf_gtaa.config import BacktestConfig
    from etf_gtaa.data import load_prices, to_monthly
    from etf_gtaa.metrics import summary
    from etf_gtaa.signals import dual_momentum, equal_weight_targets, faber_signal

    config = BacktestConfig(
        tickers=tuple(args.tickers),
        cash_ticker=args.cash_ticker,
        start=args.start,
        end=args.end,
        sma_window=args.sma_window,
        transaction_cost_bps=args.cost_bps,
        initial_capital=args.initial_capital,
        top_k=args.top_k,
        momentum_lookback=args.momentum_lookback,
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

    if args.strategy == "faber":
        signal = faber_signal(risky, window=config.sma_window)
        targets = equal_weight_targets(signal)
        strategy_label = "Faber GTAA"
    else:
        targets = dual_momentum(
            risky,
            lookback=config.momentum_lookback,
            top_k=config.top_k,
            cash_returns=cash_return,
        )
        strategy_label = "Dual Momentum"

    result = run_backtest(
        risky,
        targets,
        cash_return=cash_return,
        transaction_cost_bps=config.transaction_cost_bps,
        initial_capital=config.initial_capital,
    )

    # Equal-weight buy-and-hold benchmark: always 1/N in each risky ticker, no timing.
    n_risky = len(config.tickers)
    bnh_weights = pd.DataFrame(
        1.0 / n_risky,
        index=risky.index,
        columns=list(config.tickers),
    )
    bnh_weights["CASH"] = 0.0
    bnh_result = run_backtest(
        risky,
        bnh_weights,
        cash_return=0.0,
        transaction_cost_bps=config.transaction_cost_bps,
        initial_capital=config.initial_capital,
    )

    table = pd.DataFrame(
        {
            strategy_label: summary(result.monthly_returns, result.equity_curve),
            "EW Buy & Hold": summary(bnh_result.monthly_returns, bnh_result.equity_curve),
        }
    )
    print(table.to_string(float_format="{:.4f}".format))

    # ── Diagnostics ───────────────────────────────────────────────────────────
    # Average cash weight across the periods actually used by the backtest.
    avg_cash_pct = targets["CASH"].iloc[:-1].mean() * 100
    cash_source = (
        config.cash_ticker
        if config.cash_ticker is not None and isinstance(cash_return, pd.Series)
        else "fallback (0%)"
    )
    total_to_strategy = result.turnover.sum()
    total_to_bnh = bnh_result.turnover.sum()

    print("\nDiagnostics")
    print(f"  % months w/ cash sleeve : {avg_cash_pct:.1f}% avg cash weight")
    print(f"  Cash return source      : {cash_source}")
    print(
        f"  Total one-way turnover  : "
        f"{total_to_strategy:.2f}x ({strategy_label}) | {total_to_bnh:.2f}x (EW Buy & Hold)"
    )

