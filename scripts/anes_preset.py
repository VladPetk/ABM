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
    "tier_d_anes_sigma_pc_multiplier": 1.6,
    "tier_c_identity_pull_x": 0.020,
    "tier_c_identity_pull_y": 0.040,
    # D4: unified to the shipped-baseline value (0.04, the web_demo
    # jumpiness Step 3 value) — NOT phase10's old 0.08 — so the
    # intervention scoreboard is measured on the same substrate the
    # demo ships.
    "tier_d_aniso_noise_sigma_x": 0.04,
    "tier_d_aniso_noise_sigma_y": 0.04,
    "tier_c_party_pull_strength": 0.04,
    "tier_c_bc_strength": 0.015,
    "tier_d_coupling_rho": 0.30,
    "tier_d_cue_correlation": 0.40,
    "tier_d_ic_sigma": 0.35,
    # web_demo jumpiness Step 5 — opinion momentum (was publish-only;
    # now canonical so phase10 measures the same trajectory).
    "momentum": 0.4,
    # web_demo jumpiness Step 4 — tighten the free-mover tail.
    "fj_alpha_scale": 2.8,
    # web_demo realism — truncate the 1980 economic IC tail.
    "tier_d_ic_partisan_x_cap": 0.45,
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
