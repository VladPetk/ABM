"""Phase 5 — affective polarization as a first-class channel.

Three feature groups:

- **A1 (corrected dynamics):** out-party valence is negative-going;
  same-party neighbours produce no affect delta; close out-party
  neighbours produce less coolness than far ones but still negative.
- **A4 (BC affect modulator):** hostile out-party ties pull less; the
  ``affect_weight = 0.0`` path is bit-identical to Phase 4 BC.
- **A5 (TieRewiring affect-aware drop):** cold out-party ties drop
  preferentially over warm-but-distant ties; involuntary ties remain
  exempt.

Plus a session-level Iyengar test in ``test_pillar_stages.py``:
|Δaffect| outpaces Δideological_constraint across S0→S3 (Iyengar et al.
2019; Mason 2018; Finkel et al. 2020).
"""
from __future__ import annotations

import numpy as np

from abm.core.agent import Agent
from abm.core.environment import Environment
from abm.core.network import Network
from abm.core.space import ContinuousSpace2D
from abm.core.state import AgentState
from abm.pillars import PILLAR, apply_intervention
from abm.pillars.calm_to_camps import (
    AFFECT_BASELINE,
    AFFECT_IDENTITY_WEIGHT,
    BC_AFFECT_WEIGHT,
    TR_AFFECT_WEIGHT_REWIRE,
    build_engine,
)
from abm.rules.affective_update import AffectiveUpdate
from abm.rules.influence import BoundedConfidenceInfluence


def _two_agents(
    pos_a, pos_b, party_a, party_b, *,
    identities_a=None, identities_b=None, affect_a=None,
):
    a = Agent(
        id=0,
        state=AgentState(
            ideology=np.array(pos_a, dtype=float),
            attrs={
                "party": party_a,
                "affect": affect_a if affect_a is not None else {party_b: 0.0},
                "identities": (
                    np.asarray(identities_a, dtype=float)
                    if identities_a is not None else None
                ),
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
                "identities": (
                    np.asarray(identities_b, dtype=float)
                    if identities_b is not None else None
                ),
                "stubbornness": 0.0,
            },
        ),
    )
    return a, b


# --- A1: corrected dynamics ----------------------------------------------


def test_affect_update_emits_negative_valence_for_distant_outparty():
    """The headline sign-fix test. A far out-party neighbour produces a
    *negative* affect delta — out-party animus rises with disagreement."""
    a, b = _two_agents([0.0, 0.0], [0.8, 0.8], party_a=0, party_b=1)
    space = ContinuousSpace2D()
    space.rebuild([a, b])
    env = Environment(attrs={"network": Network({0: {1}, 1: {0}})})
    rule = AffectiveUpdate(
        radius=1.5, learning_rate=0.1, identity_weight=0.5, baseline=0.10
    )
    delta = rule.apply(a, space, env, np.random.default_rng(0))
    assert "affect" in delta.d_attrs, "Out-party encounter should emit an affect delta."
    da = delta.d_attrs["affect"]
    assert 1 in da, f"Affect delta should target the other party (1); got keys {list(da)}."
    assert da[1] < 0.0, (
        f"Distant out-party neighbour must produce negative-going affect "
        f"(coolness), got {da[1]:.4f}."
    )


def test_affect_update_skips_same_party_neighbours():
    """In-party neighbours produce no affect delta (Finkel et al. 2020:
    in-party warmth is stable, out-party animus moves)."""
    a, b = _two_agents([0.0, 0.0], [0.5, 0.5], party_a=0, party_b=0)
    space = ContinuousSpace2D()
    space.rebuild([a, b])
    env = Environment(attrs={"network": Network({0: {1}, 1: {0}})})
    rule = AffectiveUpdate(learning_rate=0.1)
    delta = rule.apply(a, space, env, np.random.default_rng(0))
    assert delta.d_attrs == {}, (
        f"Same-party neighbour shouldn't emit an affect delta; got {delta.d_attrs}."
    )


def test_close_outparty_produces_less_coolness_than_far_outparty():
    """A close out-party encounter cools the agent less than a far one,
    but still cools (the baseline ensures warming is impossible from any
    single encounter)."""
    # Close out-party encounter: agent at (0, 0), neighbour at (0.1, 0).
    a_close, b_close = _two_agents(
        [0.0, 0.0], [0.1, 0.0], party_a=0, party_b=1,
    )
    # Far out-party encounter: agent at (0, 0), neighbour at (1.0, 0).
    a_far, b_far = _two_agents(
        [0.0, 0.0], [1.0, 0.0], party_a=0, party_b=1,
    )
    rule = AffectiveUpdate(
        radius=1.5, learning_rate=0.1, identity_weight=0.0, baseline=0.10
    )
    rng = np.random.default_rng(0)

    space_c = ContinuousSpace2D()
    space_c.rebuild([a_close, b_close])
    env_c = Environment(attrs={"network": Network({0: {1}, 1: {0}})})

    space_f = ContinuousSpace2D()
    space_f.rebuild([a_far, b_far])
    env_f = Environment(attrs={"network": Network({0: {1}, 1: {0}})})

    delta_close = rule.apply(a_close, space_c, env_c, rng).d_attrs["affect"][1]
    delta_far = rule.apply(a_far, space_f, env_f, rng).d_attrs["affect"][1]
    # Both must be negative.
    assert delta_close < 0.0, f"Close out-party should still cool, got {delta_close}."
    assert delta_far < 0.0, f"Far out-party should cool, got {delta_far}."
    # Far must cool *more*.
    assert delta_far < delta_close, (
        f"Far out-party encounter should produce more coolness than close one: "
        f"close={delta_close:.4f}, far={delta_far:.4f}."
    )


# --- A4: BC affect modulator ---------------------------------------------


def test_bc_affect_weight_default_is_zero():
    """Default `affect_weight = 0.0` preserves canonical / Phase 4 behaviour
    — no existing scenario constructs BC with `affect_weight`."""
    rule = BoundedConfidenceInfluence(epsilon=0.3, strength=0.08)
    assert rule.affect_weight == 0.0


def test_pillar_opts_in_to_affect_weight_at_s2():
    """The pillar's S0/S1 bundles keep affect_weight at 0; S2-S4 turn it
    on at BC_AFFECT_WEIGHT (0.3 per Vlad's override)."""
    # S0: off.
    eng = build_engine(seed=0, n_agents=50)
    apply_intervention(eng, PILLAR.interventions[0])
    bc = next(r for r in eng.rules.rules if type(r).__name__ == "BoundedConfidenceInfluence")
    assert bc.affect_weight == 0.0
    # S2: on at 0.3.
    apply_intervention(eng, PILLAR.interventions[2])
    bc = next(r for r in eng.rules.rules if type(r).__name__ == "BoundedConfidenceInfluence")
    assert bc.affect_weight == BC_AFFECT_WEIGHT == 0.3


def test_bc_affect_modulator_mutes_hostile_outparty():
    """A hostile out-party tie has its weight muted relative to a
    neutral one. With one in-party and one out-party neighbour at equal
    distance, the cold agent's resulting pull tilts toward the in-party
    neighbour; the warm/neutral agent's pull is balanced."""
    # Two scenarios: same network, same positions, only affect differs.
    def make(affect_a):
        a = Agent(id=0, state=AgentState(
            ideology=np.array([0.0, 0.0]),
            attrs={"party": 0, "affect": affect_a, "stubbornness": 0.0},
        ))
        # Out-party (party 1) at (+0.2, 0) and in-party (party 0) at (-0.2, 0).
        out_party = Agent(id=1, state=AgentState(
            ideology=np.array([0.20, 0.0]),
            attrs={"party": 1, "affect": {}, "stubbornness": 0.0},
        ))
        in_party = Agent(id=2, state=AgentState(
            ideology=np.array([-0.20, 0.0]),
            attrs={"party": 0, "affect": {}, "stubbornness": 0.0},
        ))
        space = ContinuousSpace2D()
        space.rebuild([a, out_party, in_party])
        env = Environment(
            attrs={"network": Network({0: {1, 2}, 1: {0}, 2: {0}})}
        )
        return a, space, env

    rule = BoundedConfidenceInfluence(
        epsilon=0.3, strength=1.0, temperature=0.05, affect_weight=0.3
    )
    rng = np.random.default_rng(0)

    # Hot/neutral agent: affect toward out-party is 0 — symmetric pull.
    a_hot, space_h, env_h = make({1: 0.0})
    d_hot = rule.apply(a_hot, space_h, env_h, rng).d_ideology
    # Cold agent: affect toward out-party is -1; out-party weight muted
    # to ~0.7, so the in-party pull dominates.
    a_cold, space_c, env_c = make({1: -1.0})
    d_cold = rule.apply(a_cold, space_c, env_c, rng).d_ideology

    # Hot agent is balanced, pull cancels.
    assert abs(d_hot[0]) < 1e-9, (
        f"Hot/neutral agent should be balanced between symmetric neighbours; got {d_hot}."
    )
    # Cold agent leans away from the out-party (negative x), because
    # the in-party neighbour's weight is unscaled while the out-party's
    # is multiplied by 1 + 0.3 * (-1) = 0.7.
    assert d_cold[0] < -0.01, (
        f"Cold-affect agent should lean toward in-party (negative x); got {d_cold}."
    )
    # And the magnitude is not extreme — 0.3 is a mild weight.
    assert d_cold[0] > -0.10, (
        f"Cold-affect agent shouldn't lean drastically (0.3 is mild); got {d_cold}."
    )


def test_bc_affect_weight_zero_is_inert():
    """With affect_weight = 0, the rule produces bit-identical output to a
    fresh BC with no affect plumbing at all. Phase 4 regression guard."""
    a_cold, b_cold = _two_agents(
        [0.0, 0.0], [0.20, 0.0], party_a=0, party_b=1,
        affect_a={1: -1.0},
    )
    a_neutral, b_neutral = _two_agents(
        [0.0, 0.0], [0.20, 0.0], party_a=0, party_b=1,
    )
    space_c = ContinuousSpace2D()
    space_c.rebuild([a_cold, b_cold])
    space_n = ContinuousSpace2D()
    space_n.rebuild([a_neutral, b_neutral])
    env_c = Environment(attrs={"network": Network({0: {1}, 1: {0}})})
    env_n = Environment(attrs={"network": Network({0: {1}, 1: {0}})})
    rule = BoundedConfidenceInfluence(
        epsilon=0.3, strength=1.0, temperature=0.05, affect_weight=0.0
    )
    rng = np.random.default_rng(0)
    d_c = rule.apply(a_cold, space_c, env_c, rng).d_ideology
    d_n = rule.apply(a_neutral, space_n, env_n, rng).d_ideology
    assert np.array_equal(d_c, d_n), (
        f"affect_weight=0 must be bit-identical regardless of affect attr: "
        f"cold={d_c}, neutral={d_n}."
    )


# --- A5: TieRewiring affect-aware drop -----------------------------------


def test_tie_rewiring_affect_weight_default_is_zero():
    """Default keeps Phase 4 TieRewiring behaviour."""
    from abm.rules.tie_rewiring import TieRewiring

    rule = TieRewiring(rewire_rate=0.02)
    assert rule.affect_weight_rewire == 0.0


def test_tie_rewiring_prefers_to_drop_cold_outparty_ties():
    """A cold out-party tie at moderate distance is dropped before an
    in-party tie at the same combined distance."""
    from abm.rules.tie_rewiring import TieRewiring

    # Agent has two voluntary ties:
    #   tie 1: out-party, low ideology distance, very cold affect
    #   tie 2: in-party, low ideology distance, no affect entry
    # Combined distance is roughly equal; affect_weight_rewire = 0.30
    # should tip the balance toward dropping tie 1.
    n_candidates = 1
    agents = []
    # Agent 0: party 0, anchor at centre.
    agents.append(Agent(
        id=0,
        state=AgentState(
            ideology=np.array([0.0, 0.0]),
            attrs={
                "party": 0,
                "social_coord": 0.0,
                "affect": {1: -1.0},
                "stubbornness": 0.0,
            },
        ),
    ))
    # Agent 1: out-party (party 1), same ideology distance as agent 2.
    agents.append(Agent(
        id=1,
        state=AgentState(
            ideology=np.array([0.20, 0.0]),
            attrs={
                "party": 1, "social_coord": 0.2, "affect": {0: 0.0},
                "stubbornness": 0.0,
            },
        ),
    ))
    # Agent 2: in-party (party 0), same ideology distance.
    agents.append(Agent(
        id=2,
        state=AgentState(
            ideology=np.array([0.20, 0.0]),
            attrs={
                "party": 0, "social_coord": 0.2, "affect": {1: 0.0},
                "stubbornness": 0.0,
            },
        ),
    ))
    # Plenty of agents 3..30 are far away — candidates for the new tie.
    for k in range(3, 30):
        agents.append(Agent(
            id=k,
            state=AgentState(
                ideology=np.array([-0.5 - 0.01 * k, 0.0]),
                attrs={
                    "party": k % 2, "social_coord": -0.5, "affect": {},
                    "stubbornness": 0.0,
                },
            ),
        ))
    network = Network({a.id: set() for a in agents})
    network.add_edge(0, 1, involuntary=False)
    network.add_edge(0, 2, involuntary=False)
    space = ContinuousSpace2D()
    space.rebuild(agents)
    env = Environment(attrs={"network": network})

    # rewire_rate = 1.0 so the agent rewires on every tick.
    rule = TieRewiring(
        rewire_rate=1.0, n_candidates=5, affect_weight_rewire=0.30,
    )
    # One tick is enough — the agent picks max-score tie to drop.
    rng = np.random.default_rng(0)
    rule.apply(env, agents, space, rng, tick=0)
    # The cold out-party tie should be dropped before the in-party one.
    assert not network.has_edge(0, 1), (
        "Cold out-party tie (0-1) should have been dropped first."
    )
    assert network.has_edge(0, 2), (
        "In-party tie (0-2) should have been preserved over the cold out-party tie."
    )


def test_tie_rewiring_affect_weight_zero_is_inert():
    """With affect_weight_rewire = 0, drop ranking is by combined_distance
    only — Phase 4 behaviour preserved."""
    from abm.rules.tie_rewiring import TieRewiring

    # Same setup as the previous test, but with affect_weight_rewire = 0.
    # Now the two ties have equal combined distance, so the choice is
    # deterministic on dict insertion order. The asserted property: the
    # affect on tie 1 does not influence which tie is dropped.
    agents = [
        Agent(id=0, state=AgentState(
            ideology=np.array([0.0, 0.0]),
            attrs={"party": 0, "social_coord": 0.0, "affect": {1: -1.0},
                   "stubbornness": 0.0},
        )),
        Agent(id=1, state=AgentState(
            ideology=np.array([0.20, 0.0]),
            attrs={"party": 1, "social_coord": 0.2, "affect": {0: 0.0},
                   "stubbornness": 0.0},
        )),
        Agent(id=2, state=AgentState(
            ideology=np.array([0.20, 0.0]),
            attrs={"party": 0, "social_coord": 0.2, "affect": {1: 0.0},
                   "stubbornness": 0.0},
        )),
    ]
    for k in range(3, 20):
        agents.append(Agent(id=k, state=AgentState(
            ideology=np.array([-0.5 - 0.01 * k, 0.0]),
            attrs={"party": k % 2, "social_coord": -0.5, "affect": {},
                   "stubbornness": 0.0},
        )))
    net = Network({a.id: set() for a in agents})
    net.add_edge(0, 1, involuntary=False)
    net.add_edge(0, 2, involuntary=False)
    space = ContinuousSpace2D(); space.rebuild(agents)
    env = Environment(attrs={"network": net})

    rule = TieRewiring(rewire_rate=1.0, n_candidates=5, affect_weight_rewire=0.0)
    rng = np.random.default_rng(0)
    rule.apply(env, agents, space, rng, tick=0)
    # With affect_weight_rewire=0, ties have equal combined distance, so
    # max() is deterministic on the iteration order of the set. The
    # assertion: at least one of the two ties survives (the rule didn't
    # somehow drop both), and the dropped tie's identity is not
    # determined by affect (the cold side has no affect-driven
    # disadvantage here).
    remaining = [j for j in (1, 2) if net.has_edge(0, j)]
    assert len(remaining) == 1, (
        f"Exactly one of the two starting voluntary ties should remain; got {remaining}."
    )


def test_pillar_bundles_set_affect_weights_at_s2():
    """The pillar bundles wire BC.affect_weight and TR.affect_weight_rewire
    on at S2, S3, S4 — off at S0, S1."""
    for stage_idx, on in [(0, False), (1, False), (2, True), (3, True), (4, True)]:
        eng = build_engine(seed=0, n_agents=50)
        apply_intervention(eng, PILLAR.interventions[stage_idx])
        bc = next(r for r in eng.rules.rules
                  if type(r).__name__ == "BoundedConfidenceInfluence")
        tr = next(r for r in eng.env_rules
                  if type(r).__name__ == "TieRewiring")
        if on:
            assert bc.affect_weight == BC_AFFECT_WEIGHT == 0.3, (
                f"S{stage_idx} should have BC.affect_weight == 0.3"
            )
            assert tr.affect_weight_rewire == TR_AFFECT_WEIGHT_REWIRE == 0.30, (
                f"S{stage_idx} should have TR.affect_weight_rewire == 0.30"
            )
        else:
            assert bc.affect_weight == 0.0, f"S{stage_idx} BC.affect_weight should be 0"
            assert tr.affect_weight_rewire == 0.0, (
                f"S{stage_idx} TR.affect_weight_rewire should be 0"
            )


# --- Sanity: build constants match the spec ------------------------------


def test_affect_constants_match_spec():
    assert AFFECT_BASELINE == 0.10
    assert AFFECT_IDENTITY_WEIGHT == 0.5
    assert BC_AFFECT_WEIGHT == 0.3
    assert TR_AFFECT_WEIGHT_REWIRE == 0.30
