# etf-gtaa

Replication of **Faber (2007)** and **Antonacci (2014)** on liquid US ETFs.
Three strategies compared across 5 asset classes (US equity, developed ex-US equity,
REITs, commodities, US aggregate bonds) with monthly rebalancing.

Built as a clean, tested Python package: vectorized backtest engine, CLI, and notebooks.

## Results (2007-06 → 2024-12, SPY/EFA/IYR/GSG/AGG, 10 bps cost, BIL cash proxy)

| Metric       | EW Buy & Hold | Faber GTAA | Dual Momentum |
|--------------|:-------------:|:----------:|:-------------:|
| CAGR         |    4.04 %     |   4.21 %   |    3.64 %     |
| Ann. Vol     |   13.43 %     |   6.60 %   |   12.10 %     |
| Sharpe       |    0.36       |   0.66     |    0.36       |
| Max Drawdown |  −47.51 %     | −12.65 %   |  −31.07 %     |
| Calmar       |    0.09       |   0.33     |    0.12       |
| Hit Ratio    |   61.90 %     |  64.29 %   |   64.29 %     |

**Key result:** Faber's CAGR is close to buy-and-hold, but with roughly half the volatility, about a quarter of the maximum drawdown, and a Sharpe of 0.66 vs 0.36.

Dual Momentum underperformed buy-and-hold over this window, with a −31 % drawdown. The cause is the universe size — five risky assets give the relative-momentum stage enough survivors that the absolute filter rarely pushes the whole book to cash (only 8.5 % of months). Canonical GEM uses two or three assets, so the cash filter bites harder. It is a design tradeoff between breadth and downside protection, not a broken filter. A narrower top-1 selection would tighten the cash filter — left as future work.

*All returns are net of transaction costs (10 bps one-way).*

> Full equity curves, drawdown charts, and sensitivity heatmaps (Sharpe / CAGR across
> SMA window × transaction cost grid) are in the notebooks:
> [`01_faber_gtaa_replication.ipynb`](notebooks/01_faber_gtaa_replication.ipynb) ·
> [`02_strategy_comparison.ipynb`](notebooks/02_strategy_comparison.ipynb)

## Quickstart

```bash
# 1. Create the env
mamba env create -f environment.yml
mamba activate etf-gtaa

# 2. Install the package and dev tools
poetry install --with dev

# 3. Run the test suite
poetry run pytest

# 4. Reproduce the results in the table above (fixed window)
poetry run etf-gtaa backtest --start 2007-06-01 --end 2024-12-31

# 5. Dual Momentum (same fixed window)
poetry run etf-gtaa backtest --start 2007-06-01 --end 2024-12-31 --strategy dual_momentum

# 6. Run to today (results will differ from the table)
poetry run etf-gtaa backtest --start 2007-06-01
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
