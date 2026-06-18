# Engine peer-review audit — polarlab

**Date:** 2026-06-17
**Canonical build audited:** `abm/pillars/historical_arc.py` → `build_engine`, preset `anes_full`, seed 0
(`ANES_FULL_KWARGS` = endogenous loop + econ + cultural common-mode). Git `5d2886f`.
**Method:** fresh-eyes, multi-agent peer review (39 agents across 9 review streams +
adversarial verification of every major/critical finding + synthesis). Deliberately did
**not** rely on the ~300-test suite, the `docs/internal/audit/` trail, or the `validation/`
scripts as ground truth — under the project's *measure-then-bless* discipline those mostly
confirm outputs did not *change*, not that they are *correct*. Where a finding is marked
"verified directly" it was re-checked against the live code/data by the report author, not
just by the audit agents.
**Scope (as agreed):** engine mechanisms + forcings, an independent model-vs-ANES fit
battery, and the data pipeline/leakage. Web-demo presentation honesty was **out of scope**.
**Status:** findings + prioritized fix plan only. **No engine changes were made.** Fixes are
a separate decision per item (several trigger re-bless cascades).

---

## Verdict

The **engineering is sound and the literature spine is genuinely solid** — the delta
pipeline, Friedkin–Johnsen damping, RNG-stream integrity, and the core mechanism
implementations are correct, and the load-bearing citations (Pettigrew–Tropp, Mason, the
ANES thermometer, DW-NOMINATE) check out with the strongest extrapolation honestly E-tagged.

But the **central scientific claim — that US positional polarization *emerges* from the
model's dynamics — is not earned by the evidence**, and the headline/status layer overstates
emergence, fidelity, and "resolution" relative to the project's *own* honest measurements.
This is a **disclosure-and-framing failure at the surface layer, not hidden corruption**:
almost every weakness is already documented two docs deeper, and the honest numbers already
exist in-repo — they simply were not propagated to the surfaces a reader sees first. As a
referee: **major revisions to the claims (not the code) required** before it can be presented
as more than a *calibrated illustration*.

The good news and the indictment are the same sentence: the fixes are overwhelmingly
re-labeling and re-blessing, not re-engineering.

---

## The six peer-review questions, answered

**1. Are the mechanisms lit-grounded and faithfully implemented?**
Mostly yes — the *code* does what the docstrings say, and the empirical spine is real. But
two mechanisms are weaker or directionally *opposite* to their literature framing:
- `BoundedConfidenceInfluence` — the rule carrying the headline Hegselmann–Krause citation
  and the "who you listen to" stage — is a **near-no-op in the shipped arc** (turning it off
  moves 2025 separation by ~3%). It is load-bearing only in the *pillar's* S1 isolation
  stage. (Downgraded by the verifier from major→minor: the demo never surfaces "bounded
  confidence" to the public, so the overclaim is internal to `methods.md`, not public-facing.)
- `MediaConsumption` is **net de-polarizing (centripetal) on the position axis** — the
  opposite of the Levendusky/DellaVigna–Kaplan/Martin–Yurukoglu papers it is cited to.
  Partisan diet targets sit *inward* of party centroids (Dem |target| 0.08 vs |centroid|
  0.28 @2025), so "partisan media" mechanically pulls toward center; a clean ablation shows
  media ON *reduces* party-axis separation by ~0.20. The model's polarizing-media effect
  lives only on the **affect** axis (`MediatedAnimus`), not the positional channel.

**2. What is the model fit, on metrics the author didn't foreground?**
The combined `party_sep` fit is good, but it **hides a per-axis mis-allocation**: the model
over-produces *cultural*-axis separation and slightly under-produces *economic*, giving a
cult/econ gap ratio ≈1.0 vs ANES ≈0.66 — inverting the empirical fact that the US sorted
*more* on economics. Independent recompute: mean |cultural error| 0.132 vs |economic error|
0.056 (2.3×). The per-axis gap is an unconstrained degree of freedom the combined fit cannot
see, because the activist→elite→mass loop amplifies along a single frozen axis and welds
cultural timing to economic timing. (The related "within-cloud econ-cult correlation ~0.8 is
unrealistic" claim was **refuted** — the repo's own raw ANES shows endpoint corr ≈0.75, so
the model matches it.)

**3. Do external inputs make sense, or do they silently feed the answer / create artificial fit?**
This is the most damaging finding. **The fit is largely fed, not earned**, on the quantities
that matter most:
- `party_sep`: the activist-mobilization schedule that paces the endogenous loop is
  **ABC-fit directly to the ANES `party_sep` curve it claims to explain** (`mob_base/peak/
  backload/asym`, weighted 1.0 in `e4_fit.py`). The live `honesty_budget.json` says
  `free_flowing 0.279 / empirical_input 0.721` — only **~28% is the loop's spontaneous
  floor; ~72% is supplied by the fitted forcing.** The model's own four-cut holdout fails
  the **temporal** cut specifically and only on `party_sep`.
- Econ + cultural **center-of-mass** are **~100%-fed rigid snaps** (CommonModeEconomic with
  `relax=1.0` snaps the partisan econ COM to `economic_mood_offset(year)` each tick; output ≈
  input to 3 dp) — and they are **deliberately excluded from the honesty budget** because
  they're "sorting-invariant," so the most directly-fed results have **zero entry** in the
  fed-vs-emergent ledger whose headline reads as completeness. Blindspot #9's "64% error cut"
  is mechanical, not emergent.

**4. Do the data sources and processing make sense?**
The sources are appropriate (ANES VCF cumulative, GSS 7224) and the recodes are reproducible.
The problem is **circularity + leakage**: a single ANES recode (`respondent_coordinates.csv`)
simultaneously (a) anchors calibration, (b) defines the §11 bands the model is scored
against, and (c) builds the Wasserstein targets — so the §11 "cells-in-band" tally and
`w2_total` are **goodness-of-fit, not validation; the scorecard cannot falsify the model**.
And the `validation/anes_from_raw.py` harness that advertises itself as "independent from the
existing pipeline" actually **re-implements the identical recipe and reproduces the derived
CSV to 5e-05** — a re-execution, not an independent check (blind to systematic construct
choices like placing the master ideology item purely on the economic axis).

**5. What is the model really capturing vs what it's presented as capturing?**
It establishes a **mechanism** (an activist→elite→mass amplification loop *can* convert a
small latent cleavage into large party separation) and that **affective polarization is the
one genuinely emergent quantity** (~94%, because affect has no anchor and a monotone-cooling
floor). It does **not** establish the **timing or magnitude** of US polarization — those ride
forcings fit to the answer. Presented as "positional sorting emerges / blindspot #7
RESOLVED"; the honest statement is **"mechanism endogenous, timing/magnitude calibrated."**

**6. Is it just a sorting model — are there forces that bring people together?**
**Substantially yes — and this is the most important structural finding.** The shipped
baseline is a **one-way ratchet**: every live rule is divergent/sorting or off-axis; the one
endogenous convergence force (`BoundedConfidenceInfluence`) is inert *and* converges only
*within* camps; out-party affect can only **cool** endogenously (the `AffectiveUpdate`
warming branch needs cooperative edges the baseline never seeds — **dead code**);
depolarization exists **only** as externally-imposed resets (X6; X5 is now null/null). So the
model encodes "polarization is a ratchet" as a substantive, contestable empirical claim —
*implicit in which rule strengths are zero*, never stated as a top-level falsifiable
assumption. Classic drivers are absent or neutralized: geography→position feedback, material/
economic conditions, candidate agency, and the **asymmetric** (Republican-led) shift the
literature finds — the latter forced to symmetry by the loop's frozen ±axis.

---

## Findings by severity

Status legend: **verified** = adversarial skeptic confirmed; **verified directly** =
re-checked against live repo by report author; **downgraded/refuted** = the adversarial layer
corrected the original reviewer.

### Critical / major (validity-affecting)

| # | Finding | Status | Evidence |
|---|---------|--------|----------|
| F1 | **Fit is fed, not earned** — ~72% of the `party_sep` rise rides an ANES-shape-fit mobilization forcing; the holdout fails the temporal cut on exactly this metric | **verified directly** | `honesty_budget.json` free_flowing 0.279/0.721; `e4_fit.py` party_sep weight 1.0; `e5_holdout.md` temporal cut fail |
| F2 | **Circular calibrate-and-score** — one ANES recode (`respondent_coordinates.csv`) sets the knobs AND the §11 bands AND the Wasserstein target; the scorecard cannot falsify the model | verified (critical→major) | `phase8f_lib` band derivation; `ANES_PRIMARY_TARGETS`; same recode in KDE targets |
| F3 | **Flagship affect output is 0/5 in band** at every decade; `methods.md` still claims "all five in band" | **verified directly** | `realism_measurement.json` A4 all `in_band:false`; 2025 −0.809 vs band [−0.71,−0.51]; `methods.md:939` |
| F4 | **Stale-favorable headlines invert the honest numbers** — `CLAUDE.md` "18/24, 1.00 emergent"; actual **15/24 (FAILS the ≥18 gate)** + **0.28 emergent / 0.72 fed** | **verified directly** | `realism_measurement.json` A2 `n24=15, pass=false`; `honesty_budget.json`; blindspot #7 vs the JSON it cites |
| F5 | **Structural one-way ratchet** — baseline cannot endogenously depolarize; the assumption is hidden in zeroed knobs | verified | 135-tick census: 0 endogenous warming ticks; warming branch is dead code; only X6 helps |
| F6 | **MediaConsumption is net de-polarizing** on the position axis, opposite the cited polarizing-media literature | verified | ablation: media ON sep 0.643 vs OFF 0.841; diet targets inward of centroids |
| F7 | **Econ + cultural COM are ~100%-fed rigid snaps**, excluded from the honesty budget, yet booked as resolved blindspots | verified | CommonModeEconomic `relax=1.0`, output≈input to 3dp; budget `_provenance` "does not track" |
| F8 | **Affect has no saturation in the canonical build**; raw warmth runs off-scale to −1.27 (extreme −6.03; ~60% off-scale by 2025), hidden by clip-on-read | verified | `affective.py:47` clip; `AffectiveUpdate.saturation=0.0` under `evidence_regrade`; MediatedAnimus unsaturated |
| F9 | **Per-axis mis-allocation** — model over-produces cultural vs economic separation (cult/econ ≈1.0 vs ANES ≈0.66); single-axis loop welds the two | verified | recompute |cult err| 0.132 vs |econ err| 0.056 (2.3×); seeds correct 1986 ratio then drifts to parity |
| F10 | **I3 "enforced by test" is misadvertised** — the lint only AST-walks arc event handlers, missing `shocks.py` + `cultural_common_mode.py` which actually write outcomes | verified | lint scans `arc.__file__` `_event_/_decade_` only; shocks self-flags "I3-flagged outcome write" |
| F11 | **"Independent from-raw" harness re-uses the calibration recode** (reproduces to 5e-05) | verified | `validation/anes_from_raw.py` same 7 VCF items/flags; 5e-05 = rounding floor |
| F12 | **"~69% cohort replacement"** licensing the cultural channel's L/emergent tag is a **non-identified APC self-computation**; cited papers report 33–55% | verified | `gss_cohort.py` OLS X=[1,birth,year] omits age (age=year−birth collinear); Brooks-Bolzendahl 55%, Baunach ≈33% |

### Selected minors (downgraded or unverified, worth knowing)

- **F13** Dated historical events do **not** net-drive separation — removing them *raises*
  final `party_sep` (no-events 1.116 vs full-arc 1.084). The demo's event-driven narrative
  diverges from the engine's actual driver (the smooth mobilization curve). *(unverified)*
- **F14** Common-mode channels **bypass FJ/stubbornness** (rigid direct writes) — a
  documentation inconsistency with "FJ at apply-site of every ideology-moving rule." *(verified, minor)*
- **F15** `cohort_replacement` leaks the prior occupant's `social_coord` onto the new agent. *(unverified)*
- **F16** Stale doc/registry strings: `calibration.py` thermometer "within ~5%" model_check
  (retracted in §3.1); `MediatedAnimus` docstring "0.21→0.41" (shipped 0.20→0.33);
  `CLAUDE.md` still lists deleted `ProtectedPartyRealignment` + claims `IdentityAlignment`
  ships (replaced by `MeasuredAlignment`); `ArgumentExchange` dead in both tracks. *(unverified)*
- **F17 (REFUTED)** "Within-cloud econ-cult correlation ~0.8 is unrealistic" — the repo's own
  raw ANES shows endpoint corr ≈0.75 (`realism_measurement.json` B2), so the model matches
  it. The real issue is the *gap-ratio* mis-allocation (F9), not the correlation.

### Positive controls (what is sound — reported so the negatives are scoped fairly)

The empirical **spine is genuinely literature-grounded** (Pettigrew–Tropp r=−0.21 / 515
studies, cited exactly with the strongest extrapolation honestly E-tagged; ANES thermometer
~48°→~20°; Mason mega-identity; DW-NOMINATE ~0.4-unit elite divergence all check out). The
**delta pipeline snapshots/sums/applies synchronously and FJ damping is applied exactly once
at every apply-site**; the character-protection removal is RNG-stream-safe (the bit-identical
fingerprint is legitimate). Weaknesses concentrate in the **newest common-mode/forcing
machinery and the headline layer**, not the core or the spine.

---

## Prioritized fix plan

Grouped by purpose. Effort and re-bless risk noted. **None of these were applied.**

### Must-fix for validity / honesty (mostly zero engine risk)

- **P1 — [small] Reconcile every headline number to the live shipped config, one pass.**
  `CLAUDE.md` → 15/24 (not 18/24) and `party_sep` 0.28 emergent / 0.72 fed (not 1.00/~0);
  blindspot #7 → lead with free_flowing ≈0.28, drop "~0% input-carried"; update stale
  38/62 → 28/72 in #7 and `methods §5.29`. **Stop using `loop_attributable=1.00` as a
  synonym for emergent.** *No re-bless, no shipped-number change.* (Addresses F4, F1.)
- **P2 — [medium] Stop reporting §11 cell tally + `w2_total` as fidelity.** Relabel as
  "calibration recovery / goodness-of-fit (scored against the same recode that set the
  knobs)"; promote the genuinely held-out checks (GSS instrument cut, temporal holdout, Pew
  overlap, per-issue) to carry validation — *including honestly stating the temporal cut
  fails on `party_sep`.* (Addresses F2, F11, F1.)
- **P3 — Correct the affect claims and decide affect's status. (NOW SCOPED — see
  [validation/audit/affect_recal_verdict.md](../../validation/audit/affect_recal_verdict.md).)**
  Two options, both ready to go:
  - **(a) Recalibrate [small code change + large cascade].** A sweep on the canonical config
    confirms `affect_lr ×0.25–0.30 + saturation re-enabled (1.0) + MediatedAnimus ×0.4` takes
    affect **0/5 → 3/5** in band and the scorecard **15/16 → 19/24 (PASS the ≥18 gate)**, with
    **zero** collateral on the position metrics (affect is cleanly downstream — verified across
    3 sweeps). The fix is honest: it *undoes an over-shoot* — re-enabling the `saturation`
    decelerator that `evidence_regrade` wrongly retired. Caveats: 1990/2000 stay ~0.01 below
    the narrow early bands (saturation-limited; true 5/5 needs an early-specific lever — warmer
    1980 seed or lower early coupling); and the effective LR is below the build-time clip floor
    `[0.001,0.03]`, so that floor must be lowered too (one extra line). Cascade: re-run
    `realism_battery` → re-bless affect golden tests → **re-measure `phase10`** (interventions
    are scored on the affect axis — buckets may move) → re-export web (`cc-data.js`) →
    `honesty_budget` → docs.
  - **(b) Relabel [docs only, no cascade].** State affect is 0/5 vs grounded bands on the
    shipped config, register affect-too-cold as a first-class blindspot, stop counting affect
    toward the headline, re-bless `realism_report` A4 text.

  **Assessment:** (a) is feasible, clean, and flips the project's own gate from FAIL to PASS —
  recommended when a cascade is acceptable; (b) is the honest interim otherwise. (Addresses
  F3, F8, the affect side of F6.)
- **P4 — [small] Put the econ + cultural COM into the honesty budget** as explicit
  ~0%-emergent / ~100%-fed lines (or a prominent caveat); downgrade the econ channel's
  mechanism provenance **L→N** (E on amplitude), the cultural channel's **magnitude L→N**
  (keep L-in-direction). State #9's "64% error cut" is mechanical. (Addresses F7, F12.)
- **P5 — [small] State the one-way-ratchet as a top-level falsifiable assumption** in
  `methods.md`/`README` and add it as an explicit blindspot: no endogenous depolarizing
  channel; BC convergence is within-camp; out-party affect is monotone-cooling (warming only
  via exogenous injection); X5/X6 are imposed resets. Justify against the model's own #5
  (cross-national depolarizing cases) or mark as a scope boundary. (Addresses F5.)

### Honesty / presentation

- **P6 — [small] Fix the media framing** at the rule/intervention level (not just §5.14):
  on the position axis partisan media is modeled as **centripetal**; the polarizing-media
  effect is carried only by `MediatedAnimus`. Note dated events net-**brake** separation.
  (Addresses F6, F13.)
- **P7 — [small] Soften the I3 and BC/HK claims.** "I3 enforced for arc event handlers;
  typed input channels (shocks, common-mode) exempt by convention" (or broaden the lint with
  an allowlist). Note BC's per-tick arc contribution is ~3% (load-bearing only in pillar S1)
  and the shipped graded+affect BC path is an N/E extension whose HK test covers only the
  `temperature=0` reduction. (Addresses F10, BC finding, F14.)

### Nice-to-have / fairness

- **P8 — [medium] One cleanup pass over stale registry/doc strings + dead code** (F16):
  `calibration.py` thermometer string; `MediatedAnimus` docstring number; deleted-rule +
  `IdentityAlignment` caveats in `CLAUDE.md`; mis-cited cultural-gradient source; deprecate/
  remove `ArgumentExchange`; verify the Treier–Hillygus axis-correlation target (~0.21 vs
  paper ~0.30).

---

## Open questions (author's calls — these change what the fixes do)

1. **Validation philosophy.** Implement a genuine out-of-sample test (fit knobs on a subset
   of ANES waves, score the complement; or fit on ANES, score the *same quantities* on GSS),
   or accept that §11/`w2` are recovery checks and lean validation entirely on the held-out
   GSS/Pew/per-issue cuts? *This single decision determines whether the model can claim more
   than "calibrated illustration."*
2. **Affect.** *(Now scoped — P3a is feasible/clean/PASS, see the verdict note.)* Re-calibrate
   (P3a, full re-bless, changes shipped numbers) or re-label as a known over-animus
   extrapolation (P3b)? And: do you want the *published* affect metric to reflect the true
   unsaturated dynamics (add in-state saturation) or keep the clip-on-read and disclose it?
3. **Emergence claim scope.** Retitle blindspot #7 from "RESOLVED — positional sorting
   emerges" to "mechanism endogenous, timing/magnitude calibrated (28% emergent floor)"?
4. **Structural scope.** Is the one-way ratchet (no endogenous depolarization) an intended
   permanent scope boundary for a US-1980→2025 teaching artefact, or a deferred to-do?
5. **Single-axis loop.** Build the parked axis-decoupling / asymmetric-feedback loop (#6/#10)
   so per-axis gaps and the asymmetric-Republican-shift signature can be represented, or
   foreground that the emergent engine is single-axis and welds cultural to economic timing?
6. **Center-of-mass provenance.** Accept the L→N downgrades and report the non-identified APC
   split with its dropped-age caveat + a second-constraint sensitivity?
7. **Acceptance gate.** The shipped config is 15/24 vs the stated ≥18/24 gate, with no
   enforcing test. Lower the gate with justification, add a CI gate at the true value, or
   document explicitly why a below-gate config was accepted as canonical?

---

## Method, caveats, and limits of this audit

- 39 agents, 9 review streams, adversarial verification of all 29 major/critical findings,
  one synthesis pass. Raw findings + verdicts: `validation/audit/_findings.json`; compact
  table: `validation/audit/_findings_table.txt`; fit-battery scratch + plots:
  `validation/audit/`.
- **The audit is not infallible.** It is itself a model of the model. Minor/observation
  findings (F13, F15, F16, etc.) were *not* adversarially verified — treat as leads. The
  fit-battery numbers may be single-seed where noted; re-run on the ensemble before acting on
  a borderline per-axis claim.
- **Web-demo presentation was out of scope** — several fixes (P1, P3, P6) may also touch the
  web honesty panel / `cc-data.js`; check and re-repack if so.
- The adversarial layer **changed verdicts** (BC major→minor; econ-cult-correlation refuted),
  which is evidence the verification did real work rather than rubber-stamping.
