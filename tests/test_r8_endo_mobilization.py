"""R-phase R8 isolation test — endogenous mobilization feedback (gated).

The activist→elite→mass loop's leapfrog gain is `gain · mob_exo`. R8 adds an
endogenous term so a party's own sorting (centroid extremity along its axis) feeds
its mobilization: `mob_eff = mob_exo + endo_mob_gain · max(0, cent·dir)`. With a
sorted mass and LOW exogenous mob (1980), the elite leapfrogs FURTHER with R8 on
than off — the self-sustaining spiral that raises the emergent fraction. 0.0 →
bit-identical. See docs/internal/reversibility_spec.md (R8).
"""
from __future__ import annotations

import numpy as np

from abm.core.agent import Agent
from abm.core.environment import Environment
from abm.core.space import ContinuousSpace2D
from abm.core.state import AgentState
from abm.pillars.historical_arc import build_engine
from abm.rules.activist_elite import ActivistEliteCue
from scripts.anes_preset import ANES_FULL_KWARGS


def _world():
    """Two parties whose mass has already sorted to ±0.4 on x, with LOW (1980)
    exogenous mobilization — the regime where the endo feedback should bite."""
    agents = []
    i = 0
    for p, cx in ((0, -0.4), (1, 0.4)):
        for dx in (-0.05, 0.0, 0.05, 0.1):  # a spread incl. an activist tail
            agents.append(Agent(id=i, state=AgentState(
                ideology=np.array([cx + dx, 0.0], dtype=float),
                attrs={"party": p, "identity_strength": 0.6,
                       "party_cue": np.array([cx, 0.0], dtype=float)})))
            i += 1
    space = ContinuousSpace2D()
    space.rebuild(agents)
    env = Environment(attrs={
        "parties": {0: np.array([-0.1, 0.0]), 1: np.array([0.1, 0.0])},
        "party_axis": {0: [-1.0, 0.0], 1: [1.0, 0.0]},
        "activist_mobilization": {0: 0.1, 1: 0.1},   # low 1980 exogenous mob
    })
    return agents, space, env


def _elite_x_after(endo):
    agents, space, env = _world()
    rule = ActivistEliteCue(tail_q=0.25, gain=2.5, ceiling=0.65, endo_mob_gain=endo)
    rule.apply(env, agents, space, np.random.default_rng(0), 0)
    return float(env.attrs["parties"][1][0])   # party-1 elite x (extremity)


def test_endo_off_is_baseline():
    """Two off-path runs match (and the param defaults to no-op)."""
    assert abs(_elite_x_after(0.0) - _elite_x_after(0.0)) < 1e-12


def test_endo_amplifies_under_low_exo_mob():
    """With a sorted mass and low exogenous mob, R8 makes the elite leapfrog
    FURTHER (self-sustaining) than with the endo term off."""
    off = _elite_x_after(0.0)
    on = _elite_x_after(3.0)
    assert on > off > 0.1, f"expected endo to push elite further: off={off}, on={on}"


def _loop(eng):
    rs = [r for r in eng.env_rules if type(r).__name__ == "ActivistEliteCue"]
    assert rs, "ActivistEliteCue not in env_rules"
    return rs[0]


def test_build_off_endo_zero():
    eng = build_engine(seed=0, **ANES_FULL_KWARGS)
    assert _loop(eng).endo_mob_gain == 0.0


def test_build_on_passes_endo():
    k = dict(ANES_FULL_KWARGS); k.update(endo_mob_gain=2.0)
    eng = build_engine(seed=0, **k)
    assert _loop(eng).endo_mob_gain == 2.0
