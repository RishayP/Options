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

### Amendment 1 — 2026-08-19

**What changed.** Two thresholds that §3.8 leaves as prose placeholders are now
registered as numbers, and the split protocol this program actually runs is
stated explicitly.

1. **§3.8 effect-vs-cost gate.** §3.8 requires the conditional-minus-
   unconditional effect to reach **3x** the round-trip cost, offering "1.0 vol
   point for vol trades, 0.30% for directional single-name" as placeholders but
   registering neither. Both are now in `conf/settings.yaml` under
   `stage1_gates` and `roundtrip_cost`, and the engine reads them rather than
   hardcoding them (§11.5).

   *Why now.* The gate is unevaluable without a number, and a number chosen
   after seeing an effect is not a gate. Registering it before the first
   Stage-1 run is the only ordering that means anything. These remain the
   §3.8 placeholders, not measured costs — real ones need the P6 chain
   purchase, and a candidate clearing the gate only on optimistic costs has
   not cleared it.

2. **Split protocol.** §3.5 prescribes a three-way chronological split
   (exploration / validation / sealed holdout). **This program runs the
   two-way variant** already registered above: research vs. the most recent
   25%, sealed, one look ever. There is no separate validation block, so
   §3.8's "must pass in-sample *and* validation" reduces here to "must pass on
   the research window", with the holdout reserved for §7.9's single shot.

   *Why.* Carving a validation block out of the research window would drop
   DIR-01's `z < -3` arm below §3.8's 50-event minimum, and a gate that cannot
   be evaluated is worse than one that is honestly absent. Where §3.5 and this
   file conflict, this file governs — it is the pre-registered document.

**What did not change.** Trial budget (8), holdout fraction (25%), holdout
looks (1), candidate budget (40), calendar budget (12 months). The money
budget remains **OPEN**.

