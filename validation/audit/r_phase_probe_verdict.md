# R-phase feasibility probe — verdict (seed 0; NOT a bless)

Ran `validation/audit/r_phase_probe.py`: canonical baseline vs R1+R2 at moderate /
strong strength / a "Sweden-like" (strong restoring + weak forcing) counterfactual.
All via `build_engine` kwargs; engine untouched; canonical stays bit-identical.

## party_sep / affect @ 2025 (Δ vs baseline)

| config | 2025 party_sep | 2025 affect | Δsep | Δaffect |
|---|---|---|---|---|
| baseline (R off) | 1.065 | −0.834 | — | — |
| R-moderate | 1.066 | −0.704 | +0.001 | **+0.130** |
| R-strong | 1.072 | −0.515 | +0.007 | **+0.319** |
| Sweden-like (R-strong + mob_peak 2.5→0.8, elite_gain 1.8→1.0) | 0.776 | −0.440 | **−0.290** | +0.393 |

## Findings

1. **R1 (contact warming) works, and on the right axis.** It warms out-party affect
   strongly and self-limits sensibly: R-strong lifts 2025 affect −0.834 → −0.515 —
   essentially *into* the grounded band ([−0.71,−0.51]). Affect is now an
   **endogenously warmable** channel, which (a) is the axis the literature says
   actually moved, (b) gives the X-interventions real affect traction, and (c) is a
   bonus lever for the affect recalibration (P3a) — contact warming alone nearly
   fixes the affect-too-cold blindspot.

2. **R2 as implemented barely moves position separation.** `xpressure_sorting_damp`
   targets `ConstraintOp`, which drives issue *constraint/alignment* — but the
   headline `party_sep` is **centroid separation driven by PartyPull / the
   activist→elite→mass loop**, which R2 does not touch. And the self-limiting
   `xp = 1 − identity_alignment` is small once agents are stacked, so even constraint
   moves little (0.792 → 0.787). **Implication:** to make *positional* sorting
   reversible, cross-pressure damping must also hit **PartyPull / the loop gain**
   (not only ConstraintOp), and/or be paired with the R5 forcing reduction.

3. **No true endogenous reversal yet.** Every config is monotone-rising; the
   Sweden-like one reaches a *lower plateau* (0.776) but does not peak-then-decline.
   The falsification test's part (b) — a sorted society actually depolarizing — is
   **not met by R1+R2 alone**. Achieving it needs either much stronger restoring on
   the position channel (R2→PartyPull, R4 BC feeding position back via warmed
   affect, R6 thermostatic feedback) or a regime where divergent forces weaken while
   restoring persists.

## Recommendation for the morning
- **Keep R1** — it's a clean win on affect (and doubles as an affect-recal lever).
- **Revise R2** before the joint re-calibration: extend cross-pressure damping to
  `PartyPull` / the loop gain so it bites on `party_sep`, not only `ConstraintOp`.
- **Reversal** will need R4/R5/R6 (BC revival + media-direction/forcing-cut +
  thermostatic feedback), not just Tier-1 — consistent with the spec's staging.
- This is a design-tweak decision (which rule R2 targets) → flagged for sign-off
  rather than changed autonomously.
