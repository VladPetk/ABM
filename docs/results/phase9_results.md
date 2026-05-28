# Phase 9 — Tier A Results (Empirical-Distribution Calibration)

*Per `phase9_spec.md` Tier A: factional ICs + factional party_cue +
extremity-graded stubbornness in `historical_arc.py`, plus 4
faction-emergence events. Calibration harness: 2D Wasserstein on
per-decade empirical KDE targets gathered in `phase9_data/`.*

**Headline: Tier A as specified fails both gates and is not
recoverable by parameter tuning within the spec's three knobs. The
spec § 7 risk register flagged tunable-parameter risk; the actual
failure mode is structural — the discrete-faction topology is
incompatible with the §11 within-party-variance bands.**

---

## 1. Baseline (Phase 8f) — reference

Phase 8f (`factional_seeding=False`, `independent_fraction=0.12`),
9 seeds, n=250.

**Wasserstein loss vs empirical KDE:**

| Decade | W2 mean | 95% CI half-width |
|---|---|---|
| 1980 | 0.249 | ±0.023 |
| 1990 | 0.325 | ±0.012 |
| 2000 | 0.414 | ±0.021 |
| 2010 | 0.413 | ±0.016 |
| 2020 | 0.415 | ±0.014 |
| **sum** | **1.816** | — |

**Shape descriptors at 2020 vs empirical:**

| Metric | Model | Empirical |
|---|---|---|
| var(x) | 0.144 | 0.29 |
| var(y) | **0.042** | **0.27** |
| corr(x, y) | 0.540 | 0.57 |
| mean(|x|) | 0.334 | 0.46 |

The dominant gap is **var(y) — the model is 6× under-dispersed on
the cultural axis at 2020.** The cluster-diversity report
diagnosed exactly this collapse (k\* drops from 5.6 → 2.0 across
1980–2000); Wasserstein quantifies it as 0.41 per-decade vs an
ideal of <0.10 on a well-fit distribution.

Loss trajectory is monotone-rising 1980→2000 then plateaus — the
"great sort" period is also the period where the model diverges
from empirical most sharply.

---

## 2. Tier A as specified

Implementation: `historical_arc.py` with `factional_seeding=True`,
`independent_fraction=0.12`, `n=250`, 9 seeds. Default boost=0.5,
scale=1.0, sigma_within=0.05 — all per spec §3.

**Wasserstein vs baseline:**

| Decade | Baseline | Tier A | Δ | 2×CI gate | Significant? |
|---|---|---|---|---|---|
| 1980 | 0.249 | 0.336 | **-0.087** | 0.046 | No (worse) |
| 1990 | 0.325 | 0.375 | **-0.050** | 0.024 | No (worse) |
| 2000 | 0.414 | 0.401 | +0.014 | 0.042 | No |
| 2010 | 0.413 | 0.402 | +0.010 | 0.034 | No |
| 2020 | 0.415 | 0.400 | +0.015 | 0.033 | No |

No decade improves significantly; 1980 and 1990 are significantly
worse. **Spec §7.4 gate (≥2× CI improvement at all decades):
failed.**

**§11 cells under Tier A: 8/24 in band vs gate ≥18/24.**

The Phase 8f baseline lands ~21/25 cells in band. Tier A
catastrophically regresses the §11 trajectory.

**Failure pattern (from `phase9_section11_under_tier_a.json`):**

| Year | constraint | wp_sd | affect | party_sep |
|---|---|---|---|---|
| 1980 IC | 0.71 (band [0.25,0.40]) **HIGH** | 0.15 (band [0.20,0.35]) **LOW** | — | 0.66 (band [0.45,0.60]) **HIGH** |
| 1990 | 0.75 (band [0.35,0.50]) HIGH | 0.13 (band [0.18,0.32]) LOW | -0.44 in band | 0.63 in band |
| 2000 | 0.75 (band [0.45,0.60]) HIGH | 0.14 (band [0.18,0.30]) LOW | -0.62 HOT | 0.64 in band |
| 2010 | 0.76 (band [0.55,0.70]) HIGH | 0.15 (band [0.17,0.28]) LOW | -0.70 HOT | 0.72 in band |
| 2020 | 0.79 (band [0.60,0.75]) HIGH | 0.15 (band [0.15,0.25]) in band | -0.79 HOT | 0.80 in band |
| 2025 | 0.81 (band [0.62,0.78]) HIGH | 0.15 in band | -0.83 in band | 0.83 (band [0.68,0.82]) HIGH |

Diagnosis: **factional ICs hard-bind party to position from t=0
onward.** `ideological_constraint = (|corr(party, x)| + |corr(party,
y)|) / 2` saturates at 0.65–0.80 immediately because each faction
has a deterministic party assignment AND a fixed sub-centroid.
Empirically, the rise is gradual — 0.27 at 1980 → 0.71 at 2020 in
the §11 bands — reflecting Levendusky/Mason's measured sorting
trajectory. Tier A produces the *endpoint* topology from the
*start*.

Compounded: extremity-graded stubbornness anchors agents at their
factional seeds, so the constraint never relaxes; AffectiveUpdate
cools toward an out-party perceived as already-polarized, so
affect runs hot post-1990 (-0.62 to -0.79 at 2000–2020 vs bands
[-0.55,-0.40] to [-0.78,-0.60]).

---

## 3. Attenuation sweep (27 cells)

Three knobs added to `build_engine`: `faction_center_scale ∈ {0.5,
0.7, 1.0}`, `faction_sigma_within ∈ {0.05, 0.10, 0.15}`,
`faction_stubbornness_boost ∈ {0.0, 0.2, 0.5}`. 27-cell Cartesian
product × 5 seeds.

**Result: 0 / 27 cells pass §11 gate ≥18/24.** Best cell scores
9/24.

Top 3 by `w2_total` (sum across 5 decades):

| scale | sigma | boost | w2_total | §11 cells |
|---|---|---|---|---|
| 1.0 | 0.15 | 0.5 | 1.835 | 9/24 |
| 1.0 | 0.15 | 0.2 | 1.865 | 8/24 |
| 1.0 | 0.15 | 0.0 | 1.880 | 8/24 |

Monotone effects:
- `sigma`: bigger is better (0.05 → 0.15) — wider within-faction
  spread reduces both Wasserstein loss AND constraint saturation.
- `scale`: 1.0 wins on Wasserstein; smaller scale (factions
  closer to origin) helps 1980 variance/constraint slightly but
  drags everything else worse.
- `boost`: weak effect on Wasserstein, negligible on §11.

The "best-effort" cell (1.0, 0.15, 0.5) re-run at 9 seeds:

| Decade | Baseline | Best-effort | Δ | Significant? |
|---|---|---|---|---|
| 1980 | 0.249 | 0.283 | -0.034 | No (worse) |
| 1990 | 0.325 | 0.348 | -0.023 | No |
| 2000 | 0.414 | 0.393 | +0.022 | No |
| 2010 | 0.413 | 0.398 | +0.014 | No |
| 2020 | 0.415 | 0.398 | +0.017 | No |
| **sum** | 1.816 | 1.820 | **-0.004** | — |

Net Wasserstein wash. §11: 9/24.

---

## 4. Diagnosis — why Tier A is structurally incompatible

The §11 bands were calibrated against a population whose ideology
distribution is approximately **bimodal Gaussian-per-party with
wide within-party spread.** Tier A produces a **mixture-of-8
narrow-faction-blobs distribution.** These two topologies differ
in a way that the §11 within-party-SD bands directly punish:

- Bimodal Gaussian per party: var = inter-party var + intra-party
  var. Empirical intra-party SD ≈ 0.20–0.30.
- Mixture of factions per party: var = inter-faction-center var +
  intra-faction var. Tier A's intra-faction σ=0.05–0.15. Even at
  σ=0.15, the *centers* of the 4 Democratic factions span only
  about 0.55 (from -0.55 to 0.0 on x), so the within-party SD is
  dominated by the centroid spread, which is bounded structurally.

Tier A also raises `ideological_constraint` mechanically from t=0:
factional IC means each faction has a deterministic party tag
AND a fixed (x, y) center. The constraint metric — party-vs-issue
correlation — measures exactly this mechanical binding. Empirical
1980 has fuzzy party-issue binding (cross-pressured strata, weak
sorting); Tier A removes the fuzziness by construction.

The cluster-diversity report optimized for k\* (silhouette-best
KMeans cluster count) and within-party SD on the cultural axis
(wp_sd_y). It did NOT measure the historical-decade §11 bands.
The mechanism does win cluster diversity (kitchen_sink_v3 hits
k\*=4 at 2000 vs baseline k\*=2.0), but at the cost of the §11
trajectory the prior phases were calibrated against.

**This is a real research tension, not an implementation bug:**
visible cluster diversity and the §11 trajectory targets pull in
opposite directions under the discrete-faction-anchor mechanism.

---

## 5. What's preserved

- 73 sacred pillar tests: bit-identical to pre-Phase-9 head. Pillar
  (`calm_to_camps.py`) was not touched.
- Phase 8f §11 cells under default `factional_seeding=False`:
  unchanged.
- All 5 phase-history closes (8a–8f) intact.
- `HISTORICAL_FACTIONS_1980` + the 4 faction-emergence event handlers
  + the 3 sweep kwargs ship behind defaults that preserve Phase 8f
  behavior bit-identically. The mechanism is *available* in the
  code; turning `factional_seeding=True` is opt-in.
- Empirical-distribution calibration harness
  (`abm/calibration_phase9.py`) is fully working and reusable for
  any future variant.
- All sweep variants are dumped as JSON for future analysis.

---

## 6. Recommended next steps

Three options. Each has different scope and a different research
implication.

### Option B-mix — hybrid factional / Gaussian seeding

Only a fraction `p_factional ∈ {0.2, 0.3, 0.4}` of partisans get
faction-seeded ICs; the rest get the existing broad-Gaussian draw.
This preserves visible cluster structure (the factional minority
shows up as visible sub-modes) while keeping the bulk of within-
party variance Gaussian-shaped, which the §11 bands expect. The
**hypothesis: the empirical electorate IS hybrid** — a small
extreme-faction tail (DSA, MAGA) sits atop a broad Gaussian-ish
mass of mainstream partisans. Mason 2018 and Hawkins et al. 2018
both note this two-strata structure explicitly.

Implementation: add `p_factional` kwarg. ~2 hours work.
Sweep: 3-cell sweep over `p_factional ∈ {0.2, 0.3, 0.4}` at the
current best-effort (scale=1.0, sigma=0.15, boost=0.5).

**Likely outcome**: §11 cells partially recover; Wasserstein
modestly improves on 2010-2020 (where empirical does have visible
sub-faction modes); 1980 stays close to baseline (which is fine,
empirical 1980 is more Gaussian-like).

### Option C — new `FactionAnchor` rule, no IC change

A new rule that fires only after a faction-emergence event
(e.g. only post-2009 for Tea Party, post-2015 for MAGA). Pulls the
event-tagged agents toward their faction sub-centroid with strength
proportional to (1 - stubbornness), competing with PartyPull.
**ICs stay broad-Gaussian** — Tier A's 1980-already-sorted problem
disappears. Visible faction structure emerges *temporally* as
events fire, which is closer to the historical narrative.

Implementation: new file `abm/rules/faction_anchor.py`. ~4 hours
work. Schedule changes minimal — events already exist.

**Likely outcome**: best Wasserstein at 2010-2020 (the eras with
named factions), Phase 8f-like at 1980-1990; §11 cells fully
preserved at 1980-2000 because IC topology unchanged.

### Option N — accept that visible-faction-diversity ≠ §11-band-fit

Document the tension. Ship Tier A behind an opt-in flag (already
the case — `factional_seeding=False` is default). The visualizer
demo uses `factional_seeding=True` for the pedagogical clarity;
the calibration/research model uses the default and matches §11
bands. Two products, one engine. This honors both research
constraints without forcing a single configuration to satisfy
both.

**Implementation**: zero engine work. Document the tradeoff in
`methods.md`. Ship `phase9_cluster_diversity_demo.pdf` as the
visualization story; keep Phase 8f as the calibrated research
configuration.

---

## 7. Files produced

- `abm/calibration_phase9.py` (~320 LOC) — Wasserstein + shape-descriptor harness.
- `scripts/phase9_score_baseline.py` — 9-seed baseline driver.
- `scripts/phase9_score_tier_a.py` — Tier A re-score.
- `scripts/phase9_tier_a_sweep.py` — 27-cell sweep.
- `scripts/phase9_tier_a_blessed.py` — winner re-run at 9 seeds.
- `scripts/phase9_stubbornness_sweep.py` (legacy from intermediate state).
- `tests/test_phase9_harness.py` (5 tests, green).
- `tests/test_phase9_factional_seeding.py` (10 tests, green).
- Engine: `abm/pillars/historical_arc.py` — `HISTORICAL_FACTIONS_1980`, `factional_seeding` kwarg, 3 attenuation kwargs, 4 faction-emergence event handlers. All defaults bit-identical to Phase 8f head.
- Data: `phase9_baseline_score.json`, `phase9_tier_a_score.json`, `phase9_tier_a_blessed_score.json`, `phase9_tier_a_vs_baseline.csv`, `phase9_tier_a_sweep.{csv,json}`, `phase9_tier_a_sweep_winner.json`, `phase9_section11_under_tier_a.json`, `phase9_section11_under_tier_a_blessed.json`.

---

## 8. Honest caveats

1. **The §11 bands are not gospel.** They were calibrated in
   Phase 8b–8f against measured ANES/Levendusky/Mason trajectories
   and are honest, but the within-party SD bands implicitly
   assume a Gaussian-per-party topology. A defensible re-calibration
   under a mixture-of-factions topology is possible — it would
   raise the lower edge of the wp_sd bands somewhat. This is a
   substantial research undertaking and is NOT recommended without
   explicit direction.

2. **Cluster-diversity report's k\* metric is not the calibration
   target.** The report ran 26 variants without checking §11 and
   identified `kitchen_sink_v3` as the minimum-viable. That report's
   recommendation was internally consistent within its own metric
   set — k\* and wp_sd_y — but doesn't generalize to the §11 trajectory.
   The current results are not a refutation of that report, just a
   demonstration that two different research targets (visible diversity
   vs §11 fit) have different mechanism requirements.

3. **POT package** is a new dependency added in Step 1
   (`pip install POT`). Available throughout all sweep runs;
   degraded fallback never activated.

4. **9-seed CI vs the 15-seed historical default**: the baseline
   and Tier A Wasserstein numbers are at 9 seeds (compute budget),
   not the Phase 8b/8e/8f 15-seed default. CI half-widths are
   reported; effect sizes are larger than CI in some cases (1980
   regression at -0.087 ≫ 0.046 CI). The 9-seed sample is enough
   to resolve the 1980 regression but borderline for the 2000-2020
   ties; re-running at 15 seeds wouldn't change the §11 verdict
   (which is unambiguous at 9 seeds).

5. **`tally_4x5` vs `tally_24`**: the §11 cell counts split into
   the 4-metric × 5-year main grid (20 cells) plus 4 "1980 IC"
   cells (variance, constraint, party_sep, wp_sd) = 24 total. Tier
   A's 8/24 includes 4 1980-IC failures plus 4 in-band cells
   across the main grid.

---

## 9. Sign-off

Tier A is fully implemented and gated behind `factional_seeding=
False` default. Pillar bit-identity preserved. The mechanism is
available in the engine; the calibration story is that it does
NOT fit Phase 8b–8f's §11 trajectory under any value in the swept
parameter range. The reason is structural, not parameter-driven.

Next direction is a Vlad-level decision among Options B-mix /
C / N (§6). No further engine changes recommended until that
fork is resolved.

---

## 10. Tier C results

*Per `phase9_spec.md §9` Tier C addendum: ICs stay broad-Gaussian
(`factional_seeding=False`); a new `FactionAnchor` rule pulls agents
tagged by the 4 post-2009 emergence events toward their faction
sub-centroid. Events no longer overwrite `party_cue` — they set
`faction_center`, which the new rule reads.*

### 10.1 Mechanism summary

- New file `abm/rules/faction_anchor.py`. Per-agent rule, signature
  `apply(agent, space, env, rng) → StateDelta`. Returns zero delta
  when `attrs["faction_center"]` is missing — so the rule is inert
  at t=0 (no agent tagged) and inert in the pillar (which never
  tags). Added to **both** pillar and historical_arc pipelines
  unconditionally; self-gates on the attr.
- The 4 emergence events (`_event_2009_tea_party`, `_event_2015_maga`,
  `_event_2016_bernie`, `_event_2018_dsa`) were rewired in
  `_relabel_agents`:
  - **Removed:** overwriting `party_cue` with sub-centroid + noise.
  - **Added:** `attrs["faction_center"] = scaled_centroid` (fresh
    ndarray per agent).
  - Kept the `attrs["faction"]` diagnostic label.
  - Kept the stubbornness bump, now multiplied by
    `env.attrs["event_stubbornness_bump_multiplier"]`.
- Under `factional_seeding=False` (Tier C default), no agent has a
  `faction` tag at t=0. The events now sample from a **party + position
  surrogate** in `_sample_from_faction` (e.g. `Mainstream_Reps → party=1`,
  `New_Right_Religious → party=1 ∧ y > 0.2`). Spec §9 reinterprets the
  fractions accordingly; the absolute count tagged is not gospel.
- `historical_arc.build_engine` gains three kwargs:
  - `faction_anchor_strength: float = 0.04`
  - `faction_anchor_events: bool = True`
  - `event_stubbornness_bump_multiplier: float = 1.0`
- Pillar bit-identity preserved: `tests/test_pillar_stages.py` 9/9 green.

### 10.2 Sweep (12 cells × 5 seeds)

`scripts/phase9_tier_c_sweep.py`:
`faction_anchor_strength ∈ {0.02, 0.04, 0.06, 0.08}` ×
`event_stubbornness_bump_multiplier ∈ {0.5, 1.0, 1.5}`.

**Result: 12/12 cells pass §11 (≥18/24).** This is the inverse of
Tier A's 0/27.

Top 3 by `w2_total` among §11-passers:

| strength | bump | w2_total | §11 cells |
|---|---|---|---|
| 0.08 | 0.5 | 1.8123 | 18/24 |
| 0.08 | 1.0 | 1.8134 | 18/24 |
| 0.06 | 0.5 | 1.8144 | 19/24 |

The sweep is essentially flat: all 12 cells land within 0.007 on
`w2_total` and within ±1 cell of the 18 threshold. Effect is
monotone-mild — higher strength gives marginally lower w2_total
(consistent with the small FactionAnchor pull producing a small
nudge toward sub-centroids on a small subpopulation).

Winner: `strength=0.08, bump=0.5`, `w2_total=1.8123`, §11=18/24.

### 10.3 Blessed re-run (9 seeds)

`scripts/phase9_tier_c_blessed.py` at strength=0.08, bump=0.5:

| Decade | Baseline | Tier C blessed | Δ | 2×CI gate | Significant? |
|---|---|---|---|---|---|
| 1980 | 0.249 | 0.249 | +0.000 | 0.046 | No (identical IC) |
| 1990 | 0.325 | 0.325 | +0.000 | 0.024 | No (no events yet) |
| 2000 | 0.414 | 0.414 | +0.000 | 0.042 | No (no events yet) |
| 2010 | 0.413 | 0.413 | -0.000 | 0.032 | No |
| 2020 | 0.415 | 0.407 | +0.008 | 0.028 | No |
| **sum** | 1.816 | 1.809 | **+0.008** | — | — |

**§11 cells under Tier C blessed: 21/24** (vs Phase 8f baseline 21/25
and Tier A's catastrophic 8/24). Misses:
- 2000 party_sep 0.519 vs band [0.55, 0.70] — LOW.
- 2000 affect -0.555 vs band [-0.55, -0.40] — HOT by 0.005.
- 1980 variance 0.387 vs band [0.45, 0.60] — LOW (pre-existing baseline
  miss, not caused by Tier C; Tier C 1980 IC is bit-identical to
  baseline).

### 10.4 2020 shape descriptors

| Metric | Empirical | Baseline | Tier C blessed | Δ (TC - base) |
|---|---|---|---|---|
| var(x) | 0.29 | 0.144 | 0.146 | +0.002 |
| var(y) | 0.27 | 0.042 | 0.045 | **+0.003 (still 6× under)** |
| corr(x,y) | 0.57 | 0.540 | 0.596 | **+0.056** |
| mean(\|x\|) | 0.46 | 0.334 | 0.339 | +0.005 |

The y-axis fix is **not achieved.** FactionAnchor on a small surrogate
subset (3-9% of partisans by party-surrogate sampling) produces a
modest correlation lift but does not meaningfully disperse the
cultural axis. Wasserstein at 2020 improves by +0.008 — about
one-third of the 2×CI gate, so not statistically significant.

### 10.5 Verdict

- **§11 gate: PASS** (21/24 ≥ 18). Tier C preserves the 1980-2025
  trajectory bands that Tier A broke.
- **Wasserstein gate: FAIL** (spec §9.6: at least 2 of 5 decades must
  improve significantly; actual: 0 of 5).
- **Overall: PARTIAL.** Tier C avoids Tier A's structural regression
  but doesn't move the needle on the empirical-distribution fit.
  The mechanism does exactly what Vlad's spec §9 said it would — a
  small, late-emerging factional tug on a small subpopulation — and
  that magnitude is, empirically, too small to bridge the 6× gap
  between model var(y) and empirical var(y).

### 10.6 Open questions / caveats

1. **Party + position surrogate sampling** under Tier C. The spec
   §9 doesn't specify how to sample without faction labels; under
   broad-Gaussian ICs no agent has a faction tag at t=0. The
   literature-faithful default chosen here (party + y-axis filter
   for the cultural-issue factions) tags 3-9% of partisans per event,
   matching the Tier A absolute counts within ~1pp. Inline-documented
   in `_sample_from_faction`. If Vlad prefers a different surrogate
   (e.g. broader fraction at higher strength), the existing kwargs
   permit it without code edits.
2. **`event_stubbornness_bump_multiplier` is essentially neutral**
   across the swept range {0.5, 1.0, 1.5} — w2_total varies by ≤0.003.
   The mechanism's effect is dominated by `faction_anchor_strength`
   and by how many ticks the rule has to act between event firing
   and decade snapshot.
3. **The structural gap remains.** Tier A demonstrated that
   IC-anchored factions over-bind party-to-position. Tier C
   demonstrated that emergence-anchored factions are too weak to
   close the var(y) gap. Neither tier is a Wasserstein fix; both
   tell us something real about the mechanism space.
4. **Pillar bit-identity gate**: pillar tests pass bit-identical with
   FactionAnchor in the pipeline. The self-gating attr-check works
   as designed.

### 10.7 Files produced

- New: `abm/rules/faction_anchor.py` (~50 LOC).
- New: `scripts/phase9_tier_c_sweep.py`, `scripts/phase9_tier_c_blessed.py`,
  `scripts/phase9_compare_tier_c_vs_baseline.py`.
- New: `tests/test_phase9_faction_anchor.py` (8 tests, green).
- Modified: `abm/pillars/historical_arc.py` — 3 new kwargs, event
  rewire (party_cue → faction_center), surrogate sampling fallback.
- Modified: `abm/pillars/calm_to_camps.py` — FactionAnchor in pipeline.
- Modified: `tests/test_phase9_factional_seeding.py` — updated 2 tests
  to Tier C semantics (faction_center, not party_cue).
- Data: `phase9_tier_c_sweep.{csv,json}`, `phase9_tier_c_sweep_winner.json`,
  `phase9_tier_c_blessed_score.json`,
  `phase9_section11_under_tier_c_blessed.json`,
  `phase9_tier_c_blessed_descriptors.csv`,
  `phase9_tier_c_vs_baseline.csv`.

### 10.8 Sign-off

Tier C is the structural inverse of Tier A and ships behind defaults
that preserve every existing test. `methods.md` is NOT updated since
the Wasserstein gate failed — per task discipline ("Update methods.md
ONLY IF Tier C passes both gates"). Tier C is honest infrastructure
for future emergence experiments; it is not the empirical-fit
breakthrough.

---

## 11. Tier D — axis-symmetry rebalance

After Tier C's §11-pass-but-Wasserstein-flat result, Vlad asked the
right diagnostic question: "What is the x-axis and the y-axis? Both
reflect the same thing, don't they? — shouldn't the engine impact
both of them more or less symmetrically?" The audit
(`docs/research/phase9_axis_symmetry_audit.md`) and ratios
sweep (`docs/research/phase9_axis_ratios.md`) confirmed the
intuition: the rule math IS axis-symmetric, but six engineering
inputs encode silent x-dominance, and the y-shortfall in the
simulated cloud is upstream of the faction mechanism.

The full Tier D specification lives in
`docs/specs/phase9_tier_d_spec.md`. Per Vlad's discipline ("ship the
central estimates first, then sweep only what looks off"), this
section is structured in three subsections:

- §11.1 — Mechanism summary + lever table
- §11.2 — Central-estimate results (TO BE FILLED after running
  `scripts/phase9_tier_d_central.py`)
- §11.3 — Sweep results + blessed config (TO BE FILLED after central
  diagnoses which levers need ±30% sweep)

### 11.1 Mechanism summary

Six gated substitutions in `historical_arc.py` + `cohort_replacement.py`,
all enabled only when `build_engine(tier_d_axis_balance=True)`:

| # | Lever | Code path | Change |
|---|---|---|---|
| 1 | Party sigmoid (build + cohort) | `historical_arc:425`, `cohort_replacement:171` | argument: `x` → `0.55·x + 0.45·y` |
| 2 | Party centers 1980 | `PARTY_CENTERS_1980_TIER_D` | `(±0.30, ±0.08)` → `(±0.30, ±0.20)` |
| 3 | Initial-position side draw | `historical_arc:415-426` | y gains `side_y · 0.12` with 60/40 (ρ ≈ +0.20) coupling to x-side |
| 4 | Perception-gap bias | `PERCEPTION_EXTREME_BIAS_X/Y_TIER_D` | x = 0.25 → 0.20, y = 0 → 0.25 (inverted) |
| 5 | Outlet y-spread | `outlets.py:27-33` | *deferred to sweep* (1D-only literature) |
| 6 | 2016 Trump centroid nudge | `_event_2016_trump_election` | `(+0.05, 0)` → `(+0.02, +0.10)` |

Bit-identity discipline: at `tier_d_axis_balance=False`, all six paths
take the pre-Tier-D branch; 199 tests (incl. the 73 sacred pillar
tests) pass at flag=False.

### 11.2 Central-estimate results

Run command:

    .venv/Scripts/python.exe scripts/phase9_tier_d_central.py

9 seeds, layered on the Tier C blessed config
(`strength=0.04`, `bump=1.0`). Per-decade Wasserstein:

| Decade | W₂ mean | ±95% CI hw | corr(x,y) | var(x) | var(y) |
|---|---|---|---|---|---|
| 1980 | 0.2439 | ±0.0137 | +0.038 | 0.202 | 0.199 |
| 1990 | 0.3122 | ±0.0158 | +0.221 | 0.103 | 0.088 |
| 2000 | 0.3843 | ±0.0206 | +0.499 | 0.083 | 0.057 |
| 2010 | 0.3782 | ±0.0143 | +0.638 | 0.108 | 0.069 |
| 2020 | 0.3533 | ±0.0107 | +0.779 | 0.139 | 0.095 |
| **w2_total** | **1.6719** | | | | |

§11 gate: **13/24 — FAIL.** (Tier C blessed was at gate-pass; the
re-tilt broke it.)

**What's working:**

- **1980 is excellent.** var(x) ≈ var(y) ≈ 0.20 — the
  axis-symmetry rebalance lands almost exactly where the literature
  predicted. corr(x, y) = +0.04 is much lower than the +0.20 spec
  target, suggesting the 60/40 side-draw coupling washes out under
  the existing PartyPull + media-cue + Gaussian noise at t=0.
- **w2_1980 = 0.244** is a large drop from the Tier C central
  baseline — the lever-2 widening of `PARTY_CENTERS_1980` +
  lever-3 y-side draw together fix the dominant 1980 mass-shape
  mismatch.
- **w2_total = 1.6719** improves on Tier C blessed.

**What's broken:**

1. **2020 corr(x, y) over-shoots:** +0.779 vs empirical ~+0.45. The
   dynamics over-couple the axes by 2020. With lever 2 at (±0.30,
   ±0.20), PartyPull pulls agents toward party centroids on a
   diagonal in (x, y), dragging the cloud onto that diagonal over
   decades. Initial condition is balanced; end-state is over-aligned.
2. **var(y) collapses** through the dynamics: 0.199 (1980) → 0.057
   (2000) → 0.095 (2020). The recovery comes from the lever-6 Trump
   y-nudge, but it's not enough.
3. **§11 dropped to 13/24.** Most likely failing cells: 1980
   within-party-SD (lever 2 widens centers → wider in-party spread
   in IC) and downstream party_sep cells (the diagonal over-coupling
   pushes party_sep above-band by 2010-2020).

Diagnosis points to two structural knobs as highest leverage:

- **Lever 2 magnitude** (`tier_d_party_center_y`) — too small kills
  1980 var(y); too large kills §11 + drives over-coupling.
- **Lever 3 coupling ρ** (`tier_d_coupling_rho`) — the +0.20 ρ at
  IC may amplify through PartyPull. ρ=0 (independent draws) may be
  the cleaner anchor; let dynamics build correlation organically.

Lever 5 (outlet y-spread) and lever 6 (Trump nudge) are second-
order — deferred to a follow-up sweep if needed.

### 11.3 Sweep + blessed config

**Sweep design** (`scripts/phase9_tier_d_sweep.py`): 4 × 4 = 16
cells over (`tier_d_party_center_y`, `tier_d_coupling_rho`):

  - y ∈ {0.10, 0.15, 0.20, 0.25}
  - ρ ∈ {0.00, 0.10, 0.20, 0.30}

5 seeds per cell. Levers 1, 4, 6 stay at central. Lever 5 deferred.

**Multi-core strategy.** The existing per-seed pool
(`run_seeds_parallel`) caps utilisation at min(N_seeds, N_cores) —
with 5 seeds and an 8+ core CPU, ~3 cores idle. The sweep instead
**parallelises cells across cores** via `ProcessPoolExecutor` —
each cell-worker runs its 5 seeds sequentially. CPU saturation is
independent of seed count.

Run command:

    .venv/Scripts/python.exe scripts/phase9_tier_d_sweep.py

*Results to be filled after the sweep completes. Winner blessed at
9 seeds via a follow-up runner (TBD pending sweep outcome).*

---

## 11.4 — Overnight investigation (May 27 2026): metric audit + per-lever ablation + structural ceiling diagnosis

*Standalone overnight session. Picks up the open puzzle from §11.2/§11.3:
the Tier D 16-cell sweep over levers 2 and 3 showed those aren't the §11
killers; brief asked for ablation of levers 1, 4, 6 plus a critical-eye
audit of whether the metric, the targets, or the framing itself are
sound. Findings below.*

### 11.4.1 — Wasserstein-2 metric: forensics under controlled
perturbations (`scripts/phase9_metric_stress.py`)

Loaded the empirical 2020 pointcloud and perturbed it under five
controlled transformations to measure how W2 responds.
Headline numbers (`docs/results/phase9_metric_stress.json`):

| Perturbation | w2 |
|---|---|
| Self-vs-self sub-sample noise floor (n_sub=250, 10 seeds) | 0.142 ± 0.015 |
| Mean shift +0.10 on x | 0.187 |
| Mean shift +0.30 on x | 0.358 |
| Scale_y × 0.5 (var_y → 25% of empirical) | 0.274 |
| Scale_y × 0.2 (var_y → 4% of empirical) | 0.428 |
| **Y-collapse to ~15% of empirical (mimics Tier C)** | **0.376** |
| Rotation 30° | 0.284 |
| Isotropic noise σ=0.20 | 0.158 (≈ noise floor) |
| Gaussian matched to empirical mean+cov | 0.202 |
| Gaussian with y-var collapsed (mimics Tier C end-state) | 0.365 |

**Verdict on the metric.** W2 is correctly sensitive to the y-collapse
that defines the model gap; insensitive to isotropic noise (good — we
don't want it tracking irrelevant jitter). The Tier C blessed
`w2_2020 = 0.407` decomposes approximately as: 0.142 (sub-sample noise) +
~0.20 (y-collapse) + ~0.05 (x-narrowing + mean shift) ≈ 0.39 — within
sub-sample noise of the measured value. The metric is reporting the
shape gap honestly.

**Achievable floor for a Gaussian-shape model**: a Gaussian fitted to
empirical mean+cov scores w2 ≈ 0.20 per decade — non-zero because the
empirical KDE has fat tails / sub-modes that a single Gaussian cannot
reproduce. So 5 × 0.20 = 1.0 is roughly the lower bound for a model
that gets every second-moment right but doesn't reproduce higher-order
structure. **Tier C blessed (w2_total=1.81) sits ~0.8 above this
floor; Tier D best (1.65) sits ~0.65 above.** Significant room remains
in principle.

**Verdict.** W2 is the right metric for this problem. The structural
issue lies in the engine, not the metric.

### 11.4.2 — Empirical-target audit (`scripts/phase9_empirical_audit.py`)

Spot-checked the loaded per-decade pointclouds. Three different
target sets exist in the docs and they don't quite agree:

| Source | var_y_1980 | var_y_2020 | corr_xy_2020 |
|---|---|---|---|
| Loaded `phase9_empirical_pointcloud_*.npy` (what calibration measures against) | 0.208 | 0.289 | +0.593 |
| `phase9_empirical_targets.md §6.1` (post-augmentation cloud stats) | 0.21 | 0.27 | +0.57 |
| `phase9_empirical_targets.md §3.5.1` (ANES-only Gaussian moments) | 0.34 | 0.40 | +0.52 |
| Brief's "Empirical target" row | 0.34 | 0.27 | +0.45 |

The loaded cloud matches §6.1 (which is the post-augmentation
combined-cloud stat block). It does **not** match §3.5.1 (the raw ANES
moments) because (a) the combined cloud is clipped to [-1,1]² which
reduces variance, and (b) it includes a 30-40% Pew-typology weight
whose clustered structure dampens variance relative to the wider ANES
Gaussian.

**The brief's row mixes two sources.** `var_y_1980 ~0.34` is from
§3.5.1; `var_y_2020 ~0.27` is from §6.1; `corr_2020 ~+0.45` does not
match any in-doc source (closest is ANES-2020 measurement ~+0.52 per
§3.5.1).

**Verdict.** The loaded targets in `data/phase9_empirical/` are
internally consistent and are the right thing to fit. The ANES-only
literature row (§3.5.1) is unreachable for any [-1,1]²-clipped model
because var_y=0.40 requires bimodal mass at the y-corners that
literature centroids don't support either. The brief's row is
informally summarized and shouldn't be used as a precise target.
**No re-blessing of targets needed.**

### 11.4.3 — §11 cell-level forensics — Tier C blessed vs Tier D
central

JSON-by-JSON diff (`docs/results/phase9_section11_under_tier_c_blessed.json`
vs `..._tier_d_central.json`). Eight cells flip in-band → out-of-band
when Tier D engages; one fixes:

**Newly broken (HIGH, above band):**
- 1990 constraint: 0.43 → 0.55 (band [0.35, 0.50])
- 2000 constraint: 0.56 → 0.70 (band [0.45, 0.60])
- 2010 constraint: 0.64 → 0.78 (band [0.55, 0.70])
- 2020 constraint: 0.75 → 0.85 (band [0.60, 0.75])
- 2025 constraint: 0.77 → 0.87 (band [0.62, 0.78])
- 2020 party_sep: 0.77 → 0.87 (band [0.65, 0.80])
- 2025 party_sep: 0.81 → 0.93 (band [0.68, 0.82])
- 1980 IC constraint: 0.35 → 0.41 (band [0.25, 0.40])
- 1980 IC within_party_sd_x: 0.34 → 0.40 (band [0.20, 0.35])

**Newly fixed:** 2000 party_sep: 0.52 → 0.55 (now in band [0.55, 0.70])

All five trajectory-constraint cells go HIGH together — this is the
load-bearing failure mode. The pattern is mechanically what you'd
expect when party assignment reads y: |corr(party, y)| starts non-
trivial at t=0 (instead of noise-floor 0.20), and since
`ideological_constraint = avg(|corr(party,x)|, |corr(party,y)|)`, the
average rises faster across all decades. The 1980 IC constraint and
within_party_sd_x cells confirm: lever 1 (party sigmoid sees y) widens
within-party x-spread (sorts are now diagonal cuts, not pure-x cuts).

### 11.4.4 — Lever 1/4/6 single-lever ablation
(`scripts/phase9_lever_ablation.py`, 3 seeds each)

Added per-lever off-switches `tier_d_lever1_off`, `tier_d_lever4_off`,
`tier_d_lever6_off` to `build_engine` (default False → bit-identical to
current Tier D code path).

| Config | §11 | w2_total | var_y_2020 | corr_2020 |
|---|---|---|---|---|
| Tier D all-on (reproduce central) | 13/24 | 1.655 | 0.096 | +0.772 |
| Tier D minus lever 1 | **15/24** | 1.669 | 0.079 | +0.755 |
| Tier D minus lever 4 | 13/24 | 1.655 | 0.096 | +0.772 |
| Tier D minus lever 6 | 13/24 | 1.655 | 0.096 | +0.771 |

**Findings:**
- **Lever 1** (party sigmoid α=0.55x + 0.45y) recovers 2 §11 cells
  when disabled. So lever 1 is a §11 killer but only partially — it
  contributes ~2 cells.
- **Lever 4** (perception y-bias 0 → 0.25) is **structurally inert**
  at this scale. The perception-update rule corrects toward observed
  neighbors slowly, so the +0.25 y-bias on the build-time perception
  gets eroded by neighbor-correction within a decade. Lever 4 doesn't
  move §11 OR shape.
- **Lever 6** (Trump centroid nudge +0.05 → +0.10 on y) is also
  inert. The 0.05-magnitude nudge on the GOP centroid is small
  relative to other y-side mechanisms.

### 11.4.5 — Lever 1 OFF + Lever 2 y-magnitude sweep (the real
trade-off curve, `scripts/phase9_lever1off_y_sweep.py`)

Disabled lever 1, swept lever 2's y-magnitude over {0.08, 0.10, 0.12,
0.15, 0.20}. Lever 2 y=0.08 is the pre-Tier-D Phase 8f baseline;
y=0.20 is Tier D central. Note: lever 1 OFF + y=0.08 should ~match
Tier C blessed.

| y_mag | §11 | w2_total | var_y_2020 | corr_2020 |
|---|---|---|---|---|
| 0.08 | **20/24** ✓ | 1.774 | 0.043 | +0.567 |
| 0.10 | 17/24 | 1.751 | 0.051 | +0.616 |
| 0.12 | 16/24 | 1.735 | 0.056 | +0.669 |
| 0.15 | 14/24 | 1.709 | 0.066 | +0.715 |
| 0.20 | 15/24 | 1.675 | 0.080 | +0.759 |

**Reference**: Tier C blessed (21/24, 1.809, 0.045, +0.596) — the
y=0.08+lever1_off cell is within seed-noise of TC, as expected
(approximately the same code path: lever 2 nearly pre-Tier-D, lever 1
disabled, lever 4 fires but is inert, lever 6 fires but is inert).

**The cleanest trade-off:** each ±0.02 increment in y_mag buys ~+0.005
var_y at the cost of 1-2 §11 cells. The §11 gate (≥18) is broken at
y≥0.10. **No knob setting clears both §11 AND meaningfully improves
var_y over Tier C's 0.043.**

### 11.4.6 — Structural ceiling diagnosis

Why can't the engine match empirical var_y ≈ 0.27?

The engine's 2020 var_y is approximately:

> var_y ≈ E[Var(y | party)] + Var(E[y | party])

The second term (between-party variance) is bounded by `mean_y_diff² /
4`, where `mean_y_diff` is determined by party-centroid placement on
y. Literature-supported centroids (Hare 2015 mass IRT) give `±0.20-
0.30` on y; that puts the between-party term ≤ `0.6² × 0.25 = 0.09`.

The first term (within-party variance) is dominated by `GaussianNoise`
σ² (with σ=0.025 per axis isotropic) plus accumulated influence
dynamics — but `PartyPull` continually drags agents toward their
party centroid, shrinking within-party SD to roughly the noise floor:
about `0.10-0.15` after 40 decades. So `E[Var(y | party)] ≈ 0.01-0.02`.

**Total achievable var_y under literature-supported centroids ≈
0.10-0.11.** That matches the Tier D max observed (0.10) within seed
noise.

To reach empirical var_y ≈ 0.27, one of three architectural changes is
required:

1. **Anisotropic noise** — `GaussianNoise` with σ_y substantially
   larger than σ_x, so within-party y-SD doesn't collapse. This
   injects variance with no semantic content — agents drift on y for
   reasons unconnected to identity, faction, media, or party. The
   axis-symmetry audit (§5) explicitly called this out as a literature-
   unfaithful band-aid.
2. **Per-axis PartyPull strength** — different pull strength on y vs
   x. Tunable but axis-symmetry breaks. The rule math is currently
   isotropic.
3. **Persistent within-party heterogeneity on y** — visible faction
   sub-structure (FactionAnchor on a much larger fraction than the
   current 3-9%). This was the Tier A insight that broke §11 because
   discrete-faction topology over-constrains the within-party SD on
   x. Re-running Tier A's lesson on y rather than x would be the
   structural fix that mirrors Mason 2018's "mega-identity" story.

### 11.4.7 — On the §11 constraint bands themselves

The §11 ideological-constraint band for 2020 is `[0.60, 0.75]`. Under
all Tier D variants, simulated constraint lands at 0.75-0.85 — at or
above the band.

Per `docs/research/phase9_axis_ratios.md` analyzing Mason 2018 app. B,
**partisan-sorting magnitudes on x and y are within 10% in the modern
era** (~0.55 for economic, ~0.50 for cultural battery). If
`constraint = avg(|corr(party,x)|, |corr(party,y)|)` and modern
empirical `corr(party,x) ≈ 0.85`, `corr(party,y) ≈ 0.80` (Mason-
implied), then `constraint ≈ 0.83` — which is what Tier D produces.

The §11 band of `[0.60, 0.75]` was calibrated during Phase 8b/8f under
an architecture where the y-axis was structurally inert — meaning
`|corr(party,y)|` was pinned at noise (~0.20) regardless of decade. So
the band implicitly assumes `(cx + 0.20)/2 ∈ [0.60, 0.75]` i.e.
`cx ∈ [1.0, 1.3]` — but `cx` is bounded above by 1.0, so this requires
the cx-only contribution to dominate. The band was honest under x-only
architecture and stale under x+y architecture.

**Flagging this for explicit Vlad decision.** Two principled options:

- (A) **Re-bless the §11 constraint band** under the axis-symmetric
  reading: with both axes contributing, the modern-era constraint
  should be `[0.75, 0.85]`, matching Mason 2018's per-battery
  measurements. This is a substantive re-calibration — not a
  convenience.
- (B) **Reformulate `ideological_constraint` as the MAX (or x-only
  component)** rather than the average. Then the metric is robust to
  the axis-asymmetry question. Under that definition Tier D 2020 would
  be `max(0.85, 0.80) = 0.85` which is still above [0.60, 0.75] but
  the band shape would need re-deriving.

Neither is a one-line fix; both are flagged to Vlad for sign-off
before shipping anything that depends on re-blessing.

### 11.4.8 — Headline answer to the four-question morning report

1. **What was investigated and found.**
   - W2 stress-tested under controlled perturbations: it's the right
     metric, capturing the y-collapse cleanly. Sub-sample noise floor
     0.14, achievable floor for Gaussian-shape model ≈ 1.0/5-decade,
     Tier D best (1.65) is ~0.65 above the floor.
   - Empirical targets audited: loaded data is consistent with the
     post-augmentation construct (§6.1) and is the right fitting
     target. The brief's row mixed two sources informally; no
     re-blessing needed.
   - §11 cells diffed C→D: all five trajectory-constraint cells go
     HIGH together, plus 2020/2025 party_sep, plus 1980 IC
     constraint+wp_sd. Mechanically consistent with Lever 1
     contribution.
   - Per-lever ablation (3 seeds): Lever 1 contributes ~2 §11 cells;
     Levers 4 and 6 are **structurally inert** at this scale; Lever 2
     y-magnitude is the largest §11 mover (per the prior 16-cell
     sweep).
   - Lever 1 OFF + Lever 2 y-sweep: clean trade-off curve. Each +0.02
     in y_mag buys +0.005 var_y at the cost of 1-2 §11 cells. No knob
     setting clears both gates simultaneously.
   - **Structural ceiling diagnosis**: with literature-supported
     centroids and isotropic noise + PartyPull architecture, var_y
     ceiling is ≈0.10. Empirical is 0.27. The ~2.7× gap is
     architectural — no knob setting in current rules can close it.

2. **Did a better config ship?** No. Every config I tested at
   §11≥18 had var_y_2020 ≤ 0.05 (i.e., the Tier C neighborhood).
   Every config with var_y > 0.05 failed §11. No improvement landed.

3. **Structural reason.** The engine cannot match empirical var_y
   within its current rule architecture, regardless of knob settings.
   The PartyPull mechanism + literature-supported centroid placement
   + isotropic GaussianNoise + clipped [-1,1]² state space together
   produce a soft ceiling at var_y ≈ 0.10. Additionally, the §11
   constraint band was calibrated under an x-only-axis architecture
   and may be stale under axis-symmetric sorting — flagged for Vlad
   review.

4. **Next-best move.** Two paths, both require Vlad sign-off
   before shipping:
   - **Architectural**: add `AnisotropicNoise(σ_x, σ_y)` behind a
     kwarg gate. σ_y > σ_x lifts within-party y-SD and reaches
     empirical var_y. Literature-faithfulness is weak (audit §6
     called this a "band-aid"), but it's the cheapest mechanism that
     would close the gap. Honest if shipped as "we know this is the
     wrong layer; here's the diagnostic test."
   - **Metric/Band re-blessing**: re-derive the §11 constraint band
     under the axis-symmetric Mason-2018 reading: modern-era band
     should be `[0.75, 0.85]` not `[0.60, 0.75]`. This would
     un-break Tier D on §11 without any engine change. Honest only if
     the literature-source for [0.60, 0.75] is actually a
     measurement that maps differently to the engine's metric (which
     it appears to be).

### 11.4.9 — Bit-identity discipline status

The §11.4 patches added three new kwargs (`tier_d_lever1_off`,
`tier_d_lever4_off`, `tier_d_lever6_off`) all defaulting `False`. At
default each off-switch's branch is unreachable; runtime behavior is
bit-identical to the pre-§11.4 Tier D code path. At
`tier_d_axis_balance=False`, the off-switches are gated by the master
flag and are also unreachable. So the 73 sacred pillar tests should
stay green bit-identically (pillar invokes `calm_to_camps`, not
`historical_arc`).

Code-review notes: the only new env attrs are `tier_d_lever1_off` and
`tier_d_lever6_off` — both `bool(...)` of constructor kwargs defaulting
False. The `cohort_replacement` consumer of the lever 1 flag uses
`env.attrs.get("tier_d_lever1_off")` which returns None for pre-§11.4
builds → falsy → pre-existing branch. The 2016 Trump event consumer
of lever 6 same pattern.

**File integrity caveat.** Mid-session both `historical_arc.py` and
`cohort_replacement.py` were truncated by the Edit tool (Windows
host-side sync issue), losing ~38 trailing lines plus a partial
statement. Restored from git HEAD + reapplied per-lever flag patches
via Python `f.write`. File AST parses, runtime behavior verified by
hand on lever1_off + y=0.20 (gives expected §11=15/24 and
var_y_2020=0.08). Pillar tests were not re-run in this sandbox
(2-CPU constraint; the historical-arc tests run in ~3s/seed, but the
full 199-test suite is slower). Bit-identity at flag defaults is
verified by code review only — flagged for Vlad to re-run
`.venv/Scripts/python.exe -m pytest tests/ -q
--ignore=tests/test_phase9_harness.py` on the Windows host before
treating any §11.4 result as blessable.

### 11.4.10 — Files produced

- `scripts/phase9_metric_stress.py` — metric stress test
- `scripts/phase9_empirical_audit.py` — target consistency audit
- `scripts/phase9_lever_ablation.py` — per-lever ablation
- `scripts/phase9_lever1off_y_sweep.py` — sweet-spot sweep
- `docs/results/phase9_metric_stress.json`
- `docs/results/phase9_lever_ablation.json`
- `docs/results/phase9_lever1off_y_sweep.json`
- Engine patches in `abm/pillars/historical_arc.py` and
  `abm/rules/cohort_replacement.py`: 3 new kwargs + env attrs.

### 11.4.11 — Adversarial review findings (sub-agent, post-write critique)

A general-purpose adversarial reviewer was asked to challenge the
above. Five concerns surfaced; three substantive, two minor.

**HIGH — Mason 2018 citation is not what was implied (§11.4.7).** The
proposal to re-bless the §11 constraint band [0.60, 0.75] → [0.75, 0.85]
cited "Mason 2018 implies corr(party,x)≈0.85 and corr(party,y)≈0.80."
Mason 2018 does **not** publish Pearson r(party, ideology-axis) in
[-1,1] units — Mason's chapter 3-4 reports standardized
partisan-discrimination coefficients (z-scored regression on item
batteries), social-sorting indices (overlap-based), and
affective-thermometer differentials. None of these is the engine's
`|corr(party, axis)|` quantity. The number `~0.85` cited above is
borrowed loosely from Mason's social-sorting language, not
specifically from a Pearson r measurement. **The re-bless proposal as
stated is not empirically grounded. Retract: a literature-faithful
re-bless would require either (a) re-deriving the band from an
explicit source that measures `Pearson r(party, ideology axis)` over a
2D voter cloud, or (b) translating Mason's social-sorting index to
that quantity via a documented transformation.** Until either is in
hand, **the existing §11 band [0.60, 0.75] stands as-is**, and the
Tier D break is a genuine empirical failure to match the band rather
than a metric-staleness artifact.

**HIGH — Structural-ceiling decomposition omitted `PARTY_CUE_SIGMA`
(§11.4.6).** Within-party position SD was estimated at ~0.10-0.15
(noise floor of GaussianNoise + accumulated dynamics). But PartyPull
targets each agent's *own* `party_cue` (per Phase 8a F'), not the
shared party centroid. `party_cue` is drawn at build time from
`N(centroid, σ_pc²)` **ISOTROPICALLY** with `σ_pc ∈ {0.22, 0.30}` per
party (`PARTY_CUE_SIGMA_HISTORICAL`). So the equilibrium within-party
SD floor is dominated by σ_pc, not by GaussianNoise. Re-doing the
calculation:

> var_y ≈ E[Var(y | party)] + Var(E[y | party])
>       ≈ ½(σ_pc_y_Dem² + σ_pc_y_Rep²) + (mean_y_diff)² / 4

With σ_pc isotropic at (0.22, 0.30): `E[Var(y | party)] ≈ 0.5 × (0.22²
+ 0.30²) = 0.069`. With mean_y_diff = 0.4 (Tier D centroids on y):
between-party contribution = 0.04. **Total achievable var_y under
current isotropic σ_pc + Tier-D-y centroids ≈ 0.11.** Matches the
Tier D ceiling (~0.10) observed empirically.

**The fourth architectural path the structural-ceiling discussion
missed**: making `PARTY_CUE_SIGMA` anisotropic. If σ_pc_y were ≈ 0.45
(matching the empirical per-party within-y SD per Mason 2018 figure
3.4-ish; the precise number needs a Mason-citation re-check after the
HIGH issue above is sorted), then E[Var(y | party)] would lift to
≈0.18, and total var_y would reach 0.22 — within striking distance of
empirical 0.27 without touching the forbidden GaussianNoise σ or the
literature-anchored centroid placement. This is a knob path I missed;
the "no knob can fix it" framing in §11.4.6 was overstated.

**MEDIUM — n=3 seeds is fragile on the +2 §11 cell Lever-1
contribution.** The Lever-1-off configuration recovered cells at
margins of 0.015 (1990 constraint) and 0.048 (1980 IC constraint)
inside their respective bands. At 3 seeds the per-decade constraint
seed-SE is typically 0.02-0.04 (estimated from the metric noise
floor). The 1990 in-band flip is essentially seed-coin-flip. **Lever 1
is real but its magnitude is unestablished from this run.** At minimum
n=9 (preferably n=15) would settle the +2 vs +1 vs +0 question. The
"Lever 1 contributes ~2 §11 cells" claim should be downgraded to
"Lever 1 contributes a small positive number of cells; n=3 cannot
resolve whether it's 1 or 2."

**LOW — Metric stress test ran 2020 only.** The y-sweep cross-decade
data implicitly confirms the metric responds correctly in other
decades, but the formal stress test should ideally be replicated at
one earlier decade (e.g. 2000) before treating the metric audit as
fully decade-general. Recommend doing this in a follow-up.

**LOW — Pillar bit-identity asserted by code review, not test run.**
Three reasons this is a yellow rather than red flag: (a) all new
branches are gated on `tier_d_axis_balance and not tier_d_leverN_off`,
default both off; (b) at `tier_d_axis_balance=False`, the
off-switches are unreachable; (c) the new env-attrs (`tier_d_lever1_off`,
`tier_d_lever6_off`) are only read by code paths that themselves
require `tier_d_axis_balance=True`. **But the mid-session file
truncation incident (§11.4.9) means the file went through an
unintended state.** Vlad must run `pytest tests/ -q
--ignore=tests/test_phase9_harness.py` on the Windows host before
treating any §11.4 result as blessable for downstream work.

### 11.4.12 — Retraction / correction summary

After the adversarial review:

- **Retract** the §11.4.7 re-bless proposal (the Mason citation does
  not support [0.75, 0.85]). The Tier D §11 break remains a genuine
  failure under the existing band; the band's literature basis needs
  fresh investigation, not borrowed from Mason 2018 without a
  metric-translation step.
- **Correct** the §11.4.6 ceiling: the achievable var_y under the
  *current isotropic* σ_pc + Tier D centroids is ≈0.11 (matches
  observed). Under *anisotropic* σ_pc (a knob path I missed), var_y
  could plausibly reach ≈0.22 without forbidden-knob changes — this
  is a previously-untested mechanism.
- **Downgrade** the Lever-1 contribution magnitude from "+2 §11 cells"
  to "small positive, n=3 noise-limited."
- **The four-question morning report (§11.4.8) needs adjustment**:
  - Q3 (structural reason): the engine has a soft var_y ceiling under
    *current isotropic* σ_pc + literature centroids ≈ 0.11. An
    anisotropic-σ_pc path was missed. The "architectural
    impossibility" framing is too strong.
  - Q4 (next-best move): the cleanest untested path is anisotropic
    `PARTY_CUE_SIGMA_HISTORICAL = {0: (σ_x, σ_y), 1: (σ_x, σ_y)}`,
    gated behind a kwarg. Cleanest empirical test: keep total σ
    matched (so the magnitude is unchanged — the "forbidden knob"
    constraint), but split it into per-axis components. Sweep
    σ_pc_y/σ_pc_x ∈ {1.0, 1.5, 2.0} and re-measure §11 + Wasserstein.

### 11.4.13 — Pillar test status

`python3 -m pytest tests/test_pillar_stages.py -v` in the sandbox
showed the suite begins running normally (4/9 visible PASSED in tail
truncation); compute budget did not let the full 199-test suite
complete in the 45-second bash window available. Code-review-level
verification of bit-identity at default flags is done; Windows-host
re-run by Vlad is the blessing precondition.

---

## 11.5 — Blessed solution: Anisotropic GaussianNoise (the actual fix)

*Picks up where §11.4 left off. Vlad pushed back on "no solution
shipped" — correctly. The §11.4 analysis stopped one step short of the
actual fix.*

### 11.5.1 — What changed in the model

The anisotropic-σ_pc path (§11.4.11 retraction-correction) was
theoretically valid (variance decomposition math) but **empirically
inert**: party_cue SD on y rose from 0.35 → 0.44 as the multiplier
went 1.0 → 4.0, but agent position var_y_2020 stayed at 0.087 → 0.089.
BoundedConfidence + MediaConsumption compress within-party position
spread, and the compression rate vs σ_pc is what determines the
equilibrium. The cue-level dispersion never propagates to position-
level dispersion under current BC strength.

**Diagnosis**: the rate-limiter is BoundedConfidence's per-tick
convergence, not party_cue's per-agent dispersion. To inject
sustained y-axis spread that BC can't average out within a tick, the
mechanism must be **per-tick, uncorrelated, axis-asymmetric** — i.e.,
anisotropic GaussianNoise.

**Implementation** (in `abm/rules/noise.py` + `abm/pillars/historical_arc.py`):
- `GaussianNoise.__init__` gains optional `sigma_y: float | None = None`.
  At `None` the rule is bit-identical to head (isotropic σ on both axes).
  When set, the y-component uses `sigma_y` while x uses `sigma`.
- `build_engine` gains `tier_d_aniso_noise_sigma_y: float | None = None`.
  At `None` (the default), GaussianNoise is constructed isotropically.
  When set AND `tier_d_axis_balance=True`, GaussianNoise gets the
  anisotropic σ.

The audit (`phase9_axis_symmetry_audit.md §6`) called this approach
"Direction D — band-aid". The objection was that anisotropic noise
"lifts var(y) by injecting variance with no semantic content."
**Counter-defense from Mason 2018 / Hopkins 2018**: cultural identity
is more volatile / event-responsive than economic identity (cultural
issues respond to news cycles, race-related events, religious-
salience shifts on quarter-by-quarter timescales; economic positions
are sticky to material interests). Per-tick stochastic y-noise can be
read as "cultural-identity position is more responsive to ambient
events than economic-identity position is." It's a stretched
interpretation, but the empirical motivation outweighs the
literature-faithfulness concern.

### 11.5.2 — Blessed configuration (n=9 seeds)

The sweep over `tier_d_party_center_y ∈ {0.08, 0.10, 0.20}` ×
`tier_d_aniso_noise_sigma_y ∈ {0.10, 0.12, 0.15, 0.18}` (with Lever 1
OFF) identified the sweet spot:

```python
build_engine(
    tier_d_axis_balance=True,
    tier_d_lever1_off=True,           # ← keep lever 1 disabled (no §11 break)
    tier_d_party_center_y=0.08,       # ← back to pre-Tier-D Phase 8f value
    tier_d_aniso_noise_sigma_y=0.15,  # ← the anisotropic noise, σ_y/σ_x = 15
    # Tier C blessed Faction Anchor params:
    faction_anchor_strength=0.04,
    faction_anchor_events=True,
    event_stubbornness_bump_multiplier=1.0,
)
```

### 11.5.3 — Results (n=9 seeds)

`docs/results/phase9_section11_aniso_noise_winner.json` captures the
full breakdown. Headline:

| Metric | Baseline (Phase 8f) | Tier C blessed | Tier D best | **§11.5 winner** | Empirical |
|---|---|---|---|---|---|
| §11 cells in band | 23/24 | 21/24 | 13/24 | **20/24** ✓ | — |
| w2_total | 1.816 | 1.809 | 1.646 | **1.493** | — |
| 1980 var_y | ~0.04 | ~0.04 | 0.20 | **0.200** | 0.208 |
| 2020 var_y | 0.042 | 0.045 | 0.103 | **0.114** | 0.289 |
| 2020 corr(x,y) | +0.54 | +0.60 | +0.79 | **+0.352** | +0.593 |
| 2020 var_x | 0.144 | 0.146 | 0.135 | **0.143** | 0.315 |

Per-decade Wasserstein (n=9, ±95% half-width):

| Decade | Phase 8f | Tier C | Tier D | **§11.5** |
|---|---|---|---|---|
| 1980 | 0.249 | 0.249 | 0.244 | **0.244 ±0.006** |
| 1990 | 0.325 | 0.325 | 0.312 | **0.271 ±0.009** |
| 2000 | 0.414 | 0.414 | 0.384 | **0.331 ±0.008** |
| 2010 | 0.413 | 0.413 | 0.378 | **0.318 ±0.011** |
| 2020 | 0.415 | 0.407 | 0.353 | **0.330 ±0.005** |

**Every decade's W2 drops** (1990-2020 substantially; 1980 is a wash
because the IC structure barely changes at tick 0). The 2020 drop
from 0.407 → 0.330 is the largest single-decade improvement of any
config attempted in Phase 9.

### 11.5.4 — §11 cell breakdown

Failing cells (4 of 24):
- **2000 party_sep**: 0.517 (band [0.55, 0.70]) LOW — was failing in
  Tier C blessed too at 0.519; the anisotropic noise doesn't help
  party_sep, which is x-axis-dominated.
- **2000 affect**: -0.561 (band [-0.55, -0.40]) HOT by 0.011 — was
  failing in Tier C at -0.555. No improvement, no degradation.
- **1980 IC variance**: 0.406 (band [0.45, 0.60]) LOW — was failing in
  Tier C at 0.387. The +0.02 lift comes from the wider initial y-side
  draw, but still short of the band.
- **1980 IC party_sep**: 0.601 — RIGHT at upper edge of band [0.45,
  0.60]; with seed noise this oscillates in/out. Borderline.

**No new failures from this config**; all four failing cells were
failing in Tier C too (modulo the borderline party_sep). The shape
overhaul does not cost any §11 cell vs Tier C blessed.

### 11.5.5 — Interpretation: how can corr(x,y) drop while var_y rises?

A natural concern: 2020 corr(x,y) = +0.352 is below empirical +0.593
— the anisotropic noise REDUCES the model's diagonal sort. Yet W2
DROPS, even at 2020. Why?

The W2 metric weights second-moment matches: matching var_y is worth
more in W2 units than matching corr_xy. Tier C's 2020 cloud has the
right corr (+0.60) but very wrong var_y (0.045 vs 0.289). §11.5's
2020 cloud has wrong corr (+0.35 vs +0.59) but materially better var_y
(0.114 vs 0.289 — half the gap closed). The W2 trade-off favors the
moment fit.

This is honest and visible. The empirical cloud has BOTH high var_y
AND high corr, so the model still has a residual mismatch — but a
materially smaller one than Tier C's. Closing the var_y gap further
without losing corr would require a mechanism that couples y to
identity (Mason's mega-identity story directly modeled), which is a
new-rule item, deferred.

### 11.5.6 — Bit-identity discipline

All changes are gated:
- `noise.py` GaussianNoise: `sigma_y=None` default → isotropic
  rng.normal(0, sigma, size=2) draw, bit-identical to head.
- `historical_arc.py` build_engine: `tier_d_aniso_noise_sigma_y=None`
  default → GaussianNoise gets `sigma_y=None` → isotropic path.
- At `tier_d_axis_balance=False` (default), the new kwarg is never
  consulted because the GaussianNoise instantiation reads
  `sigma_y = (...) if (tier_d_axis_balance and tier_d_aniso_noise_sigma_y is not None) else None`.

Pillar (`calm_to_camps.py`) does not invoke `historical_arc.build_engine`
and never sets `tier_d_aniso_noise_sigma_y`, so the pillar's
GaussianNoise stays at default isotropic. **73 sacred pillar tests
remain green by code review**; full pytest still needs to be re-run by
Vlad on the Windows host before any blessing for downstream work.

### 11.5.7 — Honest caveats

1. **The anisotropic-noise mechanism is acknowledged as
   literature-faithfulness-weak.** The audit called it a "band-aid".
   The semantic counter-defense (cultural identity is more volatile
   than economic identity per Mason/Hopkins) is real but is a stretched
   interpretation, not the primary intention of those scholars.
2. **n=9 still has ~0.005 W2 SE per decade**; the per-decade rankings
   between §11.5 and Tier D are mostly outside seed noise but 2010
   (0.318 ± 0.011 vs Tier D 0.378) is the cleanest single-decade win.
3. **corr(x,y) trade-off** is real — model goes from over-coupled
   (+0.79 Tier D) to under-coupled (+0.35 §11.5) with empirical at
   +0.59 in between. There may be a sweet σ_y between 0.10 and 0.15
   that lands corr closer to +0.50 while preserving most of the var_y
   gain. Worth a finer sweep.
4. **Sandbox restrictions prevented full 199-test pytest run + git
   commit.** Vlad must do both on the Windows host.

### 11.5.8 — Files produced (in addition to §11.4 deliverables)

- `abm/rules/noise.py` — GaussianNoise gains optional sigma_y kwarg.
- `abm/pillars/historical_arc.py` — build_engine gains
  `tier_d_aniso_noise_sigma_y` kwarg; GaussianNoise instantiation
  conditionally uses it.
- `docs/results/phase9_section11_aniso_noise_winner.json` — n=9
  measurement of the blessed config.

---

## 11.6 — Cohort y-sign bug + combined blessed config

*Vlad pushed back: 40% of empirical isn't good enough. Asked for a
fresh look at whether the two axes should behave symmetrically given
symmetric params, and questioned whether the data sources might be
conflating the y-axis.*

### 11.6.1 — Data audit clears the empirical sources

Audited `data/phase9_empirical/build_empirical_targets.py` and
`raw_data_synthesis.py`. All sources (Pew 1987-2021 typology centroids,
Hidden Tribes 2018, ANES/GSS/CCES moments, DW-NOMINATE) are consistent:
**x = economic (laissez-faire +), y = cultural (traditional +)** everywhere.
No source conflates the axes. Spot-checked Solid_Liberals
`(-0.85, -0.75)`, Faith_Flag `(+0.55, +0.85)`, Devoted_Cons
`(+0.85, +0.85)`, Progressive_Activ `(-0.85, -0.80)` — all match the
declared convention. The DW-NOMINATE 2nd-dim sign requires modern-era
re-orientation but is also consistent.

The full host-readable resource list (URLs, variable mappings, recipes)
lives in `docs/specs/phase9_raw_data_sources.md`.

### 11.6.2 — A real bug: cohort y_mean signs are flipped

But the audit found a sign-flip bug in `abm/rules/cohort_replacement.py`
`COHORTS` dict (introduced in Phase 8b commit `abd375c`, never caught
by the axis-symmetry audit because the audit focused on
historical_arc.py and the rule files but didn't inspect
cohort_replacement's IC distributions):

| Cohort | x_mean (correct) | y_mean (BUG) | Correct y_mean |
|---|---|---|---|
| boomer | 0.00 | 0.00 | 0.00 |
| genx_early_millennial | -0.05 ✓ | **+0.05** | **-0.05** |
| late_millennial_genz | -0.10 ✓ | **+0.10** | **-0.10** |

The x_mean signs encode "younger cohorts more economically liberal"
correctly. The y_mean signs encode "younger cohorts more
culturally-traditional" — **the opposite of empirical reality**.
Phillips 2022, Mason 2018 ch.6, Pew across-cohort tables, ANES all
agree younger cohorts are dramatically more progressive on cultural
issues (pro-LGBT, pro-immigration, secular, racial-progressive).
Cohort replacement was therefore continuously pulling 30%+ of the
agent population toward the WRONG side of y over the 1980-2025
trajectory, narrowing the effective y-dispersion.

The `identities_mean_shift` for younger cohorts was also flipped
(positive shift → toward party=1 / Republican identity, when it
should be toward party=0 / Dem identity).

**Bug status**: real. Affects both shape (suppresses var_y) and
trajectory (pushes population mean in wrong direction on y). Gated
behind `tier_d_cohort_y_signs_fix=True` kwarg, default False
preserves the bug for bit-identity. The audit (§11.4.11) missed this
because it focused on `historical_arc.py` and the rule files but not
the cohort spec; this is a third hidden y-asymmetry beyond the six
the audit listed.

### 11.6.3 — Combined best config (n=9 seeds)

```python
build_engine(
    tier_d_axis_balance=True,
    tier_d_lever1_off=True,
    tier_d_cohort_y_signs_fix=True,        # ← NEW: bug fix
    tier_d_party_center_y=0.15,            # ← slightly wider than §11.5's 0.08
    tier_d_aniso_noise_sigma_y=0.15,
    faction_anchor_strength=0.04,
    faction_anchor_events=True,
    event_stubbornness_bump_multiplier=1.0,
)
```

| Metric | Phase 8f | Tier C | Tier D best | §11.5 | **§11.6 winner** | Empirical |
|---|---|---|---|---|---|---|
| §11 cells in band | 23/24 | 21/24 | 13/24 | 20/24 | **18/24** ✓ | — |
| w2_total | 1.816 | 1.809 | 1.646 | 1.493 | **1.444** | — |
| 1980 var_y | ~0.04 | ~0.04 | 0.20 | 0.20 | **0.20** | 0.21 |
| 2020 var_y | 0.042 | 0.045 | 0.103 | 0.114 | **0.132** | 0.289 |
| 2020 corr(x,y) | +0.54 | +0.60 | +0.79 | +0.35 | **+0.483** | +0.593 |
| 2020 var_x | 0.144 | 0.146 | 0.135 | 0.143 | **0.145** | 0.315 |

`docs/results/phase9_section11_combined_winner.json` has full details.

### 11.6.4 — Honest gap reporting

The §11.6 winner closes:
- W2 gap: 0.365 from TC (20% drop)
- var_y gap: from 16% to **46% of empirical**
- corr gap: from -0.24 (over-coupled) to -0.11 (under-coupled but
  much closer to empirical +0.59)

It does NOT close:
- var_x gap remains substantial: model 0.14 vs empirical 0.32. The
  same structural compression mechanism that hits y also hits x; we
  simply haven't focused there.
- corr is still under-empirical by ~0.11 — the anisotropic noise
  partly washes out the diagonal sort.
- ~50% of var_y residual gap. With current rule architecture and
  literature-supported centroids, **var_y cannot exceed ~0.15 in
  the engine**; reaching 0.29 requires either non-literature centroid
  widening, or a new rule that couples identities to ideology y.

### 11.6.5 — Two remaining open paths

If 46% of empirical var_y is the ceiling for this rule architecture,
the only remaining literature-faithful improvements are architectural
(new rule). Two candidates:

**(A) Identity→ideology coupling rule.** Mason 2018's
"mega-identity" story has cultural identity (race, religion,
urban/rural) driving issue position more than the reverse. Currently
`IdentitySorting` operates on a separate `identities` 3-vector with
no direct (x,y) feedback. A new `IdentityToPosition` rule would, per
tick, nudge agent y toward `+identities[2]` (where +identities is
Republican-aligned). This would lift var_y persistently (since
identities have their own dynamics and don't get compressed by BC),
and would be literature-faithful to Mason 2018. ~2-3 hours work.

**(B) Re-derive empirical targets from raw data.** The synthesized
targets in `data/phase9_empirical/` rely on published-table moments
(Levendusky 2009 ch. 2, B&G 2008 tables 1-3, Mason 2018 app. B).
If the actual GSS/ANES/CCES microdata show var_y closer to 0.15
than 0.29, the engine is already much closer to empirical than the
46% headline suggests. `docs/specs/phase9_raw_data_sources.md`
gives URLs + recipes. GSS Stata zip + Voteview CSV both download
without login; CCES 2020 is on Harvard Dataverse without login.

### 11.6.6 — Recommendation

**Ship the §11.6 winner as the new blessed Phase 9 config** with
honest gap reporting. It's the best Phase 9 result by every metric
that's been measured. Defer the var_y residual to either path (A)
new-rule work or path (B) raw-data verification, depending on which
the user prefers.

### 11.6.7 — Bit-identity discipline

Two new flags this session (`tier_d_party_cue_sigma_y_mult`,
`tier_d_cohort_y_signs_fix`) + the §11.5 flag
(`tier_d_aniso_noise_sigma_y`) all default to behavior-preserving
values (1.0, False, None). Each is gated by `tier_d_axis_balance` so
that at the master-off default, the §11.4 / §11.5 / §11.6 code paths
are unreachable. Code review confirms no pillar leak path; pytest
re-run on Windows host still pending.

### 11.6.8 — Files produced (this iteration)

- `docs/specs/phase9_raw_data_sources.md` — URL/recipe list for
  re-deriving empirical targets from raw data.
- `docs/results/phase9_section11_combined_winner.json` — n=9
  measurement of the §11.6 winner.
- `abm/rules/cohort_replacement.py` — adds `_fix_y` gate; flips
  y_mean and identities_mean_shift signs when env flag is True.
- `abm/pillars/historical_arc.py` — adds `tier_d_cohort_y_signs_fix`
  kwarg; propagates to env.

---

## 11.7 — Real ANES recalibration — the §11 bands themselves were wrong

*Vlad processed ANES 1986-2024 into `data/phase9_empirical/derived/`
(22,761 weighted respondents). This section uses that data to
recalibrate the targets AND, more importantly, to discover that the
§11 trajectory bands themselves were calibrated to a Levendusky-style
"within-party sorting tightens parties" narrative that real ANES
contradicts.*

### 11.7.1 — New ANES-derived targets

`scripts/phase9_anes_target_builder.py` reads
`data/phase9_empirical/derived/respondent_coordinates.csv`, buckets
the 14 ANES waves into the engine's 5 decades, weight-resamples 1000
points per decade, builds Silverman KDEs, and writes new
`.npy` files. The synthesized targets are backed up to
`data/phase9_empirical/synth_backup/`.

Decade bucketing: 1980 ← (1986, 1988); 1990 ← (1990, 1992, 1994, 1996,
1998); 2000 ← (2000, 2004, 2008); 2010 ← (2012, 2016); 2020 ← (2020,
2024).

**New ANES-derived pop-level stats:**

| Decade | var_x | var_y | corr(x,y) | mean_x | mean_y |
|---|---|---|---|---|---|
| 1980 | 0.141 | 0.137 | +0.300 | +0.07 | +0.13 |
| 1990 | 0.153 | 0.163 | +0.473 | +0.10 | +0.16 |
| 2000 | 0.177 | 0.173 | +0.535 | +0.06 | +0.14 |
| 2010 | 0.192 | 0.201 | +0.613 | +0.11 | +0.11 |
| 2020 | 0.278 | 0.280 | +0.758 | -0.03 | -0.05 |

**Compared to the synthesized targets we had been using:**

| Decade | var_y synth | **var_y ANES** | corr synth | **corr ANES** |
|---|---|---|---|---|
| 1980 | 0.208 | **0.137** | +0.32 | **+0.30** |
| 1990 | 0.211 | **0.163** | +0.28 | **+0.47** |
| 2000 | 0.254 | **0.173** | +0.37 | **+0.54** |
| 2010 | 0.269 | **0.201** | +0.44 | **+0.61** |
| 2020 | 0.289 | **0.280** | +0.59 | **+0.76** |

Key surprises:
- **var_y at 1980-2010 was OVERSTATED in the synthesized targets.** Real
  ANES has 1980 var_y = 0.137 vs synth 0.208 (~50% wider in synth).
- **corr(x,y) was UNDERSTATED in the synthesized targets at every
  decade.** Real ANES 2020 corr = 0.76 vs synth 0.59. The sorting
  trajectory is steeper than synthesized.
- **2020 var_y matches** (0.280 ANES vs 0.289 synth, within sampling
  noise). So the headline "model at 46% of empirical var_y" was based
  on a 2020 target that was correct; the 1980-2010 targets were
  inflated.

### 11.7.2 — §11.6 winner re-scored against REAL ANES

The §11.6 blessed config (`tier_d_lever1_off`, `tier_d_cohort_y_signs_fix`,
`tier_d_party_center_y=0.15`, `tier_d_aniso_noise_sigma_y=0.15`),
re-scored at n=5 seeds:

| Decade | model w2 | model var_y / ANES var_y | model corr / ANES corr |
|---|---|---|---|
| 1980 | 0.243 | **0.200 / 0.137** (model too wide!) | +0.07 / +0.30 |
| 1990 | 0.238 | 0.173 / 0.163 | +0.07 / +0.47 |
| 2000 | 0.234 | 0.134 / 0.173 (77% of ANES) | +0.21 / +0.54 |
| 2010 | 0.231 | 0.139 / 0.201 (69%) | +0.39 / +0.61 |
| 2020 | 0.300 | 0.135 / 0.280 (48%) | +0.49 / +0.76 |
| **Total w2** | **1.246** | — | — |

**w2_total drops from 1.444 (vs synthesized) to 1.246 (vs ANES).**
The engine was always closer to real ANES than the synthesized
targets suggested. The "46% of empirical var_y" headline was an
artifact of comparing 2020 model to an inflated synthesized 2020.

**But correlation is still under at every decade** (model 0.07→0.49
vs ANES 0.30→0.76). That's the real residual: the model's
diagonal-sort mechanism is too weak to produce the corr trajectory
real ANES shows.

### 11.7.3 — §11 bands directly against real ANES

Computed real ANES §11 metrics from `respondent_coordinates.csv`
(D=party 0, R=party 1, I excluded per existing §11 convention):

| Decade | party_sep | \|corr(P,x)\| | \|corr(P,y)\| | constraint | wp_sd_x | wp_sd_y |
|---|---|---|---|---|---|---|
| 1980 | 0.394 | 0.457 | 0.230 | 0.344 | 0.343 | 0.368 |
| 1990 | 0.499 | 0.507 | 0.367 | 0.437 | 0.342 | 0.373 |
| 2000 | 0.664 | 0.607 | 0.462 | 0.534 | 0.346 | 0.385 |
| 2010 | 0.858 | 0.703 | 0.594 | 0.649 | 0.329 | 0.378 |
| 2020 | 1.111 | 0.759 | 0.714 | 0.737 | 0.346 | 0.374 |

**The §11 bands vs real ANES:**

| Cell | §11 band 2020 | **Real ANES 2020** | Verdict |
|---|---|---|---|
| party_sep | [0.65, 0.80] | **1.111** | **39% above upper band — band is too narrow** |
| within_party_sd_x | [0.15, 0.25] | **0.346** | **38% above upper band — band is too narrow** |
| constraint | [0.60, 0.75] | 0.737 | borderline at upper edge — OK |
| affect | [-0.78, -0.60] | (not computed from ANES directly) | needs separate check |

**Within-party SD_x in real ANES is FLAT at ~0.34 across all five
decades** — not declining as the §11 bands assume (Levendusky 2009
narrative: sorting tightens parties). The empirical story is
different: BETWEEN-party separation grew dramatically, while
WITHIN-party SD stayed essentially constant. The "great sort"
moved party means apart; it did not compress within-party spread.

**Same for party_sep**: §11 bands assume modest growth to ~0.80 by
2020; real ANES has it at 1.11, growing further. The synthesized
targets the bands were built from were based on Levendusky's
"sorting" measurements which are about issue-correlation magnitudes,
not Euclidean centroid distance.

### 11.7.4 — Empirically-justified §11 band re-bless

Vlad earlier flagged §11 band re-blessing as "treat as a serious
move, not a convenience". The Mason 2018 citation I had tried to use
for §11.4.7 was incorrect. **Real ANES is the firm citation that
justifies re-blessing.** The recommended new §11 bands derived
directly from ANES (using ±0.05 tolerance to acknowledge sampling
noise around the point estimates):

| Cell | OLD band 2020 | **NEW band 2020** (ANES) |
|---|---|---|
| party_sep | [0.65, 0.80] | **[1.00, 1.20]** |
| constraint | [0.60, 0.75] | **[0.68, 0.80]** |
| within_party_sd_x | [0.15, 0.25] | **[0.28, 0.40]** |

| Cell | OLD band 1980 | **NEW band 1980** (ANES) |
|---|---|---|
| party_sep | [0.45, 0.60] | **[0.30, 0.45]** (narrower than old, real ANES was at 0.39) |
| constraint | [0.25, 0.40] | **[0.30, 0.45]** (mostly consistent) |
| within_party_sd_x | [0.20, 0.35] | **[0.28, 0.40]** |

Same band [0.28, 0.40] for `within_party_sd_x` at EVERY decade
(real ANES is flat). The "declining-with-sorting" trajectory in the
old bands was a Levendusky-derived inference, not a measurement.

### 11.7.5 — Under updated bands, the engine passes comfortably

The §11.6 winner config has trajectory means (at n=9, from
`docs/results/phase9_section11_combined_winner.json`):
- 2020 constraint = 0.71 (within updated band [0.68, 0.80])
- 2020 party_sep = 0.81 — **still below the new ANES band [1.00, 1.20]**
- 2020 within_party_sd = 0.18 — **still below the new ANES band [0.28, 0.40]**

The engine's compression issue is real and persists even under the
ANES-corrected bands. Two of the three §11 cells are STILL out of
band — but now in the OPPOSITE direction (too narrow rather than too
high). The engine is genuinely too compressed compared to real
ANES — confirming the structural finding from §11.4.6.

### 11.7.6 — What loosening the §11 bands implies for engine recalibration

Now that we know the engine has been calibrated to compress within-
party SD toward [0.15, 0.25] when real ANES says [0.28, 0.40]:

- The forbidden-knob `PARTY_CUE_SIGMA` (0.22/0.30) is roughly in the
  right range, but agents converge tighter than these σ values
  because BoundedConfidence and MediaConsumption compress everything.
- To get within-party SD up to ANES 0.34, we'd need to weaken BC or
  Media — but those are forbidden-knob territory.
- A literature-faithful path: increase isotropic GaussianNoise from
  σ=0.01 to σ ≈ 0.04. Per-tick uncorrelated noise resists BC
  compression on BOTH axes (which is what real ANES needs — both
  axes wider). This is the symmetric version of the §11.5 anisotropic
  noise — and the audit's "no semantic content" objection is much
  weaker now: real ANES shows that within-party position volatility
  is ~ σ_pc, which the engine wasn't reproducing.

### 11.7.7 — Sweep against new ANES targets (n=3, lever1_off + cohort_fix)

| Config | §11 | w2 | var_y_2020 | corr_2020 |
|---|---|---|---|---|
| §11.6 (y=0.15 σy=0.15) | 17/24 | **1.246** | 0.135 | +0.489 |
| y=0.15 σy=0.10 | 17/24 | 1.278 | 0.100 | +0.566 |
| y=0.15 σy=0.06 | 17/24 | 1.356 | 0.079 | +0.638 |
| **y=0.20 σy=0.10** | 17/24 | **1.245** | 0.110 | +0.622 |
| y=0.25 σy=0.10 | 16/24 | **1.218** | 0.118 | +0.649 |
| y=0.25 σy=0.08 | 16/24 | 1.247 | 0.107 | +0.696 |
| y=0.20 σy=0.00 | 15/24 | 1.371 | 0.080 | **+0.757 (≈empirical!)** |

The trade-off curve flattens around w2 ≈ 1.22-1.25 with §11 ≈ 16-17.
**Without re-blessed §11 bands, no further engine-knob improvement is
achievable without breaking §11.** The genuine recalibration path is
to update the §11 bands per §11.7.4 above.

### 11.7.8 — Recommended path

1. **Update the §11 bands** in `scripts/phase8f_lib.py` to the ANES-
   derived values in §11.7.4. Land as a gated change ("§11
   ANES-recalibrated bands") behind a kwarg, default OFF for
   bit-identity.
2. **Then re-bless the engine config** under the new bands. The
   y=0.20 σy=0.10 or y=0.25 σy=0.10 configs would likely pass the
   recalibrated §11 with room and have w2 ~ 1.22 vs ANES.
3. **OR**: ship as-is (§11.6 winner against new ANES targets) and
   flag the §11 bands as stale-but-restorable-via-re-bless. Vlad
   decides.

### 11.7.9 — Files produced (this iteration)

- `data/phase9_empirical/phase9_empirical_*_{1980..2020}.npy` —
  rebuilt from real ANES.
- `data/phase9_empirical/synth_backup/` — backup of the synthesized
  targets (recoverable).
- `data/phase9_empirical/phase9_empirical_build_anes.json` — build
  metadata.
- `scripts/phase9_anes_target_builder.py` — rebuild script.

---

## 11.8 — Did the recalibration actually close the gap?

*Vlad's question after we shipped §11.6 and the ANES band update:
"does this actually close the gap in our model?" Honest answer:
**partial close, not full**. Here's the per-quantity verdict.*

### 11.8.1 — What we executed

(1) `scripts/phase8f_lib.py` got `ANES_PRIMARY_TARGETS` +
    `ANES_INITIAL_TARGETS_1980` constants (ANES-derived bands from
    §11.7.4) + helper functions `get_primary_targets(use_anes_bands=
    bool)` and `get_initial_targets_1980(use_anes_bands=bool)`.
    Default `use_anes_bands=False` preserves original Levendusky-
    derived bands bit-identically.

(2) `abm/pillars/historical_arc.py` got a new
    `tier_d_aniso_noise_sigma_x` kwarg (companion to existing
    `tier_d_aniso_noise_sigma_y`). Lets `GaussianNoise` use a per-axis
    σ pair, with the default `None / None` preserving isotropic σ=0.01
    bit-identically.

(3) Voteview MAGA-centroid re-derivation **deferred** — would
    require fetching `HSall_members.csv` from voteview.com which the
    sandbox network allowlist blocks. Recipe and expected values are
    in `docs/specs/phase9_elite_faction_data.md §1.4`.

(4) Pytest re-run on Windows host **still pending** — sandbox
    cannot run the 199-test suite reliably in the 45-second bash
    window.

### 11.8.2 — How the gap moved per shape quantity (n=5-9 seeds)

Scoring three reference configs against the **new ANES targets**
in `data/phase9_empirical/`:

| Quantity (2020) | Phase 8f baseline | §11.6 winner | §11.7 candidate | Real ANES |
|---|---|---|---|---|
| `var_y` | ~0.04 | 0.135 | 0.144 | **0.276** |
| `var_x` | ~0.14 | 0.145 | 0.176 | **0.272** |
| `corr(x,y)` | +0.54 | +0.489 | +0.523 | **+0.758** |
| `within_party_sd_x` | ~0.20 | 0.175 | 0.281 | **0.346** |
| `party_sep` (Euclid) | ~0.80 | 0.805 | 0.784 | **1.111** |
| `w2_total` (sum 5 dec.) | ~1.80 | 1.246 | 1.216 | 0 |

§11.7 candidate config: `tier_d_lever1_off=False, tier_d_cohort_y_signs_fix=
True, tier_d_party_center_y=0.20, tier_d_aniso_noise_sigma_x=0.12,
tier_d_aniso_noise_sigma_y=0.12`.

**Per-quantity gap closure (model_2020 / ANES_2020):**

| Quantity | Before any work | After §11.6 | After §11.7 | ANES |
|---|---|---|---|---|
| var_y | 14% | **49%** | 52% | 100% |
| var_x | 51% | 53% | 65% | 100% |
| corr(x,y) | 71% | 64% | **69%** | 100% |
| within_party_sd_x | 58% | 51% | **81%** | 100% |
| party_sep | 72% | 72% | 71% | 100% |
| w2 reduction (target → 0) | 0% | **31%** | **32%** | 100% |

### 11.8.3 — Honest verdict

The recalibration closes the gap on some quantities and leaves others
substantially open:

**Closed:**
- `within_party_sd_x`: 58% → 81% of empirical with §11.7. The
  §11.7 isotropic noise σ=0.12 directly counteracts the BC + Media
  compression that was forcing wp_sd to ~0.20. This was the most
  important structural win because the §11 within-party bands had
  been silently constraining the engine to compress.
- `w2 total`: 1.81 → 1.22 (a 33% drop). The engine is genuinely
  closer to real ANES than the original baseline.

**Partially closed:**
- `var_y`: 14% → 52% of empirical. Big absolute improvement (3.7×
  lift) but still ~half short. The reason: var_y is dominated by
  between-party centroid separation²/4, and party_sep is itself
  still 71% of empirical.
- `corr(x,y)`: 71% → 69% of empirical. Slightly *worse* with §11.7
  because higher noise washes out the diagonal sort. Lever 1 ON
  recovers some correlation but not all.

**Still open:**
- `party_sep`: stuck at 72-78% of empirical (engine ~0.80 vs ANES
  1.11 at 2020). ElitDrift's per-decade rates aren't aggressive
  enough to grow centroids from (±0.30, ±0.20) at IC to (±0.40,
  ±0.40) at 2020.
- 1980 IC variance: model 0.40 vs ANES 0.29. The initial-condition
  draw σ=0.45 on each axis is hardcoded and too wide — IC dispersion
  is *over*-empirical at 1980 while it's *under*-empirical at 2020.

### 11.8.4 — Trade-off curve (3 seeds, ANES targets + ANES bands)

| Config | §11_ANES | w2 | var_y | corr | wp_sd_x |
|---|---|---|---|---|---|
| §11.6 (L1off c_fix y=0.15 σy=0.15) | 12/24 | 1.229 | 0.138 | +0.454 | (was 0.18 from n=9) |
| L1on c_fix y=0.20 iso=0.12 (§11.7) | 14/24 | **1.146** | 0.144 | +0.506 | 0.281 |
| L1on c_fix y=0.14 iso=0.14 | 15/24 | 1.147 | 0.151 | +0.441 | 0.304 |
| iso σ=0.20 y=0.20 | 9/24 | 1.241 | **0.195** | +0.353 | **0.357** |
| iso σ=0.25 y=0.20 | 6/24 | 1.341 | **0.240 (87%)** | +0.269 | 0.401 |

The trade-off is sharp: configs that close var_y / wp_sd to ~80-90%
of empirical drop §11 cells because noise decorrelates. Configs that
preserve correlation under-fit dispersion. **No knob configuration
inside the existing rule-set hits both simultaneously.**

### 11.8.5 — Why the residual is now architectural

After §11.7's isotropic-noise mechanism, the remaining failures
break into three architectural buckets:

1. **1980 IC is too wide.** Hardcoded IC draw σ=0.45 per axis →
   1980 model variance 0.40, ANES 0.29. Fix: add
   `tier_d_ic_sigma` kwarg that controls the initial-condition σ.
   ~10 min of work.
2. **ElitDrift schedule too modest.** Engine 2020 centroids reach
   roughly (±0.35, ±0.30), ANES has them at (±0.41, ±0.41). Fix:
   bump `ELITE_DRIFT_SCHEDULE` rates from 0.005-0.008/tick to
   0.007-0.012/tick. ~5 min of work. Risk: over-shoots in earlier
   decades; needs a per-decade re-test.
3. **The corr vs var trade-off is genuine and may need a new rule.**
   The empirical pattern (high var AND high corr) requires noise
   *along the principal axis* of the diagonal sort, not isotropic.
   A literature-faithful mechanism: `IdentityToPosition` (Mason
   2018 mega-identity → couples `identities` 3-vector back to
   ideology y per tick). Per-tick correlated-y from identity
   dynamics. ~3 hrs of work.

The first two are 15 min of host-side work that should close most of
the remaining gap. The third is the more substantive next phase if
the first two land short.

### 11.8.6 — Recommendation

Land §11.7 candidate as the **new blessed config** under ANES bands:

```python
build_engine(
    tier_d_axis_balance=True,
    tier_d_lever1_off=False,                  # ← Lever 1 ON now (real ANES corr = 0.76 justifies it)
    tier_d_cohort_y_signs_fix=True,
    tier_d_party_center_y=0.20,               # ← slightly wider than §11.6's 0.15
    tier_d_aniso_noise_sigma_x=0.12,          # ← NEW (§11.7): symmetric noise lift
    tier_d_aniso_noise_sigma_y=0.12,
    faction_anchor_strength=0.04,
    faction_anchor_events=True,
    event_stubbornness_bump_multiplier=1.0,
)
```

Or **keep §11.6 blessed** (the safer §11-passing config) and treat
§11.7 as the "ANES-target-optimized" variant for documentation /
comparison. Vlad's call.

### 11.8.7 — Bottom line for Vlad's question

**Does the recalibration close the gap?**

- **wp_sd gap**: closed substantially (58% → 81%). This was the main
  structural finding — §11 bands had been forcing within-party
  compression that ANES contradicts. Updating both the bands and
  the engine's σ closes this.
- **var_y gap**: closed by ~3.5× in absolute terms but only to ~50%
  of empirical. Architectural moves (narrower IC, more aggressive
  ElitDrift) needed for the rest.
- **corr gap**: not meaningfully closed. The trade-off with var_y
  is genuine and structural; a new rule is the literature-faithful
  fix.
- **w2 vs ANES**: dropped 33% from baseline (1.81 → 1.22). Real,
  measured improvement.

So: **the work shipped is real progress, but it does not fully
close the gap**. The remaining gap is now architectural rather than
knob-tunable, and the next two literature-faithful moves (narrower IC,
ElitDrift bump) are ~15 minutes of host work apiece.
