"""R-phase R7 isolation test — affect rest state / mean-reversion (gated).

Out-party warmth relaxes toward `affect_rest_anchor` at `affect_rest_rate`/tick:
a COLD agent is pulled up toward the anchor, a WARM agent pulled down — so affect
gains an equilibrium instead of spiraling to the floor. rate 0.0 → no term →
bit-identical. See docs/internal/reversibility_spec.md (R7).
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
# Pre-R-phase canonical (mechanisms OFF) — the baseline for "default/off" checks,
# since ANES_FULL_KWARGS is now the R-phase config (these mechanisms ON).
from scripts.anes_preset import ANES_FULL_COMMONMODE_ECON_KWARGS as OFF_KW


def _delta(warmth, rate, anchor=0.0):
    a = Agent(id=0, state=AgentState(
        ideology=np.array([0.0, 0.0], dtype=float),
        attrs={"party": 0, "affect": {1: float(warmth)}, "stubbornness": 0.0}))
    b = Agent(id=1, state=AgentState(
        ideology=np.array([0.6, 0.0], dtype=float),
        attrs={"party": 1, "affect": {}}))
    space = ContinuousSpace2D()
    space.rebuild([a, b])
    env = Environment(attrs={"network": Network({0: {1}, 1: {0}})})
    rule = AffectiveUpdate(radius=1.5, learning_rate=0.01, identity_weight=0.0,
                           baseline=0.0, affect_rest_rate=rate,
                           affect_rest_anchor=anchor)
    return rule.apply(a, space, env, np.random.default_rng(0)).d_attrs["affect"][1]


def test_rate_off_is_warmth_independent():
    """rate 0.0 → only the (warmth-independent) cooling step → bit-identical."""
    assert abs(_delta(-0.8, 0.0) - _delta(+0.5, 0.0)) < 1e-12


def test_cold_agent_pulled_up():
    """A cold agent (below the anchor) gets a POSITIVE rest contribution."""
    assert _delta(-0.8, 0.1) > _delta(-0.8, 0.0)


def test_warm_agent_pulled_down():
    """A warm agent (above the anchor) gets a NEGATIVE rest contribution."""
    assert _delta(+0.5, 0.1) < _delta(+0.5, 0.0)


def test_equilibrium_is_finite_not_floor():
    """Iterating cooling + rest converges to a finite warmth above the −1 floor
    (the rest term balances the cooling), instead of spiraling to the clip."""
    a = Agent(id=0, state=AgentState(
        ideology=np.array([0.0, 0.0], dtype=float),
        attrs={"party": 0, "affect": {1: 0.0}, "stubbornness": 0.0}))
    b = Agent(id=1, state=AgentState(
        ideology=np.array([0.9, 0.0], dtype=float),
        attrs={"party": 1, "affect": {}}))
    space = ContinuousSpace2D()
    space.rebuild([a, b])
    env = Environment(attrs={"network": Network({0: {1}, 1: {0}})})
    rule = AffectiveUpdate(radius=1.5, learning_rate=0.05, identity_weight=0.0,
                           baseline=0.0, affect_rest_rate=0.1, affect_rest_anchor=0.0)
    rng = np.random.default_rng(0)
    for _ in range(400):
        d = rule.apply(a, space, env, rng).d_attrs["affect"][1]
        a.state.attrs["affect"][1] = float(np.clip(
            a.state.attrs["affect"][1] + d, -1.0, 1.0))
    w = a.state.attrs["affect"][1]
    assert -1.0 < w < -0.05, f"expected a finite cold equilibrium, got {w}"


def _affect_rule(eng):
    rs = [r for r in eng.rules.rules if type(r).__name__ == "AffectiveUpdate"]
    assert rs, "AffectiveUpdate not in pipeline"
    return rs[0]


def test_build_off_rest_zero():
    eng = build_engine(seed=0, **OFF_KW)
    assert _affect_rule(eng).affect_rest_rate == 0.0
    # …and ON in the shipped R-phase canonical.
    assert _affect_rule(build_engine(seed=0, **ANES_FULL_KWARGS)).affect_rest_rate > 0.0


def test_build_on_passes_rest():
    k = dict(ANES_FULL_KWARGS)
    k.update(affect_rest_rate=0.05, affect_rest_anchor=-0.15)
    eng = build_engine(seed=0, **k)
    r = _affect_rule(eng)
    assert r.affect_rest_rate == 0.05 and r.affect_rest_anchor == -0.15


def _mean_partisan_lr(eng):
    return float(np.mean([a.state.attrs["affect_lr"] for a in eng.agents
                          if a.state.attrs.get("party") in (0, 1)]))


def test_p3a_affect_lr_scale_linear():
    """P3a: affect_lr_scale linearly scales the per-agent cooling rate (the floor
    scales with it, so the reduction is not truncated). 1.0 is the prereq for
    bit-identity (canonical fingerprint guards that)."""
    base = _mean_partisan_lr(build_engine(seed=0, **OFF_KW))
    k = dict(OFF_KW); k.update(affect_lr_scale=0.5)
    half = _mean_partisan_lr(build_engine(seed=0, **k))
    assert abs(half / base - 0.5) < 0.05, f"expected ~0.5x, got {half / base:.3f}"


def test_p3a_affect_saturation_override():
    """P3a affect-shape: affect_saturation overrides the build's saturation (which
    is 0.0 under evidence_regrade). None → keep build logic → bit-identical."""
    base = _affect_rule(build_engine(seed=0, **OFF_KW))
    assert base.saturation == 0.0   # evidence_regrade default (pre-R-phase)
    k = dict(OFF_KW); k.update(affect_saturation=1.0)
    on = _affect_rule(build_engine(seed=0, **k))
    assert on.saturation == 1.0
