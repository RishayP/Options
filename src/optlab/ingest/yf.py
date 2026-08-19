"""yfinance ingest -> canonical curated schema (Principles.md 1.2, 1.4).

Canonical rule from 1.4: store UNADJUSTED OHLC plus a separate `adj_factor`.
Adjusted closes rewrite history and silently break every moneyness, delta and
strike-relative filter downstream. Returns are computed from close*adj_factor;
anything touching a strike uses raw close.
"""
from __future__ import annotations

import time

import pandas as pd
import yfinance as yf

from optlab.validate.checks import INDEX_COLUMNS, OHLCV_COLUMNS


def _flatten(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """yfinance returns MultiIndex columns for some call shapes; normalise."""
    if isinstance(df.columns, pd.MultiIndex):
        lvl0 = df.columns.get_level_values(0)
        lvl1 = df.columns.get_level_values(1)
        # the ticker may sit in either level depending on version/shape
        if symbol in set(lvl1):
            df = df.xs(symbol, axis=1, level=1)
        elif symbol in set(lvl0):
            df = df.xs(symbol, axis=1, level=0)
        else:
            df = df.droplevel(1, axis=1)
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    return df


def _download(symbol: str, start: str, sleep_s: float = 1.0) -> pd.DataFrame:
    raw = yf.download(
        symbol,
        start=start,
        auto_adjust=False,
        actions=False,
        progress=False,
        threads=False,
    )
    time.sleep(sleep_s)
    if raw is None or len(raw) == 0:
        raise RuntimeError(f"yfinance returned no rows for {symbol}")
    return _flatten(raw, symbol)


def fetch_ohlcv(symbol: str, start: str, sleep_s: float = 1.0) -> pd.DataFrame:
    df = _download(symbol, start, sleep_s)
    need = {"open", "high", "low", "close", "adj_close", "volume"}
    if not need.issubset(df.columns):
        raise RuntimeError(f"{symbol}: unexpected columns {sorted(df.columns)}")

    out = pd.DataFrame(
        {
            "date": pd.to_datetime(df.index).tz_localize(None).normalize(),
            "symbol": symbol,
            "open": df["open"].astype("float64").to_numpy(),
            "high": df["high"].astype("float64").to_numpy(),
            "low": df["low"].astype("float64").to_numpy(),
            "close": df["close"].astype("float64").to_numpy(),
            "adj_factor": (df["adj_close"] / df["close"]).astype("float64").to_numpy(),
            "volume": df["volume"].fillna(0).astype("int64").to_numpy(),
        }
    )
    return out.sort_values("date").reset_index(drop=True)[OHLCV_COLUMNS]


def fetch_index(symbol: str, start: str, sleep_s: float = 1.0) -> pd.DataFrame:
    """Volatility indices: no volume, no adjustment, OHLC only."""
    df = _download(symbol, start, sleep_s)
    if "close" not in df.columns:
        raise RuntimeError(f"{symbol}: no close column, got {sorted(df.columns)}")
    for c in ("open", "high", "low"):
        if c not in df.columns:
            df[c] = df["close"]

    out = pd.DataFrame(
        {
            "date": pd.to_datetime(df.index).tz_localize(None).normalize(),
            "symbol": symbol,
            "open": df["open"].astype("float64").to_numpy(),
            "high": df["high"].astype("float64").to_numpy(),
            "low": df["low"].astype("float64").to_numpy(),
            "close": df["close"].astype("float64").to_numpy(),
        }
    )
    out = out.dropna(subset=["close"])
    return out.sort_values("date").reset_index(drop=True)[INDEX_COLUMNS]
