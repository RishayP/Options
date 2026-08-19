# Principles

**An operational playbook for building a portfolio of tested, mechanically-tradeable options setups.**

## Contents

| § | Section | What it gives you |
|---|---|---|
| **0** | [The Destination and the Doctrine](#0-the-destination-and-the-doctrine) | Definition of done, the funnel, the seven rules everything else implements |
| **1** | [Data & Repository Infrastructure](#1-data--repository-infrastructure) | Repo layout, data layers, vendor comparison, the data-quality checklist that decides whether results are real |
| **2** | [Hypothesis Generation & Pre-Registration](#2-hypothesis-generation--pre-registration) | Where ideas come from, the YAML spec schema, hash-enforced pre-registration, the triage rubric |
| **3** | [Stage 1 — Testing the Underlying Premise](#3-stage-1--testing-the-underlying-premise-no-options-yet) | Event-study method, lookahead-bias catalogue, splits, statistics, hard pass/fail gates |
| **4** | [The Anti-Overfitting Protocol](#4-the-anti-overfitting-protocol) | Trial accounting, multiplicity corrections, PBO, parameter plateaus, adversarial tests, the story test |
| **5** | [Translating a Premise into an Options Structure](#5-translating-a-validated-premise-into-an-options-structure) | Move/premium ratio, structure selection matrix, strikes, expiry, the Greek budget |
| **6** | [Stage 2 — Backtesting the Options-Wrapped Strategy](#6-stage-2--backtesting-the-options-wrapped-strategy) | Engine design, honest fill modeling, fees, lifecycle edge cases, margin, liquidity filters |
| **7** | [Evaluation — What "Proven" Actually Means](#7-evaluation--what-proven-actually-means) | Metric set, distribution and concentration diagnostics, benchmarking, the promotion gauntlet, the sealed-holdout exam |
| **8** | [Portfolio Construction](#8-portfolio-construction--running-several-setups-together) | Aggregate Greek book, hidden correlation, sizing, risk budgeting, stress grid |
| **9** | [From Proven Hypothesis to Live Trading](#9-from-proven-hypothesis-to-live-trading) | Scanner, paper protocol, execution playbook, journal, reconciliation, kill switches |
| **10** | [The Candidate Library](#10-the-candidate-library) | Pointer to `Hypotheses.md` — the candidate inventory, kept separate because it churns |
| **11** | [The Build Order](#11-the-build-order--sequenced-roadmap) | Phase map, first two weeks, definition of done, the ten failure modes |

---

## 0. The Destination and the Doctrine

### 0.1 What "done" looks like

This repo is finished when it contains **at least one — preferably three to five — hypotheses that satisfy every clause below**:

1. **Mechanically specified.** The trigger is a function of point-in-time data that returns `True`/`False` with no human judgment. Two different people running it on the same data get the same signal dates.
2. **Economically justified.** A written answer to *who is on the other side of this trade and why they are willing to lose to me* — a risk premium being paid, a structural constraint forcing someone to transact, or a flow that must happen regardless of price.
3. **Statistically survived.** It passed a pre-registered stage-1 test on the underlying, an adversarial anti-overfitting gauntlet, an options-wrapped backtest with pessimistic fills, and a one-shot sealed-holdout exam.
4. **Structurally expressed.** A specific options structure — legs, strike deltas, expiry rule, size — chosen because its dominant Greek is the one the edge actually lives in.
5. **Risk-bounded.** Known max loss, known worst-case stressed loss, a position size derived from that loss and the account, and pre-registered kill-switch thresholds.
6. **Operationally live.** A daily scanner that fires the alert, an entry checklist, a mechanical exit rule, a journal that records every trade, and a monthly test of live results against the backtest distribution.

A hypothesis missing **any** of these is not a strategy. It is a backtest.

### 0.2 The funnel

The entire process is a filter with a brutal survival rate. Plan for it, and do not become attached to any single idea:

| Stage | Count | What kills things here |
|---|---|---|
| Raw ideas brainstormed | ~40 | Vague, unmeasurable, no mechanism |
| Survive sample/viability pre-flight (§2.9) | ~20 | Too few independent clusters; effect too small to clear a spread; "trigger" fires most days |
| Written to formal spec | ~12 | Can't be computed point-in-time; no falsification condition |
| Pass stage-1 (underlying only) | ~4 | No effect vs unconditional baseline; effect is noise |
| Pass anti-overfitting gauntlet | ~2–3 | Parameter spike, one-year wonder, dies to costs |
| Pass stage-2 (options-wrapped) | ~1–2 | Spread and theta eat the edge |
| Reach live trading | **1–2** | Holdout failure |

**40 in, 1–2 out.** If your funnel is producing a higher survival rate, your tests are too weak, not your ideas too good.

### 0.3 The seven doctrines

Everything downstream in this document is an implementation of these. When a procedure and a doctrine conflict, the doctrine wins.

**I. The spec precedes the data.** Write the hypothesis down — trigger, outcome, predicted direction, falsification condition — and commit it *before* running the backtest. Adjusting the definition after seeing the result is not research; it is fitting, and it is undetectable after the fact unless you have the timestamp.

**II. Conditional versus unconditional, never versus zero.** "SPY goes up after my signal" is meaningless: SPY goes up anyway. The only question is whether the conditional distribution differs from the unconditional one by more than sampling noise.

**III. No mechanism, no trade.** A statistically beautiful result with no story about who is paying you is far more likely to be a survivor of your own search than a real anomaly. The story test is a hard gate, not a nicety.

**III½. Count the sample before you write the spec.** Independent events, not rows, are what every statistic spends. A trigger describing a persistent state collapses 10–20× from raw events to independent observations, and the check costs minutes with no outcome data. Candidates die here for free that would otherwise consume weeks. See §2.9.

**IV. Count your trials, honestly.** Every backtest you ever run — including the ones you abandoned after ten seconds — inflates the best result you will find. The single most common way a solo researcher destroys themselves is quietly not counting.

**V. Costs are part of the hypothesis.** In options, the bid/ask spread is frequently larger than the entire edge. An edge is only real if it survives pessimistic fills, commissions, and fees — and you must know the cost multiple at which it dies.

**VI. Stage 1 and stage 2 are separate falsification tests.** A validated view on the underlying gives you *no* license to assume the option expression works. Theta, vega, and spread can turn a real directional edge into a losing strategy.

**VII. The sealed holdout is sacred.** One look, ever, per hypothesis. If you look twice, it is no longer a holdout — it is a second in-sample period, and you have lost your only unbiased estimate of what happens next.

### 0.4 How to read this document

Sections 1–2 build the machinery and the ideas. Sections 3–4 are the statistical core — where you learn not to fool yourself, and where most candidates die. Sections 5–6 convert a validated premise into an options position and test it honestly. Sections 7–8 define what "proven" means numerically and how to run several setups without secretly holding one giant position. Section 9 is the live last mile. Section 10 points to `Hypotheses.md`, the candidate inventory, which lives in its own file because it changes constantly while the method should not. Section 11 is the sequenced build order.

Read 0, 2, 3, and 4 before writing any code. They are the ones that determine whether the other seven sections produce anything real.

---

## 1. Data & Repository Infrastructure

### 1.1 Repository layout

```
options/
├── Makefile                     # make data | make validate | make backtest | make scan
├── pyproject.toml               # pinned deps (uv or poetry), single source of truth
├── uv.lock                      # or poetry.lock — committed, never gitignored
├── conf/
│   ├── universe.yaml            # tickers, listing/delisting dates, sector tags
│   └── settings.yaml            # data root path, vendor keys via env var NAMES only
├── specs/                       # HYPOTHESIS SPECS — version controlled, no code
│   ├── h001_vix9d_vix_inversion.yaml
│   ├── h002_post_earnings_ivcrush.yaml
│   └── schema/spec.schema.json  # jsonschema; CI validates every spec against it
├── data/                        # gitignored entirely
│   ├── raw/                     # immutable vendor payloads, exactly as downloaded
│   │   └── polygon/options_chain/SPY/2024-03-15.json.gz
│   ├── curated/                 # parquet, partitioned, canonical schema
│   │   ├── ohlcv_daily/symbol=SPY/year=2024/part.parquet
│   │   ├── options_quotes/symbol=SPY/date=2024-03-15/part.parquet
│   │   └── vol_indices/part.parquet
│   ├── manifests/               # one JSON per ingest run (see 1.6)
│   └── cache/                   # loader-level memoized derived frames
├── src/optlab/
│   ├── ingest/                  # one module per vendor: yf.py, polygon.py, cboe.py
│   ├── validate/                # assertions run on every ingest
│   ├── io/loader.py             # the ONLY way anything reads data
│   ├── specs/                   # spec parsing, hashing, resolution
│   ├── engine/                  # signal eval, structure builder, fill model, PnL
│   ├── stats/                   # bootstrap, multiple-testing, walk-forward
│   └── scan/                    # live scanner: same spec objects, today's data
├── results/                     # gitignored except results/index.jsonl
│   └── <spec_hash>/
│       ├── spec_snapshot.yaml   # byte copy of the spec that ran
│       ├── manifest_ref.json    # data manifest hashes used
│       ├── trades.parquet
│       ├── stats.json
│       └── env.json             # python + package versions, git sha, seeds
├── notebooks/                   # exploration ONLY; may import src, never define logic
└── tests/
```

**Why specs are YAML, not Python.** A hypothesis is data: entry condition, universe, structure, holding rule, exit. If it lives in code, you cannot diff two variants cleanly, you cannot enumerate the search space you tested (which you need for multiple-testing correction), and you cannot hash it. Keeping it declarative forces you to count every variant you tried — the single biggest defense against fooling yourself. Code interprets specs; code contains no thresholds.

```yaml
# specs/h001_vix9d_vix_inversion.yaml
id: h001
universe: {file: conf/universe.yaml, group: liquid_etf}
entry:
  all:
    - {field: vix9d_vix_ratio, op: ">", value: 1.05}
    - {field: dte_to_next_fomc, op: ">", value: 5}
structure: {type: put_debit_spread, dte_target: 30, short_delta: -0.20, width_pct: 0.05}
exit: {rules: [{type: time, days_held: 10}, {type: pnl_pct, take: 0.5, stop: -1.0}]}
costs: {fill: mid_minus_edge, edge_frac_of_spread: 0.25}
```

**Why results are content-addressed by spec hash.** `spec_hash = sha256(canonical_json(spec))` — sort keys, normalize numbers, exclude comments/`description`. Results write to `results/<spec_hash>/`. Consequences: editing a threshold produces a new directory rather than overwriting, so a result can never silently belong to a spec that no longer exists; a run whose hash directory already exists is skipped or must be `--force`d; `results/index.jsonl` (one line per run: hash, spec id, date, headline stats, git sha) is committed, giving you a permanent, greppable record of every variant tested — the denominator for your false-discovery correction.

### 1.2 Data layers, in acquisition order

Acquire in this order; each layer must pass validation before you buy the next. Do not buy options chains until layers a–d have produced 2–3 hypotheses with signal.

| # | Layer | Why now | Cheapest viable source |
|---|---|---|---|
| a | Daily OHLCV + volume, unadjusted + adjustment factors | Universe construction, realized vol, all signal features | yfinance / Stooq (\$0) |
| b | Intraday bars (1m/5m) | Entry timing, opening-range and gap studies, drift within holding window | Polygon Starter, Databento, Alpaca (\$0–\$30/mo) |
| c | VIX, VIX9D, VIX3M, VIX6M, VVIX, term-structure ratios | Most durable regime conditioner; free and deep | CBOE website CSVs (\$0, history to 1990s/2007+ by index) |
| d | **IV history without chains** | Lets you test 80% of vol hypotheses before paying for chains | See below |
| e | Full historical chains: bid/ask/OI/volume/greeks per strike | Only stage where structure PnL is real | ORATS / Polygon Options / IVolatility ($$) |
| f | Event calendars: earnings, FOMC, CPI, OPEX, dividends, splits | Conditioning variable *and* a data-integrity necessity | Mixed, see 1.3 |

**(d) The cheap-IV-history trick, in priority order:**
1. **CBOE volatility indices as underlying-specific IV proxies.** VIX (SPX 30d), VXN (NDX), RVX (RUT), VXAPL/VXAZN/VXGS-style single-name indices where still published, OVX (oil), GVZ (gold), EVZ (FX). Free daily history from cboe.com. These *are* 30-day constant-maturity IV.
2. **VIX term structure** from CBOE futures settlement files (free daily CSVs per contract) — gives you contango/backwardation, a stronger conditioner than VIX level.
3. **ETF-proxy realized-vs-implied**: compute realized vol yourself (Yang-Zhang or Garman-Klass from OHLC) and pair with the index IV above to get a variance-risk-premium series with \$0 spend.
4. **Free/cheap IV-summary datasets**: ORATS sells a *summary* file (per-symbol daily IV30/IV60, skew, VRP) far cheaper than full chains — buy this before full chains. DoltHub `post-no-preference/options` has historical chain snapshots for free; treat as exploratory only.
5. **Current-chain accumulation**: start a daily cron on day one that snapshots free chains (yfinance `Ticker.option_chain`, or Tradier sandbox) at a fixed time and appends to parquet. This is worthless today and priceless in nine months. Cost: zero. Start it before anything else.

**(f) Event calendars.** Earnings dates: yfinance `Ticker.get_earnings_dates()` is *not* point-in-time and revises silently — for anything serious use a dated vendor feed or maintain your own append-only log with `as_of` stamps. FOMC/CPI: hardcode from the Fed and BLS published calendars into `conf/events/` (a few dozen rows a year; do it by hand, it is correct forever). OPEX: derive, don't fetch — third Friday, plus weeklies/EOM; use `pandas_market_calendars` for the trading-day grid and holiday shifts. Dividends/splits: yfinance `Ticker.actions`, cross-checked against price-jump detection.

### 1.3 Vendor comparison

| Vendor | What you get | Granularity | History | Cost (as of writing, verify) | Gotchas / verdict |
|---|---|---|---|---|---|
| **yfinance** | Equity/ETF OHLCV, actions, *current* option chain | Daily; 1m for ~30d | Decades daily | \$0 | Unofficial scrape, rate-limited, breaks on Yahoo changes, adjusted-only quirks, survivorship-biased (delisted tickers gone), no options history. **Use: prototyping + daily chain snapshotting.** |
| **Stooq** | OHLCV CSV, global | Daily | Long | \$0 | Good redundancy source to cross-check yfinance. No options. |
| **Alpha Vantage** | OHLCV, some indicators, limited options | Daily/intraday | Moderate | Free tier heavily rate-limited; paid tiers exist | Throttling makes bulk ingest painful. **Trap for anything bulk.** |
| **Polygon.io — Stocks** | Trades, quotes, aggregates, splits/divs, tickers incl. delisted | Tick → daily | ~15–20y aggs | Paid tiers, low-hundreds/mo at the high end | Genuinely good, well-documented REST + flat files. Delisted-ticker endpoint fixes survivorship. |
| **Polygon.io — Options** | Historical option aggregates, trades, quotes, snapshots | Tick → daily | Several years | Separate options subscription | Real option data at a solo-quant price point. Check whether *your* tier includes historical quotes vs trades only — trades-only cannot price a spread. |
| **Databento** | Raw exchange feeds incl. OPRA | MBO/MBP/tick | Vendor-dependent | Usage-based, pay-per-GB | Highest fidelity available to individuals. OPRA is enormous — a single day of full options quotes is many GB. Budget-blowing if you query carelessly. Use for targeted symbol/date pulls. |
| **CBOE DataShop** | Official EOD option quotes, open/close, greeks, VIX complex | EOD + intraday snapshots | Deep (2000s+) | Per-dataset purchase; à-la-carte can be reasonable for one symbol | Authoritative for SPX/VIX. Buy narrow: one underlying, the years you need. Free VIX-family indices and futures settlements are the best zero-cost data in this whole table. |
| **ORATS** | Option chains, greeks, IV surface, **daily summary** (IV30/60/90, skew, earnings-adjusted vol) | Daily (intraday available) | ~2007+ | Subscription; summary tier much cheaper than full chains | The pragmatic buy for a solo quant. Their vol-surface fitting saves months. Verify what's in your tier. |
| **IVolatility** | IV surfaces, historical chains, greeks | Daily | Deep | Per-dataset, quote-based | Priced for institutions; one-off historical extracts can be affordable. Get a quote before assuming. |
| **Tradier** | Brokerage API: live chains, greeks, some history | Live/intraday | Shallow | Cheap/free with account; sandbox free | Excellent for *forward* collection and live scanning. Not a backtest source. |
| **IBKR** | Live + limited historical bars, option chains | Intraday | Limited by pacing rules | Account required | Harsh pacing limits; not a bulk historical source. Fine as execution + live quotes. |
| **DoltHub / free options datasets** | Community-collected historical chain snapshots | Daily EOD | Several years | \$0 | Gaps, inconsistent coverage, unclear snapshot timestamps. **Exploratory only — never a published result's sole source.** |

Honest summary: the traps are Alpha Vantage for bulk, free datasets as a result basis, and any tier that gives options *trades* without *quotes*. The realistic path is yfinance + CBOE free (layers a, c, d) → Polygon Stocks (b) → ORATS summary → ORATS/Polygon/CBOE chains for the two or three symbols your hypotheses actually need.

### 1.4 Data quality — the section that decides whether your results are real

**Survivorship bias.** yfinance returns only live tickers. Any universe built from today's index membership backtests a portfolio of known winners. Fix: build the universe from a point-in-time membership file (`conf/universe.yaml` with `added`/`removed` dates), and source delisted tickers explicitly (Polygon's ticker endpoint with `active=false`). Assert: for every backtest date, every symbol in the universe was listed on that date.

**Dividend/split adjustment — why adjusted close breaks options backtests.** Adjusted close rewrites *history* so that today's price series is continuous. An option strike does not get rewritten. If you compare a 2019 strike of 250 to a back-adjusted 2019 close of 218, your moneyness, delta, and every filter derived from them are wrong. Rules:
- Store **unadjusted OHLC** as the canonical series, plus a separate `adj_factor` column.
- Use unadjusted prices for anything touching strikes, moneyness, or option pricing.
- Use adjusted prices only for return/realized-vol computation.
- Splits *do* adjust option contracts (strike divided, multiplier or contract count changed). Odd ratios produce non-standard deliverables — flag and exclude symbols within ±10 trading days of a split unless you have handled the adjustment explicitly.
- Special dividends shift forwards and thus put/call parity; flag them.

```python
close_adj = close_raw * adj_factor       # returns, vol
moneyness = strike / close_raw           # never close_adj
```

**Point-in-time correctness.** Every conditioning field needs an `as_of` timestamp — the time the value was *knowable*. Earnings dates get revised; index membership is announced before it is effective; economic data is revised. Rule: a feature used at decision time `t` may only depend on rows whose `as_of <= t`. Enforce with an assertion in the feature builder, not by discipline.

**Quote snapshot ≠ tradeable price.** An EOD option quote is one instant's NBBO. Your fill assumption must be explicit and pessimistic: mid minus a fraction of the half-spread, and never assume a fill at a quote whose size is unknown. Default in `costs`: pay 25% of the spread past mid on entry and exit, plus commissions and exchange fees. If a result only works at mid, it does not exist.

**Options quote pathologies to filter on ingest:**

| Pathology | Test | Action |
|---|---|---|
| Zero bid | `bid <= 0` | Drop for entry; can still be an exit at 0 |
| Crossed | `bid > ask` | Drop row, log |
| Locked | `bid == ask` | Suspect; drop unless corroborated |
| Wide-spread garbage | `(ask-bid)/mid > 0.25` (liquid) or `> 0.50` (single-name) | Exclude strike |
| Stale | quote timestamp older than N minutes vs bar close | Exclude |
| No interest | `open_interest == 0 and volume == 0` | Exclude |
| Arbitrage-violating | Call/put price outside intrinsic/parity bounds | Drop, log; a cluster means a source problem |
| Penny options | `mid < 0.05` | Exclude — spread dominates PnL |

**Timezone and timestamp alignment.** Store every timestamp as UTC, tz-aware; convert to `America/New_York` only for market-session logic. The three timestamps you must not conflate: (1) the equity bar close (16:00 ET), (2) the option quote snapshot time (frequently 15:45 or 16:15 depending on vendor), (3) settlement (SPX AM-settled options settle on the *opening* prints of expiration Friday; SPXW/PM and equity options settle at the close). Getting (3) wrong systematically biases expiration PnL. Assert that the offset between your underlying bar and your option snapshot is a constant known number of minutes, and record it in the manifest.

**NBBO vs consolidated tape.** OPRA NBBO is the best bid/offer across all options exchanges at an instant; a vendor's "consolidated" or single-exchange quote may be neither best nor synchronous. Trade prints tell you where someone traded, not where you could have. Prefer NBBO quotes; if you only have trades, you cannot backtest a multi-leg structure honestly.

**Missing days.** Compare your date index against `pandas_market_calendars.get_calendar("XNYS").schedule(...)`. Any missing session is a bug until proven a holiday. A half-day (early close 13:00 ET) must be handled, not silently averaged.

**Feed liveness is not the same check as historical completeness.** A series can be gap-free for twenty years and still be *dead right now* — the vendor quietly stopped updating it. This is invisible to every gap test, because the gap is at the end. Observed in practice: Yahoo carries `^VIX9D` and `^VIX3M` complete through history but frozen a month stale, while `^VIX` and `SPY` stay current. A backtest is unaffected; a live scanner silently trades on a flat-lining input. Assert staleness explicitly on every load — `(today - last_session).days <= max_stale_days` — and make the loader **raise**, not warn. Record `stale_days` per series in the manifest so the condition is visible before it matters.

### 1.5 Storage and loader pattern

Parquet with pyarrow, partitioned by symbol and date/year, snappy compression. Canonical dtypes fixed in a schema module so a re-ingest cannot silently change a column type.

```python
# src/optlab/io/loader.py
from pathlib import Path
import hashlib, json
import pandas as pd, pyarrow.dataset as ds

DATA = Path("data")

OHLCV_SCHEMA = {
    "date": "datetime64[ns, UTC]", "symbol": "string",
    "open": "float64", "high": "float64", "low": "float64",
    "close": "float64", "volume": "int64", "adj_factor": "float64",
}

def _key(name: str, **kw) -> str:
    return hashlib.sha256(json.dumps([name, kw], sort_keys=True, default=str).encode()).hexdigest()[:16]

def load(name: str, *, symbols=None, start=None, end=None, use_cache=True) -> pd.DataFrame:
    cache = DATA / "cache" / f"{name}_{_key(name, symbols=symbols, start=start, end=end)}.parquet"
    if use_cache and cache.exists():
        return pd.read_parquet(cache)
    filt = None
    if symbols:
        filt = ds.field("symbol").isin(list(symbols))
    df = ds.dataset(DATA / "curated" / name, format="parquet", partitioning="hive").to_table(filter=filt).to_pandas()
    if start is not None:
        df = df[df["date"] >= pd.Timestamp(start, tz="UTC")]
    if end is not None:
        df = df[df["date"] <= pd.Timestamp(end, tz="UTC")]
    df = df.sort_values(["symbol", "date"]).reset_index(drop=True)
    cache.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(cache, index=False)
    return df
```

Nothing outside `io/` touches the filesystem. That single rule is what makes the live scanner and the backtester provably read the same data through the same code path.

```python
# src/optlab/validate/checks.py
import pandas as pd, pandas_market_calendars as mcal

def validate_ohlcv(df: pd.DataFrame, start, end) -> None:
    assert set(OHLCV_SCHEMA).issubset(df.columns)
    assert df.duplicated(["symbol", "date"]).sum() == 0, "duplicate symbol/date"
    assert df["date"].dt.tz is not None, "naive timestamps"
    assert (df[["open", "high", "low", "close"]] > 0).all().all(), "non-positive price"
    assert (df["high"] >= df[["open", "close", "low"]].max(axis=1)).all(), "high < body"
    assert (df["low"] <= df[["open", "close", "high"]].min(axis=1)).all(), "low > body"
    assert (df["volume"] >= 0).all()
    sessions = mcal.get_calendar("XNYS").schedule(start, end).index.tz_localize("UTC")
    for sym, g in df.groupby("symbol"):
        missing = sessions.difference(g["date"].dt.normalize())
        assert len(missing) <= 0.005 * len(sessions), f"{sym}: {len(missing)} missing sessions"
    r = df.groupby("symbol")["close"].pct_change()
    assert (r.abs() > 0.60).sum() == 0, "unflagged >60% move — likely unhandled split"

def validate_option_quotes(df: pd.DataFrame) -> None:
    assert (df["bid"] <= df["ask"]).all(), "crossed quotes present"
    assert (df["strike"] > 0).all() and (df["expiry"] >= df["quote_date"]).all()
    assert df["dte"].between(0, 1100).all()
    assert (df["implied_vol"].dropna().between(0.01, 5.0)).all(), "IV out of range"
    assert df.duplicated(["quote_date", "symbol", "expiry", "strike", "right"]).sum() == 0
    bad = (df["ask"] - df["bid"]) / df[["bid", "ask"]].mean(axis=1)
    assert bad.median() < 0.25, "median relative spread implausible — check snapshot time"
```

Failures raise on ingest and the run aborts. Never write a curated partition from a payload that failed validation; leave it in `raw/` and log it.

### 1.6 Manifests and reproducibility

Every ingest writes `data/manifests/<dataset>_<utc_ts>.json`:

```json
{"dataset": "ohlcv_daily", "vendor": "polygon", "endpoint": "/v2/aggs/...",
 "fetched_at_utc": "2026-08-18T21:04:11Z", "params": {"start": "2010-01-01", "end": "2026-08-15"},
 "symbols": 512, "rows": 2043118, "date_min": "2010-01-04", "date_max": "2026-08-15",
 "content_sha256": "9f2c…", "validation": "passed", "code_git_sha": "a41c9e2",
 "schema_version": 3, "option_snapshot_offset_min": 15}
```

`content_sha256` is over the sorted parquet part-file hashes — it is the identity of the *data*, independent of where it sits on disk.

Reproducibility contract:

- **Pinned deps.** `pyproject.toml` + committed lockfile; `uv sync --frozen` in `make setup`. Pin `pandas`, `pyarrow`, `numpy`, `scipy`, `yfinance`, `pandas_market_calendars` exactly.
- **Seeds.** One `seed` field in every spec; `engine` sets `numpy.random.default_rng(seed)` and passes the generator explicitly. No global `np.random` calls, no bare `random`.
- **Entry points.**
  ```make
  setup:    ; uv sync --frozen
  data:     ; uv run python -m optlab.ingest.run --config conf/settings.yaml
  validate: ; uv run python -m optlab.validate.run
  backtest: ; uv run python -m optlab.engine.run --spec $(SPEC)
  scan:     ; uv run python -m optlab.scan.run --specs specs/ --date today
  ```
  `make data` is idempotent: it skips any (dataset, date-range) already covered by a passing manifest unless `FORCE=1`.
- **Re-derivability.** A result is `(spec_hash, manifest content hashes, code git sha, package lock hash, seed)`. All five go in `results/<spec_hash>/env.json`. To reproduce: check out the git sha, `uv sync --frozen`, re-fetch or restore the datasets whose `content_sha256` matches, run `make backtest SPEC=results/<hash>/spec_snapshot.yaml`. If the output stats differ by more than floating-point noise, something in that tuple is misrecorded — treat it as a P0 bug, not a curiosity.
- **Vendor data drift.** Vendors restate history. Never overwrite a curated partition in place; write a new manifest and keep the old parquet under a `schema_version`/fetch-date suffix if the content hash changes. A result whose underlying data hash no longer exists is marked stale in `results/index.jsonl` and must be re-run before it can be cited.

---

## 2. Hypothesis Generation & Pre-Registration

### 2.1 The Funnel: Over-Generate or Fail

You cannot pick winners at the idea stage. You can only run enough ideas through a fixed, honest filter that the survivors are worth capital. Budget the funnel explicitly:

| Stage | Count | Cost each | Gate to advance |
|---|---|---|---|
| Raw ideas (one-line notes) | 40 / quarter | 5 min | Passes the reality gate (§2.5) |
| Specified hypotheses (YAML, registered) | 12 | 45–90 min | Triage score ≥ 18/30 (§2.6) |
| Stage-1 tested (exploration slice, cheap) | 6–8 | 2–4 hrs | Signed effect in predicted direction, ≥100 non-overlapping events, survives basic controls |
| Stage-1 survivors | 4 | — | Advance to Stage-2 (holdout, costs, capacity) |
| Stage-2 survivors | 1–2 | 1–2 days | Paper trade |
| Live setups per year | 2–4 | — | — |

Two structural reasons to over-generate. First, the base rate: most published/folk options effects are either already arbitraged, or are risk premia that only pay if you can survive the drawdown they compensate you for. Assume a 5–10% hit rate from raw idea to tradeable. Second, multiplicity discipline only works if the denominator is known. If you generate ideas one at a time and stop when one "works," you have run an unbounded search with an unrecorded number of trials and your p-values are fiction. Fixing the batch size at 12 registered specs per quarter makes your multiple-testing correction (Section 4) actually computable.

Rule: never test an idea that was not registered as part of a numbered batch. Ideas that arrive mid-batch go into `ideas_inbox.md` and wait for the next batch.

### 2.2 Idea Source A — Market Microstructure and Mechanics

The highest-quality edges in options come from someone being forced to trade. Mine mechanics, not patterns.

Mining procedure, one week:

1. Build a one-page "flow calendar" of forced events: monthly OPEX (3rd Friday), quarterly triple witching, VIX futures settlement (Wednesday 30 days before the following month's SPX expiry), index rebalances (S&P quarterly effective 3rd Friday; Russell annual late June), month-end pension rebalance, quarterly dividend/earnings clusters.
2. For each event, ask: *who must trade, in what direction, at what time, and is the timing public?* Write the forced-flow sentence. If you cannot write it, drop the idea.
3. Convert to a testable trigger with a measurable outcome.

Concrete seed set, each already a near-hypothesis:

| Mechanic | Forced participant | Candidate effect |
|---|---|---|
| Dealer gamma positioning | Dealers delta-hedging short/long gamma books | Long-gamma regimes: intraday mean reversion, realized vol suppressed vs implied. Short-gamma: momentum, vol expansion |
| 0DTE flows | Intraday hedgers of same-day options | Late-session pinning/acceleration; premium in the last hour |
| Expiration pinning | Market makers hedging into large open interest strikes | Underlying drifts toward max-OI strike into Friday close |
| Index rebalance | Index funds forced to trade at close on effective date | Vol and skew dislocation in adds/deletes around the effective date |
| VIX futures roll | ETPs (VXX-style) mechanically rolling daily | Persistent contango carry; roll yield as a conditional short-vol signal |
| Variance risk premium | Options buyers paying insurance | IV > subsequent RV on average; conditional on VRP level, not unconditionally |
| Post-event vol crush | Uncertainty resolution at earnings/FOMC/CPI | IV collapse in the first minutes after the print; term-structure kink pre-event |
| Vol-of-vol | VIX options hedgers | VVIX/VIX relationship as a conditioning variable on tail hedge pricing |

Data you need for the gamma family: option chain snapshots with open interest and volume by strike/expiry (end-of-day is sufficient to start). Dealer positioning is *estimated*, not observed — treat every gamma-exposure construction as a proxy with a sign convention you must state in the spec.

### 2.3 Idea Source B — Academic Literature

Search efficiently, not exhaustively.

- **SSRN**: search the *effect*, not the buzzword — "variance risk premium term structure", "option expiration underlying returns", "implied volatility skew predicts returns", "delta-hedged option gains". Sort by downloads for canonical work, by date for decay checks.
- **Quantpedia**: use its strategy pages as an index of effect names and rough parameterizations, not as a source of truth. Every page names the original paper — go read that.
- **Cboe research / exchange whitepapers**: best source for index/product mechanics (settlement procedures, SPX vs SPXW, VIX calculation, 0DTE volume statistics). Mechanically reliable, promotionally biased on strategy performance.
- **Journal-level**: Journal of Financial Economics, Review of Financial Studies, Journal of Derivatives for options-specific microstructure.

A **usable** paper: states the trigger in terms of variables you can compute point-in-time; reports sample period, universe, and turnover; reports results net of some transaction-cost assumption; has an economic mechanism section that names the constrained party. An **untradeable** paper: cross-sectional sorts across thousands of single-name options with monthly rebalance and no liquidity screen; uses closing mid-quotes on illiquid options as fills; reports only alphas from a factor regression with no raw return path; requires proprietary data (signed order flow, dealer inventories, TAQ-linked options data) you will not buy.

**Decay check, mandatory before registering any literature idea.** Split the sample at the paper's publication (or first SSRN posting) date. Rebuild the simplest version of the signal yourself and compare pre-publication vs post-publication effect size on your own data. Expect roughly half the in-sample effect to vanish. Register the *post-publication* effect size as your prior, never the paper's headline number. If post-publication effect is ≤0 or the sign flips, the idea dies in the registry with cause of death `DECAYED`.

### 2.4 Idea Source C — Practitioner Writeups

Value: they name mechanics and current market plumbing years before academia does (0DTE dynamics, dealer gamma, ETP roll behavior). They are the best source for *what to look at*.

Treat with skepticism, in this order of severity: anything with an equity curve and no drawdown/sample stats; anything selling a subscription or a course; "backtests" that short options without modeling assignment, gap risk, or margin expansion; screenshots of a single trade; any claim about "dealer positioning" that presents an estimate as if it were observed inventory; anything that changes its parameters between posts.

Extraction rule: take only the *mechanism sentence* from practitioner content. Discard their parameters, their thresholds, and their performance claims. Re-derive all numbers yourself. If the writeup contains no mechanism sentence, discard entirely.

### 2.5 Idea Source D — EDA Without Contaminating the Holdout

This is where solo researchers destroy their own results, silently. The fix is structural, decided once, before you look at anything.

Partition your history the day you build the data layer:

| Slice | Share | Use |
|---|---|---|
| `EXPLORE` | earliest ~50% of history | Unlimited looking, plotting, sorting, idea generation, parameter intuition |
| `STAGE1` | next ~25% | One evaluation per registered hypothesis |
| `HOLDOUT` | most recent ~25% | Touched at most once per hypothesis, at Stage-2, ever |

Enforcement, not intention:

- Data loader takes a required `slice` argument. There is no default.
- `HOLDOUT` access requires an env var (`ALLOW_HOLDOUT=1`) and writes an append-only line to `holdout_access.log` (timestamp, hypothesis id, git commit). The log is committed.
- Any hypothesis whose id appears twice in `holdout_access.log` is retired as `CONTAMINATED`. No exceptions, no "I only fixed a bug."
- Notebooks may only import the `EXPLORE` loader; a pre-commit hook rejects notebooks referencing `HOLDOUT`.

Proper EDA on `EXPLORE`: distribution of the candidate trigger (how often does it fire? are events clustered?); overlap of holding windows; sensitivity of the outcome to the threshold (a cliff is a red flag, a plateau is good); stability across sub-periods; correlation of the trigger with obvious confounds (VIX level, term-structure slope, day-of-week, earnings proximity). Do this to *specify* the hypothesis. The moment the spec is registered, `EXPLORE` results are no longer evidence — they are the reason you believed it.

### 2.6 Idea Source E — Regime-Conditioning Known Effects

Most broad options effects are real but unconditional-average-negative-after-costs. The tradeable version is the conditional one. Take a known effect and cross it with a regime variable that is (a) computable point-in-time, (b) mechanically related to the effect.

Regime axes worth using: VIX term-structure slope (contango/backwardation), realized-vs-implied spread over trailing 20d, VVIX/VIX ratio, trailing realized vol percentile, estimated dealer gamma sign, credit-spread direction, days-to-major-macro-event.

Discipline: **one** regime variable per hypothesis, with the interaction direction predicted in advance and justified by the mechanism. Two conditioning variables on a base effect is not a hypothesis, it is a fitted subsample. If you want a second, it is a separate registered hypothesis with its own id.

### 2.7 The Hypothesis Spec

One YAML file per hypothesis at `hypotheses/H-YYYY-NNN.yaml`. Schema is validated by `scripts/validate_spec.py`; missing or empty required fields fail the commit.

```yaml
id: H-2026-007
name: opex_week_gamma_pin_spx
registered_utc: 2026-08-18T14:20:00Z
batch: 2026Q3-B1
status: REGISTERED

rationale: >
  Into monthly SPX expiration, dealer hedging of large open interest at
  round strikes suppresses realized vol relative to implied, making
  short-dated straddle selling into the pin favorable.

mechanism: >
  Dealers are net long gamma at high-OI strikes in index options. Hedging
  a long gamma book requires selling into rallies and buying dips, which
  damps realized vol. Who pays: hedgers and directional buyers of expiry-week
  optionality, who accept negative expected carry for gap protection. This
  compensation is real risk transfer, so the edge should persist but must
  lose money in gap events.

trigger:
  description: >
    On Wednesday of monthly OPEX week, at 15:45 ET, SPX spot is within
    0.35% of the strike with the largest net call+put open interest in the
    Friday expiry, and estimated dealer gamma exposure is positive.
  computable_pit: true
  inputs: [spx_spot, opex_friday_chain_oi, gex_estimate]
  threshold: {distance_pct: 0.0035, gex_sign: positive}

# Estimation and trading universes are separate on purpose. Estimate the
# effect where the sample is (wide), trade it where the liquidity is (narrow).
# The subgroup check is mandatory: an effect that vanishes in the names you
# actually intend to trade is not tradeable, however strong it is in aggregate.
estimation_universe: [SPX]
trading_universe: [SPX]
subgroup_check: >
  Effect must retain >=60% of its magnitude, with unchanged sign, when
  restricted to trading_universe alone.

entry_timing: Wednesday OPEX week, 15:45-15:55 ET, mid minus half-spread
holding_period: to Friday 09:30 ET settlement-adjacent close
exit_rule: >
  Close Friday 09:30 ET, or stop at 2x credit received, whichever first.

structure: short ATM straddle, Friday expiry, delta-neutralized at entry

outcome_variable: pnl_per_unit_vega, and realized_vol_wed_to_fri minus implied_vol_at_entry
predicted_direction: negative (RV below IV); positive strategy PnL
prior_effect_size: >
  RV - IV of -1.5 to -3.0 vol points; per-event mean PnL ~0.25 x credit,
  hit rate 65-75%, left tail to -2x credit.

falsification: >
  Dead if mean (RV - IV) >= -0.5 vol points on STAGE1, or if per-event mean
  PnL net of 1 full bid-ask spread <= 0, or if the effect is absent in the
  positive-GEX subsample (which would falsify the stated mechanism).

data_required:
  - SPX EOD option chains with OI by strike/expiry, 2016+
  - SPX 1-minute bars
  - historical bid/ask quotes for ATM Friday-expiry options

known_confounds:
  - OPEX week overlaps FOMC in 8 of 12 months in some years
  - positive GEX correlates with low VIX; effect may be a VIX-level effect
  - OI-based pin strike is endogenous to spot

expected_decay: moderate; widely discussed post-2021, monitor annually
capacity_estimate: >
  SPX Friday ATM straddle depth supports ~50-150 contracts without
  >0.05 vol slippage; far above account size. Not capacity-constrained.

sample_size_expected: {raw_events: 108, independent_clusters: 96, per_year: 12, measured_utc: 2026-08-18}
slice_plan: {stage1: STAGE1, stage2: HOLDOUT}
```

Required fields, no exceptions: `id, name, registered_utc, rationale, mechanism, trigger (with computable_pit), estimation_universe, trading_universe, subgroup_check, entry_timing, holding_period, exit_rule, outcome_variable, predicted_direction, prior_effect_size, falsification, data_required, known_confounds, expected_decay, capacity_estimate, sample_size_expected`.

`sample_size_expected` must carry the measured cluster count from the pre-flight (2.9b), not an estimate. A spec whose sample was never counted cannot be registered.

### 2.8 Pre-Registration Enforcement, Mechanically

Philosophy does not stop you from moving a threshold after seeing a result. Tooling does.

```
1. Write hypotheses/H-2026-007.yaml
2. scripts/validate_spec.py  -> schema check, fails commit if incomplete
3. git commit -m "register H-2026-007"
4. spec_hash = sha256(canonical_yaml_bytes)   # sorted keys, normalized whitespace
5. Backtest runner:
     h = sha256(spec_file)
     if h not in {hashes of this file in git log}: ABORT
     if commit_time(h) > now: ABORT
     write results/H-2026-007/<spec_hash>/ with spec_hash + git HEAD in metadata
```

Implementation notes: compute the hash over a *canonicalized* dump (sorted keys, stripped comments) so formatting churn does not invalidate a spec. The runner walks `git log --follow -- hypotheses/H-2026-007.yaml`, hashes each blob version, and requires the working-tree hash to be in that set — meaning the exact spec you are testing was committed at some point *before* this run. A pre-commit hook rejects any commit that modifies a spec whose id already appears in `results/`, unless the spec's `id` is incremented (`H-2026-007b`) and the original is retired with a cause of death. Results directories are keyed by spec hash, so a changed spec cannot overwrite an old result — you get two results and an obvious paper trail of how many variants you tried. That count feeds the multiple-testing correction.

### 2.9 The Reality Gate: Disqualifiers, Sample Pre-Flight, Viability Screen

Three checks, all applied **before writing the spec**. Together they are the cheapest filter in this document: they consume no outcome data, burn no trial, never touch the holdout, and take an afternoon for a whole batch of candidates.

**(a) Disqualifiers.** Any single hit kills the idea.

| Disqualifier | Test |
|---|---|
| No stated mechanism | You cannot write one sentence naming who is forced or compensated |
| "Who's paying you" has no answer | The counterparty is "the market" or "irrational traders" with no constraint named |
| Trigger not point-in-time | Needs data revised later, or a value from the future (close price for an at-close entry, settlement values, restated fundamentals) |
| Trigger not computable in real time | Requires data you receive with a lag longer than the holding period |
| Outcome not measurable | "Better risk-adjusted feel", no scalar you can compute per event |
| No falsification condition | You cannot state a number that would make you abandon it |
| Data you don't have | Signed order flow, dealer inventories, full tick options data — and no budget for it |
| Capacity below account size | Effect lives in options with <50 contracts daily volume or >15% spreads |
| Sample too small | Fewer than ~50 non-overlapping events available in all of history |
| Already registered | Substantively identical to an existing registry entry, alive or dead |

**(b) Sample-size pre-flight.** Run the trigger against history and count events — *never the outcome.* Counting trigger frequency is not measuring an effect, so this is legitimate pre-registration work (the spec's `sample_size_expected` field demands the number anyway) and it costs nothing.

Report three figures per candidate:

| Figure | Definition | Why it matters |
|---|---|---|
| Raw events | Bars where the trigger fires | The flattering number. Ignore it. |
| **Independent clusters** | Events separated by more than ~1.4× the holding window | The real sample. This is what powers every statistic. |
| Events per year | Raw ÷ years | A trigger firing >150×/yr is a *regime*, not a signal — see the viability screen |

```python
def clusters(dates, hold_days):
    """Events inside one holding window are one observation, not many."""
    d = sorted(dates); n, last = 1, d[0]
    for x in d[1:]:
        if (x - last).days > hold_days * 1.4:
            n += 1; last = x
    return n
```

The ratio of raw events to clusters is routinely **10–20×** for state-based triggers ("vol is high", "curve is in contango") because such states persist for weeks. It is near **1×** for point events (a gap, an earnings release). A candidate that cannot produce ≥50 events *and* ≥20 clusters (§3.8) after the holdout is carved out is dead here, before it consumes a spec.

> **Rule.** Measure the sample before you write the spec. Anything else spends effort on candidates that were arithmetically incapable of producing a trustworthy answer.

**(c) The viability screen.** Sample size alone decides nothing. Three quantities interact, and a candidate must clear all three:

> **sample size × effect size × cost tolerance**

Frequent tiny edges cannot pay the option bid/ask. Rare large edges have no sample to establish they are real. Viable candidates sit in the middle band.

| Family | Independent obs. | Typical effect | Survives the spread? |
|---|---|---|---|
| Overnight vs intraday decomposition | ~8,400/symbol | A few bps/day | **No** — spread exceeds the edge |
| Weekly expiry effects | ~1,700 | Small | Marginal |
| Earnings IV crush | ~90/name × universe | **Large** (IV falls 30–50% overnight) | **Yes** |
| Scheduled macro (FOMC, CPI) | 270 / 400 | Large, concentrated | Yes |
| Volatility-regime states (VIX-conditioned) | **~90** | Moderate | Maybe — but the sample is the binding constraint |

This is why an effect with beautiful statistics can be worthless and a noisier effect can be tradeable. Options charge a fixed toll per round trip; an edge smaller than the toll is not an edge regardless of its t-statistic. Evaluate this **before** any work, not at §6 when the options backtest finally reveals it.

**Organize idea generation by event family, not by cleverness.** The families above differ by more than 100× in available sample using the *same free data*. Sorting candidates by achievable observation count is the highest-leverage filter in the whole process, and it precedes every source in §2.2–2.6.

### 2.10 Triage Rubric

Score each specified hypothesis 1–5 on six axes before spending compute. Total 30. Threshold to advance to Stage-1: **≥18**, with **no axis scoring 1**.

| Axis | 1 | 3 | 5 |
|---|---|---|---|
| Mechanism strength | Pattern only | Plausible behavioral story | Named forced participant, structural constraint |
| Data availability | Must buy expensive data | Have it, needs cleaning | Already in local store |
| Expected sample size | <50 events | 100–300 | >500 non-overlapping |
| Tradability / liquidity | Wide spreads, thin | Tradeable with care | Index options, tight, deep |
| Crowding risk (5 = uncrowded) | Everyone runs this | Discussed but nuanced | Obscure or hard to implement |
| Expected decay (5 = durable) | Fades in months | Slow erosion | Structural, persists |

Worked example, batch 2026Q3-B1:

| id | Hypothesis | Mech | Data | Sample | Trade | Crowd | Decay | Total | Decision |
|---|---|---|---|---|---|---|---|---|---|
| H-2026-007 | OPEX gamma pin, SPX straddle | 5 | 4 | 3 | 5 | 2 | 3 | 22 | Advance |
| H-2026-008 | Post-FOMC IV crush, SPX | 4 | 5 | 3 | 5 | 2 | 3 | 22 | Advance |
| H-2026-009 | VIX term-slope conditional short vol | 5 | 5 | 5 | 4 | 1 | 2 | 22 | Advance (crowding flagged; size down) |
| H-2026-010 | Earnings vol crush, single names | 3 | 3 | 5 | 2 | 1 | 2 | 16 | Hold — liquidity + crowding |
| H-2026-011 | Skew steepness predicts index returns | 2 | 4 | 4 | 4 | 3 | 2 | 19 | Advance |
| H-2026-012 | Russell rebalance vol dislocation | 4 | 2 | 1 | 3 | 4 | 4 | 18 | Kill — sample size axis = 1 |

Note H-2026-012: total clears 18, but a 1 on any axis is fatal. One event per year cannot be validated in your lifetime.

### 2.11 The Hypothesis Registry

One file, `hypotheses/REGISTRY.md`, regenerated from the YAML specs plus results metadata by `scripts/build_registry.py`. Never hand-edited.

Statuses: `DRAFT → REGISTERED → STAGE1 → STAGE2 → PAPER → LIVE → RETIRED`. Movement is one-directional except `LIVE → RETIRED` and `PAPER → RETIRED`.

Columns: `id | name | batch | status | registered_utc | spec_hash | triage_score | stage1_result | stage2_result | live_since | retired_utc | cause_of_death | successor_id | notes`.

| id | name | status | triage | stage1 | stage2 | cause_of_death |
|---|---|---|---|---|---|---|
| H-2026-007 | opex_week_gamma_pin_spx | STAGE2 | 22 | RV-IV = -2.1 vp, n=104 | pending | — |
| H-2026-008 | fomc_iv_crush_spx | STAGE1 | 22 | mean PnL +0.11x credit, n=71 | — | — |
| H-2026-009 | vix_slope_conditional_short_vol | PAPER | 22 | passed | passed, SR 0.9 | — |
| H-2026-011 | skew_steepness_index_return | RETIRED | 19 | t=0.4, n=210 | — | NO_EFFECT |
| H-2026-012 | russell_rebalance_vol | RETIRED | 18 | — | — | INSUFFICIENT_SAMPLE |
| H-2026-004 | zero_dte_late_day_momentum | RETIRED | 20 | passed | failed net of costs | COSTS_EXCEED_EDGE |

Controlled vocabulary for `cause_of_death`: `NO_EFFECT`, `WRONG_SIGN`, `COSTS_EXCEED_EDGE`, `INSUFFICIENT_SAMPLE`, `DECAYED`, `CONFOUNDED`, `CAPACITY`, `CONTAMINATED`, `SUPERSEDED`, `LIVE_UNDERPERFORM`, `STAGE1_FALSE_POSITIVE`, `STRUCTURE_EXHAUSTED`.

The last two are stage-2 verdicts and are defined in 6.11: `STAGE1_FALSE_POSITIVE` when the underlying edge does not survive restriction to the tradeable sample, and `STRUCTURE_EXHAUSTED` when the retry budget is spent.

**Dead hypotheses never leave the registry.** Three reasons, all practical. (1) In eighteen months you will have the same idea again from a different source; the registry answers it in thirty seconds instead of two days. (2) The count of registered-and-tested hypotheses is the denominator for your false-discovery control — deleting failures inflates your apparent hit rate and invalidates every correction downstream. (3) Causes of death cluster. When five ideas die `COSTS_EXCEED_EDGE`, that is not five failures, it is one finding about your execution assumptions, and it should redirect the next batch toward wider-margin structures. Review the death ledger at the start of every batch and write down what it is telling you before generating new ideas.

---

## 3. Stage 1 — Testing the Underlying Premise (no options yet)

### 3.1 Why Stage 1 exists

An option structure has enough degrees of freedom — strike, tenor, ratio, roll rule, delta band — that it can manufacture a P&L curve out of a premise with zero information content, and it can equally bury a real edge under theta and spread. If you go straight to backtesting a "put ratio spread into earnings," you will not be able to tell whether you found a signal, a structural short-vol bias, or a fitting artifact of the strike you happened to pick.

So: **strip the trade down to the claim about the world, and test that claim on price and volatility data alone.**

> **Rule.** If the premise shows no edge in the underlying, no option structure rescues it. Stage 1 failure is terminal for that hypothesis. You do not get to argue "but the convexity makes it work."

The single legitimate exception is a hypothesis that is *inherently about implied volatility* — "IV is systematically too high the week after a VIX spike," "term structure inversion mean-reverts." Those cannot be expressed in spot alone. But they are not exempt from Stage 1; the underlying premise simply becomes **IV vs. subsequent RV**, and it is tested with exactly the same event-study machinery in §3.2–3.3(c). You still need a trigger, an outcome window, a conditional distribution, and a permutation test before you touch an option chain.

### 3.2 Every hypothesis is an event study

Force every idea into this frame. If it does not fit, it is not yet a hypothesis.

| Component | Definition | Example |
|---|---|---|
| **Universe** | Point-in-time tradeable set | S&P 500 members as of date *t*, or a fixed liquid single-name list |
| **Trigger** | Boolean series `trig[t]`, computable from data available at *t* | `RV20 / RV60 < 0.6` |
| **Anchor** | The first bar you could actually act on | `t+1` open (never `t` close) |
| **Outcome window** | Horizon *h* in bars, fixed in advance | 10 trading days |
| **Outcome** | Scalar per event | forward log return, forward RV, RV − IV |
| **Baseline** | Same outcome computed on *all* bars, or on a matched-sample of non-trigger bars | unconditional 10d return distribution |

The comparison that matters is **conditional vs. unconditional**, not conditional vs. zero. Equities drift up; forward 10-day returns are positive on average unconditionally. A signal with a positive mean forward return has proven nothing until it beats the base rate. Likewise, a "vol expansion" signal fires disproportionately in high-vol regimes where forward RV is elevated for everyone.

```python
import numpy as np, pandas as pd

h = 10
logp   = np.log(px["close"])
fwd    = (logp.shift(-h) - logp).shift(-1)      # entry at t+1, exit at t+1+h
trig   = build_trigger(px)                       # boolean, uses data <= t only
mask   = trig & fwd.notna()

cond   = fwd[mask]
uncond = fwd[fwd.notna()]

delta  = cond.mean() - uncond.mean()             # the effect size that matters
```

Report `cond.mean()`, `uncond.mean()`, their difference, and the same three for the median. Where the trigger has strong regime dependence, upgrade the baseline to a **matched sample**: bucket all bars by trailing 60d RV decile (and, for cross-sectional work, by sector), then draw the unconditional comparison only from the same buckets in the same proportions the events occupy. A raw unconditional mean is a weak baseline; a regime-matched one is honest.

### 3.3 The three outcome families

**(a) Directional drift.** Statistic: mean forward log return, conditional minus unconditional. Null: no difference. Test: OLS of `fwd ~ trig_dummy` with HAC errors (§3.6), *plus* a distribution-free companion — the **sign test** on the difference from the unconditional median, via `scipy.stats.binomtest(k=n_pos, n=n, p=p0)` where `p0` is the unconditional fraction positive over the same horizon. Report both. A mean that is significant while the sign test is flat means a handful of large moves carry the result; that is a tail trade, not a drift trade, and it changes which option structure is appropriate later.

**(b) Realized volatility / range.** Statistic: `log(RV_fwd(h) / RV_trail(k))`, in logs because vol ratios are right-skewed and the log is approximately normal. Null: the conditional mean log-ratio equals the unconditional mean log-ratio (which is *not* zero — vol mean-reverts, so the ratio is systematically < 1 after high-vol bars and > 1 after low-vol bars). Test: same HAC OLS on the log-ratio; a Levene or Brown-Forsythe test (`scipy.stats.levene(..., center='median')`) as a secondary check on dispersion.

Estimator choice matters more than people expect:

| Estimator | Use when | Note |
|---|---|---|
| Close-to-close | Outcome is what a delta-hedged position actually earns over the window | Highest variance; ~5x less efficient than range estimators |
| **Parkinson** (H/L) | Short windows, clean intraday, no gaps | Assumes zero drift, no jumps; *understates* vol when overnight gaps carry the move |
| **Garman-Klass** (OHLC) | General-purpose efficiency gain on continuous sessions | Still assumes no overnight jump; biased low around earnings |
| **Yang-Zhang** | Anything with overnight gaps — earnings, macro, single names | Drift-independent, handles open jumps; the default for event studies |

Use Yang-Zhang for measurement, close-to-close for anything you will later compare against option pricing, and say which you used. Implement them yourself from OHLC in ~15 lines of numpy; do not pull an unvetted vol package.

**(c) Implied vs. realized (variance risk premium).** Statistic: `IV_atm(t, tenor=h) - RV_cc(t+1 .. t+1+h)` in vol points, or the variance-space version `IV² - RV²` if you intend to trade variance-linear structures. Null: the conditional VRP equals the unconditional VRP for that underlying — which is structurally positive (roughly 2–4 vol points on index, wider and noisier on single names). Any hypothesis claiming "options are expensive here" must clear the *unconditional* premium, not zero. Test: HAC OLS of the spread on the trigger dummy. This is the Stage 1 test for IV-native hypotheses, and it uses only the ATM IV surface — no structure, no strikes, no P&L simulation yet.

### 3.4 Lookahead bias: the catalogue

Enumerate these on every test. Most are silent — the backtest just looks good.

1. **Same-bar entry.** Trigger computed from the *close* of bar *i*, filled at the close of bar *i*. Structurally impossible for anything but a market-on-close order placed before you knew the close. Enter at *i+1* open.
2. **Full-series indicators, then slice.** `df['z'] = (x - x.mean()) / x.std()` uses the whole sample's moments. Every normalization must be rolling/expanding.
3. **Adjusted prices restating history.** Split/dividend adjustment rewrites all prior bars. A \$50 threshold, a share-price filter, or a "penny stock" screen evaluated on adjusted prices is evaluating a number that did not exist at the time. Use raw prices for filters, adjusted for returns.
4. **Revised macro data.** CPI, NFP, GDP are revised for years. Backtesting on the current vintage is lookahead. Use point-in-time vintages (ALFRED) or exclude macro-level triggers.
5. **Event calendars known too early.** Earnings dates get moved; index rebalance announcements have a publication timestamp. Use the announcement time, not the event time.
6. **`.shift()` sign errors.** `shift(1)` moves data *forward* (yesterday's value onto today) — correct for features. `shift(-1)` pulls the future back — correct only for constructing outcomes. Mixing them up is the single most common leak. Assert on it.
7. **`rolling(..., center=True)`** — uses future bars by construction. Never in feature code.
8. **Resampling leaks.** `resample('W').last()` labels the bar at the week's start in some conventions; daily→weekly features must be lagged one full period after the period closes.
9. **Survivorship.** A universe of "today's S&P 500" removes every company that blew up. Use a point-in-time membership file, or accept that your result is an upper bound and say so.
10. **Investigator lookahead.** You chose to test XLE in 2020 and NVDA in 2023 because you remember what happened. This bias leaves no trace in code. Defense: define the universe by a mechanical rule (top *N* by dollar volume as of the sample start), fixed before you look at anything.

**Structural defense.** Do not police this by review. Build one point-in-time iterator and route every Stage 1 test through it:

```python
def run_event_study(bars, strategy_fn, h):
    """strategy_fn(view) -> bool. `view` is bars.iloc[:i+1]; nothing later exists."""
    events = []
    for i in range(WARMUP, len(bars) - h - 1):
        if strategy_fn(bars.iloc[: i + 1]):        # hard boundary
            events.append(i)
    return events
```

It is slower than vectorized code. Use it as the referee: vectorize for speed, then assert the vectorized trigger dates equal the iterator's on a 2-year slice.

**The one-extra-bar test.** Recompute every result with the entry delayed one additional bar (`fwd.shift(-1)` on top of the existing lag). A real edge with a multi-day horizon degrades *mildly* — call it under 30% loss of effect size. If the result collapses toward the unconditional baseline, you were leaking, or your edge lives entirely in the first bar and will be eaten by spread. Either way it does not advance.

### 3.5 Data splitting protocol

Three-way, strictly chronological:

| Split | Example range | Purpose | Touch limit |
|---|---|---|---|
| **Exploration / in-sample** | 2010-01-01 → 2018-12-31 | Form hypotheses, tune, fail freely | Unlimited |
| **Validation** | 2019-01-01 → 2022-12-31 | Choose among ≤5 pre-registered variants | ~5 evaluations per hypothesis |
| **Sealed holdout** | 2023-01-01 → present | Final confirmation | **Once, ever, per hypothesis** |

Chronological is right for markets because the data-generating process is non-stationary and regimes are persistent: a random split trains you on the future of the same regime you test on. It also mirrors the only deployment you will ever have — past predicts future.

**Holdout discipline.** Before touching it, write the pass/fail criteria (§3.8) into a file and commit it. Then run once. If it fails, the hypothesis is dead — you do not tweak and re-run. If you do re-run, that period is permanently burned; move the holdout boundary forward and wait for new data. Log every holdout touch in a `holdout_log.md` with date, hypothesis ID, and result. This log is the only thing standing between you and slow-motion overfitting.

**Purged/embargoed CV.** When events are few (< ~150) and you cannot afford to give up a third of the sample, use *k*-fold CV over time with purging and embargo instead of a validation block. The problem: with a 10-day outcome window, an event at the end of the training fold has an outcome that overlaps bars inside the test fold — the folds share information.

- **Purge:** drop from the training set every event whose outcome window `[t+1, t+1+h]` intersects the test fold's date range.
- **Embargo:** additionally drop training events falling within *e* bars *after* the test fold ends, where `e ≈ h` (some use `e = 0.01 * n_bars`). This kills leakage from serial correlation in features that straddle the boundary.

Implement as a custom splitter yielding index arrays and pass it to `sklearn.model_selection.cross_val_score(cv=my_splitter)` — `TimeSeriesSplit` alone does *not* purge or embargo.

### 3.6 Statistics toolkit

**Proportion CIs.** For hit rates: `proportion_confint(count=k, nobs=n, alpha=0.05, method='wilson')` from `statsmodels.stats.proportion`. Wilson, not normal — normal is badly wrong at small *n* and extreme *p*. Report the interval, never the point estimate alone. With 40 events, a 60% hit rate has a Wilson CI of roughly [44%, 74%] — which is to say, you know nothing.

**Overlapping windows and HAC.** Daily-sampled 10-day forward returns share 9 of 10 days with their neighbours. The effective sample is ~*n/h*, and the naive t-stat is inflated by roughly √h — a factor of ~3.2 at *h*=10. Fix:

```python
import statsmodels.api as sm
X   = sm.add_constant(trig.astype(float))
res = sm.OLS(fwd, X, missing='drop').fit(cov_type='HAC', cov_kwds={'maxlags': h, 'use_correction': True})
print(res.summary())          # t-stat on the trig coefficient is the number you cite
```

`maxlags = h` (or `h + 1`) is the right lag choice for an *h*-bar overlap. Alternatively, sample non-overlapping events only — cleaner, but costs you sample.

**Bootstrap.** For any path-dependent statistic (max drawdown of the cumulative outcome curve, Sharpe of an event-weighted series), i.i.d. bootstrap is invalid. Use the stationary bootstrap: `arch.bootstrap.StationaryBootstrap(block_size, data)` with `block_size ≈ h` to `2h`, then `.conf_int(func, reps=5000, method='bca')`. `CircularBlockBootstrap` is an acceptable alternative.

**Permutation test — the workhorse.** This is the single most useful test in Stage 1 because it holds the outcome series fixed and destroys only the timing information, which is exactly the thing you claim to have.

```python
def permutation_p(fwd, trig, n_perm=10000, seed=0):
    rng  = np.random.default_rng(seed)
    fwd  = fwd.dropna()
    trig = trig.reindex(fwd.index).fillna(False).values
    k, obs = trig.sum(), fwd.values[trig].mean() - fwd.values.mean()
    null = np.empty(n_perm)
    for j in range(n_perm):
        idx = rng.choice(len(fwd), size=k, replace=False)
        null[j] = fwd.values[idx].mean() - fwd.values.mean()
    return (np.sum(np.abs(null) >= abs(obs)) + 1) / (n_perm + 1), null
```

Two refinements. (i) If events cluster, permute *blocks* of trigger dates (draw contiguous runs matching the observed run-length distribution) rather than isolated dates, or the null is too easy to beat. (ii) If the trigger is regime-dependent, draw the permuted dates *within* the same RV-decile buckets, so the null preserves regime exposure. Always plot the observed statistic against the null histogram; you will learn more from the picture than the p-value.

**Minimum sample size.** For a two-sided test at α=0.05 with 80% power, the per-group requirement is

`n = 2 (z_{α/2} + z_β)² / d²  =  15.7 / d²`, where `d = Δμ / σ` (Cohen's d).

Worked: you expect a 0.40% edge in 10-day return; the unconditional 10-day σ is 4.0%. Then `d = 0.10` and `n ≈ 1570` events. That is fatal for a daily-bar single-name study, and it is the honest answer: **small directional edges are not detectable at Stage 1 sample sizes.** This is why vol-based outcomes (family b) are more productive — the log RV-ratio has `d` in the 0.3–0.6 range for real signals, needing only ~50–175 events. Compute this number *before* running the test and decide whether the study is even powered. Use `statsmodels.stats.power.TTestIndPower().solve_power(effect_size=d, alpha=0.05, power=0.8)` for the exact figure.

### 3.7 The pre-flight diagnostic pack

Every Stage 1 test emits all six. No exceptions, no "I'll check that later."

| Diagnostic | Computation | Required to advance |
|---|---|---|
| **Event count** | `trig.sum()` after warm-up and NaN drops | ≥ the §3.6 power figure, or explicitly flagged as underpowered |
| **Clustering** | Number of clusters after merging events within *h* bars; report `n_events / n_clusters` | Ratio < 4, and ≥ 20 distinct clusters. 200 events in 12 clusters is 12 observations |
| **Top-3 removal** | Recompute the effect with the 3 largest-|outcome| events dropped | Effect retains ≥ 50% of magnitude and keeps its sign |
| **By year** | Effect size + event count per calendar year | Sign consistent in ≥ 70% of years with ≥ 5 events |
| **By regime** | Bucket by trailing VIX or RV tercile; effect per bucket | Sign consistent in ≥ 2 of 3, and you can state *why* it concentrates where it does |
| **Cumulative curve** | `cond_outcomes.cumsum()` plotted against event index (not calendar) | Broadly monotone; no single vertical step > 25% of total |

The cumulative curve on *event index* is the highest-information plot in the whole stage — it exposes step-function results, dead periods, and regime death instantly.

### 3.8 Stage 1 pass/fail criteria

Hard gates. All must pass on in-sample **and** validation before the holdout is unsealed.

| Gate | Threshold |
|---|---|
| Event count | ≥ 50 events **and** ≥ 20 independent clusters |
| Effect size vs. costs | Conditional-minus-unconditional effect ≥ **3×** the round-trip cost you will face in options (use a placeholder of 1.0 vol point for vol trades, 0.30% for directional single-name) |
| Permutation p-value | ≤ 0.01 (block/regime-aware permutation, ≥ 10,000 draws) |
| HAC t-stat | \|t\| ≥ 2.5 with `maxlags = h` |
| Sign consistency | Same sign in ≥ 70% of years with ≥ 5 events, and in ≥ 2 of 3 regime buckets |
| Leave-out-best-year | Drop the single best calendar year: effect retains ≥ 60% of magnitude, permutation p ≤ 0.05 |
| Top-3 removal | Effect retains ≥ 50% of magnitude, sign unchanged |
| One-extra-bar delay | Effect retains ≥ 70% of magnitude |

These are deliberately strict. The funnel is wide — you will generate dozens of hypotheses, and at a nominal α of 0.05 you would pass several purely by chance. The p ≤ 0.01 threshold plus the structural gates (clustering, leave-out-best-year, top-3) are doing multiple-comparison duty without requiring you to formally track a family-wise error rate. If you are running many hypotheses in a batch, additionally apply Benjamini-Hochberg FDR control at q=0.10 via `statsmodels.stats.multitest.multipletests(pvals, method='fdr_bh')`.

A hypothesis that clears all eight gates has earned the right to be expressed as an options structure. Nothing else has.

---

## 4. The Anti-Overfitting Protocol

Section 3 tells you whether *one* hypothesis beat chance. This section assumes you will run hundreds of variants across dozens of hypotheses, and that the winner of that search is, by default, noise. Everything here is machinery for making the default assumption falsifiable.

### 4.1 The Arithmetic of Searching

Take `N` strategies with **zero true edge** and independent returns. Each has an estimated Sharpe that is noise around zero with standard error `SE`. For annualized Sharpe from `Y` years of data, when the true Sharpe is 0:

```
SE(SR_annual) ≈ sqrt((1 + SR²/2) / T_obs) * sqrt(periods_per_year) ≈ 1 / sqrt(Y)
```

The expected maximum of `N` iid standard normals is asymptotically `sqrt(2·ln N)`. A tighter finite-`N` form (Bailey & López de Prado) uses the Euler–Mascheroni constant `γ ≈ 0.5772`:

```
E[max_N] ≈ (1-γ)·Z⁻¹[1 - 1/N] + γ·Z⁻¹[1 - 1/(N·e)]
```

So the expected best *in-sample* Sharpe you will observe from pure noise is `E[max_N] × SE`.

| N trials | sqrt(2·ln N) | E[max_N] | Best SR, 3 yrs (SE=0.58) | Best SR, 5 yrs (SE=0.45) |
|---|---|---|---|---|
| 1 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10 | 2.15 | 1.58 | 0.91 | 0.71 |
| 50 | 2.80 | 2.28 | 1.32 | 1.02 |
| 200 | 3.26 | 2.77 | 1.60 | 1.24 |

Read the last two columns again. **A Sharpe of 1.6 on three years of data, found after 200 variants, is the expected outcome of searching pure noise.** It is not evidence of anything. Correlated trials (the usual case — you are sweeping a parameter, not drawing fresh strategies) reduce the *effective* `N`, which helps; selecting on a metric noisier than Sharpe (win rate on 40 events, max drawdown) hurts. Treat the table as the floor a candidate must clear, not the ceiling.

Two consequences drive the rest of this section: (1) you must know `N`, which means logging it; (2) you must have tests that noise fails and mechanism passes, which means adversarial controls, not more statistics on the same sample.

### 4.2 Trial Accounting

> **When a machine runs the backtests, this section becomes the binding constraint.** The arithmetic in 4.1 assumes trial counts bounded by human patience — a few dozen. An automated researcher can run two hundred variants in an hour, which pushes the expected best-of-N noise Sharpe from ~2.1 to ~2.9 and makes almost any in-sample result unremarkable. Two defenses are mandatory under automation: (i) the variant list is enumerated and committed *before* the first run, so the denominator is fixed in advance rather than discovered afterwards; (ii) a hard **trial budget per hypothesis**, agreed up front and enforced by the runner, which refuses to execute run N+1. Speed without a budget does not accelerate discovery — it manufactures false positives faster.

**Rule: every backtest execution appends one line to `trials.jsonl`, before you look at the result. Including the ones you abandon.**

The single most common way a solo researcher destroys themselves is under-reporting trials to themselves. You sweep 12 lookback windows, three of them error out, you fix a bug and re-run, you "just check" two exit rules — and then you report `N = 1` to your own deflated-Sharpe calculation. The correction is only as honest as the counter.

Schema — append-only, one JSON object per line, never edited:

```json
{"trial_id":"0f3a...","ts":"2026-03-04T18:22:11Z","hypothesis_id":"H014",
 "spec_hash":"sha256:9c1d...","code_rev":"a41b8e2","dataset_rev":"opra_2015_2024_v3",
 "params":{"gap_pct":0.02,"dte":7,"delta":0.30,"exit":"eod"},
 "split":"train","n_events":214,
 "metrics":{"sharpe":1.12,"mean_ret":0.0041,"t_hac":2.31,"p":0.021,"win_rate":0.58},
 "status":"complete","outcome":"kept","notes":"first sweep of gap threshold"}
```

`spec_hash` is a SHA-256 over the canonicalized full spec (universe, filters, entry, exit, sizing, cost model, date range) so identical re-runs collapse and any change to *anything* counts as a new trial. `status` ∈ {complete, errored, abandoned}; `outcome` ∈ {kept, killed, parked}. **Errored and abandoned runs still count toward `N`** if you saw any output from them.

```python
import json, hashlib, pathlib, datetime as dt
import pandas as pd

TRIALS = pathlib.Path("research/trials.jsonl")

def spec_hash(spec: dict) -> str:
    blob = json.dumps(spec, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(blob).hexdigest()

def log_trial(hypothesis_id, spec, params, split, n_events, metrics,
              status="complete", outcome="parked", notes=""):
    rec = dict(trial_id=hashlib.sha256(
                   f"{dt.datetime.utcnow().isoformat()}{spec_hash(spec)}".encode()).hexdigest()[:16],
               ts=dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
               hypothesis_id=hypothesis_id, spec_hash=spec_hash(spec),
               params=params, split=split, n_events=n_events, metrics=metrics,
               status=status, outcome=outcome, notes=notes)
    with TRIALS.open("a") as f:
        f.write(json.dumps(rec) + "\n")
    return rec

def load_trials(path=TRIALS) -> pd.DataFrame:
    rows = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    df = pd.json_normalize(rows)
    return df

def trial_count(df, hypothesis_id=None, family=None):
    """N for multiple-testing correction. Distinct specs, all statuses."""
    sub = df if hypothesis_id is None else df[df.hypothesis_id == hypothesis_id]
    if family is not None:
        sub = sub[sub.hypothesis_id.isin(family)]
    return sub.spec_hash.nunique()
```

Report two counts: `N_hypothesis` (variants inside one idea — the number that deflates that idea's Sharpe) and `N_program` (every trial you have ever run — the number that governs how many of your *portfolio* of surviving strategies are real).

### 4.3 Multiplicity Corrections

| Method | Controls | Use when | Verdict |
|---|---|---|---|
| Bonferroni: `α/N` | FWER | Small `N`, final gate | Too conservative, but a useful hard floor |
| Holm–Bonferroni | FWER | Same, uniformly more powerful | Prefer over plain Bonferroni |
| Benjamini–Hochberg | FDR | Screening many hypotheses | The working default at `q = 0.10` |
| Deflated Sharpe Ratio | Selection bias in SR | Reporting the *winner* of a sweep | Mandatory on every survivor |

```python
from statsmodels.stats.multitest import multipletests
reject, p_adj, _, alpha_bonf = multipletests(pvals, alpha=0.10, method="fdr_bh")
```

Use BH within a *family* — the set of variants of one hypothesis, or the set of distinct hypotheses at final gating — never across a mixed bag chosen after the fact. At the holdout gate use Holm at `α = 0.05`.

**Deflated Sharpe Ratio (DSR).** The Probabilistic Sharpe Ratio asks: what is the probability the true Sharpe exceeds a benchmark `SR*`, given non-normal returns?

```
PSR(SR*) = Z[ ((SR̂ - SR*) · sqrt(T - 1)) / sqrt(1 - γ₃·SR̂ + ((γ₄ - 1)/4)·SR̂²) ]
```

where `SR̂` and `SR*` are **per-period** (same frequency as the return series), `T` is the number of returns, `γ₃` is skew, `γ₄` is non-excess kurtosis, `Z[·]` the standard normal CDF. DSR sets the benchmark to the expected best-of-`N`-under-the-null from §4.1:

```
SR* = sqrt(Var[SR_n]) · [ (1-γ)·Z⁻¹(1 - 1/N) + γ·Z⁻¹(1 - 1/(N·e)) ]
DSR = PSR(SR*)
```

`Var[SR_n]` is the variance of the Sharpes across your `N` trials — which you have, because you logged them. Inputs: **N trials, skew, kurtosis, sample length, cross-trial Sharpe variance.**

What DSR proves: that your headline Sharpe is unlikely under the null *given the amount of searching you admitted to*. **What it does not prove:** that the edge is real out of sample, that your trials were independent, that your cost model is right, or that you counted `N` honestly. DSR is a deflator, not an oracle. Threshold: **DSR ≥ 0.95** to advance. Negatively-skewed, fat-tailed option-selling returns get punished hard by the denominator — correctly.

### 4.4 CSCV and the Probability of Backtest Overfitting

DSR corrects a number. PBO answers a different question: **when I pick the in-sample best configuration, how often is it worse than median out of sample?** That is the operational definition of overfitting.

Combinatorially Symmetric Cross-Validation:

1. Build an `T × K` matrix `M` of per-period returns: one column per configuration you swept.
2. Split rows into `S` contiguous, equal blocks (`S = 16` typical).
3. For each of the `C(S, S/2)` ways to choose `S/2` blocks as in-sample (12,870 for S=16), the complement is out-of-sample.
4. In-sample: pick `k* = argmax` Sharpe. Out-of-sample: compute the *relative rank* `r` of `k*` among all `K` configs, `r ∈ (0,1)`.
5. Logit `λ = ln(r / (1 - r))`. **PBO = fraction of splits with `λ ≤ 0`**, i.e. in-sample winner lands below the OOS median.

```python
import numpy as np, itertools
from scipy.stats import rankdata

def pbo(M, S=16):
    blocks = np.array_split(np.arange(M.shape[0]), S)
    lam = []
    for comb in itertools.combinations(range(S), S // 2):
        is_idx = np.concatenate([blocks[b] for b in comb])
        os_idx = np.concatenate([blocks[b] for b in range(S) if b not in comb])
        sr = lambda X: X.mean(0) / (X.std(0, ddof=1) + 1e-12)
        k = int(np.argmax(sr(M[is_idx])))
        r = rankdata(sr(M[os_idx]))[k] / (M.shape[1] + 1)
        lam.append(np.log(r / (1 - r)))
    lam = np.array(lam)
    return (lam <= 0).mean(), lam
```

Also plot IS Sharpe vs OOS Sharpe across splits and fit a line: a **negative slope** is the signature of a configuration space where optimization actively hurts. **Accept at PBO ≤ 0.35** (hard reject above 0.50 — you are worse than a coin flip). PBO requires `K ≥ ~20` configurations; if you only ever ran three, you cannot compute it and must lean harder on §4.5–4.6.

### 4.5 The Parameter Plateau Doctrine

Every free parameter is a dimension you searched, and every searched dimension inflates the max. The defense is not fewer sweeps — it is demanding that the surface be *flat*.

**Rules:**

1. **Sweep everything.** No parameter ships without a 1-D sweep plot of the headline metric vs the parameter over a range at least 3 steps either side of the chosen value. Two-parameter interactions get a heatmap.
2. **Plateau criterion.** The metric at **±1 step** must retain **≥ 80%** of the peak, and at **±2 steps ≥ 60%**. A spike that collapses to half one step over is noise-fitting, period.
3. **Pick the plateau center, not the peak.** If the plateau is 5–9 days, ship 7, not the 8 that happened to score best.
4. **Sign coherence.** The metric should move monotonically or unimodally across the sweep. A sawtooth surface means your effective sample per bucket is too small.
5. **Budget: ≥ 50 independent events per free parameter, and ≥ 100 events total.** Fewer than that and the sweep is decorative. Count *independent* events — overlapping option holding periods do not count separately.
6. **More than 3 free parameters ⇒ presumed overfit.** Shipping a 4th requires either a mechanistic argument for why it must exist, or the event budget for it (≥ 200 events for 4). Parameters fixed by convention or liquidity (e.g. 30-delta because that is where the quotes are) are declared as *constrained*, not free, in the registration — and you may not later tune them.

### 4.6 Adversarial Tests

Run **all seven** on every hypothesis that survives to the holdout gate. Each is a null your edge must break.

| # | Test | Construction | Pass criterion |
|---|---|---|---|
| a | **Random-trigger permutation** | Replace real triggers with the same number of random dates, matched on regime/month; 1,000 draws | Real metric > 99th pct of null (`p < 0.01`) |
| b | **Synthetic paths** | Block bootstrap (`arch.bootstrap.StationaryBootstrap`) or IID-bootstrap of returns; preserves vol, fat tails, autocorr but destroys the specific structure. Re-run the *full* strategy on 500 synthetic histories | Real Sharpe > 95th pct of synthetic distribution |
| c | **Placebo universes** | Run on 20 unrelated tickers where the mechanism predicts **no** edge, and on tickers where it predicts the edge **should** appear | Effect absent (\|t\| < 2) in placebo set; **present in the predicted set — this is the confirmatory half and is worth more than any p-value** |
| d | **Time-shift placebo** | Fire the setup at T-1 and T+1 relative to the real trigger | Edge collapses to ≤ 25% of real at both shifts. Surviving both shifts means you found a regime, not an event |
| e | **Sign flip** | Negate the trigger condition (gap down instead of up) | Effect reverses sign, or is flat if the mechanism is directional-agnostic — *some* coherent response, not the same result |
| f | **Leave-one-out** | (i) drop each calendar year in turn; (ii) drop the best decile of trades by PnL | (i) ≥ 70% of years individually positive, no single year supplying > 50% of total PnL; (ii) edge remains positive after removing the top decile |
| g | **Cost sensitivity** | Sweep total round-trip cost (half-spread + fees + slippage + assignment); find the multiple `c*` of your realistic cost estimate at which mean net PnL hits zero | **`c* ≥ 3.0`.** Below 2.0, kill it — you have found a spread, not an edge |

Test (f-ii) is the most-failed. Test (g) kills most short-dated options ideas and should be run *early*, not last.

### 4.7 The Story Test

Before any hypothesis is promoted, write two sentences in the registration:

1. **Who is on the other side and why are they there?** (A dealer hedging gamma into the close. A fund mechanically rolling covered calls on the third Friday. A retail buyer paying up for lottery convexity before earnings. An index fund forced to trade at the close.)
2. **What am I being paid for?** Name the risk you bear (gap risk, jump risk, carrying overnight vega, tail exposure) or the structural constraint you are arbitraging (mandate limits, margin rules, tax dates, index-rebalance calendars, settlement mechanics).

If you cannot fill both in without hedging language, **the hypothesis fails, regardless of its statistics.** This is not aesthetic. The prior probability that a genuine, exploitable, unrecognized anomaly exists in a market with millions of participants is low; the probability that a strategy which passed your filters is a survivor of your own search is high. Bayes does the rest: without a mechanism, the posterior stays near zero no matter how good the p-value looks. A mechanism also tells you *when the edge will stop working* — when the counterparty leaves, when the constraint is relaxed — which is the only real risk management you have.

Grade mechanism strength as **Strong** (identified counterparty and documented constraint, edge sizes proportional to the friction), **Weak** (plausible story, no direct evidence), or **None** (post-hoc narrative). None is an automatic no-go.

### 4.8 Research Hygiene: Code of Conduct

1. **The holdout is touched once, ever, per hypothesis id.** Not to "sanity check," not to debug. Looking at it converts it into training data permanently.
2. **No re-specification after seeing results.** If a result makes you want to change the rule, you have learned something — but you must **fork a new hypothesis id** (`H014` → `H014b`), register it before running, and it inherits the parent's full trial count as its starting `N`. Silent editing is the cardinal sin.
3. **Log before you look.** Append the trial record at launch, write metrics on completion. This makes it structurally impossible to forget failed runs.
4. **Cooling-off: 90 days.** A killed hypothesis cannot be re-tested for 90 days, and only then with genuinely new data or a genuinely new mechanism — recorded as such. Repeatedly re-testing a dead idea is multiple testing spread over time, and it is invisible to every correction above.
5. **Post-mortem before deletion.** No branch, notebook, or dataset is deleted before a dated post-mortem is written: what was hypothesized, what killed it, which test caught it, what you would need to see to revisit. Your kill file is a more valuable asset than your strategy file.
6. **One analyst, one clock.** Do not run exploratory sweeps and confirmatory tests in the same session. Separate scripts, separate splits, separate log entries.
7. **Freeze the cost model before the sweep**, not after seeing which cost assumption makes the result work.

### 4.9 Overfitting Risk Scorecard

Fill this in per hypothesis and paste it into the registration before the holdout gate.

| Field | Source | Green | Yellow | Red |
|---|---|---|---|---|
| `N_hypothesis` (distinct specs) | `trial_count()` | ≤ 20 | 21–100 | > 100 |
| `N_program` at time of test | `trials.jsonl` | — | — | disclose |
| Free parameters | Registration | ≤ 2 | 3 | ≥ 4 |
| Independent events / free param | `n_events / k` | ≥ 100 | 50–99 | < 50 |
| Plateau retention at ±1 step | Sweep plot | ≥ 0.90 | 0.80–0.89 | < 0.80 |
| Deflated Sharpe Ratio | §4.3 | ≥ 0.95 | 0.90–0.95 | < 0.90 |
| PBO | §4.4 | ≤ 0.20 | 0.21–0.35 | > 0.35 |
| Adversarial tests passed (of 7) | §4.6 | 7 | 6 | ≤ 5 |
| Cost multiple to death `c*` | §4.6g | ≥ 5.0 | 3.0–4.9 | < 3.0 |
| Mechanism strength | §4.7 | Strong | Weak | None |
| Years positive (LOYO) | §4.6f | ≥ 80% | 70–79% | < 70% |

**Decision rule: any Red ⇒ no-go.** More than two Yellows ⇒ no-go. Zero Reds and ≤ 2 Yellows ⇒ proceed to the holdout gate — and note that passing this scorecard earns you the *right to run one holdout test*, not a live allocation.

### 4.10 A Worked Post-Mortem

§0.2's funnel takes roughly 40 candidates in and lets 1–2 out, so nearly all your research time is spent killing things and the kill is the only output most hypotheses ever produce. §4.8.5 makes the post-mortem mandatory before deletion; this section says what one contains.

**Three consumers, none of them you-today.** (1) *Future you*, who will have this idea again in eight months from a different source and needs the registry to answer it in thirty seconds instead of two weeks (§2.11). (2) *The registry*, whose `cause_of_death` codes cluster — five deaths by `COSTS_EXCEED_EDGE` is one finding about your cost model, not five failures. (3) *The multiple-testing denominator* — a forgotten test still inflates `N_program` (§4.2); the post-mortem keeps those trials attached to a story. And the cause of death is frequently the seed of the next hypothesis, legible only while the diagnosis is fresh.

#### The worked example

> **Illustrative.** No backtest has been run. Every number below is invented to show the shape of a real post-mortem; only the sample-size figures are the measured ones from the §2.9b pre-flight.

```
HYPOTHESIS POST-MORTEM
id:             H-2026-014  (seed candidate VT-03)
name:           rv_mean_reversion_post_spike
registered_utc: 2026-08-24T09:12:00Z
killed_utc:     2026-10-02T16:40:00Z
batch:          2026Q3-B2
status:         REGISTERED -> STAGE1 -> RETIRED
slices used:    STAGE1 (1993-01..2022-12). HOLDOUT (2023+) NEVER UNSEALED.
spec hashes:    sha256:4b71a0.. (base, flag RV5/RV60>2.0, entry T+3, horizon 10d)
                sha256:9ee312.. (entry T+5)
                sha256:c0aa47.. (flag threshold 1.75)
                sha256:71d5f9.. (flag threshold 2.50)
                sha256:2f8b6c.. (horizon 21d)
                + 6 further variants, all logged in trials.jsonl
N_hypothesis:   11 distinct specs (budget 12, §4.2)
N_program:      143 at time of kill
```

**Claim (one sentence).** After a realized-vol spike, implied vol decays more slowly than realized vol does, so the IV−RV gap widens in the days following the flag and short vol entered 3–5 days after the flag is paid for a reversion the market has not priced.

**Pre-registered falsification.** "Dead if VIX's post-flag path sits at or below the HAR-implied decay path, i.e. mean (VIX_path − HAR_forecast) over the 10 days after entry is ≤ +1.5 vol points on STAGE1."

**What was measured** (base spec `4b71a0`, STAGE1, outcome = mean VIX minus HAR-implied RV forecast, 10 days post-entry, vol points):

| Quantity | Measured | §3.8 gate | Verdict |
|---|---|---|---|
| Raw trigger events | 934 | ≥ 50 | Pass |
| Independent clusters | **71** | ≥ 20 | Pass |
| Effect size | **+0.62 vp** | ≥ 3.0 vp (3× the 1.0 vp vol-trade cost placeholder) | **FAIL — 4.8× short** |
| Permutation p (block, run-length matched, 10,000 draws) | 0.14 | ≤ 0.01 | **FAIL** |
| HAC t-stat (maxlags = 10) | 1.31 | ≥ 2.5 | **FAIL** |
| Sign consistency, years with ≥5 events | 17/26 = 65% | ≥ 70% | **FAIL (marginal)** |
| Sign consistency, regime terciles | 2/3 | ≥ 2/3 | Pass |
| Leave-out-best-year (drop 2008) | +0.18 vp = **29% retention**, p = 0.51 | ≥ 60%, p ≤ 0.05 | **FAIL** |
| Top-3 removal | 41% retention | ≥ 50% | **FAIL** |
| One-extra-bar delay | 88% retention | ≥ 70% | Pass |

**The gate that decides it.** The effect-size-vs-costs gate, failed by the widest margin: +0.62 vol points against a 3.0 vol-point requirement. Everything else is corroboration — but note that leave-out-best-year is the *diagnostic* failure. Dropping 2008 alone removes 71% of the effect, which means the headline number is one crisis wearing a 26-year costume. Best variant across all 11 specs (flag 1.75, entry T+5) reached +0.94 vp at p = 0.06; §4.1 says the expected best of 11 correlated noise trials looks about like that, so it is not a rescue.

**Diagnosis — and the distinction that matters.** The pre-registered claim was **+1.5 to +3.0 vol points**. The standard deviation of the 10-day (VIX − HAR) residual on this sample is 2.4 vp, so the minimum detectable effect at 80% power on 71 independent clusters is

```
d_min = sqrt(15.7 / 71) = 0.47   ->   MDE = 0.47 x 2.4 = 1.13 vol points
```

`MDE (1.13) < prior low end (1.5)`. **The sample was powered to see the effect the spec claimed, and it was not there.** That is `NO_EFFECT` and it closes the question. Had the arithmetic gone the other way — MDE above the claimed effect — the correct verdict would have been `INSUFFICIENT_SAMPLE` with no statement about the world at all.

The measured +0.62 vp sits *below* the MDE and so is itself unresolvable; it may be real. It does not matter, because it is a fifth of the cost gate. An effect too small to resolve and too small to pay the spread is closed permanently, not parked.

**What is reusable.** (i) The Yang-Zhang RV estimator and HAR fit in `research/vol/har.py`, now the baseline forecast for VRP-01 and VT-01 — most of the value this hypothesis produced. (ii) The run-length-matched block permutation (§3.6 refinement i): naive permutation returned p = 0.008 here, the block version 0.14, a 17× difference that would have promoted a dead idea. (iii) Confirmation of the §2.9b general lesson — 1,165 raw events collapse ~14× to 86 clusters because elevated vol *persists*. State-based triggers are sample-poor by construction.

**Successor question.** The state trigger fires throughout an episode and buys nothing beyond its first day. Does the *first crossing* of `RV5/RV60` through 2.0 — a point event, one per episode, ~86 of them — carry information the persistent state washes out? Registered as **H-2026-021** `rv_reversion_first_crossing`, inheriting these 11 trials as its starting `N` per §4.8.2. Pre-flight first: 86 clusters against an MDE of 1.03 vp is thin, and if the prior effect size cannot honestly be written above that number, do not register it.

**Cause of death:** `NO_EFFECT`. **Successor:** `H-2026-021`.

#### `NO_EFFECT` vs. insufficient power

These are opposite verdicts and are constantly conflated. §2.11 spells the power verdict `INSUFFICIENT_SAMPLE`; it means *the study never had the resolution to answer the question*, says nothing about the market, and leaves the question open — re-test when more data exists, and record how much is needed. `NO_EFFECT` means *the study could have seen the claimed effect and did not*, and closes the question permanently.

The rule, mechanical, computed before you write the verdict:

```
sigma      = SD of the per-event outcome
n          = INDEPENDENT CLUSTERS (never raw events)
MDE        = sqrt(15.7 / n) * sigma            # §3.6, alpha=0.05, power=0.8
prior_low  = low end of prior_effect_size in the §2.7 spec

MDE <= prior_low   ->  NO_EFFECT             (closed; do not re-register)
MDE >  prior_low   ->  INSUFFICIENT_SAMPLE   (open; record n_required =
                                              15.7 / (prior_low/sigma)^2
                                              and the calendar year the trigger
                                              frequency will supply it)
```

Two corollaries. Without a numeric `prior_effect_size` in the spec you can compute neither verdict — which is why §2.7 makes the field required. And an `INSUFFICIENT_SAMPLE` death indicts the §2.9 pre-flight: the MDE was computable before any trial was burned and should have killed the candidate there.

#### The template

Copy to `results/<id>/<spec_hash>/postmortem.md`, front-matter first, prose under the headings.

```yaml
id:                 # hypothesis id, matching the registry
name:               # spec `name` field
registered_utc:     # from the spec
killed_utc:         # when the verdict was written, not when you lost interest
batch:              # generation batch, so death clusters by cohort
status_path:        # REGISTERED -> STAGE1 -> RETIRED
slices_used:        # which splits were touched; state explicitly if HOLDOUT is intact
spec_hashes:        # EVERY variant run, one per line, with its parameter delta
n_hypothesis:       # distinct specs (§4.2); trial budget and whether it was hit
n_program:          # program-wide trial count at time of kill

claim:              # the hypothesis in one sentence
falsification:      # verbatim from the spec's `falsification` field — not paraphrased
results_table:      # measured vs §3.8 gate vs pass/fail, every gate, no omissions
gate_failed:        # the specific gate and the numeric margin
best_variant:       # best result across all variants, vs the §4.1 best-of-N noise level
sigma:              # SD of the per-event outcome
n_clusters:         # independent clusters, not raw events
mde:                # sqrt(15.7/n)*sigma
prior_low:          # low end of prior_effect_size from the spec
verdict_logic:      # MDE vs prior_low, and which of the two verdicts follows
diagnosis:          # WHY it failed, in mechanism terms, not statistics terms
reusable:           # code, data, negative facts other hypotheses inherit
successor_question: # what the failure suggests testing next
successor_id:       # new id if registered, or "none — and why not"
cause_of_death:     # §2.11 controlled vocabulary, exactly one code
n_required:         # INSUFFICIENT_SAMPLE only: clusters needed, and the year they arrive
revisit_after:      # killed_utc + 90 days (§4.8.4)
revisit_condition:  # what new data or new mechanism would justify it
```

#### Filing rules

1. **Location:** `results/<id>/<spec_hash>/postmortem.md`, under the hash of the *base* spec, so it is content-addressed alongside the run outputs it describes (§1.1).
2. **Written before anything is deleted.** No branch, notebook, cached dataset, or results directory is removed until the post-mortem is committed (§4.8.5). Delete the artifacts, keep the finding.
3. **The registry links to it.** `scripts/build_registry.py` fills `cause_of_death`, `successor_id`, and a `notes` link to the post-mortem path. A `RETIRED` row with no linked post-mortem is a build failure, not a warning.
4. **Cooling-off is 90 days** (§4.8.4), applied to the *idea*, not the id — re-registering the same trigger under a new name to dodge the clock is the same sin as silent re-specification. Revival then requires genuinely new data or a genuinely new mechanism, named in the new spec's `rationale`, and the new id inherits the dead one's trial count.
5. **Review the death ledger before generating each batch** (§2.11). Post-mortems are what make that review say something.

---

## 5. Translating a Validated Premise into an Options Structure

### 5.1 The translation problem

A Stage-1 result is not a trade. It is a **conditional distribution**: given trigger condition $C$ at time $t$, the underlying's forward return over horizon $h$ has some drift $\mu(C,h)$, dispersion $\sigma_{RV}(C,h)$, path character, and tail shape. Section 4 told you that distribution is not an artifact of your search process. It did not tell you how to get paid on it.

An option does not pay off on the underlying's return. It pays off on a **nonlinear functional of the entire distribution and path**, decomposed by the P&L identity:

$$\Delta P \approx \Delta\cdot dS + \tfrac{1}{2}\Gamma\,(dS)^2 + \Theta\,dt + \mathcal{V}\,d\sigma_{imp} + \text{(higher order)}$$

Every term is a separate bet. Your edge lives in exactly one or two of them. The other terms are noise you are forced to carry, and each one has a cost of carry (theta) or a variance contribution (vega) that can be larger than your edge.

> **Governing principle: maximize exposure to the Greek you have an edge in; neutralize the ones you don't.**

This is the whole section in one line. A directional edge with no vol edge that is expressed as a long ATM call is a *joint* bet on direction and on IV ≥ RV — and you have evidence for only half of it. A vol edge expressed as an unhedged short strangle is a joint bet on vol and on the underlying not drifting — and you have evidence for only half of it. Structure selection is the process of stripping the unsupported halves out.

The secondary constraint: **structures with the same Greek sign are not interchangeable**, because they differ in max loss, margin, path sensitivity, and failure mode. Two structures can both be "short vol" and have opposite behavior in the scenario that actually shows up.

### 5.2 Characterizing your edge: the five-question intake

Run this on your Stage-1 output *before* looking at any option chain. The answers determine everything downstream. Each answer must be a number computed from your trigger dates, not an opinion.

**(a) Directional, vol-only, or both?**
Compute, over the $N$ historical trigger dates, the mean signed forward return $\bar r_h$ and its standard error $s/\sqrt N$. If $|\bar r_h| / (s/\sqrt N) < 2$, you have **no directional edge** — treat it as vol-only regardless of how the equity curve looked. Separately compute the conditional realized vol $\sigma_{RV}(C,h)$ against the unconditional. You can have both, but you must size them separately.

**(b) Expected magnitude vs. the priced move.**
The absolute number is meaningless; the ratio is everything. See §5.3.

**(c) Horizon and path.**
Two edges with the same 10-day return have completely different optimal structures if one is a day-1 gap and the other is a 10-day grind. Compute, on trigger dates, the mean cumulative return curve $\bar r(1), \bar r(2), \ldots, \bar r(h)$ and the **path efficiency** = $|\bar r(h)| \,/\, \mathbb{E}[\sum_{i=1}^{h}|r_i|]$. Efficiency > 0.5 = trending/pop (gamma and delta both work). Efficiency < 0.2 = choppy drift (long gamma bleeds; long delta or a vertical is better). Also compute the mean **maximum adverse excursion** — this sets your strike distance and whether a short-premium structure survives.

**(d) Is IV rich or cheap, conditionally?**
IV rank and IV percentile are weak: they are unconditional, backward-looking, and dominated by the vol-of-vol regime rather than by your setup. The correct statistic is the **conditional variance risk premium over your exact holding horizon**, computed on your trigger dates only:

$$\text{VRP}(C,h) = \mathbb{E}\big[\sigma_{imp}(t, h) - \sigma_{RV}(t \to t+h)\;\big|\;C\big]$$

where $\sigma_{imp}$ is the ATM IV for a tenor matching $h$ at the trigger timestamp and $\sigma_{RV}$ is the close-to-close (or Yang–Zhang) realized vol over exactly the subsequent $h$ days. Report the mean, the standard error, and the fraction of triggers where it was positive. A VRP of +4 vol points with 70% hit rate is a tradeable short-vol edge. An IV rank of 80 is not.

**(e) Tail shape.**
Compute conditional skewness and the 1st/99th percentile of the forward return on trigger dates. Ask specifically: *does this edge have a fat loss tail?* Short-premium edges almost always do. If the conditional 1st percentile is more than 3× the conditional mean absolute move, you must use a defined-risk structure (spread, condor, butterfly) rather than a naked short, regardless of what the expectancy says.

### 5.3 The move/premium ratio

The central decision statistic. For your exact horizon $h$:

$$R \;=\; \frac{\text{conditional expected move from Stage 1}}{\text{ATM-straddle implied expected move}}$$

For a lognormal with zero drift, $\mathbb{E}|S_T - S_0| = S\sigma\sqrt{2T/\pi} = 0.7979\,S\sigma\sqrt{T}$, which is also the Black–Scholes ATM straddle value to first order. So the market's implied expected move is well approximated by the straddle mid, or equivalently $\text{EM} \approx 0.80\,S\,\sigma_{imp}\sqrt{T}$ (many desks use $0.85\times$ straddle to correct for the discrete-strike/skew wedge — use the straddle mid directly when you have quotes).

Use **signed** drift over EM for directional edges ($R_{dir} = \bar r_h S / \text{EM}$) and **absolute** move over EM for vol edges ($R_{vol} = \mathbb{E}[|r_h|]S / \text{EM}$). Report both.

| $R_{vol}$ | Reading | Implied structure family | Notes |
|---|---|---|---|
| < 0.60 | Strongly overpriced premium | Delta-hedged short straddle; short strangle; iron condor; calendar (if term structure agrees) | Only if MAE tail is bounded; use defined risk |
| 0.60 – 0.85 | Mildly overpriced | Credit vertical (if directional), iron condor, covered/ratio structures | Thin edge; transaction costs matter most here |
| 0.85 – 1.15 | Fairly priced | **None.** If you also have a directional edge, trade shares/futures, or a debit vertical to cap cost | Options add cost without adding edge |
| 1.15 – 1.60 | Underpriced | Debit vertical, long option, risk reversal | Verify with path efficiency — grinding paths kill long premium |
| > 1.60 | Strongly underpriced / convexity | Long straddle/strangle, ratio backspread, OTM long options | Usually event-driven; check you are not just mismeasuring the event |

$R_{dir}$ interpretation runs alongside: $|R_{dir}| > 0.5$ with $R_{vol}$ near 1 means a clean directional edge that should be expressed with delta, not gamma. $|R_{dir}| < 0.2$ with $R_{vol} > 1.5$ means pure convexity — a straddle, not a call.

### 5.4 The structure selection matrix

Split into two tables over the same rows.

**A. What it expresses**

| Structure | Edge it expresses | Primary Greek | IV regime it wants | Horizon it wants |
|---|---|---|---|---|
| Long call / put | Directional + long vol, jointly | Delta, then gamma & vega | Cheap conditional IV (VRP < 0) | Short–medium; fast move |
| Debit vertical | Directional, magnitude-capped, vol-neutralized | Delta | Neutral to rich (short leg funds it) | Matched to horizon; low path sensitivity |
| Credit vertical | Directional **absence** + short vol | Theta, short vega, short delta-tail | Rich IV, elevated skew on the sold wing | Matched or slightly shorter |
| Long straddle / strangle | Pure magnitude, no direction | Gamma + vega | Cheap IV, or backwardated term structure | Event-dated or fast-dispersion |
| Short strangle | Pure "no move" + VRP capture | Short vega, short gamma, long theta | Rich IV, contango | Matched; exit before gamma cliff |
| Iron condor | Same as short strangle, tail-capped | Long theta, short vega (smaller) | Rich IV, range-bound conditional | Matched; 20–45 DTE typical |
| Calendar / diagonal | **Forward vol** mispricing; term-structure edge | Long vega (back), short gamma (front) | Front rich vs. back cheap (steep backwardation into an event) | Front expiry ≈ event; back = 2–3× |
| Ratio / backspread | Fat conditional tail in one direction | Long gamma far, short vega near | Skew mispriced: wing cheap vs. body | Medium; needs a big move to pay |
| Butterfly | Pinning / a *specific* terminal price | Short gamma, short vega, long theta | Rich IV **and** a point forecast | Terminal-value bet; hold near expiry |
| Risk reversal | Directional + skew mispricing, vol-cheap | Delta, short vega on one wing | Skew too steep relative to conditional distribution | Medium–long; capital-efficient |
| Delta-hedged option | **Pure realized-vs-implied vol** | Gamma/vega only (delta stripped) | Any; the cleanest VRP expression | Exactly your $h$; requires hedge discipline |

**B. How it fails**

| Structure | Path sensitivity | Max loss | Capital / margin | Failure mode that kills it |
|---|---|---|---|---|
| Long call / put | High — needs move *before* decay | Premium | Small debit | Right direction, too slow: theta + IV crush eats the win |
| Debit vertical | Low | Net debit | Debit | Move overshoots the short strike; you capped the fat right tail |
| Credit vertical | Low–moderate | Width − credit | Width − credit (defined) | Gap through both strikes; you lose 4–6× the credit at once |
| Long straddle / strangle | Very high — chop is fatal | Premium | Two debits | Realized moves happen but *round-trip*; terminal move ≈ 0 |
| Short strangle | High near expiry | Theoretically unbounded | Large, SPAN/RegT; margin expands as it moves | One 4σ gap erases 30 winners; margin call forces exit at the worst tick |
| Iron condor | Moderate | Width − credit per side | Defined, modest | Credit too thin vs. width; the tails you sold are the fat ones |
| Calendar / diagonal | Moderate | Net debit (roughly) | Debit + possible margin on diagonal | Underlying leaves the strike; forward vol never realizes; front doesn't crush |
| Ratio / backspread | Moderate | Loss valley between strikes | Margin on the naked ratio leg | Underlying lands *in the valley* at expiry — the single worst outcome |
| Butterfly | Extreme near expiry | Net debit | Debit | Anything other than pinning; wide bid/ask on 4 legs |
| Risk reversal | Low | Large (short-put side is stock-like) | Margin ≈ short put | Direction wrong: you own synthetic stock with negative convexity in the crash |
| Delta-hedged option | Low in P&L, high in **operations** | Bounded by vol spread × dollar-gamma | Premium + hedge financing | Hedge slippage and discrete rebalancing dominate a thin VRP |

Two rules that fall out of the matrix: **never express a vol-only edge with an unhedged directional structure**, and **never express a directional edge with a structure whose dominant Greek is theta**.

### 5.5 Strike selection via delta

For a call with $d_1 = \frac{\ln(S/K) + (r - q + \sigma^2/2)T}{\sigma\sqrt T}$, $d_2 = d_1 - \sigma\sqrt T$:

- $\Delta_{call} = e^{-qT}N(d_1)$
- Risk-neutral probability of finishing ITM $= N(d_2)$, **not** $N(d_1)$.

So delta *overstates* the risk-neutral ITM probability by roughly $\phi(d_1)\sigma\sqrt T$. For a 30-day 25-delta call at 20% vol that gap is ~2–3 points. More importantly, $N(d_2)$ is a **risk-neutral** probability: it assumes drift $r-q$ and dispersion $\sigma_{imp}$. Your Stage-1 distribution has drift $\mu(C,h)$ and dispersion $\sigma_{RV}(C,h)$. When $\sigma_{imp} > \sigma_{RV}$ (the normal case), the risk-neutral distribution is *wider* than yours — which is exactly why short-premium structures have real-world POP above what the chain implies.

**The rule: pick strikes so the structure's breakevens sit outside the bulk of your conditional distribution (short premium) or inside it (long premium), measured on your empirical trigger-date returns — never on the lognormal.**

Practical starting deltas by intent:

| Intent | Strike choice |
|---|---|
| Long directional, high conviction | 55–65Δ (mostly intrinsic, low theta/premium ratio) |
| Long directional, convexity-seeking | 25–35Δ long leg |
| Debit vertical | Buy 50–60Δ, sell at the **conditional 75th percentile** of your move distribution |
| Credit vertical / condor short leg | 15–25Δ, then verify against your empirical tail, not $N(d_2)$ |
| Short strangle | 10–16Δ each side; asymmetrize if $\bar r_h \neq 0$ |
| Butterfly body | At your conditional *modal* terminal price |
| Risk reversal | 25Δ / 25Δ, sized so net vega ≈ 0 |

Worked POP under your own distribution:

```python
import numpy as np
from scipy.stats import norm

S, K_short, K_long, T, iv = 500.0, 512.5, 520.0, 7/365, 0.18
# Empirical conditional 5-day log returns from Stage 1 (N trigger dates)
r_cond = np.load("cond_returns_5d.npy")          # shape (N,)
credit = 1.04 - 0.27                              # per share, from the chain

ST   = S * np.exp(r_cond)                         # empirical terminal prices
pnl  = credit - np.clip(ST - K_short, 0, K_long - K_short)
print("empirical POP :", (pnl > 0).mean())
print("empirical EV  :", pnl.mean())

d2 = (np.log(S/K_short) + (-0.5*iv**2)*T) / (iv*np.sqrt(T))
print("risk-neutral P(ITM short leg):", 1 - norm.cdf(d2))
```

Report both numbers. If empirical POP is not materially better than $1 - N(d_2)$, the strikes are not expressing your edge — you are just selling variance at market terms.

### 5.6 Expiry selection: the gamma/theta tradeoff

For an ATM option (set $r=q=0$ for clarity):

$$\Gamma = \frac{\phi(d_1)}{S\sigma\sqrt T} \propto T^{-1/2},\qquad \Theta = -\frac{S\phi(d_1)\sigma}{2\sqrt T} \propto T^{-1/2},\qquad \mathcal{V} = S\phi(d_1)\sqrt T \propto T^{1/2}$$

The key identity:

$$\frac{\Theta}{\Gamma} = -\frac{S^2\sigma^2}{2}\quad\Longrightarrow\quad \text{daily breakeven move} = \frac{S\sigma}{\sqrt{365}}$$

**Gamma is not cheaper in any expiry.** The theta you pay per unit of gamma is identical across tenors for ATM options; the daily move you need to break even is exactly the implied daily vol. What changes with $T$ is (i) **vega**, which grows as $\sqrt T$, and (ii) the *convexity of decay* — theta accelerates as $T^{-1/2}$, so the last 20% of the life carries a disproportionate share of the bleed and the largest gamma whipsaw.

Consequences:

- **"Buy more time than you need" costs vega.** You are long a vol position you have no evidence for. A 90-day option to express a 5-day edge is ~4× the vega per unit of gamma, so a 2-point IV drop can dominate your entire directional gain.
- **"Buy exactly enough" costs gamma-decay risk.** If the edge arrives one day late, or the move happens on the last day, you own an option whose gamma is exploding and whose theta is exploding with it. Pin risk and assignment risk join in.

**Buffer rule.** Let $h$ be the mean edge horizon and $s_h$ its standard deviation across triggers.

- **Long premium:** $\text{DTE} \ge h + 1.5\,s_h + 3$ trading days, and target $\text{DTE} \approx 1.5\text{–}2.5\times h$. Plan to exit at $\ge 0.4\times$ original DTE remaining — sell the option, don't ride the decay cliff.
- **Short premium:** $\text{DTE} \approx 1.0\text{–}1.3\times h$, exit at 50–60% of max profit or at $h$, whichever first. Do not carry short gamma into the final 3 days for a signal whose horizon already expired.
- **Event trades:** use the **first expiry after the event**. It maximizes the event's share of total variance (see §5.7) — which is what you want if you are *selling* the event, and what you must pay for if you are buying it.

| Edge horizon | Expiry scale | Dominant risk to manage |
|---|---|---|
| Intraday / single event day | 0DTE–2DTE | Gamma and slippage; vega ≈ irrelevant |
| 2–10 days | Weeklies, 7–21 DTE | Gamma/theta balance; weekend decay |
| 2–8 weeks | Monthlies, 30–60 DTE | Vega is now first-order; term structure matters |
| 3–18 months | Quarterlies / LEAPs | Vega, skew, borrow/dividends dominate; gamma is negligible |

### 5.7 Volatility diagnostics at trigger time

Run these four at every trigger, in the backtest and live. They decide *which* of the qualifying structures is right.

**Term structure.** Fit ATM IV against tenor. Contango (front < back) is the normal state and mildly favors selling the front / calendars. Backwardation (front > back) means the market prices near-term stress. A setup that triggers *in backwardation* is usually a different animal from one that triggers in contango — split your Stage-1 sample on the sign of $\sigma_{imp}(30d) - \sigma_{imp}(7d)$ and check the edge survives in both. If it only works in one regime, that condition belongs in the trigger.

**Skew.** Summarize with the 25-delta risk reversal, $RR_{25} = \sigma_{imp}(25\Delta\text{ call}) - \sigma_{imp}(25\Delta\text{ put})$, and the butterfly $BF_{25} = \tfrac{1}{2}(\sigma_{25c} + \sigma_{25p}) - \sigma_{ATM}$. Equity index $RR_{25}$ is persistently negative (puts bid). The trade is not "skew is steep" — it is **skew is steep relative to my conditional distribution's skew**. If Stage 1 shows the conditional downside tail is *no fatter* than usual while $RR_{25}$ is at a 2-year low, you are being paid to sell the put wing. If your conditional distribution is right-skewed, buying the call wing is cheap in vol terms and the risk reversal becomes the efficient directional expression.

**Forward vol.** Between expiries $T_1 < T_2$:

$$\sigma_{fwd}^2 = \frac{\sigma_2^2 T_2 - \sigma_1^2 T_1}{T_2 - T_1}$$

A calendar is the right expression when your edge is about $\sigma_{fwd}$ — i.e. you believe the *back* expiry is cheap relative to the front, not that the underlying will or won't move. If $\sigma_{fwd}$ sits well below the historical realized vol distribution for that forward window, buy the calendar; if well above, sell it. Never put on a calendar to express a directional or a simple long/short vol view — it is a curve trade with a strike-pinning side effect.

**Event vol extraction.** Let $T_1$ contain the event and $T_2$ contain it too (or not). With $\sigma_d$ the diffusive vol and $J$ the one-day event jump std in return units:

$$\sigma_1^2 T_1 = \sigma_d^2 T_1 + J^2,\qquad \sigma_2^2 T_2 = \sigma_d^2 T_2 + J^2$$

$$\Rightarrow\;\sigma_d^2 = \frac{\sigma_2^2T_2 - \sigma_1^2T_1}{T_2 - T_1} = \sigma_{fwd}^2,\qquad J = \sqrt{\sigma_1^2T_1 - \sigma_d^2 T_1}$$

The implied event-day expected absolute move is $S\cdot J\sqrt{2/\pi} \approx 0.80\,S\,J$. Compare directly to your Stage-1 conditional event-day move. That ratio *is* $R_{vol}$ for event setups, and it is far more accurate than reading the straddle, which contains several days of ordinary diffusion.

### 5.8 Synthetic pricing for prototyping

Before you buy options data, reconstruct theoretical prices and Greeks from the underlying plus an IV estimate. This is the free path — and it is strictly a **ranking** tool.

```python
import numpy as np, py_vollib_vectorized  # monkeypatches py_vollib to accept arrays
from py_vollib.black_scholes import black_scholes as bs
from py_vollib.black_scholes.greeks.analytical import delta, gamma, theta, vega

S  = np.array([500.0, 500.0]); K = np.array([512.5, 487.5])
t  = np.array([7/365, 7/365]);  r = np.array([0.05, 0.05])
iv = np.array([0.181, 0.196])   # simple skew model, see below
flag = np.array(['c', 'p'])

px = bs(flag, S, K, t, r, iv, return_as='numpy')
g  = {'delta': delta(flag,S,K,t,r,iv,return_as='numpy'),
      'gamma': gamma(flag,S,K,t,r,iv,return_as='numpy'),
      'theta': theta(flag,S,K,t,r,iv,return_as='numpy'),   # per CALENDAR DAY
      'vega' : vega (flag,S,K,t,r,iv,return_as='numpy')}   # per 1 VOL POINT
```

Note the unit conventions: py_vollib's analytical `theta` is already divided by 365 and `vega` by 100. Do not divide again.

**Where the IV input comes from, in descending order of fidelity:**
1. VIX (and VIX9D / VIX3M / VIX6M) as the SPX 30-day ATM IV term structure — good for SPX/SPY only.
2. CBOE's single-name vol indices (VXAPL, VXAZN, …) where they exist.
3. A HAR or EWMA realized-vol forecast scaled by an estimated VRP multiplier (typically 1.05–1.20 for indices, 1.0–1.15 for liquid single names), calibrated on the sample you *do* have quotes for.
4. A parametric skew overlay: $\sigma(K) = \sigma_{ATM}\big(1 + b\cdot m + c\cdot m^2\big)$ with $m = \ln(K/F)/(\sigma_{ATM}\sqrt T)$; for equity indices $b \approx -0.10$ to $-0.15$, $c \approx +0.03$ to $+0.06$. Fit $b, c$ once on any snapshot chain you can obtain.

**What this gets wrong — all of it material:**
- No real skew surface (your parametric fit misses smile dynamics, and misses them worst in the wings you actually trade).
- No bid/ask. For a 4-leg condor the round-trip spread can exceed the entire edge.
- No early exercise for American options; no dividend or hard-to-borrow adjustment.
- No liquidity, no open interest, no strike granularity — you will "trade" strikes that don't exist.
- Systematically wrong for single names, where IV proxies are worst and skew is idiosyncratic.
- No pin risk, no assignment, no expiration settlement conventions.

> **Rule: synthetic pricing ranks candidate structures against each other. It never produces a go/no-go P&L number.** Use it to answer "does the vertical or the condor express this better?" Use Section 6 to answer "is this profitable after costs?"

### 5.9 The pre-trade Greek budget

Before every structure is approved, state its Greeks **per \$1,000 of defined risk** and check that the dominant P&L driver is your edge Greek.

```python
# Attribution over a simulated hold, using Stage-1 empirical paths
dS, dt, dIV = paths[:, -1] - S, HOLD_DAYS, iv_paths[:, -1] - iv
contrib = {
    'delta': net_delta * dS,
    'gamma': 0.5 * net_gamma * dS**2,
    'theta': net_theta * dt,
    'vega' : net_vega  * (dIV * 100),
}
tot = sum(np.abs(v).mean() for v in contrib.values())
for k, v in contrib.items():
    print(f"{k:6s} mean ${v.mean():8.2f}   share of |P&L| {np.abs(v).mean()/tot:5.1%}")
```

**Acceptance rule:** the Greek your edge is about must account for ≥ 50% of mean absolute simulated P&L, and no unsupported Greek may exceed 25%. If theta explains most of the P&L on a *directional* edge, the structure is wrong — you built an income trade and attached a forecast to it. If vega dominates a *gamma* edge, you bought too much time. Fix the structure, don't rationalize the attribution.

### 5.10 Worked example, end to end

**Premise (validated in Sections 3–4):** on days when SPY closes below its lower 2σ Bollinger band and VIX9D/VIX3M > 1.05, the subsequent 5-trading-day realized vol averages **12.5%** while ATM 7-day IV at trigger averages **18.0%**. $N = 214$ triggers, mean VRP = +5.5 vol pts, SE = 0.9, positive in 71% of cases. Mean signed 5-day return = +0.31%, SE = 0.28% → $t = 1.1$.

**Intake.**
(a) $t = 1.1$ → **no directional edge**. Vol-only. (b) See below. (c) Horizon 5 days, $s_h \approx 1.5$ days; path efficiency 0.18 — choppy, so short gamma is survivable but MAE matters: mean MAE is 1.4%, 95th pct 3.6%. (d) Conditional VRP +5.5 pts, computed on trigger dates over the exact 5-day window. (e) Conditional 1st pctile 5-day return = −6.2%, versus mean |move| of 1.6% — **fat loss tail, defined risk mandatory.**

**Move/premium ratio.** $S=500$, $T = 7/365$, $\sigma_{imp}=0.18$ → EM $= 0.7979 \times 500 \times 0.18 \times \sqrt{0.0192} = \$9.95$ (1.99%). Conditional expected move at $\sigma_{RV}=0.125$ → $\$6.91$. $R_{vol} = 6.91/9.95 = \mathbf{0.69}$. Band 0.60–0.85 → mildly-to-solidly overpriced premium, no directional tilt.

**Structure.** $R_{vol} < 0.85$ + no direction → short-premium, neutral. The theoretically pure expression is a **delta-hedged short straddle**, whose P&L is $\tfrac12\int S^2\Gamma(\sigma_{imp}^2 - \sigma_{RV}^2)\,dt$ — literally the quantity Stage 1 measured. But intake (e) says fat loss tail, and daily hedging on a 5-day hold adds slippage that can exceed a 5.5-point VRP on a 7-day option. So: **iron condor**, which is the defined-risk projection of the same bet.

**Strikes.** 16Δ short legs → $K_{call} = 512.5$, $K_{put} = 487.5$ ($\pm 2.5\%$, i.e. $\pm 1.26\times$ EM, and beyond the 95th-pct MAE of 3.6%... marginally — so verify empirically). Wings 7.5 wide: long 520 call / long 480 put.

**Pricing (synthetic, flat 18% for illustration).** 512.5C = 1.04, 487.5P = 1.05, 520C = 0.27, 480P = 0.26. Net credit $= 2.09 - 0.53 = \$1.56$ → **\$156 per condor**, max loss \$750 - 156 = \$594$. Per \$1,000 of risk: **1.68 condors**.

**Expiry.** $h=5$, $s_h=1.5$ → short-premium rule gives DTE $\approx 1.0\text{–}1.3\times h$ = 5–7. Use the 7-DTE weekly. Exit at day 5 or 55% of max profit.

**Greek budget per \$1,000 risk (1.68 condors):**

| Greek | Value | Check |
|---|---|---|
| Net delta | ≈ −2 shares | Flat, as required for a vol-only edge |
| Net gamma | −3.6 shares per \$1 | −\$45 P&L on a 1% (\$5) move — the cost of being short |
| Net theta | +\$41/day at inception | ~\$205 over 5 days |
| Net vega | −\$32 per vol point | 5.5-pt VRP → ~\$176 if IV converges |

**Attribution (simulated on the 214 empirical trigger paths):** theta 44%, vega 33%, gamma 20%, delta 3% of mean |P&L|. Edge Greeks (theta + vega, the two faces of short variance) = 77% ≥ 50%. Delta 3% ≤ 25%. **Budget passes.**

**Expected value:** $\approx +\$205 - \$45 \approx +\$160$ per \$1,000 risked over 5 days, before costs — against a defined max loss of \$1,000. The condor's 4-leg bid/ask on SPY weeklies is roughly \$0.10–0.15, i.e. \$17–25 per condor, ~\$34 per \$1,000 — a 21% haircut on gross EV. That number is an estimate; **Section 6 replaces it with real quotes and real fills before this becomes a trade.**

### 5.11 Tax Treatment as a Structure Decision

> **This is not tax advice.** It is a description of long-standing features of the US federal tax code as they bear on instrument selection, written for a US retail trader. Tax law, rates, thresholds and broker reporting practice change, and treatment depends on facts this document cannot see — your account type, your state, your other positions, whether you qualify for any elective regime. Confirm current treatment with a qualified tax professional before you let any of it change a trade. Nothing below should be read as a claim about what the rules are in your tax year.

**Why this belongs in Section 5 and not an appendix.** Everything up to here optimizes pre-tax P&L. §5.4 chose structures on Greek exposure, §6.4 charged commissions and fees, §6.7 filtered on liquidity — and §5.10's worked example landed on a SPY iron condor essentially because SPY's book is tight. But the instrument you pick to express a validated premise carries a tax character, and for a high-turnover strategy the difference in tax character between two otherwise-equivalent instruments is routinely **larger than the bid/ask difference you were optimizing**. In §5.10 the 4-leg spread cost ~21% of gross EV; a difference in effective tax rate of ten points on the same P&L costs ten points of *net*, every year, with no execution skill available to reduce it.

> **After-tax expectancy is the only expectancy that matters.** Every metric in §7 — expectancy, profit factor, Sharpe, Calmar, return on capital-at-risk — is computed pre-tax. Two hypotheses with identical §7 cards are not equally good if one is expressed in an instrument taxed at ordinary rates and the other is not.

**The core distinction: Section 1256 contracts vs. equity options.** Internal Revenue Code Section 1256 covers, among other things, "nonequity options" — which generally includes exchange-listed options on **broad-based** stock indexes. SPX, XSP, NDX, RUT and similar cash-settled broad-based index products are generally Section 1256 contracts. Two consequences follow:

1. **The 60/40 split.** Gain or loss on a Section 1256 contract is generally treated as 60% long-term and 40% short-term **regardless of actual holding period** — a position opened and closed in an afternoon gets the same character as one held a year. Long-term capital rates are materially below ordinary income rates at essentially every bracket, so the blended rate on Section 1256 gains is below the ordinary rate that short-term gains attract. Sized as a mechanism rather than a number: the annual saving is approximately $0.6\times(t_{ST}-t_{LT})\times G$ on net gain $G$, where $t_{ST}$ is your ordinary marginal rate and $t_{LT}$ your long-term rate. **Look up your own two rates and compute that product** — do not take a rate figure from this document or any other.
2. **Year-end mark-to-market.** Open Section 1256 positions are generally treated as sold at fair value on the last business day of the tax year, with gain or loss recognized then and basis adjusted. This accelerates tax on unrealized gains (a cash-flow drag) and equally accelerates recognition of unrealized losses. For strategies holding nothing across the year boundary it is close to a non-event; for anything holding LEAP-scale positions (§5.6's 3–18 month row) it is not. Section 1256 results are reported separately from ordinary capital transactions, and net Section 1256 losses may be electively carried back against prior Section 1256 gains under rules whose window you should verify.

Options on **ETFs** — SPY, QQQ, IWM — and on single names are options on a *security*, not on an index, and are generally **not** Section 1256. Held under a year they produce short-term capital gain, taxed as ordinary income. For a strategy running 20–45 DTE structures, or weeklies, or 0DTE, "held under a year" describes 100% of trades. There is no holding-period discipline available that fixes this; the strategy's horizon is set by the edge (§5.6), not by the calendar.

Two boundary warnings: options on **narrow-based** indexes are generally treated as equity options, not Section 1256, and the broad/narrow determination is a legal test, not a naming convention. And Section 1092 straddle rules can defer losses on offsetting positions held across instruments — relevant the moment you hedge an index position with an ETF position. Both are professional questions.

| Instrument | Settlement (see §6.5) | General tax character | Year-end MTM | Practical implication at high turnover |
|---|---|---|---|---|
| SPX / SPXW | European, cash-settled; monthly AM vs. SET, weeklies PM | Generally Section 1256 — 60/40 | Yes | Best case: full 60/40 on every trade, no assignment, no wash sales. Large notional per contract |
| XSP (Mini-SPX) | European, cash-settled, PM | Generally Section 1256 — 60/40 | Yes | Same treatment at ~1/10 SPX notional. The small-account route to Section 1256 |
| NDX / RUT | European, cash-settled | Generally Section 1256 — 60/40 | Yes | Same as SPX; verify the specific product is broad-based |
| SPY / QQQ / IWM options | American, physically settled, PM | Generally **not** Section 1256 — short-term for sub-1-year holds | No | Tightest books, smallest notional, worst tax character. Also carries early-assignment and dividend risk (§6.5) |
| Single-name equity options | American, physically settled | Generally **not** Section 1256 — short-term | No | Worst on both axes: ordinary-rate taxation *and* wash-sale exposure *and* assignment risk |
| Underlying ETF/stock shares | n/a | Short-term unless held > 1 year | No | The delta-hedge leg of a Section 1256 index option is *not* Section 1256 — hedging can mix characters and invoke straddle rules |

**The decision rule.** Turnover is the multiplier. Let $T$ be trades per year and $G$ expected annual net gain from the strategy. The tax delta between an index and an ETF expression is roughly $0.6\times(t_{ST}-t_{LT})\times G$ — it scales with $G$, and $G$ scales with $T$. So:

- **Prefer the Section 1256 index expression** when the strategy is high-turnover (weekly or faster cadence), taxable, and the index product clears §6.7's liquidity filters at your size. This is the common case for index-premium strategies, and it should override a marginal liquidity preference for SPY.
- **Do not let tax override liquidity** when the index book cannot absorb your size, when the spread differential is large enough to exceed the tax delta on a per-trade basis (compute it: tax saving per trade vs. incremental slippage per trade, both in dollars), or when the edge itself is specific to the ETF — SPY and SPX are not the same instrument, and an edge validated on one must be re-validated on the other before you switch (§3.5, §6.8). A tax-motivated instrument swap is a **new hypothesis**, not a parameter change.
- **Notional is the usual blocker, and XSP is the usual answer.** A full SPX condor risks roughly 10× an XSP condor; an account that cannot carry SPX size at the minimums in §8.11, the position limits in §8.5, or the margin ceiling in §8.8 can often carry XSP size and still get Section 1256 treatment. Check XSP's actual spread and depth on your strikes before assuming it — the treatment is worthless if the fill costs more than it saves.

**Tax-advantaged accounts change the calculus entirely.** In an IRA or similar deferred/exempt account, gains are not currently taxed, so the 60/40 advantage largely disappears and instrument choice reverts to exactly the grounds §5 already used: liquidity, capital efficiency, settlement mechanics, notional granularity. Losses are also not deductible, which removes the loss-carryback and loss-offset arguments in the other direction. But such accounts impose structural constraints that interact directly with §8.8 and §8.11: they are generally cash-secured, borrowing on margin is typically prohibited, and undefined-risk positions — naked short calls, naked short puts beyond cash-secured, most ratio structures with a naked leg — are commonly restricted or unavailable by approval level. Half of §5.4's structure matrix may simply not be executable there. Determine your account's actual permissions **before** structure selection, not after, and record the constraint in the spec.

**Wash sales, and why systematic strategies are more exposed than discretionary ones.** The wash-sale rule disallows a loss when a substantially identical security is acquired within a window spanning roughly a month either side of the sale, with the disallowed loss added to the replacement position's basis. It generally applies to stock and securities — including equity and ETF options — and generally does **not** apply to Section 1256 contracts, which are under the mark-to-market regime instead.

The trap is mechanical. A discretionary trader who takes a loss and moves on rarely repeats the position inside the window. A systematic strategy **re-enters on a schedule** — same underlying, same structure, often similar strikes — which is precisely the fact pattern the rule catches, and it can catch it repeatedly across a chain of trades, deferring recognition of a loss out of the year in which the offsetting gains were realized. Nothing in §6.2's P&L engine models this; a backtest that nets a losing trade against a subsequent winner is silently assuming a treatment that may not apply. In pathological cases a strategy that ended the year flat can carry a taxable gain. This is another concrete argument for index products in high-turnover systematic trading. **Verify how your broker reports it** — reporting on the 1099-B is per-account and per-instrument, brokers differ in how they identify "substantially identical" across strikes and expiries, and their reporting is not necessarily identical to your obligation.

**What to actually do.**

1. **Add an `after_tax` block to the hypothesis spec (§2.7)** recording the intended instrument, its expected tax character, whether the account is taxable or deferred, and any wash-sale exposure. It is a pre-registered assumption like any other and must be stated before results are seen.

```yaml
after_tax:
  account_type: taxable            # taxable | ira_or_deferred
  instrument: XSP                  # the instrument this hypothesis will trade
  expected_character: sec_1256_60_40   # sec_1256_60_40 | short_term_ordinary
  year_end_mtm: true
  wash_sale_exposure: none         # none | material — schedule re-entry within window
  assumed_blended_rate: 0.00       # YOUR figure, verified for your tax year; 0 for deferred
  verified_with_professional: false
```

2. **Re-run §7's expectancy on an after-tax basis before promotion.** At the §7.8 gauntlet, print the pre-tax card and one line beneath it: expected annual net P&L × (1 − assumed blended rate), with the rate from the spec. If a hypothesis passes pre-tax and fails after-tax against the §7.7 benchmark, it fails.

3. **Keep the tax assumption out of the backtest engine.** Model it as a **post-hoc haircut applied to the aggregate**, never inside the per-trade P&L in §6.2. Three reasons: tax is an annual, account-level, offset-dependent computation that per-trade arithmetic gets wrong; the rate is a property of *you*, not of the strategy; and burying it in the engine makes pre-tax results non-comparable across hypotheses registered at different times under different assumed rates. The backtest reports pre-tax. The promotion decision reads both.

---

## 6. Stage 2 — Backtesting the Options-Wrapped Strategy

### 6.1 The central warning: stage 2 is a second falsification test

A statistically real edge in the underlying dies in options more often than it survives. The three killers:

- **Spread crossing.** A 5c-wide market on a \$0.60 option is an 8.3% round-trip haircut per leg. A signal with a 0.15% daily edge on the underlying, levered 5x by delta, produces ~0.75% — less than one crossing.
- **Theta/vega drag.** You are long or short a decaying, mean-reverting risk premium that has nothing to do with your signal. If your directional edge is 20 bps/day and you are paying 45 bps/day of theta on a 30-DTE ATM option, the wrapper is the trade, not the signal.
- **Expiry mismatch.** Stage-1 edges are usually defined on a horizon ("5-day forward return"). Options have a fixed maturity, a path-dependent payoff, and a strike. A signal that predicts *mean* forward return may say nothing about whether spot crosses your strike before your expiry.

**Rule: the stage-1 result grants zero license to assume the options version works.** Treat Section 6 as an independent hypothesis test with its own pass/fail. The null is "the options implementation has no edge after costs," and the burden of proof is on you. Expect a meaningful fraction of stage-1 survivors to die here. That is the system working.

### 6.2 Backtest engine architecture

Build your own. Off-the-shelf equity backtesters (`backtrader`, `zipline`, `vectorbt`) do not model multi-leg options positions, assignment, or per-leg fills. The engine is ~600 lines and you need to trust every one of them.

**Normalized chain table.** One row per (date, expiry, strike, right). Store as partitioned Parquet (`year=/month=`), read with `pyarrow`/`polars`. Sources: ORATS, CBOE DataShop (End-of-Day Summary), OptionMetrics IvyDB (academic), Polygon.io, ThetaData. Field names differ by vendor — normalize to this schema on ingest:

| Column | Type | Notes |
|---|---|---|
| `date` | date | Quote date (NBBO snapshot time — record which: EOD 15:59 vs 16:15 matters) |
| `underlying` | str | Root symbol |
| `expiry` | date | |
| `strike` | float | |
| `right` | char | `C` / `P` |
| `bid`, `ask` | float | NBBO. Keep raw, never overwrite |
| `last`, `volume`, `open_interest` | float/int | OI is prior-day settled |
| `iv` | float | Vendor IV — keep, but recompute your own |
| `delta`,`gamma`,`theta`,`vega` | float | Vendor greeks — keep, but recompute |
| `underlying_price` | float | Contemporaneous spot, same timestamp as the quote |
| `dte`, `mid`, `spread_pct` | derived | `mid=(bid+ask)/2`, `spread_pct=(ask-bid)/mid` |
| `is_adjusted` | bool | Non-standard deliverable flag |

**Compute your own greeks.** Vendor greeks are computed with the vendor's rate curve, dividend assumption, and (critically) their own IV solve — often from settlement prices, not the same NBBO snapshot you will trade against. Consistency beats accuracy: solve IV from *your* mid with `py_vollib_vectorized` (or `QuantLib` for American/discrete-dividend), then derive all greeks from that single IV. Now delta, theta and P&L attribution are internally consistent with the prices you fill at. Cross-check your IV against the vendor's; a systematic gap >1 vol point means your rate or dividend inputs are wrong — fix it before proceeding.

**Event loop.** Iterate trading days from an exchange calendar (`pandas_market_calendars`, `XNYS`). Each day: (1) load the chain snapshot, (2) mark open positions, (3) process corporate actions/assignment/expiry, (4) evaluate exit rules, (5) evaluate the entry signal, (6) size and fill. Never look at row *t+1* anywhere in steps 1–6.

```python
@dataclass
class Leg:
    right: str; strike: float; expiry: date; qty: int   # qty<0 = short
    entry_fill: float = 0.0

@dataclass
class Position:
    legs: list[Leg]; entry_date: date
    capital_at_risk: float = 0.0

class Chain:
    """Snapshot accessor keyed by (date, expiry, strike, right)."""
    def quote(self, d, expiry, strike, right) -> Quote | None: ...
    def expiries(self, d, min_dte, max_dte) -> list[date]: ...
    def strikes(self, d, expiry) -> np.ndarray: ...

def mark(pos, chain, d):          # daily mark at MID, always
    return sum(l.qty * 100 * chain.quote(d, l.expiry, l.strike, l.right).mid
               for l in pos.legs)

for d in calendar_days:
    chain = Chain(d)
    for pos in book:
        pos.mtm = mark(pos, chain, d)
        handle_assignment(pos, chain, d)     # 6.5
        if d >= min(l.expiry for l in pos.legs):
            settle(pos, chain, d); continue
        if exit_rule(pos, chain, d):
            close(pos, chain, d, k=K_FILL)   # 6.3
    if signal[d] and passes_liquidity(chain, d):   # 6.7
        book.append(open_position(chain, d, k=K_FILL))
```

Mark daily at **mid** (that is the honest carrying value); realize P&L only at fills, which are worse than mid. Do not mark at your fill model — that double-counts costs.

### 6.3 Fill modeling — the part that decides whether the backtest is honest

**Never use mid for both entry and exit.** That single choice manufactures edge out of nothing and is the most common reason a paper strategy dies live.

**The model.** Marketable limit at
```
fill = mid + k * half_spread * side      # side = +1 buy, -1 sell
half_spread = (ask - bid) / 2
```
`k = 0` is mid, `k = 1` is paying the full quoted market. `k` is an **explicit swept parameter**, not a constant you set once and forget.

**Spread as a % of premium is what actually hurts.** A 5c market is trivial on a \$12 option and fatal on a \$0.35 one:

| Option mid | Bid/ask | Spread % of mid | Round-trip at k=1 |
|---|---|---|---|
| \$12.00 | 11.95/12.05 | 0.8% | 0.8% |
| \$2.50 | 2.45/2.55 | 4.0% | 4.0% |
| \$0.60 | 0.55/0.65 | 16.7% | 16.7% |
| \$0.20 | 0.15/0.25 | 50% | 50% |

This is why "buy cheap OTM wings" strategies backtest beautifully and trade catastrophically. Any strategy whose P&L lives in options under ~\$0.50 is presumptively unbacktestable at retail.

**Multi-leg spreads.** Verticals, strangles and butterflies often fill better than the sum of legs: they route to a complex-order book (CBOE COB), the market maker nets the risk, and price improvement inside the sum-of-legs market is routine. **Do not model this benefit.** Model each leg independently at the same `k`. If the strategy only works when you assume complex-order price improvement, it does not work. Any improvement you actually get live is unbooked upside.

**Minimum tick.** Penny Interval Program names quote \$0.01 throughout; otherwise \$0.05 below \$3.00 and \$0.10 above. Round fills to the tick *away from you*. Index options (SPX) are \$0.05/\$0.10. This alone can eat the entire modeled edge of a strategy that assumes sub-penny precision.

**Quoted size ≠ available size.** NBBO size is frequently 1–10 contracts and is not a promise. Size beyond the top of book walks the market. Cap per-trade size (6.7) and, if you must trade more than displayed size, add a second `k` unit for the excess.

**Required cost-stress protocol.** Rerun the full backtest at four settings and report all four side by side:

| Run | `k` | Meaning |
|---|---|---|
| A | 0.0 | Mid — fantasy baseline |
| B | 0.5 | Mid + 25% of the full spread |
| C | 1.0 | Mid + 50% of the full spread (= full half-spread) |
| D | 2.0 | Full spread crossing |

**The bar: the strategy must be profitable and pass Section 7's criteria at run C (k = 1.0), i.e. paying the full half-spread on every leg of every entry and exit.** Justification: k=1.0 is what a marketable limit at the touch actually costs a retail account with no maker rebates, no complex-order netting credit, and no size priority. Runs A and B assume price improvement you have no entitlement to. Run D is the stress case for a bad tape — you do not need to survive it, but the P&L degradation from C to D tells you how fragile you are; a strategy that loses more than ~60% of its net P&L between C and D is a spread-harvesting artifact, not an edge.

Plot net P&L vs `k` continuously. A real edge decays roughly linearly with a shallow slope. A fake one has a steep, near-vertical cliff between k=0 and k=0.5.

### 6.4 Commissions, fees, and friction

| Item | Typical retail | Notes |
|---|---|---|
| Broker commission | \$0.15–\$0.65 / contract | Tastytrade ~\$1.00 open / \$0 close; IBKR tiered \$0.15–\$0.65; Schwab/Fidelity \$0.65 |
| OCC clearing fee | ~\$0.02 / contract | Capped per trade |
| Exchange fees | \$0.00–\$0.50 / contract | Venue and maker/taker dependent; index options higher |
| ORF (Options Regulatory Fee) | ~\$0.02–\$0.04 / contract | |
| FINRA TAF | ~\$0.00279 / contract | Sells only |
| SEC Section 31 | ~\$27.80 per \$1M | Sells only, on premium proceeds |
| Assignment / exercise | \$0–\$20 per event | Often flat per occurrence |

Model **\$0.65/contract per side** as a conservative all-in default, i.e. **\$1.30 round trip per contract**, plus assignment fees where triggered.

**Worked example — cheap options.** Strategy buys a \$0.40 call (0.35/0.45), sells at a modeled \$0.52 average.

- Gross edge: \$0.12 × 100 = **+\$12.00/contract**
- Fill at k=1.0: buy \$0.45, sell \$0.47 → realized \$0.02 × 100 = **+\$2.00**
- Commissions/fees: −\$1.30
- **Net: +\$0.70 per contract**, a 1.7% return on the \$40 premium — and one \$0.05 tick of slippage or one adverse quote makes it negative.

The same \$0.12 gross edge on a \$4.00 option with a 5c market nets \$0.07 × 100 − \$1.30 = **+\$5.70**. Frictions are close to fixed per contract; edge must scale with premium, not with contract count.

### 6.5 Position lifecycle edge cases

- **Early assignment (American).** Short calls are the danger. Rule: **early exercise of a call is rational when the dividend exceeds the remaining time value of the corresponding same-strike put** — i.e. `D > P_time_value + K*r*τ`. Simulate assignment on the business day before ex-dividend for any short call meeting that test (assume 100% assignment if deep ITM and time value < dividend; probabilistic otherwise). Short deep-ITM puts get assigned when time value approaches zero and the carry favors it. Ignoring this systematically overstates short-call P&L.
- **Pin risk.** Spot within ~\$0.25 of the strike at expiry: you do not know your assignment quantity until Saturday. Model it as a coin flip on assignment and charge a Monday-gap cost on the resulting unhedged shares.
- **Settlement style — the classic bug.** SPX is **European, cash-settled**; the monthly (third-Friday) contract settles **AM** against **SET**, the opening print of the constituents, and stops trading the Thursday before. SPXW weeklies/EOM settle **PM** on the close. SPY is **American, physically settled, PM**. Backtesting a "monthly SPX" strategy against Friday's close instead of Friday's SET open is a real, silent, sometimes multi-percent error. Encode `settlement_style` and `settlement_time` per root and expiry class.
- **Exercise by exception.** OCC auto-exercises long options **\$0.01 or more ITM** at expiry. Model it — do not let ITM longs expire worthless in your engine.
- **Expiry-day rolls.** Decide and hardcode: close at N DTE (typical: 7–21) rather than holding into gamma. Rolls are two fills, so charge two `k`s and two commissions.
- **Holidays and half days.** Use `pandas_market_calendars`; half days (day after Thanksgiving, Christmas Eve) have 1:00pm closes and thinner books. Never assume 252 or a fixed weekly cadence.
- **Corporate actions / adjusted options.** Splits, special dividends, mergers and spinoffs create non-standard deliverables (e.g. 100 shares + $X cash, or a `1` suffixed root). Their quotes are wide, their OI is stale, and their greeks are wrong under a standard 100-share model. **Exclude adjusted contracts entirely** — filter on the non-standard-deliverable flag, and independently drop any root whose strike grid contains non-standard increments. You cannot trade them reliably live either, so excluding them costs nothing and removes a large class of fake P&L.
- **Dividends and borrow.** Put-call parity holds only net of dividends and financing. Hard-to-borrow names have parity violations that look like free money in a backtest and are unavailable in practice. Screen out names with elevated borrow cost.

### 6.6 Margin and capital modeling

**Returns must be quoted on capital-at-risk / margin required, not on premium collected.** This is not a presentation choice; premium-based returns are the single largest source of inflated options-backtest results.

| Structure | Capital at risk (Reg-T) |
|---|---|
| Long option / debit spread | Net debit paid |
| Credit vertical | (Width × 100) − net credit |
| Naked short put | `max(0.20·S − OTM_amt, 0.10·K) · 100 + premium`, min ~\$50/contract |
| Naked short call | `max(0.20·S − OTM_amt, 0.10·S) · 100 + premium` |
| Short strangle | Margin on the greater side + premium of the other side |
| Cash-secured put | `K × 100` |

Portfolio margin (min \$100k equity) replaces this with a risk-array shock (roughly ±15% for broad indices, wider for singles) and typically cuts strangle requirements 2–4x — but it also introduces path-dependent margin *expansion* in a selloff. If you model PM, you must also model the margin call that forces liquidation at the worst point. Default to Reg-T.

**Worked example — short strangle.** SPY at \$500, sell the 470P/530C 45-DTE strangle for \$4.00 total credit (\$400/contract). Suppose the strategy nets \$250/contract per cycle, ~8 cycles/year.

- Premium-based: \$250 / \$400 = **62.5% per cycle → ~500%/yr**. Absurd, and exactly what naive backtests print.
- Reg-T margin, put side: `0.20 × 500 − 30 = \$70/share → \$7,000`, `+ \$400` premium ≈ **\$7,400**, plus the call-side premium. Say **\$7,700** held.
- Return: \$250 / \$7,700 = **3.2% per cycle → ~26%/yr** before you hold any buffer.
- Hold a realistic 2x margin buffer against expansion and it is **~13%/yr**.

That is a **~20–40x** difference between the premium-based and the capital-honest number. Compute margin per position, per day, take the peak, and denominate every return in Section 7 on it.

### 6.7 Liquidity filters (applied at simulation time, enforced identically live)

Every filter below runs *inside* the backtest at trade time and must be re-implemented byte-for-byte in the live order path. Divergence here is the second-most-common cause of live/backtest mismatch after fills.

| Filter | Starting value |
|---|---|
| Open interest (contract) | ≥ 500 (indices/mega-caps ≥ 1,000) |
| Volume (contract, that day) | ≥ 50 |
| Spread as % of mid | ≤ 10% (≤ 5% for anything under \$1.00) |
| Zero / missing bid | Reject |
| Crossed or locked quote (`bid ≥ ask`) | Reject the row and log it |
| Strike distance from spot | \|log(K/S)\| ≤ 0.25, or \|delta\| ∈ [0.05, 0.95] |
| DTE window | Per Section 5; reject anything < 3 DTE |
| Max participation | ≤ 5% of that contract's daily volume, hard cap ~25 contracts early |
| Underlying ADV | ≥ \$50M/day |

Log the *rejection reason counts*. If >30% of your signal dates are rejected for liquidity, the strategy's true capacity is far below what the equity curve implies and you should say so in Section 7.

### 6.8 Synthetic-vs-real reconciliation

If Section 5 prototyped with Black-Scholes-synthesized prices (a constant or realized-vol input), you owe an explicit reconciliation before any conclusion stands.

Procedure: take the exact trigger dates and exact contracts the synthetic backtest chose. Pull the real chain quotes for those (date, expiry, strike, right) tuples. Report:

```python
err      = real_mid - synthetic_price
rel_err  = err / real_mid
report(mean(err), median(err), std(err),
       quantiles(rel_err, [.05,.25,.5,.75,.95]),
       mean(rel_err).groupby([moneyness_bucket, dte_bucket]))
```

Then rerun the full strategy on real quotes and compare terminal P&L. If mean relative error is within ±5% and shows no moneyness pattern, the synthetic prototype was a fair proxy. **If the error is large and systematically ordered by moneyness — real OTM puts richer than BS, real OTM calls cheaper — that is the volatility skew, and it is a finding, not a nuisance.** It means your strategy was implicitly trading a mispriced surface. Decide explicitly: does the edge survive paying the real skew? Frequently a "buy cheap OTM puts on signal X" strategy is revealed as "the model didn't know puts cost more." Document the reconciliation table in the results; a stage-2 result with no reconciliation is not accepted.

### 6.9 Not touching the holdout

- The stage-2 options backtest **may** consume the same in-sample and validation periods used in stage 1. Reusing in-sample data across stages is fine; it is already spent.
- The **sealed holdout stays sealed** through all of Section 6. Every fill-model sweep, every liquidity threshold, every structure comparison happens outside it. You touch the holdout exactly once, at the final evaluation, with a fully frozen specification (structure, strikes, DTE, `k`, filters, sizing, margin model).
- **Every structure variant tried at stage 2 counts against the Section 4 trial budget.** Testing 3 stage-1 signals × 4 structures × 3 DTE buckets is 36 trials, not 3. Increment the counter and re-apply the multiple-testing adjustment. The fill-model sweep (runs A–D) is a robustness check on one configuration, not four trials — but choosing your DTE *because* it looked best is a trial.
- If a stage-2 result is only significant before the multiplicity adjustment, it is not a result. Go back to Section 3.

### 6.10 "Backtest smells wrong" checklist

Run all of these before believing any number. Any hit is a stop-and-investigate, not a footnote.

- [ ] **Equity curve too smooth.** R² of a linear fit to the cumulative P&L > 0.95 over multiple years. Real option strategies are lumpy.
- [ ] **No losing months** across 3+ years, or a max drawdown under ~1.5x the largest single-trade loss.
- [ ] **Concentration in a few expirations.** Top 5 expiration cycles contribute >50% of total P&L. Remove them: does the strategy still work?
- [ ] **P&L concentrated in illiquid strikes.** Bucket P&L by OI, volume and `spread_pct` decile. If the top P&L bucket is the widest-spread decile, you are harvesting a data artifact.
- [ ] **Implausible Sharpe.** Net Sharpe > 3.0 on daily marks for a retail-accessible listed-options strategy. Above that, assume a bug until proven otherwise — the realistic ceiling for this asset class at retail scale is ~1.0–2.0.
- [ ] **Winners cluster on high-`spread_pct` days**, or P&L correlates positively with spread width — a direct fingerprint of a mid-fill bug.
- [ ] **Inversion test.** Flip the signal sign and rerun at the same `k`. The inverted strategy should lose roughly symmetrically after costs (both sides paying friction). **If both directions make money, you have a pricing or fill bug — full stop.** Common causes: marking with a different timestamp than filling, mid-fill on both sides, stale-quote arbitrage, or survivorship in the chain data.
- [ ] **Timestamp audit.** Confirm the signal input, the chain snapshot, and the underlying price all come from the same or earlier moment than the fill. Signal from the close, fill at the same close, is lookahead.
- [ ] **Zero-cost check.** Rerun with commissions and spreads set to zero. If net P&L barely changes, your cost model isn't wired in.

### 6.11 When Stage 1 Passes and Stage 2 Fails

The premise cleared §3.8 and §4, the options wrapper lost money at k=1.0, and the sentence forming in your head is *"the edge is real, I just picked the wrong structure."* Sometimes that is true. Usually it is the beginning of a structure sweep dressed up as a diagnosis. This subsection is the protocol that separates the two, and it is binding: **no re-translation may be run until the failure has a named cause backed by its diagnostic.**

**Step 1 — attribute the failure before touching anything.** Run all five diagnostics on the failing backtest. They are cheap (they reuse trades you already have) and none of them is a new trial.

| Cause | Diagnostic test | Terminal? |
|---|---|---|
| **(a) Cost drag** | Cost multiple = gross edge per trade at k=0 ÷ realized round-trip cost (spread at k=1.0 + §6.4 fees). Report it per trade and at the median, not the mean. | Usually — see below |
| **(b) Horizon mismatch** | Horizon capture ρ_h = mean cumulative underlying move realized *inside* the option's actual life ÷ the full stage-1 h-day mean move. Plot mean cumulative return by day-since-trigger against your entry→exit window. ρ_h < 0.5 = mismatch. | No |
| **(c) Wrong Greek** | Rerun the §5.9 attribution on **realized** backtest paths, not simulated ones. Fails if the edge Greek is < 50% of mean \|P&L\| or any unsupported Greek is > 25%. | No |
| **(d) Path dependence** | For losing trades: was the terminal underlying move the sign/size stage 1 predicted? If yes in ≥ 60% of losers, tabulate MAE against strike distance and stop level. Path, not forecast, killed them. | Yes |
| **(e) Stage-1 false positive** | Re-run the stage-1 event study **restricted to the trigger dates that survived the §6.7 liquidity filters and the §6.5 exclusions**. If the underlying edge weakens materially or loses significance on that subset, the edge never existed in the tradeable sample. Cross-check the deflated Sharpe at the current `N`. | Yes |

Run (e) first — it is the cheapest and the most fatal. Run all five regardless; multiple causes co-occur, and **the most terminal cause found governs**, not the most convenient one.

**Step 2 — which causes license a retry.** The distinction rests on what kind of claim each cause falsifies. The hypothesis is a claim about the underlying. The §5 structure is an *estimator* of that claim — a modelling choice (which Greek, which horizon, which sign of premium) made under uncertainty before any options P&L existed. A demonstrably bad estimator does not falsify the claim. Costs, path behaviour and statistical significance are claims about the world, and failing them falsifies the trade itself.

| Cause | Retry licensed? | Condition |
|---|---|---|
| (a) Cost drag | **Only with proof** | You must name a specific structure and show, from quotes and before running anything, that it cuts round-trip cost per unit of edge by ≥ 50% and lands the cost multiple ≥ 2.0. "Try wider/cheaper" is not proof. If realistic costs exceed the edge, no structure fixes it. |
| (b) Horizon mismatch | **Yes** | One re-translation with DTE/exit re-derived from the observed cumulative-return curve per §5.6 — not scanned. |
| (c) Wrong Greek | **Yes** | One re-translation that moves the dominant Greek onto the edge Greek per §5.9. |
| (d) Path dependence | **No** | Terminal. Path risk was measurable at §5.2(c) intake; re-picking strikes to survive the MAEs you just observed is fitting the sample, and the wider strikes that survive them no longer carry enough premium or delta to clear costs. |
| (e) False positive | **No** | Terminal. Retire the hypothesis with cause of death `STAGE1_FALSE_POSITIVE`. Stage 2 did its job. |

**Step 3 — the retry budget.** **At most two structure re-translations per hypothesis, ever.** Both pre-registered before running. Both logged as trials against the §4.2 budget with new `spec_hash`. Each one justified in writing by a named diagnostic from step 1 — a written sentence naming the cause, the measured statistic, and the single change it implies. "Let's try a calendar instead" is not a justification and the runner should refuse it. **A third attempt retires the hypothesis** with cause of death `STRUCTURE_EXHAUSTED`.

The cap is §4.1 arithmetic. Three structures × the DTE and delta choices already inside each is 20–30 effective trials on one signal; at 3 years of data (SE ≈ 0.58) the expected best-of-N noise Sharpe is already ~1.3–1.4. Beyond two retries you cannot distinguish a fixed strategy from the max of a search, so the extra attempts buy no information — they only buy a number you will believe.

**Step 4 — legitimate re-translation vs fishing.** A legitimate retry is **one named change, with a numeric prediction stated before the run, judged against that prediction.**

| Legitimate | Fishing |
|---|---|
| "Attribution showed 71% theta on a directional edge. Switch the credit spread to a debit vertical with DTE matched to h=10. Prediction: theta share < 25%, delta share > 50%, net expectancy > +\$40/trade at k=1.0." | "Tried 30/45/60 DTE and 16/25/30 delta, kept the best." |
| "ρ_h = 0.31: 68% of the move lands on days 8–14, our 7-DTE contract expired first. Move to 21 DTE, exit day 14. Prediction: ρ_h > 0.8, gross edge/trade rises ≥ 2x." | "The 45-DTE version was close to breakeven so we nudged to 50." |
| "Round-trip cost is 62% of gross edge on \$0.45 wings. Replace with a 5-wide vertical on \$3.20 options; quoted spread falls from 16% to 3% of mid. Prediction: cost multiple ≥ 2.5." | "Swapped to a butterfly because the condor didn't work." |

If the retry is profitable but the prediction was wrong — theta share is still 60% and it made money anyway — that is a **fail**, not a pass. You have found a different, unregistered strategy and must register it as a new hypothesis with a fresh premise.

**Step 5 — re-registration.** The re-translated hypothesis **keeps its ID and takes a suffix** (`H-2026-007-r1`). New spec, new `spec_hash`, new results directory. The original stage-2 failure stays in `results/` with its diagnosed cause; nothing is overwritten or edited. §2.8's pre-commit hook enforces this — a spec whose ID already appears in `results/` cannot be modified in place. Add `retry_of`, `retry_cause`, and `retry_prediction` fields to the spec so the registry shows, on inspection, exactly how many structures this idea consumed. The sealed holdout is untouched throughout (§6.9, §7.9); retries spend in-sample data only.

**The honest prior.** Most stage-2 failures are real failures. Expect roughly half of stage-1 survivors to die at stage 2 with no retry warranted, and expect fewer than one retry in five to produce something that survives §7. Hold this sentence: **a strategy that only works in its third structural variant is far more likely to be fitted than fixed.**

---

## 7. Evaluation — What "Proven" Actually Means

### 7.1 Hit Rate Is a Vanity Metric

Options let you buy any win rate you want. Sell far enough OTM and you win 95% of the time; buy far enough OTM and you win 5% of the time. Win rate is a *strike selection choice*, not a measure of edge. It tells you where you put the strike, not whether you have an edge.

Two strategies, 200 trades each:

| | A: short 16Δ strangle, 45 DTE | B: long OTM call spread on signal |
|---|---|---|
| Win rate | 90% (180W / 20L) | 30% (60W / 140L) |
| Avg win | +\$120 | +\$520 |
| Avg loss | −\$1,400 | −\$180 |
| Expectancy/trade | 0.9(120) − 0.1(1400) = **−\$32** | 0.3(520) − 0.7(180) = **+\$30** |
| Capital at risk (CaR) | ~\$3,500 margin | \$180 debit |
| Expectancy / CaR | **−0.91%** | **+16.7%** |
| Total P&L over 200 | −\$6,400 | +\$6,000 |

A has a 90% win rate and bleeds. B is wrong more than two-thirds of the time and compounds. Expectancy is not "the average of the good outcomes" — it is the probability-weighted sum over the *whole* distribution, and for options the tail carries most of the weight.

**Primary metric, stated once:** expectancy per trade, and expectancy per unit of capital-at-risk (call it **R**, where 1R = the pre-defined maximum loss you sized the position against). Everything else in this section either decomposes expectancy, tests whether it is real, or tells you what it costs you to hold.

```python
def expectancy(pnl):            return pnl.mean()          # $/trade
def expectancy_R(pnl, risk):    return (pnl / risk).mean() # R/trade, comparable across structures
```

Report both. `$` sizes the account; `R` compares hypotheses.

### 7.2 The Core Metric Set

Compute all of these for every hypothesis. The "hides" column is not commentary — it is the reason the next four subsections exist.

| Metric | Formula | Hides |
|---|---|---|
| Expectancy | `E = p·W̄ − (1−p)·L̄` | Whether E comes from 3 trades or 300 |
| Avg win / avg loss | `W̄ / L̄` | Skew inside each bucket; one −8R blowup |
| Profit factor | `Σ wins / |Σ losses|` | Same concentration problem; unstable below N=50 |
| Sharpe | `(μ_r − r_f)/σ_r · √P` | Punishes the good tail, rewards short-gamma; assumes symmetry |
| Sortino | `(μ_r − MAR)/σ_d`, `σ_d = √(mean(min(r−MAR,0)²))` over **all** obs | Still a second-moment measure; blind to a single −20R |
| Calmar | `CAGR / |MaxDD|` | Path-dependent; one drawdown defines it |
| Max DD / DD duration | peak-to-trough on equity; days peak→recovery | Duration is the one that ends careers, not depth |
| Time in market | Σ position-days / calendar days | Idle capital — makes annualized returns meaningless |
| Return on CaR | `E / max_loss` | Whether max_loss is real (see 7.6) |
| CAGR vs arithmetic | `CAGR = (Π(1+rᵢ))^(1/Y) − 1`; `CAGR ≈ μ_a − σ²/2` | Arithmetic mean overstates by ~σ²/2 — for a 40%-vol equity curve that is 8%/yr of pure fiction |

**Sharpe is misleading for option payoffs.** Short-premium returns are left-skewed with fat left tails: σ is small until it isn't, so pre-blowup Sharpe is inflated. Long-premium returns are right-skewed: the winners *increase* σ and *reduce* Sharpe, penalizing the exact payoff you wanted. Never rank option hypotheses by Sharpe alone. Report it, but rank on expectancy/R with the 7.3 concentration gates applied, and always print skew alongside Sharpe so the number can be read in context.

**Honest annualization.** A strategy trading 12 times a year has ~12 independent observations per year. Two rules:

1. **Never** annualize a per-trade Sharpe as `SR_trade · √(trades/yr)` unless capital is genuinely redeployed continuously and trades are non-overlapping and serially uncorrelated. That formula assumes iid and full deployment; both usually fail.
2. Build a **calendar-daily equity curve of the whole allocated account** (idle cash earns the risk-free rate), compute daily returns, annualize `μ·252` and `σ·√252`. This automatically charges you for time out of the market.

Then print the uncertainty, because that is the honest part:

```python
se_ann = pnl.std(ddof=1) * np.sqrt(trades_per_year) / np.sqrt(years)  # $ SE of annual P&L
```

With 12 trades/yr over 5 years, a "38% annual return" typically carries a ±25pp standard error. State the interval or don't state the number. Always publish: total P&L, expectancy/trade, trades/yr, years, time-in-market, and CAGR — in that order — so a reader can reconstruct the annualized figure and its error themselves.

### 7.3 Distribution, Not Averages

Plot the P&L histogram in R units for every hypothesis. Then compute:

- **Skew** and **excess kurtosis** of trade returns. Short premium should show negative skew and high kurtosis; if it doesn't, your loss modeling is wrong.
- **Tail ratio** = `|P95| / |P5|` of trade returns. <0.7 means you are collecting nickels in front of something.
- **Concentration diagnostics** (mandatory):

```python
s = np.sort(pnl)[::-1]
drop_k    = {k: (pnl.sum() - s[:k].sum()) / len(pnl) for k in (1, 3, 5)}  # E after removing top k
top_decile_share = s[:max(1, len(s)//10)].sum() / s[s > 0].sum()

def gini(x):
    x = np.sort(x[x > 0]); n = len(x); i = np.arange(1, n+1)
    return (2*(i*x).sum())/(n*x.sum()) - (n+1)/n
```

**Hard rule: if removing the single best trade flips the strategy to unprofitable, it is not a strategy. It is one trade with 199 pieces of noise attached.** No exceptions, no appeals.

| Diagnostic | Pass | Fail |
|---|---|---|
| E after dropping top 1 | ≥ 70% of full E and > 0 | < 0 → dead |
| E after dropping top 3 | ≥ 60% of full E and > 0 | < 0 → dead |
| E after dropping top 5 | ≥ 50% of full E and > 0 | < 0 → dead |
| Top-decile share of gross profit | ≤ 50% | > 65% → dead |
| Gini of positive P&L | ≤ 0.65 | > 0.75 → dead |
| Worst single trade | ≤ 3× avg win (short premium) | > 5× → resize or dead |

Run the same drop-k test on the *loss* side for short-premium strategies. If removing the worst trade doubles expectancy, you have a strategy whose entire economics live in one unhedged tail event — that is a sizing problem, and it is a 7.6 problem.

### 7.4 Is It One Bet or Many?

200 overlapping trades on one underlying is not 200 observations. Three tests:

**Autocorrelation of trade returns.** Serial correlation inflates apparent significance:

```python
def eff_n_autocorr(r, max_lag=10):
    r = np.asarray(r, float); n = len(r)
    rho = [np.corrcoef(r[:-k], r[k:])[0, 1] for k in range(1, max_lag+1)]
    infl = 1 + 2*sum((1 - k/n)*rho[k-1] for k in range(1, max_lag+1))
    return n / max(infl, 1.0)
```

**Overlap (average uniqueness).** For each calendar day `t`, let `c_t` = number of live positions. Trade `i`'s uniqueness is the mean of `1/c_t` over its holding days; `N_eff = Σ uniqueness_i`.

```python
conc = np.zeros(n_days)
for a, b in spans: conc[a:b] += 1
n_eff_overlap = sum(np.mean(1.0/conc[a:b]) for a, b in spans)
```

**Time clustering.** Herfindahl on trades-per-year: `N_eff_time = (Σ nᵧ)² / Σ nᵧ²`. If 120 of 200 trades happened in 2020, your effective year count is ~2.

Use `N_eff = min(autocorr, overlap, time)` for every t-statistic and confidence interval in this section. A t-stat computed on raw N when trades overlap 4-deep is overstated by roughly 2×.

### 7.5 Stability

Break performance down by year, quarter, VIX tercile (or fixed buckets <15 / 15–25 / >25), day of week, month-of-year, and underlying. Also plot **rolling 12-month expectancy** (trade-count-based rolling window if trade frequency is low).

Required consistency criteria:

- ≥ 60% of calendar years positive, and **no single year contributes > 50% of total profit**.
- ≥ 60% of rolling 12-month windows positive.
- Positive expectancy in ≥ 2 of 3 VIX buckets, and no bucket worse than −0.3R average.
- If multi-asset: ≥ 60% of underlyings positive; no single underlying > 40% of total profit.
- Rolling 12m expectancy must not show a monotone decline over the last third of the sample.

**Disqualifying patterns:** all profit from one year (usually 2020 or 2022); profit only in the top VIX bucket (you have a crisis-alpha lottery ticket, not a strategy — size it as such and say so); a day-of-week or month effect strong enough to matter (that is a data artifact or an expiry-cycle artifact, and it will not survive); positive expectancy that decays monotonically across sub-periods (edge is being arbitraged away).

### 7.6 Options-Specific Risk

1. **Worst realized single-trade loss vs modeled max loss.** For defined-risk spreads these should match within a few percent; if worst realized > modeled max, your fill/assignment/pin logic is broken. For undefined-risk structures, modeled max loss is a fiction — report worst realized loss and a stressed loss instead.
2. **Gap / overnight jump exposure.** Recompute every trade's P&L assuming the worst overnight gap in the sample occurred on its highest-gamma day. Report the resulting worst loss.
3. **Tail-loss to avg-win ratio** (short premium): `|P1 of P&L| / W̄`. Above 20 means ~20 winners to repay one tail. Cap at 15 for anything you intend to size normally.
4. **Consecutive losses to expect.** With loss rate `q` over `N` trades, expected longest losing run:

   `R_max ≈ ln(N(1−q)) / ln(1/q)`, and `P(run ≥ k) ≈ 1 − exp(−N(1−q)q^k)`

   The 30%-win-rate strategy B above, over 200 trades: `ln(60)/ln(1/0.7) ≈ 11.5`. Expect an 11-trade losing streak, and a 15-streak with ~25% probability. Know this number before you trade it, and write it on the result card — most abandonment happens inside a statistically normal streak.
5. **Shock table — required, per strategy, at target size.** Reprice the *typical open position* under each scenario (underlying move, IV multiplier applied to the surface, 1 day elapsed):

| Scenario | Spot | IV | P&L (R) | vs planned risk |
|---|---|---|---|---|
| Base | 0% | ×1.0 | | |
| Mild selloff | −5% | ×1.5 | | |
| Crash | −10% | ×2.0 | | |
| Crash, fat | −10% | ×3.0 (short-dated) | | |
| Melt-up | +5% | ×0.9 | | |
| Vol crush | 0% | ×0.6 | | |
| Pin at short strike, expiry | ±0.5% | ×1.0 | | |

No scenario may exceed **3× planned per-trade risk**. If it does, the structure is wrong or the size is wrong, and no amount of backtest expectancy fixes it.

### 7.7 Benchmarking — Zero Is Not the Bar

Four comparisons, all required:

| Benchmark | Purpose | Requirement |
|---|---|---|
| Buy-and-hold underlying, **risk-matched** (scale B&H to the strategy's realized annual vol) | Are you beating the thing you could have owned for free? | Higher return at matched vol, or clearly lower max DD |
| **Always-on** version: same structure, same DTE, same exits, entered on every eligible date with **no signal** | Isolates whether the *signal* adds value beyond structural premium | Strategy expectancy/trade ≥ **1.3×** always-on, and bootstrap p < 0.05 on the difference |
| **Randomized trigger dates**: 1,000 runs with the same trade count and holding-period distribution, entry dates drawn at random | Null distribution for "this structure held for this long" | Real expectancy above the **95th percentile** of the permutation distribution |
| Same structure, **signal inverted** | Sanity — inverted should be materially worse | Inverted expectancy < always-on |

If the strategy does **not** beat always-on by the stated margin, it is not a signal — you are harvesting a risk premium. That is a legitimate business, but you must label it as such, because it changes everything downstream: sizing must assume the premium's tail is the whole risk, capacity is much larger, the failure mode is a single regime break rather than gradual decay, and the correct monitoring metric is realized-vs-implied spread, not signal hit rate. Mislabeling a premium harvest as an alpha signal is the most common way a solo book blows up.

### 7.8 The Promotion Gauntlet

A hypothesis moves from research to paper trading only by clearing **every** row. One failure is a stop.

| # | Gate | Threshold |
|---|---|---|
| 1 | Sample size | N ≥ 100 raw trades **and** N_eff ≥ 30 (§7.4) |
| 2 | Time span | ≥ 5 years, spanning ≥ 1 stress episode (Feb-18, Mar-20, 2022, Apr-25) |
| 3 | Expectancy | > 0 net of modeled costs **and** ≥ **3× round-trip cost** per trade |
| 4 | Expectancy per CaR | ≥ **0.05R** per trade |
| 5 | Statistical significance | t = E / (σ/√N_eff) ≥ **3.0** (multiplicity adjustment per §4 applied on top) |
| 6 | Profit factor | ≥ 1.30 net |
| 7 | Concentration | all six §7.3 pass rows |
| 8 | Sub-period consistency | all five §7.5 criteria |
| 9 | Signal value | beats always-on by ≥ 1.3× **or** is explicitly reclassified as premium harvest |
| 10 | Permutation | above 95th pct of randomized-date null |
| 11 | Cost-multiple-to-death | remains profitable at **≥ 3×** modeled slippage/commission |
| 12 | Worst-case loss | worst realized ≤ modeled max; shock table max ≤ 3× planned risk; worst trade ≤ 2% of account at target size |
| 13 | Drawdown | max DD ≤ 20% of allocated capital; DD duration ≤ 12 months |
| 14 | Capacity | stated explicitly: contracts/trade at ≤ 10% of strike ADV and ≤ 20% of top-of-book size; $ capacity printed on the card |
| 15 | Holdout | §7.9 passed, one shot |

These are strict on purpose. Roughly 1 in 20 plausible hypotheses clears them, and that is the intended yield. **A threshold may be relaxed only by pre-registering the relaxation** — written down, with the reason, *before* re-running — and any relaxed gate is flagged permanently on the result card. Relaxing a gate after seeing the number that failed it is indistinguishable from overfitting, and you will not be able to tell the difference later.

### 7.9 The Sealed-Holdout Final Exam

Carve out the holdout at project start: the most recent 25–30% of history (or a full contiguous 2–3 years), sealed. It is never loaded, plotted, or queried during research. Enforce it mechanically — a separate file the research loader cannot open.

**Run exactly once, when gates 1–14 pass.** One configuration, frozen: every parameter, filter, exit, and cost assumption locked and hashed before the data is opened. No variants, no "we also tried."

**Reported (only these):** N, N_eff, expectancy $/trade and R/trade, t-stat on N_eff, profit factor, max DD and duration, drop-top-1/3/5 expectancy, worst trade vs modeled max, always-on comparison, and the in-sample→holdout degradation ratio for each.

**Decision rule.** Expect degradation — 30–50% of in-sample expectancy is the normal, healthy outcome of removing selection bias.

| Holdout result | Verdict |
|---|---|
| E_hold ≥ 0.70 × E_IS, t ≥ 2.0, concentration gates hold | Pass — promote to paper trading at half size |
| 0.50–0.70 × E_IS, t ≥ 1.5, sign consistent | Pass, sized down 50%; flag as marginal |
| 0.30–0.50 × E_IS | Fail |
| < 0.30 × E_IS, or E_hold ≤ 0, or t < 1.0, or any concentration gate breaks | Fail — dead |
| E_hold > 1.2 × E_IS | Fail the *process* — investigate leakage or a regime-specific fluke before believing it |

**Fail means dead.** The hypothesis is retired, logged in the graveyard with its result card, and not re-tuned. A re-tuned hypothesis re-tested on the same holdout has no holdout — you have spent it. If you genuinely believe a variant deserves a test, it needs a new hypothesis ID, a new pre-registration, and a holdout period that has not yet been used.

### 7.10 Hypothesis Result Card

Every backtest emits this, one page, same fields, always — so twenty hypotheses sort side by side in a single table.

```
================================================================
HYPOTHESIS H-0142  |  short 25Δ put spread, SPX, IVR>40 trigger
Config hash e91c4a7  |  Run 2026-03-14  |  Data 2015-01..2022-12 (IS)
Classification: [ ] alpha signal   [x] premium harvest + filter
----------------------------------------------------------------
SAMPLE       N 214   N_eff 41 (overlap 62, ac 41, time 47)
             Years 8.0   Trades/yr 26.8   Time in mkt 61%
CORE         E $/tr  +118      E R/tr  +0.13R
             Cost/tr $27  ->  cost multiple 4.4x   death at 3.9x
             Win rate 71%   W̄ $402  L̄ $580  W/L 0.69
             Profit factor 1.68   t-stat (N_eff) 3.4
RETURN       CAGR 14.2%  Arith 17.9%  Ann.vol 19.1%  SE(ann) ±8.5pp
             Sharpe 0.74  Sortino 1.02  Calmar 0.81
             MaxDD -17.5% (2020-02..2020-06, 118d recovery)
DISTRIBUTION Skew -1.42  ExKurt 6.1  Tail ratio 0.61
             Drop top1 0.81x | top3 0.68x | top5 0.57x  [PASS]
             Top-decile share 44%  Gini(+) 0.58        [PASS]
             Worst trade -$2,410 vs modeled max -$2,500 [OK]
             Tail/avg-win 6.0x   Expected max loss streak 4 (P(>=6)=19%)
STABILITY    Yrs +: 6/8   Max yr share of profit 34%   [PASS]
             Roll-12m +: 71%   VIX buckets +: 2/3 (low -0.04R) [PASS]
SHOCK (1R = $2,500, target size 4 lots)
             -5%/IV1.5  -1.4R | -10%/IV2.0  -2.6R | -10%/IV3.0 -2.9R
             +5%/IV0.9  +0.5R | vol crush   +0.7R | pin       -0.9R  [PASS]
BENCHMARKS   Always-on E +0.09R -> ratio 1.44x, p=0.02   [PASS]
             Random-date null p95 +0.07R, actual +0.13R  [PASS]
             Inverted signal -0.06R  [OK]
             B&H risk-matched CAGR 11.8%, MaxDD -34%
CAPACITY     18 contracts/trade  ~$450k allocated  (10% ADV cap)
GATES        1-14: PASS   Relaxations pre-registered: none
HOLDOUT      2023-01..2025-12  E +0.10R (0.77x IS)  t 2.3  PF 1.51
             Concentration gates: PASS
VERDICT      PROMOTE -> paper trade, half size, review after 40 trades
================================================================
```

---

## 8. Portfolio Construction — Running Several Setups Together

### 8.1 The Central Insight: P&L Correlation Hides Greek Correlation

You have two setups. Setup A sells post-earnings strangles on single names. Setup B sells index put spreads after a VIX spike. Their trade-level return correlation over 300 historical trades is 0.04. You conclude they are independent and size them as if they are.

They are not independent. Both are net short vega. On the day the market gaps down 6% and IV doubles, both lose simultaneously, and the loss is not the sum of two independent draws — it is one draw on a single latent factor.

Trade-level P&L correlation is nearly blind to this because trades overlap only partially in time, are entered at different points in the vol cycle, and are dominated by idiosyncratic outcome noise. The shared factor loading shows up in only a handful of the historical observations — precisely the ones that matter — and gets averaged into nothing.

**The rule: a multi-strategy options book must be monitored in Greek space and factor space, not P&L-correlation space.** P&L correlation is a lagging, low-power confirmation. The aggregate Greek book is the leading, high-power measurement. Two strategies with the same sign on vega, gamma, or beta-weighted delta are correlated *by construction*, whatever the historical scatter plot says.

The factor set that actually explains a retail options book: (1) net short/long vega, (2) net short/long gamma, (3) beta-weighted delta, (4) skew/vanna exposure, (5) term-structure slope exposure. Almost every blowup is one of these five loading up quietly across strategies that each looked fine standalone.

### 8.2 The Aggregate Greek Book

Maintain one live table across every open position in every strategy, refreshed at least at every mark (and intraday when |ΔSPX| > 1%).

**Beta-weighted delta.** Raw delta summed across underlyings is meaningless: 500 deltas of a utility and 500 deltas of a high-beta semi are not the same risk. Convert everything to SPY-equivalent share delta:

```
Δ_beta,i = δ_i × 100 × N_i × β_i × (S_i / S_SPY)
Δ_beta_book = Σ_i Δ_beta,i          # in SPY shares
$Exposure = Δ_beta_book × S_SPY     # in dollars
```

where `δ_i` is per-share option delta, `N_i` signed contracts, `β_i` the underlying's beta to SPY (use 1–2y weekly-return beta, refit monthly; do not use a 5y beta on a name whose business changed).

**Vanna** = ∂vega/∂S = ∂delta/∂σ. Operationally: how much your vega changes when spot moves, and how much your delta changes when IV moves. It is the Greek that makes short-put books lethal. A short OTM put has positive vanna in the ∂vega/∂S sense: as spot falls toward the strike, the position's vega becomes *more* negative — you get shorter vol exactly as vol is exploding — and simultaneously its delta gets longer as IV rises, so you get longer the market into the decline. A book that is "only" −\$500 vega at spot can be −\$1,100 vega after a 7% drop. Any book with meaningful skew exposure (put spreads, ratios, jade lizards, short strangles) must track net vanna or its vega limit is fiction.

**Charm** = ∂delta/∂t: delta decay per calendar day. A book flat at Friday's close can be materially directional at Monday's open with no price movement at all, because near-ATM options' deltas migrate toward 0 or ±1 as time passes. Charm is largest for near-the-money, short-dated positions and flips sign across the strike. Track it as "delta drift per day" and re-check it before every weekend and every holiday.

**Hard limits, per \$100,000 of account equity** (scale linearly):

| Greek | Measured as | Limit | Justification |
|---|---|---|---|
| Beta-weighted delta | SPY-equivalent $ notional | ±\$25,000 | A 5% index gap costs ±\$1,250 = 1.25% of equity from delta alone. |
| Net dollar gamma | Δ$ change per 1% SPY move | ±\$5,000 | After a 5% move, delta has swung by 25% of equity — forces a re-hedge before delta breaches its own cap. |
| Net vega | $ P&L per 1 vol point | ±\$500 | A 10-point VIX spike = 5% of equity. Two such events in a quarter is survivable; three times this limit is not. |
| Gross vega | Σ \|bucket vega\| | \$900 | Caps the calendar bet hidden inside a flat net (see 8.3). |
| Net theta | $ per day | −\$60 to +\$150 | +\$150/day = 0.15%/day. More positive theta than this means you are short more gamma than the gamma cap allows. |
| Net vanna | Δvega per 1% down move | ±\$60 | A −10% move then shifts vega by \$600 — already above the vega cap, which is why the stress grid (8.7), not this line, is the binding constraint. |
| Net charm | Δ$ delta drift per day | ±\$2,500 | Over a 3-day weekend that is 7.5% of equity of unintended direction. |

```python
def aggregate_book(positions, spot, betas, spy_price, equity):
    """positions: list of dicts with qty (signed contracts), underlying,
    delta, gamma, vega, theta, vanna, charm  (all per-share, per-contract=×100)."""
    g = {k: 0.0 for k in ("delta$", "gamma$", "vega", "theta", "vanna", "charm$")}
    for p in positions:
        m = p["qty"] * 100
        S, b = spot[p["underlying"]], betas[p["underlying"]]
        bw = b * S / spy_price                      # beta-weight factor
        g["delta$"] += m * p["delta"] * bw * spy_price
        g["gamma$"] += m * p["gamma"] * (S * 0.01) * bw * spy_price  # Δ$ per 1% move
        g["vega"]   += m * p["vega"]                # $ per 1 vol point
        g["theta"]  += m * p["theta"]               # $ per day
        g["vanna"]  += m * p["vanna"] * (S * 0.01)  # Δvega per 1% move
        g["charm$"] += m * p["charm"] * bw * spy_price  # Δ$ per day
    scale = equity / 100_000
    return {k: (v, v / scale) for k, v in g.items()}   # (raw, per-$100k)
```

### 8.3 Vega and Gamma Concentration by Expiry Bucket

Front vega and back vega are different risks wearing the same name. A 1-vol-point move in 5-day IV and a 1-vol-point move in 6-month IV are not equally likely, not equally persistent, and not equally hedgeable: front IV can move 15 points in a session; 6-month IV rarely moves 4. Netting them produces a number that is arithmetically valid and operationally worthless.

Worse, a book showing **net zero vega** can be a large calendar-spread bet: −\$800 of 8–30d vega against +\$800 of 90d+ vega is a short-front/long-back term-structure position. In a vol spike the front IV rises far more than the back (term structure inverts), so that "flat" book takes a large loss. Bucket, then limit each bucket independently *and* limit the gross.

**Bucketed limits, per \$100,000 equity:**

| Bucket | Net vega | Gross vega | Net gamma (Δ$/1%) | Note |
|---|---|---|---|---|
| 0–7 DTE | ±\$120 | \$200 | ±\$1,500 | Vega is small; gamma and charm are enormous. Gamma is the binding limit here, not vega. |
| 8–30 DTE | ±\$300 | \$450 | ±\$3,000 | The core short-premium zone; most retail books over-concentrate here. |
| 31–90 DTE | ±\$350 | \$500 | ±\$2,000 | Most vega per dollar of margin, lower vol-of-vol. |
| 90+ DTE | ±\$250 | \$350 | ±\$800 | Slow-moving but exposed to rates, dividends, and term-structure repricing. |
| **Total** | **±\$500** | **\$900** | **±\$5,000** | Bucket nets may offset; the totals still bind. |

Additional rule: **|net vega in any single bucket| ≤ 60% of total gross vega.** This prevents a book that satisfies every line above from being 100% a single-tenor bet.

### 8.4 Correlation Analysis Done Properly

**Use daily mark-to-market, not trade-level, returns.** Build a per-strategy daily P&L series (sum of daily marks of that strategy's open positions, divided by that strategy's allocated risk capital). Trade-level correlation misaligns time and destroys the signal.

**Compute the conditional correlation, not the unconditional one.** The full-sample number is dominated by quiet days. Take the worst 10% of days for the market factor (SPY return, or better, the joint tail of SPY return and VIX change) and compute the correlation matrix on that subset only. That is the number that governs your drawdown.

```python
tail = spy_ret <= spy_ret.quantile(0.10)
rho_full = daily_pnl.corr()
rho_tail = daily_pnl[tail].corr()          # the one that matters
n_overlap = daily_pnl.dropna().shape[0]
```

Expect `rho_tail` to be 0.3–0.6 higher than `rho_full` for any two short-premium strategies. Size on `rho_tail`.

**Sample size.** The standard error of a correlation estimate is approximately (1 − ρ²)/√(n − 1). At n = 20 that is ±0.22 — a measured 0.10 is indistinguishable from 0.5. **Minimum 60 overlapping daily observations for the full-sample estimate and 40 tail-day observations for the conditional estimate** (which implies ~400 calendar days of joint history). Below those thresholds, do not use the measured correlation at all: **assume ρ = 1.0 between any two strategies with the same sign of net vega, and ρ = 0.5 otherwise**, and size accordingly. This is not conservatism theatre; it is the only defensible prior when the estimator has no power.

### 8.5 Sizing

**Define risk (R) as stressed loss, not max loss and not margin.** For a defined-risk spread, R = width − credit. For short premium with theoretically unbounded loss, max loss is infinite and margin is an arbitrary broker number that ignores vol — both are useless for sizing. Instead:

> **R = |position P&L| at the stress node: underlying moves −2σ over 5 days (σ = 20-day realized), with IV multiplied by 1.5, repriced leg-by-leg.**

Size on that. A 16-delta SPY strangle with \$180 of margin might show R = \$1,400 at the stress node. The \$1,400 is the real number.

**Kelly.** For a strategy with per-trade return mean μ and variance σ² (in units of R), the continuous Kelly fraction is:

```
f* = μ / σ²          growth rate  g(f) = f·μ − f²σ²/2 ,  g(f*) = μ² / (2σ²)
```

**Full Kelly is wrong here**, for three independent reasons:
1. **Estimation error.** f* is linear in μ, but g(f) is quadratic. Overbetting by 2× drives growth to exactly zero: g(2f*) = 0. Your μ is estimated from a few hundred trades with a standard error of σ/√n; a 30% overestimate of μ is routine and produces a 30% overbet permanently.
2. **Non-normal payoffs.** Short-premium return distributions are sharply left-skewed. Kelly's optimality assumes the estimated distribution is the true one, including the tail you have not yet observed. It has not been observed *because it is rare*, not because it is absent.
3. **Ruin risk and lumpiness.** Kelly is asymptotic and assumes infinitely divisible bets. Contracts are integers, margin calls are discrete events, and your career is finite. Full Kelly on a realistic edge implies drawdowns above 50%, which is past the point where a solo trader stops executing the system.

**Default: quarter Kelly.** f = 0.25 × μ/σ². It captures g(f*/4) = (7/16) ≈ 44% of the maximum growth rate at roughly a quarter of the volatility. If the Kelly estimate and the fixed-fractional rule below disagree, take the smaller.

**Simpler and more robust — fixed fractional risk with a per-strategy budget.** Risk a fixed fraction r of equity per trade, where risk = R as defined above:

```
contracts = floor( (r × Equity) / R_per_contract )
```

with r = 0.5%–1.0% of equity for a confirmed strategy and 0.25% for a new one. This is the recommended default. It is invariant to expectancy misestimation, needs no variance estimate, and degrades gracefully.

**Worked allocation — \$250,000 account, three strategies.** Total portfolio risk budget = 6% of equity = **\$15,000** of simultaneous stressed loss. Allocate by confidence-adjusted edge (see 8.6):

| Strategy | Backtest E[R] | Live trades | Confidence multiplier | Adj. edge | Raw weight | Capped weight | Risk $ | Max concurrent | Risk/trade |
|---|---|---|---|---|---|---|---|---|---|
| A — post-earnings strangle | 0.28 | 120 | 1.00 | 0.280 | 42.7% | 40.0% | \$6,000 | 4 | \$1,500 |
| B — index put ratio on VIX spike | 0.45 | 0 | 0.50 | 0.225 | 34.4% | 36.0% | \$5,400 | 2 | \$2,700 |
| C — pre-event long gamma | 0.20 | 30 | 0.75 | 0.150 | 22.9% | 24.0% | \$3,600 | 3 | \$1,200 |

Arithmetic: adjusted edges sum to 0.655; A = 0.280/0.655 = 42.7%. A single-strategy cap of 40% of the risk budget binds, so A is trimmed to 40% and the freed 2.7% is redistributed to B and C in their 0.225 : 0.150 ratio (60/40), giving 36.0% and 24.0%. Then B's per-trade risk is \$5,400 / 2 = \$2,700; if the stress-node loss of one B position is \$900, B trades 3 contracts.

Note that B has the highest backtested edge and still gets less risk than A, because B has zero live confirmation. That is the intended behavior.

### 8.6 Risk Budgeting Across Strategies

Allocate **risk, not capital**. Capital allocation is meaningless when one strategy uses 4% of notional in margin and another uses 40%.

**The haircut rule.** A backtest expectancy is an upper bound. Until live data confirms it, size on a discounted figure:

| Live trades completed | Expectancy used for sizing | Confidence multiplier |
|---|---|---|
| 0–19 | 50% of backtested E | 0.50 |
| 20–49 | 65%, **only if** live E is within 1 SE of backtest E | 0.65 |
| 50–99 | 80%, same condition | 0.80 |
| 100+ | 100% of the *live* estimate (not the backtest) | 1.00 |

**Ramp schedule.** Start every new strategy at 0.25% risk per trade regardless of the model's recommendation. Advance one tier only when both conditions hold: the trade-count threshold is met, *and* live realized E[R] ≥ 0.5 × backtested E[R]. Any tier advance is one step only — never skip. Any of the following forces an immediate demotion of one tier: live E[R] falling below zero over the trailing 30 trades, a strategy drawdown exceeding 1.5× its worst backtested drawdown, or a change in the execution assumptions (fill quality, spread width) versus Section 6's model.

### 8.7 Portfolio-Level Stress Testing

Run this every day after the close, on the actual open book, **by full repricing of every leg** — not by Greek approximation. At ±10% spot and +100% IV, a second-order Taylor expansion is off by a factor that matters.

**Required grid:** underlying −10% / −5% / 0 / +5% / +10% × IV +100% / +50% / 0 / −25% (IV shocks applied multiplicatively to each leg's current IV, with the shock scaled down by tenor: full shock to 0–7d, 0.7× to 8–30d, 0.45× to 31–90d, 0.3× to 90d+).

Example output for the \$250,000 book above (P&L in $, % of equity in parentheses):

| Spot \ IV | +100% | +50% | 0% | −25% |
|---|---|---|---|---|
| −10% | **−48,200 (−19.3%)** | −36,400 (−14.6%) | −24,900 (−10.0%) | −19,600 (−7.8%) |
| −5% | −26,100 (−10.4%) | −17,800 (−7.1%) | −9,300 (−3.7%) | −5,400 (−2.2%) |
| 0% | −11,900 (−4.8%) | −5,600 (−2.2%) | +1,850 (+0.7%) | +5,100 (+2.0%) |
| +5% | −8,400 (−3.4%) | −2,900 (−1.2%) | +3,400 (+1.4%) | +6,200 (+2.5%) |
| +10% | −7,100 (−2.8%) | −1,600 (−0.6%) | +2,700 (+1.1%) | +5,900 (+2.4%) |

**Two additional required scenarios:**
- **Term-structure inversion:** spot −5%, front IV +15 vol points, 8–30d +9, 31–90d +3, 90+d −1. This is the scenario that kills "vega-flat" calendar books and does not appear anywhere in the parallel-shift grid.
- **Correlation → 1:** recompute assuming every underlying moves with β = 1.2 to SPY and every IV surface shifts identically. Single-name diversification vanishes in a crash; this is the honest version of the book.

**The rule: the worst node must be ≤ 12% of account equity. At 12–20%, no new risk may be added and the largest contributor must be reduced within two sessions. Above 20%, de-risk the same day.** The example book fails at −19.3% — the required action is to cut net short vega by roughly 40% (or buy back the tail), not to hope.

### 8.8 Capital and Margin Constraints

Buying power is not a risk measure, but running out of it forces liquidation at the worst possible prices, which converts a survivable loss into a permanent one.

**Margin expands exactly when you can least afford it.** Broker margin models are vol-sensitive: portfolio margin scans widen with IV, and Reg-T naked-short requirements scale with the option's current price and the underlying's price. In a −7% / IV-doubles session, initial margin on a short-premium book routinely rises **2–3×** while equity is simultaneously falling. Both terms of the ratio move against you.

**Rules:**
1. **Deployed initial margin ≤ 30% of account equity** at rest. If margin triples to 90% of *starting* equity while equity itself falls 15%, you are at ~106% and margin-called. 30% is the level that survives a 3× expansion combined with the 12% stress-node loss.
2. **Cash / T-bill liquidity buffer ≥ 25% of equity**, held in an instrument the broker accepts as collateral and that you can liquidate same-day without a loss.
3. **Never rely on unrealized profit as buying power.** Compute the margin ratio using equity marked at the −5% / +50% IV node, not at today's marks.
4. Run the margin calculation for the *combined* book. Legs from different strategies on the same underlying can offset (reducing requirement) or, under Reg-T, fail to offset at all. Know which regime you are in before assuming relief.

### 8.9 When Not to Combine

**Netting check at the position level, not the strategy level.** Two strategies operating on the same underlying with overlapping expiries can silently compose into a position neither of them authorized. Strategy A sells a 30-day put spread on SPY; Strategy B, unaware, buys back a put at the same strike as a hedge leg. The net is a **naked short put** that no strategy's risk model ever evaluated and that no stop-loss rule owns.

Required control: before every entry, net all open legs by `(underlying, expiry, strike, right)` and re-derive the composite position. Reject the trade if the composite contains any short leg not covered by a long leg at the same or better strike in the same expiry, unless the composite is explicitly whitelisted. Also flag any composite that changes the sign of gamma or vega for that underlying.

**Hard rule:** if two strategies would hold positions on the same underlying with expiries within 7 days of each other, the smaller position is skipped. The lost expectancy is far cheaper than an unmodeled composite.

**How many strategies can one person actually run?** Each strategy costs roughly 20–30 minutes per day of scanning, management, and journaling, plus a weekly review. It also adds n(n−1)/2 correlation pairs to estimate — going from 3 to 6 strategies takes you from 3 pairs to 15, and you do not have the data for 15. Practical ceiling: **3 strategies for a part-time trader, 5 for a full-time one.** A sixth strategy has never in practice added as much as it subtracted from the attention paid to the first five.

### 8.10 Portfolio Review Cadence

| Frequency | Recompute | De-risking trigger |
|---|---|---|
| **Daily** (post-close, 15 min) | Aggregate Greek book vs. all limits; bucketed vega/gamma; full stress grid; margin ratio; cash buffer | Any Greek limit breached → flatten the excess next session. Worst stress node > 12% of equity → no new risk; > 20% → de-risk same day. Margin > 30% of equity → reduce. |
| **Daily** (pre-open, 5 min) | Overnight charm drift; gap risk vs. beta-weighted delta; earnings/event calendar for every open underlying | Delta drift pushed beta-weighted delta out of range → hedge at the open with the most liquid instrument (SPY shares or futures), not by adjusting the option legs. |
| **Weekly** | Per-strategy live E[R] vs. backtest; trade count vs. ramp tier; full and tail correlation matrix (if ≥60 obs); position netting audit across all strategies | Live E[R] < 0.5× backtest over trailing 30 trades → demote one tier. Tail correlation > 0.7 between the two largest strategies → cut the smaller allocation by half. Any unauthorized composite found → close it immediately, then fix the entry check. |
| **Monthly** | Re-fit betas; re-derive risk budget weights from updated confidence multipliers; strategy drawdown vs. backtested worst; recompute account equity base for all per-\$100k limits | Strategy drawdown > 1.5× backtested max → halve allocation. > 2× → suspend and re-run Sections 3–4 before any restart. |
| **Quarterly** | Full re-validation of each strategy against Section 7's evaluation criteria; review whether the strategy count is still within the monitoring ceiling | Any strategy failing re-validation → retire it. Do not "give it more time"; the risk budget it holds has better uses. |

One discipline underlies all of it: **the limits are computed from equity, and equity moves.** Recompute the per-\$100k scaling monthly and after any single-day move exceeding 3% of the account. Limits that were set at last year's account size are the most common reason a book that "followed the rules" ends up twice as large as the rules allowed.

### 8.11 Minimum Viable Account Size

Everything in §8 is worked on a \$250,000 account. That is not a neutral choice of units — several of the mechanics above stop functioning below a threshold, and the threshold is different for every structure. This section states where those thresholds are. It belongs at the front of the process, not here: a reader with \$20,000 should learn on page one which candidate families are arithmetically unavailable, not discover it at §6 after buying options data and spending four months.

**Three mechanisms break at small size.**

**(a) Friction is fixed per contract; edge is proportional to premium.** §6.4's default is \$0.65/contract/side, i.e. \$1.30 round trip *per leg*. A 4-leg iron condor therefore costs \$5.20 round trip per contract before slippage. A small account, sized by the 1% rule, is pushed toward exactly the cheapest structures — narrow wings, low-priced options — where that toll is largest as a fraction of the trade:

| Structure | Gross credit / contract | Round-trip friction | Friction as % of credit |
|---|---|---|---|
| 1-pt SPY vertical (2 legs) | \$40 (\$0.40) | \$2.60 | **6.5%** |
| 1-pt SPY iron condor (4 legs) | \$40 | \$5.20 | **13.0%** |
| 25-pt SPX vertical (2 legs) | \$800 | \$2.60 + index fees ≈ \$4.00 | 0.5% |

If the strategy's validated edge is 20% of collected credit (already a strong result), the 4-leg version hands back two-thirds of it before slippage. §6.4's conclusion applies with full force: **edge must scale with premium, not with contract count**, and a small account cannot buy premium.

**(b) Integer contract granularity.** `contracts = floor(r × Equity / R_per_contract)` (§8.5). When `R_per_contract` exceeds `r × Equity`, that floor is zero. There is no fractional contract. The trader then either overbets — the single most common way small accounts die — or skips the trade, in which case the strategy's realized sample diverges from its backtest and the edge estimate is no longer the one that was validated.

**(c) Minimum structure width exceeds the whole risk budget.** SPX strikes are on a 5-point grid at the front and 25 points further out; a 25-wide SPX put spread has \$2,500 of notional width, so even at a \$700 credit R = \$1,800. On a \$30,000 account at r = 1%, the budget is \$300. The structure is not "expensive" — it is unbuildable. The same applies to \$400–900 mega-cap single names, where the tradeable strike increment is \$5–10 and the narrowest liquid spread is already \$500–1,000 of risk.

**Minimum account by instrument and structure.** R is the §8.5 stress-node loss for **one** contract (−2σ over 5 days, IV × 1.5, repriced leg-by-leg), not margin and not max loss. Minimum account = `R / r`. Columns show r = 1.0% (single confirmed strategy) and the effective r for a three-strategy book, where §8.5's worked allocation puts per-trade risk near 0.5% of equity.

| Structure | R, 1 contract | Min acct @ r=1% | Min acct, 3-strategy book | Note |
|---|---|---|---|---|
| SPY/QQQ vertical, 1–2 pt wide | \$65–\$130 | \$6,500–\$13,000 | \$13,000–\$26,000 | The practical floor for any options program. Friction is 6–13% of credit (above). |
| SPY/QQQ vertical, 5 pt wide | ~\$350 | \$35,000 | \$70,000 | Better friction ratio; this is the sensible small-account default. |
| SPY/QQQ 16Δ short strangle (Reg-T) | ~\$1,400 | **\$140,000** | \$280,000 | Reg-T margin is only ~\$7,700 (§6.6) — margin is not the constraint, the stress node is. |
| SPX/index defined-risk, 5 pt | ~\$350 | \$35,000 | \$70,000 | Thin at 5 pt; the liquid grid is 25 pt. |
| SPX/index defined-risk, 25 pt | ~\$1,800 | **\$180,000** | \$360,000 | Where SPX defined-risk actually becomes tradeable. |
| SPX naked / short strangle | \$12,000–\$16,000 | **\$1.2M–\$1.6M** | \$2.5M+ | Reg-T ~\$85k/contract. Portfolio margin needs \$100k equity minimum and still ~\$30k/contract. Not a retail structure. |
| Single name \$50–200, defined risk (\$5 wide) | ~\$350 | \$35,000 | \$70,000 | Widest spreads of any row; add slippage before believing the number. |
| Single name \$50–200, earnings strangle | \$900–\$1,200 | **\$90,000–\$120,000** | \$200,000+ | Overnight gap risk is the R driver, not the Greeks. |
| Single name \$300+ , defined risk (\$10 wide) | ~\$750 | \$75,000 | \$150,000 | Strike increment sets the floor; you cannot go narrower. |
| Single name \$300+ , strangle | \$3,000–\$5,000 | **\$300,000–\$500,000** | \$750,000+ | One position consumes a \$250k book's entire per-trade budget. |
| Delta-hedged option position (SPY-scale) | ~\$500 option leg | **\$75,000–\$100,000** | \$150,000 | Binding constraint is hedge capital: ±100 shares of a \$640 underlying is \$64,000 notional (~\$32,000 at Reg-T initial), plus per-rehedge friction. |

Redo the column with your own r: `min_account = R_per_contract / r`. At r = 0.25% (the mandatory starting tier for any new strategy, §8.6), every figure above **quadruples**. A strategy you can only afford at full size is a strategy you cannot ramp into, and ramping is not optional.

**The granularity rule — a hard gate, not a guideline.**

```
R_1        = §8.5 stress-node loss of ONE contract of the intended structure
budget     = r × Equity × (strategy's share of the risk budget, §8.6)
if R_1 > budget:  the strategy is not tradeable at this account size.
```

No rounding down, no "just this once," no substituting margin for R because margin is smaller. Trading one contract when the budget permits 0.4 is a 2.5× overbet held for the life of the position, and it is permanent, not occasional — the same trade recurs every cycle.

*Worked rejection.* \$40,000 account, one confirmed strategy, r = 1.0% → budget \$400/trade. Candidate: 25-pt SPX put spread, R = \$1,800. `1,800 > 400` → rejected. The 5-pt version at R = \$350 passes the arithmetic but fails §6.7's liquidity filter (spread > 10% of mid at that width). Correct conclusion: **SPX defined-risk is unavailable at \$40,000.** The substitute is the SPY expression of the same premise — 5-pt SPY vertical, R ≈ \$350 — accepting that SPY is American-style, PM-settled, physically settled, and taxed as ordinary short-term gain rather than under Section 1256's 60/40 treatment. That tax difference is worth roughly 8–10 points of after-tax return on a short-term book. Pay it. It is far cheaper than not trading, and immeasurably cheaper than overbetting SPX.

**What a small account should actually do.**

1. **Defined risk only.** Naked short premium is not a leverage choice at small size, it is a bet-the-account choice: one SPY strangle's stress node is 3.5% of a \$40,000 account, and the §8.7 grid's −10%/+100% node is worse.
2. **Cheaper underlyings, deliberately.** SPY over SPX, QQQ over NDX, sector ETFs over mega-cap single names. You give up Section 1256 treatment and pay more per unit of notional in commission; you gain the ability to size correctly, which dominates.
3. **One strategy, not a portfolio.** Below roughly **\$100,000**, most of §8 is inert — §8.2's Greek limits scale to numbers smaller than one contract's Greeks, §8.4 needs 60 overlapping daily observations per pair you do not have, and §8.9's 3-strategy ceiling is moot. Run one strategy to \$100k, a second to \$250k, a third above that. The Greek book (§8.2) and stress grid (§8.7) are still worth maintaining — they just describe one strategy's positions.
4. **Accept slower confirmation.** §8.6's ramp needs 100+ live trades for full expectancy. At 1–2 concurrent positions and 8 cycles a year, that is years, not quarters. The correct response is patience, not larger size.
5. **Filter unavailable families out at §2.9.** Single-name earnings structures, SPX naked, mega-cap strangles, and delta-hedged vol positions are not "hard" below \$100k — they are unavailable. Do not spec them, do not backtest them, do not build a data pipeline for them.

**Where the check belongs: §2.9, alongside capacity.** Add one disqualifier row to §2.9(a), tested before the spec is written:

| Disqualifier | Test |
|---|---|
| Minimum viable position exceeds risk budget | `R_1contract of the cheapest tradeable expression > r × Equity` |

One line, computable in a minute from a synthetic price (§5.8) and a stress reprice, and it kills the candidate before it consumes a spec, a trial (§4.2), or a data purchase. §2.9 already kills ideas for capacity below account size; this is the mirror image — position size above account size.

**The honest note.** Below roughly **\$30,000**, this entire research program cannot pay for itself. A validated retail options strategy, denominated honestly on capital at risk (§6.6), realistically returns 8–15% a year. On \$25,000 that is \$2,000–\$3,750 gross. Historical options data adequate for §6 runs \$1,200–\$3,000 a year, and Sections 1–7 are 300–600 hours of work before the first live trade. The arithmetic is a negative hourly rate for several years, and it does not improve by trying harder — it improves by having more capital.

Two legitimate responses, neither of them a consolation prize. **Trade one simple, cheap, well-understood structure while building capital from outside income** — a SPY or QQQ defined-risk vertical on a mechanical rule, sized at 1%, journaled per §9.6 — which builds the execution discipline that is the actual bottleneck for most traders and costs nearly nothing. Or **run the program as education**: do Sections 1–5 on free data, learn to build a backtest that does not lie to you, and defer the §6 data purchase until the account can carry it. Both are better uses of the next two years than a correctly-researched strategy you cannot size.

---

## 9. From Proven Hypothesis to Live Trading

A validated hypothesis is a research artifact. A tradeable strategy is a *process*: a job that runs on a clock, a trigger function that cannot drift from the backtest, an order routine with a hard cost budget, a journal that can be joined against backtest rows, and a pre-registered set of conditions under which you stop. This section builds that process. The organizing principle throughout: **every live decision must be traceable to a backtested rule, and every live outcome must be comparable to a backtested outcome.** If a decision has no backtest counterpart, it is discretionary trading wearing a systematic costume.

### 9.1 The Signal Scanner

The scanner is a scheduled job that, for every hypothesis registered as `live`, evaluates its trigger against current market data and emits an actionable alert or a logged non-fire.

**The one rule that matters: one trigger implementation, imported by both the backtest engine and the scanner.** A re-implemented "live version" of the signal is a guaranteed source of divergence — off-by-one bar alignment, a different rolling window convention, a percentile computed on a different lookback. You will not find these by inspection; you will find them six months later as an unexplained 30% shortfall in trade count. Enforce it structurally: the engine and scanner both `import` from `hypotheses/`, and the scanner refuses to run any hypothesis whose spec hash differs from the hash recorded at validation.

```python
# hypotheses/h017_iv_rank_reversion.py  -- imported by BOTH engine and scanner
SPEC_HASH = "e3f1a9..."   # sha256 of the frozen spec dict; see Section 2

def trigger(ctx: Context) -> Signal | None:
    """ctx exposes only point-in-time data: ctx.asof, ctx.hist(field, n), ctx.chain().
    No forward data is reachable by construction -- same object in backtest and live."""
    ivr = ctx.iv_rank(lookback=252)
    if ivr < 0.80:
        return None
    if ctx.adv(20) < 2_000_000 or ctx.chain().median_spread_pct() > 0.06:
        return None
    return Signal(direction="short_vol", strength=ivr, features={"iv_rank": ivr,
                  "rv20": ctx.rv(20), "term_slope": ctx.term_slope()})
```

The backtest loop calls `trigger(ctx_at(t))` over history. The scanner calls `trigger(ctx_live(now))`. Nothing else calls it.

**Schedule with a deadline.** The scan must complete before the entry window opens, with slack for a rerun. If the hypothesis enters at 10:00 ET on the 15-minute bar, the scan runs at 09:55, alerts by 09:57, and a watchdog pages you if no run record exists by 09:58. Use `cron`/`systemd` timers or an orchestrator (Prefect/Airflow) — not a manually started notebook. For end-of-day-signal / next-open-entry strategies, run at 16:15 ET after settlement prints and re-verify at 09:25 the next morning.

**Log every evaluation, fired or not.** This is non-negotiable: live-vs-backtest reconciliation (9.7) needs the denominator. One row per (hypothesis, symbol, asof) with the computed feature values and the fail reason (`iv_rank_below_threshold`, `spread_filter`, `no_expiry_in_dte_window`). When live fires 11 times against a backtested 19/quarter, the log tells you whether the signal genuinely didn't occur or whether your liquidity filter is rejecting chains the backtest accepted.

**Alert format.** The alert must be *executable without further judgment* — everything needed to place and manage the trade:

```json
{"asof":"2026-08-18T09:55:00-04:00","hypothesis_id":"H017","spec_hash":"e3f1a9",
 "underlying":"XLE","signal":{"iv_rank":0.87,"rv20":0.19,"term_slope":-0.03},
 "structure":"short_put_spread",
 "legs":[{"action":"SELL","right":"P","strike":82,"expiry":"2026-09-19","qty":5},
         {"action":"BUY","right":"P","strike":78,"expiry":"2026-09-19","qty":5}],
 "quote_at_alert":{"nbbo_bid":1.22,"nbbo_ask":1.40,"mid":1.31},
 "target_credit":1.31,"walkaway_credit":1.22,"backtest_assumed_fill":1.27,
 "size_basis":"1.0% NAV max loss","max_loss":1345,"margin_req":1345,
 "exit_plan":{"profit_target":"close at 50% of max profit",
              "stop":"close at 2.0x credit received","time_stop":"close at 14 DTE",
              "invalidation":"close if iv_rank < 0.40 at any daily mark"}}
```

Route it to a channel you actually read (Slack webhook, Pushover, email) *and* persist it. The persisted alert is the "intended trade" row that the journal later joins against for slippage measurement.

### 9.2 Paper Trading Protocol

Paper trading proves three things and no others: (1) the plumbing works — auth, chain retrieval, order construction, position reconciliation, error handling on rejects; (2) the signal fires when and where the backtest said it would; (3) you can follow your own process for weeks without improvising.

It does **not** prove fills. Every broker paper engine — IBKR paper, Tradier sandbox, tastytrade demo, Alpaca paper — fills optimistically: at or near mid, instantly, at unlimited size, and with no adverse selection. Paper P&L on a multi-leg options strategy is systematically better than reality by roughly the amount that matters most (the spread), which is precisely the quantity your backtest was most uncertain about.

**The protocol:**

| Requirement | Minimum |
|---|---|
| Duration | 4 weeks *or* one full signal cycle, whichever is longer |
| Trades | 20 signal evaluations logged, ≥10 fired-and-entered |
| Plumbing errors | Zero unhandled exceptions in the final 2 weeks |
| Signal fidelity | Live fire count within the backtest's Poisson 90% band for the period |
| Re-scoring | Every paper trade re-scored at conservative fills before go-live |

**Record the real quoted bid/ask at decision time.** The paper engine's fill price is fiction; the NBBO you saw is data. Capture bid, ask, mid, and quoted size for every leg (and the combo NBBO if the broker publishes one) at alert time, at order-send time, and at fill time. Then re-score: repay the paper P&L assuming you got mid-minus-25%-of-spread on entry and mid-plus-25% on exit, plus commissions and exchange fees. **If the re-scored paper equity curve is not positive, do not go live** — you have discovered that your edge lives inside the spread.

Go-live is not full size. Ramp: 25% of target size for the first 10 trades, 50% for the next 10, 100% thereafter, and only if reconciliation (9.7) shows no divergence flag. The ramp schedule is written into the spec and is not negotiable in the moment (9.9).

### 9.3 The Order Execution Playbook

**Use native combo/multi-leg orders. Never leg in.** Submit spreads as a single BAG/combo order (`ib_insync` `Contract(secType='BAG')` with `ComboLeg`s; Tradier's multileg order endpoint; tastytrade's multi-leg order payload). Legging is a trap for three reasons: you take two spreads instead of one net spread; you carry naked directional risk between fills; and the second leg's price moves *against you* precisely when the first leg fills (the move that filled leg one is the move that reprices leg two). A short put spread legged in a fast tape can leave you short a naked put — an unbounded-risk position your backtest never contained.

**Never send market orders in options.** Displayed size is thin, the NBBO can be 10%+ wide, and a market order in an illiquid series is an invitation. Limit orders only, always.

**Price laddering with a time budget and a walk-away.** Derive the walk-away from the backtest's assumed fill cost — if the backtest assumed mid minus 25% of the spread and cleared its hurdle only under that assumption, the walk-away *is* that price.

```python
def ladder(broker, combo, mid, spread, side, backtest_fill, budget_s=180):
    walkaway = backtest_fill                    # hard limit from the backtest
    step = max(0.01, round(spread * 0.10, 2))   # 10% of spread per step
    px, t0 = mid, time.time()
    while time.time() - t0 < budget_s:
        oid = broker.place(combo, limit=px, tif="DAY")
        if broker.wait_fill(oid, seconds=30):
            return broker.fill_report(oid)
        broker.cancel(oid)
        px = px - step if side == "SELL" else px + step   # step toward the natural
        if (side == "SELL" and px < walkaway) or (side == "BUY" and px > walkaway):
            log_missed(combo, reason="cost_budget_exceeded", best_px=px, mid=mid)
            return None
    log_missed(combo, reason="time_budget_expired", best_px=px, mid=mid)
    return None
```

**Participation cap.** Size so the order is at most ~10% of the option's 20-day average daily volume in that series, and never more than the displayed size at your limit times a small multiple. If the signal's sizing rule demands more than the cap allows, take the capped size and log the shortfall — do not spread the order across strikes the backtest never tested.

**When the fill doesn't come: the trade does not exist.** Do not chase past the walk-away. Log a `missed` row with the same schema as a real trade (intended legs, size, best price reached, reason). Missed trades are data: if 30% of signals go unfilled, your live expectancy is drawn from a *selected* subset of signals — usually the calm ones — and the backtest overstates you. That bias is only measurable if misses are logged.

### 9.4 The Pre-Trade Checklist

Run this before every entry. Automate what you can and make the un-automatable items an explicit typed confirmation the order router requires.

| # | Check | Pass condition | Blocking? |
|---|---|---|---|
| 1 | Signal confirmed by scanner | Alert exists, spec_hash matches registry | Yes |
| 2 | Liquidity filters | Spread ≤ X% of mid; OI ≥ N; quoted size ≥ order size | Yes |
| 3 | Events | No earnings, ex-div, FOMC, or index rebalance inside holding window unless the spec explicitly includes them | Yes |
| 4 | Position size | Max loss ≤ risk-budget % of NAV; ramp stage respected | Yes |
| 5 | Aggregate Greeks *after* adding | Portfolio net delta/vega/gamma within Section 8 limits post-trade, not pre-trade | Yes |
| 6 | Max loss acceptable | Defined and financeable; assignment/pin risk understood for short strikes | Yes |
| 7 | Exit rule written down | All four exits populated in the alert | Yes |
| 8 | No unintended composite | New position + existing positions in same underlying ≠ a structure you never tested | Yes |
| 9 | Correlation/cluster | Not exceeding cluster cap (same sector/vol regime) | Yes |
| 10 | Margin/buying power | Post-trade requirement < 50% of available | Yes |

Item 8 deserves emphasis: a short put spread in XLE plus an existing long call in XLE is a *synthetic risk-reversal* whose behavior neither backtest describes. Check net exposure per underlying, not per order.

### 9.5 Exit Discipline

**Every exit is defined at entry and is mechanical.** Four exits, all populated, all backtested:

| Exit | Definition | Source |
|---|---|---|
| Profit target | Close at X% of max profit / X% of credit | Backtested, per-strategy |
| Stop / max loss | Close at multiple of credit, or structural max loss if defined-risk hold | Backtested |
| Time stop | Close at N DTE or N days held | Backtested |
| Signal invalidation | Close when the entry condition ceases to hold | Backtested |

Discretionary exits destroy correspondence with the backtest, and asymmetrically: you will cut winners early (relief) and hold losers (hope), which converts a positive-expectancy strategy with fat right-tail dependence into a negative one. The backtest's distribution is a distribution *of the exit rule you tested*. Change the exit and you have an untested strategy.

**Hold-to-expiry vs early close.** If the backtest assumed hold-to-expiry, then live must hold to expiry — but expiry has operational hazards backtests silently smooth over: assignment on short ITM strikes (especially the day before ex-dividend for short calls), pin risk at the strike, and expiration-day liquidity. The correct handling is to *re-backtest* the strategy with a rule "close at 15:45 ET on expiration day at the then-quoted mid" and confirm the results are statistically indistinguishable. If they are, adopt the close-on-expiry-day rule as the live rule. If they differ, your edge was in the settlement stub and is likely not harvestable. Never resolve this in the moment.

**Managing winners and losers.** "Close short premium at 50% of max profit" is a real and often beneficial rule — and it is also folklore that has been repeated into the status of scripture. It must be backtested *on your hypothesis*, as a parameter sweep (25/50/75%), reported with the same overfitting discipline as the entry (Section 4), and chosen for robustness of the plateau, not the peak. The same applies to rolling: a roll is a new trade requiring a new signal check, not a continuation. If your spec doesn't contain a roll rule, you don't roll.

### 9.6 The Trade Journal as a Database

Prose journals are unqueryable and therefore worthless for reconciliation. The journal is a table. It is the single most valuable artifact you will build, because it is the only thing that lets you *join live to backtest*.

```sql
CREATE TABLE trades (
  trade_id          TEXT PRIMARY KEY,
  ts_signal         TIMESTAMPTZ NOT NULL,   -- when the scanner fired
  ts_decision       TIMESTAMPTZ NOT NULL,   -- when quotes were captured
  ts_fill           TIMESTAMPTZ,            -- NULL for missed
  hypothesis_id     TEXT NOT NULL,
  spec_hash         TEXT NOT NULL,          -- FK to frozen spec
  status            TEXT NOT NULL,          -- filled | missed | rejected | discretionary
  underlying        TEXT NOT NULL,
  signal_values     JSONB NOT NULL,         -- every feature at entry
  structure         TEXT NOT NULL,
  legs              JSONB NOT NULL,         -- [{action,right,strike,expiry,qty,mult}]
  qty               INTEGER NOT NULL,
  quote_bid         NUMERIC, quote_ask NUMERIC, quote_mid NUMERIC,
  quoted_size       INTEGER,
  intended_fill     NUMERIC,                -- limit at first send
  backtest_fill     NUMERIC NOT NULL,       -- what the backtest assumed
  actual_fill       NUMERIC,
  slippage_vs_bt    NUMERIC GENERATED ALWAYS AS (actual_fill - backtest_fill) STORED,
  commissions       NUMERIC,
  max_loss          NUMERIC NOT NULL,
  margin_req        NUMERIC,
  ramp_stage        TEXT,
  exit_rule         JSONB NOT NULL,         -- the four exits, as written at entry
  ts_exit           TIMESTAMPTZ,
  exit_reason       TEXT,                   -- target|stop|time|invalidation|expiry|manual
  exit_fill         NUMERIC,
  realized_pnl      NUMERIC,
  holding_days      NUMERIC,
  override_flag     BOOLEAN DEFAULT FALSE,
  notes             TEXT
);
CREATE TABLE signal_log (                    -- every evaluation, fired or not
  ts TIMESTAMPTZ, hypothesis_id TEXT, spec_hash TEXT, underlying TEXT,
  fired BOOLEAN, fail_reason TEXT, features JSONB
);
```

`missed` rows carry NULL fills but full intent. `override_flag` and `exit_reason='manual'` are how discretion becomes measurable rather than invisible.

### 9.7 Live-vs-Backtest Reconciliation

Monthly, per hypothesis. Four comparisons:

**1. Trade count.** Expected fires over the period come from backtested frequency λ. Treat counts as Poisson: flag if observed is outside the 95% interval of Poisson(λ·T). Then decompose using `signal_log` — a shortfall from `fail_reason='spread_filter'` is a data/liquidity problem, not a dead edge.

**2. Slippage.** Mean and 90th percentile of `slippage_vs_bt`. If mean slippage exceeds the backtest assumption, re-run the backtest at the *observed* slippage and check whether the edge survives. This single check retires more strategies than any other.

**3. Expectancy.** Compare live mean P&L per trade to the backtest's bootstrap distribution. Concretely: bootstrap 10,000 resamples of backtested per-trade P&L at the live sample size *n*, take the 5th–95th percentiles, and ask whether the live mean falls inside. Outside the lower bound is a divergence flag, not an automatic kill (see 9.8).

```python
bt_boot = np.array([rng.choice(bt_pnl, size=n, replace=True).mean()
                    for _ in range(10_000)])
lo, hi = np.percentile(bt_boot, [5, 95])
flag = live_pnl.mean() < lo
```

**4. Power.** Be honest about *n*. With backtested per-trade Sharpe-equivalent effect size d = mean/std, detecting a 50% degradation at 80% power needs roughly n ≈ 8/(0.5·d)² trades. For a typical d ≈ 0.25, that is ~500 trades — far more than you will have in year one. **Consequence:** expectancy tests are low-power and slow; slippage and trade-count tests are high-power and fast. Weight your monitoring accordingly, and treat expectancy divergence as a size-reduction trigger long before it is statistically conclusive.

### 9.8 Edge Decay Detection and the Kill Switch

These thresholds are written into the hypothesis spec **before the first live trade**, alongside the entry and exit rules, and are hashed with it. Setting them after a loss streak is rationalization.

| Trigger | Threshold (calibrate from backtest) | Required response |
|---|---|---|
| Drawdown from strategy equity peak | > 1.5× max backtested DD | Halt; review before restart |
| " | > 1.0× max backtested DD | Cut size 50% |
| Consecutive losses | > 99th pct of backtested streak length (simulate it; don't guess) | Cut size 50%; halt at +2 beyond |
| Rolling expectancy (last 30 trades) | < 0 | Cut size 50% |
| " | < 0 for 60 trades | Retire |
| Live mean vs backtest bootstrap | Below 5th pct at n ≥ 30 | Cut size 50% and re-backtest at live slippage |
| Mean slippage | > 1.5× assumed for 20 trades | Halt; re-backtest; restart only if edge survives |
| Trade count | Outside Poisson 95% band 2 months running | Investigate data/filters; halt if unexplained |
| Structural change | Mechanism-level: exchange rule/fee change, product change (e.g. new expiry cycle), the counterparty flow you were fading disappears, market-maker structure shifts | Immediate halt regardless of P&L |

The structural trigger is the one that saves you the most money and the one systems ignore, because it fires while P&L still looks fine. If your hypothesis says "we are paid for absorbing overnight hedging flow," and that flow migrates to a new product, the edge is gone before the drawdown arrives. Write the *mechanism* into the spec and review it quarterly against reality.

"Halt" means flat and stopped, not "reduce and hope." "Retire" means the spec moves to `retired` status and may only return through full re-validation on out-of-sample data that includes the failure period.

### 9.9 Process Guardrails

Framed as enforceable rules, not aspirations:

- **No manual override without logging it as a separate discretionary trade.** If you close early on a hunch, it is logged with `override_flag=TRUE`, `exit_reason='manual'`, and it is *excluded* from systematic reconciliation and tracked as its own P&L stream. Review that stream quarterly. Almost universally it loses; that fact is the argument.
- **No size increases outside the ramp schedule.** Size is a function of NAV and the spec, computed by code, not typed by hand. A good month is not a reason.
- **Mandatory cooling-off after a kill-switch trip.** Minimum 5 trading days flat in that strategy before any restart, and restart is at 50% size regardless of the diagnosis.
- **No new live strategy while another is in drawdown-triggered review.** Adding strategies during drawdown is the reflex to "do something," and it stacks correlated risk exactly when your risk model is already off.
- **Weekly review is scheduled and time-boxed.** Watching intraday marks is not monitoring; it is exposure to your own reflexes.

### 9.10 The Operating Calendar

| Cadence | Task | Output / gate |
|---|---|---|
| Daily pre-open (09:00–09:30 ET) | Data freshness check; corporate-action feed; scanner dry-run health | Green/red; page on red |
| Daily (per spec time) | Scanner run → alerts; pre-trade checklist; execute via ladder | Alert rows; trade or `missed` rows |
| Daily post-close (16:15 ET) | Mark all positions; check exit triggers for next open; portfolio Greek snapshot; reconcile broker positions vs internal book | Position/Greek table; break report (must be zero) |
| Weekly (Fri PM) | Slippage & trade-count reconciliation; journal completeness audit; next week's earnings/ex-div/macro calendar vs open positions | Divergence flags; event conflicts resolved |
| Monthly | Full live-vs-backtest test (9.7) per hypothesis; kill-switch evaluation; discretionary-stream review; ramp-stage advancement | Size decisions, halt/retire decisions |
| Quarterly | Re-validate every live strategy on the new quarter's data appended to the sample; re-check the structural mechanism; re-run cost sensitivity at observed slippage; resize or retire | Updated spec (new hash) or retirement |
| Annually | Rebuild the whole pipeline from raw data on a clean machine; verify the backtest reproduces stored results bit-for-bit | Reproducibility certificate |

The annual reproducibility rebuild is the discipline that keeps the research stack honest as it accumulates patches. If last year's backtest no longer reproduces, you do not know what you are trading.

---

## 10. The Candidate Library

The inventory of hypotheses to feed through this pipeline lives in its own file:

> **[`Hypotheses.md`](Hypotheses.md)** — the candidate hypothesis library.

**Why it is separate.** This document is the *method* and should change rarely — when you learn something about how to test, not about what to test. The candidate library is the *material* and changes constantly: entries get added, demoted, killed, and superseded, and by the §0.2 funnel most of them will be dead within a year. Keeping them in one file would mean every dead idea churns the methodology, and the two have completely different rates of change.

**What lives there:**

| Part | Contents |
|---|---|
| Status index | Every candidate id, one line, current status, pipeline position |
| Active candidates | Full nine-field entries across six families — variance risk premium, events, microstructure, volatility regime, skew, directional |
| Deferred | Parked candidates and the reason |
| Rejected / not pursued | Dead entries retained with their cause, so nothing is re-tested by accident |
| Prioritization | Which to run first, ranked by measured independent-cluster counts from the §2.9b pre-flight |
| Anti-patterns | Popular retail "strategies" that are not hypotheses, and precisely what each is missing |
| Adding a candidate | The checklist for a new entry |

**The rule that connects the two files.** A candidate may not be promoted to ACTIVE in `Hypotheses.md` until it has cleared the §2.9 pre-flight here — measured cluster count recorded, viability screen applied, disqualifiers checked. Ideas are cheap; the gate is what makes the library worth reading.

**Current run order:** EV-01 (single-name earnings) and DIR-01 (vol-adjusted extreme moves), then EV-02 (scheduled macro). Two candidates that ranked highly on reasoning — VT-03 and VRP-02 — were demoted after measurement showed one has only 86 independent clusters and the other fires on roughly 75% of all sessions. See the prioritization section there for the numbers.

## 11. The Build Order — Sequenced Roadmap

The sections above are organized by concept. This section is organized by **what to do next**. Work top to bottom; do not start a phase until its predecessor's exit criteria are met. Time estimates assume a serious part-time effort (10–15 hrs/week) and are calibration, not deadlines.

### 11.1 Phase map

| Phase | Weeks | Objective | Exit criteria |
|---|---|---|---|
| **P0 — Scaffolding** | 1 | Repo, data loader, cache, manifest | `make data` fetches SPY/QQQ/VIX history, all ingest assertions pass, results are reproducible from a spec hash |
| **P1 — Idea inventory** | 1–2 | 40 raw ideas → 12 written specs | 12 specs committed as YAML, each passing the disqualifier gate; triage scores assigned |
| **P2 — Engine** | 2 | Point-in-time event-study engine + trial log | Engine refuses to run an unregistered spec; `trials.jsonl` appends on every run; shift-by-one sanity test wired in |
| **P3 — Stage 1 sweep** | 3–4 | Run the top 6–8 specs through stage 1 | Each has a diagnostic pack and a PASS/FAIL/KILLED verdict with cause of death recorded |
| **P4 — Gauntlet** | 2 | Anti-overfitting protocol on survivors | Permutation, placebo, parameter-plateau, cost-sensitivity results logged; overfitting scorecard filled per survivor |
| **P5 — Translation** | 1–2 | Choose structures for 2–4 survivors | Move/premium ratio computed; structure, strike deltas, expiry rule specified; Greek budget confirms the edge Greek dominates |
| **P6 — Options data** | 1 | Buy chains for the specific names/dates you now need | Normalized chain table built; synthetic-vs-real reconciliation report produced |
| **P7 — Stage 2** | 3–4 | Options-wrapped backtest with pessimistic fills | Cost-stress ladder run; smells-wrong checklist clean; result cards emitted |
| **P8 — Final exam** | 1 | Sealed holdout, one shot, per hypothesis | Promotion gauntlet table filled; pass → P9, fail → retired with post-mortem |
| **P9 — Paper** | 6–8 | Scanner + paper trading | Live signal count matches backtested frequency; quoted spreads recorded; discipline held |
| **P10 — Live, small** | ongoing | Trade at reduced size on the ramp schedule | Monthly reconciliation shows live results inside the backtest CI |
| **P11 — Portfolio** | ongoing | Add setup #2, #3 | Aggregate Greek limits and stress grid enforced before each addition |

**Realistic total to first live trade: four to six months.** Anyone promising faster is skipping P3 or P4, which is exactly where the false positives get removed.

### 11.2 The first two weeks, concretely

If you do nothing else, do this — and note that **counting comes before specifying**. Steps 3 and 4 are the cheapest filter in the document and will re-order your candidate list before you have written a single spec.

1. `git init` the structure from §1. Add `pyproject.toml` with pinned `pandas`, `numpy`, `scipy`, `statsmodels`, `yfinance`, `pyarrow`, `py_vollib`, `pyyaml`, `pytest`. Use `uv`; commit the lockfile.
2. Write the ingest and loader with the §1.4 assertions — including the **feed-liveness** check, which is separate from historical gap detection. Pull SPY, QQQ, IWM and the VIX complex to parquet, with a manifest.
3. **Run the §2.9b sample-size pre-flight on every candidate in `Hypotheses.md` before writing any spec.** Count raw events and independent clusters. This takes minutes, touches no outcome, and burns no trial. Expect it to demote candidates you were confident about — that is the point.
4. **Apply the §2.9c viability screen.** Discard anything whose effect is too small to clear an option bid/ask regardless of how good its statistics look, and anything whose trigger fires on more than roughly half of all sessions (that is a regime, not a signal).
5. Write `research/eventstudy.py`: given trigger dates and a horizon, return the conditional outcome distribution, the unconditional baseline, and the permutation p-value. ~150 lines, and the single highest-leverage file in the repo.
6. Agree a **trial budget per hypothesis** and wire it into the runner before the first backtest — mandatory if anything automated is executing runs (§4.2).
7. Write specs only for candidates that survived steps 3–4. Commit them. Note the hashes.
8. Run stage 1. Expect most to fail or come back marginal. That is the correct outcome and it means your tests work.

### 11.3 Definition of done, per hypothesis

A hypothesis is **DONE (tradeable)** when this table is fully green:

| Artifact | Location | Gate |
|---|---|---|
| Registered spec, hash in git history | `hypotheses/H-YYYY-NNN.yaml` | §2.7–2.8 |
| Stage-1 diagnostic pack | `results/<id>/<spec_hash>/stage1/` | §3.8 thresholds met |
| Overfitting scorecard | `results/<id>/<spec_hash>/gauntlet/` | §4.9 go |
| Structure + Greek budget | spec `structure:` block + §5 worksheet | §5.9 edge Greek dominates |
| Stage-2 result card, cost ladder | `results/<id>/<spec_hash>/stage2/` | §6.3 bar cleared |
| Promotion gauntlet table | `results/<id>/<spec_hash>/promotion.md` | §7.8 all rows pass |
| Sealed-holdout exam, one run | `results/<id>/<spec_hash>/holdout.md` | §7.9 pass |
| Kill-switch thresholds | spec `kill_switch:` block, added pre-live | §9.8 pre-registered |
| Scanner entry | `live/scanner.py` registry | §9.1 shared trigger fn |
| Paper trade log ≥ N trades | `journal/` | §9.2 minimum met |

### 11.4 The ten failure modes that end this project

Ordered by how often they actually kill solo research programs:

1. **Never finishing the funnel** — testing idea #1 for six months instead of testing twelve ideas once each. Breadth first; depth only on survivors.
2. **Silent trial inflation** — twenty variants tried, one reported. The fix is mechanical: the engine logs every run whether you want it to or not.
3. **Skipping stage 1** — going straight to option P&L, where theta and spread noise make everything look either amazing or terrible for reasons unrelated to the hypothesis.
4. **Holdout contamination** — "just one more look." Once looked at twice, it is gone; treat it as spent and go find a new out-of-sample period by waiting.
5. **Mid-price fills** — the most flattering and most common lie in options backtesting. It routinely converts losing strategies into winners.
6. **Ignoring margin** — quoting returns on premium collected rather than capital at risk, which overstates short-premium strategies by roughly an order of magnitude.
7. **Mislabeling risk premium as edge** — selling vol works on average; that is compensation for bearing crash risk, not a signal. If your setup doesn't beat the always-on version, know that you are a vol seller and size accordingly.
8. **Hidden Greek concentration** — three "uncorrelated" strategies that are all short vega, which is one position wearing three hats and it will be revealed on the same day.
9. **Discretionary exits** — the backtest tested a mechanical exit. If you exit by feel, you are trading an untested strategy.
10. **No kill switch** — without pre-registered shutdown rules, a decaying edge is indistinguishable from a drawdown until the account is gone.

### 11.5 Standing rules

- **The spec is the source of truth.** Code implements the spec; when they disagree, the code is wrong.
- **Killed ideas stay in the registry with a cause of death.** This is how you avoid rediscovering the same false positive in eight months.
- **Write the post-mortem before deleting anything.** A hypothesis that failed for an interesting reason often contains the next hypothesis.
- **One new live strategy at a time.** Never add a second while the first is in drawdown-triggered review.
- **Re-validate live strategies quarterly** on newly available data. An edge that worked is not an edge that works.

### 11.6 The Program-Level Stop Criterion

§9.8 tells you when to kill a *strategy*. Nothing so far tells you when to kill *the project*. That omission is how people spend four years testing hypothesis after hypothesis, each failure feeling like progress toward the one that works.

Set this before you start, for the same reason you pre-register everything else: the decision is uninterpretable once you are inside it and emotionally invested.

**Pre-register three budgets.** Write them into `results/index.jsonl`'s header or a `PROGRAM.md` at the repo root, dated, before the first backtest:

| Budget | Suggested starting value | Rationale |
|---|---|---|
| **Candidates** | 40 specs reaching stage 1 | The §0.2 funnel's own input count. If 40 pre-flight survivors yield nothing, the funnel is telling you something. |
| **Calendar** | 12 months of part-time work | Long enough to be fair, short enough to notice. |
| **Money** | A stated cap on data + infrastructure | Options data is the only large line item; decide the ceiling before the first purchase, not after the third. |

Whichever binds first triggers a **mandatory review**, not an automatic quit.

**The review asks three questions, in order.**

1. **Did anything reach stage 2?** If not a single candidate cleared §3.8 in 40 attempts, the problem is upstream of your statistics — most likely you are generating hypotheses from the same narrow well, or your triggers are all state-based and sample-starved (§2.9b). Fix the generator, not the tests.
2. **Did things reach stage 2 and die there consistently?** That is a cost problem, not an edge problem. Every survivor dying to spread and theta means your candidates live in effects too small to clear retail transaction costs. The honest response is to move to effects with larger magnitudes — events rather than conditions (§2.9c) — or to accept that your cost structure excludes this class of trade.
3. **Did something pass everything and then fail live?** That is the most expensive outcome and the most informative. Go to §9.7's reconciliation before concluding anything: a live failure caused by fills or signal-timing divergence is a fixable engineering problem, while one where the effect simply stopped is genuine decay, and decay is evidence the mechanism was real but crowded.

**What "stop" is allowed to mean.** Stopping is not one decision. Ranked by how often it is the right one:

- **Change the class of edge you are hunting.** The most common correct outcome. Frequently the honest finding is that you cannot beat the market's pricing but *can* harvest a risk premium — which is a real, defensible activity with a completely different risk profile and sizing discipline. the anti-patterns section of `Hypotheses.md` is emphatic that most retail options strategies are levered short volatility mislabelled as edge; discovering that this describes you is a finding, not a failure, provided you then size it as the risk transfer it is.
- **Reduce scope.** Keep one strategy running at small size and stop researching. A single validated setup traded patiently is a perfectly good outcome and is exactly what §0.1 defines as done.
- **Stop entirely.** Redeploy the capital to something passive and the time to something else.

**The sunk-cost trap, stated precisely.** The pipeline you have built has value independent of whether any hypothesis survived — the data layer, the event-study engine, the discipline. That value is already banked. It is not a reason to keep testing, and "I've already built all this" is not evidence about the next hypothesis. The 41st candidate has the same prior as the first.

**The one asymmetry worth respecting.** A program that produces no tradeable edge but a rigorous, honest record of 40 dead hypotheses has cost you time and taught you what does not work. A program that abandons its own gates in year two because nothing has passed will produce a "strategy," and that strategy will lose money with the confidence of something that passed a test you had already corrupted. Of the two failure modes, only the second is expensive.

> **Rule.** When a budget binds, run the review and write the verdict down. Extending a budget is permitted exactly once, must be pre-registered like anything else, and requires naming what you will do differently — not simply more of the same.

