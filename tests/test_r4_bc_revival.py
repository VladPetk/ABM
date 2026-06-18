"""R-phase R4 isolation test — BC revival via the affect_weight floor (gated).

The floor turns BC's two-sided affect modulator on: a WARM out-party neighbour is
up-weighted (cross-party convergence), a COLD one is down-weighted (echo chamber).
So under restoring (R1/R3 warming) it becomes a depolarizing position-convergence
force. Default 0.0 → byte-identical. See docs/internal/reversibility_spec.md (R4).
"""
from __future__ import annotations

import numpy as np

from abm.core.agent import Agent
from abm.core.environment import Environment
from abm.core.network import Network
from abm.core.space import ContinuousSpace2D
from abm.core.state import AgentState
from abm.pillars.historical_arc import build_engine
from abm.rules.influence import BoundedConfidenceInfluence
from scripts.anes_preset import ANES_FULL_KWARGS


def _move_x(warmth, floor):
    """x-component of agent a's BC move, with one in-party neighbour at a's
    position and one out-party neighbour offset in +x."""
    a = Agent(id=0, state=AgentState(
        ideology=np.array([0.0, 0.0], dtype=float),
        attrs={"party": 0, "affect": {1: float(warmth)}, "stubbornness": 0.0}))
    b = Agent(id=1, state=AgentState(   # in-party, co-located
        ideology=np.array([0.0, 0.0], dtype=float),
        attrs={"party": 0, "affect": {}, "stubbornness": 0.0}))
    c = Agent(id=2, state=AgentState(   # out-party, offset in +x
        ideology=np.array([0.4, 0.0], dtype=float),
        attrs={"party": 1, "affect": {}, "stubbornness": 0.0}))
    space = ContinuousSpace2D()
    space.rebuild([a, b, c])
    env = Environment(attrs={"network": Network({0: {1, 2}, 1: {0}, 2: {0}})})
    rule = BoundedConfidenceInfluence(
        epsilon=0.40, strength=0.1, temperature=0.05, affect_weight_floor=floor)
    d = rule.apply(a, space, env, np.random.default_rng(0)).d_ideology
    return float(d[0])


def test_floor_off_is_baseline():
    """floor 0.0 → affect modulator off → warmth has no effect (bit-identical)."""
    assert abs(_move_x(+0.5, 0.0) - _move_x(-0.5, 0.0)) < 1e-12


def test_warm_outparty_upweighted():
    """floor on + WARM out-party → moves MORE toward the out-party than floor-off
    (cross-party convergence = depolarizing)."""
    base = _move_x(+0.5, 0.0)
    warm = _move_x(+0.5, 0.6)
    assert warm > base > 0.0


def test_cold_outparty_downweighted():
    """floor on + COLD out-party → moves LESS toward the out-party (echo chamber)."""
    base = _move_x(-0.5, 0.0)
    cold = _move_x(-0.5, 0.6)
    assert 0.0 < cold < base


def _bc(eng):
    rs = [r for r in eng.rules.rules
          if type(r).__name__ == "BoundedConfidenceInfluence"]
    assert rs, "BC not in pipeline"
    return rs[0]


def test_build_off_floor_zero():
    eng = build_engine(seed=0, **ANES_FULL_KWARGS)
    assert _bc(eng).affect_weight_floor == 0.0


def test_build_on_passes_floor():
    k = dict(ANES_FULL_KWARGS)
    k.update(bc_affect_weight_floor=0.08)
    eng = build_engine(seed=0, **k)
    assert _bc(eng).affect_weight_floor == 0.08
