"""The ONLY way anything reads curated data (Principles.md 1.1, 1.5).

Two rules enforced here rather than by discipline:

  * `close` is raw/unadjusted and is what strike-relative logic must use;
    `close_adj` is derived for returns and realized vol only.
  * `require_fresh` refuses to serve a series staler than `max_stale_days`,
    so a silently-dead vendor feed surfaces as an error and not as a
    flat-lining signal in a backtest.
"""
from __future__ import annotations

import functools
from pathlib import Path

import pandas as pd
import yaml

DATA_ROOT = Path("data")


def _safe(symbol: str) -> str:
    return symbol.replace("^", "_idx_")


def _path(dataset: str, symbol: str, root: Path) -> Path:
    return root / "curated" / dataset / f"symbol={_safe(symbol)}" / "part.parquet"


@functools.lru_cache(maxsize=64)
def _read(dataset: str, symbol: str, root_str: str) -> pd.DataFrame:
    p = _path(dataset, symbol, Path(root_str))
    if not p.exists():
        raise FileNotFoundError(f"{symbol} not ingested for {dataset}: {p} missing. Run `make data`.")
    df = pd.read_parquet(p)
    return df.sort_values("date").reset_index(drop=True)


def load_ohlcv(
    symbol: str,
    *,
    root: Path = DATA_ROOT,
    start: str | None = None,
    end: str | None = None,
    max_stale_days: int | None = None,
) -> pd.DataFrame:
    df = _read("ohlcv_daily", symbol, str(root)).copy()
    df["close_adj"] = df["close"] * df["adj_factor"]
    df = _slice(df, start, end)
    _freshness(df, symbol, max_stale_days)
    return df


def load_index(
    symbol: str,
    *,
    root: Path = DATA_ROOT,
    start: str | None = None,
    end: str | None = None,
    max_stale_days: int | None = None,
) -> pd.DataFrame:
    df = _read("vol_indices", symbol, str(root)).copy()
    df = _slice(df, start, end)
    _freshness(df, symbol, max_stale_days)
    return df


def _slice(df: pd.DataFrame, start: str | None, end: str | None) -> pd.DataFrame:
    if start:
        df = df[df["date"] >= pd.Timestamp(start)]
    if end:
        df = df[df["date"] <= pd.Timestamp(end)]
    return df.reset_index(drop=True)


def _freshness(df: pd.DataFrame, symbol: str, max_stale_days: int | None) -> None:
    if max_stale_days is None or df.empty:
        return
    stale = (pd.Timestamp.utcnow().tz_localize(None).normalize() - df["date"].max()).days
    if stale > max_stale_days:
        raise ValueError(
            f"{symbol} last session {df['date'].max().date()} is {stale}d stale "
            f"(limit {max_stale_days}). Vendor feed may be dead; do not trade on this."
        )


def close_panel(
    symbols: list[str],
    *,
    kind: str = "index",
    root: Path = DATA_ROOT,
    adjusted: bool = False,
) -> pd.DataFrame:
    """Align several series on a common date index. Inner join by design:
    a signal comparing two series may only use dates where both existed."""
    cols = {}
    for s in symbols:
        df = load_index(s, root=root) if kind == "index" else load_ohlcv(s, root=root)
        series = df["close"] * df["adj_factor"] if (adjusted and kind != "index") else df["close"]
        cols[s] = pd.Series(series.to_numpy(), index=df["date"])
    return pd.DataFrame(cols).dropna(how="any").sort_index()


def universe(group: str, path: str = "conf/universe.yaml") -> pd.DataFrame:
    spec = yaml.safe_load(Path(path).read_text())
    rows = spec["groups"][group]
    df = pd.DataFrame(rows)
    df["added"] = pd.to_datetime(df["added"])
    df["removed"] = pd.to_datetime(df["removed"])
    return df


def listed_on(group: str, date: pd.Timestamp, path: str = "conf/universe.yaml") -> list[str]:
    """Point-in-time membership: prevents backtesting a basket of known winners."""
    u = universe(group, path)
    live = (u["added"] <= date) & (u["removed"].isna() | (u["removed"] >= date))
    return u.loc[live, "symbol"].tolist()


def manifest(root: Path = DATA_ROOT) -> dict:
    import json

    p = root / "manifests" / "latest.json"
    if not p.exists():
        raise FileNotFoundError("no ingest manifest; run `make data`")
    return json.loads(p.read_text())
