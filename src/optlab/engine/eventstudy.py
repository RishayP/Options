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
    effect_drop_top3: float
    effect_leave_out_best_year: float
    effect_delayed_one_bar: float
    equity_curve: pd.Series


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
              min_abs_t=2.5) -> dict[str, bool]:
        """The 3.8 hard gates. All must pass before options work begins."""
        d = self.diagnostics
        keep = lambda a, b: (abs(a) >= abs(b) * 0.0) if b == 0 else (abs(a) / abs(b))
        return {
            "events>=%d" % min_events: self.n_events >= min_events,
            "clusters>=%d" % min_clusters: self.n_clusters >= min_clusters,
            "perm_p<=%.3g" % max_perm_p: np.isfinite(self.perm_p) and self.perm_p <= max_perm_p,
            "|hac_t|>=%.1f" % min_abs_t: np.isfinite(self.hac_t) and abs(self.hac_t) >= min_abs_t,
            "top3_removal_keeps_50%": (
                np.isfinite(d.effect_drop_top3)
                and np.sign(d.effect_drop_top3) == np.sign(self.effect)
                and keep(d.effect_drop_top3, self.effect) >= 0.50
            ),
            "leave_out_best_year_keeps_60%": (
                np.isfinite(d.effect_leave_out_best_year)
                and keep(d.effect_leave_out_best_year, self.effect) >= 0.60
            ),
            "one_bar_delay_keeps_70%": (
                np.isfinite(d.effect_delayed_one_bar)
                and keep(d.effect_delayed_one_bar, self.effect) >= 0.70
            ),
        }

    def verdict(self, **kw) -> str:
        g = self.gates(**kw)
        return "PASS" if all(g.values()) else "FAIL"

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
            lines.append(f"    [{'PASS' if v else 'FAIL'}] {k}")
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

    diag = _diagnostics(px, trig, y, trig_ok, cond, uncond, effect, horizon, outcome)

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


def _diagnostics(px, trig, y, trig_ok, cond, uncond, effect, horizon, outcome) -> Diagnostics:
    base = float(uncond.mean())

    # per-year breakdown
    years = cond.index.year
    rows = []
    for yr in sorted(set(years)):
        sel = cond[years == yr]
        rows.append({"year": yr, "n": len(sel), "mean": float(sel.mean()),
                     "effect": float(sel.mean() - base)})
    by_year = pd.DataFrame(rows)

    # drop the three largest absolute contributors
    if len(cond) > 3:
        order = cond.sub(base).abs().sort_values(ascending=False)
        trimmed = cond.drop(order.index[:3])
        drop3 = float(trimmed.mean() - base)
    else:
        drop3 = float("nan")

    # leave out the single best year
    if len(by_year) > 1:
        best = by_year.loc[by_year["effect"].abs().idxmax(), "year"]
        rest = cond[years != best]
        lobY = float(rest.mean() - base) if len(rest) else float("nan")
    else:
        lobY = float("nan")

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
        effect_drop_top3=drop3,
        effect_leave_out_best_year=lobY,
        effect_delayed_one_bar=delayed,
        equity_curve=equity,
    )
