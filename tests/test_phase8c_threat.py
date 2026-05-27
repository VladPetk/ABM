"""Phase 8c §5 — identity-threat mechanism tests.

Covers:

- ThreatDecay env-rule decays perceived_threat by `(1 - decay_rate)`
  per tick, with half-life ~14 ticks at the default 0.05 rate.
- AffectiveUpdate amplifies negative valence by
  `(1 + threat_amplification * perceived_threat)`.
- AffectiveUpdate does NOT amplify positive (cooperative) valence.
- BacklashRepulsion amplifies push magnitude by the same factor.
- Pillar-fallback: agents without `perceived_threat` read 0.0;
  threat_factor = 1.0; bit-identical to Phase 8c §4.
- 2016 historical event fires for 60% of party=1 agents.
- Pillar invariant: pillar agents never carry `perceived_threat`.
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
    THREAT_2016_MAGNITUDE,
    THREAT_2016_R_FRACTION,
    build_engine as historical_build,
    build_schedule,
)
from abm.pillars.schedule import run_to
from abm.rules.affective_update import AffectiveUpdate
from abm.rules.repulsion import BacklashRepulsion
from abm.rules.threat_dynamics import ThreatDecay


# ---------------------------------------------------------------------
# ThreatDecay env-rule
# ---------------------------------------------------------------------


def test_threat_decay_decays_at_rate():
    """ThreatDecay multiplies perceived_threat by (1 - decay_rate)
    per tick."""
    a = Agent(
        id=0,
        state=AgentState(
            ideology=np.array([0.0, 0.0]),
            attrs={"party": 0, "perceived_threat": 1.0},
        ),
    )
    rule = ThreatDecay(decay_rate=0.05)
    rule.apply(env=None, agents=[a], space=None, rng=None, tick=1)
    assert abs(a.state.attrs["perceived_threat"] - 0.95) < 1e-9


def test_threat_decay_half_life_14_ticks():
    """At decay_rate=0.05, threat halves in ~14 ticks (per spec
    Mutz-2018 anchor)."""
    a = Agent(
        id=0,
        state=AgentState(
            ideology=np.array([0.0, 0.0]),
            attrs={"party": 0, "perceived_threat": 1.0},
        ),
    )
    rule = ThreatDecay(decay_rate=0.05)
    for t in range(14):
        rule.apply(env=None, agents=[a], space=None, rng=None, tick=t)
    # (1 - 0.05)^14 ≈ 0.488 — within tolerance of half.
    assert 0.45 < a.state.attrs["perceived_threat"] < 0.55


def test_threat_decay_zero_rate_no_op():
    """decay_rate=0 short-circuits."""
    a = Agent(
        id=0,
        state=AgentState(
            ideology=np.array([0.0, 0.0]),
            attrs={"party": 0, "perceived_threat": 0.5},
        ),
    )
    rule = ThreatDecay(decay_rate=0.0)
    rule.apply(env=None, agents=[a], space=None, rng=None, tick=1)
    assert a.state.attrs["perceived_threat"] == 0.5


def test_threat_decay_skips_agents_without_attr():
    """Pillar-fallback: agents without the attr are skipped (no
    error, no write)."""
    a = Agent(
        id=0,
        state=AgentState(
            ideology=np.array([0.0, 0.0]),
            attrs={"party": 0},  # no perceived_threat
        ),
    )
    rule = ThreatDecay(decay_rate=0.05)
    rule.apply(env=None, agents=[a], space=None, rng=None, tick=1)
    assert "perceived_threat" not in a.state.attrs


# ---------------------------------------------------------------------
# AffectiveUpdate threat amplification (negative path only).
# ---------------------------------------------------------------------


def _two_agents_for_threat(threat_a):
    a = Agent(
        id=0,
        state=AgentState(
            ideology=np.array([-0.3, 0.0]),
            attrs={
                "party": 0,
                "affect": {1: -0.5},
                "stubbornness": 0.0,
                "perceived_threat": float(threat_a),
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
    return a, b, space, env


def test_threat_amplifies_negative_valence_in_affective_update():
    """Agent with perceived_threat=1.0 cools ~2× as fast as agent
    with perceived_threat=0.0 (threat_factor = 1 + 1*1 = 2)."""
    rule = AffectiveUpdate(
        radius=1.5, learning_rate=0.01, identity_weight=0.5,
        baseline=0.10, cooperative_mute=0.5, threat_amplification=1.0,
    )
    a_low, _, space, env = _two_agents_for_threat(threat_a=0.0)
    d_low = rule.apply(a_low, space, env, np.random.default_rng(0))

    a_high, _, space, env = _two_agents_for_threat(threat_a=1.0)
    d_high = rule.apply(a_high, space, env, np.random.default_rng(0))

    # threat=1.0 → factor 2.0; valence should be 2× as negative.
    ratio = d_high.d_attrs["affect"][1] / d_low.d_attrs["affect"][1]
    assert abs(ratio - 2.0) < 1e-9, (
        f"threat=1.0 should double negative valence; ratio={ratio:.6f}"
    )


def test_threat_partial_amplification():
    """Agent with perceived_threat=0.5 has 1.5× factor."""
    rule = AffectiveUpdate(
        radius=1.5, learning_rate=0.01, identity_weight=0.5,
        baseline=0.10, cooperative_mute=0.5, threat_amplification=1.0,
    )
    a_low, _, space, env = _two_agents_for_threat(threat_a=0.0)
    d_low = rule.apply(a_low, space, env, np.random.default_rng(0))
    a_half, _, space, env = _two_agents_for_threat(threat_a=0.5)
    d_half = rule.apply(a_half, space, env, np.random.default_rng(0))
    ratio = d_half.d_attrs["affect"][1] / d_low.d_attrs["affect"][1]
    assert abs(ratio - 1.5) < 1e-9, f"ratio={ratio:.6f}, expected 1.5"


def test_threat_does_not_amplify_positive_valence():
    """In the cooperative-positive valence path (cooperative edge,
    warmth above threshold), the valence is `+coop_positive_magnitude`
    regardless of perceived_threat. Threat is identity-defensive (Mutz
    2018) — it does not amplify pro-social warmth."""
    rule = AffectiveUpdate(
        radius=1.5, learning_rate=0.01, identity_weight=0.5,
        baseline=0.10, cooperative_mute=0.5,
        coop_positive_threshold=-0.2, coop_positive_magnitude=0.05,
        threat_amplification=1.0,
    )
    # Warm-ish agent (above coop threshold), cooperative edge,
    # high threat. Positive valence should NOT be amplified.
    a = Agent(
        id=0,
        state=AgentState(
            ideology=np.array([-0.3, 0.0]),
            attrs={
                "party": 0,
                "affect": {1: -0.1},  # above coop_positive_threshold -0.2
                "stubbornness": 0.0,
                "perceived_threat": 1.0,  # high threat
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
    # Cooperative edge between a and b.
    net = Network({0: set(), 1: set()})
    net.add_edge(0, 1, cooperative=True)
    env = Environment(attrs={"network": net})
    delta = rule.apply(a, space, env, np.random.default_rng(0))
    # Positive valence: lr * +coop_positive_magnitude = 0.01 * 0.05 = 0.0005.
    # Threat does NOT amplify this.
    assert abs(delta.d_attrs["affect"][1] - 0.0005) < 1e-9, (
        f"Positive valence should not be amplified by threat. "
        f"Got {delta.d_attrs['affect'][1]:+.6f}, expected +0.0005"
    )


def test_pillar_fallback_no_threat_attr():
    """Agent without perceived_threat reads 0.0; threat_factor = 1.0;
    valence equals Phase 8c §4 unchanged."""
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
                # no perceived_threat
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
    # Expected: lr * -(disagreement + baseline) * 1.0 (no mute) * 1.0 (no threat)
    expected = 0.01 * -(0.8/1.5 + 0.10)
    assert abs(delta.d_attrs["affect"][1] - expected) < 1e-9


# ---------------------------------------------------------------------
# BacklashRepulsion threat amplification.
# ---------------------------------------------------------------------


def test_threat_amplifies_backlash_push():
    """BacklashRepulsion push is multiplied by threat_factor."""
    rule = BacklashRepulsion(
        epsilon=0.3, max_range=1.5, strength=0.05,
        affect_threshold=-0.3, threat_amplification=1.0,
    )
    a_low = Agent(
        id=0,
        state=AgentState(
            ideology=np.array([0.0, 0.0]),
            attrs={
                "party": 0,
                "affect": {1: -0.5},  # below threshold; fires backlash
                "stubbornness": 0.0,
                "perceived_threat": 0.0,
            },
        ),
    )
    a_high = Agent(
        id=2,
        state=AgentState(
            ideology=np.array([0.0, 0.0]),
            attrs={
                "party": 0,
                "affect": {1: -0.5},
                "stubbornness": 0.0,
                "perceived_threat": 1.0,
            },
        ),
    )
    b = Agent(
        id=1,
        state=AgentState(
            ideology=np.array([0.6, 0.0]),
            attrs={"party": 1, "affect": {0: 0.0}, "stubbornness": 0.0},
        ),
    )
    space = ContinuousSpace2D()
    # Low-threat agent vs neighbor.
    space.rebuild([a_low, b])
    env = Environment(attrs={"network": Network({0: {1}, 1: {0}})})
    d_low = rule.apply(a_low, space, env, np.random.default_rng(0))
    # High-threat agent vs neighbor.
    space.rebuild([a_high, b])
    env = Environment(attrs={"network": Network({2: {1}, 1: {2}})})
    d_high = rule.apply(a_high, space, env, np.random.default_rng(0))
    # Push magnitude should double under threat=1.0.
    ratio = d_high.d_ideology[0] / d_low.d_ideology[0]
    assert abs(ratio - 2.0) < 1e-9, (
        f"threat=1.0 should double backlash push; ratio={ratio:.6f}"
    )


def test_backlash_pillar_fallback_no_threat():
    """Agent without perceived_threat → push unchanged from §4."""
    rule = BacklashRepulsion(
        epsilon=0.3, max_range=1.5, strength=0.05,
        affect_threshold=-0.3, threat_amplification=1.0,
    )
    a = Agent(
        id=0,
        state=AgentState(
            ideology=np.array([0.0, 0.0]),
            attrs={"party": 0, "affect": {1: -0.5}, "stubbornness": 0.0},
        ),
    )
    b = Agent(
        id=1,
        state=AgentState(
            ideology=np.array([0.6, 0.0]),
            attrs={"party": 1, "affect": {0: 0.0}, "stubbornness": 0.0},
        ),
    )
    space = ContinuousSpace2D()
    space.rebuild([a, b])
    env = Environment(attrs={"network": Network({0: {1}, 1: {0}})})
    delta = rule.apply(a, space, env, np.random.default_rng(0))
    # No threat attr → factor 1.0 → Phase 8c §4 push.
    # Expected: -0.5 push at d=0.6 → magnitude (-(-0.5)/(0.6*0.6)) * 0.05
    # = (0.5/0.36) * 0.05 = ~0.0694 per d. Direction toward -x.
    assert delta.d_ideology[0] < 0.0  # away from neighbor (which is +x)
    assert delta.d_ideology[1] == 0.0


# ---------------------------------------------------------------------
# Historical 2016 event.
# ---------------------------------------------------------------------


def test_2016_status_threat_event_fires_at_tick_108():
    """Historical arc fires `_event_2016_status_threat` at tick 108.
    60% of party=1 agents get `perceived_threat = 0.5`; party=0
    agents are unaffected."""
    eng = historical_build(seed=0, n_agents=200)
    sched = build_schedule()
    # Run up to tick 107 — before event.
    run_to(eng, sched, 107)
    pre_threatened = sum(
        1 for a in eng.agents
        if a.state.attrs.get("perceived_threat", 0.0) > 0
    )
    assert pre_threatened == 0, (
        f"No agent should be threatened before the 2016 event; "
        f"got {pre_threatened}"
    )
    # Run to tick 108 — event fires.
    run_to(eng, sched, 108)
    r_agents = [a for a in eng.agents if a.state.attrs.get("party") == 1]
    d_agents = [a for a in eng.agents if a.state.attrs.get("party") == 0]
    r_threatened = sum(
        1 for a in r_agents if a.state.attrs.get("perceived_threat", 0.0) > 0
    )
    d_threatened = sum(
        1 for a in d_agents if a.state.attrs.get("perceived_threat", 0.0) > 0
    )
    expected_r_threatened = int(THREAT_2016_R_FRACTION * len(r_agents))
    assert r_threatened == expected_r_threatened, (
        f"Expected {expected_r_threatened}/{len(r_agents)} party=1 "
        f"agents threatened (60%); got {r_threatened}"
    )
    assert d_threatened == 0, (
        f"No party=0 agent should be threatened by Mutz-2018 event; "
        f"got {d_threatened}"
    )
    # Magnitude check.
    threatened_levels = [
        a.state.attrs["perceived_threat"]
        for a in r_agents if a.state.attrs.get("perceived_threat", 0.0) > 0
    ]
    if threatened_levels:
        assert all(t == THREAT_2016_MAGNITUDE for t in threatened_levels), (
            f"All threatened agents should have threat = "
            f"{THREAT_2016_MAGNITUDE}; got {set(threatened_levels)}"
        )


def test_2016_threat_decays_through_2025():
    """ThreatDecay at decay_rate=0.05 reduces the 2016 spike to noise
    floor by 2025 (tick 135 = 27 ticks post-event ≈ ~half-life × 2)."""
    eng = historical_build(seed=0, n_agents=200)
    sched = build_schedule()
    run_to(eng, sched, 135)
    threats = [
        a.state.attrs.get("perceived_threat", 0.0) for a in eng.agents
    ]
    mean_threat = float(np.mean(threats))
    max_threat = float(np.max(threats))
    # 0.5 * (0.95)^27 ≈ 0.5 * 0.249 ≈ 0.124. Mean across population
    # (only ~30% of agents had nonzero starting threat) ≈ 0.04 or so.
    assert mean_threat < 0.15, (
        f"Mean threat at 2025 should be near noise floor; "
        f"got {mean_threat:.4f}"
    )
    assert max_threat < 0.20, (
        f"Max threat at 2025 should be small; got {max_threat:.4f}"
    )


# ---------------------------------------------------------------------
# Pillar invariant: bit-identical.
# ---------------------------------------------------------------------


def test_pillar_agents_lack_perceived_threat():
    """Pillar S0-S4 baseline never sets perceived_threat on any agent.
    Bit-identical to Phase 8c §4."""
    eng = pillar_build(seed=0, n_agents=50)
    apply_intervention(eng, PILLAR.interventions[4])
    eng.run(200)
    for a in eng.agents:
        assert "perceived_threat" not in a.state.attrs, (
            f"pillar agent {a.id} carries perceived_threat — "
            f"pillar invariant broken"
        )
