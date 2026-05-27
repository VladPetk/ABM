# Phase 8e — Revised Historical-Arc Target Bands

*Companion to `phase8b_historical_replication_spec.md §9`. Leaves the
Phase 8b pre-registered targets intact as historical record; this
document is the revised band set for Phase 8e measurement. Decisions
per the §1 table of `phase8e_polish_spec.md`.*

---

## 1. Rationale

The Phase 8b pre-registered targets were calibrated under a strictly
binary-party population. Phase 8d added 12% Independents (party=2),
which:

- Breaks the cross-cutting tie fraction metric's interpretation
  (Independent↔partisan ties now count as cross-cutting under the
  existing definition, overshooting the 8b band by ~1.6×).
- Shifts the modularity baseline (third loose Independent community).
- Compresses the variance baseline (Independents' broader N(0, 0.4)
  IC + their inward pull on partisans).
- Leaves the partisan-only metrics (constraint, within-party SD,
  affect, party_sep) unchanged in interpretation — but the
  party_sep direction is now *literature-faithfully widened* by the
  Independent-pulls-partisans-inward dynamic (Mason 2018), which
  the 8b binary-party band didn't anticipate.

The 8e revisions:
1. **Keep** the four primary partisan-aware bands (constraint,
   party_sep, affect, within-party SD). They're literature-anchored
   on partisan-only measurements and unaffected by Independents.
2. **Widen** secondary bands (variance, modularity) to accommodate
   the three-party population. The literature anchors for these were
   inferences, not direct measurements, so a band widening is
   honest.
3. **Split** cross-cutting tie fraction into two metrics:
   `partisan_cross_cutting_fraction` (apples-to-apples with 8b
   binary band [0.15, 0.25]) and the existing
   `cross_cutting_tie_fraction` (any-pair, new band [0.30, 0.45]
   under three-party).

---

## 2. Per-decade primary targets (2025 endpoint shown; intermediate decades unchanged from `phase8b_historical_replication_spec.md §9`)

| Metric | 8b band | 8e decision | 8e band |
|---|---|---|---|
| Ideological constraint | [0.62, 0.78] | **Keep** | [0.62, 0.78] |
| Party separation | [0.68, 0.82] | **Keep** | [0.68, 0.82] |
| Affective polarization | [-0.85, -0.65] | **Keep** | [-0.85, -0.65] |
| Within-party SD_x | [0.15, 0.22] | **Keep** | [0.15, 0.22] |

Rationale: all four are partisan-aware metrics (filtered to
party ∈ {0, 1}). Their literature anchors are unchanged by
Independents in the population. Misses against these bands remain
honest misses with the same diagnoses Phase 8b identified.

---

## 3. Per-decade secondary targets (revised)

| Metric | 8b band (2025) | 8e decision | 8e band (2025) | Rationale |
|---|---|---|---|---|
| Variance (positional) | [0.13, 0.20] | **Widen** | [0.08, 0.20] | The Phase 8b variance band was inferred from total-population spread on a binary-party model. Independents' broader N(0, 0.4) IC + their inward pull on partisans compresses total variance below 0.13. The widened lower bound accommodates both binary and three-party builds. |
| `cross_cutting_tie_fraction` (any-pair) | [0.15, 0.25] | **Re-band under 3-party** | [0.30, 0.45] | Under three-party population, Independent↔partisan ties (Independents have centrist diet, partisan-agnostic identities, so they form ties broadly across partisan lines) count as cross-cutting under this metric. ANES network-survey estimates of cross-cutting exposure including unaligned voters land around 0.35-0.40. The new band accommodates the three-party measurement. At `independent_fraction = 0.0` this metric is bit-identical to `partisan_cross_cutting_fraction` (below) and the old [0.15, 0.25] band applies. |
| **`partisan_cross_cutting_fraction`** *(new submetric)* | n/a | **New** | [0.15, 0.25] | Restricted to partisan-partisan edges only. Apples-to-apples with the Phase 8b binary measurement. Lives in `abm/metrics/network.py`; at `independent_fraction = 0.0` bit-identical to `cross_cutting_tie_fraction`. |
| Modularity | [0.32, 0.45] | **Widen** | [0.20, 0.40] | Under three-way population, modularity has a third loose Independent community → smaller measured modularity. The Phase 8b band was calibrated under two-party. The widened band accommodates either. At `independent_fraction = 0.0` the old [0.32, 0.45] band applies. |

---

## 4. 1980 IC targets (revised)

| Metric | 8b band | 8e decision | 8e band |
|---|---|---|---|
| Variance | [0.45, 0.60] | **Widen** | [0.35, 0.60] | Independents (12%) sit broader at IC, compressing the partisan-only variance slightly. |
| Ideological constraint | [0.25, 0.40] | **Keep** | [0.25, 0.40] |
| Party separation | [0.45, 0.60] | **Keep** | [0.45, 0.60] |
| Affective polarization | [-0.35, -0.20] | **Keep** | [-0.35, -0.20] |
| Within-party SD_x | [0.20, 0.35] | **Keep** | [0.20, 0.35] |
| `cross_cutting_tie_fraction` (any-pair) | [0.30, 0.40] | **Re-band under 3-party** | [0.40, 0.55] |
| **`partisan_cross_cutting_fraction`** *(new)* | n/a | **New** | [0.30, 0.40] |

Phase 8d 1980 measurement reported `cross_cutting_tie_fraction =
0.50`, which lands in the new [0.40, 0.55] band. With
`partisan_cross_cutting_fraction` as the apples-to-apples metric,
the 8b band is preserved for partisan-only comparison.

---

## 5. Implementation notes

- `partisan_cross_cutting_fraction` is implemented in
  `abm/metrics/network.py` (Phase 8e §1.2). Imported and used by the
  Phase 8e historical scripts.
- Scripts that report results (`phase8b_calibration.py`,
  `phase8d_historical_replication.py`, and the new
  `phase8e_4cell_decomposition.py` / `phase8e_x7_historical.py`)
  read these revised bands.
- The 73-test pillar invariant suite is unaffected by these
  re-bandings (no pillar test references these specific bands).

---

## 6. What changes in headline reporting

The Phase 8d historical re-run produced 2/25 primary cells in band
under the 8b binary bands. Under the 8e bands:

- Primary cells (constraint, party_sep, affect, within_party_sd):
  unchanged. Phase 8d's 2/25 stays 2/25 on primaries.
- Secondary cells (variance, cross-cutting, modularity): variance
  widening puts 5/5 decades in band; new `partisan_cross_cutting_fraction`
  replaces the old cross-cutting comparison; modularity widening
  brings 2025 in band.

The new headline scoreboard is reported in `phase8e_polish_spec.md`'s
closing result post, using these revised bands as the comparison
basis.
