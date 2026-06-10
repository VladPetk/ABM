# polarlab — methods

*The artifact that backs the project's "intellectually rigorous"
claim. Every calibration choice, every honesty-label, every limitation
recorded here is the one the model actually carries. Last updated 2026-06
(Phase 10 intervention re-measure + the 2026-06 affect re-grade; web-demo
sandbox dials noted in §5.11).*

> **Source index.** For an annotated map of every dataset and paper the model
> uses — what each one anchors and where in the repo — see
> [`literature.md`](literature.md). The flat bibliography is in §"Citations" at
> the foot of this file.

---

## 1. What the model represents

polarlab is an agent-based model of political polarization in a
US-like, two-party society over a ~60-year stylised window — roughly
the post-WW2 / mid-1950s "quiet" baseline through the mid-2020s. The
default `n_agents = 250` is a "village-scale" society chosen for test
speed; the dynamics scale invariantly to larger populations.

The engine is **network-primary** (ADR-001, 2026-05-25): influence
flows along edges of a homophilous social network, not by raw
ideological proximity. Ideology space (the 2D economic × cultural
compass on `[-1, 1]²`) holds agent state and supports visualization;
it does not decide who hears whom. Classic Hegselmann-Krause survives
as the complete-graph special case — `compass_basic` runs it
unchanged, with the canonical replication tests intact.

**One tick ≈ 4 months** of stylised real-world time
(`TICKS_PER_YEAR = 3.0` in `abm/calibration.py`). The default
`TICKS = 200` represents ~67 years; the pillar's S0→S3 progression
maps to roughly the 1955-2020 ANES window.

---

## 2. The five-stage pillar

`abm.pillars.calm_to_camps` defines one canonical journey, a society
moving from neutral baseline through full polarization:

| Stage | Mechanism added | Stylised real-world span | Honesty tag |
|-------|-----------------|--------------------------|-------------|
| S0 Baseline | noise only | ~mid-1950s "calm" | control |
| S1 Bounded confidence | who you listen to | ~1960s–70s | replication (Hegselmann-Krause) |
| S2 Party identity | party cues + affect | ~1970s–90s | illustrative |
| S3 Partisan media | media diets pull diets outward | ~1990s–2010s | illustrative |
| S4 Homophilous network | sticky social-circle sorting | ~2010s onwards | illustrative |

The pillar runs **continuously**: positions carry over between stages.
Validation runs use cold per-stage builds; the journey itself never
resets.

---

## 3. Calibration anchors

The four empirical anchors recorded in `abm/calibration.py`'s
`EMPIRICAL_ANCHORS` registry. Each is the published finding the model
is checked against; the "model_check" line records what the model
actually produces.

**Provenance tags (Phase 8c D1).** Anchors and mechanisms are tagged
L / N / E throughout:

- **L (literature-supported):** the model's parameter matches a
  published empirical value (e.g. ANES thermometer fall → 200-tick
  affect projection band; DW-NOMINATE divergence rate →
  `EliteDrift.rate`).
- **N (new):** mechanism or value introduced by polarlab without a
  direct published anchor.
- **E (extrapolation):** the literature constrains direction and
  rough magnitude; polarlab maps it onto a specific per-tick / per-
  encounter operator that is not literally specified in the source.
  Examples: the cooperative-mute multiplier (§3.3) maps a cumulative
  meta-analytic `r ≈ −0.21` onto a per-encounter scale; the graded
  logistic filter (Phase 4 F2 at `temperature > 0`) departs from
  canonical HK at the operational T.

When this distinction matters for a section's calibration, the tag
is stated inline.

**A second, orthogonal axis: where the force comes from.** L/N/E grades
*how well-evidenced* a choice is. A separate question is *what kind of
force* a rule represents — and the two are independent. The engine's
forces fall into three kinds (full taxonomy + the per-rule classification
in [`ENGINE_OVERVIEW.md`](ENGINE_OVERVIEW.md) §4.7):

1. **Emergent / endogenous** — the per-agent delta depends on the
   agent's own evolving state and/or its network neighbours (bounded
   confidence, contact-gated affect, tie rewiring; identity sorting is
   endogenous *in form* but its 1980→2025 rise is ~83% schedule-carried —
   see the §5.13 relabel).
2. **Exogenous drivers on a calendar clock** — the same pressure applied
   to everyone (or a fixed group) at dated times. Legitimate *because
   the model is of the mass public*: elite divergence (`EliteDrift` /
   Gingrich-1994), the media environment (Fairness-Doctrine 1987, Fox
   News 1996, the social-media ramp), and dated shocks (2016 status
   threat) are genuinely exogenous to the 250 agents and enter as
   boundary conditions.
3. **Tuned constants applied uniformly** — calibrated scalars and curves
   (learning rates, thresholds, the party-issue coupling schedule
   0.40→1.10, `cooperative_mute = 0.5`). These are unavoidable in any
   calibrated model; they are precisely what gets tagged **N** on the
   magnitude even when the mechanism is **L**.

A constant can therefore be **L** in *direction* (Pettigrew & Tropp:
contact halves prejudice) yet an imposed, uniformly-applied, tuned
scalar in *magnitude* — the two axes say different things, and both are
recorded.

**The dated-referent test (methodological principle).** A calendar-time
schedule is admissible **only if it maps to a real dated exogenous
change** (a media launch, an adoption ramp, a campaign shock). A uniform
calendar curve tuned *only* to reproduce the target trajectory is
**curve-fitting** — "painting the target on" — and is not admissible,
because the model would merely be replaying the trajectory it was fed. A
worked enforcement of this rule is the 2026-06 affect re-grade (§5.10):
a time-ramped `affect_lr` was rejected for having no real-world referent,
and the late steepening of out-party animus was instead sourced from
*endogenous* identity-alignment × a *dated* media-exposure driver — a
schedule that does map to a real change. The corollary check that the
arc is not *only* its schedules is the **pillar**: the same mechanisms
run with no dated events, so it isolates what the dynamics generate on
their own (the composition layer; see CLAUDE.md's three test layers).

**Friedkin-Johnsen realization (Phase 8c D5 clarification).**
polarlab implements the Friedkin-Johnsen anchoring via two separate
mechanisms that, summed, approximate FJ:

1. **Per-rule `(1 − stubbornness)` scaling.** Each ideology-moving
   rule (`BoundedConfidenceInfluence`, `PartyPull`, `MediaConsumption`,
   `BacklashRepulsion`) multiplies its intended `d_ideology` by
   `(1 − stubbornness)` at the apply site. Stubborn agents (high s)
   take less of every rule's pull.
2. **`GaussianNoise` damping toward anchor.** `GaussianNoise` adds an
   extra `FJ_ALPHA * stubbornness * (anchor − position)` pull per
   tick — anchored agents are pulled back to their starting position
   at rate `FJ_ALPHA * stubbornness = 0.05 * stubbornness`.

This **sums multiple per-rule pulls before damping**, which is a
slight departure from canonical Friedkin-Johnsen (where the anchor
pull and the social pull are combined in a single update step). The
departure is small at the pillar's stubbornness distribution
(`Beta(2, 5)`, mean ≈ 0.29): the per-rule scaling is uniform across
rules, so the net effect on each step is `(1 − s) * (sum of all
rule pulls)` plus the anchor damping, which is algebraically the same
as canonical FJ for a stationary set of pulls — but for a sequence
of *different* rule pulls per tick, the polarlab realization
multiplies each by `(1 − s)` and then adds the damping at the end of
the step. The empirical difference is small at our stubbornness
distribution; the difference is flagged for transparency. **Provenance
tag for the FJ realization: L (form) + E (the multi-rule decomposition).**

### 3.1 ANES out-party thermometer (the tick-to-year scalar)

- **Source:** Iyengar, Lelkes, Levendusky, Malhotra & Westwood 2019,
  *Annual Review of Political Science* 22:129 (review of the
  1978-2020 ANES thermometer trend); Finkel et al. 2020, *Science*
  370:533 (synthesis paper that re-summarises the same trend).
  Iyengar et al. 2019 is the canonical empirical anchor; Finkel 2020
  is a synthesis citation, not an independent measurement.
- **Finding:** mean out-party feeling-thermometer scores fell from
  ~48° (1978) to ~20° (2020) — a 28-point drop over 42 years on the
  [0, 100] thermometer, or **−0.56 normalised** to the model's
  [−1, 1] affect axis.
- **Model check (what the Phase 7 test actually guards).** The
  pillar's S0→S3 measured Δaffective_polarization is ≈ −0.85 over
  200 ticks. The test in
  `tests/test_phase7.py::test_pillar_affect_trajectory_matches_anes_within_band`
  guards the **trajectory shape** at the *full-200-tick / ~67-year*
  horizon: it asserts the mean S3 affect sits within ±20% of
  `−0.56 * (200/126) ≈ −0.89` (the ANES anchor linearly projected
  to the 200-tick window). It does **not** assert that the 126-tick
  (42-year ANES window) measurement equals `−0.56`. The pillar's
  S2/S3 trajectory is non-linear (S0/S1 carry `affect_lr = 0`; most
  cooling happens in S2/S3), so the 126-tick value is not a simple
  linear scaling of the 200-tick value. The "within ~5%"
  arithmetic projection (`126/200 * −0.85 ≈ −0.535`) is a derived
  projection from the *full-window measurement*, not a separate
  measurement at 126 ticks. **Phase 8c D4 clarification:** the test
  guards trajectory shape at one horizon, not anchor agreement
  across all horizons.
- **Pinning:** `TICKS_PER_YEAR = 3.0`. The pillar's full 200-tick
  trajectory corresponds to ~67 years of stylised history.

### 3.2 DW-NOMINATE elite divergence (latent — for any scenario that
enables `EliteDrift`)

- **Source:** McCarty, Poole & Rosenthal 2006, *Polarized America*.
- **Finding:** the median Democrat–Republican NOMINATE distance
  diverged by ~0.4 units over ~50 years.
- **Model check:** `EliteDrift.rate ≈ 0.0026` per tick reproduces the
  empirical rate at `TICKS_PER_YEAR = 3.0`. EliteDrift is inert in
  the pillar's S0–S4 baseline; this anchor is a sanity check for any
  scenario that enables it.

### 3.3 Pettigrew & Tropp contact-hypothesis meta-analysis (cooperative-conditions
mute)

- **Source:** Pettigrew & Tropp 2006, *Journal of Personality and
  Social Psychology* 90:751 (meta-analysis of 515 studies on
  intergroup contact; r ≈ −0.21 between contact and prejudice).
- **Finding:** contact under Allport (1954) conditions — equal
  status, cooperative tasks, institutional support — roughly halves
  prejudice formation.
- **Pinning (Phase 8c §2 — replaces Phase 7 edge-level mute):**
  `AffectiveUpdate.cooperative_mute = 0.5` is the *agent-level*
  fully-cooperative mute multiplier. Each agent carries
  `cooperative_share ∈ [0, 1]` (default 0.0); negative valence on
  every out-party encounter is multiplied by
  `1 − cooperative_share * (1 − cooperative_mute)`. A fully-
  cooperative agent (`coop_share = 1.0`) gets exactly the
  Pettigrew & Tropp halving; a non-cooperative agent
  (`coop_share = 0.0`) gets no muting. X6's setup adds
  `cooperative=True` involuntary edges AND bumps participating
  agents' `cooperative_share`. Cooperative edges also trigger a
  positive-going valence path when the agent's warmth is at or
  above `coop_positive_threshold = -0.2` (Pettigrew 2009 secondary-
  transfer). The F3 baseline involuntary stratum (kin / workplace)
  is **not** cooperative and does **not** bump cooperative_share —
  the literature is explicit that contact alone is insufficient.
- **Provenance: E (extrapolation), not L (literature-supported).**
  Pettigrew & Tropp's `r ≈ −0.21` is a **cumulative** meta-analytic
  correlation between contact and prejudice — measured across whole
  studies, not per encounter. The "halves valence" reading is an
  *extrapolation* that maps the cumulative effect onto a per-
  encounter multiplier. The literature constrains the direction and
  rough magnitude; it does not literally specify a per-encounter
  scale factor. Earlier drafts of this section labelled the mute
  L (literature-supported); Phase 8c D1 reclassifies it E.
- **Modelling judgment flagged (Phase 6/7 reading):** the
  Phase 6/7 implementation was *edge-level* mute (only encounters
  across cooperative edges attenuated). Pettigrew 2009's "secondary
  transfer effect" suggests a broader *agent-level* mute. Phase 8c
  §2 replaces the edge-level mute with an agent-level
  implementation, more faithful to Pettigrew 2009.

### 3.4 Allcott / Meta-2020 algorithmic interventions (the null anchor
for X2)

- **Source:** Allcott, Braghieri, Eichmeyer & Gentzkow 2020,
  *American Economic Review* 110:629 (Facebook deactivation); Guess
  et al. 2023, *Science* 381:398, and Nyhan et al. 2023, *Nature*
  (Meta/US 2020 chronological-feed studies).
- **Finding:** algorithmic-feed interventions produce essentially
  null (or small, in Allcott's case) effects on issue + affective
  polarization at the population level.
- **Model check:** X2 "Fix the algorithm" measured Δsep ≈ −0.02,
  Δaff ≈ −0.01 — null on both axes.

### 3.5 Mutz 2018 status-threat (Phase 8c §5 — historical-arc only)

- **Source:** Mutz 2018, *PNAS* 115:E4330 (status threat, not
  economic anxiety, explains the 2016 vote).
- **Finding:** white Republican voters reported elevated identity /
  status threat in response to demographic and cultural-change cues
  around the 2016 election, which amplified out-group hostility.
- **Pinning (Phase 8c §5):** every agent carries
  `perceived_threat ∈ [0, 1]` (default 0.0). The 2016 historical
  event sets `perceived_threat = 0.5` for 60% of party=1
  (Republican) agents. `AffectiveUpdate` multiplies the negative-
  going valence by `(1 + threat_amplification * perceived_threat)`,
  doubling cooling at full threat; positive (cooperative) valence
  is **not** amplified (threat is identity-defensive, not socially
  open). `BacklashRepulsion` push magnitude is amplified by the
  same factor. `ThreatDecay` env-rule multiplies threat by
  `(1 - 0.05)` each tick — half-life ≈ 14 ticks ≈ 4.7 years, so
  the 2016 spike decays to ~half by 2020 and to noise by 2025.
- **Provenance: split L / E (Phase 8e §5.2 disambiguation).**
  - **L (literature-supported, *direction*)**: Mutz 2018
    establishes the existence and direction of the white-Republican-
    specific status-threat → amplified hostility effect, and the
    ~60% population fraction.
  - **E (extrapolation, *magnitude*)**: the `THREAT_2016_MAGNITUDE
    = 0.5` per-agent amplitude and the `THREAT_DECAY_RATE = 0.05`
    half-life are **post-hoc fits** to the 2016 ANES thermometer
    spike's shape. They are NOT literature anchors; they were
    chosen to roughly reproduce the empirical 2016 spike-and-decay
    pattern in the historical arc. **The 2016 spike match is
    therefore NOT independent evidence** of the model's accuracy
    — it's a curve fit, not a forward prediction. Round-2 R2
    correctly flagged this as a circularity concern; this
    disambiguation answers it. A pre-2016 calibration anchor (e.g.
    tuning to the 2008 ANES dip and treating 2016 as forward
    prediction) is a Phase 8f candidate.
- **Pillar invariant.** The pillar's S0-S4 baseline never sets
  `perceived_threat`. Consumers read 0.0 → `threat_factor = 1.0` →
  bit-identical to Phase 8c §4 in the pillar. The mechanism is
  inert in the pillar; it fires only in the historical arc's
  Schedule.

### 3.6 ANES 2D ideological compass, 1986–2024 (distribution-level fit target)

- **Source:** ANES Time Series Cumulative Data File (CDF), 1986–2024.
  Methodology spec: `data/phase9_empirical/raw/anes_2d_ideology_methodology.md`.
  Build: `scripts/anes_2d_compass.py`. Derived outputs:
  `data/phase9_empirical/derived/{coverage_table,recode_log,party_centroids,polarization_series}.csv`,
  `respondent_coordinates.csv`, `scaling_params.json`, `kde_params.json`,
  `densities/{year}_{D,I,R,ALL}.npy`. Small-multiples plot:
  `docs/phase9_empirical/density_small_multiples.png`.
- **Construction.** Window 1986–2024 (14 effective waves; 2002 excluded —
  ANES CDF did not field the cultural items that year). Fixed core panel
  chosen from the actual coverage table: economic = {`VCF0803` lib-cons
  self-placement, `VCF0809` guaranteed jobs/income, `VCF0839` services-
  spending}, cultural = {`VCF0838` abortion, `VCF0830` aid to blacks,
  `VCF0852` adjust moral views, `VCF0853` traditional values}. Listwise
  drop on all 7 items: 44,308 → 22,761 (51.4% retained). Each item
  recoded so higher = conservative; rescaled to [−1, 1] using
  **theoretical scale endpoints** (stricter than the spec's pooled
  min/max — provably zero pooled-stat leakage by construction). Axis
  score = equal-weight mean. KDE bandwidth = Scott's rule on the pooled
  weighted sample (factor 0.2022, frozen) evaluated on an 81×81 grid
  over [−1.05, 1.05]². Survey weight `VCF0009z` applied.
- **Finding (the new calibration curve).** Per-wave 2D overlapping
  coefficient between Dem and Rep joint densities — the **primary fit
  target** — drops from 0.60 (1986) → 0.20 (2020), partial recovery to
  0.25 (2024). Scaled centroid separation rises from 0.96 to 3.20.
  Hartigan's dip rejects unimodality on both axes in essentially every
  wave (only exception: cultural axis 2000, p = 0.09). Realignment
  signature visible in the centroids: Dem economic mean is left-of-zero
  throughout 1986–2024, but Dem cultural mean only crosses to
  left-of-zero from 2012 on.
- **Pinning / model check.** Canonical empirical fit target for Phase 9
  onward. The engine's per-decade pointclouds (under
  `tier_d_anes_knobs=True`, §5.10) are compared via 2D Wasserstein-2
  (`abm.calibration_phase9.aggregate`) to the matching ANES-derived
  `phase9_empirical_pointcloud_{decade}.npy` files. Engine snapshot
  ticks are bucket-centered (1980 ← 21, 1990 ← 42, 2000 ← 72,
  2010 ← 102, 2020 ← 126) so engine and ANES are temporally aligned.
  At the blessed `anes_full` preset, per-decade W₂ sits within ~0.05
  of the achievable Gaussian floor (~0.20 per decade).
- **Acceptance.** Three isolation tests in
  `data/phase9_empirical/derived/acceptance_checks.txt`: re-running
  normalization per-wave (with z-then-clip, a genuinely different scaling
  family) produces axis means that differ from the global build → scaling
  is not leaking per-wave; refitting KDE on a single wave gives bandwidth
  0.41 vs the frozen global 0.20 → density is not leaking per-wave;
  Rep ≥ Dem on both axes in every wave with both parties present → no
  direction-coding bug.
- **Known caveats.** Listwise retention biases toward respondents who
  answered every core item (more politically engaged subset); the engine
  should treat the densities as the population of opinionated voters, not
  the full electorate. 1990 cultural items and 1986 `VCF0809` are
  half-form fielded → smaller N after listwise. CDF skips midterm years
  after 2004 (2006/2010/2014/2018/2022 absent by data design).

---

## 4. The honesty-labels schema

### 4.1 Two-axis bucketing (Phase 7)

The Phase 6 intervention library carries per-axis bucket labels in
`Intervention.effect_buckets`, blessed by §11 measurement:

- **`issue_sorting`** axis: classifies Δparty_separation over the
  release-phase experiment. Helpful direction = negative (camps
  closer). Thresholds: `|Δ| < 0.05` → **null**; `−0.15 < Δ < −0.05`
  → **partial**; `Δ ≤ −0.15` → **real**; `Δ > +0.05` → **backfire**.
- **`affect`** axis: classifies Δaffective_polarization over the
  same window. Helpful direction = positive (out-party warmth
  recovers — note the sign flip from Δsep). Thresholds:
  `|Δ| < 0.05` → **null**; `+0.05 < Δ < +0.15` → **partial**;
  `Δ ≥ +0.15` → **real**; `Δ < −0.05` → **backfire**.

The literature treats these as distinct outcomes (Iyengar et al.
2019; Gidron, Adams & Horne 2020; Pettigrew & Tropp 2006 — affect /
prejudice is what contact reduces; institutional levers move issue
sorting more than affect; etc.), so the schema follows.

### 4.2 The discipline

**Move the tag, not the threshold.** Each intervention's label is
the measured bucket. If a future code change moves an intervention
out of its declared bucket on either axis, the consolidated bucket
test in `tests/test_phase6.py` fails — the calibration script is
re-run, the tag is re-blessed to the new measurement. The
intervention's *mechanism* is what gets locked; the *empirical bucket*
is what the test reports honestly. The thresholds (0.05, 0.15) are
fixed by the spec and are not adjusted to fit a desired narrative.

### 4.3 The current library

Each intervention's measured per-axis label, with the literature
finding it grounds in. Values measured at **N=250, 20 seeds**
(Phase 8c §7 S1), 200-tick release. SE is `std / sqrt(n_seeds)`.
Close-call interventions (within 1 SE of a bucket boundary) carry
a 95% CI for transparency.

> **Substrate note.** This is the **pillar** (end-of-S4) scoreboard and
> is unchanged by the Step-1/Step-2 web re-grade (those changes are
> gated behind `evidence_regrade`, off on the pillar → bit-identical).
> The **shipped / web-facing** buckets are measured on the **historical
> arc** (ANES substrate, 9-seed release-decade sweep) and are the ground
> truth for anything user-facing — see
> [`results/phase10_results.md`](results/phase10_results.md). The two
> substrates agree on direction for every lever; they differ in
> magnitude (e.g. pillar X1 +0.49 vs arc X1 +0.28…+0.40).

| ID | Lay name | Δsep ± SE | issue_sorting | Δaff ± SE | affect | Anchor |
|---|---|---|---|---|---|---|
| X1 | Show people the other side (asymmetric) | +0.490 ± 0.006 | **backfire** | −0.014 ± 0.001 | null | Bail et al. 2018 [Phase 8c §6: asymmetric backfire — party=1 push ×1.3, party=0 push ×0.7 (1.86× ratio); macro bucket unchanged but per-party drift now asymmetric per Bail's R-user finding]. **Evidence grade LOW/CONTESTED** — backfire did not replicate in Guess & Coppock 2020 / Wood & Porter 2019, and the in-engine affect gate fires for 99.8% of partisans at measurement time (§5.4.bis, §5.13). |
| X2 | Fix the algorithm | −0.029 ± 0.002 | **null** | −0.012 ± 0.001 | null | Guess/Nyhan 2023 |
| X3 | Quit cable news (cable-only) | −0.001 ± 0.002 | **null** | −0.013 ± 0.001 | null | Levendusky 2013; Allcott 2020; Martin & Yurukoglu 2017 [Phase 8c §3 re-bless: bucket flipped from backfire to null. Old X3 zeroed MediaConsumption.strength entirely (R1's "category error" — bundling centripetal broadcast with centrifugal cable). New X3 zeros only MSNBC + Fox News weights; result: cable's exit alone doesn't measurably move the macro picture.] |
| X4 | Shared-identity priming program | −0.027 ± 0.002 | **null** | −0.012 ± 0.001 | null | Levendusky 2021 (*Our Common Bonds*); Transue 2007; Wright & Esses 2017 [Phase 8c §4 re-implementation: superordinate-identity prime at 20% of population for 30 ticks. Modest individual-level effects but population-level null, consistent with Levendusky's experimental reports.] |
| X5 | Ranked-choice voting | −0.142 ± 0.002 [95% CI ≈ [−0.146, −0.138]] | **partial** † | −0.014 ± 0.001 | null | Hetherington 2001; Gidron et al. 2020 [† Phase 8c §7 cutoff sweep close call: lands at "partial" under default cutoff 0.15; lands at "real" under tighter cutoff 0.10. CI does not cross −0.15 boundary at 20 seeds.] |
| X6 | Shared neighborhoods and workplaces | −0.048 ± 0.003 [95% CI ≈ [−0.053, −0.043]] | **null** † | +0.242 ± 0.005 | **real** | Allport 1954; Pettigrew & Tropp 2006; Pettigrew 2009 [Phase 8c §2 re-bless: bucket flipped from backfire to real under agent-level cooperative-share mute — see §5.3. † Phase 8c §7 cutoff sweep close call on issue_sorting: "null" under default; "partial" under tighter cutoff 0.03.] |
| X7 | Correct the perception gap | −0.027 ± 0.002 | **null** | −0.012 ± 0.001 | null | Levendusky & Malhotra 2016; Ahler & Sood 2018; Druckman et al. 2022 [Phase 8c §4 new intervention. In the pillar release-phase, X7 is a no-op — pillar agents don't model perception (Path A bit-identity discipline). The meaningful X7 measurement is in the historical arc, where agents carry biased perceptions seeded at build.] |

**Cutoff-sweep stability (Phase 8c §7 S2).** Of the 7 X-interventions,
5 (X1, X2, X3, X4, X7) are bucket-stable across {0.03/0.10},
{0.05/0.15} (default), and {0.08/0.20}. Two are close calls:

- **X5 issue_sorting**: `partial` at default + loose; `real` at tight.
  The Δsep = −0.142 sits ~0.008 from the default "real" boundary.
- **X6 issue_sorting**: `null` at default + loose; `partial` at tight.
  The Δsep = −0.048 sits ~0.002 from the default "null" boundary.

Both close calls are documented honestly: X5's claim is "partial
under the spec's default cutoffs; would be real if the field's
effect-size convention adopted a tighter `real` threshold." X6's
issue-sorting result is "null but borderline." Affect labels are
robust across all configs for both interventions.

The default 0.05/0.15 cutoffs are kept per §7 Fork 7-A's
data-driven decision: 5/7 stable is robust enough to justify the
current threshold scheme; the two close-call interventions get
explicit CI reporting rather than a threshold re-bless.

### 4.5 §11 sensitivity under 12% Independents (Phase 8d)

The §4.3 table reports buckets at the canonical binary-party build
(`independent_fraction = 0.0`). Phase 8d adds a sensitivity reading:
the same §11 release-phase experiment with **12% pure independents
(party=2) in the population** (Klar & Krupnikov 2016 *Independent
Politics*; ANES 2020 pure-independents share ~11-12%). Independents
don't fire `AffectiveUpdate`, `BacklashRepulsion`, `PartyPull`, or
`PerceptionUpdate`; they participate fully in `BoundedConfidenceInfluence`,
`MediaConsumption`, `TieRewiring`, `GaussianNoise`, `IdentitySorting`.
Measured at N=250, 20 seeds, 200-tick release:

| ID | Δsep (binary) | Δsep (12% indep) | Δaff (binary) | Δaff (12% indep) | Note |
|---|---|---|---|---|---|
| X1 | +0.490 ± 0.006 | **+0.253 ± 0.008** | −0.014 ± 0.001 | −0.016 ± 0.001 | **X1 macro backfire halves under 12% Independents.** The 12% who don't fire `BacklashRepulsion` drag the population-mean separation back. Bucket stays *backfire* (still > +0.05) but the magnitude is much closer to Bail 2018's empirical effect size. |
| X2 | −0.029 ± 0.002 | −0.009 ± 0.002 | −0.012 ± 0.001 | −0.013 ± 0.001 | null/null both. |
| X3 | −0.001 ± 0.002 | +0.020 ± 0.003 | −0.013 ± 0.001 | −0.015 ± 0.001 | null/null at default cutoffs; X3 dips into a small *backfire* on Δsep under tighter (0.03) cutoffs in the variant. The cable-zero removes the centripetal partisan-cable pull on partisans but Independents are unaffected (centrist diet); net effect slightly worse on partisan separation. |
| X4 | −0.027 ± 0.002 | −0.009 ± 0.002 | −0.012 ± 0.001 | −0.013 ± 0.001 | null/null. X4 primes 20% of all agents; primed Independents are wasted primes (they have no identity_weight to override). |
| X5 | −0.142 ± 0.002 | −0.129 ± 0.002 | −0.014 ± 0.001 | −0.015 ± 0.001 | partial/null both. Halving partisan centroids affects only partisans; Independents have no party_cue to halve. Slight magnitude drop (12% of agents don't move). |
| X6 | −0.048 ± 0.003 | −0.034 ± 0.002 | +0.242 ± 0.005 | +0.225 ± 0.008 | null/**real** both. Affect warming is partisan-only (Independents have no out-party affect to mute); cooperative ties still form. |
| X7 | −0.027 ± 0.002 | −0.009 ± 0.002 | −0.012 ± 0.001 | −0.013 ± 0.001 | null/null both. X7 still a no-op in pillar context (pillar agents don't seed perception). |

**Story.** Under the 12% Independents variant, X1's macro backfire
drops by ~50% (Bail 2018's R-leaning effect is concentrated in
partisans; Independents have no out-party identity to defend, so 12%
of the population is naturally insulated from cross-cutting backfire).
This is the headline §8d finding: **including Independents in the
population tempers the most prominent "backfire" intervention's macro
effect — without changing its categorical direction.** Other
interventions are largely unchanged on direction/bucket. X6's affect
warming is partisan-only mechanism and stays "real."

### 4.6 4-cell decomposition of the 2025 affect-in-band result (Phase 8e §4)

Per round-2 R2: the Phase 8d "affect 2025 in band" finding is
disambiguated via {Independents on/off} × {augmented engine / 8b
baseline}. Each cell at 15 seeds × 135 ticks.

| Cell | Engine | Independents | 2025 affect |
|---|---|---|---|
| A | 8b baseline | 0.0 | −0.8994 ± 0.0034 |
| B | 8b baseline | 0.12 | −0.8202 ± 0.0066 |
| C | augmented | 0.0 | −0.8780 ± 0.0065 |
| D | augmented (full Phase 8e) | 0.12 | −0.7907 ± 0.0066 |

**Decomposition.** The total improvement (D − A) = +0.109 splits:
- **Compositional shift (B − A): +0.079 — 72.9% of the improvement.** 
  Adding 12% null-affect Independents to the unchanged 8b engine
  arithmetically pulls the population-mean less-negative.
- **Mechanism shift (C − A): +0.021 — 19.7% of the improvement.**
  The 8c §2 positive-going channel + Obama 2008 warmth + identity-
  threat + 8e party-issue-coupling + 8e media_cue together
  contribute roughly a fifth of the affect-in-band finding under
  the 0% Independents condition.
- **Interaction: +0.008 — 7.4%** (small positive — mechanisms
  amplify slightly under the Independent-diluted partisan
  population, or vice versa).

**Honest re-statement of the §8d headline.** "The 2025 affect-in-
band result is *predominantly compositional*. 12% null-affect
Independents in the population pull mean affect arithmetically
less-negative — that alone is ~73% of the improvement. The 8c §2
positive-going + identity-threat + 8e mechanism additions
contribute ~20%. The model's mechanism additions are *real* but
not sufficient to bring affect into band by themselves; the
demographic-composition shift does most of the work. Round-2 R2
flagged this risk; the decomposition confirms it."

### 4.7 X7 historical-arc measurement (Phase 8e §4)

Round-2 R1 asked for X7 to be measured in its meaningful context
(historical arc; the pillar release was null/null because the
pillar doesn't seed perception). Fired at tick 90 (=2010) and tick
105 (=2015) in the historical arc; measured 2025 endpoint vs
unfired baseline at 15 seeds:

| Cell | Δaffect | Δconstraint | Δparty_sep |
|---|---|---|---|
| baseline (no X7) | n/a (-0.791 absolute) | n/a (+0.570) | n/a (+0.569) |
| X7 at 2010 | −0.007 ± 0.010 | +0.013 ± 0.018 | **−0.032 ± 0.007** |
| X7 at 2015 | −0.005 ± 0.010 | +0.006 ± 0.017 | −0.007 ± 0.008 |

**Honest reading.** X7 fired at 2010 (15 years before measurement)
produces a small but measurable reduction in party separation
(Δsep = −0.032). The affect direction is *slightly negative*
(more polarized, by 0.007 — within ~1 SE of zero) because the
perception correction also removes the bias-amplification that had
been accelerating cooling; the post-X7 trajectory has slightly
slower cooling, but the 2016 threat event still fires
post-correction and dominates the remaining 15 years. **The
intervention's effect in the historical context is modest
issue-sorting reduction; the affect channel is unchanged within
noise.** The literature anchors (Levendusky & Malhotra 2016, etc.)
report effects on warmth, not on issue positions; the model
inverts that emphasis under the implemented mechanism.

### 4.4 The story arc

- **One backfire** (X1): the flagship cross-cutting-exposure
  intervention — "show the other side" — *increases* issue sorting
  at the polarized end-state because R1 affect-gated repulsion
  fires reliably (Bail 2018). X3 was the second backfire under
  Phase 7 but the Phase 8c §3 re-implementation (cable-only zeroing
  instead of full media kill) re-blessed it to **null** — R1's
  "category error" diagnosis was correct.
- **Three null** on issue sorting (X2, X4, X6): the platform-
  intervention (X2), the participation-bounded one (X4), and the
  structural-contact one (X6) fail to move issue positions even when
  X6 produces "real" affect warming. F1 anchoring + active PartyPull
  tether agents to their starting side on positions; the affect
  channel is what contact actually moves (Gidron, Adams & Horne
  2020).
- **One partial** (X5): RCV / electoral reform moves issue sorting
  meaningfully (−0.14) but doesn't clear "real" (−0.15). Honest
  reading: the most-promoted institutional reform produces only a
  *partial* effect on issue sorting over a 200-tick release.
- **One "real" on affect** (X6 — Phase 8c §2 re-bless): structural
  shared-life contact under the Pettigrew 2009 *secondary-transfer*
  mechanism (agent-level cooperative-share mute applied to every
  out-party encounter, plus a small positive valence on cooperative
  edges when warmth is above the threshold) produces Δaff = +0.235
  — meaningful warming at the population level. The bucket flipped
  from "backfire" (Phase 7 edge-level mute, Δaff = -0.23) to "real"
  under the §2 mechanism change without any change to the literature-
  anchored `cooperative_mute = 0.5`. This is the literature-faithful
  reading both external reviewers (R1, R2) argued for; the Phase 7
  edge-level reading was conservative.
- **One "real" / "zero real" split on issue sorting.** No
  intervention clears "real" on issue sorting under the current
  library. X5 reaches partial; the others are null or backfire. The
  lay framing: institutional reforms and contact programs move
  *affect* before they move *positions*; position-level sorting is
  much stickier (F1 anchoring + PartyPull keeps agents on their side).

---

## 5. Known limitations

A short, honest list. Each item is also a Phase 8+ follow-up
candidate.

### 5.0 Step-1 evidence re-grade (web/ANES path; `evidence_regrade=True`)

The web/ANES build (`scripts/anes_preset.ANES_FULL_KWARGS`) re-grades the
period shocks to the literature
([`polarization_causal_model.md`](polarization_causal_model.md) §4.3):
elite divergence is attributed to a discrete **Gingrich/1994** inflection
(R-heavy) rather than **Citizens United** (demoted to a non-causal era
marker, with late-period drift preserved via the decade boundary); the
**social-media** affect coupling is demoted to a small contested
accelerant (`affect_weight` terminal ≈0.05 vs 0.30); and an explicit
**identity-alignment** state (Mason mega-identity) now drives out-party
animus. The default path (pillar + Phase 4–9) is bit-identical — every
re-grade consumer reads its no-op value when `evidence_regrade=False`.
These edits are **bit-changing for the shipped trajectory and owe a
Phase-10 re-measure + re-bless** (Step 2 of `docs/execution_roadmap.md`);
the realism preset already sits *within* the ANES envelope but below the
bare `party_sep` anchors (a documented trade for reduced jumpiness), and
"within envelope, contested knobs flagged" — not point-perfect — is the
bar. See `ENGINE_KNOBS.md` §5.8/§7.1.

### 5.1 X3 cable-set sensitivity (Phase 8c §3)

The Phase 8c §3 X3 zeros only MSNBC + Fox News weights (per Fork
3-A default). Under that mechanism, X3 measures Δsep = -0.001
(SE 0.003), Δaff = -0.014 (SE 0.001) — **null on both axes**. The
Phase 7 "X3 backfires" reading was a category error (R1's
diagnosis): the Phase 7 setup zeroed `MediaConsumption.strength`
entirely, bundling broadcast/local's centripetal pull with cable's
centrifugal pull and producing Δsep = +0.27 as a *bundling artifact*.
The §3 rewrite separates the two.

**Open sensitivity item.** The "null" reading depends on the set of
outlets classified as partisan cable (`X3_PARTISAN_CABLE_OUTLET_IDS`
= {MSNBC, Fox News}). Broader definitions — e.g. adding NYT and/or
WSJ as "partisan newspapers" — would tighten the cable-only set
and might shift X3 toward "partial helpful" on issue sorting (the
remaining outlets would lean more centrist). The narrower definition
is Fork 3-A default; sensitivity to the broader definition is Phase
8c §7's cutoff-and-roster sweep.

### 5.1.bis Outlet calibration (historical note)

The pre-§3 sensitivity reading found X3's backfire was robust
across {default, polarized, no-Local-TV} rosters at the strength=0
implementation. That robustness was an artifact of the bundling: any
roster with even a single centrist outlet, killed by `strength=0`,
removed inward-pulling content and let PartyPull drive the camps
apart. Under the §3 cable-only X3, the centrist outlets stay in the
diet at their original weights, so the bundling no longer drives
the result.

### 5.2 X5 centroid-pull magnitude

X5 "Ranked-choice voting" halves the party centroids
(`0.5 * centroid`). Sensitivity sweep (`scripts/phase7_sensitivity.py`):

- **pull = 1.00×** (no change, control): Δsep = −0.02 (null)
- **pull = 0.75×** (mild moderation): Δsep = −0.08 (partial)
- **pull = 0.50×** (default RCV): Δsep = −0.14 (partial — just shy of "real")
- **pull = 0.25×** (drastic moderation): Δsep = −0.20 (**real**)
- **pull = 0.00×** (abolish partisan centroids): Δsep = −0.27 (**real**)

The default 0.5× is the literature-faithful "RCV moderates elites,
doesn't erase party" reading (Hetherington 2001 reverse-direction).
A Phase 8 design choice could add `X5b "Drastic electoral reform"`
at 0.25× as a separate intervention — the sweep confirms it would
honestly land in "real" on issue sorting.

### 5.3 X6 cooperative-mute mechanism — Phase 8c §2 agent-level + §8e fragility

**Phase 8e §5.1 magnitude-sensitivity sweep.** The X6 "real on
affect" headline at Δaff = +0.242 (canonical magnitude 0.05) is
**sensitive to `AffectiveUpdate.coop_positive_magnitude`**. Sweep
at 20 seeds across {0.02, 0.05, 0.08, 0.10}:

| `coop_positive_magnitude` | Δaff at X6 | Affect bucket |
|---|---|---|
| 0.02 | +0.123 ± 0.005 | **partial** |
| 0.05 (canonical) | +0.242 ± 0.005 | **real** |
| 0.08 | +0.401 ± 0.004 | **real** |
| 0.10 | +0.509 ± 0.005 | **real** |

**Honest reading.** X6's affect bucket flips from "real" to
"partial" at magnitude ≤ ~0.04. The canonical 0.05 puts X6 at
"real" with a margin of ~0.09 above the partial/real boundary —
not borderline, but not robust to a halving of the magnitude. The
literature (Pettigrew & Tropp 2006 + Pettigrew 2009) does not pin
this magnitude; 0.05 is an extrapolation (E provenance per Phase
8c D1 audit). A defensible alternative reading: at the most-
conservative magnitude tested (0.02), X6 lands at "partial", not
"real". The intervention library is robust on *direction* (warmth
recovers) but the specific bucket label depends on the calibration
choice.

---

### 5.3.legacy X6 cooperative-mute mechanism — Phase 8c §2 agent-level

**The mechanism that ships (Phase 8c §2).** Each agent carries
`cooperative_share ∈ [0, 1]` (default 0.0). Negative-going valence
on every out-party encounter is muted by
`neg_mute = 1 − cooperative_share * (1 − COOPERATIVE_MUTE)`. A
fully-cooperative agent (`coop_share = 1.0`) gets
`neg_mute = COOPERATIVE_MUTE = 0.5` — Pettigrew & Tropp 2006's
"contact halves prejudice" reading. A non-cooperative agent
(`coop_share = 0.0`) gets `neg_mute = 1.0` (no muting). X6's setup
increments `cooperative_share` for participating agents based on the
ratio of new cooperative ties to total ties.

**On top of the negative mute, a positive-going path.** Cooperative
edges (`network.is_cooperative(i, j) == True`) trigger a small
positive valence (+`coop_positive_magnitude` = +0.05 per encounter)
when the agent's current warmth is at or above
`coop_positive_threshold` = -0.2. Cold-but-not-extreme agents on
cooperative encounters warm; cold-extreme agents stay on the
(muted) negative path — Pettigrew & Tropp 2006: very cold agents
don't warm easily.

**Pillar-fallback discipline.** Agents without `cooperative_share`
read 0.0; pillar S0-S4 has no cooperative edges; positive-going
path never triggers in S0-S4. Pillar trajectory bit-identical to
Phase 8b. Verified at the §11 measurement: pillar 73-test invariant
remains green through the Phase 8c §2 rewrite.

**Phase 6/7 history.** The pre-§2 implementation was *edge-level*:
only encounters across `cooperative=True` edges had their negative
valence attenuated. Under that mechanism X6's affect bucket landed
at *backfire* (Δaff = -0.23). Both external reviewers (R1, R2)
argued the Pettigrew 2009 secondary-transfer reading was more
literature-faithful; Phase 8c §2 implements it and X6 re-blesses to
"real" (Δaff = +0.235) without any change to the literature-anchored
`cooperative_mute = 0.5` value. The Phase 6/7 edge-level reading is
documented for transparency; the §2 reading is what ships.

### 5.4.bis Affect-gate firing-rate diagnostic (Phase 8e §5.3)

Round-2 R1 noted that the Phase 8c D6 affect-gate firing-rate
diagnostic was promised but never reported in §11. Now delivered.

`BacklashRepulsion`'s affect-gate (`affect_threshold = -0.3`) is
the conditional that distinguishes Bail-style backfire (fires on
already-cold agents) from universal cross-cutting repulsion. The
diagnostic reports: what fraction of out-party encounters meet
`warmth < -0.3` at the polarized end-state?

Measured at the pillar S4-end (12 seeds, N=250):

| Phase | Setting | Gate firing rate | Median agent warmth | Cold agents (warmth < -0.3) |
|---|---|---|---|---|
| S4 baseline | (pre-X intervention) | **0.998** | −1.000 | 187/250 (75%) |
| Post-X1 release | "Show other side" | 0.999 | −1.000 | 189/250 |
| Post-X6 release | (after coop-share bump) | (similar) | (mixed) | (varies) |

**Reading.** At S4-end the gate fires on essentially every out-
party encounter because the median partisan agent is already at
warmth = −1.0 (the affect clip floor). The conditional
interpretation of the gate ("R1 backfires only on already-cold
agents") is **not load-bearing in this regime** — almost every
agent is already cold enough to trigger backfire. R2 raised this
in round 1; the diagnostic confirms it. The gate's discriminative
work is at S2/S3 transitions, not at S4-end where the
intervention measurements happen. This does not invalidate the X1
"backfire" bucket (the mechanism IS firing), but it does mean the
"affect-gated" framing is descriptively accurate of the rule shape
rather than empirically discriminating among agents.

The diagnostic is now produced by
`scripts/phase8c_diagnostics.py` (D6 deliverable from Phase 8c §1).

### 5.4.ter Statistical reporting — CI bands + determinism (Phase 8e §5.4 + §5.5)

**95% CI bands.** All Phase 8e measurements report 95% confidence
intervals via the t-distribution at `n=15` (historical) or `n=20`
(pillar). The `abm/calibration_parallel.ci_95` helper provides the
interval. Format: `point ± SE  [95% CI: lo, hi]`.

**Serial-vs-parallel determinism.** `tests/test_parallel_determinism.py`
explicitly runs a small ensemble both serially and via
`run_seeds_parallel`, asserting bit-identical per-seed results at
`atol=0` (true equality, not float-close). The parallel-seed
runner is determinism-verified, not just trusted.

### 5.4 FJ_ALPHA sweep — no-collapse property

`scripts/phase7_sensitivity.py` reports the S4-end position
histogram across `FJ_ALPHA ∈ {0.02, 0.05, 0.08, 0.10}`:

| α | <0.20 | [0.20, 0.50) | ≥0.80 |
|---|---|---|---|
| 0.02 | 0.023 | **0.974** | 0.000 |
| 0.05 (default) | 0.019 | **0.931** | 0.001 |
| 0.08 | 0.014 | 0.836 | 0.002 |
| 0.10 | 0.011 | 0.773 | 0.005 |

The no-collapse property (mid-band fraction > 0.85, extreme fraction
< 0.02) holds at α ∈ {0.02, 0.05}; the band loosens at α=0.08 (still
no-collapse but fewer agents in the mid-band) and looser still at
α=0.10. The default α=0.05 is the comfortable middle.

### 5.5 INVOLUNTARY_PER_AGENT sweep

`scripts/phase7_sensitivity.py` reports t=0 cross-cutting fraction
across `INVOLUNTARY_PER_AGENT ∈ {0, 1, 2, 3}`:

| per_agent | t=0 cross-cutting fraction |
|---|---|
| 0 | 0.193 (cleanly in Mutz band 0.18-0.25) |
| 1 (default) | 0.305 (just above band) |
| 2 | 0.390 (well above band) |
| 3 | 0.456 (well above band) |

Confirms the Phase 4 §13 reading: `per_agent=0` would land *cleanly*
in Mutz's headline 0.20 band, but defeats F3's purpose (no
structural cross-cutting edges that survive rewiring). `per_agent=1`
is the minimum that preserves F3 and lands 0.05 above the band — an
acknowledged but bounded compromise.

### 5.6 Per-agent parameter heterogeneity

F1 ships with per-agent `stubbornness ~ Beta(2, 5)` but every other
agent-level parameter (`epsilon`, FJ `α`, affect `lr`) is
population-uniform. Real populations have heterogeneous receptivity,
elite trust, and identity strength. Adding per-agent jitter on these
parameters is a Phase 8 modelling task; Phase 7 stays global-scalar
to preserve the Phase 4-6 measurement work.

### 5.7 Affect dilution under tie isolation at S4

The Phase 5 §11 measurement showed a non-monotonic affective_polarization
trajectory: S2 ≈ −0.85, S3 ≈ −0.85, S4 ≈ −0.71 (*less* negative).
Cause: S4's tie-rewiring isolates some agents from out-party
neighbours; their affect freezes at the seed value 0.0, diluting the
population mean toward zero. This is documented in the
`affective_polarization` metric's docstring as "S4 sorts so hard that
some agents stop forming animus altogether" — not "S4 reverses the
sign-fix." The honest reading is an honest finding, not a bug.

### 5.8 Two-party / single-country scope

The pillar's two-party structure is fixed; multi-party / proportional-
representation / cross-national dynamics are out of scope. Phase 8
could add an electoral-system parameter and a `multi_party_4` pillar
variant; the cross-national institutional findings (Gidron et al.
2020; McCoy & Somer 2019) would be the calibration anchors.

### 5.9 Timeline is schematic, not literal

The 200 ticks ≈ 67 years mapping at `TICKS_PER_YEAR = 3.0` is a
stylization: the pillar's S0 doesn't claim to be exactly 1955, and
S4 doesn't claim to be exactly 2022. The mapping pins the *rate of
affective cooling* against the ANES headline; it does not claim
calendar-accurate timestamps for specific simulation events.

### 5.10 Phase 9 — per-decade ANES recalibration

Phase 9 replaces the §11 scalar-band-only gate with a **2D
Wasserstein-2 distance against real ANES respondent clouds**, and
recalibrates the historical-arc scenario's knobs against ANES 1986-
2024 data (§3.6). The final landing summary is in
`docs/results/phase9_results.md`; the per-rule and per-knob
inventory is in [`docs/ENGINE_KNOBS.md`](ENGINE_KNOBS.md). This
section records the calibration philosophy and the architectural
boundaries shipped.

**What's being calibrated against.** Per-decade pointclouds
(1000 points each, weighted-sample from ANES) built from
`data/phase9_empirical/derived/respondent_coordinates.csv`. Each
decade's "snapshot" tick is centered on the ANES waves it
represents — 1980 ← tick 21 (≈1987, post-Reagan), 1990 ← 42
(1994), 2000 ← 72 (2004), 2010 ← 102 (2014), 2020 ← 126 (2022) —
so engine and ANES are temporally aligned. Pre-Reagan initial
conditions at tick 0 use party centroids estimated from pre-1986
Voteview / Mass IRT (`PARTY_CENTERS_PRE_REAGAN_ANES`); the engine
drifts to 1986 centroids by tick 21.

**Both metrics now run.** The primary gate is the 2D Wasserstein
(`abm.calibration_phase9.aggregate`); the §11 cell tally is kept
as a secondary band-based regression gate. Both old (Levendusky-
derived) and new (ANES-derived) band sets are scored side-by-side
by `scripts/phase9_anes_score.py` — see
`ANES_PRIMARY_TARGETS` / `ANES_INITIAL_TARGETS_1980` in
`scripts/phase8f_lib.py`. The ANES bands consistently relax the
upper edge of `within_party_sd` and `party_sep` by ~0.10, which
reflects that the original Levendusky / Baldassarri-Gelman bands
were silently compressed below what the ANES cumulative file
actually measures.

**Discipline.** All engine changes outside the pillar are gated
behind a master flag `tier_d_anes_knobs: bool = False` in
`build_engine`. At its default, every code path takes the
pre-Phase-9 branch and the 73 sacred pillar tests + the Phase
4-8 regression tests stay green bit-identically. The pillar
(`abm/pillars/calm_to_camps.py`) was not touched at all during
Phase 9. The ANES recalibration affects only the historical-arc
scenario.

**Architectural moves that landed.** Six classes of change, all
gated:

1. **Per-axis cue σ + Cholesky-correlated noise + cue ρ** —
   `GaussianNoise(sigma_x, sigma_y, rho)`; cue draws use
   `tier_d_cue_correlation`. Lets within-party clouds match the
   ANES diagonal tilt rather than being round.
2. **Per-axis & per-decade-asymmetric ElitDrift** — adds
   `rate_y` and `ELITE_DRIFT_ASYMMETRIC_ANES_SCHEDULE` (Reagan-
   era R-heavy 1980-1990, balanced 1990-2010, D-heavy 2010-
   2020 cult sort). Drives centroid trajectories that match the
   ANES party-centroid path.
3. **Centroid-anchored cohort replacement** — under
   `tier_d_anes_knobs`, `CohortReplacement` draws new agents
   from `N(party_centroid, σ_anchor=0.30)` instead of
   `N(0, σ_cohort)`. Removes the centrist-injection dilution
   that was depressing late-decade `party_sep`.
4. **Identity → ideology coupling** — new rule
   `IdentityToIdeologyPull` (Mason 2018 mega-identity →
   position) wired in at small per-axis strengths
   (`tier_c_identity_pull_x = 0.020`, `tier_c_identity_pull_y =
   0.040`). Inert at default `sx = sy = 0`.
5. **Activist sub-populations on emergence** — pre-existing
   `FactionAnchor` rule (Tier C) re-tuned to Mason 2018 strong-
   partisan tail magnitudes; subpopulations (Tea Party 10%,
   MAGA 13% + 50%, Bernie 8%, DSA 5%) pull toward sub-centroids
   with `faction_anchor_strength=0.10`.
6. **Affect saturation** — `AffectiveUpdate(saturation=1.0)`
   adds a soft cap `max(0, 1 − w²)` on per-encounter step size,
   replacing the hard-clip at ±1 with the Iyengar et al. 2019
   ch. 4 saturation curve. **(Superseded by the affect re-grade
   below: under `evidence_regrade` saturation is retired — it was
   fit to the pre-re-grade, too-cold affect bands.)**

**Affect re-grade (2026-06, `affect-bands-investigation`; gated behind
`evidence_regrade`).** The affect bands were originally hand-scaled off
Iyengar/Finkel figures; re-derived from the raw ANES out-party PARTY
thermometer (VCF0218/0224, partisans, weighted) via the principled
midpoint map `aff=(deg−50)/50` (`scripts/affect_band_builder.py`), the
old bands ran ~0.2 too cold. The engine had been calibrated to those
cold bands and over-produced animus — concave (front-loaded) where the
real thermometer is convex (flat-warm early, collapse late). Diagnosis:
animus was *contact-gated*, so homophilous sorting starved it as the real
drivers accelerated. Fix: warm the 1980 seed to the real thermometer,
soften the contact `affect_lr`, retire saturation, and add a new
contact-independent **`MediatedAnimus`** channel — parasocial animus via
the agent's own identity-alignment × a dated media-exposure ramp
(Mason 2018; Iyengar et al. 2019). The convex shape now *emerges* from
endogenous state rather than a calendar-time rate.
- Mechanism (`MediatedAnimus`, identity+media-driven out-party animus):
  **L** (literature-supported — Mason mega-identity, parasocial/mediated
  animus).
- Magnitudes (seed −0.09, `affect_lr` base 0.003, `MediatedAnimus.lr`
  0.014, media ramp): **N** (the model's calibration, validated 9-seed
  against the grounded bands).

**Result.** At 9 seeds the `anes_full` preset places all five affect
decades + the 1980 IC in the data-grounded affect bands; the ANES-band
§11 gate is **15/24** (the remaining fails are the pre-existing
constraint/within-SD cells, not affect or network). Scorecard:
`docs/results/phase9_anes_score_anes_full.json`. (The earlier "18/24"
figure scored a stale preset that predated the Step-1/affect re-grade —
see `docs/affect_bands_investigation.md`.)

**Intervention re-bless.** The X1–X7 sweeps were re-run on the
re-graded engine (`phase10_measure`, 9 seeds). One public bucket moved:
**X6 affect `real` → `partial`** (Δaff +0.218 → +0.149, decade-dependent:
real at 2020, partial earlier) — the less-polarized re-grounded baseline
leaves a contact lever less animus to undo. All other buckets hold;
`test_phase6` green. See `docs/results/phase10_results.md`.

### 5.11 Web-demo sandbox dials — illustrative, not a finding (2026-06)

The web demo's interactive **sandbox** lets a visitor dial five knobs (five
positions each) and watch the resulting alternate 1980→2025 play out on the
compass. Rather than run the engine in the browser, all 5⁵ = 3,125 combinations
are pre-rendered (`scripts/build_sandbox_data.py`, whole-alternate-history: each
knob-vector is applied as `build_engine` kwargs *from the start*, seed 0) and
served as small static files. The grid's centre cell reproduces the shipped arc
to within decimation noise (sep 1.12 vs 1.13, animus 0.69 vs 0.68, mod 0.20 vs
0.20, align 0.41 vs 0.39 — the sandbox stores 160 of 250 agents at every other
tick).

The five dials were chosen **data-driven** by a metric-span screen
(`scripts/sandbox_knob_screen.py`) so each owns a distinct outcome axis:
`elite` (`tier_d_anes_drift_multiplier` → party separation), `animus`
(`sandbox_animus_mult` → out-party warmth), `identity` (`sandbox_identity_mult`
→ mega-identity stacking), `echo` (`sandbox_rewire_mult` → network modularity),
`openness` (`tier_c_bc_strength` → within-party tightness). The three
`sandbox_*_mult` kwargs are **new multiplier hooks** added to `build_engine`
(see ENGINE_KNOBS §5.9), gated so the default (`×1.0`) path is bit-identical —
the pillar and all Phase 4–10 tests are unaffected.

**Honesty status.** The sandbox is **illustrative only**: its ranges crank the
model *past* its calibration envelope (animus ×8, drift ×8, etc.), so its cells
are **not measured, not re-blessed, and not a finding** — provenance **E**
(mechanisms) / **N** (the chosen ranges). The UI labels it as such. It exists to
let visitors build intuition about which channels move which outcome, not to
predict counterfactual histories. The measured, blessed results remain the
Phase 10 intervention buckets (§4.3, `docs/results/phase10_results.md`).

### 5.12 MHV T0.1 — dead-knob retirement: `PARTY_ASSIGNMENT_K_ANES` + σ_pc fold (2026-06)

The engine-wide knob audit (`docs/internal/engine_knob_audit.md`,
`docs/internal/calibration_interpretation.md` §2.1 — internal audit
notes, kept out of the public repo) found that
`PARTY_ASSIGNMENT_K_ANES` — the ANES-derived party-assignment sigmoid
schedule — was **dead code in the shipped configuration**: under
`tier_d_anes_knobs` party is pre-committed at build (§11.7-D6) and cohort
replacement uses the centroid-anchor draw, so the K-sigmoid never executed
(a 100× swing changed the 58-stat audit battery by exactly 0.00e+00). It
was retired (audit Option A). The actual **sorting-sharpness lever** under
the ANES path is `tier_d_ic_sigma` (σ_ic, the IC width around the party
centroids). The legacy `PARTY_ASSIGNMENT_K` remains live on the non-ANES
path.

In the same change, the near-inert `tier_d_anes_sigma_pc_multiplier`
(×1.6 in the shipped preset) was **folded into**
`PARTY_CUE_SIGMA_HISTORICAL_ANES` (now `0.42*1.6` / `0.57*1.6`,
bit-identical products); the kwarg is deprecated (accepted, warns,
ignored). The within-party-spread lever is `noise_sigma`
(`tier_d_aniso_noise_sigma_x/y`), which dominates that channel (§2.2 of
the calibration-interpretation doc).

**Inertness proof, not assertion:** the full shipped arc (`anes_full`,
seed 0, ticks 0–135) hashes bit-identically before and after the change
(sha256 `17395a6b…`; runner `scripts/audit/t01_bit_identity.py`, which
anyone can re-run — the hash JSONs live in the local-only
`docs/internal/audit/`). No re-bless was needed — by
construction, no pinned value moved. Drift guards:
`tests/test_t01_retire_k.py`. No provenance-table change: no mechanism was
added or removed (the retired constant never acted in the shipped build).

### 5.13 MHV T0.2 — honesty relabels (2026-06)

Three claims are re-graded to match what the engine-wide knob audit
measured (internal audit notes, `docs/internal/engine_knob_audit.md`).
Buckets and mechanisms are unchanged — these are *label* corrections,
per the measure-then-bless discipline.

**1. Identity alignment is ~83% schedule-carried (until the planned
emergent-sorting rebuild lands).** The freeze ablation (all schedules
clamped at their 1980 values, ≥6 seeds) leaves only **17%** of the
1980→2025 `identity_alignment` rise — the rest is carried by
`IDENTITY_SORTING_SCHEDULE` (0.02→0.045), the ×5
`IDENTITY_SORTING_REGRADE_MULTIPLIER`, and the party-issue coupling
schedule. The `IdentitySorting` *mechanism* is endogenous in form and
its qualitative story is Mason 2018 (**L**), but the *trajectory* is a
scheduled input (**N**) and must not be presented as an emergent
finding. (Party separation and affect are different: 0.65 / 0.63
emergent fractions under the same ablation.) Compare the §6 dark-matter
budget once the MHV S2 rebuild lands (target: ≥0.50 emergent).

**2. X1 ("show people the other side") backfire — external grade
LOW/CONTESTED.** The measured in-engine bucket stays **backfire**
(Δsep +0.25…+0.49 depending on variant; §4.3, §4.5). But (a) the
anchoring finding (Bail et al. 2018) has not replicated as a general
phenomenon — counter-attitudinal exposure produced *no* attitudinal
backfire across 3 experiments in Guess & Coppock 2020, and factual-
correction backfire is "elusive" in Wood & Porter 2019; and (b)
in-engine, the backfire is delivered by `BacklashRepulsion`, whose
affect gate (`warmth < −0.3`) fires for **99.8% of partisan agents** in
the polarized regime where interventions are measured (§5.4.bis) — the
mechanism is nearly unconditional there, so the engine cannot exhibit
the conditional, threat-moderated backfire the literature debates. Read
the X1 result as "what follows *if* Bail-2018-style backfire is the
rule," not as settled science.

**3. Cultural-axis elite anchor — MED/N.** The y-axis elite-drift
schedule (`ELITE_DRIFT_SCHEDULE_ANES_Y`, 1.3× the x-rate per decade) is
anchored to ANES *voter*-centroid velocities, not to a legislator
series (DW-NOMINATE dim-2 is not a clean cultural axis pre-2000s). It
is a declared proxy: **MED** evidence grade, **N** provenance on the
magnitude. The x-axis anchor (NOMINATE dim-1) remains L/HIGH.

### 5.14 MHV T0.3 — "events as a brake" attributed (2026-06)

The knob audit's open question — removing the dated events makes 2025
party separation **overshoot 1.13 → 1.61 (+0.48)**, so the event layer
net-*restrains* the arc — is now attributed by a leave-one-out /
add-one-back bisection over all 12 event units (8 seeds, decomposed
schedule validated bit-identical to the shipped one before ablation).

**Finding: the brake is the partisan-media tether plus faction anchors,
98% jointly attributed.** Removing {Fairness Doctrine 1987, Fox News
1996, the four faction-emergence events} together reproduces **98%** of
the overshoot (+0.474 of +0.482, sign-stable 8/8 seeds); adding the same
set to the events-free schedule restores 100%. Mechanism: both media
events do one thing — set `MediaConsumption.strength` (0 → 0.02 at the
1987 repeal, → 0.04 at Fox '96) — and the media pull targets outlet
positions that sit **inward of the party centroids** (the documented
outlet-calibration property the X3 reading also depends on; see the
ENGINE_OVERVIEW provenance row "Media-diet pulls inward"). Activating
partisan-media drift therefore *tethers* the mass inward against
elite-driven separation. The two events are **redundant activators** —
Fox alone restrains +0.46 (95%), the Fairness Doctrine alone +0.26
(54%), but each is nearly inert *marginally* when the other is present —
which is why the additive leave-one-out sum captured only 35% and the
audit's earlier single-mechanism tests (stubbornness bumps, +0.03)
failed to find the cause. Faction anchors contribute a further ~+0.13
independent restraint. All other events are ≈0 on separation (Citizens
United, COVID/Jan6, the 2016 status threat, both exogenous shocks),
confirming the audit's falsification; the affect side of the overshoot
(+0.10 warming) traces mainly to the social-media ramp's animus channel.

**Two honest implications.** (a) The brake rests on the inward-outlet
property, which is **E-tagged** (a calibration artifact of the 2024 ANES
outlet roster, not a literature claim) — so "events restrain the arc" is
a *model* property, not an empirical finding. (b) For MHV S3
(forces-as-inputs): when the media events are re-expressed as
adoption/penetration series, this attribution must be re-checked — the
brake should survive re-expression or the S3 change is wrong (spec
requirement). Full tables:
`docs/internal/audit/events_brake_bisection.{json,md}`.

### 5.15 MHV T0.4 — demo-physics knob adjudication (2026-06)

The three "web-demo jumpiness/realism" knobs that had crept into the
canonical substrate (§5.11 history) were adjudicated per-knob, with user
sign-off, into mechanism-with-provenance vs presentation-side:

**`momentum = 0.4` → relocated to presentation.** The engine's
delta-EMA (added so trajectories read smoothly) is *not* a calibrated
mechanism; it now lives in `scripts/repack_web_demo.py` as a
display-only EMA over published position tracks (β = 0.6, reset at
cohort-replacement splices). The engine kwarg remains accepted
(default 0.0 = off). Opinion-inertia per se is literature-plausible
(Converse 1964; Green, Palmquist & Schickler r ≈ .97 stability), and an
S4 refit may *calibrate* a momentum term against VOTER-panel
within-person autocorrelation — but the 0.4 was tuned for looks, so out
it goes.

**`fj_alpha_scale = 2.8` → kept as mechanism, L/E/N.** The scale was
picked so lifetime big-movers (>1 unit over 45 model-years among
never-replaced agents) fall to 2.4%, against a 1–2% target from panel
stability. Tag: **L** (Friedkin–Johnsen anchoring) / **E** (the
lifetime-mover target) / **N** (the 2.8 value). Honest flag: the
effective α = 0.14 sits outside the §5.4 no-collapse sweep range
(0.02–0.10); extending that sweep is queued at T0.6.

**`tier_d_ic_partisan_x_cap = 0.45` → recalibrated to an ANES-anchored
soft cap.** A data check (this change) showed the hard cap *overcorrects*:
the real ANES 1980–1990 cloud has a wrong-side economic tail — **3.76%**
of Democratic partisans past +0.45 and **1.60%** of Republicans past
−0.45 (weighted, `respondent_coordinates.csv`) — which the hard cap
clipped to exactly 0% (and the untruncated Gaussian over-produced at
~6%/3%). The cap is now *soft*: a beyond-cap draw is kept with analytic
probability `target_rate / P_gauss(beyond)`, reproducing the measured
tail (engine-measured 3.6%/2.0% over 24 seeds). Tag: **L** (the target
rates) / **N** (the thinning operator). Slated for retirement at MHV S2,
whose IC rebuild must reproduce the tail natively.

**Re-bless.** The substrate change (momentum out, soft cap in) was
re-blessed: the ANES §11 scorecard *improved* 15/24 → **20/24** (the
1980 variance and party_sep cells and several later sep/affect cells
moved into band), and the X1–X7 library was re-measured
(`scripts/phase10_measure.py`; see `docs/results/phase10_results.md`
for the post-T0.4 buckets). The web bundle and sandbox grid were
regenerated on the new substrate.

---

## 6. What the model is for

polarlab is a **teaching artifact** for a public, non-expert
audience. It is not a policy-prediction engine. The six-intervention
library (X1–X6) is the primary public-facing payoff: a calibrated,
literature-anchored demonstration that:

1. The most-demanded depolarization interventions (contact, platform
   reform) don't work or backfire at a sorted end-state.
2. Self-help interventions (quitting cable news, dialogue programs)
   are null at the population level even where they help
   participants.
3. Even institutional reform (RCV) produces only partial issue-
   sorting reductions over realistic timescales.
4. Even structural shared-life contact under Allport conditions
   doesn't reverse accumulated animus — it slows further cooling but
   doesn't undo what's already there.

The model's results are **illustrative within a citation envelope**.
Each intervention's bucket is the model's reading; each is grounded
in a published finding, but each is also subject to the limitations
in §5. Anyone using the model to argue for or against a real-world
policy should read §5 first.

---

## Citations (full list, alphabetical)

- Allcott, H., Braghieri, L., Eichmeyer, S., & Gentzkow, M. (2020).
  The welfare effects of social media. *AER* 110:629.
- Allport, G. W. (1954). *The Nature of Prejudice*. Addison-Wesley.
- Bail, C. A. et al. (2018). Exposure to opposing views on social
  media can increase political polarization. *PNAS* 115:9216.
- Brown, J., & Enos, R. (2021). The measurement of partisan
  sorting for 180 million voters. *Nature Human Behaviour*.
- Deffuant, G., Neau, D., Amblard, F., & Weisbuch, G. (2000). Mixing
  beliefs among interacting agents. *Advances in Complex Systems*
  3:87.
- Finkel, E. J. et al. (2020). Political sectarianism in America.
  *Science* 370:533.
- Friedkin, N. E., & Johnsen, E. C. (1999). *Social Influence Networks
  and Opinion Change*.
- Gidron, N., Adams, J., & Horne, W. (2020). *American Affective
  Polarization in Comparative Perspective*. Cambridge University
  Press.
- Guess, A. M. et al. (2023). How do social media feed algorithms
  affect attitudes and behavior in an election campaign? *Science*
  381:398.
- Hegselmann, R., & Krause, U. (2002). Opinion dynamics and bounded
  confidence. *JASSS* 5(3).
- Hetherington, M. J. (2001). Resurgent mass partisanship. *APSR*
  95:619.
- Iyengar, S., Lelkes, Y., Levendusky, M., Malhotra, N., & Westwood,
  S. J. (2019). The origins and consequences of affective
  polarization in the United States. *ARPS* 22:129.
- Kan, U., Porter, M. A., & Mason, J. (2023). An adaptive
  bounded-confidence model of opinion dynamics on networks. *Journal
  of Complex Networks*.
- Levendusky, M. (2013). Why do partisan media polarize viewers?
  *AJPS* 57:611.
- Levendusky, M. (2021). *Our Common Bonds: Using What Americans Share
  to Help Bridge the Partisan Divide*. University of Chicago Press.
- Mason, L. (2018). *Uncivil Agreement: How Politics Became Our
  Identity*. University of Chicago Press.
- McCarty, N., Poole, K. T., & Rosenthal, H. (2006). *Polarized
  America*. MIT Press.
- McCoy, J., & Somer, M. (2019). Toward a theory of pernicious
  polarization. *Annals of the American Academy of Political and
  Social Science*.
- McPherson, M., Smith-Lovin, L., & Cook, J. M. (2001). Birds of a
  feather: Homophily in social networks. *Annual Review of Sociology*
  27:415.
- Mutz, D. C. (2006). *Hearing the Other Side: Deliberative versus
  Participatory Democracy*. Cambridge University Press.
- Mäs, M., & Flache, A. (2013). Differentiation without distancing.
  *PLOS ONE* 8:e74516.
- Nyhan, B. et al. (2023). Like-minded sources on Facebook are
  prevalent but not polarizing. *Nature*.
- Pettigrew, T. F., & Tropp, L. R. (2006). A meta-analytic test of
  intergroup contact theory. *JPSP* 90:751.
- Pettigrew, T. F. (2009). Secondary transfer effects of intergroup
  contact. *Annual Review of Psychology* 60:121.
- Ross Arguedas, A., Robertson, C. T., Fletcher, R., & Nielsen, R. K.
  (2022). *Echo Chambers, Filter Bubbles, and Polarisation: A
  Literature Review*. Reuters Institute.

### Additional anchors (Phase 9–10 + causal model)

*Added to the canonical list during the 2026-06 bookkeeping pass. These were
already in use across the engine, the Phase 9 data spec, the Phase 10
intervention briefs, and `polarization_causal_model.md`, but had not yet been
folded into the alphabetical list above. Full annotation (what each anchors) is
in [`literature.md`](literature.md); a few post-2020 intervention citations
still need venue/year verification — see literature.md §5.*

### MHV T0.2 anchors (belief-system structure + X1 evidence grade, 2026-06)

*DOI-verified at entry; annotations in literature.md §2.8 and §3.*

- Bonica, A. (2014). Mapping the ideological marketplace. *AJPS*
  58(2):367. [+ the DIME dataset, data.stanford.edu/dime — reserved
  for the S3 elite input series.]
- Boutyline, A., & Vaisey, S. (2017). Belief network analysis: A
  relational approach to understanding the structure of attitudes.
  *AJS* 122(5):1371.
- DellaPosta, D. (2020). Pluralistic collapse: The "oil spill" model
  of mass opinion polarization. *ASR* 85(3):507.
- Guess, A., & Coppock, A. (2020). Does counter-attitudinal
  information cause backlash? Results from three large survey
  experiments. *BJPS* 50(4):1497.
- Hare, C. (2022). Constrained citizens? Ideological structure and
  conflict extension in the US electorate, 1980–2016. *BJPS*
  52(4):1602.
- Kozlowski, A. C., & Murphy, J. P. (2021). Issue alignment and
  partisanship in the American public: Revisiting the "partisans
  without constraint" thesis. *Social Science Research* 94:102498.
- Treier, S., & Hillygus, D. S. (2009). The nature of political
  ideology in the contemporary electorate. *POQ* 73(4):679.
- Wood, T., & Porter, E. (2019). The elusive backfire effect: Mass
  attitudes' steadfast factual adherence. *Political Behavior*
  41(1):135.

- Abramowitz, A. I., & Webster, S. (2016). The rise of negative
  partisanship. *Electoral Studies* 41:12.
- Ahler, D. J., & Sood, G. (2018). The parties in our heads:
  Misperceptions about party composition. *Journal of Politics* 80:964.
- Ansolabehere, S., & Schaffner, B. F. (2022). *2020 CCES/CES Common
  Content Codebook*. Harvard Dataverse (CES dataset).
- Baldassarri, D., & Gelman, A. (2008). Partisans without constraint:
  Political polarization and trends in American public opinion. *AJS*
  114(2):408.
- Boxell, L., Gentzkow, M., & Shapiro, J. M. (2017/2021). Cross-cohort
  and cross-national evidence on affective polarization (by-age; period
  effect).
- Carmines, E. G., & Stimson, J. A. (1989). *Issue Evolution: Race and
  the Transformation of American Politics*. Princeton University Press.
- DellaVigna, S., & Kaplan, E. (2007). The Fox News effect. *QJE*
  122:1187.
- Drutman, L. (2020). *Breaking the Two-Party Doom Loop*. Oxford
  University Press.
- Ghitza, Y., Gelman, A., & Auerbach, J. (2023). The great society,
  Reagan's revolution, and generations of presidential voting. *AJPS*
  67:520 (formative-years imprinting).
- Green, D., Palmquist, B., & Schickler, E. (2002). *Partisan Hearts and
  Minds*. Yale University Press (party-ID continuity r ≈ .97).
- Hare, C., Liu, T.-P., & Lupton, R. N. (2018). What ordinary Americans
  (sometimes) think about ideological labels. *Research & Politics* 5(2).
- Iyengar, S., & Westwood, S. J. (2015). Fear and loathing across party
  lines. *AJPS* 59:690.
- Klar, S., & Krupnikov, Y. (2016). *Independent Politics: How American
  Disdain for Parties Leads to Political Inaction*. Cambridge University
  Press.
- Kuziemko, I., & Washington, E. (2018). Why did the Democrats lose the
  South? *AER* 108:2830 (race-driven realignment).
- Levendusky, M. (2009). *The Partisan Sort*. University of Chicago Press.
- Levendusky, M. (2018). Americans, not partisans: Can priming American
  national identity reduce affective polarization? *Journal of Politics*
  80:59.
- Martin, G. J., & Yurukoglu, A. (2017). Bias in cable news. *AER*
  107:2565.
- Mousa, S. (2020). Building social cohesion between Christians and
  Muslims through soccer in post-ISIS Iraq. *Science* 369:866.
- Mutz, D. C. (2018). Status threat, not economic hardship, explains the
  2016 presidential vote. *PNAS* 115:E4330.
- Phillips, J. (2022). Affective polarization: Over time, through the
  generations, and during the lifespan. *Political Behavior* (APC).
- Stoker, L. (2020). Reflections on the APC analysis of affective
  polarization.
- Treier, S., & Hillygus, D. S. (2009). The nature of political ideology
  in the contemporary electorate. *POQ* 73(4):679.
- Voelkel, J. G. et al. (2023/2024). Megastudy / Strengthening Democracy
  Challenge findings (affect ≠ anti-democratic attitudes; dialogue-prime
  ~0.04–0.05 SD on affect). *Venue pending verification.*
- Zaller, J. R. (1992). *The Nature and Origins of Mass Opinion*.
  Cambridge University Press (receive-accept-sample).

**Datasets (calibration anchors):** ANES Time Series Cumulative Data File
(electionstudies.org); ANES out-party feeling thermometer (VCF0218/0224);
DW-NOMINATE / Voteview (voteview.com); GSS Cumulative File (gss.norc.org);
CCES/CES 2020 Common Content (Harvard Dataverse); Democracy Fund Voter Study
Group VOTER Survey; PRRI American Values Atlas. See [`literature.md`](literature.md)
§1 for what each calibrates.
