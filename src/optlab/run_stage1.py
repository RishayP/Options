"""Stage-1 runner: spec in, verdict out (Principles.md 2.8, 3.8, 4.2, 7.9).

The order of operations here is the point of the file, and it is deliberately
inconvenient:

  1. refuse to run a spec that is not committed (2.8)
  2. refuse to run a trial the budget will not pay for (4.2)
  3. run, seal the holdout unless explicitly unsealed (7.9)
  4. write the result under the spec hash, so a later edit cannot overwrite it

Every one of those is a refusal rather than a warning. A warning is something a
researcher at 1am can decide to ignore, which is the same as it not existing.

    python -m optlab.run_stage1 --spec specs/H-2026-001.yaml [--trial NAME]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import platform
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from optlab.engine import eventstudy as es
from optlab.engine import features as F
from optlab import specs  # NB: optlab.specs re-exports load/spec_hash as names,
                          # so `from optlab.specs import load` would bind the
                          # function, not the module.
from optlab.stats import trials as tr

RESULTS = Path("results")
SETTINGS = Path("conf/settings.yaml")

# which registered cost applies to which outcome family (3.8)
_COST_KEY = {
    "logret": "logret_directional_etf",
    "abs_logret": "logret_directional_etf",
    "fwd_rv": "vol_points",
}


def _git_sha() -> str:
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                             text=True, check=True)
        return out.stdout.strip()
    except Exception:
        return "unknown"


def _env(seed: int) -> dict:
    import scipy
    import statsmodels

    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scipy": scipy.__version__,
        "statsmodels": statsmodels.__version__,
        "git_sha": _git_sha(),
        "seed": seed,
        "utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
    }


def run_trial(spec: dict, trial: dict, cfg: dict, *, seed: int = 0,
              n_perm: int = 10_000, unseal_holdout: bool = False,
              spec_hash: str = "", write: bool = True) -> es.EventStudyResult:
    """Run one enumerated trial. Registers it against the budget first (4.2)."""
    p = trial["params"]
    arm_name, horizon, outcome = p["arm"], int(p["horizon"]), p["outcome"]

    arm = spec["trigger"]["arms"][arm_name]
    symbol = spec["estimation_universe"][0]

    # 4.2: register the QUESTION before asking it. Raises if the budget is spent.
    key = tr.guard(
        spec["id"],
        {"arm": arm_name, "horizon": horizon, "outcome": outcome,
         "field": arm["field"], "op": arm["op"], "value": arm["value"],
         "rv_window": spec["trigger"]["rv_window"],
         "rv_shift": spec["trigger"]["rv_shift"],
         "symbol": symbol, "unseal_holdout": bool(unseal_holdout)},
        spec_hash=spec_hash,
        note=trial["name"],
    )

    try:
        feats = F.build(
            symbol,
            rv_window=int(spec["trigger"]["rv_window"]),
            rv_shift=int(spec["trigger"]["rv_shift"]),
        )
        trigger = F.evaluate(feats, arm)

        result = es.run(
            feats.price, trigger,
            horizon=horizon,
            name=f"{spec['name']}:{trial['name']}",
            outcome=outcome,
            holdout_frac=0.25,          # PROGRAM.md, registered 2026-08-19
            unseal_holdout=unseal_holdout,
            n_perm=n_perm,
            seed=seed,
        )
    except Exception as exc:
        tr.finish(key, "error", {"error": f"{type(exc).__name__}: {exc}"})
        raise

    gate_kw = _gate_kwargs(cfg, outcome)
    verdict = result.verdict(**gate_kw)

    tr.finish(key, "complete", {
        "trial": trial["name"], "verdict": verdict,
        "effect": result.effect, "perm_p": result.perm_p,
        "hac_t": result.hac_t, "n_events": result.n_events,
        "n_clusters": result.n_clusters,
    })

    if write:
        _write(spec, spec_hash, trial, result, gate_kw, verdict, seed)
    return result


def _gate_kwargs(cfg: dict, outcome: str) -> dict:
    """Thresholds come from conf, never from code (11.5)."""
    g = cfg["stage1_gates"]
    cost = cfg["roundtrip_cost"].get(_COST_KEY.get(outcome))
    return {
        "min_events": g["min_events"],
        "min_clusters": g["min_clusters"],
        "max_perm_p": g["max_perm_p"],
        "min_abs_t": g["min_abs_hac_t"],
        "min_year_sign_frac": g["sign_consistent_year_frac"],
        "min_year_events": g["min_events_per_year"],
        "min_regime_agree": g["sign_consistent_regime_buckets"],
        "roundtrip_cost": cost,
        "cost_multiple": g["effect_vs_cost_multiple"],
    }


def _write(spec, spec_hash, trial, result, gate_kw, verdict, seed) -> Path:
    out = RESULTS / spec["id"] / spec_hash[:16] / "stage1" / trial["name"]
    out.mkdir(parents=True, exist_ok=True)
    d = result.diagnostics

    (out / "report.txt").write_text(result.report(**gate_kw) + "\n")
    d.by_year.to_csv(out / "by_year.csv", index=False)
    d.by_regime.to_csv(out / "by_regime.csv", index=False)
    d.equity_curve.to_csv(out / "equity_by_event.csv", header=["cum_excess"])
    (out / "env.json").write_text(json.dumps(_env(seed), indent=2))

    gates = {k: (None if v is es.NOT_EVALUATED else bool(v))
             for k, v in result.gates(**gate_kw).items()}
    stats = {
        "id": spec["id"], "spec_hash": spec_hash, "trial": trial["name"],
        "params": trial["params"], "verdict": verdict, "gates": gates,
        "n_events": result.n_events, "n_clusters": result.n_clusters,
        "collapse_ratio": d.collapse_ratio,
        "cond_mean": result.cond_mean, "uncond_mean": result.uncond_mean,
        "effect": result.effect,
        "boot_lo": result.boot_lo, "boot_hi": result.boot_hi,
        "hac_t": result.hac_t, "hac_p": result.hac_p, "perm_p": result.perm_p,
        "sign_pos": result.sign_pos, "sign_n": result.sign_n,
        "sign_p": result.sign_p, "mde": result.mde,
        "effect_drop_top3": d.effect_drop_top3,
        "effect_leave_out_best_year": d.effect_leave_out_best_year,
        "perm_p_leave_out_best_year": d.perm_p_leave_out_best_year,
        "effect_delayed_one_bar": d.effect_delayed_one_bar,
        "thresholds": {k: v for k, v in gate_kw.items()},
    }
    (out / "stats.json").write_text(json.dumps(stats, indent=2, default=_jsonable))

    # one line per run, committed -- the greppable denominator for 4.3
    RESULTS.mkdir(parents=True, exist_ok=True)
    with (RESULTS / "index.jsonl").open("a") as fh:
        fh.write(json.dumps({
            "utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "id": spec["id"], "spec_hash": spec_hash, "trial": trial["name"],
            "params": trial["params"], "verdict": verdict,
            "effect": result.effect, "perm_p": result.perm_p,
            "hac_t": result.hac_t, "n_events": result.n_events,
            "n_clusters": result.n_clusters, "git_sha": _git_sha(),
        }, sort_keys=True, default=_jsonable) + "\n")
    return out


def _jsonable(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    return str(o)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Run a registered spec through stage 1")
    ap.add_argument("--spec", required=True)
    ap.add_argument("--trial", action="append",
                    help="trial name; repeatable. default: all enumerated trials")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--n-perm", type=int, default=10_000)
    ap.add_argument("--config", default=str(SETTINGS))
    ap.add_argument("--unseal-holdout", action="store_true",
                    help="7.9: ONE look per hypothesis, ever. Not for iteration.")
    ap.add_argument("--allow-unregistered", action="store_true",
                    help="escape hatch for local experiments; never for a recorded result")
    a = ap.parse_args(argv)

    path = Path(a.spec)
    spec = specs.load(path)
    cfg = yaml.safe_load(Path(a.config).read_text())

    if not a.allow_unregistered:
        specs.require_registered(path, spec)      # 2.8: aborts, does not warn
    else:
        print("WARNING: 2.8 registration check bypassed; this result is not citable.")

    shash = specs.spec_hash(spec)
    wanted = a.trial or [t["name"] for t in spec.get("trials", [])]
    by_name = {t["name"]: t for t in spec.get("trials", [])}
    unknown = [w for w in wanted if w not in by_name]
    if unknown:
        raise SystemExit(f"not enumerated in the spec: {unknown}. "
                         f"Adding one now would break the pre-registered denominator (4.2).")

    print(f"{spec['id']}  {spec['name']}  spec_hash={shash[:16]}")
    print(f"budget: {tr.remaining(spec['id'])} of {tr.DEFAULT_BUDGET} trials left\n")

    rows = []
    for name in wanted:
        result = run_trial(spec, by_name[name], cfg, seed=a.seed, n_perm=a.n_perm,
                           unseal_holdout=a.unseal_holdout, spec_hash=shash)
        kw = _gate_kwargs(cfg, by_name[name]["params"]["outcome"])
        print(result.report(**kw))
        print()
        rows.append((name, result, result.verdict(**kw)))

    print("=" * 62)
    for name, r, v in rows:
        print(f"  {v:4s}  {name:20s} effect {r.effect:+.4f}  "
              f"perm_p {r.perm_p:.4f}  t {r.hac_t:+.2f}  n {r.n_events}")
    print(f"\nbudget remaining: {tr.remaining(spec['id'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
