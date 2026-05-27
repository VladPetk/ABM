"""Phase 8e §3 — per-agent media_cue tests.

Covers:

- MediaConsumption reads media_cue with fallback None (no bias);
  pillar bit-identical to Phase 8d.
- Historical_arc partisan agents seed media_cue ~ N(0, 0.15);
  Independents do NOT (centrist diet by construction).
- An agent with non-zero media_cue is pulled in the shifted-effective-
  outlet direction.
"""
from __future__ import annotations

import numpy as np

from abm.core.agent import Agent
from abm.core.environment import Environment
from abm.core.outlets import US_MEDIA_OUTLETS_2024
from abm.core.space import ContinuousSpace2D
from abm.core.state import AgentState
from abm.pillars import PILLAR, apply_intervention
from abm.pillars.calm_to_camps import build_engine as pillar_build
from abm.pillars.historical_arc import (
    MEDIA_CUE_SIGMA,
    build_engine as historical_build,
)
from abm.rules.media_consumption import MediaConsumption


def test_media_consumption_pillar_fallback_no_cue():
    """Agent without media_cue uses unbiased outlet positions —
    pillar bit-identical to Phase 8d. The keystone pillar invariant
    check for §8e.3."""
    outlets_by_id = {o.id: o for o in US_MEDIA_OUTLETS_2024}
    diet = {0: 0.1, 1: 0.2, 2: 0.3, 3: 0.2, 4: 0.2}  # sums to 1.0
    pos = np.array([0.2, -0.1])
    a = Agent(
        id=0,
        state=AgentState(
            ideology=pos.copy(),
            attrs={"media_diet": dict(diet), "stubbornness": 0.0},
            # No media_cue.
        ),
    )
    space = ContinuousSpace2D()
    space.rebuild([a])
    env = Environment(attrs={"outlets": outlets_by_id})
    rule = MediaConsumption(strength=0.04)
    delta = rule.apply(a, space, env, np.random.default_rng(0))
    # Expected: sum of weight_i * (outlet_i.position - pos), * 0.04.
    expected = 0.04 * sum(
        diet[oid] * (outlets_by_id[oid].position - pos)
        for oid in diet
    )
    assert np.allclose(delta.d_ideology, expected, atol=1e-12)


def test_media_consumption_with_cue_shifts_pull_direction():
    """An agent with positive-x media_cue is pulled MORE in the +x
    direction than the same agent without the cue."""
    outlets_by_id = {o.id: o for o in US_MEDIA_OUTLETS_2024}
    diet = {0: 0.1, 1: 0.2, 2: 0.3, 3: 0.2, 4: 0.2}  # sums to 1.0
    pos = np.array([0.0, 0.0])
    cue = np.array([0.3, 0.0])  # right-biased media perception

    a_no_cue = Agent(
        id=0,
        state=AgentState(
            ideology=pos.copy(),
            attrs={"media_diet": dict(diet), "stubbornness": 0.0},
        ),
    )
    a_with_cue = Agent(
        id=1,
        state=AgentState(
            ideology=pos.copy(),
            attrs={
                "media_diet": dict(diet),
                "stubbornness": 0.0,
                "media_cue": cue.copy(),
            },
        ),
    )
    space = ContinuousSpace2D()
    env = Environment(attrs={"outlets": outlets_by_id})
    rule = MediaConsumption(strength=0.04)

    space.rebuild([a_no_cue])
    d_no_cue = rule.apply(
        a_no_cue, space, env, np.random.default_rng(0)
    ).d_ideology
    space.rebuild([a_with_cue])
    d_with_cue = rule.apply(
        a_with_cue, space, env, np.random.default_rng(0)
    ).d_ideology
    # Positive cue on x → pull is shifted +x.
    assert d_with_cue[0] > d_no_cue[0], (
        f"Positive media_cue should shift pull +x; no_cue={d_no_cue}, "
        f"with_cue={d_with_cue}"
    )


def test_historical_partisan_agents_seed_media_cue():
    """Phase 8e §3: partisan historical agents carry media_cue."""
    eng = historical_build(seed=0, n_agents=200)
    partisans = [a for a in eng.agents if a.state.attrs.get("party") in (0, 1)]
    assert all("media_cue" in a.state.attrs for a in partisans)


def test_historical_independents_lack_media_cue():
    """Phase 8e §3: Independents (party=2) do NOT carry media_cue
    (centrist diet by construction; no need for partisan-cue bias)."""
    eng = historical_build(
        seed=0, n_agents=200, independent_fraction=0.20,
    )
    indeps = [a for a in eng.agents if a.state.attrs.get("party") == 2]
    assert len(indeps) > 0
    assert not any("media_cue" in a.state.attrs for a in indeps)


def test_historical_media_cue_mean_zero():
    """Population-mean media_cue is approximately zero (N(0, 0.15)
    distribution; partisan population)."""
    eng = historical_build(seed=0, n_agents=400)
    cues = [
        a.state.attrs["media_cue"] for a in eng.agents
        if "media_cue" in a.state.attrs
    ]
    mean_cue = np.mean(np.array(cues), axis=0)
    assert all(abs(x) < 0.05 for x in mean_cue), (
        f"Media_cue population mean should be near zero; got {mean_cue}"
    )


def test_pillar_S4_bit_identical_without_media_cue():
    """Phase 8e §3 keystone: pillar S4 trajectory bit-identical to
    Phase 8d (no media_cue seeded; fallback None)."""
    eng_before = pillar_build(seed=0, n_agents=100)
    apply_intervention(eng_before, PILLAR.interventions[4])
    eng_before.run(50)
    eng_after = pillar_build(seed=0, n_agents=100)
    apply_intervention(eng_after, PILLAR.interventions[4])
    eng_after.run(50)
    pos_before = np.array([a.state.ideology for a in eng_before.agents])
    pos_after = np.array([a.state.ideology for a in eng_after.agents])
    # Both runs at default — should be bit-identical.
    assert np.allclose(pos_before, pos_after, atol=1e-12)
