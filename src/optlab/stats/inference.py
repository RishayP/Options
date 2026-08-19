"""Inference for overlapping, clustered event studies (Principles.md 3.6).

The recurring hazard here is that trigger events are not independent. A
state-based trigger ("vol is elevated") stays on for weeks, so 1,000 firing
days may be 80 episodes. Naive t-stats and naive permutations both treat those
1,000 rows as 1,000 observations and overstate significance by roughly the
square root of the collapse ratio -- an order of magnitude in practice.

Everything here is built to respect that.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats as sps


# --------------------------------------------------------------------------
# clustering
# --------------------------------------------------------------------------
def cluster_ids(dates: pd.Series | pd.DatetimeIndex, hold_days: int,
                slack: float = 1.4) -> np.ndarray:
    """Label events that fall inside one holding window as a single episode.

    `slack` converts a trading-day horizon to calendar days (~1.4x).
    """
    d = pd.DatetimeIndex(pd.Series(dates).sort_values())
    if len(d) == 0:
        return np.array([], dtype=int)
    gap_limit = hold_days * slack
    ids = np.zeros(len(d), dtype=int)
    anchor = d[0]
    k = 0
    for i, x in enumerate(d):
        if (x - anchor).days > gap_limit:
            k += 1
            anchor = x
        ids[i] = k
    return ids


def n_clusters(dates, hold_days: int, slack: float = 1.4) -> int:
    ids = cluster_ids(dates, hold_days, slack)
    return int(ids[-1] + 1) if len(ids) else 0


def collapse_ratio(dates, hold_days: int) -> float:
    n = len(pd.Series(dates))
    c = n_clusters(dates, hold_days)
    return float(n / c) if c else float("nan")


# --------------------------------------------------------------------------
# effect size and power
# --------------------------------------------------------------------------
def min_detectable_effect(n_eff: int, sigma: float, alpha: float = 0.05,
                          power: float = 0.80) -> float:
    """Smallest true effect this sample could have detected.

    Used by 4.10 to separate NO_EFFECT (the study could have seen the claimed
    effect and did not) from INSUFFICIENT_SAMPLE (it never had the resolution).
    """
    if n_eff <= 1:
        return float("inf")
    z_a = sps.norm.ppf(1 - alpha / 2)
    z_b = sps.norm.ppf(power)
    return float((z_a + z_b) * sigma / np.sqrt(n_eff))


def required_n(effect: float, sigma: float, alpha: float = 0.05,
               power: float = 0.80) -> int:
    if effect == 0:
        return 2**31 - 1
    z_a = sps.norm.ppf(1 - alpha / 2)
    z_b = sps.norm.ppf(power)
    return int(np.ceil(((z_a + z_b) * sigma / abs(effect)) ** 2))


# --------------------------------------------------------------------------
# HAC t-statistic
# --------------------------------------------------------------------------
def hac_tstat(outcome: np.ndarray, trigger: np.ndarray, maxlags: int) -> tuple[float, float, float]:
    """OLS of outcome on a trigger dummy with Newey-West errors.

    Returns (effect, tstat, pvalue). Overlapping outcome windows induce
    autocorrelation; without the HAC correction the t-stat is inflated.
    """
    import statsmodels.api as sm

    y = np.asarray(outcome, dtype=float)
    d = np.asarray(trigger, dtype=float)
    ok = np.isfinite(y) & np.isfinite(d)
    y, d = y[ok], d[ok]
    if d.sum() < 2 or (1 - d).sum() < 2:
        return (np.nan, np.nan, np.nan)
    X = sm.add_constant(d)
    fit = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": max(1, maxlags)})
    return (float(fit.params[1]), float(fit.tvalues[1]), float(fit.pvalues[1]))


# --------------------------------------------------------------------------
# permutation
# --------------------------------------------------------------------------
def block_permutation_test(outcome: np.ndarray, trigger: np.ndarray,
                           block: int, n_draws: int = 10_000,
                           seed: int = 0) -> tuple[float, float, np.ndarray]:
    """Permutation test that preserves the trigger's run-length structure.

    Naive permutation shuffles the trigger day by day, destroying the fact that
    it fires in runs. That makes the null far too easy to beat: 3.6 records a
    case where naive gave p=0.008 and the block version p=0.14 on the same data.

    Implemented as a circular rotation of the trigger series, which preserves
    run lengths exactly while breaking any relationship to the outcome.
    """
    y = np.asarray(outcome, dtype=float)
    d = np.asarray(trigger, dtype=bool)
    ok = np.isfinite(y)
    y, d = y[ok], d[ok]
    n = len(y)
    if n == 0 or d.sum() == 0:
        return (np.nan, np.nan, np.array([]))

    observed = y[d].mean() - y[~d].mean() if (~d).any() else np.nan
    rng = np.random.default_rng(seed)
    null = np.empty(n_draws)
    shifts = rng.integers(block, n - block, size=n_draws) if n > 2 * block else rng.integers(1, max(2, n), size=n_draws)
    for i, s in enumerate(shifts):
        dd = np.roll(d, int(s))
        null[i] = y[dd].mean() - y[~dd].mean() if (~dd).any() and dd.any() else np.nan

    null = null[np.isfinite(null)]
    if null.size == 0:
        return (observed, np.nan, null)
    # two-sided, with the +1 correction so p is never exactly zero
    p = (1 + np.sum(np.abs(null) >= abs(observed))) / (1 + null.size)
    return (float(observed), float(p), null)


# --------------------------------------------------------------------------
# bootstrap
# --------------------------------------------------------------------------
def stationary_bootstrap_ci(values: np.ndarray, stat=np.mean,
                            n_boot: int = 5_000, mean_block: int = 10,
                            alpha: float = 0.05, seed: int = 0) -> tuple[float, float, float]:
    """Percentile CI under a stationary (geometric-block) bootstrap."""
    v = np.asarray(values, dtype=float)
    v = v[np.isfinite(v)]
    n = len(v)
    if n < 3:
        return (float("nan"),) * 3
    rng = np.random.default_rng(seed)
    p = 1.0 / max(1, mean_block)
    out = np.empty(n_boot)
    for b in range(n_boot):
        idx = np.empty(n, dtype=int)
        i = rng.integers(0, n)
        for k in range(n):
            idx[k] = i
            i = rng.integers(0, n) if rng.random() < p else (i + 1) % n
        out[b] = stat(v[idx])
    lo, hi = np.percentile(out, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return (float(stat(v)), float(lo), float(hi))


# --------------------------------------------------------------------------
# proportions
# --------------------------------------------------------------------------
def proportion_ci(k: int, n: int, alpha: float = 0.05) -> tuple[float, float, float]:
    from statsmodels.stats.proportion import proportion_confint

    if n == 0:
        return (float("nan"),) * 3
    lo, hi = proportion_confint(k, n, alpha=alpha, method="wilson")
    return (k / n, float(lo), float(hi))


def sign_test(outcome: np.ndarray, baseline_median: float) -> tuple[int, int, float]:
    y = np.asarray(outcome, dtype=float)
    y = y[np.isfinite(y)]
    pos = int((y > baseline_median).sum())
    n = int((y != baseline_median).sum())
    if n == 0:
        return (pos, n, float("nan"))
    return (pos, n, float(sps.binomtest(pos, n, 0.5).pvalue))


@dataclass
class Deflated:
    sharpe: float
    deflated: float
    n_trials: int


def deflated_sharpe(sr: float, n_obs: int, n_trials: int,
                    skew: float = 0.0, kurt: float = 3.0) -> Deflated:
    """Probability the observed Sharpe exceeds the best expected from `n_trials`
    of pure noise (Bailey & Lopez de Prado). Not proof of an edge -- only that
    the result is not explained by the size of the search."""
    if n_obs < 3 or n_trials < 1:
        return Deflated(sr, float("nan"), n_trials)
    e = 0.5772156649
    z = sps.norm.ppf(1 - 1.0 / n_trials) if n_trials > 1 else 0.0
    z2 = sps.norm.ppf(1 - 1.0 / (n_trials * np.e)) if n_trials > 1 else 0.0
    sr0 = (1 - e) * z + e * z2                      # expected max under the null
    denom = np.sqrt(1 - skew * sr + (kurt - 1) / 4 * sr**2)
    if denom <= 0:
        return Deflated(sr, float("nan"), n_trials)
    stat = (sr - sr0) * np.sqrt(n_obs - 1) / denom
    return Deflated(sr, float(sps.norm.cdf(stat)), n_trials)
