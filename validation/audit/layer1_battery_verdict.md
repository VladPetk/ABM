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
