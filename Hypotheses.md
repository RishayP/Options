# Candidate Hypothesis Library

**The inventory of untested claims that feeds the `Principles.md` pipeline.**

`Principles.md` is the *method* — how an idea is specified, pre-registered, tested, and killed. This file is the *material*: the standing list of candidates that method is applied to. It is a living document. It will grow, and most of what is in it will eventually be discarded.

Three rules govern it.

**Every entry is an untested claim.** Nothing here is a strategy, and nothing here has been shown to work. Each entry is a claim about the data with a named mechanism and a cheap way to be proven wrong. Parameters are round starting values, not optimized; changing them is a research decision that must be logged against the multiple-testing budget (`Principles.md` §4.2). No entry carries performance numbers, because no entry has any.

**Entries are written to be killed cheaply.** The value of a candidate is not how promising it sounds but how fast and how definitively free data can dispose of it. An entry whose falsification condition cannot be stated as a number is not ready to be in this file.

**Entries move down, and nothing is deleted.** As candidates are tested they migrate from `## Active Candidates` to `## Deferred` or `## Rejected / Not Pursued`. A rejected entry keeps its full mechanism description and gains a stated reason for death and a note on what would have to change to revive it. This mirrors `Principles.md` §2.11: dead hypotheses never leave the registry. In eight months you will have the same idea again from a different source, and the cause of death answers it in thirty seconds instead of two days. Deleting failures also destroys the denominator that every false-discovery correction downstream depends on.

**Cross-references.** A bare section reference such as §2.9 or §3.8 always points to `Principles.md`, never to this file. Sections of this file are named in words.

**Notation.** `RV_n` = n-day close-to-close realized vol, annualized 252. Forward windows overlap — block bootstrap, never naive t-stats. Throughout, **effective N = independent episodes, not row count.**

---

## Status Table

The index. Statuses here are library statuses, not registry statuses — nothing in this file has been registered as a spec yet, so none of these carry a `Principles.md` §2.11 status (`REGISTERED`, `STAGE1`, …). "Pipeline position" says where each candidate stands relative to the §2.9 reality gate and the §2.7 spec.

| id | Candidate | Status | Pipeline position |
|---|---|---|---|
| **EV-01** | Single-name earnings IV crush | **ACTIVE** | §2.9 pre-flight passed. **Run first.** Write spec next; paid option data required earlier than any other candidate |
| **DIR-01** | Behavior after vol-adjusted extreme moves and gaps | **STAGE1 DONE** | Registered `H-2026-001`, all 8 trials run 2026-08-19, budget spent. **Directional claim dead (`NO_EFFECT`); volatility claim passed §3.8.** Survives in reduced form — see entry |
| **EV-02** | Scheduled macro vol cycle (FOMC/CPI) | **ACTIVE** | §2.9 pre-flight passed. Run second, after EV-01/DIR-01 |
| **VRP-01** | Conditional short premium at wide IV–RV spread | **ACTIVE** | §2.9 pre-flight passed (259 clusters). Queued; sample fine, effect likely thin vs. costs |
| **VT-01** | VIX9D/VIX ratio as short-horizon regime signal | **ACTIVE** | §2.9 pre-flight passed (166 clusters). Queued; short history (2011+) |
| **MS-03** | Month-end / quarter-end and index-rebalance flow | **ACTIVE** | §2.9 pre-flight passed (~400 events). Queued; literature check required before spec |
| **MS-01** | Monthly OPEX gamma unwind and strike pinning | **ACTIVE** | §2.9 pre-flight passed for arm (a) (~394 cycles). Queued; arm (b) blocked on historical OI by strike |
| **VT-03** | Realized-vol mean reversion after spikes | **ACTIVE** | §2.9 pre-flight passed with almost no margin (86 clusters). **Demoted.** Queued last; any subgroup split breaches §3.8 |
| **VRP-02** | Term-structure-conditioned short vol | **ACTIVE** | §2.9 pre-flight passed but fires 188 days/yr. **Demoted to conditioning overlay on VRP-01**, never a standalone entry |
| **VRP-02b** | VRP-02 backwardation arm | **ACTIVE** | Sub-arm of VRP-02. 57 clusters — marginal. Test separately or not at all |
| **VT-02** | VVIX conditioning of short-vol exposure | **DEFERRED** | Never standalone. Sizing overlay on VRP-01/VRP-02; revisit once a short-vol P&L proxy series exists |
| **SK-01** | Put skew steepness as a conditioning signal | **DEFERRED** | Low usable sample on the free proxy; `^SKEW` is a poor stand-in for tradeable skew |
| **SK-02** | Index vs. component vol (dispersion) | **REJECTED** | Untradeable in a retail account (30–60 legs). Premise not falsifiable on free data |
| **MS-02** | 0DTE intraday behavior into the close | **REJECTED** | Untestable on available data — free intraday coverage is ~60 days, which supports no claim |

---

## Active Candidates

Nine candidates, specified in the `Principles.md` §2.7 field format. Each is an untested claim.

### A. Variance Risk Premium / IV–RV Spread

#### VRP-01 — Conditional short premium at wide IV–RV spread
- **Name / id:** `vrp_conditional_spread_spy`
- **Mechanism:** Hedgers (vol-target funds, pension overlays, retail put buyers) buy index convexity for mandate reasons, not expected return; dealers absorbing that flow are short jump risk and must be paid. Claim: the payment is state-dependent, widest when demand outruns delivered vol.
- **Trigger:** At the close, `spread = VIX − RV20`; enter when positive and in the top tercile of its trailing 2-year distribution, hold 21 days.
- **Predicted effect:** `IV_entry − RV_fwd21` larger in the top tercile than the middle; null is equality across terciles.
- **Stage-1 test:** `^VIX` + `^GSPC` since 1993; mean gap per tercile with block-bootstrapped CIs. Falsified if top tercile is indistinguishable from middle.
- **Candidate structure:** 30-45 DTE short strangle at 15-20 delta.
- **Data needed:** Free; paid chains (ORATS/CBOE DataShop) for Stage 2 only.
- **Confounds:** VIX is a variance-swap strip with a skew loading, not tradeable ATM IV, so the gap overstates the ATM premium. Top-tercile days cluster in 2008/2011/2020, and conditioning on elevated RV is mechanically mean-reverting — few regimes, not many observations.
- **Crowding & decay:** High — the most-harvested premium in the market; assume thinner edge and fatter left tail than any backtest.

#### VRP-02 — Term-structure-conditioned short vol
- **Name / id:** `vrp_term_structure_gate`
- **Mechanism:** Contango indicates calm hedging demand and carry paid to sellers; backwardation means spot risk exceeds forward risk, i.e. the premium is compensating risk currently arriving. The claim is conditionality, not that contango is inherently profitable.
- **Trigger:** `ts = VIX3M/VIX` (or `VX2/VX1`). Short-vol arm when `ts > 1.05`; stand aside or long-vol arm when `ts < 0.98`. 21-day horizon.
- **Predicted effect:** Conditional mean `IV_entry − RV_fwd` larger and steadier in contango, near zero or negative in backwardation; the 1% tail should differ by state too.
- **Stage-1 test:** `^VIX`, `^VIX3M`, plus free CBOE settlement files for true `VX2/VX1`. The by-state difference must survive block bootstrap **and** adding lagged RV as a control.
- **Candidate structure:** VRP-01's strangle, gated by curve state.
- **Data needed:** Free.
- **Confounds:** Backwardation is rare and clustered — tiny effective N. Curve state is near-contemporaneous with realized vol, so the gate may be a lagged-RV filter with no independent content.
- **Crowding & decay:** High; every VIX ETP rebalances on this. Search SSRN/Quantpedia for "variance risk premium term structure" before spending effort.
- **Status note (demotion):** The contango arm fires ~188 days/year — roughly 75% of all sessions. That is not a trigger, it is a description of normal conditions. Register and test it as a **conditioning overlay on VRP-01**, never as a standalone entry, and hold it to the §7.7 benchmark: does the gated version beat the always-on short-vol version? The backwardation arm (VRP-02b, 57 independent clusters) is the only part of this candidate that describes an unusual state, and it is marginal on sample.

### B. Event-Driven

#### EV-01 — Single-name earnings IV crush

**Top-priority candidate.** This entry is longer than the others because it is the one being specified first, and the decisions below have to be settled before the spec is written rather than discovered mid-test.

- **Name / id:** `earnings_iv_crush_largecap`
- **Mechanism:** Retail lottery buying and fund event-hedging bid short-dated options into earnings for reasons unrelated to the variance delivered. Market makers warehousing that inventory take real gap risk; the claim is they are overpaid for it on average. The counterparty is named and constrained: the buyer wants a payoff shape on a known date and is price-insensitive about what it costs, and the dealer cannot decline the inventory.
- **Trigger (headline):** Top ~150 liquid names. On the close before a confirmed report, enter if the first post-earnings expiry's implied move exceeds `1.15 × median(|actual 2-day move|, last 8 reports)`; exit next open.
- **Predicted effect:** `|actual move| / implied_move` has mean below 1 — a claim on the mean **and** the tail shape.
- **Stage-1 test:** Free OHLC plus a scraped earnings calendar (hand-verify a sample); compute `|close(t+1)/close(t−1) − 1|` per event against a proxy implied move. Falsified if the ratio centers at or above 1.
- **Candidate structure:** Short front-expiry strangle or iron condor, defined risk, sized to survive a 3-sigma gap.
- **Data needed:** Free is marginal; a clean Stage 1 wants historical option prices. Date accuracy is the dominant risk.
- **Confounds:** Survivorship in any liquid-names list built today; shifted dates and BMO/AMC misclassification invert the trade window. The mean can look good while a few −8-sigma gaps consume cumulative P&L — read the sum, not the average.
- **Crowding & decay:** High and named; the implied move is publicly quoted. Any edge lives in name selection and structure, not the effect.

##### Trigger, stated precisely

The headline trigger above is not specifiable as written — "top ~150 liquid names" and "the first post-earnings expiry" both hide decisions. Starting values, all round, none optimized:

| Parameter | Starting value | Note |
|---|---|---|
| Universe size | 150 names | See universe construction below; the number is a liquidity cutoff, not a target |
| Underlying liquidity filter | trailing 60-day ADV ≥ $200M **and** share price ≥ $20 | Price floor keeps strike spacing from dominating the structure |
| Option liquidity filter | front-expiry ATM straddle OI ≥ 500 contracts **and** quoted spread ≤ 10% of mid at the entry close | Applied at simulation time and enforced identically live (§6.7) |
| Expiry selected | first listed expiry strictly after the announcement session, DTE ≤ 7 at entry | If no expiry within 7 days exists, the event is dropped, not substituted |
| History lookback `K` | 8 prior reports (~2 years) | Require ≥ 6 usable; otherwise drop the event |
| Richness threshold `θ` | 1.15 | Plateau check at `θ ∈ {1.00, 1.15, 1.30}` per §4.5 — three logged trials, not a search |
| Entry | close of the last regular session strictly before the announcement | See timing below |
| Exit | next open (baseline) | A next-close variant is one additional logged trial, not a free alternative |
| Holding window for clustering | 2 sessions | Feeds the §2.9b cluster count; earnings are point events so raw ≈ clusters |

Every one of these is a parameter the spec must fix in writing before any outcome is computed. Changing one after seeing a result creates a new id (`H-YYYY-NNNb`) and retires the original with a cause of death (§2.8).

##### Universe construction and the survivorship problem

The universe question is not "which names are liquid" — it is "which names *were* liquid, on the date of each event, using only information available then."

Any top-150 list assembled today is the list of companies that survived and grew into it. Testing an earnings effect on that list measures the earnings behavior of eventual winners. The bias is not small and it is not conservative: firms that de-listed, were acquired mid-cycle, or collapsed after a bad print are exactly the events where a short front-expiry strangle takes its worst losses, and they are precisely the ones a today-built list omits.

The fix, in order of preference:

1. **Point-in-time membership.** Reconstruct the universe annually from a historical index-membership source, or from a liquidity rank computed as of each January using only data through the prior December. Include tickers that later de-listed. This requires a price source that retains de-listed symbols — most free sources do not, and that gap *is* the bias, not an inconvenience around it.
2. **Rolling liquidity rank with an explicit delisting audit.** If de-listed history is unavailable, rank names by trailing 60-day dollar volume at each annual rebalance, and separately count how many names present in year *Y* are absent from the price source in year *Y+3*. That count bounds the bias. If it is material, report the result as an upper bound on the effect, never as the effect.
3. **Refuse to test.** If neither is achievable, EV-01's cross-sectional claim cannot be established, and only the single-name time-series version on names with continuous history survives — a much smaller, much more biased sample.

Separately, apply the `Principles.md` §2.7 split between **estimation universe** and **trading universe**. Estimate the effect where the sample is (every name passing a point-in-time liquidity rank, which may be several hundred), and trade it where the liquidity is (the liquid large caps actually intended for trading). The `subgroup_check` field is mandatory and binding here: the effect must retain **≥ 60% of its magnitude with unchanged sign** when restricted to the trading universe alone. An earnings effect that is strong across a wide universe and absent in mega-caps is not tradeable by this account, however clean its aggregate statistics. Given that the stated intent is to trade only liquid large caps, this is the check most likely to kill the candidate — run it early, not at the end.

##### The before/after-close timing problem

This is the single largest source of false confirmation in EV-01, and it is not symmetric noise — it manufactures the result the hypothesis predicts.

A company reporting **after the close (AMC)** on session `t` is first traded on `t+1`. The last pre-announcement close is `t`, so entry is at the `t` close and the event move is `close(t+1)/close(t) − 1`. A company reporting **before the open (BMO)** on session `t` is first traded on `t` itself. The last pre-announcement close is `t−1`, entry is at the `t−1` close, and the event move is `close(t)/close(t−1) − 1`.

Misclassify in either direction and the measured window shifts off the announcement onto an ordinary session:

- **BMO tagged as AMC** → entry at the `t` close, which is *after* the market has already absorbed the news. The implied vol has already collapsed, so the position is sold at post-crush prices, and the measured "event move" is the following quiet day.
- **AMC tagged as BMO** → entry at the `t−1` close and measurement of `close(t)/close(t−1)`, a session containing no announcement at all, while the actual gap on `t+1` is never observed.

Both errors put a low-volatility non-event day in the numerator of `|actual move| / implied_move`. Both therefore push the ratio *down*, toward the hypothesis. A dirty calendar does not add noise to this test; it produces a spurious pass. Treat any strong result on unverified dates as evidence about the calendar, not about the market.

Controls, all required before the spec is registered:

- Hand-verify a random sample of **≥ 100 events** against press-release timestamps, and record the observed error rate in the spec's `known_confounds`.
- Run a mechanical cross-check: for a correctly dated event, the announcement session should be the local maximum of `|return| / (RV20/√252)` within `t−1 … t+2` in a large majority of cases. If the flagged session is the max-move session materially less often than that, the calendar is wrong and no amount of statistics will fix it.
- **Drop ambiguous events; never guess the tag.** Dropping loses sample. Guessing biases toward confirmation, which is worse.
- Apply the §3.4 one-extra-bar-delay test as a sanity check on the whole pipeline.

##### What free data can and cannot establish

This is the point at which EV-01 differs from every other candidate in this file, and the reason it needs a data budget sooner.

**Free daily OHLC plus a verified earnings calendar CAN:**

- Measure the realized move distribution around confirmed announcements — mean, dispersion, and, most importantly, the tail.
- Build the backward-looking baseline `median(|actual 2-day move|, last K reports)` and measure how well it forecasts the next realized move.
- Test the **price-side proxy**: realized move versus a history-derived expectation of the move. This establishes whether earnings moves are systematically smaller than a naive backward-looking forecast.
- Count events and independent clusters for §2.9b, measure event-date accuracy, and run the survivorship audit above.
- Estimate, via a synthetic pricer (§5.8), what a defined-risk structure would have paid at expiry — with the enormous caveat that the entry price is invented, not observed.

**Free data CANNOT establish the premise.** The claim in EV-01 is that *implied* vol collapses by more than the delivered variance justifies. That is a statement about the price the option market actually charged before the announcement and the price it charged after. It requires:

- the pre-announcement front-expiry ATM straddle price (the market's implied move), not a proxy built from history;
- the post-announcement IV level on the same expiry;
- quoted bid/ask at both points, because the entire predicted effect is of the same order as the spread on a single-name weekly.

The distinction matters because the market's implied move and the historical median are not the same object and are not close. The market conditions on information the backward-looking median cannot see: guidance already issued, a recent analyst day, a sector peer that has already reported, a pending deal. Substituting the historical proxy tests a *different and weaker* hypothesis — "earnings moves are smaller than their own history suggests" — which can pass while the actual premise fails. A free-data pass on the proxy is a green light to buy data, not evidence for the premise.

**Consequence for sequencing.** EV-01 should carry a targeted data purchase in its plan from the start: EOD option chains for the trading universe only, ~5 years, restricted to the two expiries bracketing each earnings date. That is a narrow pull, not a full surface history, and it is the minimum that makes the premise falsifiable. Compare DIR-01 and EV-02, both of which can be taken to a genuine Stage-1 verdict on free data alone — which is why they run alongside EV-01 rather than behind it.

##### Which side to test first

**Test the short side first, and only the short side.**

The reason is not that the short side is expected to win. It is that the short side is the only side with a mechanism. The stated mechanism — buyers bidding event convexity for reasons unrelated to delivered variance, dealers warehousing it and being compensated — describes a forced, price-insensitive buyer and a constrained seller. Reverse it and there is no story: "buy earnings straddles" names no participant who is forced to sell them too cheaply. Under `Principles.md` §2.9a that is an automatic disqualifier — no mechanism, no counterparty, no hypothesis. Testing it anyway would be a pattern hunt with the multiple-testing cost of a real test.

Two conditions on the short-side test:

1. **The pass criterion is the cumulative sum of per-event P&L net of a full bid-ask spread, not the mean of `|actual move| / implied_move`.** The ratio mean is the diagnostic; the sum is the verdict. A distribution with a good mean and three catastrophic gaps is a losing strategy that passes a t-test.
2. **Defined risk from the first line of code.** Not because it improves the estimate, but because an undefined-risk version tests a structure that will never be traded, and §5 translation cannot recover from that.

If the short-side test returns a ratio centered at or above 1, EV-01 is falsified as written. That result does not automatically promote the long side — it requires a *new* mechanism naming who is systematically underpricing event risk and why they cannot stop, written and registered as its own candidate with its own id. Flipping the sign of a dead hypothesis is not a new hypothesis.

#### EV-02 — Scheduled macro: pre-event ramp, event-day move, post-event crush
- **Name / id:** `macro_event_vol_cycle`
- **Mechanism:** FOMC/CPI put a known resolution date on the calendar. Front-dated implieds must embed the event's variance and back-dated ones amortize it, so the front ramps into the print and loses that variance discontinuously after. The counterparty wants event protection and is price-insensitive about its decay.
- **Trigger:** (a) `VIX9D/VIX` rises t−5 to t−1; (b) enter at the t−1 close when `VIX9D/VIX > 1.0`, exit event-day close; (c) event-day `|SPY return|` vs. the priced move proxied by pre-event `VIX/√252`.
- **Predicted effect:** The ratio ramps then compresses more than on matched days, and mean `|return| / priced move` differs from matched days — **sign unknown a priori**, which is what makes it a real test.
- **Stage-1 test:** `^VIX9D`, `^VIX`, SPY, plus Fed and BLS calendars (free, ~200 events since 2008). Event-study t−5 to t+3 against days matched on VIX level and weekday; falsified if event windows sit within noise of matched days.
- **Candidate structure:** Front-vs-back calendar, or an event-day straddle with the side chosen by the test.
- **Data needed:** Free for Stage 1; intraday quotes for Stage 2, since the crush happens in minutes.
- **Confounds:** Ratio compression says nothing about P&L — the event-day move can fully offset it. Severe regime dependence: 2022 CPI prints behave nothing like 2015 ones.
- **Crowding & decay:** Very high; a known dealer trade, already priced. The question is whether residual premium survives spreads.

### C. Market Microstructure / Positioning

#### MS-01 — Monthly OPEX: gamma unwind and strike pinning
- **Name / id:** `opex_gamma_and_pinning`
- **Mechanism:** Concentrated monthly OI forces dealer delta-hedging, which is a constraint rather than a view. If dealers are net long gamma into expiry, hedging suppresses realized vol until expiry removes it; near a large-OI strike the same hedging buys weakness and sells strength, pulling spot toward it.
- **Trigger:** (a) OPEX week = the week containing the third Friday; compare `RV5` there to the following week at equal starting VIX. (b) On expiry morning, take the max-OI strike within ±2% of spot and predict the close lands nearer it than a random walk implies.
- **Predicted effect:** (a) Lower OPEX-week RV as a paired difference. (b) `|close − strike| / strike_spacing` shifted toward zero vs. a no-pinning simulation.
- **Stage-1 test:** (a) Free SPY OHLC since 1993, ~390 cycles, paired with VIX control; falsified if the difference is zero or flips sign across decades. (b) Not free-testable; proxy by round-dollar clustering of expiry closes.
- **Candidate structure:** Short vol into OPEX, flat after; small defined-risk expiry-day butterfly at the strike.
- **Data needed:** Free for (a); historical OI by strike for (b).
- **Confounds:** "Dealers are long gamma" is an assumption, unobservable without OI and trade-side data. Weeklies and 0DTE have hollowed out monthly OI since ~2019, so pre-2019 results may not describe today's market. Round-number clustering has non-options causes.
- **Crowding & decay:** High; gamma dashboards are retail products now, and structural change decays this independently of crowding.

#### MS-03 — Month-end / quarter-end and index-rebalance flow
- **Name / id:** `calendar_forced_flow`
- **Mechanism:** Pension and target-date funds rebalance on fixed dates, and index funds must trade the rebalance close to minimize tracking error. Price-insensitive flow on a public timetable — a mandate, not a view.
- **Trigger:** (a) Long SPY from close T−3 to close T+1 around month-end, scaled by the trailing month's equity-minus-bond return spread as an imbalance proxy. (b) On S&P quarterly rebalance dates, measure index RV in the window.
- **Predicted effect:** (a) Window return exceeds the unconditional 4-day mean, with the excess increasing in the equity-bond spread. (b) Rebalance-day RV exceeds matched days.
- **Stage-1 test:** Free SPY + TLT/IEF since 2002, ~280 month-ends; regress window return on trailing spread. Falsified if the slope is indistinguishable from zero.
- **Candidate structure:** Short-dated call spread or plain long delta; long straddle into rebalance day for the vol variant.
- **Data needed:** Free.
- **Confounds:** The turn-of-month effect is decades old and published — a prime arbitraged-away candidate. It overlaps OPEX, and a few bps of cost erase effects this small.
- **Crowding & decay:** Very high. Search SSRN/Quantpedia for "turn of the month effect" and check post-publication performance first.

### D. Volatility Regime / Term Structure

#### VT-01 — VIX9D/VIX ratio as a short-horizon regime signal
- **Name / id:** `vix9d_vix_ratio_regime`
- **Mechanism:** The 9d/30d implied ratio measures near-term stress relative to medium-term. Spikes are typically driven by immediate hedging demand that decays once the catalyst passes — a flow effect, not information.
- **Trigger:** Enter on the downward cross of `VIX9D/VIX` through 1.00 following a reading `> 1.10`; strictly causal, no peak-picking. Test the mirror state (`< 0.85`) separately.
- **Predicted effect:** Forward 5-10 day RV falls faster after a spike than the ratio implies; conditional short-vol payoff better *after* the spike than during it.
- **Stage-1 test:** Free `^VIX9D` (from 2011) + `^VIX`; bucket by ratio and measure forward 5/10/21-day RV. Falsified if forward RV is monotone in the ratio in the implied direction, i.e. the ratio is unbiased.
- **Candidate structure:** Short 7-14 DTE strangle on the causal cross.
- **Data needed:** Free; ~3,500 rows but far fewer independent episodes.
- **Confounds:** Sample starts 2011, dominated by a secular vol-selling bull market. Spikes are highly autocorrelated — independent episodes number in the dozens.
- **Crowding & decay:** Moderate-high; widely watched, though this exact conditioning is less standardized than raw VIX.

#### VT-03 — Realized-vol mean reversion after spikes
- **Name / id:** `rv_mean_reversion_post_spike`
- **Mechanism:** RV is strongly mean-reverting at multi-week horizons (the HAR structure). If implied vol anchors too heavily on recent realized — extrapolation bias in the marginal price-setter — post-spike implieds sit above the RV that follows.
- **Trigger:** Flag when `RV5/RV60 > 2.0`; enter on a strictly causal rule (N days after the flag, never after the observed peak), measuring forward RV20 and IV change over 10-21 days.
- **Predicted effect:** Forward RV reverts toward RV60 faster than implied vol does, widening the IV−RV gap in the days after the flag.
- **Stage-1 test:** Free SPY/`^GSPC` OHLC (Yang-Zhang) + `^VIX`; ~8,000 rows, hundreds of spike episodes since 1993. Fit a baseline HAR forecast and test whether VIX's post-spike path sits systematically above it; falsified if VIX decays at or below the HAR-implied rate.
- **Candidate structure:** Short vol entered 3-5 days after the flag, 21-45 DTE, defined risk.
- **Data needed:** Free. Best data economics of any candidate here.
- **Confounds:** RV mean reversion is public and priced; the tradeable claim is that IV does *not* already price it, which is far stronger. Spikes cluster, shrinking effective N.
- **Crowding & decay:** The underlying fact is public, so any surviving edge lives in the timing rule — precisely the part most prone to overfitting.
- **Status note (demotion):** 1,165 raw events collapse to **86 independent clusters**, clearing §3.8's minimum with almost no margin. Any subgroup or sub-period analysis will breach it, which means the leave-out-best-year and top-3-removal gates are likely to be fatal. Remains ACTIVE only because its data economics are the best in the file; ranked last among active candidates.

### E. Skew / Cross-Sectional

No active candidates. SK-01 is in `## Deferred`; SK-02 is in `## Rejected / Not Pursued`. The family heading is retained so that new skew candidates have a home and so that the absence is visible rather than silent.

### F. Conditional Directional

#### DIR-01 — Behavior after vol-adjusted extreme moves and gaps
- **Name / id:** `sigma_extreme_conditional_drift`
- **Mechanism:** Two rival mechanisms the test can separate. (a) Forced deleveraging: vol-target and risk-parity funds mechanically sell for 1-5 days after a vol shock, pushing price below fair value → reversal. (b) Information: the move is genuine repricing → continuation. Opposite signs, so the test is informative either way.
- **Trigger:** `z = daily_return / (RV20/√252)`; condition on `z < −3`, and separately on overnight gap `|gap| > 1.5%`. Measure forward 1/3/5/10-day returns and forward RV.
- **Predicted effect:** Non-zero conditional mean forward return, sign TBD, plus elevated forward RV regardless of sign — the vol claim is far likelier to survive than the direction claim.
- **Stage-1 test:** Free SPY since 1993, **99** `z < −3` events (87 independent clusters at h=5) and **288** `|gap| > 1.5%` events (165 clusters). Bootstrap the conditional mean against the unconditional distribution and split by date. Falsified if the mean sits inside the unconditional CI or flips sign across halves.
- **Candidate structure:** Reversal → short put spread, 7-21 DTE; continuation → put debit spread; vol-only → long straddle or an exclusion filter on short-vol candidates.
- **Data needed:** Free.
- **Confounds:** Extreme down days cluster inside crises — perhaps 10-15 independent episodes, not 200 — so the conditional mean is dominated by March 2020 and October 2008. Buying after −3 sigma is the trade that works for years and then does not.
- **Crowding & decay:** Moderate; reversal has weakened as capital entered, but forced deleveraging is structural and will not vanish.
- **Measurement note (2026-08-19) — corrected sample counts.** This entry previously carried **268 raw events / 211 independent clusters** in the Prioritization table, and that figure was the main reason DIR-01 was ranked "run first". It is not the sample for the trigger stated above. Re-measuring reproduces 268 / 211 / 8.0-per-year exactly from **`|z| > 2.5`** — a *two-sided* condition at a *looser* threshold than the one-sided `z < −3` this entry specifies. The specified trigger yields **99 events / 87 clusters**, roughly one third as much.

  Both arms still clear §3.8's 50-event and 20-cluster floors on the research window (67/60 and 198/111 respectively), so the candidate survives and the ranking does not change — the gap arm carries the larger sample. But the recorded number described a trigger nobody had written down, which is the §4.2 failure mode in miniature: a sample count measured on a variant that was never specified is not evidence about the specified variant. The counts above are now measured with the canonical definition registered in the spec — log returns on `close_adj`, `RV20` shifted one bar so the trigger day is excluded from its own volatility scale, and gaps against the previous *unadjusted* close.

  Excluding the trigger day from its own RV window is worth stating explicitly because it is not cosmetic: including it collapses the `z < −3` count from **99 to 33**, since a large move inflates its own denominator.

- **STAGE-1 RESULT (2026-08-19) — spec `H-2026-001`, spec_hash `18abe5ca6c83ed41`.** All eight pre-registered trials run; the trial budget is spent and PROGRAM.md permits no ninth. Research window only, 1993-01-29 → 2018-03-23; the holdout has not been unsealed.

  | trial | effect | perm p | HAC t | verdict |
  |---|---|---|---|---|
  | `sigma_h1_logret` | −0.30% | 0.035 | −1.31 | **FAIL** |
  | `sigma_h3_logret` | −0.06% | 0.790 | −0.21 | **FAIL** |
  | `sigma_h5_logret` | +0.20% | 0.507 | +0.58 | **FAIL** |
  | `sigma_h5_fwdrv` | +7.2 vol pts | 0.0003 | +3.32 | PASS |
  | `sigma_h10_fwdrv` | +5.7 vol pts | 0.0001 | +2.85 | PASS |
  | `gap_h5_fwdrv` | +21.1 vol pts | 0.0012 | +6.72 | PASS |
  | `gap_h10_fwdrv` | +18.9 vol pts | 0.0014 | +5.58 | **FAIL** — leave-out-best-year 58% (needs 60%) |
  | `gap_h5_abslogret` | +1.45% | 0.0055 | +6.40 | PASS |

  **The directional claim is dead — `NO_EFFECT`, not `INSUFFICIENT_SAMPLE`.** All three directional trials fail, and the §4.10 distinction resolves cleanly. The minimum detectable effect at h=5 is **0.86%**, and the §3.8 cost gate requires **0.90%** to be worth trading. Those two numbers are essentially equal, which means this sample was almost exactly powered for the decision being made: any reversal large enough to clear an option bid/ask was large enough for this test to see, and it was not there. What the test *cannot* rule out is a reversal below 0.86% — which cannot be traded anyway. The observed effects are −0.30%, −0.06%, +0.20%: not merely insignificant but **sign-inconsistent across adjacent horizons**, which is what noise looks like. Neither rival mechanism survives: no reversal, so no exploitable forced-deleveraging window; no continuation either.

  **The volatility claim passed, and was always the likelier survivor.** Forward realized volatility after a >1.5% gap is 36.1% against an unconditional 15.0% at h=5. It clears every §3.8 gate including top-3 removal, leave-out-best-year with its permutation re-test, and the one-bar delay. `gap_h10_fwdrv` misses on one gate only — 58% retention against a 60% floor once 2008 is removed — so the effect is real but more crisis-concentrated at ten days than at five. **h=5 is the honest horizon; h=10 is not claimed.**

  **The caveat that matters more than the p-values.** The by-regime split shows the effect is monotone increasing in trailing volatility: for `gap_h5_fwdrv`, +8.9 / +14.0 / +40.3 vol points across low/mid/high terciles. Conditioning on a large move conditions on elevated volatility, which is mean-reverting by construction, so a large part of this is mechanical rather than a mispricing. For `sigma_h5_fwdrv` the low-volatility tercile is actually **negative** (−1.5 vol points); it passes only because §3.8 asks for 2 of 3. This is a statement about volatility clustering, which is public knowledge, not about anything the options market has failed to price. **Nothing here says implied vol is cheap after a gap** — that is a different and much stronger claim, and testing it needs the IV data this program has not bought.

  **Disposition.** The directional half moves to the death ledger with cause `NO_EFFECT`. The volatility half is *not* promoted to a standalone Stage-2 candidate — an unconditional long-straddle-after-a-gap trade would be buying elevated implied vol precisely when it is most expensive, and §7.7's benchmark test would very likely show it adds nothing. Its correct use is the one the entry already named: **an exclusion filter on short-volatility candidates.** VRP-01, VRP-02 and VT-01 should not initiate short vol within 5 sessions of a >1.5% gap, and that rule is now measured rather than assumed. Reviving the directional claim requires a *new vehicle*, not a re-run: intraday data to test whether the reversal exists and decays inside the day, which is invisible to daily bars. That is MS-02 territory and is currently `REJECTED` on data grounds.

---

## Deferred

Parked, not dead. Each has a stated reason and a condition for reactivation. Deferred entries are not registered and consume no trial budget.

#### VT-02 — VVIX conditioning of short-vol exposure
- **Name / id:** `vvix_gate_short_vol`
- **Mechanism:** VVIX prices vol-of-vol, i.e. surface convexity. When it is elevated relative to VIX the tail of the vol distribution is being bid, plausibly by funds hedging their own short-vol books — selling vol there means selling exactly what is in demand.
- **Trigger:** Halve or suppress short-vol exposure when `VVIX/VIX` is in the top quintile of its trailing 2-year distribution; full size otherwise.
- **Predicted effect:** Fatter left tail for short-vol returns in high `VVIX/VIX` states, with materially worse conditional CVaR(5%). A claim about tails, not means.
- **Stage-1 test:** Free `^VVIX` (from 2007) + `^VIX`; build a proxy short-vol P&L series and compare quantiles across buckets. Falsified if the tail is no worse — **or if it fails to beat a VIX-level-only gate**, the benchmark it must clear.
- **Candidate structure:** Not standalone; a sizing overlay on VRP-01/VRP-02.
- **Data needed:** Free.
- **Confounds:** VVIX spikes are near-contemporaneous with VIX spikes, so the gate may be a lagged-VIX filter with extra steps.
- **Crowding & decay:** Low as an overlay; the premium it gates is heavily crowded.
- **REASON DEFERRED:** Overlay-only. VT-02 gates an exposure that does not yet exist — there is no validated short-vol candidate for it to size. Testing a sizing rule before the thing being sized has passed Stage 1 spends a trial on a question that cannot yet have a useful answer.
- **To reactivate:** VRP-01 (or another family-A candidate) clears §3.8, **and** a proxy short-vol P&L series exists to bucket. At that point VT-02 becomes a §7.7 benchmark question — does the VVIX gate beat the plain VIX-level gate? — rather than a standalone hypothesis.

#### SK-01 — Put skew steepness as a conditioning signal
- **Name / id:** `put_skew_steepness`
- **Mechanism:** Index put skew is set by persistent one-way protection demand, so steepness may measure hedging intensity more than crash probability. If demand overshoots, downside puts are rich relative to realized downside and the seller is paid to absorb a positioning imbalance.
- **Trigger:** Proxy with CBOE `^SKEW` (free) or a 25-delta put/call IV differential where chains exist; condition on the top/bottom quintile of the trailing 1-year distribution.
- **Predicted effect:** Forward 21-day realized downside — semivariance, max drawdown — is **not** higher after high-skew readings, implying an embedded premium.
- **Stage-1 test:** Free `^SKEW` (from 1990) + SPY; bucket forward drawdown and semivariance by skew quintile. Falsified if high skew genuinely forecasts higher downside — the premium would then be fair and there is no trade.
- **Candidate structure:** Put ratio or put credit spread, never naked; or skew as a filter on VRP-01.
- **Data needed:** Free proxy for Stage 1; delta-specific IVs for Stage 2.
- **Confounds:** `^SKEW` is a poor, non-monotone proxy for tradeable skew. High-skew periods are rare and clustered, and the whole test is a peso problem — short a tail that may simply not have occurred in-sample.
- **Crowding & decay:** Moderate; institutional territory with far better execution, and retail is the worst-positioned participant for this exposure.
- **REASON DEFERRED:** Low usable sample on the free proxy, and the free proxy is the wrong instrument — `^SKEW` is not monotone in tradeable skew, so a null result would not falsify the claim and a positive result would not support it. The test as specified cannot resolve the hypothesis in either direction, which is the definition of a test not worth running.
- **To reactivate:** Delta-specific IV history is on hand (25-delta put/call differential from a paid chain source), making the conditioning variable the actual quantity in the mechanism rather than a proxy for it. Cheaper alternative: reframe as a *filter* on VRP-01 and evaluate it inside that candidate's §7.7 benchmark rather than as its own entry.

---

## Rejected / Not Pursued

Kept in full, permanently. Each entry retains its mechanism description so that the idea, when it arrives again from a different source, is recognized immediately. Per `Principles.md` §2.11, these are never deleted.

#### SK-02 — Index vs. component vol (dispersion)
- **Name / id:** `index_component_dispersion`
- **Mechanism:** Index options carry hedging demand single names do not, so implied correlation embedded in the index may sit above realized. The counterparties are index hedgers and structured-product desks selling single-name vol into autocallables — a flow imbalance with clear institutional origin.
- **Trigger:** `rho_imp ≈ (IV_idx² − Σ wᵢ²IVᵢ²) / (Σ_{i≠j} wᵢwⱼIVᵢIVⱼ)`; short index vol / long component vol when `rho_imp` is in its top quintile.
- **Predicted effect:** Realized correlation over the next 21-45 days averages below implied at entry, with the gap widest in the top quintile.
- **Stage-1 test:** Free data builds only the realized-correlation baseline (index RV vs. cap-weighted component RV, top ~30 names). The premium claim itself **cannot be falsified with free data.**
- **Candidate structure:** Short index strangle vs. long strangles on 15-30 components, vega-matched — realistically 30-60 legs.
- **Data needed:** Paid option data required.
- **Confounds:** Membership and weight drift create severe survivorship bias. Realized correlation jumps toward 1 exactly when the short-index leg hurts most — the trade is short a correlation tail.
- **Crowding & decay:** High and institutionally mature.
- **REASON NOT PURSUED:** **Untradeable in a retail account.** The structure requires 30-60 legs, vega-matched and periodically re-matched. Retail per-contract commissions and bid-ask on 30-60 single-name legs consume the entire claimed effect before any correlation premium is captured, and the rebalancing cost recurs. This is the §2.9a "capacity below account size" disqualifier applied from the cost side rather than the depth side. Secondarily, the premise cannot be falsified on free data at all — the entry would fail the reality gate even if it were tradeable. Retained here to mark the boundary of scope: it is the clearest example of a mechanically sound idea that this account cannot express.
- **What would have to change:** A vehicle that expresses dispersion in one or two trades rather than thirty — a listed correlation product, a dispersion-linked ETP with a transparent construction, or an account structure with institutional commissions and access to a basket desk. Absent that, no amount of favorable data revives this. Note that if such a vehicle appeared, the correlation-tail risk in the confounds would be unchanged and would still be the dominant risk.

#### MS-02 — 0DTE intraday behavior into the close
- **Name / id:** `zerodte_late_session_drift`
- **Mechanism:** 0DTE flow is a large, time-clustered share of SPX volume, and dealer hedging of same-day gamma concentrates in the last 60-90 minutes when gamma per unit premium is largest. Any pattern is a hedging-flow artifact, not a forecast.
- **Trigger:** SPY 14:30-16:00 ET return and realized vol, conditioned on the 09:30-11:00 return sign and magnitude.
- **Predicted effect:** Conditional late-session RV or return autocorrelation differs from the mid-session baseline, **and** the difference is larger post-2022 than before.
- **Stage-1 test:** yfinance intraday caps near 60 days of minute bars — a screen, not a test. The real falsifier is the structural break: if the identical pattern exists in 2015, the 0DTE mechanism is wrong even if the pattern is real.
- **Candidate structure:** Same-day defined-risk spreads entered ~14:30, closed 15:55.
- **Data needed:** Minute bars; free coverage inadequate.
- **Confounds:** Sixty days supports no claim. Time-of-day effects are the most p-hacked area in retail research, and 15:55 costs can exceed the whole measured effect.
- **Crowding & decay:** Extreme; flow composition changes quarterly.
- **REASON NOT PURSUED:** **Untestable on available data.** The stated predicted effect requires a pre-2022 versus post-2022 comparison, and free intraday coverage is roughly 60 days — it cannot reach 2015, so the one observation that would distinguish the 0DTE mechanism from a generic time-of-day artifact is unobtainable. This is the §2.9a "data you don't have" disqualifier. Running the 60-day screen anyway would produce a number with no evidentiary value and would burn a trial against the multiple-testing budget for it.
- **What would have to change:** A minute-bar history for SPY or SPX covering 2015 to present, so that the structural-break test can actually be run. That is the whole requirement — the mechanism is plausible and the trigger is point-in-time; only the data is missing. Even with the data, note the second obstacle in the confounds: a 15:55 exit on same-day options faces costs that can exceed the entire measured effect, so a passing Stage 1 would still face a hostile §5 translation. Budget the data purchase behind EV-01's, which buys a falsifiable premise rather than a testable one.

---

## Prioritization

**Measured, not reasoned.** The counts below come from the §2.9b pre-flight run against free daily data (SPY 1993–2026; the VIX complex from 1990, 2006 or 2011 depending on series). Independent clusters — not raw events — are the sample that powers every statistic.

| id | Family | Data cost | Raw events | **Indep. clusters** | Events/yr | Verdict |
|---|---|---|---|---|---|---|
| EV-01 | B | Free dates, paid IV later | ~90/name | **~90/name × universe** | 4/name | **Run first** |
| DIR-01a | F | Free | 99 | **87** | 3.0 | **Stage 1 done** — direction `NO_EFFECT`; forward vol passed |
| DIR-01b | F | Free | 288 | **165** | 8.6 | **Stage 1 done** — forward vol and magnitude passed at h=5 |
| EV-02 | B | Free calendar | ~270 FOMC / ~400 CPI | ~270 / ~400 | 8 / 12 | Run second |
| VRP-01 | A | Free | 2,776 | 259 | 83 | Sample fine, effect likely thin |
| VT-01 | D | Free | 486 | 166 | 31 | Viable; short history (2011+) |
| MS-03 | C | Free | ~400 | ~400 | 12 | Viable |
| MS-01 | C | Free / paid OI | ~394 | ~394 | 12 | Viable |
| VT-03 | D | Free | 1,165 | **86** | 35 | **Demoted** — thin sample |
| VRP-02 | A | Free | 3,761 | 217 | **188** | **Demoted** — see below |
| VRP-02b | A | Free | 377 | 57 | 19 | Backwardation arm; marginal |
| VT-02 | D | Free | n/a | overlay | — | Overlay only, never standalone |
| SK-01 | E | Free proxy | Low | Low | — | Defer |
| MS-02 | C | Paid / thin | Unknown | Unknown | — | Defer — untestable on available data |
| SK-02 | E | Paid | Low | Low | — | Defer — untradeable retail |

**Run first: EV-01, DIR-01.** Then EV-02.

- **EV-01 (earnings)** — the only candidate combining a large sample with an effect big enough to clear the bid/ask. Roughly 90 events per name back to 2002 on free data; across a liquid large-cap universe that is thousands of genuinely independent observations, since one company's report is unrelated to another's. The effect itself — implied vol collapsing once the announcement removes the uncertainty — is large and mechanical. This sits squarely in the middle band of the §2.9c viability screen.
- **DIR-01 (vol-adjusted extreme moves)** — two arms, counted separately because they are separate claims. The `z < -3` arm is **99 events / 87 independent clusters**; the `|gap| > 1.5%` arm is **288 / 165**. Collapse ratios of 1.14x and 1.75x are the lowest in this file, because large moves are isolated point events rather than persistent states. Free, and genuinely two-sided so it cannot be talked into confirming itself. Run the gap arm first: it carries three times the sample and therefore the most margin over §3.8's 50-event floor.
- **EV-02 (scheduled macro)** — moderate counts (~270 FOMC, ~400 CPI since 1993) but large, concentrated, precisely dated effects. Needs only a release calendar, which the Fed and BLS publish free.

**Two demotions, both produced by measurement rather than argument:**

- **VT-03** was ranked first on reasoning and is **86 independent clusters** on inspection — 1,165 raw events collapsing roughly 14× because elevated realized vol persists for weeks at a time. It clears §3.8's minimum with almost no margin, and any subgroup or sub-period analysis will breach it.
- **VRP-02** fires **188 days per year — about 75% of all sessions.** Contango is the market's default state, so this is not a trigger; it is a description of normal conditions. §7.7's benchmark test (does the signal beat the always-on version?) would very likely show it adds nothing over simply being short vol continuously. Test it as a *conditioning overlay* on VRP-01, never as a standalone entry.

**The general lesson.** Both demotions came from arithmetic that took five minutes and no outcome data. State-based triggers ("vol is high", "the curve is steep") collapse 10–20× from raw events to independent clusters, because states persist. Point-event triggers (a gap, an earnings release, a scheduled announcement) barely collapse at all. **Prefer point events wherever the mechanism permits** — they buy an order of magnitude in effective sample for free.

---

## Anti-Patterns — Popular "Strategies" That Are Not Hypotheses

Each fails the `Principles.md` §2.7 spec at the same two fields: **no mechanism** (who is on the other side, and why they must trade against you) and **no falsification condition** (what observation would make the author stop).

- **The wheel.** Sell cash-secured puts, take assignment, sell covered calls. Not a hypothesis but a *position*: levered long, short vol, short skew, truncated upside. It makes no claim about *when* premium is rich, so nothing can be tested; "it works until it doesn't" is unfalsifiable. To make it a hypothesis, state when put IV is rich relative to subsequent realized — which is VRP-01, and the wheel adds nothing to it.
- **0DTE martingale / recovery sizing.** Doubling after a loss reshapes the return distribution without changing its expectation, converting many small wins into one terminal loss. No mechanism, because size is not information. Its falsification test — does expectancy per unit of risk improve? — has a known negative answer before any data is collected.
- **"Sell premium because theta always wins."** Theta is the accounting rate of time-value decay, offset in expectation by gamma losses under the pricing model; quoting it as income confuses a bookkeeping entry with an edge. The real claim underneath — implied variance exceeds subsequent realized variance on average — is legitimate (family A), but conditional, heavily negatively skewed, and the most harvested premium in the market. Stated unconditionally it names no trigger, no horizon, and no condition under which to stop.
- **Indicator-crossover systems** (MACD, RSI thresholds, MA crosses, and their options wrappers). They start from a chart pattern with no account of who is forced to trade the other side. The parameter space is large and the transform arbitrary, so finding an in-sample winner by chance is near-certain — which is why they always arrive with a backtest and never a mechanism. If you cannot say who is losing money to you and why they cannot stop, there is no hypothesis.
- **The shared failure mode.** Most retail options "strategies" are the same trade — unconditionally levered short volatility — wearing different labels, and they correlate near 1 precisely when that matters. Before adding any candidate to the pipeline, regress its returns on a plain short-strangle benchmark. High correlation means it is not new alpha; it is the variance risk premium with extra steps, to be evaluated as a *conditioning rule on VRP*, not as an independent strategy.

---

## Adding a Candidate

The checklist for adding an entry to this file. It is short on purpose — most of the work happens before anything gets written down.

1. **Run the `Principles.md` §2.9 pre-flight FIRST, before writing the entry.** All three parts: the §2.9a disqualifier table (any single hit kills the idea outright), the §2.9b sample-size count, and the §2.9c viability screen. This costs an afternoon, consumes no outcome data, touches no holdout, and burns no trial. Writing an entry before the pre-flight means writing entries for ideas that were arithmetically incapable of producing a trustworthy answer.

2. **Record the measured cluster counts.** Raw events, **independent clusters**, and events per year — measured against real history with the §2.9b `clusters()` routine, not estimated. The clusters figure goes in this file's Prioritization table and, later, in the spec's `sample_size_expected` field. A candidate with fewer than ~50 events *and* 20 clusters after the holdout is carved out (§3.8) does not get an entry; it gets a line in the death ledger. A trigger firing more than ~150×/yr is a regime, not a signal — either re-specify it as a conditioning overlay or drop it.

3. **Name the mechanism and the counterparty.** One sentence identifying who is on the other side and what constraint forces them there — a mandate, a hedging requirement, an inventory they cannot decline, a payoff shape they are buying for reasons unrelated to expected return. "The market" and "irrational traders" are not counterparties. If the sentence cannot be written, stop; §2.9a has already killed it.

4. **State the falsification condition as a number.** Not "if it doesn't work" — a specific statistic crossing a specific threshold that ends the candidate. If the free-data test cannot resolve the claim in *either* direction, the test is not worth running: say so in the entry and file it under Deferred with the data requirement stated, rather than running a screen that produces a number with no evidentiary value.

5. **Assign an id following the family convention.** `VRP` (variance risk premium), `EV` (event-driven), `MS` (microstructure / positioning), `VT` (vol regime / term structure), `SK` (skew / cross-sectional), `DIR` (conditional directional), plus the next free number in that family. Sub-arms of an existing candidate take a letter suffix (`VRP-02b`). Ids are never reused, including for rejected entries. If no family fits, add a new family letter and heading rather than forcing the id.

6. **Check it is not already here.** Including the Deferred and Rejected sections. A candidate substantively identical to a dead entry is disqualified under §2.9a "already registered" — the cause of death is the answer, and re-testing it without new data or a new vehicle is spending a trial on a question already resolved.

7. **Set status ACTIVE only after it clears the pre-flight.** Until then the entry does not go in this file at all. ACTIVE means "cleared the reality gate and is worth writing a §2.7 spec for" — not "seems interesting". Add the row to the status table and the Prioritization table at the same time, or the index stops being the thing the reader can trust.

8. **When it is tested, move it down — never delete it.** A candidate that fails Stage 1 moves to `## Rejected / Not Pursued` with a REASON NOT PURSUED and a note on what would have to change to revive it, using the §2.11 controlled vocabulary (`NO_EFFECT`, `WRONG_SIGN`, `COSTS_EXCEED_EDGE`, `INSUFFICIENT_SAMPLE`, `DECAYED`, `CONFOUNDED`, `CAPACITY`, `CONTAMINATED`, `SUPERSEDED`, `LIVE_UNDERPERFORM`) where it applies. Causes of death cluster: when several entries die of the same cause, that is one finding about the research process, not several failures. Read the rejected section before generating the next batch.
