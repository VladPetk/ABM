"""Phase 9 Tier C — FactionAnchor rule tests.

Covers:
- No-op for agents lacking `faction_center` attr.
- Linear pull toward `faction_center` at strength × (1 - stubbornness).
- Stubbornness scales the pull (FJ-style).
- Clipping to the unit box.
- Pillar: no agent ever gets `faction_center` even after a full run.
- 2015 MAGA event sets faction_center near (+0.50, +0.55), does NOT
  overwrite party_cue.
- Post-event drift: tagged agents move under FactionAnchor over time.
- `event_stubbornness_bump_multiplier` halves the +0.15 → +0.075 bump.
"""
from __future__ import annotations

import numpy as np
import pytest

from abm.core.agent import Agent
from abm.core.environment import Environment
from abm.core.space import ContinuousSpace2D
from abm.core.state import AgentState
from abm.pillars import historical_arc as ha
from abm.pillars.calm_to_camps import build_engine as pillar_build
from abm.pillars.historical_arc import build_engine, build_schedule
from abm.pillars.schedule import run_to
from abm.rules.faction_anchor import FactionAnchor


# ---------------------------------------------------------------------
# Unit tests on the rule itself
# ---------------------------------------------------------------------


def _make_agent(ideology, **attrs):
    return Agent(
        id=0,
        state=AgentState(
            ideology=np.asarray(ideology, dtype=float), attrs=dict(attrs)
        ),
    )


def _empty_env():
    return Environment(attrs={})


def _space():
    return ContinuousSpace2D(bounds=((-1.0, 1.0), (-1.0, 1.0)))


def test_no_faction_center_attr_no_op():
    """Agents without `faction_center` get a zero StateDelta."""
    rule = FactionAnchor(strength=0.04)
    a = _make_agent([0.1, 0.2], stubbornness=0.0)
    d = rule.apply(a, _space(), _empty_env(), np.random.default_rng(0))
    assert np.array_equal(d.d_ideology, np.zeros(2))
    assert d.d_attrs == {}


def test_faction_anchor_pulls_toward_center():
    """At strength=0.1, stubbornness=0, center=(0.5, 0.5), origin=(0, 0)
    → delta == (0.05, 0.05) (linear pull, single tick)."""
    rule = FactionAnchor(strength=0.1)
    a = _make_agent(
        [0.0, 0.0],
        stubbornness=0.0,
        faction_center=np.array([0.5, 0.5]),
    )
    d = rule.apply(a, _space(), _empty_env(), np.random.default_rng(0))
    assert np.allclose(d.d_ideology, [0.05, 0.05])


def test_stubbornness_scales_pull():
    """Stubbornness=0.5 → pull is halved relative to stubbornness=0."""
    rule = FactionAnchor(strength=0.1)
    a = _make_agent(
        [0.0, 0.0],
        stubbornness=0.5,
        faction_center=np.array([0.5, 0.5]),
    )
    d = rule.apply(a, _space(), _empty_env(), np.random.default_rng(0))
    assert np.allclose(d.d_ideology, [0.025, 0.025])


def test_faction_anchor_clipped_to_unit_box():
    """The engine's space.clip applies after the agent phase; here we
    verify the rule's delta plus current ideology, after clipping, stays
    inside [-1, 1]^2. center=(2.0, 0) is outside-the-box defensively
    (events should never set it there, but the rule shouldn't explode).
    """
    rule = FactionAnchor(strength=1.0)   # extreme to test clipping
    a = _make_agent(
        [0.95, 0.0],
        stubbornness=0.0,
        faction_center=np.array([2.0, 0.0]),
    )
    d = rule.apply(a, _space(), _empty_env(), np.random.default_rng(0))
    # raw new position would be 0.95 + 1.0 * (2.0 - 0.95) = 2.0
    new = _space().clip(a.state.ideology + d.d_ideology)
    assert -1.0 <= new[0] <= 1.0
    assert -1.0 <= new[1] <= 1.0
    assert new[0] == 1.0


# ---------------------------------------------------------------------
# Pillar bit-identity gate
# ---------------------------------------------------------------------


def test_faction_anchor_in_pillar_no_op():
    """Pillar build: no agent has `faction_center`. Run a short loop;
    no agent acquires `faction_center` (the pillar never tags)."""
    eng = pillar_build(seed=0, n_agents=50)
    eng.run(20)
    for a in eng.agents:
        assert a.state.attrs.get("faction_center") is None


# ---------------------------------------------------------------------
# Tier C event semantics
# ---------------------------------------------------------------------


def test_event_2015_maga_sets_faction_center_not_party_cue():
    """The 2015 MAGA event should:
      - set `faction_center` ≈ (+0.50, +0.55) on tagged agents,
      - leave `party_cue` near its original party-centroid-noise value
        (NOT overwrite it with the sub-centroid as Tier A did)."""
    eng = build_engine(
        seed=0, n_agents=300,
        independent_fraction=0.12,
        factional_seeding=True,
    )
    sched = build_schedule(factional_seeding=True)
    # Snapshot party_cue values BEFORE MAGA fires for every partisan.
    run_to(eng, sched, 104)
    pre_cue = {
        a.id: np.asarray(a.state.attrs.get("party_cue")).copy()
        for a in eng.agents
        if a.state.attrs.get("party_cue") is not None
    }
    # Advance past MAGA at tick 105.
    run_to(eng, sched, 107)
    maga = [
        a for a in eng.agents
        if a.state.attrs.get("faction") == "MAGA"
    ]
    assert maga, "MAGA event should have tagged some agents"
    target = np.array([0.50, 0.55])
    for a in maga:
        center = np.asarray(a.state.attrs["faction_center"])
        assert np.allclose(center, target), (
            f"agent {a.id} faction_center {center} != {target}"
        )
        # party_cue should NOT equal the sub-centroid (Tier C: not
        # overwritten). It either matches the pre-event value or
        # is missing (independents had no party_cue but they're not
        # tagged either). At minimum: party_cue distance to target is
        # large (we did NOT overwrite to sub-centroid + 0.04 noise).
        cue = a.state.attrs.get("party_cue")
        if cue is not None:
            assert np.linalg.norm(cue - target) > 0.10, (
                f"agent {a.id} party_cue {cue} suspiciously close to "
                f"sub-centroid {target} — Tier C should not overwrite"
            )


def test_post_event_drift():
    """After MAGA fires, tagged agents should drift over subsequent
    ticks (FactionAnchor pulls them toward sub-centroid). Their
    position at +10 ticks differs from their position at MAGA-fire."""
    eng = build_engine(
        seed=0, n_agents=300,
        independent_fraction=0.12,
        factional_seeding=True,
    )
    sched = build_schedule(factional_seeding=True)
    # Run up to just-after MAGA fires.
    run_to(eng, sched, 106)
    maga_ids = [
        a.id for a in eng.agents
        if a.state.attrs.get("faction") == "MAGA"
    ]
    assert maga_ids
    pos_at_fire = {
        a.id: a.state.ideology.copy() for a in eng.agents if a.id in maga_ids
    }
    # Run 10 more ticks.
    run_to(eng, sched, 116)
    moved = 0
    for a in eng.agents:
        if a.id not in maga_ids:
            continue
        if not np.array_equal(a.state.ideology, pos_at_fire[a.id]):
            moved += 1
    # Almost all MAGA agents should have drifted (FactionAnchor + the
    # rest of the pipeline both contribute).
    assert moved >= max(1, int(0.8 * len(maga_ids)))


def test_event_bump_multiplier():
    """`event_stubbornness_bump_multiplier=0.5` halves the +0.15 bump
    to +0.075 for MAGA-tagged agents. We measure the stubbornness
    delta on the same seeded population."""
    # Run without the multiplier first to establish baseline delta.
    eng_a = build_engine(
        seed=0, n_agents=300, independent_fraction=0.12,
        factional_seeding=True,
        event_stubbornness_bump_multiplier=1.0,
    )
    sched_a = build_schedule(factional_seeding=True)
    run_to(eng_a, sched_a, 104)
    pre_stub_a = {a.id: float(a.state.attrs["stubbornness"])
                  for a in eng_a.agents
                  if "stubbornness" in a.state.attrs}
    ha._event_2015_maga(eng_a)
    post_stub_a = {a.id: float(a.state.attrs["stubbornness"])
                   for a in eng_a.agents}
    maga_a = [a.id for a in eng_a.agents
              if a.state.attrs.get("faction") == "MAGA"]
    deltas_a = []
    for aid in maga_a:
        if aid in pre_stub_a:
            # Only count deltas where the cap didn't bind (cap = 0.95).
            if post_stub_a[aid] < 0.9499:
                deltas_a.append(post_stub_a[aid] - pre_stub_a[aid])

    # Now with multiplier=0.5.
    eng_b = build_engine(
        seed=0, n_agents=300, independent_fraction=0.12,
        factional_seeding=True,
        event_stubbornness_bump_multiplier=0.5,
    )
    sched_b = build_schedule(factional_seeding=True)
    run_to(eng_b, sched_b, 104)
    pre_stub_b = {a.id: float(a.state.attrs["stubbornness"])
                  for a in eng_b.agents
                  if "stubbornness" in a.state.attrs}
    ha._event_2015_maga(eng_b)
    post_stub_b = {a.id: float(a.state.attrs["stubbornness"])
                   for a in eng_b.agents}
    maga_b = [a.id for a in eng_b.agents
              if a.state.attrs.get("faction") == "MAGA"]
    deltas_b = []
    for aid in maga_b:
        if aid in pre_stub_b:
            if post_stub_b[aid] < 0.9499:
                deltas_b.append(post_stub_b[aid] - pre_stub_b[aid])

    # Baseline ~ +0.15; halved ~ +0.075.
    assert deltas_a, "should have some uncapped MAGA agents in baseline"
    assert deltas_b, "should have some uncapped MAGA agents in halved"
    mean_a = float(np.mean(deltas_a))
    mean_b = float(np.mean(deltas_b))
    assert abs(mean_a - 0.15) < 1e-6
    assert abs(mean_b - 0.075) < 1e-6
