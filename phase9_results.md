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
