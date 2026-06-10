"""T0.1 drift guards (MHV spec docs/internal/mhv_spec.md S0/T0.1).

PARTY_ASSIGNMENT_K_ANES is retired (dead code under the shipped config —
docs/internal/calibration_interpretation.md §2.1 Option A) and the shipped 1.6
sigma_pc multiplier is folded into PARTY_CUE_SIGMA_HISTORICAL_ANES.
These tests pin the deprecation contract: the kwarg stays accepted, warns,
and is a behavioral no-op; the legacy non-ANES K machinery is untouched.
"""
import warnings

import numpy as np
import pytest

import abm.pillars.historical_arc as H
from abm.pillars.schedule import Schedule, run_to

ANES_FLAGS = {
    "n_agents": 80,
    "tier_d_axis_balance": True,
    "tier_d_anes_knobs": True,
}


def _snapshot(eng, ticks=4):
    sched = Schedule([])
    for t in range(1, ticks + 1):
        run_to(eng, sched, t)
    pos = eng.positions()
    cues = np.array([
        np.asarray(a.state.attrs.get("party_cue", np.zeros(2)), dtype=float)
        for a in eng.agents
    ])
    return pos, cues


def test_party_assignment_k_anes_retired():
    assert not hasattr(H, "PARTY_ASSIGNMENT_K_ANES")


def test_sigma_pc_fold_exact_values():
    # the fold must be the exact IEEE products the old runtime computed
    assert H.PARTY_CUE_SIGMA_HISTORICAL_ANES[0] == 0.42 * 1.6
    assert H.PARTY_CUE_SIGMA_HISTORICAL_ANES[1] == 0.57 * 1.6


def test_sigma_pc_multiplier_warns_and_is_noop():
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        eng_plain = H.build_engine(seed=0, **ANES_FLAGS)
    with pytest.warns(DeprecationWarning, match="sigma_pc_multiplier"):
        eng_mult = H.build_engine(
            seed=0, tier_d_anes_sigma_pc_multiplier=1.6, **ANES_FLAGS
        )
    pos_a, cue_a = _snapshot(eng_plain)
    pos_b, cue_b = _snapshot(eng_mult)
    assert np.array_equal(pos_a, pos_b)
    assert np.array_equal(cue_a, cue_b)


def test_legacy_k_schedule_still_registered():
    # non-ANES (legacy) path: the live K-sigmoid machinery is untouched
    eng = H.build_engine(seed=0, n_agents=80)
    assert eng.env.attrs.get("party_assignment_k_schedule") == H.PARTY_ASSIGNMENT_K
    # ANES path: the registered schedule now carries the legacy values too
    # (provably never consumed there — party is pre-committed, and cohort
    # replacement takes the ANES centroid-anchor branch).
    eng2 = H.build_engine(seed=0, **ANES_FLAGS)
    assert eng2.env.attrs.get("party_assignment_k_schedule") == H.PARTY_ASSIGNMENT_K
