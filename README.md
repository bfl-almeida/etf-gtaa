# etf-gtaa

Replication of **Faber (2007), *A Quantitative Approach to Tactical Asset Allocation***
on liquid US ETFs. A 10-month simple moving average timing rule across 5 asset classes
(US equity, developed ex-US equity, REITs, commodities, US aggregate bonds), with
equal weights and monthly rebalancing.

Built as a clean, tested Python package: vectorized backtest, CLI, notebook results.

## Quickstart

```bash
# 1. Create the env (Python + Poetry only)
mamba env create -f environment.yml
mamba activate etf-gtaa

# 2. Install the package and dev tools
poetry install --with dev

# 3. Run the test suite
poetry run pytest

# 4. Run the baseline backtest
poetry run etf-gtaa backtest --start 2003-09-01
```

## What's in the repo

```
src/etf_gtaa/
  data.py        yfinance loader + parquet cache + month-end resampling
  signals.py     Faber 10-month SMA rule + equal-weight target builder
  backtest.py    Vectorized monthly backtest engine (no-lookahead)
  metrics.py     CAGR / annualized vol / Sharpe / max DD / Calmar / hit ratio
  cli.py         `etf-gtaa backtest` entry point
  config.py      BacktestConfig dataclass

tests/           pytest, no network calls (synthetic fixtures)
notebooks/       01_faber_gtaa_replication.ipynb — equity curves and headline metrics
```

## Development

```bash
poetry run pytest                  # tests + coverage
poetry run ruff check src tests    # lint
poetry run ruff format src tests   # format
poetry run mypy src                # type check (strict)
```

## Reference

Faber, M. T. (2007). *A Quantitative Approach to Tactical Asset Allocation.*
The Journal of Wealth Management, Spring 2007. SSRN: 962461.

## Roadmap

- [x] Project scaffold, CONTEXT, tests skeleton
- [ ] Phase 1 — baseline Faber replication
- [ ] Phase 2 — Antonacci (2014) dual momentum overlay
- [ ] Phase 2 — walk-forward parameter sensitivity
