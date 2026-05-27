"""Phase 8f §2 — softer 1980 sigmoid party-assignment tests.

Covers:

- Historical build at 1980 uses K=5.0 (the calibrated value); ~88%
  sign-aligned at |x|=0.3.
- PARTY_ASSIGNMENT_K schedule shape (rises across decades).
- Cohort-aware K is plumbed into env.attrs.
- Pillar bit-identity preserved (pillar doesn't seed the schedule).
"""
from __future__ import annotations

import numpy as np

from abm.pillars.calm_to_camps import build_engine as pillar_build
from abm.pillars.historical_arc import (
    PARTY_ASSIGNMENT_K,
    build_engine as historical_build,
)


def test_party_assignment_k_schedule_rises_monotonically():
    """K rises across decades (party-as-coalition → tight coupling)."""
    ks = [PARTY_ASSIGNMENT_K[d] for d in
          ("1980-90", "1990-00", "2000-10", "2010-20", "2020-25")]
    assert all(ks[i] <= ks[i + 1] for i in range(len(ks) - 1))
    # 1980 lower than 2010+ (the literature reading: 1980 fuzzy,
    # modern tight).
    assert PARTY_ASSIGNMENT_K["1980-90"] < PARTY_ASSIGNMENT_K["2010-20"]


def test_historical_build_uses_1980_k():
    """Historical builder reads the 1980 K from the schedule. Verify
    cross-pressured fraction is in the expected range (~12% at K=5 —
    moderate fuzziness vs the prior K=8 default at ~5%)."""
    eng = historical_build(seed=0, n_agents=500)
    partisans = [a for a in eng.agents if a.state.attrs.get("party") in (0, 1)]
    cross_pressured = 0
    for a in partisans:
        x = a.state.ideology[0]
        party = a.state.attrs["party"]
        if (x < 0 and party == 1) or (x > 0 and party == 0):
            cross_pressured += 1
    fraction = cross_pressured / len(partisans)
    # At K=5: theoretical ~12% cross-pressured for the broad-x
    # population. Allow generous tolerance for finite-sample.
    assert 0.05 < fraction < 0.25, (
        f"Cross-pressured fraction at K=5 should be ~12%; got {fraction:.3f}"
    )


def test_party_assignment_k_in_env_attrs():
    """Historical env carries the schedule for cohort replacement."""
    eng = historical_build(seed=0, n_agents=50)
    schedule = eng.env.attrs.get("party_assignment_k_schedule")
    assert schedule is not None
    assert schedule == PARTY_ASSIGNMENT_K


def test_pillar_bit_identity_no_schedule_seeded():
    """Pillar's env does NOT carry party_assignment_k_schedule —
    CohortReplacement (which is inert in pillar but its helper code
    runs cleanly) falls back to sign-only party assignment.
    Pillar invariant preserved."""
    eng = pillar_build(seed=0, n_agents=50)
    assert "party_assignment_k_schedule" not in eng.env.attrs


def test_cohort_replacement_inplace_uses_k_when_schedule_present():
    """When env carries the schedule, _replace_agent_inplace uses
    cohort-aware K. Empirical test: at K=5 (1980 cohort), ~12% of
    replaced agents are cross-pressured."""
    from abm.rules.cohort_replacement import (
        COHORTS, _replace_agent_inplace,
    )
    from abm.core.agent import Agent
    from abm.core.environment import Environment
    from abm.core.state import AgentState
    rng = np.random.default_rng(0)
    cohort = dict(COHORTS["boomer"])
    cohort["_label"] = "boomer"
    env = Environment(attrs={
        "parties": {0: np.array([-0.3, -0.08]), 1: np.array([0.3, 0.08])},
        "party_assignment_k_schedule": PARTY_ASSIGNMENT_K,
    })
    n = 500
    cross_pressured = 0
    for i in range(n):
        a = Agent(
            id=i,
            state=AgentState(
                ideology=np.array([0.0, 0.0]),
                attrs={"party": 0, "stubbornness": 0.0,
                       "identities": np.zeros(3), "affect": {1: 0.0}},
            ),
        )
        _replace_agent_inplace(a, cohort, env, rng)
        x = a.state.ideology[0]
        p = a.state.attrs["party"]
        if (x < 0 and p == 1) or (x > 0 and p == 0):
            cross_pressured += 1
    fraction = cross_pressured / n
    # K=5 at the boomer cohort → ~12% cross-pressured.
    assert 0.05 < fraction < 0.30, (
        f"Expected ~12% cross-pressured at K=5; got {fraction:.3f}"
    )
