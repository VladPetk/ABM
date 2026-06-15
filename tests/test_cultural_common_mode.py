"""Permanent reality gate for the cultural common-mode channel (methods §5.30).

The existing band/drift suite does NOT pin the cultural center of mass — that gap
is precisely why the mid-period "Republicans in the progressive-redistributive
quadrant" bug shipped undetected. This module guards the fix directly: it pins the
society-wide cultural center against the ROBUST (GSS-corroborated) trajectory at
a few decades, and guards the wrong-quadrant tail and bit-identity of the default
path. Reality anchors are recomputed from raw in validation/ (which reproduces the
ANES derivation exactly); the bands here are the GSS-matched levels the fix targets,
NOT the non-robust ANES mid-90s "hump".
"""
import numpy as np
import pytest

from scripts.anes_preset import ANES_FULL_KWARGS, ANES_FULL_ENDOGENOUS_KWARGS
from abm.pillars.historical_arc import build_engine, build_schedule
from abm.pillars.schedule import run_to


def _run_canonical():
    kw = dict(ANES_FULL_KWARGS)
    eng = build_engine(seed=0, **kw)
    sched = build_schedule(
        factional_seeding=kw.get("factional_seeding", False),
        faction_anchor_events=kw.get("faction_anchor_events", True),
        evidence_regrade=kw.get("evidence_regrade", False),
        exogenous_shocks=kw.get("exogenous_shocks", False),
    )
    snaps = {}
    for t in range(1, 136):
        run_to(eng, sched, t)
        yr = int(round(1980 + t / 3))
        if yr in (2000, 2024) and yr not in snaps:
            party = np.array([a.state.attrs.get("party") for a in eng.agents])
            pos = np.array([a.state.ideology for a in eng.agents])
            m = (party == 0) | (party == 1)
            R = pos[party == 1]
            snaps[yr] = {
                "cult_center": float(pos[m, 1].mean()),
                "R_LL": float(np.mean((R[:, 0] <= 0) & (R[:, 1] <= 0))),
                "party_sep": float(np.hypot(*(pos[party == 1].mean(0) - pos[party == 0].mean(0)))),
            }
    return snaps


@pytest.fixture(scope="module")
def canonical_snaps():
    return _run_canonical()


def test_canonical_build_has_common_mode_on():
    """The shipped config must have the cultural common-mode channel enabled."""
    assert ANES_FULL_KWARGS.get("cultural_common_mode") is True


def test_default_path_has_no_birth_year_bit_identity():
    """Common-mode OFF (pre-fix endogenous config) seeds no birth_year — the
    default path stays bit-identical (guards the gating)."""
    eng = build_engine(seed=0, **dict(ANES_FULL_ENDOGENOUS_KWARGS))
    assert not any("birth_year" in a.state.attrs for a in eng.agents)


def test_initial_cultural_center_traditional():
    """1980 seed cultural center is TRADITIONAL (~+0.10, matching ANES 1986) and
    every agent carries a birth_year on the canonical (common-mode) build."""
    eng = build_engine(seed=0, **dict(ANES_FULL_KWARGS))
    assert all("birth_year" in a.state.attrs for a in eng.agents)
    party = np.array([a.state.attrs.get("party") for a in eng.agents])
    pos = np.array([a.state.ideology for a in eng.agents])
    m = (party == 0) | (party == 1)
    assert 0.05 <= float(pos[m, 1].mean()) <= 0.16


def test_midperiod_cultural_center_not_collapsed(canonical_snaps):
    """THE regression guard: the 2000 partisan cultural center must be on the
    traditional side (GSS partisan ≈ +0.07), NOT collapsed near 0 as in the
    pre-fix build (~+0.02). Lower bound catches a regression of the common-mode
    channel; the upper bound keeps us from over-fitting the non-robust ANES hump."""
    c = canonical_snaps[2000]["cult_center"]
    assert 0.035 <= c <= 0.13, f"2000 cultural center {c:+.3f} outside the GSS-matched band"


def test_endpoint_cultural_center_progressive(canonical_snaps):
    """By 2024 the cultural center has liberalized to slightly progressive
    (ANES/GSS ≈ −0.05), emergently via cohort turnover."""
    c = canonical_snaps[2024]["cult_center"]
    assert -0.11 <= c <= 0.02, f"2024 cultural center {c:+.3f} off the empirical endpoint"


def test_republican_wrong_quadrant_bounded(canonical_snaps):
    """The Republican progressive-redistributive (lower-left) tail at 2000 must be
    bounded — the screenshot bug. Pre-fix ~0.19; fixed ~0.14; ANES ~0.08."""
    assert canonical_snaps[2000]["R_LL"] <= 0.17


def test_sorting_preserved(canonical_snaps):
    """The common-mode channel must not break party separation (rigid cultural
    translation is sorting-invariant): 2024 party_sep stays in the ANES band."""
    assert 1.0 <= canonical_snaps[2024]["party_sep"] <= 1.18
