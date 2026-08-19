"""Point-in-time feature and trigger construction (Principles.md 1.4, 3.4).

Every column here is built so that its value at bar `t` depends only on bars
`<= t`. The one that matters most is the volatility scale in `z`: the natural
way to write it is

    z = today_return / (std(returns over the last 20 days) / sqrt(252))

and the natural implementation includes *today's* return in that 20-day
window. That is not lookahead in the usual sense -- the number is knowable at
the close -- but it is a measurement error that works against the hypothesis:
a large move inflates its own denominator and so shrinks its own z-score.
Measured on SPY, including today collapses the `z < -3` count from 99 to 33.
The window is therefore shifted by one bar by default, and `rv_shift` is a
declared spec field rather than a constant here, so the choice is visible in
the spec hash rather than buried in code (11.5).

Trigger predicates are evaluated from the spec's `{field, op, value}` form.
Code contains no thresholds.
"""
from __future__ import annotations

import operator
from dataclasses import dataclass

import numpy as np
import pandas as pd

from optlab.io import loader

_OPS = {
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
    "==": operator.eq,
    "!=": operator.ne,
}


class FeatureError(ValueError):
    """Raised when a spec asks for a field or operator that does not exist."""


@dataclass
class Features:
    """Aligned point-in-time feature frame plus the price series to trade."""

    frame: pd.DataFrame
    price: pd.Series          # close_adj -- returns and realized vol only (1.4)
    price_raw: pd.Series      # unadjusted close -- anything strike-relative

    def __len__(self) -> int:
        return len(self.frame)


def build(
    symbol: str,
    *,
    rv_window: int = 20,
    rv_shift: int = 1,
    start: str | None = None,
    end: str | None = None,
) -> Features:
    """Build the DIR-01 feature set for one symbol.

    `rv_shift=1` excludes the current bar from the volatility scale; see the
    module docstring for why that is the default and not a detail.
    """
    if rv_shift < 0:
        raise FeatureError(f"rv_shift must be >= 0, got {rv_shift}")

    df = loader.load_ohlcv(symbol, start=start, end=end)
    idx = pd.DatetimeIndex(df["date"])

    close_adj = pd.Series(df["close_adj"].to_numpy(), index=idx, name="close_adj")
    close_raw = pd.Series(df["close"].to_numpy(), index=idx, name="close")
    open_raw = pd.Series(df["open"].to_numpy(), index=idx, name="open")

    logret = np.log(close_adj).diff()

    # Annualized close-to-close realized vol. shift(rv_shift) is what makes the
    # scale strictly prior-bar information.
    rv = logret.rolling(rv_window).std().shift(rv_shift) * np.sqrt(252)

    # Daily move in units of its own prior volatility.
    z = logret / (rv / np.sqrt(252))

    # Overnight gap against the previous *unadjusted* close: this is a price
    # relationship, not a return, so it must not use the adjusted series (1.4).
    gap = open_raw / close_raw.shift(1) - 1.0

    frame = pd.DataFrame(
        {
            "logret": logret,
            "rv": rv,
            "z": z,
            "gap": gap,
            "abs_gap": gap.abs(),
            "abs_z": z.abs(),
        }
    )

    return Features(frame=frame, price=close_adj, price_raw=close_raw)


def evaluate(features: Features, arm: dict) -> pd.Series:
    """Turn a spec arm `{field, op, value}` into a boolean trigger series.

    NaNs are false, never dropped: a warm-up bar where the feature is not yet
    defined must not fire, and must not silently shift the index either.
    """
    for key in ("field", "op", "value"):
        if key not in arm:
            raise FeatureError(f"trigger arm missing required key {key!r}: {arm}")

    field, op, value = arm["field"], arm["op"], arm["value"]
    if field not in features.frame.columns:
        raise FeatureError(
            f"unknown trigger field {field!r}; available: "
            f"{sorted(features.frame.columns)}"
        )
    if op not in _OPS:
        raise FeatureError(f"unknown operator {op!r}; available: {sorted(_OPS)}")

    col = features.frame[field]
    fired = _OPS[op](col, value)
    return fired.where(col.notna(), False).astype(bool)


def regime_buckets(features: Features, n: int = 3) -> pd.Series:
    """Trailing-vol terciles for the 3.7 by-regime diagnostic.

    Uses the same shifted `rv` as the trigger, so the bucket a bar lands in was
    knowable before its outcome window opened.
    """
    rv = features.frame["rv"]
    try:
        return pd.qcut(rv, n, labels=False, duplicates="drop")
    except ValueError:  # too few distinct values to form n buckets
        return pd.Series(np.nan, index=rv.index)
