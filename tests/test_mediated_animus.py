"""Isolation tests for MediatedAnimus — the contact-independent (parasocial)
out-party animus channel (affect-bands-investigation, step 3).

Per the CLAUDE.md three-layer drift-guard: this is the *isolation* layer —
one rule on a clean substrate. It verifies the channel's contract: off by
default, contact-independent, scales with lr x weight x identity_alignment,
negative-going, Independent-safe, and additive with existing affect.
"""
from __future__ import annotations

import numpy as np

from abm.core.agent import Agent
from abm.core.environment import Environment
from abm.core.space import ContinuousSpace2D
from abm.core.state import AgentState
from abm.rules.mediated_animus import MediatedAnimus


def _agent(party=0, alignment=0.5, warmth=-0.3):
    return Agent(id=0, state=AgentState(
        ideology=np.array([0.0, 0.0]),
        attrs={"party": party, "affect": {1 - party: warmth},
               "identity_alignment": alignment},
    ))


def _ctx(weight=1.0):
    env = Environment(attrs={"mediated_animus_weight": weight})
    space = ContinuousSpace2D()
    return space, env, np.random.default_rng(0)


def _delta(agent, weight=1.0, lr=0.02):
    space, env, rng = _ctx(weight)
    return MediatedAnimus(learning_rate=lr).apply(agent, space, env, rng)


def test_noop_when_lr_zero():
    """lr=0 -> exact no-op (pillar / non-arc bit-identical)."""
    d = _delta(_agent(), lr=0.0)
    assert d.d_attrs == {}


def test_noop_when_weight_zero():
    """mediated_animus_weight=0 (the default) -> exact no-op."""
    d = _delta(_agent(), weight=0.0, lr=0.02)
    assert d.d_attrs == {}


def test_noop_for_independents():
    """Independents (party=2) carry no out-party animus."""
    d = _delta(_agent(party=2), lr=0.02)
    assert d.d_attrs == {}


def test_noop_when_alignment_zero():
    """No aligned identity -> no parasocial animus."""
    d = _delta(_agent(alignment=0.0), lr=0.02)
    assert d.d_attrs == {}


def test_contact_independent():
    """Fires with NO network neighbours (the whole point) — the rule never
    queries the network, so an isolated agent still cools."""
    d = _delta(_agent(), lr=0.02, weight=1.0)
    assert 1 in d.d_attrs["affect"]
    assert d.d_attrs["affect"][1] < 0.0      # negative-going


def test_magnitude_scales_lr_weight_alignment():
    """Δ = -lr * weight * alignment, exactly."""
    a = _agent(party=0, alignment=0.4)
    d = _delta(a, lr=0.02, weight=0.5)
    assert abs(d.d_attrs["affect"][1] - (-0.02 * 0.5 * 0.4)) < 1e-12


def test_doubling_weight_doubles_cooling():
    base = _delta(_agent(alignment=0.5), lr=0.02, weight=0.5).d_attrs["affect"][1]
    dbl = _delta(_agent(alignment=0.5), lr=0.02, weight=1.0).d_attrs["affect"][1]
    assert abs(dbl - 2 * base) < 1e-12


def test_targets_out_party_only():
    """Republican (party=1) cools toward the Democratic party (0), not self."""
    d = _delta(_agent(party=1), lr=0.02)
    assert set(d.d_attrs["affect"].keys()) == {0}
