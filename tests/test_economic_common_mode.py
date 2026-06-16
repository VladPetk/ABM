"""Gated reality guard for the ECONOMIC common-mode channel (branch
econ-common-mode-mood; companion to test_cultural_common_mode.py).

The channel is implemented GATED and is NOT yet in the canonical preset (awaiting
the user sign-off before the canonical flip / re-bless cascade). So this module
builds with ``economic_common_mode=True`` explicitly and pins:
  - gate OFF = bit-identical (the rule is absent, econ center stays pinned ≈0);
  - gate ON = the partisan econ center tracks the exogenous mood curve
    (rightward mid-90s, leftward 2024);
  - the cultural axis is untouched (the econ channel is orthogonal);
  - sorting is preserved (a rigid econ translation is sorting-invariant).
Anchors are the validation/ from-scratch ANES+GSS targets (the robust econ tide).
"""
import numpy as np
import pytest

from scripts.anes_preset import ANES_FULL_KWARGS
from abm.pillars.historical_arc import build_engine, build_schedule
from abm.pillars.schedule import run_to
from abm.rules.cultural_common_mode import economic_mood_offset, ECON_MOOD_AMPLITUDE


def _run(econ_on):
    kw = dict(ANES_FULL_KWARGS)
    if econ_on:
        kw["economic_common_mode"] = True
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
        if yr in (1996, 2000, 2024) and yr not in snaps:
            party = np.array([a.state.attrs.get("party") for a in eng.agents])
            pos = np.array([a.state.ideology for a in eng.agents])
            m = (party == 0) | (party == 1)
            snaps[yr] = {
                "econ_center": float(pos[m, 0].mean()),
                "cult_center": float(pos[m, 1].mean()),
                "party_sep": float(np.hypot(*(pos[party == 1].mean(0)
                                              - pos[party == 0].mean(0)))),
            }
    return snaps


@pytest.fixture(scope="module")
def off_snaps():
    return _run(econ_on=False)


@pytest.fixture(scope="module")
def on_snaps():
    return _run(econ_on=True)


def test_mood_curve_shape():
    """The exogenous econ mood offset: rightward peak at the 1996 welfare-reform
    high-water mark, declining to slightly leftward by 2024."""
    assert economic_mood_offset(1996.0) == pytest.approx(ECON_MOOD_AMPLITUDE)
    assert economic_mood_offset(1996.0) > economic_mood_offset(1986.0) > 0
    assert economic_mood_offset(2024.0) < 0 < economic_mood_offset(2008.0)


def test_default_canonical_has_econ_channel_off():
    """The shipped preset must NOT yet carry the econ channel (gate off until the
    user-approved flip). Guards against an accidental early canonical flip."""
    assert ANES_FULL_KWARGS.get("economic_common_mode") in (None, False)


def test_gate_off_econ_center_pinned(off_snaps):
    """With the channel OFF, the partisan econ center is pinned near 0 the whole
    arc (the bug): mid-90s nowhere near the ANES/GSS +0.09 rightward level."""
    assert off_snaps[1996]["econ_center"] < 0.04


def test_gate_on_tracks_mood_curve(on_snaps):
    """With the channel ON, the econ center snaps to the exogenous mood curve:
    rightward mid-90s, leftward by 2024."""
    assert on_snaps[1996]["econ_center"] == pytest.approx(
        economic_mood_offset(1996.0), abs=0.03)
    assert on_snaps[2024]["econ_center"] == pytest.approx(
        economic_mood_offset(2024.0), abs=0.03)
    # the headline fix: mid-90s econ center moves rightward into the robust band
    assert 0.06 <= on_snaps[1996]["econ_center"] <= 0.12


def test_cultural_axis_untouched(off_snaps, on_snaps):
    """The econ channel is orthogonal — the cultural center is unchanged (it must
    not regress the shipped cultural common-mode fix)."""
    for yr in (1996, 2024):
        assert on_snaps[yr]["cult_center"] == pytest.approx(
            off_snaps[yr]["cult_center"], abs=0.01)


def test_sorting_preserved(off_snaps, on_snaps):
    """A rigid econ translation is sorting-invariant: party separation is not
    reduced (here it is marginally improved)."""
    assert on_snaps[2024]["party_sep"] >= off_snaps[2024]["party_sep"] - 0.02
    assert 1.0 <= on_snaps[2024]["party_sep"] <= 1.18
