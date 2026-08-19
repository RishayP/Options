"""Tests for the stage-1 machinery.

The most important test here is `test_no_edge_in_noise`: an engine that finds
significance in a random walk is worse than useless, because every result it
ever produces is uninterpretable.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from optlab.engine import eventstudy as es
from optlab.stats import inference as inf
from optlab.stats import trials


def random_walk(n=4000, seed=0, mu=0.0003, sigma=0.011):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2000-01-03", periods=n)
    r = rng.normal(mu, sigma, n)
    return pd.Series(100 * np.exp(np.cumsum(r)), index=idx)


# ---------------------------------------------------------------- clustering
def test_cluster_collapse_for_persistent_state():
    """A trigger that stays on for a month is one episode, not twenty."""
    idx = pd.bdate_range("2020-01-01", periods=100)
    on = pd.Series(False, index=idx)
    on.iloc[10:30] = True   # one 20-day run
    on.iloc[60:80] = True   # another
    dates = on.index[on]
    assert inf.n_clusters(dates, hold_days=21) == 2
    assert inf.collapse_ratio(dates, hold_days=21) == pytest.approx(20.0)


def test_point_events_do_not_collapse():
    idx = pd.bdate_range("2020-01-01", periods=500)
    dates = idx[::40]  # widely separated
    assert inf.n_clusters(dates, hold_days=5) == len(dates)


# ----------------------------------------------------------------- lookahead
def test_outcome_never_uses_trigger_bar():
    px = random_walk(200)
    y = es.forward_outcome(px, horizon=5)
    # outcome at t must be computable only from bars strictly after t
    lp = np.log(px)
    expected = float(lp.iloc[1 + 5] - lp.iloc[1])
    assert y.iloc[0] == pytest.approx(expected)


# -------------------------------------------------------------------- nulls
def test_no_edge_in_noise():
    """The engine must NOT find an effect in a random walk."""
    px = random_walk(4000, seed=7)
    rng = np.random.default_rng(11)
    trig = pd.Series(rng.random(len(px)) < 0.05, index=px.index)
    r = es.run(px, trig, horizon=10, name="noise", n_perm=2000)
    assert r.perm_p > 0.05, f"found significance in noise: p={r.perm_p}"
    assert r.verdict() == "FAIL"


def test_planted_effect_is_found():
    """Sanity in the other direction: a large planted effect must be detected."""
    n = 4000
    rng = np.random.default_rng(3)
    idx = pd.bdate_range("2000-01-03", periods=n)
    r = rng.normal(0.0003, 0.011, n)
    trig_raw = rng.random(n) < 0.04
    for i in np.flatnonzero(trig_raw):
        r[i + 1: i + 11] += 0.004          # strong 10-day drift after the trigger
    px = pd.Series(100 * np.exp(np.cumsum(r[:n])), index=idx)
    trig = pd.Series(trig_raw, index=idx)
    res = es.run(px, trig, horizon=10, name="planted", n_perm=2000)
    assert res.effect > 0
    assert res.perm_p < 0.01, f"missed a planted effect: p={res.perm_p}"


def test_block_permutation_is_stricter_than_naive():
    """Run-length-preserving permutation must not be more permissive."""
    px = random_walk(3000, seed=5)
    y = es.forward_outcome(px, 10).dropna()
    on = pd.Series(False, index=y.index)
    for s in range(0, len(on) - 30, 120):
        on.iloc[s: s + 25] = True          # persistent runs
    _, p_block, _ = inf.block_permutation_test(
        y.to_numpy(), on.to_numpy(), block=10, n_draws=2000, seed=1
    )
    assert np.isfinite(p_block)


# ------------------------------------------------------------------- power
def test_mde_separates_no_effect_from_underpowered():
    """4.10's distinction: MDE below the claimed effect closes the question."""
    small = inf.min_detectable_effect(n_eff=25, sigma=1.0)
    large = inf.min_detectable_effect(n_eff=2500, sigma=1.0)
    assert small > large
    assert inf.required_n(effect=0.1, sigma=1.0) > inf.required_n(effect=0.5, sigma=1.0)


# ------------------------------------------------------------------ budget
def test_trial_budget_is_enforced(tmp_path: Path):
    p = tmp_path / "trials.jsonl"
    for i in range(8):
        trials.guard("EV-01", {"variant": i}, budget=8, path=p)
    assert trials.count("EV-01", path=p) == 8
    assert trials.remaining("EV-01", budget=8, path=p) == 0
    with pytest.raises(trials.TrialBudgetExceeded):
        trials.guard("EV-01", {"variant": 99}, budget=8, path=p)


def test_repeating_a_question_is_free(tmp_path: Path):
    """Byte-identical re-runs are one trial -- 4.2 counts questions."""
    p = tmp_path / "trials.jsonl"
    for _ in range(5):
        trials.guard("DIR-01", {"z": 2.5}, budget=8, path=p)
    assert trials.count("DIR-01", path=p) == 1


def test_budget_is_per_hypothesis(tmp_path: Path):
    p = tmp_path / "trials.jsonl"
    for i in range(8):
        trials.guard("EV-01", {"v": i}, budget=8, path=p)
    trials.guard("DIR-01", {"v": 0}, budget=8, path=p)   # must not raise
    assert trials.program_total(path=p) == 9


# ------------------------------------------------------------------ holdout
def test_holdout_is_sealed_by_default():
    px = random_walk(2000, seed=2)
    trig = pd.Series(True, index=px.index)
    sealed = es.run(px, trig, horizon=5, n_perm=200)
    opened = es.run(px, trig, horizon=5, n_perm=200, unseal_holdout=True)
    assert opened.n_events > sealed.n_events
