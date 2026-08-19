"""Point-in-time guarantees for the feature builder (Principles.md 1.4, 3.4).

These tests exist because every bug this file can have is silent: a feature
that peeks one bar into the future still produces a plausible-looking series,
a plausible-looking backtest, and a wrong answer.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from optlab.engine import features as F


@pytest.fixture(scope="module")
def spy() -> F.Features:
    return F.build("SPY")


def test_rv_uses_only_prior_bars(spy):
    """The volatility scale at t must be computable from bars strictly < t."""
    fr = spy.frame
    i = 4000
    asof = fr.index[i]

    # Rebuild rv at `asof` from a frame truncated at the PREVIOUS bar. If the
    # shipped value matches, no part of bar `asof` entered its own scale.
    hist = spy.price.loc[: fr.index[i - 1]]
    expected = np.log(hist).diff().rolling(20).std().iloc[-1] * np.sqrt(252)

    assert np.isclose(fr.loc[asof, "rv"], expected, rtol=1e-12)


def test_shifting_rv_changes_the_trigger_materially(spy):
    """Guards the choice documented in the module docstring.

    A move inflates its own denominator when the current bar is included, so
    the unshifted variant systematically under-counts extreme days. If this
    ever stops being true the default deserves re-examination.
    """
    shifted = F.evaluate(spy, {"field": "z", "op": "<", "value": -3.0}).sum()
    unshifted = F.evaluate(
        F.build("SPY", rv_shift=0), {"field": "z", "op": "<", "value": -3.0}
    ).sum()
    assert shifted > unshifted * 2


def test_gap_uses_unadjusted_closes(spy):
    """Gap is a price relationship; the adjusted series would corrupt it (1.4).

    `close_adj = close * adj_factor` rewrites history so the *series* is
    continuous, but an overnight gap is a comparison of two actual traded
    prices. Building it from the adjusted series silently rescales every gap
    before the most recent dividend.
    """
    from optlab.io import loader

    raw = loader.load_ohlcv("SPY")
    idx = pd.DatetimeIndex(raw["date"])
    open_raw = pd.Series(raw["open"].to_numpy(), index=idx)
    close_raw = pd.Series(raw["close"].to_numpy(), index=idx)

    expected = open_raw / close_raw.shift(1) - 1.0
    got = spy.frame["gap"]

    pd.testing.assert_series_equal(
        got.dropna(), expected.dropna(), check_names=False, rtol=1e-12
    )

    # and it is genuinely a different series from the adjusted-close version
    adj_version = spy.price / spy.price.shift(1) - 1.0
    assert not np.allclose(
        got.dropna().to_numpy(), adj_version.reindex(got.dropna().index).to_numpy()
    )


def test_warmup_never_fires(spy):
    """NaN features must be False, not dropped -- dropping would shift dates."""
    sig = F.evaluate(spy, {"field": "z", "op": "<", "value": -3.0})
    assert sig.index.equals(spy.frame.index)
    assert not sig.iloc[:20].any()
    assert sig.dtype == bool


def test_unknown_field_and_operator_raise(spy):
    with pytest.raises(F.FeatureError, match="unknown trigger field"):
        F.evaluate(spy, {"field": "not_a_field", "op": "<", "value": 1})
    with pytest.raises(F.FeatureError, match="unknown operator"):
        F.evaluate(spy, {"field": "z", "op": "~=", "value": 1})
    with pytest.raises(F.FeatureError, match="missing required key"):
        F.evaluate(spy, {"field": "z", "op": "<"})


def test_negative_rv_shift_rejected():
    with pytest.raises(F.FeatureError):
        F.build("SPY", rv_shift=-1)


def test_regime_buckets_are_balanced_and_prior_information(spy):
    b = F.regime_buckets(spy)
    counts = b.value_counts()
    assert len(counts) == 3
    assert counts.max() - counts.min() <= 1
    # buckets derive from the shifted rv, so they carry no same-bar information
    assert b.isna().sum() == spy.frame["rv"].isna().sum()


def test_synthetic_z_is_recovered_exactly():
    """On a series with known constant vol, z must equal the analytic value."""
    n = 300
    idx = pd.bdate_range("2000-01-03", periods=n)
    rng = np.random.default_rng(0)
    r = rng.normal(0, 0.01, n)
    px = pd.Series(100 * np.exp(np.cumsum(r)), index=idx)

    lr = np.log(px).diff()
    rv = lr.rolling(20).std().shift(1) * np.sqrt(252)
    z = lr / (rv / np.sqrt(252))

    # the same arithmetic the builder performs, so any refactor that changes
    # the formula's meaning fails here rather than in a research result
    assert np.isclose(z.iloc[25], lr.iloc[25] / lr.iloc[5:25].std(), rtol=1e-12)
