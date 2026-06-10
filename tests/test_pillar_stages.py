"""Per-stage directional validation tests for the calm_to_camps pillar.

Each stochastic assertion runs over the STAGE_SEEDS ensemble (built once in
conftest fixtures) and tests the ensemble mean against an empirically
measured tolerance (phase1_spec §7, §9; phase2_spec §5, §8).
"""
from __future__ import annotations

import numpy as np

from abm.core.network import Network
from abm.metrics.affective import affective_polarization
from abm.metrics.network import cross_cutting_tie_fraction, party_modularity
from abm.pillars import PILLAR, apply_intervention, build_at_stage

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
    """S1 — bounded confidence cuts variance to <92% of S0.

    Re-blessed under ADR-001 and Phase 4: BC flows along a homophilous
    network, and Phase 4's anchored agents (F1) damp how far the bulk
    move. Measured ratio under F1+F2+F3 is ~0.83 (essentially unchanged
    from the ADR-001 measurement — anchoring damps both worlds
    proportionally). The qualitative direction (variance falls) is what
    the test asserts; the 0.92 threshold has a ~0.09 cushion.

    Re-blessed under MHV S2 T2.5 (D=7 issues substrate): item-space RMS
    distances carry within-block residual texture, which starved BC at
    ε=0.30 (ratio degraded to 0.922 — the pillar-side twin of the T0.6
    arc finding). The model was re-picked, not the threshold: pillar ε
    0.30 → 0.35 (sweep in scripts/audit/t25_pillar_repick.py) restores
    the measured ratio to ~0.89; threshold unchanged at <0.92.
    """
    _, s0_finals = s0_ensemble
    _, s1_finals = s1_ensemble
    mean_s0 = float(np.mean(s0_finals))
    mean_s1 = float(np.mean(s1_finals))
    assert mean_s1 < 0.92 * mean_s0, (
        f"S1 mean variance {mean_s1:.3f} should be <92% of S0 {mean_s0:.3f}; "
        f"observed ratio {mean_s1 / mean_s0:.3f}."
    )


# --- S2 / S3 (Phase 2) ----------------------------------------------------

def test_positional_fast_path_is_a_faithful_approximation():
    """The `positional_engine` fast path (used by every positional test
    for speed) zeroes the affect channel — `AffectiveUpdate.lr`,
    `BoundedConfidenceInfluence.affect_weight`, and
    `TieRewiring.affect_weight_rewire`. Phase 2 D6 promised that this
    fast path was bit-identical to the full bundle; Phase 5's A4 makes
    BC read affect per neighbour, so the bit-identical claim no longer
    holds (the calibration measures positional metrics differ by ~0.005
    between affect-on and affect-off).

    This test pins the weaker but still useful invariant: the fast path
    is a **faithful approximation** — the population variance and party
    separation under the affect-off fast path are within 0.02 of the
    full Phase 5 bundle at S2. The test catches any future change that
    makes the affect channel a *macro*-position-shifter rather than the
    intended subtle nudge.
    """
    from abm.metrics.polarization import variance
    from abm.pillars.calm_to_camps import build_engine

    n = 250
    ticks = 60
    real = build_engine(seed=0, n_agents=n)
    apply_intervention(real, PILLAR.interventions[2])
    fast = build_engine(seed=0, n_agents=n)
    apply_intervention(fast, PILLAR.interventions[2])
    for rule in fast.rules.rules:
        name = type(rule).__name__
        if name == "AffectiveUpdate":
            rule.lr = 0.0
        elif name == "BoundedConfidenceInfluence":
            rule.affect_weight = 0.0
    for rule in fast.env_rules:
        if type(rule).__name__ == "TieRewiring":
            rule.affect_weight_rewire = 0.0

    real.run(ticks)
    fast.run(ticks)
    var_real = variance(real.positions())
    var_fast = variance(fast.positions())
    sep_real = party_separation(real)
    sep_fast = party_separation(fast)
    assert abs(var_real - var_fast) < 0.02, (
        f"Fast path variance drift {abs(var_real - var_fast):.4f} should be "
        f"<0.02 — affect channel is meant to be a subtle nudge, not a "
        f"macro-shifter (real {var_real:.4f} vs fast {var_fast:.4f})."
    )
    assert abs(sep_real - sep_fast) < 0.05, (
        f"Fast path party_separation drift {abs(sep_real - sep_fast):.4f} "
        f"should be <0.05 — affect channel is meant to be a subtle nudge "
        f"(real {sep_real:.4f} vs fast {sep_fast:.4f})."
    )


def test_s2_party_identity_raises_constraint(s1_engines, s2_engines):
    """S2 — adding PartyPull raises ideological constraint over S1.

    Re-blessed under Phase 4: F1 (anchoring) damps PartyPull's effect on
    the bulk of agents, so the S1→S2 constraint gap shrinks from Phase
    2's ~+0.08 to ~+0.04. Measured +0.038; threshold pinned at 0.02 with
    a ~0.018 cushion.
    """
    c1 = [constraint_avg(e) for e in s1_engines]
    c2 = [constraint_avg(e) for e in s2_engines]
    mean_c1 = float(np.mean(c1))
    mean_c2 = float(np.mean(c2))
    assert mean_c2 > mean_c1 + 0.02, (
        f"S2 constraint {mean_c2:.3f} should exceed S1 {mean_c1:.3f} by >0.02; "
        f"observed gap {mean_c2 - mean_c1:+.3f}."
    )


def test_affect_outpaces_ideology_iyengar(s0_affect_engines, s3_affect_engines):
    """Iyengar et al. 2019 / Mason 2018 / Finkel et al. 2020 — affective
    polarization rises faster than ideological polarization through the
    same period.

    Operationalised here as: between **S0** (no parties, no affect) and
    S3 (parties + media + affect channel active for the full S2+S3
    period), |Δaffective_polarization| should be at least 2×
    Δideological_constraint AND clear a 0.20 absolute floor (so dialing
    `lr` down can't pass the ratio while breaking the qualitative
    claim). Measured: |Δaffect| ≈ 0.85 vs Δconstraint ≈ 0.15 —
    ratio ≈ 5.8×. The 2× threshold has a ~3.8× cushion.

    Uses the `*_affect_engines` fixtures (which keep AffectiveUpdate.lr
    at its bundle value) rather than the positional fixtures (which
    zero it for speed).
    """
    aff_s0 = [affective_polarization(e.agents) for e in s0_affect_engines]
    aff_s3 = [affective_polarization(e.agents) for e in s3_affect_engines]
    con_s0 = [constraint_avg(e) for e in s0_affect_engines]
    con_s3 = [constraint_avg(e) for e in s3_affect_engines]
    d_affect = abs(float(np.mean(aff_s3)) - float(np.mean(aff_s0)))
    d_constraint = float(np.mean(con_s3)) - float(np.mean(con_s0))
    assert d_affect > 0.20, (
        f"Absolute affect movement {d_affect:.3f} should exceed 0.20 — "
        f"a tiny ratio can pass the 2x check while losing the empirical "
        f"signal."
    )
    assert d_affect > 2.0 * d_constraint, (
        f"Affect should outpace ideology by at least 2x: "
        f"|d_affect|={d_affect:.3f}, d_constraint={d_constraint:.3f}, "
        f"ratio {d_affect / max(d_constraint, 1e-9):.2f}."
    )
    # Plus a direction check: affect must move negative (out-party
    # animus, not warmth) — the A1 sign-fix at the ensemble level.
    assert float(np.mean(aff_s3)) < float(np.mean(aff_s0)), (
        f"Affect should be more negative at S3 than S0: "
        f"S0={np.mean(aff_s0):+.3f}, S3={np.mean(aff_s3):+.3f}."
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
    # Re-blessed under Phase 4 (F1+F2+F3): media still pushes heavy-diet
    # agents outward, but anchoring (F1) and the graded filter (F2) dilute
    # the per-agent radial signal. Measured mean ~0.21 with one seed near
    # zero (0.001); the rest are clearly positive (range ~0.12-0.36).
    # Two-pronged assertion:
    #   1. Ensemble *mean* > 0.10 — sustains direction across seeds.
    #   2. ≥ 9 of 12 seeds yield a positive correlation — guards against
    #      the mean masking a directional break on a subset of seeds.
    assert mean_corr > 0.10, (
        f"Mean paired correlation {mean_corr:.3f} should exceed 0.10 — "
        f"per-seed correlations: {[round(c, 3) for c in correlations]}."
    )
    positive = sum(1 for c in correlations if c > 0.0)
    assert positive >= 9, (
        f"At least 9 of {len(correlations)} seeds should yield a positive "
        f"correlation; got {positive}. "
        f"Per-seed: {[round(c, 3) for c in correlations]}."
    )


# --- S4 (ADR-001 / Phase 3) ----------------------------------------------

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
    # Re-blessed under Phase 4: F3 (involuntary stratum) puts a structural
    # floor on cross-cutting exposure, so the drop is smaller than under
    # ADR-001 alone (measured 0.162 vs. today's ~0.25). The 0.10 threshold
    # has a ~0.06 cushion. Modularity rise measured 0.161; threshold
    # likewise at 0.10. The qualitative directions — cross-cutting falls,
    # modularity rises — are what the test guards.
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

# Re-opened bounded-confidence radius during the release phase. Wide enough
# that, on an unsorted social graph, the two camps would re-merge — so any
# residual separation in World A is attributable to *structure*, not to a
# narrow confidence radius.
RELEASE_EPSILON = 1.0


def _random_graph_matched_degree(node_ids, mean_degree: int, rng) -> Network:
    """Erdos-Renyi G(n, m) with m chosen to match ``mean_degree``.

    The release-phase World B graph: a homophily-free graph that shares
    the evolved World A's mean degree but none of its sorting. If the
    ratchet is structural, World A — which keeps its evolved homophilous
    graph — stays apart while World B's camps re-merge.
    """
    ids = list(node_ids)
    n = len(ids)
    target_edges = (n * mean_degree) // 2
    adjacency: dict[int, set[int]] = {i: set() for i in ids}
    placed = 0
    while placed < target_edges:
        i, j = int(rng.integers(n)), int(rng.integers(n))
        if i == j or ids[j] in adjacency[ids[i]]:
            continue
        adjacency[ids[i]].add(ids[j])
        adjacency[ids[j]].add(ids[i])
        placed += 1
    return Network(adjacency)


def _release_run(seed: int, swap_network: bool) -> float:
    """Serial reference for the paired ratchet experiment. The hot path
    (`test_s4_is_a_ratchet`) runs the seeds in parallel via
    `_parallel_workers.ratchet_release_worker`, which mirrors this function
    line-for-line; this version is kept as the readable spec / serial
    fallback (cf. `conftest._run_pillar_stage`).

    Paired ratchet helper: polarise through S4, then release the
    polarising forces (PartyPull, MediaConsumption) and reopen
    bounded-confidence to a wide radius. The only thing that distinguishes
    worlds A and B is the *graph*: World A keeps its evolved homophilous
    network; World B has it replaced by a homophily-free random graph of
    matched mean degree (ADR-001 impl-spec §11).
    """
    eng = positional_engine(4, seed)        # S4 with AffectiveUpdate.lr=0
    eng.run(TICKS)
    for r in eng.rules.rules:
        name = type(r).__name__
        if name == "PartyPull":
            r.strength = 0.0
        elif name == "MediaConsumption":
            r.strength = 0.0
        elif name == "BoundedConfidenceInfluence":
            r.epsilon = RELEASE_EPSILON
    for r in eng.env_rules:
        if type(r).__name__ == "TieRewiring":
            # Freeze the graph through the release phase — the experiment
            # tests whether the *current* graph holds the camps apart.
            r.rewire_rate = 0.0
    if swap_network:
        net: Network = eng.env.attrs["network"]
        n = len(eng.agents)
        m = sum(net.degree(a.id) for a in eng.agents)
        mean_degree = max(1, m // n)
        rng = np.random.default_rng(seed + 12345)
        eng.env.attrs["network"] = _random_graph_matched_degree(
            [a.id for a in eng.agents], mean_degree, rng
        )
    eng.run(RELEASE_TICKS)
    return party_separation(eng)


def test_s4_is_a_ratchet():
    """ADR-001 headline: a paired release experiment.

    Two identical worlds are polarised through S4, then released — the
    polarising forces drop, bounded-confidence reopens. World A keeps
    its evolved homophilous network; World B has the network replaced
    by a homophily-free random graph of matched mean degree. If S4 is a
    *structural* ratchet, World A stays apart while World B re-merges —
    the camps survive only because the graph keeps them apart.
    """
    # Run both worlds (swap=False, swap=True) for every seed in a single
    # parallel batch — bit-identical to the serial `_release_run` loop, but
    # the 40 release runs go across all cores instead of one at a time.
    from abm.calibration_parallel import run_seeds_parallel
    from ._parallel_workers import ratchet_release_worker

    k = len(STAGE_SEEDS)
    args = (
        [(seed, False) for seed in STAGE_SEEDS]
        + [(seed, True) for seed in STAGE_SEEDS]
    )
    results = run_seeds_parallel(ratchet_release_worker, args)
    sep_a, sep_b = results[:k], results[k:]
    mean_a, mean_b = float(np.mean(sep_a)), float(np.mean(sep_b))
    assert mean_a > mean_b + RATCHET_MARGIN, (
        f"S4 failed to act as a structural ratchet: sepA={mean_a:.3f} "
        f"vs sepB={mean_b:.3f} (gap {mean_a - mean_b:+.3f}, "
        f"needed > {RATCHET_MARGIN}). Per-seed: "
        f"A={[round(x, 3) for x in sep_a]} B={[round(x, 3) for x in sep_b]}."
    )


# Re-measured under Phase 4 (F1+F2+F3) at N=250, TICKS=200,
# STAGE_SEEDS=range(12): mean sepA=0.511, sepB=0.232, gap=+0.279.
# Phase 4 anchoring (F1) damps both worlds in the release phase: World B
# no longer collapses to ~0, and the absolute separation is smaller. The
# gap remains comfortably positive and tightly clustered across seeds
# (min per-seed gap +0.260). Margin pinned at 0.15 — a ~0.13 cushion below
# the measured gap, well under the worst-seed gap.
RATCHET_MARGIN = 0.15


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
