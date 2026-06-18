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

## CRITICAL UPDATE — the 5-seed fit + budget overturn the fed→earned premise

The 3-seed A6 was optimistic. At **5 seeds** the frontier (`recal_fit.py`) is:

| config | §11 ANES | affect | party_sep | 2025 sep |
|---|---|---|---|---|
| current shipped | 17/24 | 0/5 | 4/5 | 1.082 |
| **corrections only (no mob cut)** | **20/24** | **3/5** | 4/5 | 1.117 |
| + 30% mob cut | 20/24 | 2/5 | 4/5 | 1.072 |
| + 40% mob cut | 19/24 | 2/5 | 3/5 | 1.049 |

**Finding 1 — the corrections carry the whole win.** Fixing the media DIRECTION
(R5 part A) + the affect mechanism (R7 rest + P3a recal) lifts §11 17→20/24 and
affect 0→3/5 with **no forcing cut at all** — real fixes to two audit blindspots
(F6 wrong-direction media; the affect 0/5).

**Finding 2 — fed→earned does NOT work, and measurement proves it.** The honesty
budget (`recal_budget_check.py`, party_sep free_flowing) across the frontier:

| config | final sep | all-frozen floor | emergent % |
|---|---|---|---|
| canonical | 1.082 | 0.574 | 35% |
| corrections only | 1.119 | 0.570 | 33% |
| + 30% cut | 1.077 | 0.570 | 35% |
| + 40% cut | 1.050 | 0.570 | 36% |

Cutting the mob forcing 40% moves the emergent fraction only 33→36%. **Why: the
all-frozen "emergent" floor freezes EVERY external driver including media, and
media penetration is itself a FED forcing (`data_fed_media`). So R5's centrifugal
media shifts sorting from one forcing (mobilization) to another (media) —
forcing→forcing, not forcing→emergent.** The frozen-1980 loop floor (~0.57) is
unchanged by the mob cut; cutting only lowers the *forced* top, costing per-decade
sep fit and affect (3→2) for ~zero honesty gain.

**Consequence — blindspot #7 is NOT resolvable by R5.** The positional rise is
structurally forcing-driven (the dark-matter finding: the 1980 seed cannot
self-organize to 2025 sorting). The honest stance: keep the drivers as *realistic
forcings routed through mechanisms* (mob→loop→PartyPull; media→diet→
MediaConsumption) — which they are — and report the emergent fraction truthfully
(~33%), NOT pretend the rise is emergent. R5 part A (media direction) is still a
real bug-fix; R5 part B (fed→earned) is **abandoned as measured-not-to-work**.

## DIGGING ON EMERGENCE — R8 (endogenous mobilization) + the definitive cap

Per the user's "keep digging on emergence," built **R8** — endogenous
self-mobilization in the activist→elite→mass loop: a party's own sorting feeds its
mobilization (`mob_eff = mob_exo + endo_mob_gain·max(0, cent·dir)`), the empirically
real polarization spiral (Mason 2018). This is the RIGHT fed→earned mechanism (vs
R5's media, which is itself fed). It reads the *unfrozen* sorting state, so it
self-sustains when the budget freezes the fed drivers → it genuinely raises the
emergent (free_flowing) fraction.

**It works — and measurement maps the exact cap.** Frontier (5-seed §11 + 2-seed budget):

| endo_mob_gain | §11 ANES | party_sep cells | emergent % |
|---|---|---|---|
| 0.00 (corrections only) | 19/24 | 4/5 | 33% |
| **0.15** | **18/24 PASS** | 4/5 | **39%** |
| 0.25 | 17/24 FAIL | 3/5 | 56% |
| 0.35 | 13/24 | 2/5 | 55% |
| ≥2.0 | (runaway) | — | >100% (ignites to ceiling) |

**The definitive finding: fit-compatible emergence caps at ~39%.** A positive-
feedback spiral is bistable (quiescent vs ignite-to-ceiling); the tunable middle
exists, but past endo≈0.15 the spiral FRONT-LOADS polarization and breaks the
per-decade §11 fit — because **US polarization's TIMING is exogenously event-paced
(Gingrich/Fox/Trump), not a spontaneous spiral.** So the magnitude *can* be made
emergent (R8 reaches the endpoint at any gain), but matching the US *trajectory
shape* requires external pacing. This QUANTIFIES and EXPLAINS blindspot #7: the
forcing-carried share is structural (it encodes the real event timing), not a
fixable flaw. The honest ceiling on emergence-with-fit is ~39%, up from ~33%.

## Final re-cal recommendation: CORRECTIONS + R8@0.15

Adopt R5 media-direction + R7 rest + P3a (affect_lr_scale 0.30 + saturation 1.0) +
mild R1 + **R8 endo_mob_gain 0.15** (no mob cut): §11 **18/24 PASS**, affect ~2-3/5,
sep 4/5, **emergent fraction 33→39%** — fixes the media + affect blindspots AND
ships the genuine (data-supported) self-reinforcement, with #7 honestly quantified
(cap ~39%, timing exogenous). Then the re-bless cascade + honest docs. (R8 stays a
tunable knob; the cap is the headline finding.)
