"""
Canonical ANES-full engine preset — single source of truth.

Step 1 (web_demo evidence re-grade, decision D4). Previously the
`anes_full` kwargs were *copied* into both `scripts/publish_web_data.py`
(the shipped baseline + counterfactuals) and `scripts/phase10_measure.py`
(the intervention scoreboard). The two copies had **drifted**:

  - publish added the web-demo realism knobs `momentum=0.4`,
    `fj_alpha_scale=2.8`, `tier_d_ic_partisan_x_cap=0.45`, and halved
    the per-tick noise to `tier_d_aniso_noise_sigma_{x,y}=0.04`;
  - phase10 still measured at `...=0.08`, with no momentum / fj-scale /
    x-cap.

So the interventions were being scored against an engine config the demo
never actually ships — i.e. the "what happened" baseline and the
"intervention Δ" were measured on **different** substrates, which
silently breaks the honesty contract (the Δ a user sees can't be added to
the trajectory they see).

This module makes both consumers import ONE dict. The principled choice
is the **shipped-baseline config**: interventions must be measured against
exactly what the demo displays, so the canonical preset is the publish
config (realism knobs on, noise 0.04). Phase 10's re-measure (Step 2)
will re-bless the buckets against this unified substrate.

`evidence_regrade=True` is part of the canonical config: the web/ANES
path is where the Step-1 truth-pass re-grade (D1a/D2a/D3b) is meant to
take effect. The default path (pillar + Phase 4–9 historical tests) never
imports this preset, so it stays bit-identical.
"""
from __future__ import annotations

# The single canonical web/ANES engine configuration. Consumed by
# scripts/publish_web_data.py and scripts/phase10_measure.py. Treat as
# read-only — callers spread it (**ANES_FULL_KWARGS) or copy it
# (dict(ANES_FULL_KWARGS)) rather than mutating it.
ANES_FULL_KWARGS = {
    "n_agents": 250,
    "independent_fraction": 0.12,
    "factional_seeding": False,
    "faction_anchor_strength": 0.10,
    "faction_anchor_events": True,
    "event_stubbornness_bump_multiplier": 1.0,
    "tier_d_axis_balance": True,
    "tier_d_lever1_off": True,
    "tier_d_cohort_y_signs_fix": True,
    "tier_d_anes_knobs": True,
    "tier_d_anes_drift_multiplier": 3.0,
    # MHV T0.1: tier_d_anes_sigma_pc_multiplier (was 1.6) removed — folded
    # into PARTY_CUE_SIGMA_HISTORICAL_ANES (0.42*1.6 / 0.57*1.6), bit-
    # identically. The kwarg is deprecated (accepted, warns, no-op).
    "tier_c_identity_pull_x": 0.020,
    "tier_c_identity_pull_y": 0.040,
    # D4: unified to the shipped-baseline value (0.04, the web_demo
    # jumpiness Step 3 value) — NOT phase10's old 0.08 — so the
    # intervention scoreboard is measured on the same substrate the
    # demo ships.
    # MHV S4 T4.3 — CALIBRATED VALUES (the ABC fitted point, full-trajectory fit
    # against ANES 1980-2025 per-wave bands + grounded affect; methods §5.25,
    # docs/internal/audit/s4_fit.{json,md}). Closes the de-artifacted party_sep
    # undershoot (2020 sep 0.58 -> 1.08, in ANES band) with affect on-target late.
    # The three sep levers (party_pull, fj_alpha_scale, elite_lead_factor) are a
    # documented RIDGE (arc identified, decomposition not; SBC coverage ~nominal,
    # ks-uniformity fails on the ridge-coupled marginals) — this is one defensible
    # point on it. idpull / bc_strength / drift_mult were FROZEN in the fit.
    "tier_d_aniso_noise_sigma_x": 0.0478,
    "tier_d_aniso_noise_sigma_y": 0.0478,
    "tier_c_party_pull_strength": 0.297,
    "sandbox_animus_mult": 0.655,
    "elite_lead_factor": 1.798,
    # MHV S2 T2.6 — the BC wake (T0.6 finding: at 0.30/0.015 the BC
    # channel was effectively dead on the ANES substrate; eps 0.40 /
    # strength 0.03 restores a live influence channel, gain ~2.9x).
    "tier_c_bc_strength": 0.03,
    "tier_c_bc_epsilon": 0.40,
    "tier_d_coupling_rho": 0.30,
    "tier_d_cue_correlation": 0.40,
    "tier_d_ic_sigma": 0.35,
    # MHV T0.4 — momentum (was 0.4) RELOCATED to a presentation-side
    # EMA in scripts/repack_web_demo.py (user adjudication 2026-06-10):
    # it was a display-smoothness knob, not a mechanism. The engine kwarg
    # remains accepted (default 0.0 = off).
    # web_demo jumpiness Step 4 — tighten the free-mover tail.
    # MHV T0.4 adjudication: KEPT as mechanism. L (Friedkin–Johnsen
    # anchoring) / E (the 1–2% lifetime-big-mover target from panel
    # stability) / N (the 2.8 value). See methods.md §5.15.
    "fj_alpha_scale": 2.195,   # MHV S4 T4.3 (was 2.8) — fitted
    # MHV S2 T2.6 — the T0.4 soft wrong-side-tail cap is RETIRED as
    # promised (s2_spec §1): on the D=7 substrate the item-level seeding
    # reproduces wrong-side tails NATIVELY from the measured 1986
    # party-conditional moments (pinned by tests/test_t21_issue_state.py).
    # The tier_d_ic_partisan_x_cap / tier_d_ic_wrongside_tail_target
    # kwargs remain available for the legacy 2D path only.
    #
    # MHV S2 T2.6 — THE CANONICAL FLIP. The shipped substrate becomes the
    # D=7 ANES issue battery (frozen loadings, native IC) and the
    # emergent rule set replaces the scheduled alignment spine:
    # ConstraintOp (network-local consensus projection; rate at the
    # T2.3 prior center) + MeasuredAlignment readout; IdentitySorting,
    # IDENTITY_SORTING_SCHEDULE, the x5 regrade multiplier, and
    # PARTY_ISSUE_COUPLING_SCHEDULE are retired on this path; the dyadic
    # identity-distance affect term is off (M3-light). Viability re-pick
    # (NOT calibration - S4 owns the fit): scripts/audit/t26_arc_repick.py;
    # methods.md §5.23.
    "n_issues": 7,
    "constraint_rate": 0.0348,   # MHV S4 T4.3 (was 0.02) — fitted
    "constraint_resid_sigma": 0.01,
    # MHV S3 T3.5 — THE FORCES-AS-INPUTS FLIP. The scheduled EliteDrift and the
    # discrete FD/Fox/social-media media steps are replaced by data-fed input
    # series (abm/pillars/inputs.py):
    #   - data_fed_elite: party centroids from the ANES voter-centroid series
    #     (data/mhv/party_centroid_series.json). REMOVES the corner-pin artifact
    #     (scheduled EliteDrift pinned the attractor at [+-1,+-1] by 2014; T0.6).
    #     The de-artifacted party_sep is LOWER (~0.59 vs the artifact-inflated
    #     0.94) and undershoots the ANES target pending the S4 fit — accepted at
    #     the T3.5 sign-off (option 1): re-bless down honestly, S4 closes the gap
    #     via party_pull/fj. See methods §5.24 + docs/internal/audit/t32_datafed.md.
    #   - data_fed_media: media coupling from the penetration series
    #     (data/mhv/media_penetration_series.json). Faithful re-expression of the
    #     FD/Fox/social-media steps — near trajectory-neutral.
    "data_fed_elite": True,
    "data_fed_media": True,
    # Step 1 (web_demo evidence re-grade) — master gate for the engine
    # truth-pass (D1a Gingrich/CU, D2a social-media demotion, D3b
    # identity-alignment → animus). On for the web/ANES path.
    "evidence_regrade": True,
    # web_demo exogenous-shocks workstream — master gate for the general
    # external-shock mechanism (abm/pillars/shocks.py): the empirical
    # catalogue S-911 (transient out-party warming, Sept 2001) and
    # S-Obergefell (slight cultural-axis divergence, June 2015). Enabled on
    # the web/ANES path AFTER the re-validate → re-measure Phase 10 →
    # re-bless cycle (2026-06-01). Default-path scenarios never import this
    # preset, so they stay bit-identical.
    "exogenous_shocks": True,
}
