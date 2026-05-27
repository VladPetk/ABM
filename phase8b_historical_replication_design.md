# Phase 8b — Historical Replication Design (revised)

*Design spec, not implementation. The question the test asks: when
polarlab is started in a state that matches the 1980 US empirical
landscape and run forward 45 years with mechanisms calibrated
decade-by-decade against real-world events, does each decade's
end-state match the empirical decade-end on the metrics that
matter — without breaking any of the pillar's calibrated invariants?
This document proposes what that test would look like — the
targets, the time mapping, the mechanism inventory, the decade-by-
decade workflow, the curve-fitting guardrails, the success criteria,
and the validation discipline — with explicit judgment forks
throughout. **No code, no implementation details.** Vlad iterates
on the design first; implementation follows confirmation.*

*Revision history. v1 (1955 start, strict forward-prediction
discipline, 3 mechanisms, 8 events) → v2 (this doc: 1980 start, 5
mechanisms with per-agent heterogeneity + time-varying IdentitySorting,
6 events post-1980, decade-by-decade calibration with curve-fitting
guardrails, seed count 5 for tractability).*

---

## 1. Why this test, and what it would prove

The pillar (S0→S4) tells a *qualitative* story — a society moving
from neutral baseline through identity sorting to network sorting.
Its mechanisms are literature-anchored, its trajectory passes the
ANES rate-of-cooling check (Phase 7 §C2). But the pillar is
**ahistorical** — there is no claim that S2 is 1985, S4 is 2020.
Those mappings are stylized.

A historical-replication test would make a stronger claim: the
model, started from empirically-anchored 1980 conditions and run
forward with mechanisms calibrated to real-world historical events,
*tracks the empirical US trajectory decade-by-decade* on multiple
metrics simultaneously.

**The honest framing** (a notable revision from v1): this is a
**calibrated historical reconstruction**, not a strict
out-of-sample forward prediction. Each decade is allowed to be
calibrated against its own empirical targets. The discipline that
keeps this from being silent curve-fitting is the guardrail set
in §9: the pillar's calibrated invariants — canonical HK,
machinery, Phase 4-8a §11 thresholds, the six X-intervention
bucket labels — must stay green throughout the historical scenario's
existence. The pillar is sacred; the historical scenario gets its
own knobs.

Pass = the model can produce empirically sensible trajectories
through each decade *when* calibrated against decade-ends, while
preserving every existing engine invariant. Fail = some decade
cannot be calibrated within band, *or* calibrating it breaks a
pillar invariant. Either outcome is informative.

A stricter forward-prediction-stacked validation (calibrate
1980-90, predict 1990-2000, etc.) is deferred to **Phase 8c** as
the next-level test. The Phase 8b test is the necessary precursor.

---

## 2. Why 1980 (and not 1955)

v1 of this design proposed a 1955 start. v2 moves it to 1980 for
three reasons:

- **Data quality.** Modern ANES (with full feeling-thermometer
  panel) starts in 1964; DW-NOMINATE has high-precision Congress
  data from ~1970 onward; GSS launches 1972 and is in full swing
  by 1980. 1955 anchors required historical reconstructions with
  low confidence on cross-cutting tie share and modularity; 1980
  anchors are mostly direct measurement.
- **The CRA / Southern realignment becomes initial-condition fact,
  not modeled mechanism.** Carmines & Stimson 1989 *Issue Evolution*
  documents the realignment as substantially complete by ~1980.
  Skipping pre-1980 lets the model start from the post-realignment
  state without needing to model the 1964 → 1980 transformation.
- **Compute tractability.** 135 ticks vs 210 ticks; fewer events
  to schedule; one fewer decade to calibrate.

**Trade-off:** the model now skips the 1955-1980 transformation,
which is where some of the most interesting polarization mechanics
happened. Worth honest acknowledgment in the methods doc, but the
1980-2025 window is still 45 years of substantial dynamics.

---

## 3. 1980 initial-condition target

| Metric | 1980 target band | Source | Confidence |
|---|---|---|---|
| **Variance** (positions on [-1, 1]²) | ~0.45-0.60 — moderate dispersion, some sorting underway | ANES 1980 self-placement spread; Levendusky 2009 ch. 2 | medium |
| **Ideological constraint** (party↔issue \|r\|) | ~0.25-0.40 — sort underway but pre-modern | Baldassarri & Gelman 2008 cross-tabs; Levendusky 2009 longitudinal | high |
| **Party separation** (centroid distance) | ~0.45-0.60 — clear parties but issue distance modest | DW-NOMINATE 96th Congress (1979-81) | high |
| **Affective polarization** (mean out-party warmth, scaled) | ~ -0.20 to -0.35 — out-party warmth ~45° (Iyengar figure 1) | Iyengar et al. 2019; Finkel et al. 2020 figure 1 | high |
| **Cross-cutting tie fraction** | ~0.30-0.40 — substantial cross-party social ties remained | Mutz 2006; Putnam *Bowling Alone* | medium |
| **Party modularity (Q)** | ~0.10-0.20 — networks moderately sorted | Mutz historical reconstruction + homophily literature | medium |
| **Within-party SD_x** | ~0.20-0.35 — DW-NOMINATE 96th Congress within-caucus SDs | DW-NOMINATE | high |
| **Education-party correlation** | ~0.00-0.10 — minimal in 1980 (pre-diploma-divide) | Sides, Tausanovitch & Vavreck 2022 *The Bitter End* | high |
| **Identity-party correlation** (sorting_index) | ~0.20-0.35 — partial sorting underway, mega-identity not yet consolidated | Mason 2018 *Uncivil Agreement* historical figure | medium |

Most 1980 anchors are **medium-to-high confidence**, vs v1's
1955 anchors which had low-confidence reconstructions. This is the
main payoff of the start-year shift.

**Reagan / Moral Majority** (1980, religious realignment seed) is
treated as **part of the initial-condition setup** rather than a
discrete event — the model starts with identity-party correlation
already ~0.25, encoding the post-realignment religious cleavage as
baked in.

---

## 4. Decade-end target trajectory

Per-decade targets, with tolerance bands that **tighten over time**
because later decades have richer data. The model must hit each
decade-end within its band.

| Decade end | Year | Variance | Constraint | Sep | Affect | XC ties | Mod | Within-party SD |
|---|---|---|---|---|---|---|---|---|
| 1990 | 1990 | 0.40-0.55 | 0.35-0.50 | 0.50-0.65 | -0.30 to -0.45 | 0.25-0.35 | 0.15-0.25 | 0.18-0.32 |
| 2000 | 2000 | 0.30-0.45 | 0.45-0.60 | 0.55-0.70 | -0.40 to -0.55 | 0.20-0.30 | 0.20-0.30 | 0.18-0.30 |
| 2010 | 2010 | 0.20-0.35 | 0.55-0.70 | 0.60-0.75 | -0.50 to -0.65 | 0.18-0.28 | 0.25-0.38 | 0.17-0.28 |
| 2020 | 2020 | 0.15-0.25 | 0.60-0.75 | 0.65-0.80 | -0.60 to -0.78 | 0.15-0.25 | 0.30-0.42 | 0.15-0.25 |
| 2025 | 2025 | 0.13-0.20 | 0.62-0.78 | 0.68-0.82 | -0.65 to -0.85 | 0.15-0.25 | 0.32-0.45 | 0.15-0.22 |

Sources by metric:
- **Variance, constraint, separation, within-party SD**: ANES self-
  placement series + DW-NOMINATE per-Congress + Baldassarri & Gelman
  2008.
- **Affective polarization**: Iyengar et al. 2019 figure 1; Finkel
  et al. 2020 figure 1.
- **Cross-cutting ties**: Mutz 2006; Levendusky 2021; Brown & Enos
  2021 (precinct-level).
- **Modularity**: derived from cross-cutting + party-density
  reconstructions; medium-low confidence.

**Band widths shrink** later because (a) data quality improves and
(b) the model is calibrated decade-by-decade, so cumulative
uncertainty should narrow as the trajectory is fit.

---

## 5. Time mapping

At `TICKS_PER_YEAR = 3.0` (unchanged from Phase 7), 1980 → 2025 is
**45 years = 135 ticks**. Decade boundaries:

| Decade | Ticks | Duration |
|---|---|---|
| 1980-1990 | 0 → 30 | 30 ticks |
| 1990-2000 | 30 → 60 | 30 ticks |
| 2000-2010 | 60 → 90 | 30 ticks |
| 2010-2020 | 90 → 120 | 30 ticks |
| 2020-2025 | 120 → 135 | 15 ticks |

Per-decade calibration runs each decade independently from the
fitted endpoint of the previous decade. The model is *continuous*
across decades; the calibration *re-tunes* the schedule's
parameters at each decade boundary.

---

## 6. The five mechanisms

v1's three-mechanism set grew to five. Per Vlad: uniform `epsilon`/
`α`/`affect_lr` implicitly assumes everyone is equally receptive,
when Converse 1964, Achen & Bartels 2016 *Democracy for Realists*,
and Zaller 1992 all show a fat-tailed minority of high-engagement
partisans does most of the causal work on macro polarization. So
per-agent heterogeneity becomes part of the minimum-viable set.
And Mason's mega-identity argument means `IdentitySorting` *must*
be on (with a time-varying rate) for the model to qualitatively
distinguish modern from pre-modern polarization.

### 6.1 Residential / network sorting (Bishop's *Big Sort*)

- **Claim:** since the 1970s, Americans have geographically sorted
  by partisan preference; "landslide counties" rose from ~26%
  (1976) to ~60% (2020). Bishop 2008; Brown & Enos 2021 (precinct-
  level confirmation).
- **Engine map:** `social_coord` migration — agents drift in
  `social_coord` over time toward party-similar coordinates,
  analogous to `TieRewiring` for ties but for the social-coord
  attribute. New rule `ResidentialMigration`. Brown & Enos
  estimate ~30% is intentional partisan sorting; ~70% is
  inadvertent lifestyle correlation — the rate parameter must mix
  the two.
- **Time profile:** ramp up from 1980 onward, accelerating post-
  ~2000 (mass online lifestyle clustering).
- **Confidence:** medium-high.

### 6.2 Cohort replacement

- **Claim:** the population's polarization profile shifts as
  cohorts age in and out. Boomers replacing Silent; Millennials/
  Gen-Z replacing Boomers. Phillips 2022 *Political Behavior*
  44:1483 decomposes the rise into period/cohort/life-cycle.
- **Engine map:** ~0.3% of agents replaced per tick (~1%/yr at 3
  ticks/yr), drawn from a younger-cohort distribution. New
  `EnvRule`. The new-cohort distribution shifts over time:
  Boomers (entering through 1990s) more centrist; Millennials
  (entering 2000s+) more liberal-leaning and more politically
  identified; Gen-Z (entering 2010s+) further liberal-leaning,
  diploma-divide-stratified.
- **Time profile:** constant rate, but the cohort being introduced
  changes by decade.
- **Confidence:** high mechanism (demography); medium on cohort
  distribution differences.

### 6.3 Asymmetric polarization (Hacker & Pierson)

- **Claim:** the GOP has moved further right than Dems have moved
  left. DW-NOMINATE GOP median +0.30, Dem median -0.10 over the
  modern era — roughly 3:1 asymmetry. Hacker & Pierson 2020 *Let
  Them Eat Tweets*; Pierson & Schickler 2020.
- **Engine map:** asymmetric `EliteDrift` (the existing rule
  already supports `asymmetric={0: 0.5, 1: 1.5}`); per-party
  `PARTY_CUE_SIGMA` (Phase 8a P-Asymmetry deferred fork — now
  activated). The Phase 8a default of symmetric σ=0.25 for both
  parties is replaced in the historical scenario with asymmetric
  values (σ_dem ≈ 0.22, σ_rep ≈ 0.30 — wider Republican
  distribution per Hacker & Pierson's diagnosis).
- **Time profile:** ramp up over decades; Citizens United (2010)
  is the discrete acceleration.
- **Confidence:** medium-high empirically; medium on the specific
  σ split.

### 6.4 Per-agent heterogeneity on `epsilon`, `α`, `affect_lr`

- **Claim:** the population isn't uniformly receptive. A
  fat-tailed minority of "engaged partisans" (Converse 1964 "issue
  publics"; Zaller 1992 high-information citizens; Achen & Bartels
  2016 "team-identified" voters) does disproportionate causal work
  on macro polarization. Uniform engine parameters wash this out.
- **Engine map:** at build, draw per-agent:
  - `epsilon` ~ Beta(α₁, β₁) centered at the pillar's 0.30,
    fat-tailed (some agents close-minded, many normally
    receptive).
  - `α` (FJ anchor rate) ~ Beta(α₂, β₂) centered at 0.05,
    correlated with `identity_strength` (high-identity agents are
    more anchored).
  - `affect_lr` ~ Beta(α₃, β₃) centered at 0.01, also correlated
    with `identity_strength`.
  - The pillar's existing `stubbornness` ~ Beta(2, 5) is the model
    of this pattern; extend it to the other three parameters with
    similar Beta distributions.
- **Engine implementation:** each rule reads its parameter from
  `agent.state.attrs` first, falling back to the rule's instance
  attribute (the current population-uniform value). Non-pillar
  scenarios continue to use the rule-level uniform values.
- **Time profile:** the distributions shift over decades — engaged-
  partisan tail grows post-2000 (cable TV/social media engagement);
  median agent unchanged.
- **Confidence:** high mechanism (multiple classic citations);
  medium-low on specific Beta shapes (judgment fork).

### 6.5 IdentitySorting with time-varying rate

- **Claim:** Mason 2018's mega-identity-sorting is what *qualitatively*
  distinguishes modern polarization. Running historical replication
  with `IdentitySorting.sort_rate = 0` (the pillar default) would
  guarantee a miss on the modern endpoint — there's no mechanism
  to align race / religion / lifestyle with party.
- **Engine map:** `IdentitySorting` is in the pipeline already
  (currently inert in the pillar at `sort_rate = 0`). The historical
  scenario activates it with a time-varying rate:
  - 1980-1990: low rate (~0.005) — sorting underway but slow.
  - 1990-2000: medium rate (~0.015) — post-Southern-realignment
    consolidation; Mason's "the great sort" period.
  - 2000-2010: high rate (~0.025) — cable-news + early-internet
    intensification.
  - 2010-2020: high rate (~0.025) — social media + cultural
    polarization.
  - 2020-2025: medium-high (~0.020) — slight saturation.
- **Pillar untouched:** the pillar continues to run
  `IdentitySorting.sort_rate = 0`. Stage clarity preserved. The
  pillar's S0-S4 bundle parameters are sacred (§9).
- **Confidence:** mechanism is high (Mason is direct); rate
  schedule is calibration judgment.

**Judgment fork B-Mechanisms-Confirm:** confirm all 5? Drop any?
Recommended default: keep all 5 — anything less misses something
the empirical literature says is load-bearing.

---

## 7. One-off historical events (post-1980)

v1's 8-event schedule shrank to 6 post-1980 events. CRA / Southern
realignment is initial-condition fact; Reagan / Moral Majority is
absorbed into the 1980 initial conditions (identity-party
correlation pre-seeded).

| Year | Tick | Event | Sign | Engine map |
|---|---|---|---|---|
| 1987 | 21 | Fairness Doctrine repealed | enables partisan broadcast media | step-up `MediaConsumption.strength` from 0 to baseline |
| 1996 | 48 | Fox News launched | partisan media intensifies | step-up `MediaConsumption.strength` further; outlet roster shifts |
| 2008-2012 | 84-96 | Smartphone + social media mass adoption | algorithmic amplification | ramp-up `BoundedConfidenceInfluence.affect_weight` (Phase 5 A4) from 0 to 0.3 over the ramp |
| 2010 | 90 | Citizens United | donor influence on elite divergence | step-up `EliteDrift.rate` (asymmetric, R-heavy) |
| 2016 | 108 | Trump election | non-monotonic GOP coalition realignment | one-off shift in GOP `party_cue` distribution + step in identity sorting rate |
| 2020 | 120 | COVID + 2020 election + January 6 fallout | affective polarization spike | step-up `AffectiveUpdate.lr` for 2020-21 then return to baseline |

**Implementation pattern:** each event is a *scheduled parameter
change* fired at its tick. The historical scenario carries a
`Schedule` object: an ordered list of `(tick, callable)` pairs;
each callable mutates the engine's rule parameters at that tick.

**Judgment fork B-Events-Granularity-Revised:** is 6 events right?

- **(a) Keep 6** as listed. Captures the major mechanism transitions.
- **(b) Drop to 4** (Fairness, Fox, social-media-ramp, Trump). Tighter
  scope.
- **(c) Expand to 8+**: add 2014-15 (BLM identity salience), 2017
  (Charlottesville), specific tax-cut events, etc. Higher fidelity;
  higher overfit risk.

**Recommended: (a) 6 events.**

---

## 8. Decade-by-decade workflow

The workflow that replaces v1's strict forward-prediction discipline.

### 8.1 Sequence

1. **Build at 1980.** Cold-build a population matching the 1980
   initial-condition targets (§3). The build itself has parameters
   (initial position distribution, identity correlations, etc.)
   that are calibrated **once** to hit the 1980 anchors.
2. **Run 1980-1990 (30 ticks).** Apply the 1987 event at tick 21.
   Measure decade-end metrics.
3. **Calibrate 1990 fit.** The 6.4 heterogeneity distributions and
   the 6.5 IdentitySorting schedule for 1980-90 are the per-decade
   knobs. Adjust them to hit the 1990 target band. Once hit, freeze.
4. **Repeat for 1990-2000, 2000-2010, 2010-2020, 2020-2025.** Each
   decade's per-decade knobs are independently calibrated; previous
   decades' calibrations are not revisited.
5. **Final pass:** end-to-end run with the full calibrated schedule.
   Report every decade-end measurement vs target. Document hits,
   misses, and the fit's sensitivity.

### 8.2 What the per-decade knobs are

**Judgment fork B-Per-Decade-Scope:** which parameters can be tuned
per-decade?

- **Tunable per-decade** (default scope):
  - `IdentitySorting.sort_rate` (the 6.5 schedule)
  - `ResidentialMigration.rate` (6.1 ramp)
  - The cohort-replacement source distribution (6.2)
  - `MediaConsumption.strength` (event-triggered steps; the *step
    size* per event is tunable)
  - `BoundedConfidenceInfluence.affect_weight` (the 2008-12 ramp)
  - `EliteDrift.rate` and `asymmetric` (6.3 + 2010 event)
  - `AffectiveUpdate.lr` (2020 spike + baseline)

- **Tunable once (build-time only):**
  - The 1980 initial-condition distributions
  - Per-agent heterogeneity Beta shapes (6.4)
  - `PARTY_CUE_SIGMA` per party (6.3 asymmetric)
  - The cooperative-mute factor (Phase 7 setting; unchanged)

- **Forbidden — pillar-calibrated invariants** (§9):
  - The pillar's S0-S4 bundle parameter values
  - The HK canonical-test thresholds
  - The X1-X6 intervention bucket labels under the pillar's
    end-state
  - `TICKS_PER_YEAR`, `FJ_ALPHA`, `BC_TEMPERATURE`,
    `BC_AFFECT_WEIGHT`, `TR_AFFECT_WEIGHT_REWIRE`,
    `BACKLASH_AFFECT_THRESHOLD`, `COOPERATIVE_MUTE` constants

**Recommended default:** as above. The "tunable per-decade" set is
generous enough to fit; the forbidden set is sacred.

### 8.3 What happens when a decade doesn't fit

**Judgment fork B-Decade-Miss:**

- **(a) Abort.** If decade-end metrics can't be brought into band
  by tuning the per-decade knobs, stop. The model is missing a
  mechanism; document and propose a new mechanism as Phase 8c work.
- **(b) Accept miss, continue.** Run the model with the
  best-attempt calibration and continue to the next decade.
  Document the miss in `methods.md`.
- **(c) Propose mid-stream mechanism.** If a decade can't be fit
  with the existing 5-mechanism set, document the specific failing
  metric and propose a new mechanism (e.g., perception-gap
  dynamics for an unmoving affect; social-media-as-distinct-channel
  for an unmoving cross-cutting). Then update the spec, re-run.

**Recommended default: (b) accept miss, continue, document.** This
respects the curve-fitting guardrails (don't add mechanisms post-
hoc within the same calibration session) while keeping the run
complete. (c) is the Phase 8c → 8d evolution path.

---

## 9. Curve-fitting guardrails — the discipline

The discipline that replaces strict pre-registration in v2. The
historical scenario gets its own knobs; the pillar stays sacred.

### 9.1 What stays green throughout

These tests **must** pass at the same thresholds throughout Phase
8b's existence. Any historical-scenario change that breaks any of
them is invalid.

- **Canonical HK tests** (`tests/test_canonical.py`): loose ε =
  0.001, mid = 0.554, tight = 0.648 final variance. Unchanged
  thresholds.
- **Machinery tests** (`tests/test_machinery.py`): determinism,
  idempotence, the apply_intervention error cases. All 5.
- **Network unit tests** (`tests/test_network.py`): all 11.
- **Phase 4 unit tests** (`tests/test_phase4.py`): all 12 — F1
  anchored agents, F2 graded filter, F3 involuntary stratum.
- **Phase 5 unit tests** (`tests/test_phase5.py`): all 12 — A1
  sign fix, A4 BC affect modulator, A5 tie-rewiring affect bias.
- **Phase 6 unit tests** (`tests/test_phase6.py`): all 11,
  including the **consolidated bucket test** that locks every
  X-intervention's per-axis label.
- **Phase 7 tests** (`tests/test_phase7.py`): all 6 — calibration
  constants, ANES anchor regression, X3 backfire guard,
  no-collapse property.
- **Phase 8a tests** (`tests/test_phase8a_partypull.py`): all 4 —
  party_cue seeded, fallback, personal-cue pull, within-party SD
  regression.
- **Phase 4-7 pillar §11 thresholds** (`tests/test_pillar_stages.py`):
  all 9.

Total: **73 tests**, all currently green at Phase 8a. Phase 8b
adds historical-scenario tests on top; it does NOT modify any of
the above.

**Judgment fork B-Guardrail-Inventory:** which tests count? The
list above is comprehensive — every test currently in the suite.
A leaner version could drop the unit tests (which test mechanism
fidelity) and keep only the §11-measured pillar / canonical /
intervention-bucket assertions (which test calibrated behaviour).

**Recommended default:** include everything. The unit tests are
cheap to run and catch mechanism regressions that the §11
behavioural assertions might miss.

### 9.2 Pre-registration of per-decade targets

Before calibrating each decade, the empirical targets for that
decade (the table in §4 — and any narrowing within the band) are
committed to this design doc. The target itself cannot slide to
match the model's behaviour.

**The flow:**
1. Pin the decade's target band (from §4 — or narrow it before
   calibration starts).
2. Run, calibrate per-decade knobs, measure.
3. If measurement is in band → bless the calibration.
4. If measurement is out of band → §8.3 fork (abort / accept-miss
   / propose-mechanism).
5. **Do not** widen the target band post-hoc to make the
   measurement fit.

### 9.3 No retroactive step-size re-tuning

The pillar's calibrated step sizes (BC strength, PartyPull
strength, MediaConsumption strength, FJ_ALPHA, etc.) come from the
Phase 4-7 §11 process. Phase 8b does **not** re-tune them. The
historical schedule turns mechanisms on/off and adjusts magnitudes
*within* the pillar's calibrated envelope, but does not reach into
the calibrated constants.

This is the hardest discipline to maintain because it's tempting
to bump a step size by 10% to make a decade fit. **The rule: if
the historical scenario needs a step size outside the pillar's
calibrated value, the missing-mechanism case (§8.3 (c)) applies.**

### 9.4 Sensitivity sweeps

For each per-decade knob, run a sensitivity sweep showing how the
decade-end metrics vary. If a 10% perturbation flips a metric from
pass to fail, the fit is fragile — say so in `methods.md`.

### 9.5 Single-seed shipping forbidden

Every result is a 5-seed ensemble mean (for historical-arc
specifically; the pillar stays at 12).

### 9.6 Document misses honestly

`methods.md` gets a new §7: "Historical replication results." Every
decade-end's measured value is recorded next to its target band.
Hits reported; misses reported with diagnosis. Per-decade
calibration commits are recorded.

---

## 10. Measurement cadence

When to measure during the 1980 → 2025 arc.

**Judgment fork B-Cadence-Revised:**

- **(a) Decade-end only** (5 measurement points: 1990, 2000,
  2010, 2020, 2025). Cheapest; matches the per-decade workflow.
- **(b) Event-anchored + decade-end** (~10 points: 6 events + 5
  decade-ends, minus overlaps). Allows event-impact diagnostics.
- **(c) Annual** (45 points). Trajectory smoothness comparison.
  Most expensive.

**Recommended default: (b) event-anchored + decade-end.** Captures
event impacts (Fox News step, social media ramp, etc.) plus
decade-end calibration checks. Cheaper than annual; richer than
decade-end alone.

**Aggregation:** 5-seed ensemble means.

---

## 11. Seed count and compute

Phase 8b uses **5 seeds for historical-arc runs**, not the pillar's
12. The pillar's tests stay at 12.

**Why 5:** the historical-arc run is more expensive (5 mechanisms,
135 ticks, multiple measurement points per run). With the
default 12 seeds it would take ~25-30 min per ensemble. At 5 seeds,
~10-12 min per ensemble — fast enough for per-decade calibration
iteration.

**Compute budget:** per-decade calibration could require 5-10
ensemble runs (sweep the per-decade knobs). At 12 min/ensemble ×
8 runs = ~96 min per decade × 5 decades = ~8 hours total
calibration. Acceptable for a one-time setup.

**Judgment fork B-Seeds-Confirm:** 5 OK, or should historical-arc
use a different count?

- **(a) 5** — Vlad's stated default.
- **(b) 8** — middle ground.
- **(c) 12** — match pillar; but ensemble runs are 2.5× slower.

**Recommended default: (a) 5.**

---

## 12. Pass rubric

Per-decade calibration within the §4 tolerance bands, with the §9
guardrails as the honesty discipline.

**Pass per decade:** decade-end measurement in band for all
primary metrics. Secondary metrics (modularity, cross-cutting
fraction at low-confidence anchors) are reported but don't gate.

**Pass overall (Phase 8b complete):** every decade-end passes;
the §9 guardrails (every pillar test green) hold throughout;
sensitivity sweeps documented; misses (if any) honestly reported.

**Judgment fork B-Pass-Per-Decade-Tiered:**

- **(a) All primary metrics in band per decade.** Strictest.
- **(b) Tiered: high-confidence anchors gate; medium/low report.**
  Mirrors the v1 §3 tiering for 2025 endpoint.
- **(c) N-of-M: at least 5-of-7 primary metrics in band per
  decade.** Allows small misses without failing the decade.

**Recommended default: (b) tiered.** Use the §3-§4 confidence tiers
to weight pass conditions. Constraint / separation / affect / SD
gate; cross-cutting / modularity / variance report.

---

## 13. The fork list — v2

The revised, consolidated list of judgment forks for Vlad's call.
Forks marked **(NEW)** emerged from v1→v2; others updated.

| ID | Fork | Default | Worth weighing |
|---|---|---|---|
| **B-Run-Mode** | Test architecture | standalone scenario (`abm/pillars/historical_arc.py`); pillar untouched | pillar variant; replace pillar |
| **B-Mechanisms-Confirm** (NEW) | Confirm the 5-mechanism set | Big Sort + cohort + asymmetric + heterogeneity + IdentitySorting-time-varying | drop any; add religious / social-media-channel / perception-gap |
| **B-Heterogeneity-Shapes** (NEW) | How to calibrate the Beta distributions for `epsilon`/`α`/`affect_lr` | Beta shapes pinned at build-time, fitted to ANES engagement-distribution fat tail; correlated with `identity_strength` | each parameter independent; chosen by hand without empirical fitting |
| **B-IdentitySorting-Schedule** (NEW) | Shape of the time-varying `sort_rate` | piecewise-constant per decade (1980-90: 0.005; 1990-00: 0.015; 2000-10: 0.025; 2010-20: 0.025; 2020-25: 0.020) | smooth ramp; sigmoid centered on 1995; step at 1990 only |
| **B-Events-Granularity-Revised** | Event schedule scope | 6 events post-1980 | drop to 4; expand to 8+ |
| **B-Events-Implementation** | Step vs ramp per event | mixed (Fox = step; social media = ramp) | all step; all ramp |
| **B-Cadence-Revised** | Measurement schedule | event-anchored + decade-end | decade-end only; annual |
| **B-Seeds-Confirm** (NEW) | Seed count for historical arc | 5 | 8; 12 (match pillar) |
| **B-Per-Decade-Scope** (NEW) | Which parameters tunable per-decade | as §8.2 default scope; pillar invariants forbidden | wider scope (allow step-size touching — would break the discipline); narrower scope (only IdentitySorting and event step sizes) |
| **B-Decade-Miss** (NEW) | What if a decade can't fit | accept-miss, continue, document | abort; propose new mechanism mid-stream |
| **B-Guardrail-Inventory** (NEW) | Which existing tests count as sacred invariants | all 73 (every current test) | leaner: only §11 behavioural assertions, not unit tests |
| **B-Pass-Per-Decade-Tiered** | Pass/fail composition per decade | tiered (primary gates, secondary report) | all-in-band strict; N-of-M |
| **B-PartyPull-Asymmetry-Now** | Per-party `PARTY_CUE_SIGMA` (Phase 8a deferred) | σ_dem ≈ 0.22, σ_rep ≈ 0.30 — activated in the historical scenario only; pillar stays symmetric at 0.25 | symmetric in historical too; different split |
| **B-Pillar-Status** | Does pillar exist alongside historical | yes (pillar = teaching; historical = validation) | replace pillar |

---

## 14. What this design does NOT specify

- Code-level file layouts, class names, function signatures.
- Test names or assertion syntax.
- The implementation-spec house-style §11 measure-then-bless steps
  (those go in a separate `phase8b_historical_replication_spec.md`
  once this design is confirmed).
- Specific 1980 initial-condition distribution parameter values
  (these follow from §3 once the band-narrowing-pre-calibration
  step is committed).
- Specific per-decade knob values (these emerge from the
  calibration process, not the design).

---

## 15. Open questions / sanity checks

- **Does the per-agent heterogeneity break the pillar's
  Phase 4-8a invariants?** The historical scenario is a separate
  scenario file; the pillar continues to use rule-level uniform
  values. The implementation must ensure non-pillar scenarios
  (including the pillar) fall back to the uniform values when
  per-agent attrs are absent (same pattern as Phase 8a's
  `party_cue`).
- **Compute budget for per-decade calibration.** Estimated ~8
  hours total. Acceptable; not interactive.
- **What about post-2025?** The model is calibrated to 1980-2025;
  extrapolation to 2050 is not defended. The eventual public-
  facing demo must NOT promise forecast capability.
- **The 1980-2025 window leaves out the 1955-1980 transformation.**
  Vlad's call: accept this as initial-condition. The pre-1980
  transformation is documented in `methods.md` as a known gap.
- **What's the relationship between heterogeneity and X-interventions?**
  The intervention library (X1-X6) was calibrated under uniform
  agent parameters. Adding per-agent heterogeneity might shift the
  X-bucket measurements. The §9 guardrail says the X buckets must
  stay green — but the X buckets are measured *on the pillar's
  S4 end-state*, not the historical scenario's end-state.
  Heterogeneity lives in the historical scenario only; pillar
  X-buckets are preserved.

---

## 16. Sign-off

This v2 design folds in all of Vlad's adjustments:
1. Heterogeneity added as a mechanism (5.4).
2. IdentitySorting activated with time-varying rate (5.5).
3. Start year 1980, not 1955 (§2-§3).
4. Decade-by-decade workflow (§8).
5. Curve-fitting guardrails (§9).
6. Seed count 5 for historical only (§11).
7. Revised 6-event set post-1980 (§7).
8. Per-decade tolerance bands weighted by data quality (§4).
9. Tiered pass rubric (§12).

Strict forward-prediction-stacked validation is **documented as
Phase 8c** — the next-level test once 8b confirms decade-by-decade
calibration is achievable without breaking pillar invariants.

Standing by for confirm or further iteration on the design before
any implementation work begins.
