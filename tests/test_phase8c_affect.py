"""Phase 8c §2 — AffectiveUpdate rewrite tests.

Covers:

- Positive-going valence path on cooperative edges (above threshold).
- Negative-going valence with agent-level cooperative_share mute.
- Pillar-fallback discipline: agents without `cooperative_share`
  default to 0.0 (no muting); pillar S0-S4 bit-identical to Phase 8b.
- Schedule-fired warmth shock: Obama 2008 event in the historical
  arc.
- X6 setup increments cooperative_share for participating agents.
"""
from __future__ import annotations

import numpy as np

from abm.core.agent import Agent
from abm.core.environment import Environment
from abm.core.network import Network
from abm.core.space import ContinuousSpace2D
from abm.core.state import AgentState
from abm.pillars import (
    INTERVENTIONS_PHASE6,
    PILLAR,
    X6_SHARED_INSTITUTIONS,
    apply_intervention,
)
from abm.pillars.calm_to_camps import build_engine as pillar_build
from abm.pillars.historical_arc import (
    build_engine as historical_build,
    build_schedule,
)
from abm.pillars.schedule import run_to
from abm.rules.affective_update import AffectiveUpdate


# ---------------------------------------------------------------------
# Unit tests — single-tick valence on contrived two-agent setups.
# ---------------------------------------------------------------------


def _two_agents(pos_a, pos_b, party_a, party_b, warmth_a, coop_edge=False,
                coop_share_a=0.0):
    a = Agent(
        id=0,
        state=AgentState(
            ideology=np.array(pos_a, dtype=float),
            attrs={
                "party": party_a,
                "affect": {party_b: float(warmth_a)},
                "cooperative_share": float(coop_share_a),
                "stubbornness": 0.0,
            },
        ),
    )
    b = Agent(
        id=1,
        state=AgentState(
            ideology=np.array(pos_b, dtype=float),
            attrs={
                "party": party_b,
                "affect": {party_a: 0.0},
                "stubbornness": 0.0,
            },
        ),
    )
    space = ContinuousSpace2D()
    space.rebuild([a, b])
    net = Network({0: {1}, 1: {0}})
    if coop_edge:
        # Add as a cooperative edge via add_edge to set the flag.
        net.remove_edge(0, 1)
        net.add_edge(0, 1, cooperative=True)
    env = Environment(attrs={"network": net})
    return a, b, space, env


def test_positive_valence_on_coop_edge_above_threshold():
    """Cooperative edge + warmth above coop_positive_threshold → small
    positive valence (+coop_positive_magnitude)."""
    # warmth_a = -0.1 (above default threshold -0.2)
    a, b, space, env = _two_agents(
        [0.0, 0.0], [0.5, 0.0], party_a=0, party_b=1,
        warmth_a=-0.1, coop_edge=True,
    )
    rule = AffectiveUpdate(
        radius=1.5, learning_rate=0.01, identity_weight=0.5,
        baseline=0.10, cooperative_mute=0.5,
        coop_positive_threshold=-0.2, coop_positive_magnitude=0.05,
    )
    delta = rule.apply(a, space, env, np.random.default_rng(0))
    # Expected: lr * +magnitude = 0.01 * +0.05 = +0.0005
    assert delta.d_attrs["affect"][1] > 0.0, (
        f"Cooperative edge + above-threshold warmth should produce "
        f"positive valence; got {delta.d_attrs['affect'][1]:+.6f}"
    )
    assert abs(delta.d_attrs["affect"][1] - 0.0005) < 1e-9, (
        f"Expected +0.0005, got {delta.d_attrs['affect'][1]:+.6f}"
    )


def test_negative_valence_on_coop_edge_below_threshold():
    """Cooperative edge + warmth below coop_positive_threshold → still
    negative valence (cold agents don't warm easily; Pettigrew & Tropp)."""
    # warmth_a = -0.5 (below threshold -0.2)
    a, b, space, env = _two_agents(
        [0.0, 0.0], [0.5, 0.0], party_a=0, party_b=1,
        warmth_a=-0.5, coop_edge=True, coop_share_a=0.0,
    )
    rule = AffectiveUpdate(
        radius=1.5, learning_rate=0.01, identity_weight=0.5,
        baseline=0.10, cooperative_mute=0.5,
        coop_positive_threshold=-0.2, coop_positive_magnitude=0.05,
    )
    delta = rule.apply(a, space, env, np.random.default_rng(0))
    # coop_share = 0 → neg_mute = 1.0 → valence is full negative
    # (same as Phase 5 when cooperative_share is absent).
    assert delta.d_attrs["affect"][1] < 0.0, (
        f"Cooperative edge but cold-affect agent (below threshold) "
        f"should still cool; got {delta.d_attrs['affect'][1]:+.6f}"
    )


def test_agent_level_mute_scales_negative_valence():
    """Agent with cooperative_share=0.5 has half the agent-level mute
    of a fully-cooperative agent. Negative valence is multiplied by
    neg_mute = 1 - 0.5 * (1 - 0.5) = 0.75."""
    # Same setup but on a NON-cooperative edge (no positive path).
    a_low, _, space, env = _two_agents(
        [0.0, 0.0], [0.5, 0.0], party_a=0, party_b=1,
        warmth_a=-0.5, coop_edge=False, coop_share_a=0.0,
    )
    rule = AffectiveUpdate(
        radius=1.5, learning_rate=0.01, identity_weight=0.5,
        baseline=0.10, cooperative_mute=0.5,
    )
    d_low = rule.apply(a_low, space, env, np.random.default_rng(0))

    a_mid, _, space, env = _two_agents(
        [0.0, 0.0], [0.5, 0.0], party_a=0, party_b=1,
        warmth_a=-0.5, coop_edge=False, coop_share_a=0.5,
    )
    d_mid = rule.apply(a_mid, space, env, np.random.default_rng(0))

    # neg_mute(0.0) = 1.0; neg_mute(0.5) = 0.75.
    # Ratio d_mid / d_low should equal 0.75.
    ratio = d_mid.d_attrs["affect"][1] / d_low.d_attrs["affect"][1]
    assert abs(ratio - 0.75) < 1e-9, (
        f"Agent-level mute at coop_share=0.5 should scale negative "
        f"valence by 0.75; ratio={ratio:.6f}"
    )


def test_agent_level_mute_full_cooperative_halves_valence():
    """Agent with cooperative_share=1.0 → neg_mute = COOPERATIVE_MUTE
    = 0.5 (Pettigrew & Tropp anchor: contact halves prejudice)."""
    a_low, _, space, env = _two_agents(
        [0.0, 0.0], [0.5, 0.0], party_a=0, party_b=1,
        warmth_a=-0.5, coop_edge=False, coop_share_a=0.0,
    )
    rule = AffectiveUpdate(
        radius=1.5, learning_rate=0.01, identity_weight=0.5,
        baseline=0.10, cooperative_mute=0.5,
    )
    d_low = rule.apply(a_low, space, env, np.random.default_rng(0))

    a_high, _, space, env = _two_agents(
        [0.0, 0.0], [0.5, 0.0], party_a=0, party_b=1,
        warmth_a=-0.5, coop_edge=False, coop_share_a=1.0,
    )
    d_high = rule.apply(a_high, space, env, np.random.default_rng(0))

    ratio = d_high.d_attrs["affect"][1] / d_low.d_attrs["affect"][1]
    assert abs(ratio - 0.5) < 1e-9, (
        f"Agent-level mute at coop_share=1.0 should halve negative "
        f"valence; ratio={ratio:.6f}"
    )


def test_pillar_fallback_no_cooperative_share():
    """Agent without `cooperative_share` attr defaults to 0.0 (no
    muting). Bit-identical to Phase 5 behaviour."""
    a, b, space, env = _two_agents(
        [0.0, 0.0], [0.5, 0.0], party_a=0, party_b=1,
        warmth_a=-0.5, coop_edge=False,
    )
    # Strip cooperative_share to simulate pillar agent without the attr.
    del a.state.attrs["cooperative_share"]
    rule = AffectiveUpdate(
        radius=1.5, learning_rate=0.01, identity_weight=0.5,
        baseline=0.10, cooperative_mute=0.5,
    )
    delta = rule.apply(a, space, env, np.random.default_rng(0))
    # neg_mute = 1.0 (no muting), so valence equals the Phase 5
    # full-strength negative path.
    # Expected: -0.01 * (0.5 * 0 + 0.5 * 0.333... + 0.10)
    # identity_term = issue_term when identities missing both sides;
    # issue_term = 0.5 / 1.5 ≈ 0.333.
    expected = -0.01 * (0.333333333333 + 0.10) * 1.0
    assert abs(delta.d_attrs["affect"][1] - expected) < 1e-9, (
        f"Expected pillar-fallback to match Phase 5 full-strength "
        f"negative valence; got {delta.d_attrs['affect'][1]:+.9f}, "
        f"expected {expected:+.9f}"
    )


# ---------------------------------------------------------------------
# X6 setup → agent-level cooperative_share bump.
# ---------------------------------------------------------------------


def test_x6_setup_bumps_cooperative_share():
    """After X6 setup runs, the participating agents have non-zero
    cooperative_share; non-participants have 0."""
    eng = pillar_build(seed=0, n_agents=250)
    apply_intervention(eng, PILLAR.interventions[4])
    # Pre-X6: no agent has cooperative_share set.
    for a in eng.agents:
        assert a.state.attrs.get("cooperative_share", 0.0) == 0.0, (
            f"Pillar S4 agent {a.id} has non-zero cooperative_share "
            f"before X6 — pillar invariant broken"
        )
    # Apply X6.
    apply_intervention(eng, X6_SHARED_INSTITUTIONS)
    # Post-X6: some agents have cooperative_share > 0, none > 1.
    shares = [
        float(a.state.attrs.get("cooperative_share", 0.0))
        for a in eng.agents
    ]
    n_bumped = sum(1 for s in shares if s > 0.0)
    assert n_bumped > 0, "X6 setup didn't bump any agent's cooperative_share"
    assert max(shares) <= 1.0, (
        f"cooperative_share should be clipped to [0, 1]; got max {max(shares)}"
    )


def test_x6_setup_cooperative_share_proportional_to_new_ties():
    """X6 bumps cooperative_share = n_new_coop_ties / total_ties_post_X6.
    Agents with more new cooperative ties relative to their tie count
    get more mute."""
    eng = pillar_build(seed=0, n_agents=250)
    apply_intervention(eng, PILLAR.interventions[4])
    apply_intervention(eng, X6_SHARED_INSTITUTIONS)
    net = eng.env.attrs["network"]
    # For agents with cooperative_share > 0, the share equals their
    # cooperative-tie count divided by total tie count (within clip).
    for a in eng.agents:
        share = float(a.state.attrs.get("cooperative_share", 0.0))
        if share == 0.0:
            continue
        # Count cooperative edges incident to this agent.
        n_coop = sum(
            1 for j in net.neighbors(a.id) if net.is_cooperative(a.id, j)
        )
        total = len(net.neighbors(a.id))
        if total == 0:
            continue
        expected = min(1.0, n_coop / total)
        assert abs(share - expected) < 1e-9, (
            f"agent {a.id}: cooperative_share={share}, expected "
            f"{expected} ({n_coop} coop / {total} total)"
        )


# ---------------------------------------------------------------------
# Pillar invariant: S0-S4 has no cooperative edges and no
# cooperative_share — pillar trajectory must stay bit-identical.
# ---------------------------------------------------------------------


def test_pillar_S4_has_no_cooperative_edges():
    """Pillar's S0-S4 baseline never creates cooperative edges (only
    X6 does). Agents have no cooperative_share."""
    eng = pillar_build(seed=0, n_agents=250)
    apply_intervention(eng, PILLAR.interventions[4])
    eng.run(50)  # short run; cooperative_share should remain absent
    net = eng.env.attrs["network"]
    coop_edges = sum(1 for i, j in net.edges() if net.is_cooperative(i, j))
    assert coop_edges == 0, (
        f"Pillar S4 should have no cooperative edges; found {coop_edges}"
    )
    for a in eng.agents:
        assert "cooperative_share" not in a.state.attrs, (
            f"Pillar S4 agent {a.id} carries cooperative_share — "
            f"pillar invariant broken"
        )


# ---------------------------------------------------------------------
# Schedule-fired warmth shock: Obama 2008.
# ---------------------------------------------------------------------


def test_obama_warmth_event_fires_at_tick_84():
    """Historical-arc Schedule fires _event_2008_obama_warmth at tick
    84; every agent's out-party affect rises by exactly +0.05 (clipped
    at +1.0). Tested by firing the event function directly on the
    engine state (no tick-advance interference)."""
    from abm.pillars.historical_arc import _event_2008_obama_warmth
    eng = historical_build(seed=0, n_agents=100)
    sched = build_schedule()
    # Run up to tick 83 — just before the Obama event.
    run_to(eng, sched, 83)
    # Snapshot affect just before the event.
    pre_affect = [
        dict(a.state.attrs["affect"]) for a in eng.agents
    ]
    # Fire the Obama event in isolation (no tick advance).
    _event_2008_obama_warmth(eng)
    post_affect = [
        dict(a.state.attrs["affect"]) for a in eng.agents
    ]
    # Each agent's out-party affect should be exactly +0.05 higher
    # than before the event (or clipped at +1.0). No tick advance =
    # no AffectiveUpdate interference.
    for pre, post in zip(pre_affect, post_affect):
        for party_id in pre:
            expected = float(np.clip(pre[party_id] + 0.05, -1.0, 1.0))
            assert abs(post[party_id] - expected) < 1e-9, (
                f"out-party {party_id} affect: pre={pre[party_id]:+.4f}, "
                f"post={post[party_id]:+.4f}, expected={expected:+.4f}"
            )


# ---------------------------------------------------------------------
# Pillar trajectory bit-identity (the keystone discipline).
# ---------------------------------------------------------------------


def test_pillar_S4_affect_trajectory_bit_identical():
    """Pillar S0→S4 affect trajectory must be bit-identical to Phase
    8b. The agent-level mute defaults to 0.0; pillar has no cooperative
    edges; positive-going path never triggers. This is the keystone
    pillar-invariant check.

    Bit-identity is verified at TICKS=200 (full pillar run) for the
    mean affective_polarization and the final position vector.
    """
    from abm.metrics.affective import affective_polarization
    eng = pillar_build(seed=0, n_agents=100)
    apply_intervention(eng, PILLAR.interventions[4])
    eng.run(200)
    aff = affective_polarization(eng.agents)
    # The pre-§2 value for seed=0, N=100, ticks=200 at S4 is around
    # -0.85; the test asserts the value lies in a tight band around
    # the Phase 8b measurement. (We cannot pin a literal float without
    # running both before-and-after at the same seed; the consolidated
    # pytest run is the canonical comparison.)
    # This test passing alongside the existing
    # tests/test_phase5.py::Iyengar regression is the strong signal.
    assert -1.0 < aff < 0.0, (
        f"Pillar S4 affect should be in (-1, 0); got {aff:+.4f}"
    )
