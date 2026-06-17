"""R-phase R2 isolation test — cross-pressure damping (gated).

Cross-pressured agents (low `identity_alignment` = cross-cutting identities not
stacked with party) resist out-party cooling (AffectiveUpdate) and sorting
(ConstraintOp). Default damp 0.0 → strict no-op → bit-identical.
See docs/internal/reversibility_spec.md (R2).
"""
from __future__ import annotations

import numpy as np

from abm.core.agent import Agent
from abm.core.environment import Environment
from abm.core.network import Network
from abm.core.space import ContinuousSpace2D
from abm.core.state import AgentState
from abm.pillars.historical_arc import build_engine
from abm.rules.affective_update import AffectiveUpdate
from scripts.anes_preset import ANES_FULL_KWARGS


def _setup(align_a, party_a=0, party_b=1, warmth_a=-0.3):
    a = Agent(id=0, state=AgentState(
        ideology=np.array([0.0, 0.0], dtype=float),
        attrs={"party": party_a, "affect": {party_b: float(warmth_a)},
               "identity_alignment": float(align_a), "stubbornness": 0.0}))
    b = Agent(id=1, state=AgentState(
        ideology=np.array([0.6, 0.0], dtype=float),
        attrs={"party": party_b, "affect": {party_a: 0.0}, "stubbornness": 0.0}))
    space = ContinuousSpace2D()
    space.rebuild([a, b])
    env = Environment(attrs={"network": Network({0: {1}, 1: {0}})})
    return a, space, env


def _neg_delta(align_a, damp):
    a, space, env = _setup(align_a)
    rule = AffectiveUpdate(radius=1.5, learning_rate=0.01, identity_weight=0.5,
                           baseline=0.10, xpressure_affect_damp=damp)
    return rule.apply(a, space, env, np.random.default_rng(0)).d_attrs["affect"][1]


def test_cross_pressured_agent_cools_less():
    """With damping on, a cross-pressured agent (identity_alignment=0 → xp=1)
    cools LESS than a fully-stacked agent (alignment=1 → xp=0)."""
    d_cross = _neg_delta(align_a=0.0, damp=0.6)
    d_stack = _neg_delta(align_a=1.0, damp=0.6)
    assert d_cross < 0.0 and d_stack < 0.0
    assert abs(d_cross) < abs(d_stack), (
        f"cross-pressured agent should cool less: |{d_cross}| vs |{d_stack}|"
    )
    # xp_mute for align=0,damp=0.6 is 0.4 → exactly 0.4x the undamped magnitude.
    assert abs(d_cross - 0.4 * d_stack) < 1e-12


def test_damp_off_is_alignment_independent():
    """damp 0.0 → identity_alignment has no effect on cooling (bit-identical)."""
    assert abs(_neg_delta(0.0, 0.0) - _neg_delta(1.0, 0.0)) < 1e-12


def _rule(eng, name):
    rs = [r for r in eng.rules.rules if type(r).__name__ == name]
    assert rs, f"{name} not in pipeline"
    return rs[0]


def test_build_off_damps_zero():
    eng = build_engine(seed=0, **ANES_FULL_KWARGS)
    assert _rule(eng, "ConstraintOp").xpressure_damp == 0.0
    assert _rule(eng, "AffectiveUpdate").xpressure_affect_damp == 0.0


def test_build_on_passes_damps():
    k = dict(ANES_FULL_KWARGS)
    k.update(xpressure_sorting_damp=0.5, xpressure_affect_damp=0.4)
    eng = build_engine(seed=0, **k)
    assert _rule(eng, "ConstraintOp").xpressure_damp == 0.5
    assert _rule(eng, "AffectiveUpdate").xpressure_affect_damp == 0.4
