"""Phase 8c §6 — asymmetric BacklashRepulsion tests.

Covers:

- `asymmetric = None` (pillar default) preserves Phase 8c §5
  behaviour exactly (symmetric multiplier 1.0).
- `asymmetric = {0: 0.7, 1: 1.3}` scales push per-party (Bail 2018
  reading: R-users push harder away).
- X1 setup applies the asymmetric multiplier dict.
- Pillar S0-S4 bundles carry `asymmetric = None`; pillar
  invariant preserved.
"""
from __future__ import annotations

import numpy as np

from abm.core.agent import Agent
from abm.core.environment import Environment
from abm.core.network import Network
from abm.core.space import ContinuousSpace2D
from abm.core.state import AgentState
from abm.pillars import (
    PILLAR,
    X1_SHOW_OTHER_SIDE,
    apply_intervention,
)
from abm.pillars.calm_to_camps import build_engine as pillar_build
from abm.pillars.interventions_phase6 import X1_ASYMMETRIC_RATIO
from abm.rules.repulsion import BacklashRepulsion


def _two_agents_for_backlash(party_a, party_b, warmth_a=-0.5):
    a = Agent(
        id=0,
        state=AgentState(
            ideology=np.array([0.0, 0.0]),
            attrs={
                "party": party_a,
                "affect": {party_b: float(warmth_a)},
                "stubbornness": 0.0,
            },
        ),
    )
    b = Agent(
        id=1,
        state=AgentState(
            ideology=np.array([0.6, 0.0]),
            attrs={"party": party_b, "affect": {party_a: 0.0}, "stubbornness": 0.0},
        ),
    )
    space = ContinuousSpace2D()
    space.rebuild([a, b])
    env = Environment(attrs={"network": Network({0: {1}, 1: {0}})})
    return a, b, space, env


def test_asymmetric_none_preserves_pre_section_6_behaviour():
    """`asymmetric = None` (constructor default + pillar default)
    produces multiplier 1.0 — bit-identical to §5 push magnitude."""
    rule_none = BacklashRepulsion(
        epsilon=0.3, max_range=1.5, strength=0.05,
        affect_threshold=-0.3, asymmetric=None,
    )
    rule_default = BacklashRepulsion(
        epsilon=0.3, max_range=1.5, strength=0.05,
        affect_threshold=-0.3,
    )  # asymmetric kwarg omitted → default None
    a1, _, space, env = _two_agents_for_backlash(party_a=0, party_b=1)
    d1 = rule_none.apply(a1, space, env, np.random.default_rng(0))
    a2, _, space, env = _two_agents_for_backlash(party_a=0, party_b=1)
    d2 = rule_default.apply(a2, space, env, np.random.default_rng(0))
    assert np.allclose(d1.d_ideology, d2.d_ideology, atol=1e-12)


def test_asymmetric_dict_scales_party_0_down():
    """`{0: 0.7, 1: 1.3}`: party=0 agent's push is multiplied by 0.7
    relative to symmetric (1.0)."""
    rule_sym = BacklashRepulsion(
        epsilon=0.3, max_range=1.5, strength=0.05,
        affect_threshold=-0.3, asymmetric=None,
    )
    rule_asym = BacklashRepulsion(
        epsilon=0.3, max_range=1.5, strength=0.05,
        affect_threshold=-0.3, asymmetric={0: 0.7, 1: 1.3},
    )
    a1, _, space, env = _two_agents_for_backlash(party_a=0, party_b=1)
    d_sym = rule_sym.apply(a1, space, env, np.random.default_rng(0))
    a2, _, space, env = _two_agents_for_backlash(party_a=0, party_b=1)
    d_asym = rule_asym.apply(a2, space, env, np.random.default_rng(0))
    ratio = d_asym.d_ideology[0] / d_sym.d_ideology[0]
    assert abs(ratio - 0.7) < 1e-9, f"party=0 ratio should be 0.7; got {ratio:.6f}"


def test_asymmetric_dict_scales_party_1_up():
    """`{0: 0.7, 1: 1.3}`: party=1 agent's push is multiplied by 1.3
    relative to symmetric (1.0)."""
    rule_sym = BacklashRepulsion(
        epsilon=0.3, max_range=1.5, strength=0.05,
        affect_threshold=-0.3, asymmetric=None,
    )
    rule_asym = BacklashRepulsion(
        epsilon=0.3, max_range=1.5, strength=0.05,
        affect_threshold=-0.3, asymmetric={0: 0.7, 1: 1.3},
    )
    a1, _, space, env = _two_agents_for_backlash(party_a=1, party_b=0)
    d_sym = rule_sym.apply(a1, space, env, np.random.default_rng(0))
    a2, _, space, env = _two_agents_for_backlash(party_a=1, party_b=0)
    d_asym = rule_asym.apply(a2, space, env, np.random.default_rng(0))
    ratio = d_asym.d_ideology[0] / d_sym.d_ideology[0]
    assert abs(ratio - 1.3) < 1e-9, f"party=1 ratio should be 1.3; got {ratio:.6f}"


def test_asymmetric_missing_party_defaults_to_1():
    """If asymmetric dict doesn't contain an agent's party id, the
    multiplier defaults to 1.0 (symmetric)."""
    rule_partial = BacklashRepulsion(
        epsilon=0.3, max_range=1.5, strength=0.05,
        affect_threshold=-0.3, asymmetric={1: 1.5},  # party 0 not in dict
    )
    rule_sym = BacklashRepulsion(
        epsilon=0.3, max_range=1.5, strength=0.05,
        affect_threshold=-0.3, asymmetric=None,
    )
    a1, _, space, env = _two_agents_for_backlash(party_a=0, party_b=1)
    d_partial = rule_partial.apply(a1, space, env, np.random.default_rng(0))
    a2, _, space, env = _two_agents_for_backlash(party_a=0, party_b=1)
    d_sym = rule_sym.apply(a2, space, env, np.random.default_rng(0))
    assert np.allclose(d_partial.d_ideology, d_sym.d_ideology, atol=1e-12)


# ---------------------------------------------------------------------
# X1 intervention under asymmetric mechanism.
# ---------------------------------------------------------------------


def test_x1_setup_applies_asymmetric_dict():
    """X1's param_bundle includes the asymmetric dict; after X1 fires,
    BacklashRepulsion has the dict set."""
    eng = pillar_build(seed=0, n_agents=50)
    apply_intervention(eng, PILLAR.interventions[4])
    # Pre-X1: asymmetric is None.
    br = next(
        r for r in eng.rules.rules if type(r).__name__ == "BacklashRepulsion"
    )
    assert br.asymmetric is None, f"pre-X1: asymmetric should be None; got {br.asymmetric}"
    # Apply X1.
    apply_intervention(eng, X1_SHOW_OTHER_SIDE)
    assert br.asymmetric == X1_ASYMMETRIC_RATIO, (
        f"post-X1: asymmetric should be {X1_ASYMMETRIC_RATIO}; got {br.asymmetric}"
    )


def test_x1_produces_asymmetric_per_party_drift():
    """Under X1 (asymmetric ratio 0.7:1.3), party 1's mean drift is
    larger in magnitude than party 0's mean drift."""
    eng = pillar_build(seed=0, n_agents=250)
    apply_intervention(eng, PILLAR.interventions[4])
    eng.run(200)
    pos_pre = eng.positions()
    parties = np.array([a.state.attrs["party"] for a in eng.agents])
    pre_d_x = float(pos_pre[parties == 0, 0].mean())
    pre_r_x = float(pos_pre[parties == 1, 0].mean())
    apply_intervention(eng, X1_SHOW_OTHER_SIDE)
    eng.run(200)
    pos_post = eng.positions()
    post_d_x = float(pos_post[parties == 0, 0].mean())
    post_r_x = float(pos_post[parties == 1, 0].mean())
    d_drift = abs(post_d_x - pre_d_x)
    r_drift = abs(post_r_x - pre_r_x)
    assert r_drift > d_drift, (
        f"R drift {r_drift:.4f} should exceed D drift {d_drift:.4f} "
        f"under asymmetric X1"
    )


# ---------------------------------------------------------------------
# Pillar invariant: bit-identical (pillar carries asymmetric=None).
# ---------------------------------------------------------------------


def test_pillar_S4_carries_asymmetric_none():
    """Pillar S4 bundle sets asymmetric=None — bit-identical to
    pre-§6 BacklashRepulsion behaviour."""
    eng = pillar_build(seed=0, n_agents=50)
    apply_intervention(eng, PILLAR.interventions[4])
    br = next(
        r for r in eng.rules.rules if type(r).__name__ == "BacklashRepulsion"
    )
    assert br.asymmetric is None, (
        f"Pillar S4: asymmetric should be None; got {br.asymmetric}"
    )
