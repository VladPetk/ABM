"""R-phase R6 isolation test — two-signed thermostatic feedback (gated).

When party-centroid separation overshoots `reference`, both party clouds drift
toward their midpoint (sep ↓); below it they drift apart (sep ↑). Rigid per-party
translation → within-party spread preserved. gain 0.0 → no-op → bit-identical.
See docs/internal/reversibility_spec.md (R6).
"""
from __future__ import annotations

import numpy as np

from abm.core.agent import Agent
from abm.core.environment import Environment
from abm.core.space import ContinuousSpace2D
from abm.core.state import AgentState
from abm.pillars.historical_arc import build_engine
from abm.rules.thermostatic_feedback import ThermostaticFeedback
from scripts.anes_preset import ANES_FULL_KWARGS


def _world(sep):
    """Two party clouds centred at ±sep/2 on the economic axis, each with spread."""
    half = sep / 2.0
    agents = []
    i = 0
    for p, c in ((0, +half), (1, -half)):
        for dx in (-0.1, 0.0, 0.1):
            agents.append(Agent(id=i, state=AgentState(
                ideology=np.array([c + dx, 0.0], dtype=float),
                attrs={"party": p})))
            i += 1
    space = ContinuousSpace2D()
    space.rebuild(agents)
    env = Environment(attrs={})
    return agents, space, env


def _sep(agents):
    c0 = np.mean([a.state.ideology for a in agents
                  if a.state.attrs["party"] == 0], axis=0)
    c1 = np.mean([a.state.ideology for a in agents
                  if a.state.attrs["party"] == 1], axis=0)
    return float(np.linalg.norm(c0 - c1))


def _spread(agents, party):
    xs = [a.state.ideology[0] for a in agents if a.state.attrs["party"] == party]
    return float(np.std(xs))


def test_gain_off_is_noop():
    agents, space, env = _world(sep=1.0)
    before = [a.state.ideology.copy() for a in agents]
    ThermostaticFeedback(gain=0.0).apply(env, agents, space, None, 0)
    after = [a.state.ideology for a in agents]
    assert all(np.allclose(b, a) for b, a in zip(before, after))


def test_overshoot_contracts_separation():
    agents, space, env = _world(sep=1.0)
    s0, sp0 = _sep(agents), _spread(agents, 0)
    ThermostaticFeedback(gain=0.5, reference=0.6).apply(env, agents, space, None, 0)
    assert _sep(agents) < s0          # sep contracts toward reference
    assert abs(_spread(agents, 0) - sp0) < 1e-12   # within-party spread preserved


def test_undershoot_expands_separation():
    """Two-signed: below the reference the clouds drift APART toward it."""
    agents, space, env = _world(sep=0.3)
    s0 = _sep(agents)
    ThermostaticFeedback(gain=0.5, reference=0.6).apply(env, agents, space, None, 0)
    assert _sep(agents) > s0


def test_build_off_not_installed():
    eng = build_engine(seed=0, **ANES_FULL_KWARGS)
    assert not any(type(r).__name__ == "ThermostaticFeedback"
                   for r in eng.env_rules)


def test_build_on_installed():
    k = dict(ANES_FULL_KWARGS)
    k.update(thermostatic_gain=0.4)
    eng = build_engine(seed=0, **k)
    rs = [r for r in eng.env_rules if type(r).__name__ == "ThermostaticFeedback"]
    assert len(rs) == 1 and rs[0].gain == 0.4
