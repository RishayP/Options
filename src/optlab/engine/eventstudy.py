"""Stage-1 event study (Principles.md 3.2-3.8).

Given trigger dates and a horizon, return the conditional outcome distribution,
the unconditional baseline, and the full 3.7 diagnostic pack. Two structural
guarantees are enforced here rather than left to care:

  * **Entry is never on the trigger bar.** The outcome window opens at t+1, so
    a close-triggered signal cannot be filled at that same close (3.4).
  * **The comparison is conditional vs unconditional**, never vs zero (3.2).
    Equities drift up; a positive conditional mean proves nothing on its own.

The engine also refuses to look at data past the holdout boundary unless
explicitly unsealed, which happens once per hypothesis, ever (7.9).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from optlab.stats import inference as inf


@dataclass
class Diagnostics:
    n_events: int
    n_clusters: int
    collapse_ratio: float
    by_year: pd.DataFrame
    by_regime: pd.DataFrame
    effect_drop_top3: float
    effect_leave_out_best_year: float
    perm_p_leave_out_best_year: float
    effect_delayed_one_bar: float
    equity_curve: pd.Series


class _NotEvaluated:
    """A gate that could not be checked, e.g. no round-trip cost configured (3.8).

    Falsy on purpose: verdict() is a plain all() over the gate values, and a
    gate that silently passes when unconfigured is worse than no gate at all.
    """

    __slots__ = ()

    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return "NOT_EVALUATED"


NOT_EVALUATED = _NotEvaluated()

Gate = bool | _NotEvaluated


def _retention(a: float, b: float) -> float:
    """Fraction of baseline effect `b` that variant effect `a` retains (3.8).

    A zero or non-finite baseline retains nothing measurable, so it scores 0.0
    and fails every retention gate rather than passing on a ratio that was
    never computed.
    """
    if not np.isfinite(a) or not np.isfinite(b) or b == 0:
        return 0.0
    return abs(a) / abs(b)


@dataclass
class EventStudyResult:
    name: str
    horizon: int
    n_events: int
    n_clusters: int
    cond_mean: float
    uncond_mean: float
    effect: float
    cond_median: float
    uncond_median: float
    hac_t: float
    hac_p: float
    perm_p: float
    boot_lo: float
    boot_hi: float
    sign_pos: int
    sign_n: int
    sign_p: float
    mde: float
    diagnostics: Diagnostics = field(repr=False, default=None)

    def gates(self, min_events=50, min_clusters=20, max_perm_p=0.01,
              min_abs_t=2.5, min_year_sign_frac=0.70, min_year_events=5,
              min_regime_agree=2, roundtrip_cost=None,
              cost_multiple=3.0, max_lob_perm_p=0.05) -> dict[str, Gate]:
        """The 3.8 hard gates. All must pass before options work begins.

        `roundtrip_cost` is a caller-supplied number (conf/settings.yaml), not a
        constant: 11.5 says code implements the spec and holds no thresholds.
        Left at None the cost gate reports NOT_EVALUATED, which is falsy.
        """
        d = self.diagnostics
        sgn = np.sign(self.effect)

        # cost gate: unconfigured means unknown, never "fine" (3.8)
        if roundtrip_cost is None:
            cost = NOT_EVALUATED
        else:
            cost = bool(np.isfinite(self.effect)
                        and abs(self.effect) >= cost_multiple * abs(float(roundtrip_cost)))

        # sign consistency, by year: only years carrying enough events vote (3.7)
        voters = d.by_year[d.by_year["n"] >= min_year_events] if len(d.by_year) else d.by_year
        if sgn == 0 or len(voters) == 0:
            year_sign = NOT_EVALUATED if len(voters) == 0 else False
        else:
            year_sign = bool((np.sign(voters["effect"]) == sgn).mean() >= min_year_sign_frac)

        # sign consistency, by trailing-RV tercile (3.7); no terciles, no verdict
        rg = d.by_regime
        if rg is None or len(rg) < 3:
            regime_sign = NOT_EVALUATED
        elif sgn == 0:
            regime_sign = False
        else:
            regime_sign = bool(int((np.sign(rg["effect"]) == sgn).sum()) >= min_regime_agree)

        return {
            "events>=%d" % min_events: bool(self.n_events >= min_events),
            "clusters>=%d" % min_clusters: bool(self.n_clusters >= min_clusters),
            "effect>=%gx_roundtrip_cost" % cost_multiple: cost,
            "perm_p<=%.3g" % max_perm_p: bool(np.isfinite(self.perm_p) and self.perm_p <= max_perm_p),
            "|hac_t|>=%.1f" % min_abs_t: bool(np.isfinite(self.hac_t) and abs(self.hac_t) >= min_abs_t),
            "same_sign_in>=%d%%_of_years" % round(min_year_sign_frac * 100): year_sign,
            "same_sign_in>=%d_of_3_regimes" % min_regime_agree: regime_sign,
            "top3_removal_keeps_50%": bool(
                np.sign(d.effect_drop_top3) == sgn
                and _retention(d.effect_drop_top3, self.effect) >= 0.50
            ),
            "leave_out_best_year_keeps_60%": bool(
                np.sign(d.effect_leave_out_best_year) == sgn
                and _retention(d.effect_leave_out_best_year, self.effect) >= 0.60
            ),
            "leave_out_best_year_perm_p<=%.2g" % max_lob_perm_p: (
                NOT_EVALUATED if not np.isfinite(d.perm_p_leave_out_best_year)
                else bool(d.perm_p_leave_out_best_year <= max_lob_perm_p)
            ),
            "one_bar_delay_keeps_70%": bool(
                np.sign(d.effect_delayed_one_bar) == sgn
                and _retention(d.effect_delayed_one_bar, self.effect) >= 0.70
            ),
        }

    def verdict(self, **kw) -> str:
        g = self.gates(**kw)
        # bool() so NOT_EVALUATED counts as not passing, never as a pass
        return "PASS" if all(bool(v) for v in g.values()) else "FAIL"

    def report(self, **kw) -> str:
        g = self.gates(**kw)
        lines = [
            f"{self.name}   horizon={self.horizon}d",
            "-" * 62,
            f"  events {self.n_events}   clusters {self.n_clusters}   "
            f"collapse {self.diagnostics.collapse_ratio:.1f}x",
            f"  conditional  mean {self.cond_mean:+.4f}   median {self.cond_median:+.4f}",
            f"  uncondition. mean {self.uncond_mean:+.4f}   median {self.uncond_median:+.4f}",
            f"  EFFECT       {self.effect:+.4f}   "
            f"[{self.boot_lo:+.4f}, {self.boot_hi:+.4f}] 95% block-bootstrap",
            f"  HAC t {self.hac_t:+.2f} (p={self.hac_p:.4f})   "
            f"block-permutation p={self.perm_p:.4f}",
            f"  sign test {self.sign_pos}/{self.sign_n} (p={self.sign_p:.4f})",
            f"  min detectable effect at this sample: {self.mde:.4f}",
            "",
            "  3.8 gates:",
        ]
        for k, v in g.items():
            mark = "NOT EVAL" if v is NOT_EVALUATED else ("PASS" if v else "FAIL")
            lines.append(f"    [{mark:^8}] {k}")
        if any(v is NOT_EVALUATED for v in g.values()):
            lines.append("    (NOT EVAL = gate unconfigured or uncomputable; counts as not passing)")
        lines.append(f"\n  VERDICT: {self.verdict(**kw)}")
        return "\n".join(lines)


def forward_outcome(px: pd.Series, horizon: int, kind: str = "logret") -> pd.Series:
    """Outcome measured from t+1 to t+1+h. Never uses the trigger bar's close."""
    lp = np.log(px.astype(float))
    if kind == "logret":
        fwd = lp.shift(-horizon) - lp
    elif kind == "abs_logret":
        fwd = (lp.shift(-horizon) - lp).abs()
    elif kind == "fwd_rv":
        r = lp.diff()
        fwd = r.rolling(horizon).std().shift(-horizon) * np.sqrt(252)
    else:
        raise ValueError(f"unknown outcome kind: {kind}")
    return fwd.shift(-1)  # entry at t+1, not at the trigger close


def run(
    prices: pd.Series,
    trigger: pd.Series,
    *,
    horizon: int,
    name: str = "unnamed",
    outcome: str = "logret",
    holdout_frac: float = 0.25,
    unseal_holdout: bool = False,
    n_perm: int = 10_000,
    seed: int = 0,
) -> EventStudyResult:
    """Run one stage-1 event study.

    `prices` and `trigger` must share an index. `trigger` must have been built
    from data available at or before each bar -- the engine cannot verify that,
    which is why 3.4 prescribes the one-extra-bar delay test reported below as
    a leak detector: an effect that collapses when delayed was leaking.
    """
    px = prices.dropna().astype(float)
    trig = trigger.reindex(px.index).fillna(False).astype(bool)

    # --- holdout seal (7.9) ------------------------------------------------
    if not unseal_holdout and holdout_frac > 0:
        cut = px.index[int(len(px) * (1 - holdout_frac))]
        px = px.loc[:cut]
        trig = trig.loc[:cut]

    y = forward_outcome(px, horizon, outcome)
    ok = y.notna()
    y, trig_ok = y[ok], trig[ok]

    cond = y[trig_ok]
    uncond = y
    if len(cond) == 0:
        raise ValueError(f"{name}: trigger never fires in the research window")

    effect = float(cond.mean() - uncond.mean())
    ev_dates = trig_ok.index[trig_ok]
    ncl = inf.n_clusters(ev_dates, horizon)

    hac_e, hac_t, hac_p = inf.hac_tstat(y.to_numpy(), trig_ok.to_numpy(), maxlags=horizon)
    _, perm_p, _ = inf.block_permutation_test(
        y.to_numpy(), trig_ok.to_numpy(), block=max(2, horizon), n_draws=n_perm, seed=seed
    )
    _, blo, bhi = inf.stationary_bootstrap_ci(
        cond.to_numpy(), mean_block=max(2, horizon), seed=seed
    )
    spos, sn, sp = inf.sign_test(cond.to_numpy(), float(uncond.median()))
    mde = inf.min_detectable_effect(ncl, float(uncond.std()))

    diag = _diagnostics(px, trig, y, trig_ok, cond, uncond, effect, horizon, outcome,
                        n_perm=n_perm, seed=seed)

    return EventStudyResult(
        name=name, horizon=horizon,
        n_events=int(trig_ok.sum()), n_clusters=ncl,
        cond_mean=float(cond.mean()), uncond_mean=float(uncond.mean()), effect=effect,
        cond_median=float(cond.median()), uncond_median=float(uncond.median()),
        hac_t=hac_t, hac_p=hac_p, perm_p=perm_p,
        boot_lo=blo, boot_hi=bhi,
        sign_pos=spos, sign_n=sn, sign_p=sp, mde=mde,
        diagnostics=diag,
    )


def _diagnostics(px, trig, y, trig_ok, cond, uncond, effect, horizon, outcome,
                 n_perm: int = 10_000, seed: int = 0) -> Diagnostics:
    base = float(uncond.mean())

    # per-year breakdown
    years = cond.index.year
    rows = []
    for yr in sorted(set(years)):
        sel = cond[years == yr]
        rows.append({"year": yr, "n": len(sel), "mean": float(sel.mean()),
                     "effect": float(sel.mean() - base)})
    by_year = pd.DataFrame(rows)

    # regime buckets: trailing-RV terciles (3.7). shift(1) keeps the bucket
    # strictly point-in-time -- it uses returns through the prior close only,
    # so the trigger bar itself can never decide which regime it lands in.
    rv = np.log(px).diff().rolling(20).std().shift(1) * np.sqrt(252)
    rv_ev = rv.reindex(cond.index).dropna()
    codes = None
    if len(rv_ev) >= 3:
        try:
            codes = pd.qcut(rv_ev, 3, labels=False, duplicates="drop")
        except ValueError:                       # degenerate RV, no tercile edges
            codes = None
    rg_rows = []
    if codes is not None and codes.nunique() == 3:
        for c, nm in enumerate(("low_rv", "mid_rv", "high_rv")):
            sel = cond.loc[rv_ev.index[(codes == c).to_numpy()]]
            rg_rows.append({"bucket": nm, "n": len(sel), "mean": float(sel.mean()),
                            "effect": float(sel.mean() - base)})
    by_regime = pd.DataFrame(rg_rows, columns=["bucket", "n", "mean", "effect"])

    # drop the three largest absolute contributors
    if len(cond) > 3:
        order = cond.sub(base).abs().sort_values(ascending=False)
        trimmed = cond.drop(order.index[:3])
        drop3 = float(trimmed.mean() - base)
    else:
        drop3 = float("nan")

    # Leave out the single best year. The year is dropped from the baseline as
    # well as from the events: leaving 2008 in the unconditional mean while
    # removing it from the conditional one measures a difference between two
    # different samples, not the robustness 3.8 is asking about.
    lobY, lob_p = float("nan"), float("nan")
    if len(by_year) > 1:
        best = by_year.loc[by_year["effect"].abs().idxmax(), "year"]
        keep = y.index.year != best
        y_lo, t_lo = y[keep], trig_ok[keep]
        if t_lo.sum() >= 2 and (~t_lo).sum() >= 2:
            lobY = float(y_lo[t_lo].mean() - y_lo.mean())
            # 3.8 requires permutation p <= 0.05 on the leave-out sample too,
            # not merely retained magnitude.
            _, lob_p, _ = inf.block_permutation_test(
                y_lo.to_numpy(), t_lo.to_numpy(),
                block=max(2, horizon), n_draws=n_perm, seed=seed,
            )

    # one-extra-bar delay: a leak detector, not a robustness nicety
    y_del = y.shift(-1)
    m = y_del.notna() & trig_ok
    delayed = float(y_del[m].mean() - y_del.dropna().mean()) if m.any() else float("nan")

    equity = cond.sub(base).cumsum()

    return Diagnostics(
        n_events=int(len(cond)),
        n_clusters=inf.n_clusters(cond.index, horizon),
        collapse_ratio=inf.collapse_ratio(cond.index, horizon),
        by_year=by_year,
        by_regime=by_regime,
        effect_drop_top3=drop3,
        effect_leave_out_best_year=lobY,
        perm_p_leave_out_best_year=lob_p,
        effect_delayed_one_bar=delayed,
        equity_curve=equity,
    )
