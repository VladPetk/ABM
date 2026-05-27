# Phase 8f §3 — Blind-Spot Metrics Audit

*Companion to `phase8f_spec.md §3`. Walks each aggregate metric the
historical-arc scenario reports, decomposes into components,
verifies achievable ranges under the current mechanism inventory,
documents any hidden ceilings, and flags small fixes vs Phase 8g+
structural items.*

*Motivation: the Phase 8f investigation found a structural ceiling
on `ideological_constraint` (the y-axis was inert at ~0.20 because
party centers were placed only on the x-axis). That kind of hidden
ceiling is exactly what an audit catches before it becomes a
six-month miss.*

---

## Audit format (per metric)

Each entry follows:

```
### <metric>
Definition: <what it computes>
Decomposition: <component split>
Achievable range under current mechanisms: <span>
Hidden ceilings flagged: <any>
Three-party behaviour: <semantics under party=2>
Verdict: stable | small-fix-here | 8g+ structural
```

---

## 1. `variance` (positional spread)

- **Definition**: `np.var(positions, axis=0).sum()` — sum of per-axis variance across the population.
- **Decomposition**: two components, `var_x + var_y`. The Phase 8f §3 small-fix `variance_per_axis()` returns each component separately.
- **Achievable range**: with x ∈ [-1, 1] and y ∈ [-1, 1], theoretical max is `2.0` (uniform spread on both axes). The empirical pre-§8f y-axis was inert at noise level (~0.20) so total variance had a hidden ceiling at `var_x_max + 0.20 ≈ 0.6` for tightly-sorted x-axis. §8f.1's y-axis party bias (±0.08) unblocked this: the y-axis can now span ~0.20-0.30 across the trajectory.
- **Hidden ceiling flagged (was)**: y-axis dispersion inert pre-§8f.1; *fixed by combo_JJ*.
- **Three-party behaviour**: Independents have broader N(0, 0.4) initial position → contribute extra variance. Phase 8e §1 widened the variance band [0.08, 0.20] to accommodate. Honest under three-party.
- **Verdict**: **small-fix-here** (added `variance_per_axis` decomposer). No structural issue remaining.

## 2. `ideological_constraint` (party-issue correlation)

- **Definition**: `(|Pearson r(party, x)| + |Pearson r(party, y)|) / 2` averaged across the two axes.
- **Decomposition**: `(cx + cy) / 2` where cx, cy are per-axis between-party correlations. The Phase 8f §3 small-fix `ideological_constraint_per_axis()` exposes both components.
- **Achievable range**: each component bounded in [0, 1]. Both axes can in principle reach the empirical 0.65-0.75 band. Pre-§8f.1: cy was structurally pinned at ~0.20 (noise) because party centers had y-component = 0. Maximum constraint achievable = `(0.92 + 0.20)/2 = 0.56` — the constraint plateau.
- **Hidden ceiling flagged (was)**: cy structural inert; *fixed by §8f.1 y-axis bias*. Post-fix: 2025 constraint reaches 0.75 (in band).
- **Three-party behaviour**: filtered to party ∈ {0, 1} per Phase 8d §4 — Independents excluded. No distortion under three-party. The exclusion is a metric semantics choice (Phase 8d) documented in methods.md §4.5.
- **Verdict**: **structural fix from §8f.1 already landed**; small-fix (per-axis exposed) now too. No remaining issue.

## 3. `party_separation` (partisan centroid distance)

- **Definition**: `||mean(positions[party==0]) - mean(positions[party==1])||` — Euclidean distance between partisan centroids.
- **Decomposition**: x-component + y-component of the centroid-difference vector. The empirical literature anchor (DW-NOMINATE divergence) is x-axis only.
- **Achievable range**: in [0, 2*sqrt(2)] ≈ [0, 2.83]. Under modern partisan sort, ~0.8 is achievable in the model.
- **Hidden ceiling flagged**: none — both components have agency.
- **Three-party behaviour**: filtered to party ∈ {0, 1} by construction (the function indexes `[parties == 0]` and `[parties == 1]`). Independents excluded automatically. Phase 8d documented the literature-faithful side-effect: partisans drift inward via BC + media interactions with Independents, slightly widening the magnitude undershoot. Phase 8f §1.1 PartyPull=0.07 + ELITE_DRIFT reshape addresses this; 2025 sep now 0.80 ± 0.01 (in band [0.68, 0.82]).
- **Verdict**: **stable** post-8f.1.

## 4. `affective_polarization` (out-party warmth mean)

- **Definition**: mean over all `affect[other_party]` entries across the population, clipped to [-1, 1].
- **Decomposition**: per-agent out-party warmth. Aggregate scalar; no axis decomposition. Per-party subaggregation possible (mean Dem warmth toward Reps vs mean Rep warmth toward Dems) but currently not reported.
- **Achievable range**: [-1, 0] (post-Phase 5 sign fix; warmth is monotonically negative under the negative-going valence path). Empirical band [-0.85, -0.20]; achievable.
- **Hidden ceiling flagged**: clip at -1.0 (the affect floor) means agents pinned at the floor stop contributing dynamics — but the diagnostic shows 75% of agents are at floor by S4-end (Phase 8e §5.4 affect-gate firing-rate). For 8f.1's `baseline=0.0` (no per-encounter floor), the trajectory cools more gently — slower approach to -1.0 — so the clip-pinning effect is mitigated.
- **Three-party behaviour**: Independents have no `affect` dict (Phase 8d) → excluded from the mean. Three-party-honest.
- **Verdict**: **stable**. Per-party subaggregation (Dem warmth vs Rep warmth) could be a Phase 8g+ enhancement if asymmetric findings are wanted.

## 5. `within_party_sd` (per-party SD on x-axis)

- **Definition**: mean of `positions[party==0, 0].std()` and `positions[party==1, 0].std()` — per-party x-axis position SD, then averaged.
- **Decomposition**: per-party (Dem SD, Rep SD). Currently averaged but components could be reported separately.
- **Achievable range**: 0 (perfectly sorted within-party) to ~0.5 (broad cohort). Empirical 0.15-0.22 band.
- **Hidden ceiling flagged**: pre-§8e.3 was structurally compressed by `MediaConsumption`'s single-attractor pull at the partisan diet target. Fixed by §8e.3 (per-agent `media_cue`) at modest σ=0.15; lifted further by §8f.1 (`MEDIA_CUE_SIGMA=0.40`).
- **Y-axis component**: NOT currently reported (within_party_sd is x-axis only). With §8f.1's y-axis party bias, y-axis within-party SD is also non-trivial. **Routine documentation note**: methods.md could add a y-axis sibling metric in a future polish phase. Defer to 8g (not blocking).
- **Three-party behaviour**: Independents excluded (loop iterates `for p in (0, 1)`). Honest under three-party.
- **Verdict**: **stable** post-8f.1; y-axis SD reporting is a Phase 8g+ optional enhancement.

## 6. `cross_cutting_tie_fraction` (any-pair)

- **Definition**: fraction of network edges where the two endpoints have different `party` attributes (any pair: 0-1, 0-2, 1-2 all count as cross-cutting).
- **Decomposition**: by partisan-partisan vs partisan-Independent. The Phase 8e §1 `partisan_cross_cutting_fraction` is the partisan-only submetric.
- **Achievable range**: [0, 1]. Empirical literature anchor: Mutz 2006 / ANES estimates of cross-cutting discussion-partner exposure ~0.30-0.40 under three-party.
- **Hidden ceiling flagged (was)**: pre-Phase 8d "binary band [0.15, 0.25]" was apples-to-oranges with three-party measurements. *Fixed by §8e.1 — band re-banded to [0.30, 0.45] under three-party; new `partisan_cross_cutting_fraction` submetric for apples-to-apples binary comparison.*
- **Three-party behaviour**: documented in methods.md §4.5 + phase8e_targets.md.
- **Verdict**: **stable** post-§8e.1.

## 7. `partisan_cross_cutting_fraction` (Phase 8e §1 — new)

- **Definition**: `cross-cutting / partisan-partisan-edges` (Independent-involving edges excluded entirely from numerator AND denominator).
- **Decomposition**: a single ratio, partisan-only.
- **Achievable range**: [0, 1]. Empirical anchor [0.15, 0.25] under modern partisan-only network.
- **Hidden ceiling flagged**: none.
- **Three-party behaviour**: by construction, excludes party=2 entirely; bit-identical to `cross_cutting_tie_fraction` at `independent_fraction=0.0`. Tested in `test_phase8d_independents.py::test_partisan_cross_cutting_fraction_*`.
- **Verdict**: **stable**.

## 8. `party_modularity` (Newman Q under party partition)

- **Definition**: `sum_c (L_c / m - (D_c / 2m)^2)` — Newman modularity treating each party as a community.
- **Decomposition**: per-party (L_c, D_c contributions). The Phase 8d Independents add a third community.
- **Achievable range**: [0, ~0.5] for typical network structure. Empirical anchor ~0.32-0.45 under binary; ~0.20-0.40 under three-party (8e §1 widening).
- **Hidden ceiling flagged**: third-party community lowers measured modularity vs binary. *Documented in 8e §1; band widened.*
- **Three-party behaviour**: counts party=2 as its own community → numerator and denominator both reflect three-way structure. Defensible.
- **Verdict**: **stable**.

## 9. `sorting_index` (Mason 2018 mega-identity)

- **Definition**: mean over identity dimensions of |Pearson r(party, identity_dim)|. Measures how well party predicts each non-political identity.
- **Decomposition**: per-dimension r. Currently averaged.
- **Achievable range**: [0, 1] per dimension; aggregate in [0, 1]. Empirical band ~0.40-0.70 under Mason mega-identity.
- **Hidden ceiling flagged**: dimensions where the partisan identity-bias is zero will contribute zero correlation; if all dimensions are zero-mean per the build, expected sorting_index is driven by the `identity_bias_1980 = 0.20` constant in `historical_arc.py` and the IdentitySorting rule's `differentiation` parameter. Both can move the metric; achievable.
- **Three-party behaviour**: filtered to party ∈ {0, 1} (Phase 8e §1). Independents excluded. Honest under three-party.
- **Verdict**: **stable**.

---

## Summary table

| Metric | Decomposition | Hidden ceiling? | Three-party? | Verdict |
|---|---|---|---|---|
| variance | x + y | y was inert pre-§8f.1 | ✓ widened band | **fixed + small-fix** |
| ideological_constraint | x + y | y was inert pre-§8f.1 | ✓ partisan-only | **fixed + small-fix** |
| party_separation | x + y | none | ✓ partisan-only | stable |
| affective_polarization | scalar (per-agent) | clip at -1 noted | ✓ excludes party=2 | stable |
| within_party_sd | per-party (x only) | media-attractor (§8e.3) | ✓ partisan-only | stable; y-axis 8g+ |
| cross_cutting_tie_fraction | scalar | pre-§8e binary band wrong | ✓ re-banded | stable |
| partisan_cross_cutting_fraction | scalar | none | ✓ by construction | stable |
| party_modularity | per-community | three-party lowers Q | ✓ widened band | stable |
| sorting_index | per-dimension | none | ✓ partisan-only | stable |

---

## Small fixes landed in 8f.3

1. **`variance_per_axis(positions)`** — `abm/metrics/polarization.py`. Returns
   `{"x": var_x, "y": var_y}`. Aggregate `variance()` unchanged.
2. **`ideological_constraint_per_axis(agents)`** — `abm/metrics/affective.py`.
   Alias-friendly wrapper around `ideological_constraint()` that
   makes the explicit component-split visible to callers. Functionally
   equivalent (returns the same dict).

Both small-fixes are non-behavioural — they expose existing
decompositions for transparency. Pillar bit-identity unaffected
(no rule reads these new functions).

## Items deferred to Phase 8g+ (not blocking)

- **Per-party affective polarization** (Dem-toward-Rep mean vs Rep-toward-Dem mean) — asymmetric finding visibility.
- **`within_party_sd_y`** — y-axis within-party dispersion (currently x-only). Now meaningful post-§8f.1 y-axis bias.
- **`sorting_index_per_dimension`** — per-identity-dim component visibility (currently averaged).

None of these are structural; they're component-visibility enhancements that didn't surface as load-bearing in the current empirical comparison.

---

## What this audit prevents

The y-axis-constraint-plateau structural miss in the Phase 8f
investigation took ~70 variants × ~30s/variant to identify in
post-hoc diagnostic. With per-axis decomposition functions
available from build-day, a single `ideological_constraint_per_axis()`
call would have surfaced the cy ~ 0.20 inert pattern in seconds
during any standard run. The blind-spot audit format here is
designed to catch the *next* structural miss before it requires a
70-variant investigation.

Future metric additions should ship with their component
decompositions documented in this format.
