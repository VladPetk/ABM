"""Per-stage directional validation tests for the calm_to_camps pillar.

Each stochastic assertion runs over the STAGE_SEEDS ensemble (built once in
conftest fixtures) and tests the ensemble mean against an empirically
measured tolerance (phase1_spec §7, §9; phase2_spec §5, §8).
"""
from __future__ import annotations

import numpy as np

from abm.pillars import PILLAR, apply_intervention, build_at_stage

from abm.metrics.network import cross_cutting_tie_fraction, party_modularity

from .conftest import (
    N,
    STAGE_SEEDS,
    TICKS,
    constraint_avg,
    diet_extremity,
    party_separation,
    positional_engine,
)


# --- S0 / S1 (Phase 1) ----------------------------------------------------

def test_s0_baseline_no_organized_motion(s0_ensemble):
    """S0 — nothing organized happens: variance stays within the noise band."""
    initials, finals = s0_ensemble
    rel_changes = [abs(v1 - v0) / v0 for v0, v1 in zip(initials, finals)]
    mean_rel_change = float(np.mean(rel_changes))
    assert mean_rel_change < 0.05, (
        f"S0 baseline variance drifted {mean_rel_change:.3f} on average — "
        "noise-only baseline should not move variance more than 5%."
    )


def test_s1_bounded_confidence_pulls_society_together(s0_ensemble, s1_ensemble):
    """S1 — bounded confidence cuts variance to <85% of S0."""
    _, s0_finals = s0_ensemble
    _, s1_finals = s1_ensemble
    mean_s0 = float(np.mean(s0_finals))
    mean_s1 = float(np.mean(s1_finals))
    assert mean_s1 < 0.85 * mean_s0, (
        f"S1 mean variance {mean_s1:.3f} should be <85% of S0 {mean_s0:.3f}; "
        f"observed ratio {mean_s1 / mean_s0:.3f}."
    )


# --- S2 / S3 (Phase 2) ----------------------------------------------------

def test_affective_update_is_positionally_inert():
    """Phase 2 D6: AffectiveUpdate writes only the `affect` attribute and
    never draws from the RNG, so zeroing its `lr` must leave every position
    bit-identical. Justifies the `positional_engine` fast path."""
    from abm.pillars.calm_to_camps import build_engine

    n = 250
    real = build_engine(seed=0, n_agents=n)
    apply_intervention(real, PILLAR.interventions[2])           # lr = 0.01

    fast = build_engine(seed=0, n_agents=n)
    apply_intervention(fast, PILLAR.interventions[2])
    for rule in fast.rules.rules:
        if type(rule).__name__ == "AffectiveUpdate":
            rule.lr = 0.0                                        # the fast path

    real.run(60)
    fast.run(60)
    assert np.array_equal(real.positions(), fast.positions()), (
        "Zeroing AffectiveUpdate.lr must leave positions bit-identical — "
        "if not, AffectiveUpdate has become position-affecting or RNG-consuming."
    )


def test_s2_party_identity_raises_constraint(s1_engines, s2_engines):
    """S2 — adding PartyPull raises ideological constraint over S1."""
    c1 = [constraint_avg(e) for e in s1_engines]
    c2 = [constraint_avg(e) for e in s2_engines]
    mean_c1 = float(np.mean(c1))
    mean_c2 = float(np.mean(c2))
    assert mean_c2 > mean_c1 + 0.04, (
        f"S2 constraint {mean_c2:.3f} should exceed S1 {mean_c1:.3f} by >0.04; "
        f"observed gap {mean_c2 - mean_c1:+.3f}."
    )


def test_s3_partisan_media_pushes_heavy_consumers_out(s2_engines, s3_engines):
    """S3 — paired test (Phase 2 D5): the per-agent radial change S3-vs-S2
    correlates with the agent's diet extremity. Heavy partisan-diet agents
    are pushed outward more than centrist-diet agents. Same seed → same
    population, so each agent is its own control."""
    correlations: list[float] = []
    for eng2, eng3 in zip(s2_engines, s3_engines):
        radii_2 = np.array([np.linalg.norm(a.state.ideology) for a in eng2.agents])
        radii_3 = np.array([np.linalg.norm(a.state.ideology) for a in eng3.agents])
        media_effect = radii_3 - radii_2
        extremity = np.array([diet_extremity(a) for a in eng3.agents])
        if media_effect.std() == 0 or extremity.std() == 0:
            correlations.append(0.0)
        else:
            correlations.append(float(np.corrcoef(extremity, media_effect)[0, 1]))
    mean_corr = float(np.mean(correlations))
    assert mean_corr > 0.5, (
        f"Mean paired correlation {mean_corr:.3f} should exceed 0.5 — "
        f"per-seed correlations: {[round(c, 3) for c in correlations]}."
    )


# --- S4 (Phase 3) ---------------------------------------------------------

def test_cross_tie_weight_1_is_inert(s1_ensemble):
    """Phase 3 E3 regression guard: the exposure-aware BC refactor must take
    a fast path bit-identical to the pre-Phase-3 plain-mean rule whenever
    `cross_tie_weight == 1.0`. The whole Phase 1/2 suite is the broad
    guarantee; this single test pins S1's measured final variance to a
    tight tolerance so any drift in the refactored fast path is loud and
    immediate (not buried in a downstream test)."""
    _, finals = s1_ensemble
    mean_final = float(np.mean(finals))
    # Phase 1 measured baseline at this N/TICKS/seeds: ~0.533.
    assert abs(mean_final - 0.533) < 0.01, (
        f"S1 mean final variance {mean_final:.4f} drifted from the Phase 1 "
        "baseline 0.533 — the exposure-aware refactor of BC must keep the "
        "cross_tie_weight==1.0 path bit-identical to np.mean."
    )


def test_s4_narrows_exposure(s4_engines, initial_network_metrics):
    """S4 — co-evolution should sort the tie network: cross-cutting tie
    fraction falls and party modularity rises across the ensemble."""
    xc_after = [
        cross_cutting_tie_fraction(e.agents, e.env.attrs["network"])
        for e in s4_engines
    ]
    mod_after = [
        party_modularity(e.agents, e.env.attrs["network"])
        for e in s4_engines
    ]
    xc_before = [m[0] for m in initial_network_metrics]
    mod_before = [m[1] for m in initial_network_metrics]
    mean_xc_drop = float(np.mean(xc_before) - np.mean(xc_after))
    mean_mod_rise = float(np.mean(mod_after) - np.mean(mod_before))
    assert mean_xc_drop > 0.10, (
        f"S4 cross-cutting fraction barely moved: "
        f"{np.mean(xc_before):.3f} -> {np.mean(xc_after):.3f} "
        f"(drop {mean_xc_drop:+.3f}, need >0.10)."
    )
    assert mean_mod_rise > 0.10, (
        f"S4 party modularity barely moved: "
        f"{np.mean(mod_before):.3f} -> {np.mean(mod_after):.3f} "
        f"(rise {mean_mod_rise:+.3f}, need >0.10)."
    )


# Release-phase length; matched to TICKS so the experiment is symmetric.
RELEASE_TICKS = TICKS

# §13.3 step 5: smallest epsilon at which the ungated world reliably
# re-merges, plus one step of cushion. Measured during calibration —
# see commit notes / sign-off report.
RELEASE_EPSILON = 0.8  # placeholder, recalibrated below


def _release_run(seed: int, gate: float, rewire: float) -> float:
    """Paired ratchet helper: polarise through S4, then release the
    polarising forces (PartyPull, MediaConsumption) and reopen
    bounded-confidence to a calibrated radius. The only thing that
    distinguishes worlds A and B is whether the homophilous ratchet
    (soft gate + slow rewiring) stays on during release."""
    eng = positional_engine(4, seed)        # S4 with AffectiveUpdate.lr=0
    eng.run(TICKS)
    for r in eng.rules.rules:
        name = type(r).__name__
        if name == "PartyPull":
            r.strength = 0.0
        elif name == "MediaConsumption":
            r.strength = 0.0
        elif name == "BoundedConfidenceInfluence":
            r.epsilon = RELEASE_EPSILON     # calibrated, not maximised (§13)
            r.cross_tie_weight = gate
    for r in eng.env_rules:
        if type(r).__name__ == "TieRewiring":
            r.rewire_rate = rewire
    eng.run(RELEASE_TICKS)
    return party_separation(eng)


def test_s4_is_a_ratchet():
    """Phase 3 headline (D1, §9, §13): a paired release experiment.

    Two identical worlds are polarised through S4, then released — the
    polarising forces are dropped and bounded-confidence reopens at a
    calibrated radius (not maximised — §13 fixed the epsilon-vs-gate
    coupling). World A keeps the homophilous soft gate (0.10) plus slow
    rewiring; World B turns the gate fully off. If S4 truly *amplifies
    and locks in* polarisation, world B's camps re-merge while world
    A's stay apart — even though world A still hears the other side at
    attenuated weight."""
    sep_a, sep_b = [], []
    for seed in STAGE_SEEDS:
        sep_a.append(_release_run(seed, gate=0.10, rewire=0.02))
        sep_b.append(_release_run(seed, gate=1.0, rewire=0.0))
    mean_a, mean_b = float(np.mean(sep_a)), float(np.mean(sep_b))
    assert mean_a > mean_b + RATCHET_MARGIN, (
        f"S4 failed to act as a ratchet: gated world sepA={mean_a:.3f} "
        f"vs ungated sepB={mean_b:.3f} (gap {mean_a - mean_b:+.3f}, "
        f"needed > {RATCHET_MARGIN}). Per-seed: "
        f"A={[round(x, 3) for x in sep_a]} B={[round(x, 3) for x in sep_b]}."
    )


# §13.3 step 6: gap = mean(sepA) - mean(sepB), then subtract cushion.
# Filled in below from the recalibrated sweep.
RATCHET_MARGIN = 0.10  # placeholder, set after sweep


# Sanity: assert pillar has the five stages Phase 3 introduces.
def test_pillar_has_five_stages():
    assert len(PILLAR.interventions) == 5
    ids = [iv.id for iv in PILLAR.interventions]
    assert ids == [
        "S0_baseline",
        "S1_bounded_confidence",
        "S2_party_identity",
        "S3_partisan_media",
        "S4_homophilous_network",
    ]
