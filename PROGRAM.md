# Program Pre-Registration

Budgets and standing parameters for this research program, fixed **before** any
backtest was run. Changing anything here requires a dated amendment at the
bottom of this file stating what changed and why — never a silent edit.

See `Principles.md` §4.2 (trial accounting) and §11.6 (program-level stop).

---

## Registered 2026-08-19

| Parameter | Value | Authority |
|---|---|---|
| **Trial budget per hypothesis** | **8** | Decided by the account owner, 2026-08-19, before any stage-1 run |
| Trials counted | Any re-run that changes the question asked of the data: threshold, horizon, lookback, universe, estimator, filter | §4.2 |
| Trials not counted | Bug fixes and re-runs of byte-identical specs | §4.2 |
| Enforcement | `optlab.stats.trials` refuses run 9 for a given hypothesis id | mechanical |
| **Holdout** | Most recent **25%** of each series, sealed | §7.9 |
| Holdout looks permitted | **1**, ever, per hypothesis | §7.9 |
| Candidate budget | 40 specs reaching stage 1 | §11.6 default |
| Calendar budget | 12 months from 2026-08-19 | §11.6 default |
| Money budget | Not yet set — required before the first options-data purchase (§11.1 P6) | **OPEN** |

### Notes on the choices

**Trial budget of 8.** Chosen knowing that an automated researcher can execute
hundreds of variants per hour, which is exactly the condition under which the
§4.1 search arithmetic turns noise into apparent discovery. Eight covers the
parameter choices that are genuinely uncertain a priori and nothing else. The
eight configurations must be enumerated in the spec *before* the first run, so
the denominator is fixed in advance rather than discovered afterwards.

**Holdout at 25%.** For SPY this seals roughly 2018-2026, which contains four
distinct stress episodes (2018, 2020, 2022, 2025). §7.9 also permits a
contiguous 2-3 year holdout, which would return around five years of clusters
to the research set. The longer holdout was preferred because most candidates
here are short-volatility in character, and a holdout without stress episodes
cannot falsify a short-vol strategy at all.

**Money budget is deliberately open.** It must be set before P6, not after, and
it is the one budget that cannot be revised by working harder.

---

## Amendments

_None._
