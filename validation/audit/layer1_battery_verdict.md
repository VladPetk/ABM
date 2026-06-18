# Layer-1 generic validation gate (G1) — baseline verdict

Ran `validation/audit/layer1_battery.py` (seed 0; NOT a bless) to establish the
mechanism layer's generic behaviour **before** the R-mechanisms are finished.
This is the de-circularization gate (audit F2): the mechanism layer judged on
directional criteria across regimes, **not** on US ANES bands. Engine untouched;
canonical bit-identical.

## Baseline result (R1+R2 only; R3–R6 not built; R2 not yet retargeted)

| Cell | forcing | restoring | 2025 party_sep | 2025 affect |
|---|---|---|---|---|
| C1 polarizing | high | off | **1.065** | **−0.834** |
| C2 resisted | high | strong | 1.072 | −0.515 |
| C3 neutral | **off** | off | 0.236 | −0.767 |
| C4 depolarizing | sweden | strong | 0.776 | −0.440 |

**G1 = 1/4 criteria pass.** rise PASS · flat FAIL · reverse FAIL · order FAIL.

## The key finding — the two axes have OPPOSITE Layer-1 deficiencies

Zeroing the exogenous forcing (C3: `mob_*`=0, common-modes off, dated events off
— the loop mechanism intact but unmobilized) splits the two channels cleanly:

- **Position has a rest state but no emergence and no restoring.**
  `party_sep` with forcing off ends at **0.236** (Δ −0.054 vs the 1980 seed ~0.30)
  — it does *not* run away. So the positional rise to 1.065 is **~entirely
  forcing-carried** (the 72%-fed honesty-budget number, now shown generically and
  independently). And under strong restoring it does *not* come down: C2 sep
  (1.072) ≥ C1 sep (1.065) — R1+R2 have **zero positional traction** (R2 damps
  `ConstraintOp`, but `party_sep` is `PartyPull`/loop-driven). → G1-order fails on
  sep; G1-reverse fails. **Fix: R2→PartyPull retarget + R4/R5/R6.**

- **Affect has dynamics but no rest state.**
  With *zero* drivers, out-party warmth still cools to **−0.767** (Δ −0.621),
  nearly as cold as full-forcing C1 (−0.834). `AffectiveUpdate`'s negative valence
  fires unconditionally on out-party ties → affect spirals to near the floor with
  no equilibrium. This is the "engine over-produces animus" blindspot, shown
  generically: a neutral society with no polarizing drivers should not reach −0.77.
  R1 (contact warming) is the correct mechanistic counter-force (C2/C4 affect are
  much warmer, and the affect *ordering* C1<C2<C4 is already correct) — it gives
  affect a two-sided dynamic. → G1-flat fails on affect. **Fix: R1 + the affect
  recalibration P3a (give affect a rest state, not just a slower cool).**

## Reading it against the three-layer contract

This is exactly the diagnostic the tripartite framing predicts:
- **Mechanism layer (L1) is incomplete on BOTH axes** — position lacks an
  emergent generator *and* a restoring force; affect lacks an equilibrium. A valid
  general model should rest flat with no drivers and be able to reverse under
  restoring conditions. It currently does neither.
- The positional rise is **forcing-carried** (L2), confirming the central audit
  finding from a fully independent angle (generic regimes, not the §11 recode).

## What each remaining R-mechanism must move (measured against this gate)

- **R2-retarget → PartyPull/loop gain**: should make C2 sep < C1 sep (restoring
  gains positional traction) → G1-order on sep.
- **R4 (BC revival) + R5 (media fed→earned) + R6 (thermostatic)**: should let C4
  peak-then-decline → G1-reverse; R5 additionally raises the *emergent* fraction
  of the positional rise (lets mechanisms generate what forcing now carries).
- **R1 + P3a**: give affect a rest state → C3 affect Δ within tolerance → G1-flat.
- **G1-ablation** (per-mechanism sign test) runs once R3–R6 land.

Thresholds in `layer1_battery.py` / spec §4 are pre-registered but provisional
(lock at AGREE). The point of pre-registering: they can't be slid to fit.

---

## Update — after the R2 retarget (PartyPull damping) → G1 2/4

Extended cross-pressure damping to `PartyPull` (the actual `party_sep` driver),
driven by the same `xpressure_sorting_damp` knob (so R2 now damps both sorting
rules; ConstraintOp kept). Canonical seed-0 2025 endpoint **bit-identical**
(1.065353525 / −0.833695686 / 0.791709610); +3 isolation tests; pillar pin +
canonical guards green.

| Cell | 2025 sep (was → now) | 2025 affect |
|---|---|---|
| C1 polarizing | 1.065 (unchanged) | −0.834 |
| C2 resisted | 1.072 → **0.880** | −0.473 |
| C4 depolarizing | 0.776 → **0.568** | −0.393 |

- **G1-order now PASS**: sep C1 1.065 > C2 0.880 > C4 0.568 — restoring finally
  has positional traction (cut C2/C4 sep by ~0.18–0.21). The probe's "R2 doesn't
  bite on party_sep" is fixed.
- **G1-reverse still FAIL but close**: C4 sep peak→end drop 0.035 → **0.093**
  (threshold 0.10). R4/R5/R6 should push it over. Affect in C4 cools to a warmer
  *plateau* (−0.393) rather than reversing (cool-then-warm), so the affect
  reverse leg needs contact to eventually *dominate* cooling (stronger R1 /
  the P3a rest state), not just offset it.

**G1 = 2/4** (rise, order PASS; flat, reverse FAIL). Remaining gaps map exactly
to the unbuilt work: flat-on-affect → R1 + P3a (affect rest state); reverse →
R4 (BC revival) + R5 (media fed→earned) + R6 (thermostatic).

---

## Update — after R3 (cross-cutting bridge formation) → still G1 2/4, but reverse now affect-only

R3: `TieRewiring` forms cross-party "bridge" ties (gated `bridge_rewire`), flagged
cooperative so they feed R1. Canonical bit-identical; +5 isolation tests.

| Cell | sep (post-R2 → post-R3) | affect (→) |
|---|---|---|
| C2 resisted | 0.880 → **0.789** | −0.473 → −0.352 |
| C4 depolarizing | 0.568 → **0.519** | −0.393 → −0.292 |

- **C4 sep reversal 0.093 → 0.169** — crosses the 0.10 bar. The **position leg of
  G1-reverse now passes** (peak 0.688 @ tick 24 → 0.519). Bridges mix the network
  so BC/ConstraintOp average across party, and feed R1 (affect much warmer).
- **G1-reverse is now blocked ONLY by the affect leg** (affect warm-reversal
  0.023 < 0.10). Affect cools to a warm *plateau* (−0.292) but never
  cools-then-warms — because `AffectiveUpdate` has no rest state, contact only
  *offsets* the cooling to a higher floor, it can't reverse it. **So the affect
  rest-state fix (mean-reversion mechanism and/or P3a recalibration) is on the
  critical path for G1-reverse, not just G1-flat.** R4/R6 are position-axis and
  won't move this leg.

---

## Update — after R4 (BC affect_weight floor) → G1 2/4 (R4 marginal here, by design)

R4: a floor on BC's affect modulator so warmth re-opens cross-party convergence
(two-sided: cold→echo, warm→bridge). Canonical bit-identical; +5 isolation tests.

Battery effect is **small** (C4 sep 0.519 → 0.521): the position leg already
reverses via R2+R3, so R4 is second-order on this gate. Recorded honestly — R4
is *not* a G1-mover; its value is (a) the audit "BC ~3% no-op" force-fix and (b) a
live affect-mediated position-convergence channel for the joint US-fit re-cal
(more emergent-position headroom once the forcing is cut in R5). G1 stays 2/4,
still blocked only by the **affect** leg (flat + reverse). R6 is also position-
axis, so the affect rest state remains the gating decision before G1 ≥ 3/4.

---

## Update — after R6 (thermostatic feedback) → full R1–R6 stack; affect is the sole gap

R6: a two-signed negative feedback on the party-separation overshoot (homeostat
around a `reference`; rigid per-party translation → within-party spread
preserved). Canonical bit-identical; +5 isolation tests.

**Homeostat-vs-metric subtlety (recorded honestly):** R6 *prevents* overshoot, it
doesn't *reverse* from a peak. At a strong setting (gain 0.6 / ref 0.4) it lowered
the C4 endpoint to 0.445 but *flattened* the peak-then-decline (sep reversal fell
0.170 → 0.066) — so it can regress the peak-decline metric while improving the
*level*. The level is the right lens for a homeostat; the peak-decline metric is
the right lens for R2/R3. A gentle setting (gain 0.10 / ref 0.4) lowers the level
AND keeps the reversal visible.

**Full restoring stack R1+R2+R3+R4+R6 (gentle R6):**

| Cell | 2025 party_sep | 2025 affect | sep reversal | affect reversal |
|---|---|---|---|---|
| C1 polarizing | 1.065 | −0.834 | — | — |
| C2 resisted | 0.660 | −0.332 | 0.101 | 0.021 |
| C3 neutral | 0.236 | −0.767 | — | — |
| C4 depolarizing | **0.497** | **−0.291** | **0.139** | 0.024 |

**The position axis now behaves like a valid general mechanism — every position
criterion passes:** rises under forcing (C1), rests without forcing (C3 sep Δ
−0.054), reverses under restoring (C4 sep reversal 0.139 ≥ 0.10), orders correctly
(C1 > C2 > C4). **G1 = 2/4, and BOTH failures are now purely the affect axis:**
- **G1-flat (affect):** C3 affect cools to −0.767 with zero drivers — no rest state.
- **G1-reverse (affect):** C4 affect plateaus warm (−0.291) but never
  cools-then-warms (reversal 0.024 < 0.10) — contact offsets cooling, can't reverse it.

**None of R1–R6 fix the affect axis** (R1 contact only offsets to a plateau). The
gate now isolates a single decision: give `AffectiveUpdate` a **rest state**. The
G1 diagnostic argues this is structural (no equilibrium), so the principled fix is
a gated **mean-reversion term** (affect relaxes toward a neutral anchor absent
drivers, analogous to the FJ ideology anchor) — not merely the P3a rate
recalibration, which slows cooling but adds no equilibrium. This is the proposed
**R7** (decision pending sign-off), to be paired with the P3a magnitude tune.

---

## Update — after R7 (affect rest state) → Layer-1 mechanism set COMPLETE; affect needs R7 + P3a

R7: `AffectiveUpdate` gains a mean-reversion term — out-party warmth relaxes
toward `affect_rest_anchor` at `affect_rest_rate`/tick (gated; isolation test
proves a finite cold equilibrium instead of the floor). It is a **mechanism-layer
correction** (affect *should* have an equilibrium), so the battery applies it in a
`BASE` group ON in every regime — including C3 where G1-flat is measured.
Canonical bit-identical; +6 isolation tests (46 R-phase tests total).

**Full set R1–R7 (BASE: R7 gentle; RESTORING: R1–R4,R6):**

| Cell | 2025 sep | 2025 affect | sep reversal | affect reversal |
|---|---|---|---|---|
| C1 polarizing | 1.062 | −0.701 | — | — |
| C2 resisted | 0.656 | −0.311 | 0.101 | 0.017 |
| C3 neutral | 0.284 | −0.582 | — | — |
| C4 depolarizing | 0.498 | −0.285 | 0.139 | 0.019 |

- **G1 = 2/4** (rise, order PASS), and the position axis fully validates.
- **R7 directionally fixes the affect rest** (C3 affect Δ −0.621 → −0.430; C4
  affect much warmer) but does **not** fully clear G1-flat/reverse-affect.
- **Why, and the handoff:** with the *canonical* affect_lr (the documented
  over-cooling blindspot), no single R7 rate puts C1 at ≤−0.6 *and* C3 near the
  anchor — C3 retains nonzero intrinsic cooling that only the **P3a magnitude
  recalibration** (reduce affect_lr / animus_mult) removes. **R7 is the mechanism
  (equilibrium); P3a is the magnitude. The affect axis needs BOTH.** At rate 0.03
  R7 over-warmed C1 (broke G1-rise); rate 0.015 preserves G1-rise but leaves C3/C4
  affect short — i.e. the cooling magnitude, not the mechanism, is the residual.

**Conclusion: the Layer-1 mechanism set (R1–R7) is complete.** The position axis
behaves like a valid general model on every G1 criterion. The affect axis has the
right mechanisms (R1 warming + R7 rest); clearing its two G1 legs is now a
**calibration** task (P3a), folded into the joint re-cal — not a missing mechanism.
The remaining build decision is **R5** (media direction + fed→earned), flagged for
sign-off, after which the joint re-calibration runs (R5 + P3a + the R-knob fit +
G2 US-fit + the falsification battery).
