"""Realism-battery pinned sanity guards (realism-check spec, Tier C).

The realism battery itself is a measure-then-bless REPORT (not a CI gate, spec
AGREE #4). Only these three cheap, high-value face checks are pinned as pytests:

  C1  per-tick-label discipline — reproduces the false-undershoot bug: agents
      realign party over the arc, so party_sep MUST be measured with live
      per-tick labels; frozen tick-0 labels understate it.
  C2  projection parity — the shipped 2D compass (a.state.ideology) IS the
      block-mean projection of the calibrated 7D issue substrate, every agent.
  C3  no corner-pin — the de-artifacted cloud keeps <5% of agents at the
      boundary at 2025.

One arc run (seed 0, canonical config) backs all three.
"""
from __future__ import annotations

import numpy as np
import pytest

from abm.core.issues import project1
from abm.pillars.historical_arc import build_engine, build_schedule
from abm.pillars.schedule import run_to
from scripts.anes_preset import ANES_FULL_KWARGS


@pytest.fixture(scope="module")
def arc():
    k = dict(ANES_FULL_KWARGS)
    eng = build_engine(seed=0, **k)
    sched = build_schedule(
        factional_seeding=k.get("factional_seeding", False),
        faction_anchor_events=k.get("faction_anchor_events", True),
        evidence_regrade=k.get("evidence_regrade", False),
        exogenous_shocks=k.get("exogenous_shocks", False),
    )
    init_party = np.array([a.state.attrs["party"] for a in eng.agents], int)
    run_to(eng, sched, 135)
    return eng, init_party


def _sep(pos, party):
    d, r = party == 0, party == 1
    if d.sum() == 0 or r.sum() == 0:
        return 0.0
    return float(np.linalg.norm(pos[d].mean(0) - pos[r].mean(0)))


def test_C1_per_tick_label_discipline(arc):
    """Agents realign; party_sep must use live labels (the tick-0 bug)."""
    eng, init_party = arc
    pos = eng.positions()
    live = np.array([a.state.attrs["party"] for a in eng.agents], int)
    realigned = float((live != init_party).mean())
    assert realigned > 0.05, f"expected party realignment; only {realigned:.1%}"
    sep_live = _sep(pos, live)
    sep_frozen = _sep(pos, init_party)
    # the calibrated separation, measured correctly
    assert sep_live >= 1.0, f"live-label 2025 sep too low: {sep_live:.3f}"
    # frozen tick-0 labels fabricate an undershoot (mislabel every switcher)
    assert sep_frozen < sep_live, (
        f"frozen-label sep {sep_frozen:.3f} should UNDERstate live {sep_live:.3f}")


def test_C2_projection_parity(arc):
    """ideology == project1(issues) for every agent — the shipped picture is
    the calibrated substrate, not a drifting secondary field."""
    eng, _ = arc
    rt = eng.env.attrs["issue_runtime"]
    for a in eng.agents:
        proj = project1(np.asarray(a.state.attrs["issues"], float), rt)
        assert np.allclose(proj, a.state.ideology, atol=1e-9), (
            f"agent {a.id}: project1(issues)={proj} != ideology={a.state.ideology}")


def test_C3_no_corner_pin(arc):
    """De-artifacted cloud keeps the boundary nearly empty at 2025."""
    eng, _ = arc
    pos = eng.positions()
    frac = float((np.abs(pos).max(axis=1) > 0.9).mean())
    assert frac < 0.05, f"corner occupancy {frac:.1%} >= 5% (corner-pin?)"
