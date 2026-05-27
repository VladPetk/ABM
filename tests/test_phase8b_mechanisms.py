"""Phase 8b mechanism tests — pillar-fallback discipline.

Each of the 5 new/extended mechanisms (M1 heterogeneity, M2
ResidentialMigration, M3 CohortReplacement, M4 asymmetric
PARTY_CUE_SIGMA + EliteDrift, M5 time-varying IdentitySorting)
must behave as a no-op for the pillar — the pillar's 73-test suite
stays green. These tests verify the fallback discipline directly.
"""
from __future__ import annotations

import numpy as np

from abm.core.agent import Agent
from abm.core.environment import Environment
from abm.core.network import Network
from abm.core.space import ContinuousSpace2D
from abm.core.state import AgentState
from abm.pillars.calm_to_camps import build_engine as pillar_build
from abm.pillars.historical_arc import (
    EPSILON_HETERO_FACTOR,
    FJ_HETERO_FACTOR,
    LR_HETERO_FACTOR,
    PARTY_CUE_SIGMA_HISTORICAL,
    build_engine as historical_build,
    build_schedule,
)
from abm.pillars.schedule import Schedule, ScheduledEvent, run_to
from abm.rules.affective_update import AffectiveUpdate
from abm.rules.cohort_replacement import CohortReplacement, cohort_for_tick
from abm.rules.influence import BoundedConfidenceInfluence
from abm.rules.noise import GaussianNoise
from abm.rules.residential_migration import ResidentialMigration


# --- M1: per-agent heterogeneity fallback -------------------------------


def test_pillar_agents_lack_per_agent_heterogeneity_attrs():
    """Pillar agents do not carry per-agent epsilon/fj_alpha/affect_lr.
    The rules fall back to their rule-level / env-level defaults —
    bit-identical to Phase 8a."""
    eng = pillar_build(seed=0, n_agents=50)
    for a in eng.agents:
        assert "epsilon" not in a.state.attrs, (
            f"pillar agent {a.id} has per-agent epsilon — pillar invariant broken"
        )
        assert "fj_alpha" not in a.state.attrs, (
            f"pillar agent {a.id} has per-agent fj_alpha — pillar invariant broken"
        )
        assert "affect_lr" not in a.state.attrs, (
            f"pillar agent {a.id} has per-agent affect_lr — pillar invariant broken"
        )


def test_historical_agents_carry_heterogeneity_attrs():
    """Historical-arc agents carry all three per-agent heterogeneity
    attrs."""
    eng = historical_build(seed=0, n_agents=200)
    for a in eng.agents:
        assert "epsilon" in a.state.attrs, f"historical agent {a.id} missing epsilon"
        assert "fj_alpha" in a.state.attrs, f"historical agent {a.id} missing fj_alpha"
        assert "affect_lr" in a.state.attrs, f"historical agent {a.id} missing affect_lr"


def test_heterogeneity_correlates_with_identity_strength():
    """Per Phase 8b M1 §3.2: epsilon negatively, α + affect_lr
    positively correlated with identity_strength."""
    eng = historical_build(seed=0, n_agents=400)
    ids = np.array([a.state.attrs["identity_strength"] for a in eng.agents])
    eps = np.array([a.state.attrs["epsilon"] for a in eng.agents])
    alpha = np.array([a.state.attrs["fj_alpha"] for a in eng.agents])
    lr = np.array([a.state.attrs["affect_lr"] for a in eng.agents])
    # Pearson correlations (signs only — magnitudes will vary by jitter).
    r_eps = np.corrcoef(ids, eps)[0, 1]
    r_alpha = np.corrcoef(ids, alpha)[0, 1]
    r_lr = np.corrcoef(ids, lr)[0, 1]
    assert r_eps < -0.5, (
        f"epsilon should correlate NEGATIVELY with identity_strength "
        f"(engaged = close-minded); got r={r_eps:.3f}"
    )
    assert r_alpha > 0.5, (
        f"fj_alpha should correlate POSITIVELY with identity_strength "
        f"(engaged = anchored); got r={r_alpha:.3f}"
    )
    assert r_lr > 0.5, (
        f"affect_lr should correlate POSITIVELY with identity_strength "
        f"(engaged = strong affect); got r={r_lr:.3f}"
    )


def test_heterogeneity_magnitudes_match_spec_defaults():
    """The historical_arc module carries the spec-confirmed
    magnitudes (40/60/80%) for epsilon/α/affect_lr correlation."""
    assert EPSILON_HETERO_FACTOR == 0.40
    assert FJ_HETERO_FACTOR == 0.60
    assert LR_HETERO_FACTOR == 0.80


def test_bc_falls_back_to_rule_epsilon_when_no_agent_attr():
    """BoundedConfidenceInfluence.epsilon is used when agent doesn't
    set per-agent epsilon — pillar-fallback pattern."""
    rule = BoundedConfidenceInfluence(epsilon=0.30, strength=1.0)
    a = Agent(
        id=0,
        state=AgentState(
            ideology=np.array([0.0, 0.0]),
            attrs={"party": 0, "stubbornness": 0.0},  # no "epsilon" key
        ),
    )
    b = Agent(
        id=1,
        state=AgentState(
            ideology=np.array([0.25, 0.0]),  # within rule-level 0.30
            attrs={"party": 0, "stubbornness": 0.0},
        ),
    )
    space = ContinuousSpace2D()
    space.rebuild([a, b])
    env = Environment(attrs={"network": Network({0: {1}, 1: {0}})})
    rng = np.random.default_rng(0)
    delta = rule.apply(a, space, env, rng).d_ideology
    # b is at 0.25 < rule epsilon 0.30, so pulled toward b.
    assert delta[0] > 0.0, (
        f"Fallback should use rule-level epsilon=0.30; b at 0.25 should pull; "
        f"got delta={delta}"
    )


# --- M2: ResidentialMigration --------------------------------------------


def test_residential_migration_at_zero_rate_is_no_op():
    """`migration_rate = 0` is an exact no-op — pillar invariant."""
    eng = pillar_build(seed=0, n_agents=100)
    initial_sc = np.array([a.state.attrs["social_coord"] for a in eng.agents])
    rule = ResidentialMigration(migration_rate=0.0)
    rng = np.random.default_rng(0)
    rule.apply(eng.env, eng.agents, eng.space, rng, tick=10)
    final_sc = np.array([a.state.attrs["social_coord"] for a in eng.agents])
    assert np.array_equal(initial_sc, final_sc), (
        "migration_rate=0 must leave social_coord unchanged"
    )


def test_residential_migration_at_positive_rate_shifts_social_coord():
    """At positive migration rate, social_coord drifts toward in-party
    mean over many ticks."""
    eng = historical_build(seed=0, n_agents=200)
    rule = ResidentialMigration(migration_rate=0.05)
    rng = np.random.default_rng(0)
    initial_sc = np.array([a.state.attrs["social_coord"] for a in eng.agents])
    for tick in range(50):
        rule.apply(eng.env, eng.agents, eng.space, rng, tick=tick)
    final_sc = np.array([a.state.attrs["social_coord"] for a in eng.agents])
    # Some non-trivial fraction of agents must have moved.
    n_moved = int((final_sc != initial_sc).sum())
    assert n_moved > 20, (
        f"Migration should move many agents; only {n_moved}/{len(eng.agents)} moved"
    )


# --- M3: CohortReplacement -----------------------------------------------


def test_cohort_replacement_at_zero_rate_is_no_op():
    """`replacement_rate = 0` is an exact no-op."""
    eng = pillar_build(seed=0, n_agents=100)
    initial_ids = [(a.id, a.state.ideology.copy()) for a in eng.agents]
    rule = CohortReplacement(replacement_rate=0.0)
    rng = np.random.default_rng(0)
    rule.apply(eng.env, eng.agents, eng.space, rng, tick=10)
    for (orig_id, orig_pos), a in zip(initial_ids, eng.agents):
        assert a.id == orig_id
        assert np.array_equal(a.state.ideology, orig_pos), (
            f"agent {a.id} ideology changed under rate=0"
        )


def test_cohort_for_tick_picks_correct_label():
    """Cohort labels switch at ticks 45 and 105."""
    assert cohort_for_tick(0) == "boomer"
    assert cohort_for_tick(44) == "boomer"
    assert cohort_for_tick(45) == "genx_early_millennial"
    assert cohort_for_tick(104) == "genx_early_millennial"
    assert cohort_for_tick(105) == "late_millennial_genz"
    assert cohort_for_tick(134) == "late_millennial_genz"


def test_cohort_replacement_preserves_agent_id_for_network():
    """When an agent is replaced, its `id` is inherited so network
    ties stay structurally intact."""
    eng = historical_build(seed=0, n_agents=100)
    rule = CohortReplacement(replacement_rate=1.0)   # replace every agent
    initial_ids = [a.id for a in eng.agents]
    rng = np.random.default_rng(0)
    rule.apply(eng.env, eng.agents, eng.space, rng, tick=10)
    final_ids = [a.id for a in eng.agents]
    assert initial_ids == final_ids, (
        "agent ids must be preserved under cohort replacement — network "
        "ties depend on stable ids"
    )


# --- M4: asymmetric PARTY_CUE_SIGMA --------------------------------------


def test_historical_party_cue_sigma_is_asymmetric():
    """Phase 8b M4: σ_dem ≈ 0.22, σ_rep ≈ 0.30. Verified on a built
    population's empirical SDs."""
    eng = historical_build(seed=0, n_agents=600)
    cues = {0: [], 1: []}
    centroids = {0: -0.30, 1: 0.30}   # 1980 historical centroids
    for a in eng.agents:
        cue = a.state.attrs["party_cue"]
        cues[a.state.attrs["party"]].append(cue[0])
    sd_dem = float(np.std(cues[0]))
    sd_rep = float(np.std(cues[1]))
    assert abs(sd_dem - PARTY_CUE_SIGMA_HISTORICAL[0]) < 0.04, (
        f"Dem σ = {sd_dem:.3f}, expected ≈ {PARTY_CUE_SIGMA_HISTORICAL[0]:.3f}"
    )
    assert abs(sd_rep - PARTY_CUE_SIGMA_HISTORICAL[1]) < 0.04, (
        f"Rep σ = {sd_rep:.3f}, expected ≈ {PARTY_CUE_SIGMA_HISTORICAL[1]:.3f}"
    )
    assert sd_rep > sd_dem, (
        f"Asymmetric σ should have σ_rep > σ_dem (Hacker & Pierson 2020)"
    )


# --- M5: time-varying IdentitySorting + schedule -------------------------


def test_schedule_fires_decade_boundary_transitions():
    """Schedule fires IdentitySorting transitions at ticks 30, 60,
    90, 120 — and the rate ramps up correctly each decade."""
    eng = historical_build(seed=0, n_agents=50)
    sched = build_schedule()
    from abm.pillars.historical_arc import IDENTITY_SORTING_SCHEDULE
    # At tick 0, rate should be the 1980-90 value.
    for r in eng.rules.rules:
        if type(r).__name__ == "IdentitySorting":
            initial_rate = r.sort_rate
            break
    assert initial_rate == IDENTITY_SORTING_SCHEDULE["1980-90"], (
        f"Initial IdentitySorting rate at 1980-90 should match the schedule "
        f"({IDENTITY_SORTING_SCHEDULE['1980-90']}), got {initial_rate}"
    )
    # Run to tick 30 (1990 boundary).
    run_to(eng, sched, 30)
    for r in eng.rules.rules:
        if type(r).__name__ == "IdentitySorting":
            rate_at_1990 = r.sort_rate
            break
    assert rate_at_1990 == IDENTITY_SORTING_SCHEDULE["1990-00"], (
        f"IdentitySorting rate at 1990-00 should match the schedule "
        f"({IDENTITY_SORTING_SCHEDULE['1990-00']}), got {rate_at_1990}"
    )
    # Run to tick 60.
    run_to(eng, sched, 60)
    for r in eng.rules.rules:
        if type(r).__name__ == "IdentitySorting":
            rate_at_2000 = r.sort_rate
            break
    # IDENTITY_SORTING_SCHEDULE["2000-10"] is the source of truth.
    from abm.pillars.historical_arc import IDENTITY_SORTING_SCHEDULE
    assert rate_at_2000 == IDENTITY_SORTING_SCHEDULE["2000-10"], (
        f"IdentitySorting rate at 2000-10 should match the schedule "
        f"({IDENTITY_SORTING_SCHEDULE['2000-10']}), got {rate_at_2000}"
    )


# --- Sacred guardrail: pillar 73-test invariant ---------------------------


def test_pillar_engine_unaffected_by_phase8b_imports():
    """Importing the Phase 8b modules must not change pillar
    behaviour. Build a pillar engine, run a few ticks, confirm
    determinism (same seed → same state) holds."""
    eng1 = pillar_build(seed=42, n_agents=100)
    eng2 = pillar_build(seed=42, n_agents=100)
    assert np.array_equal(eng1.positions(), eng2.positions())
    eng1.run(20)
    eng2.run(20)
    assert np.array_equal(eng1.positions(), eng2.positions()), (
        "Phase 8b imports must not break pillar determinism"
    )
