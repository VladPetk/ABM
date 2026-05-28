"""Phase 8c §3 — per-outlet MediaConsumption + X3 re-implementation tests.

Covers:

- Per-outlet pull equals diet_target * strength for normalised diets
  (regression guard: pillar S0-S4 bit-identical to Phase 7).
- Per-outlet pull magnitude shrinks when X3 zeros cable weights
  (no re-normalisation; Fork 3-B default).
- X3 setup zeros only MSNBC + Fox News (id=0, 4); leaves
  NYT, Local TV, WSJ untouched.
- Pillar-fallback discipline: scenario without media_diet (compass_basic)
  is bit-identical to Phase 8b.
"""
from __future__ import annotations

import numpy as np

from abm.core.agent import Agent
from abm.core.environment import Environment
from abm.core.outlets import (
    US_MEDIA_OUTLETS_2024,
    diet_target,
)
from abm.core.space import ContinuousSpace2D
from abm.core.state import AgentState
from abm.pillars import (
    PILLAR,
    X3_QUIT_CABLE_NEWS,
    apply_intervention,
)
from abm.pillars.calm_to_camps import build_engine as pillar_build
from abm.pillars.interventions_phase6 import X3_PARTISAN_CABLE_OUTLET_IDS
from abm.rules.media_consumption import MediaConsumption


# ---------------------------------------------------------------------
# Per-outlet pull regression guard.
# ---------------------------------------------------------------------


def _outlets_by_id():
    return {o.id: o for o in US_MEDIA_OUTLETS_2024}


def _agent_with_diet(pos, diet):
    return Agent(
        id=0,
        state=AgentState(
            ideology=np.array(pos, dtype=float),
            attrs={"media_diet": dict(diet), "stubbornness": 0.0},
        ),
    )


def test_per_outlet_pull_equals_diet_target_for_normalized_diet():
    """When diet weights sum to 1 (normalised — every pillar /
    historical-arc agent), the new per-outlet pull equals
    `strength * (diet_target - ideology)` exactly. Pillar S0-S4
    bit-identical to Phase 7."""
    outlets_by_id = _outlets_by_id()
    diet = {0: 0.1, 1: 0.2, 2: 0.3, 3: 0.2, 4: 0.2}  # sums to 1.0
    pos = np.array([0.2, -0.1])
    a = _agent_with_diet(pos, diet)
    space = ContinuousSpace2D()
    space.rebuild([a])
    env = Environment(attrs={"outlets": outlets_by_id})
    rule = MediaConsumption(strength=0.04)
    delta = rule.apply(a, space, env, np.random.default_rng(0))
    target = diet_target(diet, outlets_by_id)
    expected = 0.04 * (target - pos)
    assert np.allclose(delta.d_ideology, expected, atol=1e-12), (
        f"For normalised diet, per-outlet pull should equal "
        f"strength * (diet_target - ideology). Got {delta.d_ideology}, "
        f"expected {expected}."
    )


def test_per_outlet_pull_shrinks_when_diet_partially_zeroed():
    """When X3 zeros MSNBC + Fox weights (Fork 3-B default: no
    re-normalisation), the remaining outlets pull at their original
    absolute weights and the agent's total media intake drops
    proportionally."""
    outlets_by_id = _outlets_by_id()
    full_diet = {0: 0.1, 1: 0.2, 2: 0.3, 3: 0.2, 4: 0.2}
    cable_zeroed = {0: 0.0, 1: 0.2, 2: 0.3, 3: 0.2, 4: 0.0}  # ~70% intake
    pos = np.array([0.2, -0.1])
    space = ContinuousSpace2D()
    env = Environment(attrs={"outlets": outlets_by_id})
    rule = MediaConsumption(strength=0.04)

    a_full = _agent_with_diet(pos, full_diet)
    space.rebuild([a_full])
    d_full = rule.apply(a_full, space, env, np.random.default_rng(0)).d_ideology

    a_zeroed = _agent_with_diet(pos, cable_zeroed)
    space.rebuild([a_zeroed])
    d_zeroed = rule.apply(
        a_zeroed, space, env, np.random.default_rng(0)
    ).d_ideology

    # Pull magnitude should drop because cable's contribution is gone.
    assert np.linalg.norm(d_zeroed) < np.linalg.norm(d_full), (
        f"Pull magnitude should drop after zeroing cable. "
        f"full={np.linalg.norm(d_full):.4f}, zeroed={np.linalg.norm(d_zeroed):.4f}"
    )
    # Specifically, d_zeroed equals the contribution of NYT+Local+WSJ
    # at their original weights (NOT re-normalised).
    expected_zeroed_pull = sum(
        w * (outlets_by_id[oid].position - pos)
        for oid, w in cable_zeroed.items()
        if w > 0
    )
    expected_zeroed = 0.04 * expected_zeroed_pull
    assert np.allclose(d_zeroed, expected_zeroed, atol=1e-12), (
        f"d_zeroed should equal absolute per-outlet pull of "
        f"remaining outlets. Got {d_zeroed}, expected {expected_zeroed}."
    )


def test_per_outlet_no_renormalisation_after_x3():
    """X3 zeroing cable should NOT boost remaining outlets'
    contributions (Fork 3-B default: no re-normalisation). NYT's
    pull magnitude stays at its absolute weight, not boosted to fill
    the 100% mark."""
    outlets_by_id = _outlets_by_id()
    pos = np.array([0.2, -0.1])
    space = ContinuousSpace2D()
    env = Environment(attrs={"outlets": outlets_by_id})
    rule = MediaConsumption(strength=0.04)

    # NYT-only diet (id=1), weight 0.2 (NOT normalised — absolute).
    nyt_only = {1: 0.2}
    a = _agent_with_diet(pos, nyt_only)
    space.rebuild([a])
    d = rule.apply(a, space, env, np.random.default_rng(0)).d_ideology
    # Expected: 0.04 * 0.2 * (NYT.pos - pos) = 0.008 * (NYT.pos - pos).
    expected = 0.04 * 0.2 * (outlets_by_id[1].position - pos)
    assert np.allclose(d, expected, atol=1e-12), (
        f"Single-outlet pull at weight 0.2 should not be boosted. "
        f"Got {d}, expected {expected}"
    )


# ---------------------------------------------------------------------
# X3 setup zeros only cable outlets.
# ---------------------------------------------------------------------


def test_x3_setup_zeros_only_partisan_cable_outlets():
    """X3 zeroes MSNBC (id=0) + Fox News (id=4) weights for the
    treated 20% of agents; leaves all non-cable outlets untouched
    for every agent.

    Phase 10 reframe (was Phase 8c §3 §3-A): Phase 6 / Phase 8c X3
    zeroed the cable outlets for *all* agents (100% reach). Phase
    10 X3 redesigns this as a low-prevalence counterfactual per
    Allcott et al. 2020 take-up envelope — applied to a treated
    20% fraction of agents. The test therefore checks: (a) ~20%
    of agents have cable zeroed (deterministic given the X3 RNG
    seed); (b) non-cable outlets are untouched for ALL agents
    regardless of treatment; (c) untreated agents retain their
    original cable weights.
    """
    from abm.pillars.interventions_phase6 import X3_TREATED_FRACTION
    eng = pillar_build(seed=0, n_agents=100)
    apply_intervention(eng, PILLAR.interventions[4])
    eng.run(50)
    # Snapshot pre-X3 diets in full.
    pre = {
        a.id: dict(a.state.attrs.get("media_diet") or {})
        for a in eng.agents
    }
    apply_intervention(eng, X3_QUIT_CABLE_NEWS)
    # Count treated (cable zeroed).
    n_treated = 0
    for a in eng.agents:
        diet = a.state.attrs.get("media_diet") or {}
        # Non-cable outlets unchanged for every agent.
        for oid, pre_w in pre[a.id].items():
            if oid in X3_PARTISAN_CABLE_OUTLET_IDS:
                continue
            assert diet.get(oid) == pre_w, (
                f"agent {a.id}: non-cable outlet {oid} weight "
                f"changed from {pre_w} to {diet.get(oid)} — X3 should "
                f"leave it alone"
            )
        # Determine treatment status from cable weights.
        cable_all_zero = all(
            diet.get(cable_id, 0.0) == 0.0
            for cable_id in X3_PARTISAN_CABLE_OUTLET_IDS
        )
        if cable_all_zero:
            n_treated += 1
        else:
            # Untreated agent: cable weights match pre-X3.
            for cable_id in X3_PARTISAN_CABLE_OUTLET_IDS:
                if cable_id in pre[a.id]:
                    assert diet.get(cable_id) == pre[a.id][cable_id], (
                        f"untreated agent {a.id}: cable outlet "
                        f"{cable_id} weight changed unexpectedly"
                    )
    expected = int(X3_TREATED_FRACTION * len(eng.agents))
    assert n_treated == expected, (
        f"X3 should treat {expected} agents ({X3_TREATED_FRACTION:.0%} "
        f"of {len(eng.agents)}); got {n_treated}"
    )


def test_x3_partisan_cable_outlet_ids_are_msnbc_and_fox():
    """The X3 cable-outlet id set matches MSNBC + Fox News in the
    default US_MEDIA_OUTLETS_2024 roster. Regression guard for the
    spec's §3-A default (Fork 3-A)."""
    by_name = {o.name: o.id for o in US_MEDIA_OUTLETS_2024}
    assert by_name["MSNBC"] in X3_PARTISAN_CABLE_OUTLET_IDS
    assert by_name["Fox News"] in X3_PARTISAN_CABLE_OUTLET_IDS
    assert by_name["New York Times"] not in X3_PARTISAN_CABLE_OUTLET_IDS, (
        "NYT should not be in the X3 cable set (Fork 3-A default: "
        "only MSNBC + Fox News)"
    )
    assert by_name["Wall St Journal"] not in X3_PARTISAN_CABLE_OUTLET_IDS, (
        "WSJ should not be in the X3 cable set"
    )
    assert by_name["Local TV"] not in X3_PARTISAN_CABLE_OUTLET_IDS


# ---------------------------------------------------------------------
# Pillar-fallback: compass_basic without media_diet bit-identical.
# ---------------------------------------------------------------------


def test_media_consumption_no_op_without_diet():
    """An agent without a media_diet attr produces no d_ideology —
    same as Phase 7. Pillar-fallback for scenarios that don't seed
    media_diet (compass_basic, actb, etc.)."""
    a = Agent(
        id=0,
        state=AgentState(
            ideology=np.array([0.0, 0.0]),
            attrs={"stubbornness": 0.0},  # no media_diet
        ),
    )
    space = ContinuousSpace2D()
    space.rebuild([a])
    env = Environment(attrs={"outlets": _outlets_by_id()})
    rule = MediaConsumption(strength=0.04)
    delta = rule.apply(a, space, env, np.random.default_rng(0))
    assert np.array_equal(delta.d_ideology, np.zeros(2)), (
        f"No media_diet → no d_ideology; got {delta.d_ideology}"
    )


def test_media_consumption_no_op_without_outlets():
    """Same fallback for env without outlets dict."""
    a = _agent_with_diet([0.0, 0.0], {0: 0.5, 4: 0.5})
    space = ContinuousSpace2D()
    space.rebuild([a])
    env = Environment(attrs={})  # no outlets
    rule = MediaConsumption(strength=0.04)
    delta = rule.apply(a, space, env, np.random.default_rng(0))
    assert np.array_equal(delta.d_ideology, np.zeros(2)), (
        f"No outlets env attr → no d_ideology; got {delta.d_ideology}"
    )


def test_media_consumption_zero_strength_no_op():
    """`strength = 0` short-circuit preserved."""
    a = _agent_with_diet([0.0, 0.0], {0: 0.5, 4: 0.5})
    space = ContinuousSpace2D()
    space.rebuild([a])
    env = Environment(attrs={"outlets": _outlets_by_id()})
    rule = MediaConsumption(strength=0.0)
    delta = rule.apply(a, space, env, np.random.default_rng(0))
    assert np.array_equal(delta.d_ideology, np.zeros(2))
