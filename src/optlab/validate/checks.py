"""Ingest-time data sanity assertions (Principles.md 1.4).

Every curated frame passes through `run_checks` before it is written. A HARD
failure aborts the ingest; a SOFT failure is recorded in the manifest so the
condition is visible later rather than silently absorbed into a backtest.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

OHLCV_COLUMNS = ["date", "symbol", "open", "high", "low", "close", "adj_factor", "volume"]
INDEX_COLUMNS = ["date", "symbol", "open", "high", "low", "close"]


@dataclass
class CheckResult:
    symbol: str
    dataset: str
    hard: list[str] = field(default_factory=list)
    soft: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.hard

    def as_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "dataset": self.dataset,
            "passed": self.passed,
            "hard": self.hard,
            "soft": self.soft,
        }


def run_checks(df: pd.DataFrame, *, dataset: str, symbol: str, cfg: dict) -> CheckResult:
    r = CheckResult(symbol=symbol, dataset=dataset)
    v = cfg.get("validation", {})
    expected = OHLCV_COLUMNS if dataset == "ohlcv_daily" else INDEX_COLUMNS

    # --- schema -----------------------------------------------------------
    missing = [c for c in expected if c not in df.columns]
    if missing:
        r.hard.append(f"missing columns: {missing}")
        return r  # nothing further is meaningful
    if list(df.columns) != expected:
        r.hard.append(f"column order drift: {list(df.columns)} != {expected}")

    if len(df) < v.get("min_rows", 200):
        r.hard.append(f"only {len(df)} rows (min {v.get('min_rows', 200)})")

    # --- index integrity --------------------------------------------------
    if df["date"].duplicated().any():
        dups = df.loc[df["date"].duplicated(), "date"].dt.date.unique()[:5]
        r.hard.append(f"duplicate dates, e.g. {list(dups)}")
    if not df["date"].is_monotonic_increasing:
        r.hard.append("dates not monotonically increasing")
    if isinstance(df["date"].dtype, pd.DatetimeTZDtype):
        r.hard.append("date column is tz-aware; curated dates must be naive session dates")

    # --- nulls ------------------------------------------------------------
    price_cols = ["open", "high", "low", "close"]
    for c in price_cols:
        n = int(df[c].isna().sum())
        if n:
            r.soft.append(f"{c}: {n} null bars")

    # --- OHLC coherence ---------------------------------------------------
    body = df.dropna(subset=price_cols)
    bad_hl = body["high"] < body["low"]
    if bad_hl.any():
        r.hard.append(f"high < low on {int(bad_hl.sum())} bars")
    out_of_range = (
        (body["high"] < body[["open", "close"]].max(axis=1))
        | (body["low"] > body[["open", "close"]].min(axis=1))
    )
    if out_of_range.any():
        r.hard.append(f"open/close outside high-low on {int(out_of_range.sum())} bars")
    nonpos = (body[price_cols] <= 0).any(axis=1)
    if nonpos.any():
        r.hard.append(f"non-positive price on {int(nonpos.sum())} bars")

    # --- return sanity (split / bad-tick detector) ------------------------
    close = body["close"].to_numpy(dtype=float)
    if close.size > 1:
        ret = np.abs(np.diff(close) / close[:-1])
        lim = float(v.get("max_abs_daily_return", 0.35))
        n_ext = int((ret > lim).sum())
        if n_ext:
            idx = np.argsort(ret)[::-1][:3]
            worst = [
                f"{body['date'].iloc[i + 1].date()}:{ret[i]:.1%}" for i in idx if ret[i] > lim
            ]
            # Volatility indices genuinely move >35% in a day; equities do not.
            bucket = r.soft if dataset == "vol_indices" else r.hard
            bucket.append(f"{n_ext} bars with |return| > {lim:.0%} — {worst}")

    # --- calendar gaps ----------------------------------------------------
    gaps = df["date"].diff().dt.days
    max_gap = int(v.get("max_gap_days", 6))
    n_gap = int((gaps > max_gap).sum())
    if n_gap:
        worst = df.loc[gaps.idxmax(), "date"].date() if gaps.notna().any() else "?"
        r.soft.append(f"{n_gap} session gaps > {max_gap}d (largest ends {worst})")

    # --- adjustment factor ------------------------------------------------
    if dataset == "ohlcv_daily":
        af = df["adj_factor"].dropna()
        if af.empty:
            r.hard.append("adj_factor entirely null")
        else:
            if (af <= 0).any():
                r.hard.append("non-positive adj_factor")
            if not af.is_monotonic_increasing:
                # factors should rise toward 1.0 as you approach the present
                drops = int((af.diff() < -1e-9).sum())
                r.soft.append(f"adj_factor non-monotonic at {drops} points")
            if abs(float(af.iloc[-1]) - 1.0) > 0.02:
                r.soft.append(f"latest adj_factor {float(af.iloc[-1]):.4f} != 1.0")
        neg_vol = int((df["volume"].fillna(0) < 0).sum())
        if neg_vol:
            r.hard.append(f"negative volume on {neg_vol} bars")

    return r


def staleness_days(df: pd.DataFrame, asof: pd.Timestamp) -> int:
    """Calendar days between the frame's last session and `asof`."""
    return int((asof.normalize() - df["date"].max().normalize()).days)
