# Phase 9 — Landing Summary

*Status: shipped. Engine recalibrated against real ANES 1986–2024.
Last updated 2026-05-28.*

Phase 9 extended the calibration target set from the §11 cells
(scalar band gate) to per-decade 2D Wasserstein distance against
real ANES respondent-coordinate clouds. This document records
the final landed state. The phase-by-phase narrative (Tier A →
Tier C → Tier D → ANES recalibration → activist tail → affect
saturation) lives in git history; the artifacts that survived
are the engine code itself, the empirical anchors JSON, and this
summary.

---

## 1. Blessed configuration

The authoritative scoring preset lives in
`scripts/phase9_anes_score.py::PRESETS["anes_full"]`:

```python
build_engine(
    n_agents=250,
    independent_fraction=0.12,
    factional_seeding=False,
    faction_anchor_strength=0.10,
    faction_anchor_events=True,
    event_stubbornness_bump_multiplier=1.0,
    tier_d_axis_balance=True,
    tier_d_lever1_off=True,
    tier_d_cohort_y_signs_fix=True,
    tier_d_anes_knobs=True,
    tier_d_anes_drift_multiplier=3.0,
    tier_d_anes_sigma_pc_multiplier=1.6,
    tier_c_identity_pull_x=0.020,
    tier_c_identity_pull_y=0.040,
    tier_d_aniso_noise_sigma_x=0.08,
    tier_d_aniso_noise_sigma_y=0.08,
    tier_c_party_pull_strength=0.04,
    tier_c_bc_strength=0.015,
    tier_d_coupling_rho=0.30,
    tier_d_cue_correlation=0.40,
    tier_d_ic_sigma=0.35,
)
```

`tier_d_anes_knobs=True` is the master switch that opts the
historical-arc scenario onto the ANES-derived parameter set
(see §3). At its default `False`, the engine is bit-identical
to the pre-Phase-9 head. The pillar (`calm_to_camps.py`) is
untouched throughout Phase 9; the 73 sacred pillar tests stay
green.

---

## 2. Scoreboard (9 seeds, anes_full)

Final scorecard JSON: `docs/results/phase9_anes_score_anes_full.json`.

**Wasserstein-2 vs real ANES (lower = closer):**

| Decade | W₂ mean | CI95 hw | corr(x,y) | var(x) | var(y) |
|---|---|---|---|---|---|
| 1980 | 0.156 | ±0.017 | +0.44 | 0.166 | 0.150 |
| 1990 | 0.155 | ±0.017 | +0.46 | 0.138 | 0.119 |
| 2000 | 0.171 | ±0.016 | +0.58 | 0.158 | 0.117 |
| 2010 | 0.197 | ±0.022 | +0.72 | 0.194 | 0.164 |
| 2020 | 0.196 | ±0.021 | +0.78 | 0.209 | 0.168 |
| **sum** | **0.876** | — | — | — | — |

Reference floors: sub-sample noise ≈ 0.14 per decade; achievable
Gaussian-shape floor ≈ 0.20 per decade. Per-decade W₂ now sits
within ~0.05 of the Gaussian floor, dominated by sub-sample
noise plus minor higher-moment residuals.

**§11 cells — old Levendusky-derived bands vs new ANES-derived
bands:**

| Band set | Tally | Pass (≥18/24)? |
|---|---|---|
| Old bands | 8/24 | No |
| ANES bands | 18/24 | **Yes** |

The 10 cells that flip from out-of-band to in-band under ANES
bands are concentrated on `within_party_sd` (every decade) and
`party_sep` (1990, 2010): the original Levendusky / Baldassarri-
Gelman bands silently compressed both quantities below what real
ANES measures.

> **Calibration-recovery, not validation (peer-review audit P2 / F2, F11).**
> The §11 cell tally and the Wasserstein-2 `w2_total` are **goodness-of-fit /
> calibration-recovery** numbers: they are scored against the *same* ANES recode
> (`data/phase9_empirical/derived/respondent_coordinates.csv`) that set the
> knobs and that defines the bands and the W₂ target — so they cannot, by
> construction, *falsify* the model. Do not present them as independent
> validation. The genuinely held-out checks carry the validation claim: the
> **GSS instrument cut** (sorting outpaces constraint), the **temporal holdout**
> (`docs/results/e5_holdout.md`), the **Pew 2014 overlap** benchmark, and the
> **per-issue trajectory** (incl. the racial item, never fit). Note honestly
> that the temporal holdout **fails on `party_sep`** — the late-period timing
> rides an exogenously-calibrated mobilization forcing and is not out-of-sample
> predictable (`e5_holdout.md`, blindspot #7). The 18/24 figure above is the
> Phase-9 landing on the 9-seed ANES bands; the *current shipped common-mode
> config* reads **17/24** (5-seed scorecard) / **15/24** (9-seed realism
> battery) — both below the project's own ≥18/24 target (methods §5.30/§5.31).

---

## 3. Architectural changes shipped

All changes outside the pillar (`calm_to_camps.py`) and gated
behind the kwarg flags above. Defaults preserve every pre-Phase-9
test bit-identically.

### 3.1 New rules

- **`IdentityToIdeologyPull`** (`abm/rules/identity_to_position.py`)
  — Mason 2018 mega-identity → ideology coupling. Per tick,
  pulls each agent's `(x, y)` toward the mean of their identity
  3-vector, scaled by per-axis `sx`, `sy` and `party_issue_coupling`.
  Default `sx = sy = 0.0` makes it a no-op for non-ANES paths.

### 3.2 Modified rules

- **`GaussianNoise`** (`abm/rules/noise.py`) — added optional
  `sigma_x`, `sigma_y` (anisotropic per-axis σ) and `rho`
  (Cholesky'd cross-axis correlation). At defaults, isotropic
  σ=0.025, ρ=0 — bit-identical to pre-Phase-9.
- **`EliteDrift`** (`abm/rules/elite_drift.py`) — added optional
  per-axis `rate_y` and an `asymmetric_per_decade` schedule. ANES
  path uses cult > econ drift for Democrats post-2010 and the
  Reagan-era R-heavy pull pre-1990.
- **`CohortReplacement`** (`abm/rules/cohort_replacement.py`) —
  under `tier_d_anes_knobs`, replacement positions are drawn
  from `N(current_party_centroid, σ_anchor=0.30)` instead of
  `N(0, σ_cohort)`, eliminating the centrist-injection dilution
  of late-decade party_sep.
- **`AffectiveUpdate`** (`abm/rules/affective_update.py`) — added
  optional `saturation` kwarg. ANES path uses `saturation=1.0`:
  per-encounter step is scaled by `max(0, 1 − w²)` where `w` is
  the running warmth, soft-clipping the affect trajectory in
  the spirit of Iyengar et al. 2019 ch. 4.

### 3.3 Modified historical-arc

- **Party centroids** — new ANES-derived constants
  `PARTY_CENTERS_PRE_REAGAN_ANES`, `PARTY_CENTERS_1986_ANES`,
  and per-decade interpolation through 2025.
- **Sigmoid K schedule** (`PARTY_ASSIGNMENT_K_ANES`) — back-solved
  from ANES per-decade `corr(party, axis)`: 2.1 (1980) → 5.1 (2020).
- **Per-axis cue σ** — `PARTY_CUE_SIGMA_HISTORICAL_ANES = {D: 0.42,
  R: 0.57}`, multiplied by `tier_d_anes_sigma_pc_multiplier` (1.6).
- **ElitDrift schedules** — `ELITE_DRIFT_SCHEDULE_ANES`,
  `_ANES_Y` (30% higher on cultural axis),
  `ELITE_DRIFT_ASYMMETRIC_ANES_SCHEDULE` (per-decade party-asymmetric
  factors), all scaled by `tier_d_anes_drift_multiplier` (3.0).
- **Temporal-bucket alignment** — historical-arc snapshot ticks
  shifted to match ANES bucket centroids:
  1980 ← tick 21 (≈1987), 1990 ← 42 (1994), 2000 ← 72 (2004),
  2010 ← 102 (2014), 2020 ← 126 (2022). The pre-Reagan centroids
  are the IC at tick 0, then drift to 1986 centroids by tick 21.
- **Emergence-event factions** — re-tuned subpopulation fractions
  and centroids against ANES post-2010 sub-mode locations:
  Tea Party (10%, +0.58/+0.32), MAGA (13% + 50%, +0.60/+0.40),
  Bernie (8%, −0.60/−0.40), DSA (5%, −0.75/−0.65). Activated by
  `faction_anchor_events=True`.

### 3.4 Modified inputs

- **Outlets** (`abm/core/outlets.py`) — `US_MEDIA_OUTLETS_2024_ANES`
  widens outlet positions to match ANES cluster extents: MSNBC
  (−0.80, −0.55), NYT (−0.50, −0.30), LocalTV (0, +0.05), WSJ
  (+0.60, +0.25), Fox (+0.85, +0.65).
- **ANES §11 bands** (`scripts/phase8f_lib.py`) —
  `ANES_PRIMARY_TARGETS` and `ANES_INITIAL_TARGETS_1980` derived
  per-decade from `data/phase9_empirical/derived/`. Selectable
  via `get_primary_targets(use_anes_bands=True)`.

---

## 4. Outstanding gaps

The model is now within seed noise of the achievable Gaussian
floor on most quantities. Three residuals remain:

1. **`party_sep` 2020/2025 below ANES band.** Engine reaches
   0.99 at 2020; ANES is 1.11. The centroid trajectory under
   the current `ELITE_DRIFT_SCHEDULE_ANES × 3.0` multiplier is
   the bottleneck. A modest schedule bump would close it but
   risks 2010 over-shoot. Not a load-bearing failure for the
   intervention work.
2. **`corr(x,y)` at 1980/1990 below ANES.** Engine measures
   ~0.45 vs ANES ~0.55. The per-tick ρ-correlated noise + cue
   ρ closes most of the gap but the early-decade diagonal sort
   takes a few ticks to build. Acceptable.
3. **2025 `party_sep` `within_party_sd`** at edge of ANES band.
   The 2025 endpoint sits just outside the upper band; a
   continued `EliteDrift` ramp post-2020 would lift it. Future
   work.

None of these block the next phase (intervention re-validation
on the new engine).

---

## 5. Files of record

**Engine + rules** (load-bearing):
- `abm/pillars/historical_arc.py` — ANES knobs + schedules
- `abm/rules/identity_to_position.py` — new rule (Phase 9 C)
- `abm/rules/noise.py` — aniso + ρ
- `abm/rules/elite_drift.py` — per-axis + asymmetric
- `abm/rules/cohort_replacement.py` — centroid-anchored under
  `tier_d_anes_knobs`
- `abm/rules/affective_update.py` — saturation
- `abm/rules/faction_anchor.py` — emergence-event pull
- `abm/core/outlets.py` — ANES outlet positions
- `scripts/phase8f_lib.py` — ANES band sets

**Calibration + scoring** (operational):
- `scripts/phase9_anes_score.py` — authoritative scorer; PRESETS["anes_full"]
- `scripts/phase9_anes_knob_anchors.py` — derives empirical knobs
  from ANES respondent CSV
- `scripts/phase9_anes_target_builder.py` — builds per-decade
  `.npy` pointclouds from ANES respondent CSV
- `scripts/phase9_sim_compass.py` — engine-only 2D plot
- `scripts/phase9_sim_vs_anes_compass.py` — side-by-side plot
- `scripts/phase9_shape_diag.py` — within-party covariance + axis
  shape diagnostics
- `scripts/phase9_activist_diag.py` — emergence-event population
  diagnostics
- `abm/calibration_phase9.py` — Wasserstein harness

**Data**:
- `data/phase9_empirical/derived/respondent_coordinates.csv` —
  real ANES, 22,761 rows, 1986-2024
- `data/phase9_empirical/phase9_empirical_pointcloud_{decade}.npy` —
  weighted 1000-point samples per decade (built from CSV)
- `data/phase9_empirical/phase9_empirical_kde_{decade}.npy` — KDEs
  on 50×50 grid
- `docs/results/phase9_anes_knob_anchors.json` — per-decade ANES
  stats + sigmoid K back-solve + centroid velocities
- `docs/results/phase9_anes_score_anes_full.json` — final
  scorecard at n=9 seeds
- `docs/results/phase9_empirical_targets_visualization.pdf` —
  density small-multiples plot

**Phase 8 narrative context** (kept for audit trail):
- `docs/results/phase8b_results.md`, `phase8d_historical_results.md`,
  `phase8e_results.md`, `phase8f_results.md`

---

## 6. Discipline checklist

- [x] Pillar (`calm_to_camps.py`) untouched. 73 sacred tests green
      bit-identically.
- [x] All new kwargs default to values that preserve pre-Phase-9
      behavior. `tier_d_anes_knobs=False` reproduces head exactly.
- [x] Real ANES data (1986-2024) is the calibration target; no
      synthesized targets remain in the loop.
- [x] Empirical anchors derived from ANES, not hand-set:
      `phase9_anes_knob_anchors.json` captures the derivations.
- [x] Sub-sample noise floor measured and reported. Engine sits
      within ~0.05 W₂ of the achievable Gaussian floor.
