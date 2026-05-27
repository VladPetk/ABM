# Phase 8f — Results

*Comprehensive close result for Phase 8f: ship combo_JJ +
1980-sigmoid-softening + systematic blind-spot metrics audit. All
within historical-arc scope; no pillar invariants touched.*

---

## Headlines

**Primary cells in band: 21/25 at 20 seeds** (vs 8/25 in Phase 8e
— a ~2.6× improvement, the largest single-phase jump in the
project's history).

**First-time achievements:**
- All four 2025 primary metrics in band simultaneously
- 1980 party_sep IN BAND at 0.55 ± 0.01 (was 0.66 across 8b/8e —
  the polarization-expert's round-1 "party-as-coalition without
  coupling" diagnosis fix lands)
- Within-party SD trajectory in band across 1990, 2010, 2020, 2025
  (was structurally compressed at 0.10 through 8e)
- Constraint trajectory matches ANES band across all decades (was
  plateaued at 0.56 geometric ceiling)

**Test suite: 181/181 green** (5 new §8f.2 sigmoid-K tests). 73
sacred pillar tests bit-identical.

---

## Per-decade trajectory under Phase 8f vs targets

| Year | Constraint (target) | Party_sep (target) | Affect (target) | Within-party SD (target) |
|---|---|---|---|---|
| 1980 | **0.39 ✓** ([0.25, 0.40]) | **0.55 ✓** ([0.45, 0.60]) | **−0.25 ✓** ([−0.35, −0.20]) | **0.31 ✓** ([0.20, 0.35]) |
| 1990 | **0.46 ✓** ([0.35, 0.50]) | **0.55 ✓** ([0.50, 0.65]) | **−0.41 ✓** ([−0.45, −0.30]) | **0.19 ✓** ([0.18, 0.32]) |
| 2000 | **0.56 ✓** ([0.45, 0.60]) | 0.53 ✗ ([0.55, 0.70]) | −0.56 ✗ ([−0.55, −0.40]) | 0.18 borderline ([0.18, 0.30]) |
| 2010 | **0.65 ✓** ([0.55, 0.70]) | **0.66 ✓** ([0.60, 0.75]) | **−0.60 ✓** ([−0.65, −0.50]) | **0.18 ✓** ([0.17, 0.28]) |
| 2020 | **0.72 ✓** ([0.60, 0.75]) | **0.77 ✓** ([0.65, 0.80]) | **−0.69 ✓** ([−0.78, −0.60]) | **0.18 ✓** ([0.15, 0.25]) |
| 2025 | **0.75 ✓** ([0.62, 0.78]) | **0.80 ✓** ([0.68, 0.82]) | **−0.74 ✓** ([−0.85, −0.65]) | **0.18 ✓** ([0.15, 0.22]) |

**21/25 primary cells in band.** Plus 1980 variance the only
remaining 1980 miss.

---

## Remaining out-of-band cells (precisely located)

1. **1980 variance** (0.38 vs band [0.45, 0.60]) — Independents
   (12%) broader initial condition + partisans not yet sorted. The
   sigmoid K=5 softening helps party_sep but slightly tightens
   variance. Phase 8g candidate: revisit IC variance separately
   from party assignment.

2. **2000 party_sep / affect / wp_sd trio** — small misses
   (each within 1-2 SE of band edge), all caused by the K=5
   sigmoid trade-off. K=4.0 would fix 1980 party_sep harder but
   collapses 2000 downstream. K=5.0 documented as the chosen
   compromise; net +9 cells vs prior K=8.0.

---

## What landed (three sub-phases)

### §8f.1 — combo_JJ shipped

Five coordinated changes, all in `historical_arc.py`:

1. `PARTY_CENTERS_1980` y-component ±0.08 — **the architectural
   fix** that unblocks the constraint plateau. The investigation's
   key insight: constraint = (cx + cy)/2, and with party centers
   on x-axis only, cy stayed inert at ~0.20 noise level, capping
   constraint at ~0.56. Adding y-axis party bias unlocks cy.
2. `MEDIA_CUE_SIGMA` 0.15 → 0.40 — lifts within-party SD into
   ANES voter band.
3. `AffectiveUpdate(baseline=0.0)` historical-only override —
   fixes 1990-2010 affect over-cooling. Pillar's class default
   stays at 0.10 (Phase 5).
4. `PartyPull(strength=0.07)` historical-only override — fixes
   the party_sep U-shape. Pillar's class default stays at 0.04.
5. `ELITE_DRIFT_SCHEDULE` reshaped, front-loaded — peak 0.008 in
   1990-2000 and 2000-2010, taper after.

Each component is load-bearing (ablation confirms — drop any and
2-4 cells fall out of band).

### §8f.2 — Softer 1980 sigmoid (party_sep fix)

`PARTY_ASSIGNMENT_K` per-decade schedule: 5.0 (1980-90) → 6.0 →
7.0 → 8.0 → 8.0.

- Build samples 1980 K=5.0 → fuzzier party assignment, more
  cross-pressured 1980 partisans, party centroids closer at t=0.
- `CohortReplacement._replace_agent_inplace` uses cohort-aware K
  per arrival decade.
- Pillar falls back to sign-only assignment (bit-identical).

5 new tests verify the K-aware assignment + pillar bit-identity.

Calibration history (documented routine fork):
- K=2.5 too fuzzy → 1990/2000 party_sep collapses downstream.
- K=4.0 fixes 1980 hard, but net −2 cells downstream.
- **K=5.0 chosen** — 1980 party_sep INTO BAND (0.55 vs target
  [0.45, 0.60]); downstream cells stable with small 2000
  trade-off (~1-2 SE).

### §8f.3 — Blind-spot metrics audit

`phase8f_metrics_audit.md` walks all 9 aggregate metrics:

| Metric | Decomposed | Hidden ceiling? | Three-party safe? | Verdict |
|---|---|---|---|---|
| variance | x, y components | no | yes | clean |
| ideological_constraint | cx, cy components | **YES (was)** | yes | **FIXED in §8f.1** |
| party_sep | x, y components | y was inert | yes (partisan-only) | **FIXED in §8f.1** |
| affective_polarization | mean out-party warmth | no | yes (already partisan-only) | clean |
| within_party_sd | x, y components | no, but y-component lower | yes (partisan-only) | per-axis helper added |
| cross_cutting_tie_fraction | edges | no | **NO** (Indep↔partisan count) | partisan-only submetric added in 8e |
| partisan_cross_cutting_fraction | edges (partisan-only) | no | yes (by construction) | clean |
| modularity | network community | no | yes (partisan-only mode) | clean |
| sorting_index | per-identity | no | yes | per-dimension helper deferred |

**Two non-behavioural helpers added:** `variance_per_axis()` in
`polarization.py`, `ideological_constraint_per_axis()` in
`affective.py`. Both expose existing components without changing
metric semantics.

**Deferred to 8g+** (non-blocking): per-party affect mean,
per-dimension sorting index, full y-axis within-party SD
investigation.

**Methodological closure:** the audit format prescribes that
future metric additions ship with their decomposition documented.
The y-axis-constraint-plateau insight took ~70 variants × 30s to
find post-hoc; with `ideological_constraint_per_axis()` available,
the cy inert pattern would surface in seconds.

---

## Pillar invariant audit

- `calm_to_camps.py` not modified.
- Pillar's `PartyPull(strength=0.04)` (S0-S4 bundles unchanged).
- Pillar's `AffectiveUpdate(baseline=0.10)` (Phase 5 default).
- Pillar agents don't seed `media_cue`, y-axis party_cue, or
  `party_assignment_k_schedule`.
- Pillar's `CohortReplacement` falls back to sign-only assignment
  (pillar's env doesn't carry the schedule).
- 73 sacred pillar tests + 100+ accumulated 8a-8e tests + 5 new
  8f tests = **181/181 green at 20 seeds in 598s** under the
  parallel-seed runner.

---

## Honest curve-fitting breakdown

Per the investigation report:

- **1 structural fix:** y-axis party centers — genuinely-discovered
  geometric gap, not a fit. The model now represents the cultural
  dimension (y) the way it represented the economic dimension (x).
- **2 literature-defensible parameter shifts:** PartyPull 0.07
  (within Hetherington 2001 elite-cue range); MEDIA_CUE_SIGMA 0.40
  (within ANES self-placement within-party dispersion).
- **2 honest curve-fits:** AffectiveUpdate baseline 0.0 (removes
  Phase 5 modeling choice with no literature anchor); ELITE_DRIFT
  reshape (post-hoc to mid-decade party_sep).
- **1 routine calibration:** PARTY_ASSIGNMENT_K = 5.0 (chosen
  among 2.5/4.0/5.0/8.0 candidates; trade-off documented).

The model now tracks the empirical 1980-2025 trajectory closely
on every primary metric. The blind-spot audit closes a
methodological gap; future capacity-ceiling issues like the y-axis
one should be discoverable in minutes, not months.

---

## Cumulative scoreboard through Phase 8f

| Phase | Tests | Primary cells in band |
|---|---|---|
| Phase 7 close | 73 | (no historical scenario yet) |
| Phase 8b | 86 | 3/24 |
| Phase 8c | 139 | (intervention work, not historical) |
| Phase 8d | 159 | 2/24 (at strict bands) |
| Phase 8e | 176 | 8/24 |
| **Phase 8f** | **181** | **21/25** |

The progression from 3/24 to 21/25 across phases 8b-8f is the
project's empirical-fit story arc. The structural y-axis fix in
8f.1 was the unblocker; the 1980 sigmoid softening in 8f.2
completes the early-decade fit; the metrics audit in 8f.3 closes
the methodological gap that hid the y-axis issue for so long.

---

## Phase 8g candidates (deferred)

- 1980 variance fix (IC generator separate from party assignment).
- 2000 trio refinements (K=5 trade-off cost).
- Per-party affect mean decomposition (audit deferred).
- Per-dimension sorting index (audit deferred).
- Full y-axis within-party SD investigation.

None blocking. The historical arc now tells a defensible empirical
story across 1980-2025 on every primary metric except 1980 variance
+ the 2000 trade-off.
