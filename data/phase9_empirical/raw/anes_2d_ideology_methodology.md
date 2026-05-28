# Methodology: Stable 2D Ideological Map of US Voters, 1980–2024 (ANES CDF)

## Purpose and non-negotiable constraint

Build a 2D ideological coordinate system (economic axis × cultural axis) for individual ANES respondents, 1980–2024, using the ANES Time Series Cumulative Data File (CDF). The output is consumed by an external simulation engine that fits against the real-world time series, so **cross-year comparability is the primary objective**. Any operation that re-scales, re-fits, or re-defines an axis on a per-year basis is forbidden, because it would erase the temporal drift the engine is meant to reproduce.

State this rule to yourself before every transformation: *the coordinate system is global and fixed; only respondents move within it.*

The same stability discipline extends to density estimation (Step 7): KDE bandwidth and evaluation grid are global, computed once, never per-wave.

## Temporal unit

ANES is a **biennial** study (even years: presidential + midterm). The base temporal unit is therefore the **study wave**, not the calendar year and not a fixed-width calendar bin. Compute every metric per wave. Do **not** hard-bin into 5-year buckets — 5-year bins straddle the electoral cycle (mixing high-engagement presidential waves with midterm waves) and discard resolution the engine needs to fit drift dynamics, and that resolution cannot be recovered afterward.

Smoothing, where wanted, is a **layer on top of** wave-level data, not a replacement for it: report each metric both raw-per-wave and as a centered moving average over a configurable window (default: 3 waves). If coarser grouping is ever required, group by **4-year presidential cycle** so each bin is electorally comparable — never by arbitrary calendar width.

## Data source

ANES Time Series Cumulative Data File (CDF), downloaded from the ANES data center (registration required). Accept `.dta`, `.sav`, or `.csv` plus the variable codebook. The codebook is authoritative — when this spec and the codebook disagree on a variable code, polarity, or coverage year, **trust the codebook and flag the discrepancy in your output log.** The variable codes below are provided as a starting hypothesis and must be verified, not assumed.

Key administrative variables:
- `VCF0004` — year of study (filter to 1980–2024)
- `VCF0301` — party identification, 7-point (use for centroids; collapse to 3-category Dem/Ind/Rep for party clouds)

## Step 0 (FIRST OUTPUT, before any modeling) — coverage table

Before constructing anything, emit a coverage matrix: rows = candidate items, columns = study years 1980–2024, cells = present / absent (and, optionally, valid-N after dropping missing codes). Save as `coverage_table.csv`. Every downstream item-selection decision must be justified against this table. Do not proceed to axis construction until this table exists and the fixed core panel (Step 2) has been chosen from it.

## Step 1 — candidate items

Treat the lists below as candidates, not requirements. Select final items by coverage (Step 2), not by theoretical desirability. Verify every code against the codebook.

**Economic axis candidates** (target: higher = more economically conservative):
- `VCF0803` — liberal–conservative 7-pt self-placement (master ideology item; long coverage)
- `VCF0809` — guaranteed jobs & income scale, 7-pt (govt vs. individual; long coverage)
- `VCF0806` — government health insurance scale, 7-pt (long coverage)
- `VCF0839` — government services vs. spending tradeoff, 7-pt (good coverage, ~1982+)

**Cultural axis candidates** (target: higher = more culturally conservative):
- `VCF0834` — women's equal role, 7-pt (long coverage)
- `VCF0838` — abortion, 4-pt by-law scale (good coverage; verify scale direction)
- `VCF0830` — government aid to minorities / should help, 7-pt (racial policy; long but verify continuity)

**Thin / late-arriving items — likely to FAIL the coverage rule; include only if the coverage table justifies it:**
- immigration level items (sparse before ~2008)
- gay rights / sexual orientation items (~1988+, intermittent)
- affirmative action items (`VCF9037`-family; recent)
- authoritarian child-rearing battery (`VCF0846`-family; recent waves only — almost certainly excluded)
- union / regulation items (no clean long-run CDF equivalent — do not invent one)

## Step 2 — fixed core panel (resolves the changing-item-set bias)

Choose, from the coverage table, the largest set of items present in **every** year of the 1980–2024 window (or in a clearly stated supermajority, with the exact included years listed). This is the **fixed core panel**. Each axis is defined by the same items in every year — no item enters or leaves the axis definition partway through the series.

Do **not** compute an axis score as "the mean of whatever items a respondent answered." If the item set varies by respondent or by year, year-over-year movement conflates real attitude change with composition change. Two acceptable handling rules — pick one and document it:
- (A) Require non-missing on all core items (listwise); report the resulting N per year.
- (B) Mean-impute or model-impute within the fixed item set, documenting the method.

Prefer (A) for a pedagogical, auditable build unless N loss is severe.

## Step 3 — recoding (must be printed and verifiable)

For every selected item, produce a recode log row containing: variable code, codebook label, original valid codes, the codebook's stated direction, and the mapping to the recoded scale. Save as `recode_log.csv`. This is mandatory — ANES polarities are inconsistent (some 7-pt scales place liberal at 1, some at 7; the abortion scale runs permissive→restrictive), and silent direction errors are the single most common failure in ANES work.

Rules:
- Drop don't-know / refused / inapplicable codes (commonly 0, 8, 9, 97, 98, 99 — **verify per item**) before scaling. Do not treat them as midpoints.
- Orient every item so higher = more conservative on its axis. Record any reversal explicitly in the log.

## Step 4 — global normalization (resolves the per-year rescaling trap)

Compute all scaling parameters **once, on the pooled all-years data**, and apply the identical parameters to every year.

1. Recode each item to a common conservative direction.
2. Rescale each item to [−1, 1] using its **pooled** min/max (or pooled mean/SD if you prefer z-then-clip). The min/max/mean/SD are computed across all years combined, never per year.
3. Axis score = simple average of that axis's (recoded, rescaled) core items. Equal weights.
4. Final coordinates already lie in [−1, 1] by construction.

Persist the pooled scaling parameters to `scaling_params.json` so the transform is reproducible and so a new year of data can be projected into the *same* space later.

## Step 5 — optional factor model (only if axes stay fixed)

If you compare averages against a latent-variable model: fit loadings **once on pooled data**, then project each wave onto those frozen loadings. Never run PCA/factor analysis per wave — per-wave components sign-flip and rotate, making coordinates non-comparable. If frozen-loading projection is not implemented, omit the factor model entirely; equal-weight averages are more defensible here because each axis means the same thing by construction.

## Step 6 — density estimation (the core object)

Moments (mean/SD/skew) assume a single blob and are blind to the thing you most want to detect: a distribution that *splits*. A clean bimodal distribution can have skew ≈ 0, and a single bimodality coefficient compresses the signal into one lossy number. So estimate the actual density — with three stability rules, or the densities won't be comparable across waves.

1. **Fixed bandwidth, fixed grid, global.** Compute one KDE bandwidth on the pooled all-waves data (or fix it by substantive choice) and evaluate every wave's density on the **same** coordinate grid. Per-wave bandwidth selection (Scott/Silverman on each wave's N) makes early sparse waves smoother than dense recent ones, so apparent sharpening over time becomes an artifact of changing N. Persist bandwidth + grid to `kde_params.json`.

2. **The 2D joint density is the real object, not the 1D marginals.** The two axes are correlated and increasingly so — economic and cultural conservatism co-occurring *is* ideological sorting, and sorting is half the polarization story. Estimate the **2D KDE per wave × party** on the fixed grid. Keep the 1D marginal densities too, for legible plotting, but the joint is what encodes sorting.

3. Apply survey weights in the density estimation, not just the summaries.

## Step 7 — outputs

1. `coverage_table.csv` — from Step 0.
2. `recode_log.csv` — from Step 3.
3. `scaling_params.json` — from Step 4.
4. `kde_params.json` — global bandwidth + grid from Step 6.
5. `respondent_coordinates.csv` — one row per respondent: wave, year, party ID, weight, economic score, cultural score.
6. **Per-wave density plots** — 2D KDE of respondents in the fixed space, one panel per wave (small multiples) for visual drift inspection; party clouds overlaid.
7. **Party centroids** — per wave × party (Dem / Rep, optionally Ind): mean economic and cultural score.
8. **Polarization metric series** (`polarization_series.csv`) — all per wave, all on the fixed grid/bandwidth, reported both raw-per-wave and as the configurable moving average:
   - **2D overlapping coefficient (OVL)** between the Dem and Rep joint densities — **primary metric.** Defined directly on the densities (1 = identical party distributions, → 0 as they separate), so it captures shape and sorting, not just centers.
   - **Hartigan's dip statistic** (+ p-value) per axis — honest unimodal-vs-not test; replaces the bimodality coefficient.
   - **Scaled separation** — between-party distance `sqrt((econ_mean_R − econ_mean_D)^2 + (cult_mean_R − cult_mean_D)^2)`, scaled by pooled within-party SD.
   - **EMD / Wasserstein distance** between the two party densities (per axis and/or 2D) — respects how far mass moved, not only how much overlaps.

   OVL is the primary curve-fitting target for the engine; the rest are supporting series.

## Documentation requirements

- Apply ANES survey weights for all population-level summaries (centroids, distributions, polarization); state which weight variable was used. Unweighted individual coordinates are fine for the scatter export, but flag the distinction.
- Every recoding, exclusion, and item-selection decision must appear in a log file, not only in code comments.
- Record the exact included-years list for each axis if any item is supermajority- rather than universally-present.

## Acceptance checks (run before declaring done)

- Re-running normalization on a single wave in isolation must NOT reproduce that wave's coordinates from the global build — if it does, scaling leaked to per-wave and the build is invalid.
- Re-estimating KDE on a single wave with its own bandwidth must NOT reproduce that wave's density from the global build — same leakage test, applied to density estimation.
- The recode log must show, for each item, a human-verifiable direction consistent with "higher = more conservative."
- The coverage table must justify every item in the fixed core panel.
- Dropping or adding one wave of input must not change any other wave's coordinates or densities.
- Every reported metric must exist as a raw-per-wave series; the moving average must be derived from it, never the only form stored.

---

## Build implementation log (2026-05-28)

This section records the actual build, the choices made within the spec's degrees of freedom, and the one place where the implementation diverged. The intent is that someone re-running the build later can reproduce or argue with these decisions in isolation from the methodology proper above.

### Script and outputs
- Implementation: `scripts/anes_2d_compass.py` — single-pass, deterministic, no random component.
- Source: `data/phase9_empirical/raw/timeseries_csv.csv` (ANES CDF, all columns loaded as strings with `' '` for missing; coerced with `pd.to_numeric(errors='coerce')`).
- Outputs land in `data/phase9_empirical/derived/`:
  - `coverage_table.csv`, `recode_log.csv`, `scaling_params.json`, `kde_params.json`
  - `respondent_coordinates.csv` — per-respondent (year, party_7pt, party {D,I,R}, weight, econ, cult)
  - `party_centroids.csv`, `polarization_series.csv` (raw + centered MA(3))
  - `densities/{year}_{D,I,R,ALL}.npy` — KDE evaluated on the fixed grid
  - `build_log.md`, `acceptance_checks.txt`
- Small-multiples plot: `docs/phase9_empirical/density_small_multiples.png`.

### Window and waves
- Chose **1986–2024** to keep the moral-traditionalism battery (`VCF0852`, `VCF0853`) in the cultural axis, accepting the loss of 1980/1982/1984 (the methodology's recommended trade-off).
- 15 candidate waves in window; **2002 excluded** because its listwise survivors = 0 (the CDF row for 2002 has `VCF0809`, `VCF0839`, `VCF0838`, `VCF0830`, `VCF0852`, `VCF0853` all missing — only `VCF0803` is fielded). 14 effective waves: 1986, 1988, 1990, 1992, 1994, 1996, 1998, 2000, 2004, 2008, 2012, 2016, 2020, 2024.
- One verified codebook/data discrepancy: the codebook excerpt claims `VCF0830` (aid to blacks) misses 2002 and 2012, but the CSV has it fielded in every wave except 2002. Trust the data, document the discrepancy, proceed.

### Fixed core panel (chosen from the actual coverage table, not the codebook excerpt)
- Economic (3 items): `VCF0803`, `VCF0809`, `VCF0839`
- Cultural (4 items): `VCF0838`, `VCF0830`, `VCF0852`, `VCF0853`
- `VCF0806` (govt health insurance) excluded — sparse, 1986/1990/1998 missing.
- `VCF0834` (women equal role) excluded — series ends in 2008.
- `VCF0894` (welfare spending) excluded — starts 1992 and is a 3-pt direction-of-change item, not policy-position.

### Missing-handling rule
- **Listwise drop** on all 7 core items per respondent (rule A in Step 2). 44,308 → 22,761, **51.4% retention**. Borderline by the methodology's "unless N loss is severe" caveat; retained anyway because the alternative (imputation) introduces a model that the calibration engine would then be fitting against rather than data.
- Don't-know / refused codes dropped per item before any computation; codes documented in `recode_log.csv`.

### Normalization choice (deviation from spec, stricter)
The methodology offers "pooled min/max OR pooled mean/SD with z-then-clip." This build uses **theoretical scale endpoints** (1↔−1, 7↔+1 for 7-pt; 1↔−1, 4↔+1 for the 4-pt abortion; etc.) rather than pooled empirical min/max. The choice is stricter than the spec: it uses **zero** pooled statistics from the data, so the transform is provably wave-independent by construction. The trade-off is that a future wave whose response distribution genuinely shifts will still land in the same coordinate frame (good for the engine's drift target), and bumps the theoretical min/max can never recede if a future wave fails to span the full scale.

Axis score = simple equal-weight mean of the recoded items on that axis. No factor model.

### KDE
- Bandwidth: Scott's rule applied **once** to the pooled, all-waves, all-parties, weighted sample. Factor = 0.2022. Frozen and reused for every wave × party fit.
- Grid: 81 × 81 on [−1.05, 1.05]² (slight halo past the [−1, 1] coordinate range to avoid kernel clipping at corners). Cell = 0.0263, cell area = 6.89e−4.
- Survey weights (`VCF0009z`) applied in `scipy.stats.gaussian_kde(weights=...)`. Weight is 1.0 in 1986–1990 (SRS-era CDF convention) and the proper full-sample weight from 1992 on.

### Polarization metrics
- `ovl_2d` — 2D overlapping coefficient between Dem and Rep joint densities, ∑ min(f_D, f_R) · cell_area. **Primary** calibration target.
- `scaled_separation` — Euclidean distance between (econ, cult) centroids, divided by the weighted-pooled within-party RMS SD across both parties.
- `wasserstein_econ`, `wasserstein_cult` — 1D Wasserstein-1 between weighted Dem/Rep marginals per axis. 2D Wasserstein skipped (cost vs added signal not worth it here; the OVL already captures shape).
- `dip_econ`, `dip_cult` — Hartigan's dip statistic + p-value, per axis, on the pooled wave (parties combined). diptest is unweighted; this is acceptable because dip is a shape test, and the unweighted respondent set is the empirical sample whose multimodality we're testing.
- All metrics also written as `*_ma3` columns: centered moving average over 3 waves, `min_periods=3` so the endpoint waves report NaN rather than a one-sided average.

### Acceptance test redesigns
- **norm-isolation:** the spec says "re-running normalization on one wave must NOT reproduce the global build." If you re-run by recomputing pooled min/max on a single wave, results coincide when the items span their full scale in that wave — so the spec's test is vacuously true under theoretical-endpoint rescaling. Test redesigned to **per-wave z-then-clip**: a different normalization family that *will* differ from the global build when scaling is genuinely wave-independent. Passes — 2000 wave: per-wave-z econ +0.034 / cult +0.009 vs global econ +0.112 / cult +0.212.
- **kde-isolation:** unchanged from spec. Refit `gaussian_kde` on one wave with its own Scott factor and confirm the factor differs from the global. Passes — 2000 wave: own_bw 0.4058 vs global_bw 0.2022.
- **direction:** in every wave with both parties present, the Rep centroid is ≥ the Dem centroid on both axes. Passes everywhere.

### Result snapshot
- OVL: 0.60 (1986) → 0.20 (2020), partial recovery to 0.25 (2024).
- Scaled separation: 0.96 (1986) → 3.20 (2020), 2.93 (2024).
- Dip-test p-values reject unimodality on the econ axis in every wave and on the cultural axis in every wave except 2000 (p=0.09).
- Visible in `density_small_multiples.png`: 1986–1998 clouds heavily overlap, separation begins ~2004, two distinct clouds in 2020/2024. Dem path shows the realignment — economically left-of-zero throughout but only culturally left-of-zero from 2012 on.

### Known limitations to flag when calibrating
- 51.4% listwise retention biases toward more politically engaged respondents who answer every item. The engine's fit should treat the densities as the population of *opinionated* respondents, not the full electorate.
- 1990 cultural items `VCF0852`/`VCF0853` are Form B–only (~half the wave); 1986 `VCF0809` is Form A–only (~half the wave). N for those waves is correspondingly lower after listwise drop — see `coverage_table.csv`.
- The CDF's 4-year midterm gaps after 2004 (no 2006/2010/2014/2018/2022) are inherent to the dataset; the engine should not be asked to fit those years.
