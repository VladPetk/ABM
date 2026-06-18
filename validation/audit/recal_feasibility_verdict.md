# Joint re-calibration — feasibility probe verdict (NOT a fit/bless)

Ran `validation/audit/recal_feasibility_probe.py` (3 seeds) to confirm the joint
re-cal targets are reachable with the R-phase corrections on, BEFORE the expensive
full ABC fit + re-bless cascade. Scored on the REAL §11 ANES bands. Engine
untouched; canonical bit-identical.

## Results

| candidate | §11 ANES | affect cells | party_sep cells | 2025 sep |
|---|---|---|---|---|
| A0 canonical | 16/24 | 0/5 | 4/5 | 1.081 |
| A1 affect-fix (R7+P3a+mild R1) | 17/24 | 1/5 | 4/5 | 1.074 |
| A2 + R5 media | 17/24 | 1/5 | 4/5 | 1.116 |
| A3 + mob cut 20% | 17/24 | 1/5 | 4/5 | 1.093 |
| **A4 + mob cut 40%** | **20/24 PASS** | 2/5 | **5/5** | 1.053 |
| A5 (harder affect) + cut 40% | 20/24 PASS | 2/5 | 5/5 | 1.055 |

(3-seed, so A0 reads 16 vs the 5-seed 17 — noise, not drift.)

## Verdict: FEASIBLE — proceed to the full fit

**Q1 (affect ⊥ position) — confirmed.** The affect fix (R7 rest + P3a `affect_lr_scale`
+ mild R1 contact) warms 2025 affect −0.827 → −0.68 (into the 2025 band) with
party_sep essentially unchanged (1.081 → 1.074) — affect is orthogonal to the
position metrics on the live arc, as the audit predicted. No §11 damage.

**Q2 (fed→earned) — confirmed, and stronger than expected.** With R5 media now
centrifugal (carrying real positional sorting), cutting the **mob_\* forcing 40%**
(A4) doesn't just hold §11 — it **improves it to 20/24 PASS** with party_sep
**5/5 in band**. Less forcing, same trajectory ⇒ the mechanisms carry more of the
rise. This is the central honesty win (emergent fraction up); the full budget
number gets measured properly in the re-cal.

**Affect ceiling ≈ 2/5 with current knobs; ~3/5 needs the saturation lever.**
Pushing P3a/rest/contact harder (A5) does not add affect cells beyond 2/5 — the
narrow early-decade bands (1990/2000) are the binding constraint, exactly as the
earlier affect recal found (`affect_recal_verdict.md`: 3/5 required re-enabling
`saturation`, which is not yet a build knob). So the full fit needs **one small
extra prereq — a `saturation` (or affect-shape) build knob** — to reach 3/5; the
2025/2010/2020 cells already land.

## What the full re-cal should do (de-risked)

1. **Prereq:** add a `saturation` build knob (affect-shape) for the early-decade
   affect cells — the only remaining build lever (P3a `affect_lr_scale` + R7 done).
2. **Fit (parsimonious):** mob_\* (cut ~40%, fed→earned) + elite_gain + party_pull/fj
   + P3a (affect_lr_scale, saturation) + R7 (rest rate/anchor) + R1 (mild contact)
   + media_centrifugal. Fix R2/R3/R4/R6 near-off (counterfactual capacity, not
   shipped brakes) — only R5/R7/P3a/mild-R1 are active in the shipped arc.
3. **Targets:** §11 ≥18 (20/24 shown reachable), affect ≥3/5, party_sep in band
   (5/5 shown), per-axis ratio, holdout cuts, emergent-fraction ↑ (the 40% cut).
4. **Then:** flip canonical → full suite → re-bless cascade → G2 + falsification.

The expensive fit + irreversible re-bless are justified: the joint targets are
demonstrably reachable, and fed→earned delivers.

## Update — saturation knob added → A6 hits all targets (the re-cal candidate point)

Added the `affect_saturation` build knob (overrides the build's 0.0-under-regrade).
Candidate **A6** = mob cut 40% + R5 media + R7 rest (rate 0.02, anchor −0.30) + P3a
(affect_lr_scale 0.30, **saturation 1.0**) + mild R1 contact:

| | §11 ANES | affect cells | party_sep cells | 2025 affect | 2025 sep |
|---|---|---|---|---|---|
| current shipped | 17/24 | 0/5 | — | −0.83 | 1.08 |
| **A6 (3-seed)** | **21/24 PASS** | **3/5** | **5/5** | −0.579 | 1.055 |

A6 **beats the current shipped config on every axis** (§11 17→21, affect 0→3/5,
sep fully in band) *while forcing the arc 40% less* (fed→earned). The saturation
lever delivered the 3rd affect cell exactly as the earlier recal predicted. This
is the re-cal candidate point — a light local fit around it (multi-seed) selects
the adopted point, then the re-bless cascade. Canonical bit-identical.
