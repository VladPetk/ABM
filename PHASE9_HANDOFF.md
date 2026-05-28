# Phase 9 Calibration — Handoff Document

*Status: shape calibration partially landed. Architectural gap
remains. Updated 2026-05-28.*

This file is **self-contained**. A reader with no prior context
should be able to pick up the work from this document alone. Detailed
artifacts are referenced by path; nothing here assumes those have
been read.

---

## 1. What polarlab is and what Phase 9 is trying to do

**polarlab** is an agent-based model of US political polarization
1980-2025. Agents live in a 2D ideology compass:

- **x ∈ [-1, 1]**: economic axis. −1 = redistributive / pro-government
  / pro-regulation. +1 = laissez-faire / small-government /
  anti-regulation.
- **y ∈ [-1, 1]**: cultural / social axis. −1 = secular / cosmopolitan
  / pro-LGBT / pro-immigration / racial-progressive. +1 = traditional
  / religious / restrictionist / racial-conservative.

This matches the conventional Nolan-chart / political-compass
orientation. The pillar (`abm/pillars/calm_to_camps.py`) is a
five-stage progression model — S0 baseline through S4 narrow-exposure
camps — that's been blessed across Phase 1-7. **The pillar is
load-bearing infrastructure and its behavior is bit-identity-locked**:
73 sacred tests defend it.

The historical-arc scenario (`abm/pillars/historical_arc.py`) re-uses
the same engine + rules but runs from 1980 (tick 0) to 2025 (tick
135), with per-decade event schedules (Tea Party 2009, MAGA 2015,
Bernie 2016, DSA 2018, etc.) and time-varying ElitDrift /
IdentitySorting / party-issue-coupling schedules.

**Phase 9's goal**: calibrate the engine so its simulated 2D agent
positions at each decade endpoint resemble what real US-electorate
ANES data shows the 2D ideological distribution actually looked like
at that decade. Two metrics:

- **Primary**: 2D Wasserstein-2 distance (`ot.emd2` via POT) between
  the engine's simulated agent cloud at each decade and the empirical
  ANES point cloud at that decade. Lower is better.
- **Gate**: the Phase 8b §11 "cells" — 24 (metric × decade) tests
  against per-decade band targets. Old bands derived from
  Levendusky 2009 / Baldassarri-Gelman 2008 published tables. **New
  bands derived directly from ANES 1986-2024** (see §3 below).
  Gate threshold: ≥18/24 cells in band.

---

## 2. The empirical target — ANES data Vlad processed

Vlad processed ANES Time Series Cumulative Data File 1948-2020
(+2024 wave) into `data/phase9_empirical/derived/`. The processing
pipeline (Vlad's, not mine):

- **Window**: 1986-2024, 14 effective waves (2002 excluded — zero
  listwise survivors).
- **N**: 22,761 respondents after listwise drop on the 7 core items.
- **Weight**: ANES `VCF0009z` (survey weight).
- **Party**: `VCF0301` 7-pt collapsed to D (1-3) / I (4) / R (5-7).
- **Economic axis (3 items)**: `VCF0803` (7-pt lib-cons self-place),
  `VCF0809` (gov-services tradeoff), `VCF0839` (gov healthcare).
- **Cultural axis (4 items)**: `VCF0838` (abortion), `VCF0830` (aid
  to blacks), `VCF0852` (moral views adjust), `VCF0853` (traditional
  values emphasis).
- **Normalization**: each item recoded to higher=conservative,
  rescaled to [-1, 1] using theoretical scale endpoints. Axis score
  is equal-weight mean of items on that axis.

### 2.1 Outputs in `data/phase9_empirical/derived/`

```
respondent_coordinates.csv   22,761 rows: year, party_7pt, party, weight, econ, cult
party_centroids.csv          per-(year, party): n, econ_mean, cult_mean, econ_sd, cult_sd
polarization_series.csv      per-year: ovl_2d, raw/scaled separation, dip stats, MA3
densities/{year}_{D,I,R,ALL}.npy   56 KDEs, 81×81 grid on [-1.05, 1.05]²
coverage_table.csv, recode_log.csv, scaling_params.json, kde_params.json
build_log.md, acceptance_checks.txt
```

### 2.2 What ANES says the population looks like, per decade

(Weighted, all-parties pooled, computed in
`scripts/phase9_anes_target_builder.py`):

| Decade | var(x) | var(y) | corr(x,y) | mean(x) | mean(y) |
|---|---|---|---|---|---|
| 1980 | 0.141 | 0.137 | +0.30 | +0.07 | +0.13 |
| 1990 | 0.153 | 0.163 | +0.47 | +0.10 | +0.16 |
| 2000 | 0.177 | 0.173 | +0.54 | +0.06 | +0.14 |
| 2010 | 0.192 | 0.201 | +0.61 | +0.11 | +0.11 |
| 2020 | 0.278 | 0.280 | +0.76 | -0.03 | -0.05 |

(1980 ← 1986+1988; 1990 ← 1990-1998; 2000 ← 2000-2008; 2010 ←
2012+2016; 2020 ← 2020+2024.)

### 2.3 Key empirical findings the engine needs to match

1. **var(x) ≈ var(y) at every decade** — both axes have essentially
   the same dispersion. The two axes "behave similarly-ish" as Vlad
   originally intuited.
2. **Both variances grow modestly 1980→2010** (~0.14 → 0.20) then
   **jump steeply 2010→2020** (~0.20 → 0.28).
3. **Correlation rises monotonically** from +0.30 (1980) to +0.76
   (2020) — the "great sort" is correlation-builder.
4. **Within-party SD is FLAT** at ~0.33-0.35 across all decades
   (1980-2020). The "sorting tightens parties" narrative is wrong;
   real ANES shows within-party SD doesn't compress. The "sort"
   moves party MEANS apart while within-party spread stays constant.
5. **Party centroids spread dramatically**: D mean (econ, cult) goes
   from (-0.09, +0.05) in 1980 to (-0.41, -0.41) in 2020. R mean
   goes from (+0.25, +0.17) to (+0.40, +0.35). The Dem cultural
   mean drops from +0.05 to -0.41 — a 0.46-unit progressive shift
   on the cultural axis is the single biggest movement.

### 2.4 What real ANES says §11 cells should be

Computed directly from `respondent_coordinates.csv` in §11.7.3 of
`docs/results/phase9_results.md`:

| Decade | party_sep | constraint | wp_sd_x | wp_sd_y |
|---|---|---|---|---|
| 1980 | 0.394 | 0.344 | 0.343 | 0.368 |
| 1990 | 0.499 | 0.437 | 0.342 | 0.373 |
| 2000 | 0.664 | 0.534 | 0.346 | 0.385 |
| 2010 | 0.858 | 0.649 | 0.329 | 0.378 |
| 2020 | 1.111 | 0.737 | 0.346 | 0.374 |

**These are the empirical truths the engine should match.** The
old §11 bands (Levendusky-derived) had `party_sep` 2020 at [0.65,
0.80] — real ANES is 1.11. They had `wp_sd_x` 2020 at [0.15, 0.25]
— real ANES is 0.35. **The old bands were systematically wrong.**

The new ANES-derived bands are in `scripts/phase8f_lib.py` as
`ANES_PRIMARY_TARGETS` + `ANES_INITIAL_TARGETS_1980`, gated by
`get_primary_targets(use_anes_bands=True)`.

---

## 3. The problem — engine output vs ANES

At the current best blessed config, the engine produces an agent
cloud that's substantially under-dispersed relative to ANES. Per
decade endpoints (n=9 seeds):

| 2020 quantity | Engine §11.7 | ANES | Closure |
|---|---|---|---|
| var(x) | 0.176 | 0.272 | 65% |
| var(y) | 0.144 | 0.276 | 52% |
| corr(x, y) | +0.52 | +0.76 | 69% |
| within_party_sd_x | 0.281 | 0.346 | 81% |
| party_sep (Euclid) | 0.78 | 1.11 | 71% |
| w2 to ANES (sum 5 dec) | 1.22 | 0 | — |

For comparison, the **Phase 8f baseline** (pre-Phase-9, no
calibration work) had: var(y) 0.04 (14% of ANES), w2 = 1.81. So
substantial progress has been made (var_y up 3.6×; w2 down 33%).
But the engine still under-matches on every shape quantity.

### 3.1 Decade-by-decade trajectory mismatch

The engine has the right SHAPE OF THE TRAJECTORY for some quantities
and wrong shape for others:

- **var(y)**: ANES rises 0.14 → 0.28 (2× growth). Engine rises 0.20
  → 0.14 (compresses!). Engine starts too wide, then dynamics
  compress it. Empirical does the opposite.
- **corr(x,y)**: ANES rises +0.30 → +0.76 (great sort). Engine
  rises +0.07 → +0.52 (right direction, half the magnitude).
- **wp_sd_x**: ANES flat at ~0.34 across all decades. Engine starts
  at ~0.34 in 1980 then compresses to ~0.18-0.28 by 2020. Engine has
  the right starting point but the dynamics compress it.

---

## 4. What's been tried (chronological)

Full record in `docs/results/phase9_results.md` (~1800 lines).
Summary:

### Tier A (failed)
Discrete factional initial conditions — 8 named 1980 factions with
hard-bound party. Failed §11 structurally (0/27 sweep cells passed).
Discrete-faction topology mechanically forced within-party SD below
empirical band.

### Tier C (passes §11, fails Wasserstein)
`FactionAnchor` rule firing on emergence events (Tea Party 2009,
etc.) with broad-Gaussian ICs. Passes §11 at 21/24 (old bands) but
w2 only mildly improves (1.81 → 1.81 effectively). The y-axis cloud
stays at var_y ≈ 0.045 — 6× too small.

### Tier D (improves Wasserstein, breaks §11)
Six-lever axis-symmetry rebalance. The
`docs/research/phase9_axis_symmetry_audit.md` found that the engine's
rule math is axis-symmetric but six engineering inputs encode silent
x-dominance:

1. Party-assignment sigmoid uses x only (`sigmoid(K·x)`) →
   Tier D variant `sigmoid(K·(0.55x + 0.45y))`.
2. `PARTY_CENTERS_1980` placed at (±0.30, ±0.08) → Tier D (±0.30,
   ±0.20).
3. Initial-position side draw `side·0.15` on x, zero on y → Tier D
   adds `side_y·0.12` with ρ ≈ +0.20 coupling.
4. Perception-gap bias +0.25 on x, 0 on y → Tier D inverts to
   +0.20 on x, +0.25 on y (cultural-axis perception gap is bigger
   per Ahler-Sood 2018).
5. Outlet positions span 1.5× more on x than y → deferred.
6. 2016 Trump centroid nudge (+0.05, 0) → Tier D (+0.02, +0.10)
   per Sides/Tesler/Vavreck 2018 fig. 7.3.

Tier D improves w2 to 1.65 but breaks §11 to 13/24.

### §11.4 — Diagnostic phase
- Metric stress-test: W2 IS sensitive to y-collapse; the metric is
  honestly capturing the shape gap.
- §11 cell-level diff Tier C → Tier D: all 5 decade-constraint
  cells go HIGH together; pattern consistent with Lever 1.
- Per-lever ablation (3 seeds): Lever 1 contributes a small positive
  number of cells when disabled; Levers 4 and 6 are **structurally
  inert** at this scale (Δ < 0.001 in all measured cells).

### §11.5 — Anisotropic GaussianNoise
The audit had pre-emptively labeled anisotropic noise (σ_y > σ_x) as
"Direction D — band-aid". But empirically tested, it works: per-tick
uncorrelated y-noise escapes BC compression because BC averages
neighbors (which preserves variance injection). With σ_y=0.15 +
Lever 1 off + y_centroid=0.08, achieved §11=20/24, w2=1.49 (down
0.32 vs Tier C blessed), var_y_2020 = 0.114 (up from 0.045).

### §11.6 — Cohort y-sign bug fix
Found a real long-standing bug in
`abm/rules/cohort_replacement.py` `COHORTS` dict:

```python
"genx_early_millennial": { "y_mean": 0.05 },        # WRONG: should be -0.05
"late_millennial_genz":  { "y_mean": 0.10 },        # WRONG: should be -0.10
```

Under engine convention (+y = traditional), `y_mean=+0.10` for
Gen-Z says "younger cohorts more culturally traditional" — the
opposite of every empirical cohort study (Phillips 2022, Mason
2018). The x_mean signs are correct (younger = -x = more
economic-liberal). The bug went undetected for ~6 phases because
the y-axis was structurally inert until Phase 9 cared.

Fixed gated behind `tier_d_cohort_y_signs_fix=True` kwarg.

Combined with §11.5 noise, the §11.6 winner (cohort_fix + lever1_off
+ y=0.15 + σ_y=0.15) achieved §11=18-20/24, w2=1.44 (vs Tier C 1.81),
var_y_2020=0.13.

### §11.7 — Real ANES recalibration (this session)
Vlad processed real ANES data into `data/phase9_empirical/derived/`.
This revealed:

- The synthesized targets we'd been using were INFLATED at
  1980-2010 var_y and UNDER-stated correlations at every decade.
- Real ANES `within_party_sd_x` is FLAT at ~0.34 across all decades.
- The §11 bands themselves had been systematically wrong — they
  were calibrated to a Levendusky-narrative "sorting tightens
  parties" reading that real ANES contradicts.
- New ANES-derived §11 bands added to `scripts/phase8f_lib.py`
  (gated; default preserves old bands).
- A new `tier_d_aniso_noise_sigma_x` kwarg added so isotropic noise
  can lift both axes (since real ANES says var_x ≈ var_y).

### §11.8 — Did the gap actually close?
Honest answer: **partial close**. See §3 above. The wp_sd gap closes
substantially (51% → 81% of empirical). var_y and corr gaps narrow
but stay at ~50-70%. w2 drops 33% from baseline.

---

## 5. The current blessed config (or two candidates)

Two configs sit at the Pareto frontier:

### Option A — §11.6 (safer, passes §11 at 18/24 with old bands)

```python
from abm.pillars.historical_arc import build_engine

eng = build_engine(
    n_agents=250,
    independent_fraction=0.12,
    factional_seeding=False,
    faction_anchor_strength=0.04,
    faction_anchor_events=True,
    event_stubbornness_bump_multiplier=1.0,
    tier_d_axis_balance=True,
    tier_d_lever1_off=True,                  # Lever 1 disabled
    tier_d_cohort_y_signs_fix=True,
    tier_d_party_center_y=0.15,
    tier_d_aniso_noise_sigma_y=0.15,         # anisotropic y-only noise
)
```

Measured (n=9, vs new ANES targets): §11_OLD=18/24, w2=1.246,
var_y_2020=0.135, corr_2020=+0.489.

### Option B — §11.7 (better shape, doesn't pass old §11 gate)

```python
eng = build_engine(
    n_agents=250,
    independent_fraction=0.12,
    factional_seeding=False,
    faction_anchor_strength=0.04,
    faction_anchor_events=True,
    event_stubbornness_bump_multiplier=1.0,
    tier_d_axis_balance=True,
    tier_d_lever1_off=False,                 # Lever 1 ON (real ANES corr=0.76)
    tier_d_cohort_y_signs_fix=True,
    tier_d_party_center_y=0.20,
    tier_d_aniso_noise_sigma_x=0.12,         # ISOTROPIC noise lift
    tier_d_aniso_noise_sigma_y=0.12,
)
```

Measured (n=9): §11_OLD=12/24, §11_ANES=13/24, w2=1.216,
var_y_2020=0.144, corr_2020=+0.523, wp_sd_2020=0.281.

Option A is the safer "ship it" choice. Option B is the better
shape match but fails the §11 gate at the current threshold.

---

## 6. What's still missing (in priority order)

### 6.1 IC dispersion is too wide (1980 problem)

`abm/pillars/historical_arc.py` lines ~467, ~479 have the hardcoded
initial-condition draw:

```python
pos_x = float(np.clip(side * 0.15 + rng.normal(0, 0.45), -1.0, 1.0))
pos_y = float(np.clip(rng.normal(0, 0.45), -1.0, 1.0))   # or with Tier D lever 3
```

The `0, 0.45` Gaussian draw produces var ≈ 0.20 per axis at 1980.
Real ANES 1980 has var ≈ 0.14. **The IC is too wide by ~40%.**

**Fix**: add a `tier_d_ic_sigma: float | None = None` kwarg. When
set AND `tier_d_axis_balance=True`, the IC draw uses
`rng.normal(0, tier_d_ic_sigma, …)` instead of 0.45. Empirical-
matching value ≈ 0.35 (gives var ≈ 0.12, close to ANES 0.14).

**Risk**: may cascade through 1990-2020 trajectories. Probably good
because the engine currently has 1980 var_y too high AND 2020 var_y
too low — narrowing 1980 plus the existing noise mechanism may
naturally produce a flatter-then-rising trajectory closer to ANES.

### 6.2 ElitDrift schedule too modest (post-2000 problem)

`abm/pillars/historical_arc.py` lines 135-147:

```python
ELITE_DRIFT_SCHEDULE = {
    "1980-90": 0.005,
    "1990-00": 0.008,
    "2000-10": 0.008,
    "2010-20": 0.007,
    "2020-25": 0.006,
}
```

These rates produce party-centroid drift summing to about ±0.35
on each axis by 2020. Real ANES has centroids at (±0.41, ±0.41).
**Centroid drift is too modest by ~20% at the long-term horizon.**

**Fix**: bump the schedule to {1980: 0.005, 1990: 0.010, 2000:
0.010, 2010: 0.008, 2020: 0.007}. The 1990-2010 rates are the
biggest movers (peak "great sort" era). Also consider per-axis
asymmetry — real ANES cultural-axis growth (D mean cult +0.05 →
-0.41) is bigger than economic-axis growth (D mean econ -0.09 →
-0.41 also, actually similar). So isotropic bump is probably fine.

**Risk**: may push 1980-2000 §11 cells out of band.

### 6.3 corr vs var trade-off — a new rule is the literature-faithful fix

The §11.7 config can match wp_sd but loses corr (~0.50 vs ANES
0.76). Higher noise widens dispersion but decorrelates the diagonal
sort. With knobs alone, this trade-off seems pinned.

**Architectural fix**: a new `IdentityToPosition` rule. The
existing `IdentitySorting` rule operates on a 3-vector `identities`
attribute that's separate from ideology (x,y). Mason 2018's
"mega-identity" story has cultural identity (race, religion,
urban/rural) **driving** issue position, not the reverse. A new
per-tick rule that nudges agent y toward `+identities[mean]`
(where +identities = party-1-aligned in the existing convention)
would:

- Produce y-axis variance driven by identity variance (which doesn't
  get BC-compressed because identity space isn't subject to BC).
- Preserve correlation because identity ↔ party correlation is
  high.

**Estimated work**: ~3 hours. New file `abm/rules/identity_to_position.py`,
gate behind a kwarg `tier_d_identity_to_position=False`.
Literature-faithful per Mason 2018 ch. 4.

### 6.4 MAGA sub-centroid (small but documented inaccuracy)

`abm/pillars/historical_arc.py:963` has the MAGA event setting
sub-centroid at (+0.50, +0.55). Per Voteview House Freedom Caucus
115th Congress: actual mean DW-NOMINATE is (+0.63, +0.40). The
engine has the y-coordinate too high. Per Sides/Tesler/Vavreck
2018 voter-level analysis: Trump voters shifted cult by ~0.30 from
2012-2016, not the engine's +0.55.

**Fix**: change the centroid to (+0.55, +0.40) — splits the
difference between legislator and voter-level estimates. ~2 lines
of code. Effect on aggregate stats: small.

`docs/specs/phase9_elite_faction_data.md` has the full elite-data
resource list (Voteview, Bonica DIME, etc.) for re-deriving all
four faction sub-centroids if Vlad wants to do it comprehensively.

---

## 7. Discipline / constraints

These constraints from Vlad's earlier briefs are still in force:

- **Pillar bit-identity is non-negotiable.** Any code path added
  must be gated behind a kwarg defaulting to the pre-existing
  behavior. The 73 sacred pillar tests must stay bit-identically
  green. (As of now: code review verifies bit-identity at flag
  defaults; `pytest tests/ -q --ignore=tests/test_phase9_harness.py`
  hasn't been re-run on Windows host after §11.4-§11.8 changes —
  Vlad needs to do this before treating any new config as fully
  blessed.)

- **Forbidden knobs**: `TICKS_PER_YEAR`, `FJ_ALPHA`, `BC_TEMPERATURE`,
  `BC_AFFECT_WEIGHT`, `TR_AFFECT_WEIGHT_REWIRE`,
  `BACKLASH_AFFECT_THRESHOLD`, `COOPERATIVE_MUTE`, `PARTY_CUE_SIGMA`
  scalar magnitudes (0.22/0.30 locked — though per-axis split was
  added gated). `X1-X7` bucket labels under §11 (until re-blessed
  via §11).

- **Don't touch UI/website files** (`website/`, Solara-related).

- **Investigations don't require pre-approval**; shipping does.
  Re-blessing §11 bands counts as "shipping" and requires Vlad
  sign-off. The §11.7 ANES band re-bless is the case in point —
  bands are wired into the code as `ANES_PRIMARY_TARGETS` but
  default to OFF; Vlad still needs to explicitly approve flipping
  the default.

---

## 8. Quick orientation for a fresh agent / future Vlad

If you're picking this up cold:

1. **Read this file** (you're here).
2. **Read `docs/results/phase9_results.md` §11.4 - §11.8** for the
   full investigation history (~1000 lines). Skim §11.7 - §11.8 for
   the current state.
3. **Read `docs/results/phase9_morning_report.md`** for the
   condensed version.
4. **Look at what `scripts/phase9_anes_target_builder.py` does** to
   understand how the ANES respondent data becomes the per-decade
   .npy target files.
5. **Look at the kwargs in `abm/pillars/historical_arc.build_engine`**
   — there are 8+ Tier-D-era kwargs, all default-off, all wired up
   and tested.

### Quickest win (15 min)

Add `tier_d_ic_sigma` kwarg (§6.1) and re-run the §11.7 config with
`tier_d_ic_sigma=0.35`. Should close the 1980-IC-too-wide gap
without breaking anything downstream because IC dispersion
narrowing reduces seed compression in later decades. Expected: §11
gate passes both old and ANES bands; w2 drops further; var_y_2020
might creep up to 0.16-0.18.

### Medium win (1 hour)

Add `tier_d_ic_sigma` + bump `ELITE_DRIFT_SCHEDULE` per §6.2.
Sweep 9 cells (ic_sigma × drift_rate) at 5 seeds. Find best
combination. Expected: w2 drops below 1.1 vs ANES; var_y_2020
approaches 0.20 (~70% of empirical).

### Architectural win (3-4 hours)

Implement `IdentityToPosition` rule per §6.3. This is the
literature-faithful path that decouples var_y from the noise vs
corr trade-off. Expected: var_y AND corr both improve simultaneously
because identity dynamics carry both.

---

## 9. Files at a glance

| Path | Purpose |
|---|---|
| `abm/pillars/historical_arc.py` | Historical-arc scenario, kwargs, event handlers |
| `abm/rules/noise.py` | `GaussianNoise` rule, now with optional `sigma_y` |
| `abm/rules/cohort_replacement.py` | `CohortReplacement` rule, now with y-sign fix gate |
| `abm/calibration_phase9.py` | Wasserstein scorer + shape descriptors |
| `scripts/phase8f_lib.py` | §11 measurement, NEW + OLD band sets |
| `scripts/phase9_anes_target_builder.py` | Rebuilds targets from Vlad's ANES data |
| `data/phase9_empirical/derived/` | Vlad's ANES processing outputs |
| `data/phase9_empirical/phase9_empirical_*.npy` | Per-decade target KDEs / pointclouds (now ANES-derived; synth backup in `synth_backup/`) |
| `docs/results/phase9_results.md` | Full investigation log §11.4 - §11.8 |
| `docs/results/phase9_morning_report.md` | Condensed report |
| `docs/specs/phase9_raw_data_sources.md` | URLs for ANES/GSS/CCES/Voteview raw data |
| `docs/specs/phase9_elite_faction_data.md` | URLs for elite/faction caucus data |
| `docs/research/phase9_axis_symmetry_audit.md` | The original Tier-D-motivating audit |
| `docs/research/phase9_axis_ratios.md` | Per-lever literature ratios |
| `docs/specs/phase9_tier_d_spec.md` | Tier D implementation spec |

---

## 10. The single sentence

**Goal**: make the engine produce 2D agent clouds at each decade
endpoint that look like real ANES.
**Status**: shape gap is now ~33% closed in w2 terms (1.81 → 1.22);
within-party SD gap mostly closed (51% → 81% of empirical); var_y
and corr gaps remain at ~50-70% of empirical.
**Next move**: narrower IC dispersion + more aggressive ElitDrift
schedule (§6.1, §6.2), then if still short, add an
IdentityToPosition rule (§6.3).
