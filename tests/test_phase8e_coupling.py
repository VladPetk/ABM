"""Phase 8e §2 — party-issue coupling tests.

Covers:

- PartyPull reads `party_issue_coupling` env-attr with fallback 1.0;
  pillar bit-identical.
- AffectiveUpdate reads `party_issue_coupling` and scales issue_term;
  pillar bit-identical.
- Historical_arc env carries the per-decade schedule; decade-boundary
  events update env.attrs["party_issue_coupling"].
"""
from __future__ import annotations

import numpy as np

from abm.core.agent import Agent
from abm.core.environment import Environment
from abm.core.network import Network
from abm.core.space import ContinuousSpace2D
from abm.core.state import AgentState
from abm.pillars import PILLAR, apply_intervention
from abm.pillars.calm_to_camps import build_engine as pillar_build
from abm.pillars.historical_arc import (
    PARTY_ISSUE_COUPLING_SCHEDULE,
    build_engine as historical_build,
    build_schedule,
)
from abm.pillars.schedule import run_to
from abm.rules.affective_update import AffectiveUpdate
from abm.rules.party_pull import PartyPull


def test_party_pull_pillar_fallback_coupling_1():
    """PartyPull at coupling=1.0 (pillar default, no env attr) is
    bit-identical to Phase 8d behaviour. The pillar must remain
    bit-identical."""
    rule = PartyPull(strength=0.05)
    a = Agent(
        id=0,
        state=AgentState(
            ideology=np.array([-0.2, 0.0]),
            attrs={
                "party": 0,
                "party_cue": np.array([-0.5, 0.0]),
                "identity_strength": 0.6,
                "stubbornness": 0.0,
            },
        ),
    )
    space = ContinuousSpace2D()
    space.rebuild([a])
    # No party_issue_coupling in env → fallback 1.0 → same as pre-8e
    env = Environment(attrs={"parties": {0: np.array([-0.5, 0.0])}})
    delta = rule.apply(a, space, env, np.random.default_rng(0))
    # Expected: 0.05 * 1.0 * 0.6 * ([-0.5, 0] - [-0.2, 0]) = -0.009 on x.
    expected_x = 0.05 * 1.0 * 0.6 * (-0.5 - -0.2)
    assert abs(delta.d_ideology[0] - expected_x) < 1e-9


def test_party_pull_coupling_scales_magnitude():
    """PartyPull magnitude halves when coupling=0.5."""
    rule = PartyPull(strength=0.05)
    a = Agent(
        id=0,
        state=AgentState(
            ideology=np.array([-0.2, 0.0]),
            attrs={
                "party": 0,
                "party_cue": np.array([-0.5, 0.0]),
                "identity_strength": 0.6,
                "stubbornness": 0.0,
            },
        ),
    )
    space = ContinuousSpace2D()
    space.rebuild([a])
    # Coupling = 0.5 → half pull magnitude
    env = Environment(attrs={
        "parties": {0: np.array([-0.5, 0.0])},
        "party_issue_coupling": 0.5,
    })
    delta = rule.apply(a, space, env, np.random.default_rng(0))
    expected_x = 0.05 * 0.5 * 0.6 * (-0.5 - -0.2)
    assert abs(delta.d_ideology[0] - expected_x) < 1e-9


def test_affective_update_pillar_fallback_coupling_1():
    """AffectiveUpdate at coupling=1.0 (pillar default) is bit-
    identical to Phase 8d."""
    rule = AffectiveUpdate(
        radius=1.5, learning_rate=0.01, identity_weight=0.5,
        baseline=0.10, cooperative_mute=0.5,
    )
    a = Agent(
        id=0,
        state=AgentState(
            ideology=np.array([-0.3, 0.0]),
            attrs={
                "party": 0,
                "affect": {1: -0.5},
                "stubbornness": 0.0,
            },
        ),
    )
    b = Agent(
        id=1,
        state=AgentState(
            ideology=np.array([0.5, 0.0]),
            attrs={"party": 1, "affect": {0: 0.0}, "stubbornness": 0.0},
        ),
    )
    space = ContinuousSpace2D()
    space.rebuild([a, b])
    env = Environment(attrs={"network": Network({0: {1}, 1: {0}})})
    delta = rule.apply(a, space, env, np.random.default_rng(0))
    # No coupling attr → 1.0 → same expected value as Phase 8d.
    # d_iss = 0.8, issue_term = 0.8/1.5, identity_term = same (no
    # identities), disagreement = 0.5*it + 0.5*1.0*it = it.
    expected_value = 0.01 * -((0.8/1.5) + 0.10)
    assert abs(delta.d_attrs["affect"][1] - expected_value) < 1e-9


def test_affective_update_coupling_scales_issue_term():
    """Coupling=0.5 reduces issue_term's contribution; net negative
    valence is smaller in magnitude."""
    rule = AffectiveUpdate(
        radius=1.5, learning_rate=0.01, identity_weight=0.5,
        baseline=0.10, cooperative_mute=0.5,
    )
    # Make agent + neighbour with identities (so identity_term and
    # issue_term differ).
    a = Agent(
        id=0,
        state=AgentState(
            ideology=np.array([-0.3, 0.0]),
            attrs={
                "party": 0,
                "affect": {1: -0.5},
                "identities": np.array([-0.5, -0.5, -0.5]),
                "stubbornness": 0.0,
            },
        ),
    )
    b = Agent(
        id=1,
        state=AgentState(
            ideology=np.array([0.5, 0.0]),
            attrs={
                "party": 1,
                "affect": {0: 0.0},
                "identities": np.array([0.5, 0.5, 0.5]),
                "stubbornness": 0.0,
            },
        ),
    )
    space = ContinuousSpace2D()
    space.rebuild([a, b])

    env_full = Environment(attrs={
        "network": Network({0: {1}, 1: {0}}),
        "party_issue_coupling": 1.0,
    })
    space.rebuild([a, b])
    d_full = rule.apply(a, space, env_full, np.random.default_rng(0))

    a.state.attrs["affect"] = {1: -0.5}  # reset
    env_low = Environment(attrs={
        "network": Network({0: {1}, 1: {0}}),
        "party_issue_coupling": 0.4,
    })
    space.rebuild([a, b])
    d_low = rule.apply(a, space, env_low, np.random.default_rng(0))

    # At lower coupling, issue_term contributes less → less negative
    # valence (smaller |Δ|).
    assert abs(d_low.d_attrs["affect"][1]) < abs(d_full.d_attrs["affect"][1])


def test_historical_arc_seeds_party_issue_coupling_attr():
    """Historical_arc build wires party_issue_coupling into env at
    the 1980-90 schedule value (0.40)."""
    eng = historical_build(seed=0, n_agents=50)
    env_val = eng.env.attrs.get("party_issue_coupling")
    assert env_val == PARTY_ISSUE_COUPLING_SCHEDULE["1980-90"]


def test_decade_boundary_updates_coupling():
    """Each decade-boundary event updates party_issue_coupling per
    the schedule."""
    eng = historical_build(seed=0, n_agents=50)
    sched = build_schedule()
    # Tick 0 (1980-90 default).
    assert eng.env.attrs["party_issue_coupling"] == PARTY_ISSUE_COUPLING_SCHEDULE["1980-90"]
    # Run to tick 30 (1990 boundary).
    run_to(eng, sched, 30)
    assert eng.env.attrs["party_issue_coupling"] == PARTY_ISSUE_COUPLING_SCHEDULE["1990-00"]
    # Run to tick 60 (2000 boundary).
    run_to(eng, sched, 60)
    assert eng.env.attrs["party_issue_coupling"] == PARTY_ISSUE_COUPLING_SCHEDULE["2000-10"]
    # Run to tick 90 (2010 boundary).
    run_to(eng, sched, 90)
    assert eng.env.attrs["party_issue_coupling"] == PARTY_ISSUE_COUPLING_SCHEDULE["2010-20"]
    # Run to tick 120 (2020 boundary).
    run_to(eng, sched, 120)
    assert eng.env.attrs["party_issue_coupling"] == PARTY_ISSUE_COUPLING_SCHEDULE["2020-25"]


def test_pillar_S4_bit_identical_under_coupling_default():
    """Phase 8e §2 keystone: the pillar's S0-S4 trajectory at the
    default coupling=1.0 (env attr absent) is bit-identical to
    Phase 8d. The pillar invariant must hold."""
    eng_a = pillar_build(seed=0, n_agents=100)
    apply_intervention(eng_a, PILLAR.interventions[4])
    eng_a.run(50)
    eng_b = pillar_build(seed=0, n_agents=100)
    # Explicitly set coupling = 1.0 to test the active code path
    # against absent attr.
    eng_b.env.attrs["party_issue_coupling"] = 1.0
    apply_intervention(eng_b, PILLAR.interventions[4])
    eng_b.run(50)
    pos_a = np.array([a.state.ideology for a in eng_a.agents])
    pos_b = np.array([a.state.ideology for a in eng_b.agents])
    assert np.allclose(pos_a, pos_b, atol=1e-12), (
        f"Bit-identity broken at coupling=1.0 vs absent: max diff = "
        f"{np.max(np.abs(pos_a - pos_b)):.2e}"
    )
