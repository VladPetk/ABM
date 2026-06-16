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
| 0.02 | 0.048 | **0.944** | 0.000 |
| 0.05 (default) | 0.030 | **0.901** | 0.000 |
| 0.08 | 0.023 | 0.821 | 0.005 |
| 0.10 | 0.019 | 0.756 | 0.011 |
| 0.14 (arc effective) | 0.019 | 0.647 | 0.023 |

The no-collapse property (mid-band fraction > 0.85, extreme fraction
< 0.02) holds at α ∈ {0.02, 0.05}; the band loosens at α=0.08 (still
no-collapse but fewer agents in the mid-band) and looser still at
α=0.10. The default α=0.05 is the comfortable middle.

*MHV T0.6 (2026-06) re-run + extension.* The table above is the
2026-06 re-run (12 seeds); the α ≤ 0.10 rows shifted slightly vs the
original Phase 7 run (engine evolution since, with the pillar
re-blessed along the way) — the default-α no-collapse guard in
`tests/test_phase7.py` still passes. The new **α = 0.14** row is the
historical arc's *effective* α (0.05 × `fj_alpha_scale` 2.8, §5.15):
the strict pillar band does not hold there — mid-band 0.647, extremes
2.3% — but the failure direction is "agents held spread at their FJ
anchors" (center fraction 1.9%, no consensus collapse), which is the
*intended* effect of the lifetime-mover pinning. Flagged honestly: the
arc operates outside the pillar's documented comfortable band.

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

### 5.16 MHV T0.5 — battery v2 + inference hygiene (2026-06)

The identifiability instruments (`scripts/audit/battery.py`,
`phase5_identifiability.py`) were rebuilt after an external math review
found the published "model is sloppy, rank ≈ 1 of 10" headline to be an
artifact of one discrete statistic (a BIC mode count with seed-SD
exactly 0) hitting an unprincipled Monte-Carlo-SD floor. No engine
behavior changed — this is instrument-side only. The hygiene now in
force:

- **Every battery stat is tagged `continuous | discrete`**; Fisher/
  Jacobian analyses consume continuous-only, and discrete stats enter
  ABC/SBI only as soft summaries with real prior-variance.
- **Noise model** in place of the floor: per-stat scale
  σ = √(MC-var over 24 seeds + (1% of the stat's prior-design range)²).
  The target-error term matters because some stats are
  *schedule-deterministic* (the elite-trajectory block) — their MC-SD is
  float noise, and pure-MC standardization lets them carry the entire
  Fisher (reproduced and documented before fixing).
- **A known-dead control parameter** (a no-op by construction) rides the
  full inference path; its posterior shrinkage (0.096) measures the
  pipeline's spurious-contraction floor, and all shrinkages are reported
  net of it.
- **SBC + coverage** (Talts et al. 2018 rank-uniformity, leave-one-out
  over the ABC reference table; `scripts/audit/sbc_harness.py`) gate any
  quoted shrinkage. Current verdict: rejection-ABC is conservative
  (over-coverage), so shrinkages are lower bounds.
- **New stats** future-proofed for the multi-issue substrate:
  participation-ratio dimensionality of the attitude cloud, a
  constraint index and the Baldassarri–Gelman 2008 partisan-vs-issue
  alignment pair (pooled + within-party), and an APC cohort-affect
  decomposition (recent entrants vs 1980 incumbents, from the
  replacement log).

Corrected headline (full tables in the internal analysis): the model is
**moderately sloppy, not degenerate** — local Fisher rank 2 at the
shipped point under the 1% noise model (rank 1→7 as assumed measurement
precision varies, dominated by how precisely the deterministic elite
block is matched), scale-free effect-direction rank ≈ 5 of 8, two
parameters individually identified (the elite-drift gain via the elite
block — its design purpose — and the mega-identity multiplier, net
shrinkages 0.37/0.44), a real mass-channel substitution ridge
(party-pull ↔ identity-pull), and the bounded-confidence strength
uninformative because the shipped value is effectively off (T0.6).

### 5.17 MHV T0.6 — de-saturation attempt: STOP-by-finding (2026-06)

The shipped operating point sits on three saturations (elite centroids
corner-pinned at ±1 from **1996** onward, every seed; 28.5 % of
partisans at the −1 affect floor by 2025; bounded-confidence influence
effectively off at strength 0.015). A pre-registered re-pick attempt
under a user-adopted acceptance gate (ANES scorecard ≥ 18/24, cloud
distance within 15 % of shipped, headline anchors no-regress, plus the
de-saturation goals) **found no passing interior point and stopped
without changing the shipped configuration**. The three structural
findings, each now an evidence-backed requirement on the MHV rebuild
stages rather than a knob change:

1. **The elite corner-pin is not fixable by the drift multiplier.**
   Lowering it makes the DW-NOMINATE shape residual *worse* (2.75 →
   17.3 at 1.0×) and only delays the pin — the drift schedule
   integrates without bound, and the shipped 3.0× scores best precisely
   because early pinning mimics the empirical late deceleration. Fix:
   a data-fed elite position series (NOMINATE dim 1), already planned.
2. **The affect floor trades one-for-one against the current affect
   bands**, which were calibrated against the over-cooled baseline;
   the floor cannot come down until the bands are re-derived from the
   raw ANES thermometer (a validated, not-yet-applied recalibration).
3. **BC can be woken** (ε 0.40, strength 0.03 → ~2.9× effective gain,
   within-party SD essentially unchanged) at a small scorecard cost;
   deferred into the substrate rebuild rather than shipped as a lone
   knob flip.

The de-saturated *diagnostic* point also answered the open
identifiability question from the external math review: the
party-pull ↔ identity-pull substitution ridge persists essentially
unchanged off the corner (cosine 0.67 vs 0.63–0.68 shipped) — the
ridge is **intrinsic to mass-position observables**, not a saturation
artifact, and a new honest trade-off pair (BC strength ↔ noise σ,
cosine ≈ −0.65) appears once BC is awake. Breaking these ridges
requires different facts (the elite block; multi-wave curvature), not
a different operating point.

### 5.18 MHV S2 T2.1 — D-dimensional issue state, dormant substrate (2026-06)

First S2 increment: the engine gains a dimension-parametric issue vector,
wired dormant (nothing reads it yet; the shipped trajectory is bit-identical,
pinned by test).

- **Frozen loadings file** `data/mhv/issue_loadings.json` (generator:
  `scripts/build_issue_loadings.py`): the D=7 ANES battery the S1 pilot
  validated — econ {VCF0803, VCF0809, VCF0839}, cultural-moral {VCF0838,
  VCF0852, VCF0853}, racial {VCF0830} — with the measured 1986-wave item
  correlation matrix (PSD-corrected), party-conditional item means/SDs
  (weighted, VCF0301 with leaners as partisans), and the compass-readout
  definition. Recode recipe is byte-identical to the empirical compass
  pipeline (`scripts/anes_2d_compass.py`), so engine issue space and the
  ANES targets share units exactly. **Wave caveat (E):** 1980 lacks
  VCF0839/0852/0853 entirely; 1986 is the earliest full-coverage wave and
  stands in for the ~1980 baseline. Tags: **L** (items, moments,
  correlations — ANES CDF) / **N** (the 3-block assignment) / **E** (the
  1986→1980 proxy).
- **Kernels** (`abm/core/issues.py`, pure vectorized numpy): party-
  conditional Gaussian-copula-style seeding `v = μ_party + σ_party ⊙ (Lz)`
  clipped to [−1,1]; compass projection x = econ-block mean, y =
  cultural-core mean (the empirical pipeline's exact lens); **RMS distance
  convention** `‖Δv‖·√(2/D)` — at D=2 the factor is exactly 1.0, so the
  N=2 path reproduces the current 2D arithmetic bit-for-bit (invariant I1;
  pinned by `tests/test_t21_issue_state.py`).
- **Measured-by-construction bonuses** (to be pinned when kernels go live
  at T2.2): the seeded projection's within-party SD lands at ~0.32–0.34
  (the ANES wp_sd target the 2D IC undershot at 0.28), and the wrong-side
  economic tail appears **natively** (Dem 6.0% / Rep 2.2% past ±0.45 from
  the 1986 marginals vs the 3.76%/1.60% 1980–90 pooled targets) — the
  retirement path for the §5.15 soft cap.

### 5.19 MHV S2 T2.2 — issue kernels live (2026-06)

Second S2 increment: the D-dimensional state became the *live* position
substrate behind `n_issues` (still opt-in; no shipped preset sets it —
the canonical flip happens at the S2 arc re-pick, together with the BC
re-pick, so there is exactly one re-bless wave).

- **Apply site** (`Engine.step`): in issues mode the position state is
  `attrs["issues"]`; `ideology` is its cached block-means projection,
  recomputed after every apply. Native rules emit `d_attrs["issues"]`;
  legacy rules still emit `d_ideology`, which is **lifted**
  (block-broadcast) onto the items — lift is the exact right-inverse of
  the projection, so a lifted delta moves the compass by exactly that
  delta and legacy emitters keep their semantics.
- **Native D-dim kernels:** `BoundedConfidenceInfluence` (RMS distances
  + targets over full issue vectors, both filter branches),
  `PartyPull` and `MediaConsumption` (2D cues/outlets lifted; every
  issue pulled toward the package position — cue-taking bundles issues,
  the party_pull → constraint catalysis made explicit),
  `GaussianNoise` (axis-level draws lifted — same rng consumption;
  item-level idiosyncratic noise is deliberately deferred to the
  constraint-operator design, where it is part of the bounded-collapse
  dynamics), the FJ anchor pull (native: agents anchor to initial item
  positions), `BacklashRepulsion` (RMS ring + item-space push).
  **Deliberately projection-based:** `AffectiveUpdate` (affect responds
  to compass-level distance; perceptions are stored 2D; the affect
  rebuild is M4, out of MHV scope) and `TieRewiring` (shares its metric
  with the network generator, which is projection-based).
- **Out-of-pipeline writers synced** (I3-flagged either way; S3
  re-expresses them): shock position nudges lift their 2D displacement;
  cohort replacement reseeds a fresh issue vector anchored at the drawn
  2D position (item residuals from the frozen correlation structure,
  recentered so the projection is exact; draws from a dedicated rng).
- **The I1 proof got teeth:** with `n_issues=2` the entire position
  state flows through the live path (native kernels, lift, projection),
  and the arc trajectory is **bit-identical** to the plain 2D run over
  an event-bearing window (`tests/test_t21_issue_state.py`). The D=7
  live path is guarded by `tests/test_t22_issues_live.py`: the
  projection-cache invariant holds at <1e-12 over 45 ticks of the full
  pipeline (events, shocks, replacements), native IC moments in band,
  momentum rejected (retired knob).

### 5.20 MHV S2 T2.3 — emergent constraint: `ConstraintOp` (2026-06)

The S2 core mechanism: `abm/rules/constraint_op.py` productionizes the
S1 pilot's validated operator. For each agent, the rule builds the
**network-local consensus direction** (normalized mean of network
neighbours' issue vectors) and pulls the agent's own vector toward its
projection onto that axis — within-person cross-issue spread collapses
onto a locally shared line. This is the oil-spill mechanism (DellaPosta
2020) operating on the Boutyline–Vaisey belief-network reading;
provenance **L** (mechanism) / **N** (operator form and rate). Two
properties are pinned by permanent tests: the **anti-centroid AST
guard** carried over from the pilot (the executable body references no
party/centroid/corner target — the operator is correlation-inducing,
never position-herding; an agent already on its local axis is a fixed
point however far it sits from the neighbourhood mean), and a
**bounded-collapse tripwire** (at the operating rate over 2× the arc
horizon, within-party effective dimensionality stays > 2 — within-party,
because pooled PR also absorbs partisan alignment, which is PartyPull's
job, not this rule's). The dispersion counterweight is the rule's own
**block-residual noise** (deferred from §5.19): per-item noise with its
block means removed, so it disperses items within blocks without moving
the compass at all (exactly zero at D=2 — I1-safe by construction).

**Emergent mode** (`constraint_rate > 0`, requires `n_issues`): the
scheduled alignment spine is retired on this path — `IdentitySorting`
is not installed, `IDENTITY_SORTING_SCHEDULE` and the ×5 regrade
multiplier are inert, and `PARTY_ISSUE_COUPLING_SCHEDULE` is pinned at
1.0 (the ~83%-schedule-carried trajectory the knob audit flagged).
Defaults 0.0 → strict no-op → every existing path bit-identical.

**Prior-centering sweep** (`scripts/audit/t23_rate_sweep.py`, 28 arc
runs): the headline finding is that emergent mode roughly **reproduces
the legacy pooled-constraint endpoint without the schedules** (pooled
mean |r| 2025 ≈ 0.70–0.74 vs legacy 0.745) — the operator + un-scheduled
cue-taking generate what the hand-drawn spine used to impose. The shape
differs honestly: emergent starts hotter at 1986 (0.38 vs 0.27; the
coupling schedule used to suppress early bundling), which is what S3's
data-fed elite series should restore mechanically (1980s elites were
simply closer together). Prior center for the rate: **0.02** (residual
σ 0.01) — kwarg default stays 0.0 (off); S4 fits the rate against the
B&G/Kozlowski constraint-slope targets.

### 5.21 MHV S2 T2.4 — measured identity alignment (M3-light) (2026-06)

The identity cluster was one latent wearing five hats (the parallel
reviews' construct census): `IdentitySorting` moved the `identities`
vector on a schedule; the `IdentityAlignment` rule relaxed a scalar
projection of that vector; `IdentityToIdeologyPull` pulled positions
toward its mean; `AffectiveUpdate` read the vector again as a dyadic
`identity_term` *and* multiplied animus by the scalar (`align_factor`);
`MediatedAnimus` multiplied by the same scalar once more. T2.4 collapses
this, on the emergent-constraint path, to **exactly two identity
couplings**: **identity→issues** (`IdentityToIdeologyPull`, unchanged)
and **identity→affect** (one quantity — the measured
`identity_alignment` — read by `MediatedAnimus` and `align_factor`
through the same attr name, unchanged consumers).

`identity_alignment` is no longer a relaxed stock; it is a **measured
per-agent readout of current state** (`abm/rules/measured_alignment.py`,
maintained through the ordinary delta pipeline):

> `align = sqrt( clip(sign_p·mean(identities), 0, 1) ×
> clip(p·((v − m)·u), 0, 1) )`

where `u`, `m` are the **frozen 1986 party-gap axis and midpoint** over
the seven issue items (from `data/mhv/issue_loadings.json` — measured
data, never re-fit from the running population; the per-item gap signs
are not uniform, e.g. VCF0838's 1986 gap is inverted, which is why a
naive sign-mean would mis-measure). Geometric mean of identity stacking
× issue-package stacking: the Mason construct is *both* pointing at the
same party pole. Construct **L** (Mason 2018; the measured-not-imposed
discipline is DellaPosta 2020's); the formula itself **N**, pinned
exactly by `tests/test_t24_measured_alignment.py`. The `identities`
vector becomes a slow endowment (changed only by generational
turnover), which retires the weakest within-person claim — survivors'
identities re-sorting on a hand-drawn schedule.

Consequences, measured (`scripts/audit/t24_alignment_trace.py`, 8
seeds): emergent alignment runs **0.21 → 0.31**, carried entirely by
the issue factor (0.41 → 0.63) — real sorting, zero schedule — vs the
legacy spine's 0.21 → 0.41, roughly half of which the freeze test had
attributed to schedule. The measured construct needs its **own
empirical anchor at S4** (the old 0.35–0.45 band was authored against
the relaxed-stock definition and doesn't transfer). Emergent affect
also runs cooler early (coupling pinned at 1.0 from 1980 + the dyadic
identity term retired) — the same hotter-start shape as §5.20, owned by
the S3 data-fed series and the T2.6 re-pick.

Guard rails: `IDENTITY_ALIGNMENT` shocks raise on the emergent path (an
additive bump to a measurement would be silently erased next tick —
shock the underlying identities/issues/affect instead); X1's
`identity_weight` 0.5→0.6 lever is skipped there (it would resurrect
the retired dyadic coupling mid-window; its emergent-mode
re-mechanization is an S4 re-measure item); the sandbox identity dial
has nothing to scale on this path (a measurement is not a force) and is
inert pending the S5 dial re-map. Cohort replacement reseeds arrivals
with the same measured formula; legacy paths are bit-identical
(IdentityAlignment, the seeding formula, and `identity_weight=0.5` all
unchanged when `constraint_rate=0`).

### 5.22 MHV S2 T2.5 — pillar rebuilt on the issues substrate (2026-06)

The calm-to-camps pillar (the no-events composition control — the only
layer where an arc regression bisects into rule-interaction vs
event-handler) is rebuilt on the D=7 issue substrate with the emergent
rule set: `ConstraintOp` enters at stage S2 (where `IdentitySorting`
nominally sat — at `sort_rate=0.0` in every stage bundle, so the legacy
rule had never actually run in the pillar), `MeasuredAlignment` provides
the alignment readout, and `AffectiveUpdate.identity_weight=0.0` matches
the M3-light collapse. The IC stays stylized — uniform 2D compass
positions, party by sign — lifted to items with within-block residuals
from the frozen correlation structure (the cohort-replacement draw
semantics), NOT the arc's empirical party-conditional seeding: the
pillar is a mechanism control, not an empirical build.

**Re-bless outcome (full-suite measurement, 20-seed ensembles).** The
rebuild broke 4 of 281 tests; none was a qualitative break:
- Two phase-4 FJ isolation tests manipulated `state.ideology` and the
  2D `anchor` directly — harness staleness (position state lives in
  `issues`; the FJ anchor is `anchor_issues`). Ported to the issues
  state; **original thresholds pass unchanged** — the FJ physics is
  intact.
- Two scale shifts, answered by re-picking knobs, never thresholds
  (sweep: `scripts/audit/t25_pillar_repick.py`, 9-cell ε×σ_pc grid):
  item-space RMS distances carry residual texture the 2D compass never
  had, starving BC at ε=0.30 (S1 variance ratio 0.922 vs the pinned
  <0.92 — the pillar-side twin of the T0.6 arc finding) → **pillar ε
  0.30→0.35** (ratio ~0.89); and the block-means lens compresses the
  projection's within-party SD (at σ_pc=0.25, S2-end SD_x 0.137, just
  under the [0.14, 0.30] DW-NOMINATE band) → **σ_pc 0.25→0.35**, the
  §11 bless's documented cushion ceiling (restores ~0.151–0.154). ε=0.40
  (the arc's T2.6 re-pick value) was measured and rejected for the
  pillar: it over-compresses wp_sd to the band floor. Pillar parameters
  remain stylized; the arc re-picks its own preset at T2.6.

Everything else — the S2 constraint rise, the S3 media-diet radial
correlation, the S4 exposure-narrowing and the structural-ratchet
release experiment, the affect-outpaces-ideology (Iyengar) claim, the
phase-6/7 pillar intervention buckets, independents, cooperative
contact — passed on the new substrate without touching a threshold.

### 5.23 MHV S2 T2.6 — the canonical flip + freeze gate (2026-06)

**The flip.** The canonical shipped preset (`scripts/anes_preset.py`,
`ANES_FULL_KWARGS`) now builds the emergent engine: `n_issues=7` (the
frozen ANES battery, native item-level IC), `constraint_rate=0.02` /
`constraint_resid_sigma=0.01` (the T2.3 prior center), and the T0.6 BC
wake (`tier_c_bc_epsilon=0.40`, `tier_c_bc_strength=0.03` — the BC
channel was effectively dead at 0.30/0.015). The T0.4 soft wrong-side
tail cap is **retired** from the preset as promised (§5.15→s2_spec §1):
the item-level seeding reproduces wrong-side tails natively (pinned by
`tests/test_t21_issue_state.py`). **MHV S4 T4.6:** the soft-cap kwargs
(`tier_d_ic_partisan_x_cap` / `tier_d_ic_wrongside_tail_target`) + their IC
cap/thinning code were **removed entirely** with the 3 t04 soft-cap tests — the
cap-less draw is bit-identical for every non-cap caller (full suite 304 green).

**Viability re-pick, not calibration** (s2_spec §7;
`scripts/audit/t26_arc_repick.py`, 24 cells × 6 seeds over
constraint_rate × party_pull × animus × idpull). The surface is flat —
the emergent substrate is forgiving — and the **minimal-change cell**
was chosen: every knob other than the flip components keeps its shipped
value (party_pull 0.04, idpull 0.020/0.040, animus ×1.0; the ×0.8
animus cell *under*-cools to −0.63). Chosen-cell endpoints (6 seeds):
sep@2025 0.93, affect@2025 −0.70, pooled |r| 0.73 (legacy 0.745),
measured alignment 0.33, modularity 0.20.

**Freeze gate — the S2 headline.** The phase-2 freeze instrument on the
flipped canonical (8 seeds, `docs/internal/audit/phase2_freeze.json`):
the **alignment emergent fraction is 1.07** (107% of the 1980→2025 rise
survives all-schedules-frozen + no-events) vs **0.17 on the legacy
spine** — the ≥0.50 S2 gate passes decisively; the alignment trajectory
is now carried by rule interaction, not schedules. The
`freeze_identity_sorting` / `freeze_coupling` / `freeze_party_k` rows
read exactly 1.00: the three retired schedules are measured-dead on the
canonical path. Dark-matter budgets (§6 of the MHV spec, adopted at S2
sign-off) measured sep 1.10 / affect 0.87 / alignment 1.07 against
floors 0.60/0.60/0.50 and are now **wired into
`tests/test_dark_matter_budget.py`** (with the pre-registered alignment
ratchet to 0.60 at S4 documented in the file).

**Honest ledger of what is still imposed.** Elite drift carries ~30% of
the sep rise (freeze fraction 0.70) and the social-media ramp ~21% of
the affect rise (0.79) — these are the two residual schedule levers the
S3 typed-inputs caps (≤0.15/≤0.15/≤0.10) exist to retire. Dated events
still *brake* separation on the new substrate (no-events sep fraction
1.60 — the T0.3 finding survives the rebuild). The informational §11
scorecard reads **9/24 ANES cells vs the legacy 20/24** (w2_total
1.018): the dominant systematic miss is `within_party_sd` ≈ 0.24 vs the
voter band [0.27, 0.41] at every decade (the known
bc_strength↔noise_sigma pair from §5.17 is S4's lever), with mid-arc
affect slightly over-cool; 1980 sep and 2020/2025 constraint land
in-band natively. S2's gate is explicitly not ANES quality — **S4 owns
the fit** — but the number is recorded here so the cost of the honest
rebuild is visible, not hidden.

**Consequences for published numbers.** The phase-10 intervention
buckets and the web export were blessed on the pre-flip substrate;
`phase10_results.md` carries a staleness banner until the S4
full-protocol re-measure. The consolidated arc-buckets test measured
exactly one movement on the new substrate — **X6's affect axis crosses
partial→real** (cross-release Δaff +0.172 vs the 0.15 boundary; X6 had
been flagged as sitting on that line) — and the tag was **re-blessed at
user sign-off** (move the tag, not the threshold); every other X-bucket
holds its declared class. The T0.4 soft-cap drift guards convert to
explicit legacy-2D-path guards (user sign-off; kill candidates at the
post-S4 legacy retirement pass). One shock guard re-blessed: the
Obergefell gap-preservation checkpoints at ticks 120/135 get a 0.005
noise tolerance (the strict ≥ was pinning paired butterfly-effect noise
on the 7-item substrate, measured −0.0002 on a 0.59 gap; the onset
check stays strict).

---

### 5.24 MHV S3 — forces as data-fed inputs (M6-lite) (2026-06)

S3 re-expresses the arc's exogenous forces as **typed, data-fed input series**
instead of hand-tuned schedules and ad-hoc state pokes. New module
`abm/pillars/inputs.py`: a provenance-gated `Series` loader (units/source/L-N-E
tag required) + a `DataFedSeries` env-rule with two consumers. Gated behind
`data_fed_elite` / `data_fed_media` (default off → bit-identical); the canonical
`ANES_FULL_KWARGS` flips both **on** at T3.5.

**This is M6-*lite* — data-fed series, NOT feedback-coupled elites.** The
mass→elite feedback literature (Hall 2015 extremist penalty; Bafumi & Herron
2010 leapfrogging; Thomsen 2017 moderate self-selection; Leonard 2021 asymmetric
feedback) is M6-full, out of MHV scope and recorded as a **documented blindspot**
(`docs/model_blindspots.md` §3, §6): the model does not separate a more-extreme,
R-led elite layer from the mass public.

- **Elite channel (T3.2).** `PartyCentroidSeries` sets `env.attrs["parties"][pid]`
  each tick from the measured ANES *voter* party centroids
  (`data/mhv/party_centroid_series.json`; 1986–2024 + a pre-Reagan 1980 anchor)
  and propagates the shift to `party_cue`, replacing the scheduled `EliteDrift`.
  Decision **D-S3-1**: ANES voter centroids, **not DW-NOMINATE** — the compass is
  the mass public, the drift was already voter-calibrated, and the elite/voter
  series carry *opposite* asymmetry (DW-NOMINATE elites R-led ~3:1: R +0.24 / D
  −0.08 1980→2020; ANES voters D-led ~2:1: D econ −0.34 / cult −0.47, R receding
  post-2012). DW-NOMINATE is cited as corroborating elite evidence; the
  mass-elite gap is the blindspot above. Provenance: **L** (ANES measured), the
  1980 anchor **E**.
  - **Why this was a hard requirement (T0.6).** The scheduled `EliteDrift` runs
    the attractor into the domain corners (`[±1, ±1]` by 2014 — physically
    nonsensical, maximally extreme on every issue). Its party_sep of 0.94 is that
    corner-pin artifact. The data-fed series feeds realistic attractors
    (max |coord| 0.44, **no domain bound — accept clause met**) and yields
    party_sep **0.59**. The raw voter-centroid separation (~1.06) matches the
    ANES target, but the FJ-anchored, weakly-pulled (`party_pull=0.04`) population
    lags the attractor. **Closing 0.59 → ~1.04 is an S4 calibration lever**
    (party_pull / fj / the bc↔noise ridge); an honest elite-lead factor (~1.2×
    per leapfrogging) does not close it, so it is not faked at S3. Re-blessed
    down honestly at the T3.5 sign-off (option 1: accept the de-artifacted
    pre-S4 level; S4 closes the gap).
- **Media channel (T3.3).** `MediaPenetrationSeries` writes `env.attrs`
  `media_strength` (= 0.04 × a partisan-media regime curve) and `bc_affect_weight`
  (= 0.094 × Pew social-media adoption) each tick from
  `data/mhv/media_penetration_series.json`; `MediaConsumption` and
  `BoundedConfidenceInfluence` read those slots with a fallback to their own
  value (bit-identical when absent). The weak coefficients **reproduce** the
  discrete step values they replace (FD-1987→0.02 / Fox-1996→0.04; the demoted
  regrade ramp ~0.02/0.04/0.05 @2008/10/12) — a faithful re-expression, **near
  trajectory-neutral** (full-flip affect −0.63 vs −0.69, alignment 0.28 vs 0.33).
  Weak coupling is the **media-paradox blindspot cluster** (Boxell 2017
  age-gradient — which the model cannot reproduce, no age structure: a documented
  limitation; Guess 2023 / Allcott 2024 nulls; Prior 2013 / Guess 2021
  heavy-tailed diets). Internet (Pew, verified 2000–24) is carried for context.
  Provenance: social-media **L**, the FD/Fox regime curve **N/E** (re-expression
  on documented onset dates).
- **Outcome-nudge cleanup (T3.4).** The **Obama-2008 warmth bump** (a +0.05
  one-shot direct write to every agent's out-party affect — an I3 violation) is
  **dropped** (D-S3-2); if a 2008–09 warmth blip is real, S4's thermometer fit
  recovers it. The **Trump-2016 centroid nudge** is retired on the data-fed path
  (the series carries 2016 natively). **I3 is now enforced** by
  `tests/test_i3_no_outcome_writes.py` (AST lint: no direct affect/issues/
  ideology/alignment writes in arc handlers). *Deferred:* the 2016 status-threat
  write (`perceived_threat`, a mechanism *input* to ThreatDecay — not an I3
  outcome variable) stays a direct write; migrating it to the declarative
  `shocks.py` `TargetState.THREAT` channel is deferred (it would move the event
  from the always-on base schedule to the `exogenous_shocks`-gated catalogue,
  changing every legacy non-shock arc test, and risks double-decay with
  ThreatDecay).

**Budget accounting + brake (T3.5).** Data-fed inputs are empirical — the
opposite of dark matter — so they are deliberately **not** frozen in the
`test_dark_matter_budget.py` floors (which still pass: frozen-fraction sep ≈0.81
≥ 0.60). The finer split (`scripts/audit/t35_budget_brake.py`, 6 seeds):
party_sep emergent 0.45 / input-carried 0.36; affect emergent 0.84 / input ~0;
alignment 0.39 / 0.38 — the data-fed elite legitimately carries ~0.36 of sep.
**T0.3 brake re-check:** the events-as-a-brake explanation **re-expressed** — the
cause (the partisan-media tether) moved from the Fox/FD *events* into the
always-on data-fed media *input*, so removing dated events no longer overshoots
sep (full 0.598 vs no-events 0.550). The mechanism survives; its locus moved to
the input where it belongs.

**Tests retired (legacy-path kill, deliberate):**
`test_obama_warmth_event_fires_at_tick_84` (pinned the dropped Obama event).
`test_intervention_library_directions_hold` is **xfail pending the S4 re-measure**
(the de-artifacted lower separation moves weak interventions — X5 ranked-choice,
Δsep ≈ +0.002 — across the null/partial boundary; the X1–X7 bucket re-bless is
S4's, phase10 bannered stale since T2.6).

---

### 5.25 MHV S4 T4.2 — the elite-lead factor (closing the undershoot) (2026-06)

S4's calibration-lite fit (5-knob disciplined set: party_pull, fj_alpha_scale,
constraint_rate, animus_mult, noise_sigma) hit a **STOP-by-finding**
(`docs/internal/audit/t42_undershoot.md`): with the data-fed ANES *voter*
centroids as the `PartyPull` cue attractor, `party_sep` **saturates ~0.81** — even
at party_pull 25× canonical with FJ→0 — and so cannot reach the ANES ~1.11 (2020).
The FJ-anchored, BC-coupled mass tracks its attractor at only ~76% efficiency, so
attractors ~1.06 apart yield a mass-sep ceiling ~0.81. This **refines** the §5.24
S3 estimate (a ~1.2× lead "does not close it"): the gap closes at a larger lead
combined with elevated pull.

**Fix (user-adopted 2026-06-12): `elite_lead_factor` (L).** A *static* declared
factor scaling each data-fed centroid outward from the origin — the `PartyPull`
cue attractor is the **elite** position, which leads the voter mean. This is the
real, documented **mass-elite gap** (the §5.24 blindspot; DW-NOMINATE elite
separation exceeds ANES voter separation), now made an explicit lever rather than
left as a limitation. It is **M6-*lite* compatible**: a static lead, NOT mass→elite
feedback (M6-full stays out of scope). It does **not** reverse D-S3-1: the centroid
*trajectory* (asymmetry, 1994/2016 inflections) stays ANES-voter-derived; L sets
only the cue *amplitude*. `build_engine(elite_lead_factor=...)`, default **1.0 =
voter centroids = bit-identical**; wired into `PartyCentroidSeries`; guarded by
`tests/test_s4_elite_lead.py` (default bit-identity, monotone widening, no domain
bound at L=2.0). With L≈1.5–1.6 + party_pull≈0.4–0.5, sep2020 reaches 1.06–1.07
(in band) with within-party SD in band (~0.35); max centroid coordinate ≈0.64 < 1
(S3 accept clause survives). L is **fit at S4** (6th knob, DW-NOMINATE-anchored
prior ~[1.0, 2.0]; SBC-gated). Provenance: **E** (the lead magnitude is calibrated,
the mechanism — elite-leads-mass — is **L**, DW-NOMINATE / leapfrogging
Bafumi & Herron 2010).

**The fit (T4.3, ABC point applied to `ANES_FULL_KWARGS`).** Full-trajectory NPE/ABC
fit (2500 draws × 2 seeds, `scripts/audit/s4_fit.py`) against the ANES 1980–2025
per-wave bands + grounded affect + the GSS constraint series. Shipped point (the ABC
median; NPE corroborates the *arc* but its median sits at a poorer ridge location):
party_pull **0.297**, fj_alpha_scale **2.195**, constraint_rate **0.0348**,
animus_mult **0.655**, noise_sigma **0.0478**, elite_lead_factor **1.798**
(idpull / bc_strength / drift_mult frozen). **Result: ANES §11 scorecard 18/24 PASS**
(was 9/24 at S2); the de-artifacted party_sep undershoot is closed (2020 sep 0.58→1.08,
in band); affect on-target late. **Identifiability (honest):** the three separation
levers `party_pull ↔ fj_alpha_scale ↔ elite_lead_factor` form a **ridge** (column
cosine up to 0.81) — the *arc* is identified, its decomposition into the three knobs is
not; SBC coverage is ~nominal (0.89–0.96) but rank-uniformity fails on the ridge-coupled
marginals. The shipped point is one defensible location on that ridge. Residual misfits
reported, not chased: early affect ~0.1 too cold (animus at its 0.6 floor — the known
over-cooling), and `wp_sd` slightly off (the bc↔noise structural limit).

**Dark-matter ratchet (T4.3).** The pre-registered identity-alignment floor ratchet
(0.50 → **0.60**) is **applied** in `tests/test_dark_matter_budget.py`. Re-measured
emergent+input fractions on the fitted config (6 seeds, `scripts/audit/s4_budget_check.py`):
party_sep **1.02**, affect **0.85**, identity_alignment **0.975** — all clear their
floors, the alignment fraction comfortably above the new 0.60 bar.

### 5.26 MHV S5 T5.0 — X5 replaced: "Deprogramming & exit programs" (2026-06)

The Phase-10 X5 "Ranked-choice voting" lever was an artifact of the pre-S3
engine: its durable arm halved `tier_d_anes_drift_multiplier`, which scales the
**scheduled** `EliteDrift` rule. S3 moved elite forcing to a data-fed party-
centroid series (`PartyCentroidSeries`), so that rule is never added and the
multiplier is inert (the `_find_rule(engine, "EliteDrift")` lookup returns
`None`). With its durable arm dead, the remaining transient centroid/cue halve
is overwritten each tick by the series, and the residual `FactionAnchor.strength`
halve slightly *raised* separation — so the T4.5 re-measure honestly recorded X5
as a **backfire**. That is a dangling-lever measurement, not a finding about RCV
(whose direct empirics are mostly null anyway).

**Decision (user, MHV S5 T5.0):** rather than re-wire RCV onto an arbitrary
`[T]` magnitude, **replace X5** with **"Deprogramming & exit programs"** — the
library's only *targeted-tail* intervention. Mechanism (`_x5_deprogramming_setup`):
at the intervention tick, a treated fraction (`X5_TREATED_FRACTION = 0.50`) of
**faction-tagged** agents (those the emergence events gave a `faction_center` —
Tea Party '87 / MAGA '105 / Bernie '108 / DSA '114) undergoes **two levers**:
(1) **exit the faction** — clear `faction_center`, so `FactionAnchor` (which
self-gates on a present center) stops tugging them toward the sub-centroid
permanently; (2) **moderate the extremist identity** — scale `identity_strength`
by 0.5, which linearly damps `PartyPull` (it reads `identity_strength` as a pull
modulator). Both levers are live and shipped (`FactionAnchor` /
`faction_anchor_events=True`; `PartyPull`). Provenance **[N]** — deradicalization
program efficacy is modest/contested (Horgan 2009; Koehler 2017; Berger 2018;
Gielen 2019 review); the 50% reach (an optimistic upper bound) + two-lever
magnitude is a design choice within that envelope, not a measured effect size.

**Measured bucket (measure-then-bless, 9 seeds × 4 release decades):** **null /
null** (cross-release mean Δsep −0.0062, Δaff +0.0004). Decade-gated: an exact
no-op at the 1990/2000 releases (no factions have emerged), correctly signed but
sub-threshold where factions exist (Δsep −0.0037 at 2010, −0.0212 at 2020). The
finding is robust across an escalation ladder (exit-only −0.0049 → +identity
−0.0102 → +50% reach −0.0212 at 2020, all still null): **a targeted
counter-extremism program on the organized extreme does not scale to aggregate
separation** — the tail is a small slice of a population whose separation is set
by the broad middle; reaching "partial" would require abandoning the
targeted-tail nature (population-wide identity moderation), a different
intervention. This is the honest, on-message result (the library's thesis that
most interventions barely move the needle). Isolation guards:
`tests/test_isolation_guards.py::test_x5_deprogramming_*`. Replaces the §5.2 RCV
centroid-pull sweep (now legacy).

### 5.27 Realism battery + the 2025 `party_sep` band correction (T-RB1/T-UNDER) (2026-06)

A core realism battery (`scripts/audit/realism_battery.py` →
[`docs/results/realism_report.md`](results/realism_report.md), 9 seeds, **live
per-tick party labels**) scores the shipped config against checks it was *not*
fit to. Verdict: **substantially realistic** — Wasserstein-2 below the
achievable floor; the **held-out GSS instrument** matched (sorting outpaces
constraint); the per-**issue** trajectories *including the racial item* VCF0830
emergently track ANES (gap 0.22→0.73, never fit; `build_anes_item_means.py`);
overlap collapse near-exact to **Pew 2014** (Republicans-more-liberal-than-median-
Democrat 23%→4% vs sim 21%→2.4%); 21/24 on the §11 scorecard. Three documented
gaps: early over-animus, axes over-correlate late (corr 0.75 vs Treier-Hillygus
~0.21), 1980 variance slightly high.

**T-UNDER — the "2025 `party_sep` undershoot" was a band artifact, not a model
miss.** The 9-seed 2025 sep (1.056) sat ~1 SE below the old ANES floor 1.08. But
both ANES sources (`party_centroid_series.json` and the band's own
`polarization_series.csv`) show voter party-separation **peak at 2020 (1.147)
then DECLINE to 2024 (1.056)** — and the engine reproduces the 2024 value almost
exactly. The old 2025 band `(1.08, 1.22)` had been **extrapolated upward past the
last ANES wave (2024)**, its floor exceeding the latest actual measurement.
Corrected to flat-carry the last real decade bucket (1.111 ± 0.07 = `(1.04,
1.18)`; `scripts/phase8f_lib.py` `ANES_PRIMARY_TARGETS[2025]`). **The engine is
unchanged** — provenance **[N]** on the threshold move, justified solely because
the old floor exceeded the data (a defective extrapolation), not to chase the
model. A lift probe (`party_pull`/`elite_lead`) was declined: it only trades the
2020-peak fit for the 2024-endpoint fit at ~net-zero error while worsening the
axis over-correlation. Pinned guards: `tests/test_realism_guards.py` (per-tick-
label discipline, projection parity, no corner-pin). A residual mild **under-
peak** at 2020 (model ~1.06 vs ANES 1.147 — flatter trajectory) is documented,
not closed.

### 5.28 MHV S5 T5.2 — the honesty-budget panel + the input-carried finding (2026-06)

The web Methods page gained an **honesty budget** section: per headline metric,
the freeze-decomposition of the 1980→2025 rise into **emergent** (rules alone,
every external driver frozen at 1980), **empirical-input** (what the data-fed
ANES series adds back), and **hand-drawn residual** (scripted bumps + dated
events), plus the four-cut **holdout scorecard** (transcribed from
[`docs/results/s4_holdout.md`](results/s4_holdout.md), 3/3 PASS). Numbers are
blessed in [`docs/results/honesty_budget.json`](results/honesty_budget.json) —
re-measured on the **fitted shipped config** (`ANES_FULL_KWARGS`, 6 seeds;
`scripts/audit/t35_budget_brake.py`), not the pre-fit S3 reading. Provenance
**[N]** on the presentation; the fractions themselves are measured.

**The finding the panel surfaces (honestly, not buried).** On the fitted config
the 3-way split is: `party_sep` emergent **−0.04 / input 1.06 / residual −0.02**
(grounded 1.02); `affect` emergent **0.87 / input −0.02 / residual 0.15**
(grounded 0.85); `identity_alignment` emergent **0.02 / input 0.95 / residual
0.02** (grounded 0.98). I.e. **party separation and identity alignment are
carried almost entirely by the empirical data-fed party trajectory, not by
emergent rule interaction; only affect is genuinely emergent.** The combined
"grounded" (emergent + empirical-input) totals match the blessed dark-matter
floors exactly (`tests/test_dark_matter_budget.py`: ≥0.60 each, all clear), and
the T0.3 events-brake still survives. This is *by design* of the S3 forces-as-
inputs flip (feeding real data was chosen over hand-drawing the elite curve),
and is defensible under an elite-led reading of mass positional sorting — but it
means the model **tracks** positional sorting rather than **explaining** it.
Registered as a first-class blindspot (#7 in
[`docs/model_blindspots.md`](model_blindspots.md)); an emergence-recovery pass is
the next workstream. **(Superseded by §5.29 — that pass landed: the numbers and
the 3/3 holdout here are the pre-E5 FED state, kept as the motivation record.)**

### 5.29 emergence-recovery — positional sorting made emergent (2026-06)

The blindspot-#7 fix. The canonical config no longer feeds party positions:
positional sorting now **emerges** from an endogenous activist→elite→mass
feedback loop. `scripts/anes_preset.py` keeps the pre-E5 config as
`ANES_FULL_FED_KWARGS` and points the canonical `ANES_FULL_KWARGS` at the new
`ANES_FULL_ENDOGENOUS_KWARGS` (one-line revert).

**Mechanism (`abm/rules/activist_elite.py::ActivistEliteCue`, EnvRule).** Each
tick, each party's elite position is generated from its **activist tail** — the
extreme, intensity-weighted minority along the party's realignment axis — leapt
over by a `elite_gain` factor and bounded by a saturating `tanh` `elite_ceiling`
(the nonlinearity that keeps the positive-feedback loop at a stable, partial
fixed point rather than fizzling or running to the corners). The per-tick elite
shift is propagated into every agent's `party_cue`, which `PartyPull` reads —
structurally mirroring the retired fed `PartyCentroidSeries`, except the cue is
**generated from the mass, not fed from data**. The loop closes: mass → activist
tail → elite → cue → (PartyPull) mass → … , so a small 1980 seed is **amplified**
into the calibrated separation. The amplification **axis** is fixed at the first
tick to the frozen partisan-gap direction `align_u` (the ANES 1986 party-moment
axis, projected to 2D; R = +axis, D = −axis) — anchoring the *direction* as
exogenous historical structure so the loop ignites reliably rather than
bifurcating on the seed; the *magnitude* still emerges. Cohort newcomers enter on
the cohort distribution and sort via the loop (no longer teleported to the fed
centroid — the second answer-feeding channel, also removed). The loop's **pace**
is set by a per-party **activist-mobilization schedule** (low/quiescent 1980 →
R-led accelerating into the 2010s), stepped by the dated events; this is the
exogenous time-structure the loop amplifies (the force-calibration diagnostic
proved a constant-drive loop *cannot* produce the gradual-then-accelerating ANES
shape at any strength — time-structure is genuinely necessary, not a mask).

**Calibration (E4).** Eight knobs — `elite_gain`, `elite_ceiling`, the four
mobilization-schedule shape parameters (`mob_base/peak/backload/asym`), the mass
`uptake` (`tier_c_party_pull_strength`), and `fj_alpha_scale` — were fit by
ABC-rejection (1500 draws × 3 seeds) to the ANES per-decade bands. The adopted
point (`scripts/audit/e4_fit.py`; recorded in `ANES_FULL_ENDOGENOUS_KWARGS`):
gain 1.7689, ceiling 0.8237, mob_base 0.0779 / peak 2.4838 / backload 1.3548 /
asym 0.1880, uptake 0.2532, fj 1.7797. Robust across seeds after the `align_u`
stable-direction fix (no bifurcation).

**Provenance.** Loop mechanism **[L]** — elites track the activist base, not the
median voter (Bawn et al. 2012 *A Theory of Political Parties*; Hacker & Pierson;
Zaller receive-accept-sample); mass cue-taking is per-individual fast but
aggregate-slow (Levendusky *The Partisan Sort*). Functional form (intensity-
weighted tail mean, leapfrog gain, `tanh` ceiling, the mobilization schedule
shape) **[N]**. The eight magnitudes and the compounded arc **[E]**.

**Re-bless cascade (measure-then-bless, all on the endogenous config).**
- **Honesty budget (the WIN, with the honest empirical-input split — E5.8).** The
  fed-POSITION channel is gone: `fed_positions` ~0 for every metric (was ~1.0
  input-carried for sep/identity — the "feed the answer" channel). Freezing the
  whole loop collapses sep to the 1980 seed (`loop_attributable` 1.00 / identity
  0.95), so the loop is the generative mechanism. BUT the panel does **not** claim
  "wholly emergent / 0 empirical input": the loop's pace is set by an ANES-
  calibrated mobilization forcing, so the honest two-way split of each rise is
  **free_flowing** (mechanism with every empirical/external driver removed) vs
  **empirical_input** = `(rise_with − rise_sans)/rise_with` (how much the
  calibrated forcing — mobilization timing + dated events + media — adjusts it).
  Measured (6 seeds, rise-based): `party_sep` free-flowing **0.38** / empirical
  input **0.62**; `identity_alignment` **0.34 / 0.66**; `affect` **0.87 / 0.13**
  (its own mechanism). The empirical input is **timing/intensity, not positions**
  (legitimate forcing) — but it is real and shown, not rounded to zero.
  `honesty_budget.json`, `scripts/audit/t35_budget_brake.py` (the `endogenous_loop`
  freeze handle gives `loop_attributable`; `value`-based empirical input is a
  cross-check field).
- **ANES §11 scorecard** — 17/24 (6 seeds) / 18/24 (9 seeds, realism battery) vs
  FED 18/24: a wash. The endogenous config **fixes** the FED 2025-sep undershoot
  and the 1980 init overshoots but adds a mild **2010 overshoot** (sep 0.96 /
  constraint 0.73). `phase9_anes_score.py`.
- **Realism battery** — 18/24 PASS (9 seeds); 2025 party centroids land within
  ±0.07 of the ANES *voters* having **emerged** there; A6 racial-item trajectory
  still tracks ANES. Costs: W2 0.73→0.92 (still ≈ floor), 1994 centroids lag
  (emergence is behind early), corr(x,y) 0.749→0.776. `realism_report.md`.
- **Intervention library (phase10)** — every bucket **unchanged** (X1 backfire,
  X6 affect real, X5 deprogramming null/null, rest null); robust to the flip.
- **Web** — re-exported (`cc-data.js`, sandbox); the Methods honesty panel + the
  sandbox "Elite extremism" dial re-mapped to the endogenous carriers
  (`elite_gain`+`elite_ceiling` co-scaled, since `elite_lead_factor` is inert).

**The holdout finding (honest limitation).** The four-cut holdout
([`docs/results/e5_holdout.md`](results/e5_holdout.md)) scores **1/3** on the
endogenous config (FED scored 3/3). Cut 3 (statistic) passes; cut 2 (instrument)
fails on the issue-corr slope (1.62× GSS — the axis over-correlation); cut 1
(temporal) fails — refitting on ≤2000 under-predicts the 2010+ acceleration. This
is the honest cost of genuine emergence: the FED config passed cut 1 **trivially**
by feeding the centroid trajectory, whereas the endogenous late-period **timing**
rides the exogenously-calibrated mobilization schedule and is *not* predictable
from early dynamics (consistent with the budget: only ~38% of `party_sep` is the
spontaneous loop floor; ~62% is the fitted forcing). **The model explains the
mechanism but not the timing** — which §5.29.1 shows is a property of mass
polarization at this layer, not a fixable shortcoming. A failed band is a finding,
not a retune (the E4 point is fixed). Two candidate refinements were pressure-tested
and **declined for v1** (`docs/internal/` honesty memos): a *time-evolving* `align_u`
that interpolates the per-wave ANES party-gap direction is a **fed answer** (the axis
rotation *is* the realignment the model should explain) and additionally circular with
the measurement axis — refused; only a *static balanced two-axis* loop is defensible,
and it would address the corr(x,y) over-correlation as a **realism** change (a second
fixed exogenous direction + a second mobilization schedule) that adds fitted forcing
and does **not** fix the timing. Both are deferred, not adopted.

The same forcing-dependence trips the **dark-matter floor** gate
(`tests/test_dark_matter_budget.py`): the all-frozen-no-events *spontaneous*
floor is 0.38 (party_sep) / 0.34 (identity_alignment), below the 0.60 bar
(affect 0.87 clears it). This is **not** silently lowered — the floor's escape
hatch requires a holdout-validated fit, which this is not — so those two metrics
are recorded as documented **xfails** pointing here.

#### 5.29.1 The saturation-ratchet finding (the I4 dark-matter decision: keep, document)

The 38% spontaneous floor reads, at first, like a defect to refine away — for a
model whose headline is *emergence*, the majority of `party_sep` riding a fitted
forcing is the soft spot. We pressure-tested whether it is refinable and concluded
it is a **measurement of a real property, not a modeling shortcut**. The decision
is therefore to **keep the endogenous flip and document this as the result** — *not*
to keep refining the loop toward a bigger emergent number. The reasoning, with the
load-bearing numbers measured offline (positions fixed, real seeded 1980 IC,
canonical endogenous config; `scripts/audit/latent_separation.py`,
[`docs/results/latent_separation.md`](results/latent_separation.md)):

The honest question is whether the 62% is a *framing artifact*: the model routes
all positional sorting through `PartyPull` (agents **move**) and omits endogenous
party **re-sorting** (agents keep their sticky FJ-anchored positions but **re-label**
their party — the empirically central "great sort"). If much separation were already
latent in the 1980 seed, recoverable by re-labeling alone, the forcing would be
absorbing share an emergent re-sorting channel should carry. So we **measured the
ceiling of that latent pool:**

| quantity | party_sep | share of 1980→2025 rise |
|---|---|---|
| engine 1980 baseline (as built) | 0.36 | — (≈ ANES 1980) |
| **optimal re-label** (positions fixed, D/R counts preserved, best direction) | **0.66** ± 0.03 | **+40%** |
| realistic re-label (½–¾ of cross-pressured sort) | 0.60–0.65 | +32–38% |
| spontaneous loop, mobilization ramp OFF | 0.55–0.57 | +21–28% |
| **full arc (with the fitted forcing)** | **1.11** | **+100%** |
| ANES 2025 target | 1.11 | +100% |

The prize **collapses**, three ways:

1. **Re-labeling cannot reach the end-state.** The optimal re-label of the fixed
   1980 distribution tops out at **0.66**, while 2025 is **1.11**: **~60% of the
   1980→2025 rise sits *above* the absolute ceiling** of any re-labeling of the 1980
   positions — almost exactly the **62% fitted-forcing share**. The part re-sorting
   provably *cannot* make (positions more separated than 1980's ever were) is the
   part the forcing makes. Forcing-dependence is therefore **not** a modeling
   shortcut; it is the share of the rise that provably exceeds what re-arranging the
   1980 world can yield. **1980 was genuinely calm** (latent ceiling 0.66 ≪ 1.11), so
   reaching 2025 required real positional/compositional change whose timing is
   externally paced.
2. **The dynamics already extract most of the latent structure.** The spontaneous
   loop (mobilization ramp off) already reaches ~0.55, i.e. **~83–86% of the 0.66
   re-sort ceiling** — so an explicit re-sorting channel's *incremental* headroom over
   what the model already does spontaneously is small (and hard-capped at 0.66).
3. **The latent prize ≈ the emergent floor we already report.** The re-sort ceiling
   as a share of the rise (~37–40%) lands right on the **~38% spontaneous floor** the
   budget quotes: the model's spontaneous emergence already ≈ the latent re-sortable
   separation in the 1980 seed. There is no hidden un-extracted pool for re-sorting to
   convert.

**Direction check (no fed-axis artifact).** The latent separation lies on the
population's **own** principal axis (PC re-label **0.659**) which is essentially
identical to the fed `align_u` re-label (**0.658**) and the plain economic x-axis
(**0.643**); the angle-sweep maximum (0.660 at ~22°) sits between `align_u` (~17°)
and the emergent PC (~26°). The unlockable structure is robustly the **economic
cleavage**, recovered the same way whether by the population's own axis or the fed
axis — we are **not** re-measuring the answer we fed.

**The affect (87%) vs party_sep (38%) asymmetry is a FEATURE, not an artifact.**
Affect has three structural properties positions lack, and they are *empirically*
correct: (i) **no anchor** — affect deltas accumulate with no FJ/stubbornness damping
and no pull to a baseline, while every position-moving rule is multiplied by
`(1−stubbornness)` and FJ-anchored to 1980 (positions are sticky — Converse — *that's
why FJ is there*); (ii) a **monotone cooling floor** — every out-party encounter cools
by at least `baseline`, a one-way ratchet positions have no equivalent of; (iii)
**self-amplification** — animus scales with disagreement × own alignment × threat and
feeds back through affect-weighted tie-rewiring. So affect free-runs and self-organizes
while issue positions are sticky and externally paced. The 87/38 gap is the model
**faithfully reproducing a real asymmetry** (affect polarized autonomously and ran
away; positions sorted slowly under elite/institutional pacing + turnover) — and it is
the strongest single piece of evidence that the 38% is real.

**The honest residual mechanism (realism, not emergence).** Endogenous party
re-sorting *is* a genuine missing mechanism (the mass party label is fixed at build;
`ProtectedPartyRealignment` is gated to spotlight characters only). It is worth
building **later, for realism** — it faithfully renders the great sort and is
FJ-compatible — but it is **not** an emergence-floor lever and must not be sold as
one: it raises the emergent fraction of the *magnitude* not the *timing*, so it
**will not fix the temporal holdout (cut 1)**; its emergence is emergence-*of-sorting*,
not of-extremity; and it is **hard-capped at 0.66 ≪ 1.11**. (The bistable-loop and
time-evolving-axis refinements were separately pressure-tested and rejected as either
empirically unwarranted at the scored mass layer or as fed-answer/forcing-inflating —
see [`docs/internal/`](internal/) memos; the axis decouple is a scoring-only no-op on
this rotation-invariant metric.)

**Headline framing (for the docs and the web honesty panel):** *The model supplies
the mechanism; history supplies the timing. ~38% of the 1980→2025 rise was already
latent in the 1980 electorate and emerges from the loop on its own; the rest required
45 years of real change whose timing no model can author from initial conditions.*
"Explains the mechanism, not the timing" is the **result**, not an open to-do.

**Residuals carried (documented, not hidden):** early over-animus (blindspot #1,
unchanged); axis over-correlation corr(x,y)~0.78 (the single-axis loop's cost);
mild 2010 overshoot + marginally tight late within-party spread; emergence lags
ANES at 1994; late timing not out-of-sample predictable (holdout cut 1 +
dark-matter spontaneous floor).

### 5.30 reality-validation — the common-mode cultural channel (2026-06)

An **independent** validation harness (`validation/`, built from scratch against
**raw** ANES + GSS, deliberately not reusing `tests/` or the arc golden tests)
re-checked the shipped arc against real-world survey data, ten stylized facts
graded year-by-year. It first reproduced the existing ANES derivation **exactly**
(`validation/anes_from_raw.py`, max diff 0.0000 vs `party_centroids.csv`), so the
anchor is trustworthy, then found one real failure concentrated entirely on the
**cultural axis**: the partisan **center of mass** sat ~0.10–0.20 too progressive
in the mid-period (worst ~1996–2000), even though party *separation*, axis
*correlation*, affect *shape*, and within-party *spread* all passed. Real voters
were culturally **traditional** in the 80s/90s (ANES partisan cult +0.10→+0.22;
GSS public traditionalism z +0.2) and liberalized only in the 2010s. The endpoint
(2020s) matched — which is why the endpoint-anchored §11 band gates were blind to
it (and why the four-cut temporal holdout fails). The visible symptom was the
Republican cloud's lower-left tail spilling into the progressive-redistributive
quadrant (model R-in-LL @2000 ≈ 15% vs ANES 8%).

**Diagnosis (mechanism, not parameter).** The engine had a *differential*
(party-sorting) channel but **no common-mode** channel on the cultural axis: the
symmetric endogenous elite loop (§5.29) keeps the two elites' midpoint ≈ 0 and
`PartyPull` drags the mass to track it, so cultural position was effectively
collapsed onto party. The literature's dominant driver of secular cultural change
— **cohort replacement** (~69% per a GSS 1972–2024 age–period decomposition;
Firebaugh & Davis 1988, Brooks & Bolzendahl 2004, Baunach 2012; the remaining
~31% is within-cohort period drift) — could not register: an experiment steepening
the existing (already correctly-signed) cohort gradient moved the center by
**nothing**, because party pull washes out generational signal at the historical
turnover rate.

**The fix (`abm/rules/cultural_common_mode.py`, gated `cultural_common_mode`).**
Each agent carries a `birth_year`; its cultural baseline follows the **measured
ANES birth-cohort gradient** (born 1910s ≈ +0.17 traditional → born 2000s ≈ −0.29
progressive, ≈ −0.044 compass/decade). The society-wide common mode `m(t)` = the
population-mean baseline declines **emergently** as traditional cohorts turn over
(turnover raised to 0.007/tick ≈ 2.1%/yr, demographically realistic; mean-birth
advance ~0.95/yr vs the real ~0.85). It is expressed as a rigid shift of the **7D
issue vector** — `ideology` is re-projected from `issues` every tick (engine.step),
so an `ideology`-only shift would be cosmetic; and since `project(lift([0,d]))≡[0,d]`
the shift is an exact, **sorting-invariant** rigid cultural translation. **Only two
demographic primitives are fed** — the generational gradient (a measured per-cohort
fact) and the turnover rate — never the aggregate trajectory, which emerges.
Provenance: **L** (cohort-replacement mechanism) + **N** (the common-mode
expression). Pre-fix config preserved as `ANES_FULL_ENDOGENOUS_KWARGS`; canonical
is now `ANES_FULL_COMMONMODE_KWARGS`.

**Results (measure-then-bless).** New battery 6 FAIL+1 WARN → **3 FAIL+7 PASS**
(F1 R-traditionalism, F3 econ-separation, F4 cultural-back-loading, F6
axis-correlation all flip to PASS; F0/F2 downgraded CRITICAL→HIGH). Sorting is
**preserved or improved** (party_sep @2000 0.45→0.52, @2024 1.09→1.05; corr @2024
0.77→0.81). The established gates are **neutral**: pytest suite green (the band
guards are too loose to even register the cultural center — itself a finding);
ANES scorecard 17/24 (was 18, the one cell is the orthogonal pre-existing
affect-too-cold issue; issue-constraint cells improved 3/4→4/4); **phase10
intervention buckets unchanged** (X1 backfire / X6 affect-real / X5 null-null /
rest null — the library is robust to the fix). **Honest residual:** the three
remaining HIGHs (F0/F2/F5) are because the battery targets the ANES partisan
center, which carries a mid-90s "+0.22 hump" that **GSS does not corroborate**
(GSS partisan ≈ +0.07 at 1996, which the fix matches almost exactly). Pushing the
common mode higher to "pass" those cells would over-fit a non-robust ANES
item-composition artifact — refused under measure-then-bless. Full trail:
[`validation/REPORT.md`](../validation/REPORT.md) +
[`validation/FIX_INVESTIGATION.md`](../validation/FIX_INVESTIGATION.md).

### 5.31 reality-validation — the common-mode **economic** channel (2026-06)

After §5.30 fixed the cultural axis, the same from-scratch battery exposed the
**identical architecture gap on the economic axis**: only a *differential*
(party-sorting) channel, so the partisan economic **center of mass** is pinned
≈ 0 the whole arc, while ANES rises to ~+0.15 (rightward) in the mid-90s and
declines to ~−0.05 by 2024. Decomposing the 1996 Republican-econ residual (−0.19):
**center-of-mass LEVEL error −0.16 (≈84 %)**, party half-GAP error −0.04 (≈16 %)
— a common-mode level error, not a sorting-gap error. Visible symptom: the econ
half of the same Republican lower-left (progressive-redistributive) tail as §5.30.

**Why a fed forcing here, not emergent.** The cultural common mode is *emergent*
(mean of a measured birth-cohort gradient; cohort replacement is monotone and
generates the monotone cultural decline). The economic tide is **non-monotone**
(rightward to the mid-90s, then leftward), so a monotone demographic primitive
cannot generate it. The mechanism is the **thermostatic policy mood**
(Erikson–MacKuen–Stimson, *The Macro Polity*; Wlezien's thermostat): econ policy
preference moves rightward under the Reagan→Clinton "end of big government" era
(welfare reform / Gingrich 1994–96) and leftward in the post-2008 reaction. This
is an **exogenous forcing** — an input, not the party-sorting answer.

**The fix (`abm/rules/cultural_common_mode.py::CommonModeEconomic`, gated
`economic_common_mode`).** A new env rule snaps the partisan econ common mode to
an exogenous mood-offset curve `economic_mood_offset(year)` each tick, via the same
rigid, **sorting-invariant** issue-vector translation as §5.30 (shared
`rigid_common_mode_shift`; here `project(lift([d,0]))≡[d,0]`, axis 0). The curve is
a **parsimonious thermostatic shape** whose inflection *years* are documented
policy events (1980 Reagan baseline → 1996 welfare-reform peak → post-2008 leftward
reaction) and whose **single fitted scalar** is the amplitude (`ECON_MOOD_AMPLITUDE
= 0.09`, the robust GSS-corroborated mid-90s level). Provenance: **L** (thermostatic
common-mode mechanism) + **N** (curve functional form) + **E** (amplitude/shape
extrapolated). Canonical is now `ANES_FULL_COMMONMODE_ECON_KWARGS`; the pre-econ
config is preserved as `ANES_FULL_COMMONMODE_KWARGS`.

**The honesty crux — corroborated, not replayed.** The real **Stimson Annual Policy
Mood** index was downloaded (`stimson.web.unc.edu` → `Mood5224.xlsx` →
`validation/data/stimson_mood_annual.json`) and used to *corroborate* the curve's
direction (mood conservative into the mid-90s 69→59, liberal through the 2010s
54→66) — **not** as the literal tick-by-tick driver. Fed literally, Stimson injects
a spurious **+0.20 econ spike at 2012** (the Tea-Party *government-spending* mood
swing that economic *self-placement* refused; r≈0.38 contemporaneous, secular
component wrong-signed) — falsified in `validation/exp_econ_commonmode.py`. The
target arc is **triply confirmed** — ANES econ COM, GSS `helppoor`+`eqwlth` (mid-90s
+0.106 → late-2010s −0.057, `validation/gss_econ_check.py`), and Stimson — so
matching it is not ANES over-fitting; but the engine is *told* the mood, it does not
derive it. This is a **weaker honesty claim than §5.30** (a fed forcing), documented
as such (blindspot #9).

**Results (measure-then-bless; the full re-bless cascade ran on the flip).**
Econ-COM error over 1986–2024 cut **64 %** (mean|err| 0.084→0.030); 1996 econ
center −0.018→**+0.088**; the Republican wrong-quadrant (LL) tail improves every
measured year (e.g. 2000 0.120→0.093 = ANES 0.082), regresses none. The **cultural
axis is bit-identical** (the channel is orthogonal) and the **default path is
bit-identical to head** (canonical-arc SHA-256 unchanged with the gate off). Sorting
is preserved/improved (party_sep@135 1.056→1.065). Established gates on the flip:
**phase10 intervention buckets UNCHANGED** (X1 backfire / X6 affect partial→real /
X2–X5,X7 null — library robust to the econ fix too); **ANES §11 scorecard 17/24**
(unchanged — the scorecard grades party_sep/variance/SD/constraint/affect, not the
econ center, and a rigid translation is invariant to all of them); **pytest green**.
The validation battery tags are unchanged (F0/F2/F5 HIGH, F3 MEDIUM): F0/F2 are
*cultural* (untouched) and the F5 residual is the early-period cultural center, not
econ. **Realism battery: 15/24** — the econ channel is realism-**neutral** (15/24
identical with the gate off, same cells/values; the channel does not move a single
realism cell). The drop from the previously-reported 18/24 is **not** the econ flip:
that 18/24 was a stale figure not re-measured on the shipped §5.30 cultural config
(turnover 0.007), whose true realism is 15/24, dominated by the known affect-too-cold
blindspot (#1) plus mild 2010 sep/constraint overshoots — a separate workstream,
refused-not-chased here. Full trail:
[`validation/FIX_INVESTIGATION_ECON.md`](../validation/FIX_INVESTIGATION_ECON.md).

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
3. Even a targeted intervention on the organized extreme
   (deprogramming / exit programs that make half the faction-tagged
   agents exit and moderate) is null at the aggregate — the extreme
   tail is a small slice, and it is decade-gated by when those
   factions emerge.
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
- Talts, S., Betancourt, M., Simpson, D., Vehtari, A., & Gelman, A.
  (2018). Validating Bayesian inference algorithms with
  simulation-based calibration. arXiv:1804.06788.
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
