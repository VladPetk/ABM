# Emergence-recovery E5.1 — endogenous holdout battery scorecard

**Overall: FAIL** (1/3 substantive cuts pass; power-band rule: >=2/3). Bands pre-registered in s4_targets.py (config-independent); ABC refits on the endogenous knob set. The adopted E4 ABC point is fixed (a failed band is a finding, not a retune).

| cut | verdict |
|---|---|
| cut1_temporal | FAIL |
| cut2_instrument | FAIL |
| cut3_statistic | PASS |

## Cut 1 — temporal (fit <=2000 → predict 2010/2020/2025)
refit point: elite_gain=1.750, mob_base=0.036, mob_peak=1.653, mob_backload=1.190, mob_asym=0.186, uptake=0.060, fj_alpha_scale=2.906, elite_ceiling=0.675

| decade.metric | pred band (8 seeds) | widened ANES band | in? |
|---|---|---|---|
| 2010.party_sep | [0.435,0.500] | [0.72,1.0] | ** |
| 2010.affect | [-0.451,-0.410] | [-0.58,-0.34] | OK |
| 2010.constraint | [0.501,0.567] | [0.51,0.79] | OK |
| 2010.within_party_sd | [0.234,0.270] | [0.19,0.47] | OK |
| 2020.party_sep | [0.538,0.629] | [0.97,1.25] | ** |
| 2020.affect | [-0.513,-0.473] | [-0.73,-0.49] | OK |
| 2020.constraint | [0.585,0.649] | [0.6,0.87] | OK |
| 2020.within_party_sd | [0.224,0.262] | [0.21,0.48] | OK |
| 2025.party_sep | [0.538,0.660] | [0.97,1.25] | ** |
| 2025.affect | [-0.528,-0.491] | [-0.78,-0.44] | OK |
| 2025.constraint | [0.593,0.680] | [0.62,0.89] | OK |
| 2025.within_party_sd | [0.224,0.272] | [0.21,0.48] | OK |

## Cut 2 — instrument (shipped endogenous point → held-out GSS trends)
shipped point: elite_gain=1.769, mob_base=0.078, mob_peak=2.484, mob_backload=1.355, mob_asym=0.188, uptake=0.253, fj_alpha_scale=1.780, elite_ceiling=0.824

| trend | engine slope/yr | GSS slope/yr | within +/-50% & sign? |
|---|---|---|---|
| partisan align (bg) | +0.01128 | +0.00851 | OK |
| issue |corr| (constraint_index) | +0.00903 | +0.00568 | ** |

## Cut 3 — statistic (fit sep/affect/wp_sd → predict constraint)
refit point: elite_gain=2.032, mob_base=0.050, mob_peak=2.119, mob_backload=0.821, mob_asym=0.076, uptake=0.131, fj_alpha_scale=1.578, elite_ceiling=0.726

| decade | pred constraint band | widened ANES constraint | in? |
|---|---|---|---|
| 1980 | [0.265,0.516] | [0.2,0.48] | OK |
| 1990 | [0.299,0.558] | [0.3,0.58] | OK |
| 2000 | [0.495,0.637] | [0.39,0.67] | OK |
| 2010 | [0.677,0.744] | [0.51,0.79] | OK |
| 2020 | [0.705,0.785] | [0.6,0.87] | OK |
| 2025 | [0.737,0.785] | [0.62,0.89] | OK |

## Interpretation — the emergence trade-off (read this)

The FED config passed all three cuts (s4_holdout.md, 3/3). The endogenous
config passes only cut 3. This is **not** a regression in the usual sense —
two of the cuts only became *meaningful* once positional sorting stopped
being fed:

- **Cut 1 (temporal) FAIL — the honest cost of genuine emergence.** Refit on
  <=2000 and the ABC picks a low mobilization ramp (mob_peak ~1.65 vs 2.48,
  uptake ~0.06 vs 0.25) that fits the flat early period — then under-predicts
  the 2010+ acceleration (2025 party_sep ~0.5-0.7 vs the needed ~1.0-1.25).
  Only party_sep fails; affect/constraint/within_sd all pass. The FED config
  passed this cut TRIVIALLY: it fed the ANES centroid series, so the late
  trajectory was carried regardless of the fit knobs. The endogenous config
  makes cut 1 a real out-of-sample test, and it reveals that the late
  acceleration is NOT predictable from early dynamics — it rides the
  exogenously-fit activist-mobilization timing (consistent with the E5.2
  honesty budget: only ~38% of party_sep is the spontaneous loop floor; ~62%
  depends on the fitted forcing). The model EXPLAINS the mechanism (loop
  amplification) but the TIMING is calibrated to the full period, not predicted.
- **Cut 2 (instrument) FAIL — one sub-test, the axis over-correlation.** The
  partisan-align slope passes (engine 1.44x GSS, within +/-50%); the issue-corr
  slope is 1.62x GSS — just over the band. This is the documented single-axis
  loop residual (realism B2: corr(x,y) ~0.78 vs ANES ~0.5-0.6). The
  time-evolving / balanced realignment direction refinement is the candidate fix.
- **Cut 3 (statistic) PASS.** Constraint (partisan alignment) is well predicted
  from sep/affect/spread across all six decades.

**Verdict:** the holdout fails the pre-registered >=2/3 bar (1/3). Honest
reading: the emergence win is real (E5.2), but the late-period TIMING is an
exogenously-calibrated forcing the model amplifies rather than predicts, and
the single-axis loop over-correlates the compass axes. Both are documented
limitations, not hidden. A failed band is a finding, not a retune trigger
(the adopted E4 ABC point is fixed). Whether to ship the endogenous flip given
this is a user call (see the morning report).
