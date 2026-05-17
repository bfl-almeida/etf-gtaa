# etf-gtaa

Replication of **Faber (2007)** and **Antonacci (2014)** on liquid US ETFs.
Three strategies compared across 5 asset classes (US equity, developed ex-US equity,
REITs, commodities, US aggregate bonds) with monthly rebalancing.

Built as a clean, tested Python package: vectorized backtest engine, CLI, and notebooks.

## Results (2007-06 → 2024-12, SPY/EFA/IYR/GSG/AGG, 10 bps cost, BIL cash proxy)

| Metric        | EW Buy & Hold | Faber GTAA | Dual Momentum |
|---------------|:-------------:|:----------:|:-------------:|
| CAGR          | —             | —          | —             |
| Ann. Vol      | —             | —          | —             |
| Sharpe        | —             | —          | —             |
| Max Drawdown  | —             | —          | —             |
| Calmar        | —             | —          | —             |
| Hit Ratio     | —             | —          | —             |

> Run `poetry run etf-gtaa backtest --start 2007-06-01` to populate the table above,
> or open `notebooks/01_faber_gtaa_replication.ipynb` for equity curves and drawdown
> charts, and `notebooks/02_strategy_comparison.ipynb` for the 3-way comparison and
> sensitivity heatmaps (Sharpe / CAGR across SMA window × transaction cost grid).

## Quickstart

```bash
# 1. Create the env
mamba env create -f environment.yml
mamba activate etf-gtaa

# 2. Install the package and dev tools
poetry install --with dev

# 3. Run the test suite
poetry run pytest

# 4. Faber GTAA vs equal-weight benchmark
poetry run etf-gtaa backtest --start 2007-06-01

# 5. Dual Momentum strategy
poetry run etf-gtaa backtest --start 2007-06-01 --strategy dual_momentum
```

## What's in the repo

```
src/etf_gtaa/
  data.py        yfinance loader + parquet cache + month-end resampling
  signals.py     Faber SMA rule, equal-weight targets, dual momentum
  backtest.py    Vectorized monthly backtest engine (no-lookahead)
  metrics.py     CAGR / Vol / Sharpe / Max DD / Calmar / Hit Ratio
  analysis.py    Sensitivity grid (SMA window × transaction cost)
  cli.py         `etf-gtaa backtest` entry point
  config.py      BacktestConfig dataclass

tests/           24 pytest tests, no network calls (synthetic fixtures)
notebooks/
  01_faber_gtaa_replication.ipynb   Faber vs EW B&H — equity curves, drawdowns
  02_strategy_comparison.ipynb      3-way comparison + sensitivity heatmaps
```

## Development

```bash
poetry run pytest                  # tests + coverage
poetry run ruff check src tests    # lint
poetry run ruff format src tests   # format
poetry run mypy src                # type check (strict)
```

## References

Faber, M. T. (2007). *A Quantitative Approach to Tactical Asset Allocation.*
The Journal of Wealth Management, Spring 2007. SSRN: 962461.

Antonacci, G. (2014). *Dual Momentum Investing.* McGraw-Hill.

## Roadmap

- [x] Project scaffold, CONTEXT, tests skeleton
- [x] Phase 1 — baseline Faber replication (tagged `v0.1.0`)
- [x] Phase 2A — Antonacci (2014) dual momentum overlay
- [x] Phase 2B — sensitivity / robustness analysis + notebooks (tagged `v0.2.0`)
