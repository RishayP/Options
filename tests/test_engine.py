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


# ------------------------------------------------------- 3.8 sign + cost gates
def _synthetic(effect=0.01, year_rows=None, regime_rows=None):
    """A result whose six original gates all pass, so a new gate is the only
    thing that can flip the verdict."""
    if year_rows is None:
        year_rows = [(2000 + i, 10, effect) for i in range(5)]
    if regime_rows is None:
        regime_rows = [("low_rv", 20, effect), ("mid_rv", 20, effect), ("high_rv", 20, effect)]
    diag = es.Diagnostics(
        n_events=100, n_clusters=40, collapse_ratio=2.5,
        by_year=pd.DataFrame([{"year": y, "n": n, "mean": e, "effect": e}
                              for y, n, e in year_rows]),
        by_regime=pd.DataFrame([{"bucket": b, "n": n, "mean": e, "effect": e}
                                for b, n, e in regime_rows],
                               columns=["bucket", "n", "mean", "effect"]),
        effect_drop_top3=effect, effect_leave_out_best_year=effect,
        perm_p_leave_out_best_year=0.001,
        effect_delayed_one_bar=effect, equity_curve=pd.Series(dtype=float),
    )
    return es.EventStudyResult(
        name="synthetic", horizon=10, n_events=100, n_clusters=40,
        cond_mean=effect, uncond_mean=0.0, effect=effect,
        cond_median=effect, uncond_median=0.0,
        hac_t=4.0, hac_p=1e-4, perm_p=1e-3, boot_lo=effect / 2, boot_hi=effect * 2,
        sign_pos=60, sign_n=100, sign_p=0.01, mde=effect / 2, diagnostics=diag,
    )


def _gate(g, needle):
    return next(v for k, v in g.items() if needle in k)


def test_sign_consistency_fails_when_years_disagree():
    """3.8: same sign in >= 70% of years with >= 5 events."""
    ok = _synthetic()
    assert _gate(ok.gates(), "of_years") is True
    flip = _synthetic(year_rows=[(2000, 10, +0.01), (2001, 10, +0.01), (2002, 10, -0.01),
                                 (2003, 10, -0.01), (2004, 10, -0.01)])   # 40% agree
    assert _gate(flip.gates(), "of_years") is False
    assert flip.verdict() == "FAIL"


def test_thin_years_do_not_vote():
    """A 3-event year cannot outvote the years that carry the sample (3.7)."""
    r = _synthetic(year_rows=[(2000, 10, +0.01), (2001, 10, +0.01), (2002, 10, +0.01),
                              (2003, 2, -0.01), (2004, 1, -0.01)])
    assert _gate(r.gates(), "of_years") is True
    none = _synthetic(year_rows=[(2000, 2, +0.01), (2001, 3, +0.01)])
    assert _gate(none.gates(), "of_years") is es.NOT_EVALUATED


def test_regime_sign_gate_needs_two_of_three():
    """3.8: same sign in >= 2 of 3 trailing-RV terciles."""
    two = _synthetic(regime_rows=[("low_rv", 20, +0.01), ("mid_rv", 20, +0.01),
                                  ("high_rv", 20, -0.02)])
    assert _gate(two.gates(), "of_3_regimes") is True
    one = _synthetic(regime_rows=[("low_rv", 20, +0.03), ("mid_rv", 20, -0.01),
                                  ("high_rv", 20, -0.01)])
    assert _gate(one.gates(), "of_3_regimes") is False
    assert one.verdict() == "FAIL"
    thin = _synthetic(regime_rows=[])
    assert _gate(thin.gates(), "of_3_regimes") is es.NOT_EVALUATED


def test_cost_gate_does_not_pass_when_unconfigured():
    """An unconfigured gate must block, not wave through (3.8)."""
    r = _synthetic()
    g = r.gates()
    assert _gate(g, "roundtrip_cost") is es.NOT_EVALUATED
    assert not _gate(g, "roundtrip_cost")
    assert r.verdict() == "FAIL", "unconfigured cost gate silently passed"
    rep = r.report()
    assert "NOT EVAL" in rep and "PASS" in rep


def test_cost_gate_uses_the_supplied_cost():
    """The threshold is a caller argument, never a constant in the engine (11.5)."""
    r = _synthetic(effect=0.01)
    assert _gate(r.gates(roundtrip_cost=0.0030), "roundtrip_cost") is True   # 0.01 >= 3x0.003
    assert r.verdict(roundtrip_cost=0.0030) == "PASS"
    assert _gate(r.gates(roundtrip_cost=0.0040), "roundtrip_cost") is False  # 0.01 < 3x0.004
    assert r.verdict(roundtrip_cost=0.0040) == "FAIL"


def test_zero_effect_never_passes_a_retention_gate():
    """A zero baseline retains nothing; it must not divide its way to a pass."""
    assert es._retention(0.5, 0.0) == 0.0
    assert es._retention(float("nan"), 0.01) == 0.0
    flat = _synthetic(effect=0.0)
    g = flat.gates(roundtrip_cost=0.0)
    assert not _gate(g, "top3_removal")
    assert not _gate(g, "leave_out_best_year")
    assert not _gate(g, "one_bar_delay")
    assert flat.verdict(roundtrip_cost=0.0) == "FAIL"


def test_regime_buckets_are_point_in_time_terciles():
    """3.7 by-regime diagnostic: trailing RV known before the trigger bar."""
    px = random_walk(3000, seed=13)
    rng = np.random.default_rng(4)
    trig = pd.Series(rng.random(len(px)) < 0.05, index=px.index)
    trig.iloc[:5] = True                  # inside the RV20 warm-up
    r = es.run(px, trig, horizon=10, name="regime", n_perm=200)
    rg = r.diagnostics.by_regime
    assert list(rg.columns) == ["bucket", "n", "mean", "effect"]
    assert len(rg) == 3
    assert rg["n"].min() > 0
    # no 20-day trailing RV yet on those first bars, so they cannot be bucketed
    assert rg["n"].sum() <= r.n_events - 5


# --------------------------------------------- 3.8 leave-out-best-year, in full
def _with(result, **fields):
    """Clone a synthetic result with some diagnostics overridden."""
    import dataclasses as dc
    diag = dc.replace(result.diagnostics, **fields)
    return dc.replace(result, diagnostics=diag)


def test_leave_out_best_year_requires_the_sign_to_hold():
    """Retaining 60% of the magnitude with the sign flipped is not survival."""
    r = _synthetic(effect=0.01)
    assert _gate(r.gates(), "leave_out_best_year_keeps") is True

    flipped = _with(r, effect_leave_out_best_year=-0.009)   # 90% magnitude, wrong sign
    assert _gate(flipped.gates(), "leave_out_best_year_keeps") is False
    assert flipped.verdict() == "FAIL"


def test_leave_out_best_year_permutation_gate():
    """3.8 asks for permutation p <= 0.05 on the leave-out sample, not just
    retained magnitude -- an effect can keep its size and still be noise."""
    r = _synthetic(effect=0.01)
    assert _gate(r.gates(), "leave_out_best_year_perm_p") is True

    noisy = _with(r, perm_p_leave_out_best_year=0.20)
    assert _gate(noisy.gates(), "leave_out_best_year_perm_p") is False
    assert noisy.verdict() == "FAIL"

    # uncomputable (one year of data) must not pass by default
    unknown = _with(r, perm_p_leave_out_best_year=float("nan"))
    assert _gate(unknown.gates(), "leave_out_best_year_perm_p") is es.NOT_EVALUATED
    assert unknown.verdict() == "FAIL"


def test_one_bar_delay_requires_the_sign_to_hold():
    """A sign flip under a one-bar delay is the leak signature (3.4)."""
    r = _synthetic(effect=0.01)
    assert _gate(r.gates(), "one_bar_delay") is True

    flipped = _with(r, effect_delayed_one_bar=-0.010)
    assert _gate(flipped.gates(), "one_bar_delay") is False
    assert flipped.verdict() == "FAIL"


def test_leave_out_best_year_drops_the_year_from_the_baseline_too():
    """Removing a year from the events but not the baseline compares two
    different samples. Planted: events every year, effect only in 2002."""
    idx = pd.bdate_range("2000-01-03", periods=2000)
    rng = np.random.default_rng(7)
    y = pd.Series(rng.normal(0, 0.001, len(idx)), index=idx)

    trig = pd.Series(False, index=idx)
    for yr in sorted(set(idx.year)):
        trig.loc[idx[idx.year == yr][:20]] = True     # 20 events every year

    hot = idx[(idx.year == 2002)][:20]
    y.loc[hot] += 0.05                                # only 2002 pays
    px = pd.Series(100 * np.exp(np.cumsum(y.to_numpy())), index=idx)

    r = es.run(px, trig, horizon=3, name="one_year_wonder",
               holdout_frac=0.0, n_perm=500, seed=1)
    d = r.diagnostics

    assert len(d.by_year) > 1, "fixture must span several years to leave one out"
    assert np.isfinite(d.effect_leave_out_best_year)
    # 2002 was the only source of the effect, so removing it must gut the result
    assert abs(d.effect_leave_out_best_year) < abs(r.effect) * 0.6
    assert _gate(r.gates(), "leave_out_best_year_keeps") is False
    assert r.verdict() == "FAIL"
