# Affect-recalibration feasibility — scope verdict (audit follow-up)

**Question (user, post-audit):** before committing to the full affect re-bless (P3a),
can re-tuning the affect knobs bring out-party affect back into the grounded ANES bands
(currently **0/5** on the shipped config), and at what cost?

**Method:** monkeypatch sweep over the pure affect knobs on the canonical `ANES_FULL_KWARGS`,
reusing the real scorer (`_score_cells`). Engine files untouched. Scripts + logs in
`validation/audit/affect_recal_scope*.{py,log,json}`. Baseline cell reproduces
`realism_measurement.json` A4 (validates the harness).

## Verdict: FEASIBLE and CLEAN, but it's a substantial re-tune + a real cascade

**1. Affect is cleanly downstream of the position metrics — recalibration cannot break the
scorecard.** Across every knob cell in three sweeps, the set of *non-affect* cells out of
band is byte-identical. Warming affect has **zero** measurable effect on `party_sep` /
`constraint` / `within_party_sd` / `variance`. (The affect→backlash→position feedback is
negligible because BC is near-inert and backlash is weakly gated.) This is the key
de-risking result: the only thing affect recalibration changes is affect.

**2. A clean recalibration flips the FAIL to a PASS.** Best robust cell (3 seeds):
`affect_lr ×0.25–0.30, saturation 1.0 (re-enabled), MediatedAnimus ×0.4`:
- affect **0/5 → 3/5** in band (2010/2020/2025 solidly in; see table),
- scorecard **15–16/24 → 19/24 — PASSES the ≥18 gate**,
- **no position-metric collateral.**

| Decade | canonical | recal (0.3,1.0,0.4) | ANES band | status |
|---|---|---|---|---|
| 1990 | −0.32 | −0.22 | [−0.206,−0.096] | edge (~0.01 cold) |
| 2000 | −0.48 | −0.33 | [−0.313,−0.179] | edge (~0.01 cold) |
| 2010 | −0.66 | −0.48 | [−0.512,−0.412] | **in** |
| 2020 | −0.79 | −0.58 | [−0.658,−0.558] | **in** |
| 2025 | −0.83 | −0.61 | [−0.708,−0.508] | **in** |

**3. Two honest caveats.**
- **The required cut is large (3–5×) + saturation back on.** The `evidence_regrade` affect
  re-tune (which *retired* the saturation decelerator and added MediatedAnimus) left the
  channel **substantially over-cooled** against the corrected (warmer) re-graded bands. The
  fix is essentially "undo the over-shoot": re-enable the saturation that §11.7-G says exists
  precisely to stop affect over-shooting "at every decade," and walk the LRs back. Even the
  best cell sits at the **cold edge** of every band — this is the *minimum* cut, not an
  over-correction.
- **1990/2000 stay ~0.01 below the narrow early bands** and don't warm further (contact
  cooling is saturation-limited there). Solid 5/5 would need one early-specific lever (a
  slightly warmer 1980 affect seed, or lower early `party_issue_coupling`), i.e. a bit more
  tuning. 3/5 already passes the gate.

## Implementation wrinkle
The effective `affect_lr` needed (~0.0006–0.0009) is **below the build-time clip floor**
`np.clip(affect_lr, 0.001, 0.03)` (`historical_arc.py` `compute_agent_heterogeneity`). A real
implementation must lower that floor too (the sweep scaled per-agent LRs post-build to bypass
it). One extra one-line calibration change.

## Re-bless cost of P3a (full recalibrate)
Small code change (3 constants + the clip floor) → but the standard cascade re-runs:
1. `realism_battery.py` (9 seeds, ~10 min) → `realism_measurement.json` (A2/A4) + `realism_report.md` A4.
2. **Affect golden/drift tests re-bless** — any test pinning affect values (e.g. the phase7
   affect-trajectory band test, realism guards, affect-band tests) will fail and need honest
   re-blessing.
3. **`phase10_measure.py` re-measure** — interventions are scored on the affect axis, so
   recalibrating affect can flip intervention buckets → `phase10_results.md` may change
   (measure-then-bless: must re-run, don't assume unchanged).
4. **Web re-export** — `publish_web_data.py` + `repack_web_demo.py` → `cc-data.js` (the
   "scissors" affect viz changes).
5. `honesty_budget.json` (`t35_budget_brake.py`) — affect magnitudes change (emergent
   fraction ~unchanged).
6. Docs: methods §5.10/§5.27/§5.30, blindspot register.

## Cost of P3b (relabel only)
Docs only, no cascade: state affect is 0/5 vs grounded bands on the shipped config, register
affect-too-cold as a first-class blindspot, stop counting affect toward the headline, re-bless
`realism_report` A4 text. Affect stays over-cooled but honestly disclosed.

## Recommendation
The recalibration is **worth doing**: it is clean (orthogonal), honest in narrative (corrects
a documented over-shoot by re-enabling the decelerator that was wrongly retired), and it flips
the project's own gate from FAIL to PASS. The blocker is not feasibility — it's that it
triggers the phase10 + web re-bless cascade, which is the user's call on timing. If a cascade
is unwelcome now, **P3b (relabel) is the honest interim** and P3a becomes a tracked follow-up.
