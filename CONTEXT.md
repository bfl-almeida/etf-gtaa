# CONTEXT.md — ETF GTAA Backtest

> Read this file before touching code. It defines what the project is, how it must
> be built, and what "done" means.

## Project goal

Replicate **Faber (2007), "A Quantitative Approach to Tactical Asset Allocation"** on
a 5-asset ETF universe and ship it as a clean Python package with tests, a CLI, and
a results notebook. After the baseline matches, extend with Antonacci (2014) dual
momentum.

## Why this project exists

This repo is a portfolio artifact for buy-side / ETF advisory quant interviews
(Kepler Cheuvreux ETF One, Amundi ETF, Lyxor, etc.). Two hard constraints:

1. **Code quality matters more than complexity.** A small, well-tested, well-documented
   package beats a sprawling notebook every time.
2. **Replicate first, innovate second.** The reviewer checks whether the numbers match
   the paper. Do not add features before the baseline matches within tolerance.

## Reference paper

Faber, M. T. (2007). *A Quantitative Approach to Tactical Asset Allocation.*
The Journal of Wealth Management, Spring 2007. SSRN: 962461.

**Key claim to reproduce:** a monthly timing rule on 5 asset classes — be invested
when the monthly close is above the 10-month simple moving average, hold cash
otherwise — delivers equity-like returns with materially lower drawdown than buy-and-hold.

The original paper uses indices (S&P 500, MSCI EAFE, GSCI, NAREIT, 10Y UST, T-bills
as cash). We use liquid ETFs as the modern, investable equivalent.

## Asset universe

| Asset class           | Primary ETF | Inception | Long-history fallback |
| --------------------- | ----------- | --------- | --------------------- |
| US equity             | VTI         | 2001-05   | SPY (1993-01)         |
| Developed ex-US       | VEU         | 2007-03   | EFA (2001-08)         |
| US REITs              | VNQ         | 2004-09   | IYR (2000-06)         |
| Broad commodities     | DBC         | 2006-02   | GSG (2006-07)         |
| US aggregate bonds    | BND         | 2007-04   | AGG (2003-09)         |
| Cash proxy            | BIL         | 2007-05   | (zero return option)  |

**Use the fallback set (SPY/EFA/IYR/GSG/AGG) for the replication run** so the sample
covers the 2008 drawdown — this is the key test of the timing rule.

## The Faber rule (exact specification)

For each ETF, at the close of each month-end trading day:

1. Compute the 10-month simple moving average of monthly closes, **including the
   current month**.
2. If `close > SMA_10` → target weight = 1/N for that sleeve (long).
3. If `close <= SMA_10` → that sleeve's weight goes to cash.
4. N = 5 (the number of risky sleeves). Equal-weighted across sleeves.
5. Apply position **at the next trading day's open** to avoid lookahead.
6. Rebalance only on month-end.

**Costs:** 0.1% one-way transaction cost on turnover (configurable, in basis points).

**Cash return:** monthly return of BIL when available, else 0 (configurable).

## Tech stack

- Python 3.11 or 3.12
- Package management: **Poetry 2.0+** (`pyproject.toml`, PEP 621 + Poetry groups)
- Env management: **mamba/conda** for env creation only — Poetry handles deps inside
- Core libs: pandas (>=2.2), numpy (<2 for yfinance compatibility), scipy, matplotlib, yfinance
- Tests: pytest + pytest-cov, no network calls in tests
- Lint: ruff
- Type check: mypy (strict)

## Repo layout

```
etf-gtaa/
├── CONTEXT.md              <- this file
├── README.md
├── pyproject.toml          <- Poetry config
├── environment.yml         <- mamba env (Python + Poetry only)
├── .gitignore
├── src/
│   └── etf_gtaa/
│       ├── __init__.py
│       ├── config.py       <- BacktestConfig dataclass
│       ├── data.py         <- yfinance loader + parquet cache + to_monthly
│       ├── signals.py      <- sma, faber_signal, equal_weight_targets
│       ├── backtest.py     <- run_backtest (vectorized)
│       ├── metrics.py      <- CAGR, vol, Sharpe, max DD, Calmar, hit ratio
│       └── cli.py          <- `etf-gtaa backtest ...`
├── tests/
│   ├── conftest.py         <- synthetic price fixtures
│   ├── test_data.py
│   ├── test_signals.py
│   ├── test_backtest.py
│   └── test_metrics.py
├── notebooks/
│   └── 01_faber_gtaa_replication.ipynb
└── data/                   <- parquet cache (gitignored except .gitkeep)
    └── .gitkeep
```

## Coding conventions

- **Type hints everywhere.** `mypy --strict` must pass on `src/`.
- Functions over classes unless persistent state is needed. The only dataclasses
  are `BacktestConfig` and `BacktestResult`.
- **Vectorized pandas / numpy.** No row-level Python loops in the backtest engine.
  If you find yourself writing `for i in range(len(df))`, stop and rethink.
- Pure functions in `signals.py` and `metrics.py`. I/O only in `data.py` and `cli.py`.
- All public functions have one-line summary + Args + Returns docstring (Google style).
- No magic numbers. Configuration via `BacktestConfig`.
- File paths via `pathlib`, never raw strings.

## Test policy

- One test file per source module.
- Each public function: at least one happy-path test + one edge-case test.
- Synthetic data fixtures in `conftest.py`, deterministic (seeded numpy RNG).
- **Do not call yfinance in tests.** The data layer is tested with monkeypatched
  return values.
- Coverage target: **>85% on `signals.py`, `backtest.py`, `metrics.py`**. Data layer
  may be lower.
- Critical invariant tests:
  - No-lookahead: mutating the last row of target weights must not change any
    earlier return in the backtest output.
  - All-cash backtest with constant cash return must reproduce that return exactly
    (modulo first-month application lag).
  - Equal-weight targets sum to 1.0 per row.

## Done criteria

### Phase 1 — Baseline replication

- [ ] `mamba env create -f environment.yml && poetry install --with dev` works on a clean machine
- [ ] `poetry run pytest` passes, coverage >85% on core modules
- [ ] `poetry run ruff check src tests` clean
- [ ] `poetry run mypy src` clean
- [ ] CLI: `poetry run etf-gtaa backtest --start 2003-09-01` prints a metrics table
- [ ] Notebook `01_faber_gtaa_replication.ipynb` shows:
  - Equity curve vs equal-weight buy-and-hold
  - Drawdown chart
  - Metrics table
  - One paragraph commenting on the 2008 result (this is the headline number)
- [ ] README quickstart works copy-paste

### Phase 2 — Extensions (only after Phase 1 is shipped)

- [ ] Add Antonacci dual momentum overlay (`signals.dual_momentum`)
- [ ] Walk-forward parameter sensitivity (SMA window: 6, 8, 10, 12 months) as a heatmap
- [ ] Optional: Sharpe with transaction cost grid (5–25 bps)

## Common commands

```bash
# One-time setup
mamba env create -f environment.yml
mamba activate etf-gtaa
poetry install --with dev

# Daily loop
poetry run pytest                          # tests + coverage
poetry run ruff check src tests            # lint
poetry run ruff format src tests           # auto-format
poetry run mypy src                        # type check

# Run the backtest
poetry run etf-gtaa backtest --start 2003-09-01 --end 2024-12-31
```

## What NOT to do

- Do not call `yfinance` from `signals.py`, `backtest.py`, or `metrics.py`. Data layer only.
- Do not add new strategies, signals, or assets until the baseline Faber result is
  reproduced and tested.
- Do not use `df.iterrows()`, `df.apply(axis=1)` with a heavy function, or any
  row-by-row Python loop in the engine.
- Do not skip docstrings or type hints "to ship faster". This repo's value IS the polish.
- Do not hardcode dates, paths, tickers, or costs. Everything goes in `BacktestConfig`.
- Do not commit `data/*.parquet`. The cache directory is gitignored except `.gitkeep`.
- Do not introduce a new dependency without justifying it in the PR description.

## Glossary (for a non-finance agent)

- **ETF (Exchange-Traded Fund):** a basket of securities (e.g. all S&P 500 stocks)
  that trades like a single stock. Used here as the building block.
- **SMA (Simple Moving Average):** average of the last N closes. The Faber rule
  uses N=10 on monthly data.
- **Drawdown:** drop from the running peak of the equity curve, expressed as a
  negative fraction. Max drawdown is the worst such drop in the sample.
- **Turnover:** sum of absolute weight changes between rebalances. Drives costs.
- **CAGR:** compound annual growth rate. `(NAV_end / NAV_start)^(1/years) - 1`.
- **Sharpe ratio:** `(mean return - risk-free) / stdev`, annualized by `sqrt(12)`
  for monthly returns.
- **No-lookahead:** the strategy at time `t` may only use data available at time
  `t`. Standard backtest correctness condition.
