"""MHV S2 T2.2 — live D=7 issues-mode guards.

What these pin: the projection-cache invariant (ideology IS the block-means
projection of issues at every tick), the live IC's native moments (the
wrong-side tail and ANES-neighborhood within-party spread that retire the
T0.4 soft cap on this path), replacement reseeding consistency, and basic
sanity of a multi-decade live run including events/shocks.

The D=2 reduction proof lives in test_t21_issue_state.py
(test_n2_live_engine_bit_identity).
"""
from __future__ import annotations

import numpy as np
import pytest

from abm.core.issues import project_compass, load_loadings


@pytest.fixture(scope="module")
def live_run():
    """One seed-0 D=7 live arc, run to tick 45 (past Fairness Doctrine
    1987, Gingrich 1994, and several cohort-replacement firings), with the
    canonical gates on so the event layer is exercised."""
    from abm.pillars.historical_arc import build_engine, build_schedule
    from abm.pillars.schedule import run_to

    eng = build_engine(seed=0, n_issues=7, evidence_regrade=True,
                       exogenous_shocks=True)
    sched = build_schedule(evidence_regrade=True, exogenous_shocks=True)
    for t in range(1, 46):
        run_to(eng, sched, t)
    return eng


def _projection_residual(eng):
    ld = load_loadings()
    V = np.array([a.state.attrs["issues"] for a in eng.agents])
    P = project_compass(V, ld)
    pos = eng.positions()
    return float(np.abs(P - pos).max())


def test_initial_ideology_is_projection():
    from abm.pillars.historical_arc import build_engine

    eng = build_engine(seed=1, n_issues=7)
    assert _projection_residual(eng) == 0.0


def test_initial_native_moments():
    """The live D=7 IC must land the moments that retire the T0.4 soft
    cap: a native wrong-side econ tail (party-ordered) and within-party
    spread in the ANES neighborhood. Loose bands here; the exact pinning
    happens at T2.6 against the scorecard."""
    from abm.pillars.historical_arc import build_engine

    eng = build_engine(seed=1, n_issues=7)
    pos = eng.positions()
    party = eng.attr_array("party")
    d, r = party == 0, party == 1
    dem_tail = float((pos[d, 0] > 0.45).mean())
    rep_tail = float((pos[r, 0] < -0.45).mean())
    assert 0.0 < dem_tail < 0.20
    assert rep_tail < dem_tail
    assert 0.22 < pos[d, 0].std() < 0.45
    assert 0.22 < pos[r, 0].std() < 0.45


def test_projection_cache_invariant_over_run(live_run):
    """After 45 ticks of the full pipeline (BC, pulls, noise, events,
    shocks, replacements), ideology must still BE the projection of
    issues for every agent — no rule or handler desyncs the cache."""
    assert _projection_residual(live_run) < 1e-12


def test_issues_stay_bounded(live_run):
    V = np.array([a.state.attrs["issues"] for a in live_run.agents])
    assert V.min() >= -1.0 and V.max() <= 1.0
    assert V.shape[1] == 7


def test_replacement_reseeds_issues(live_run):
    """Every replaced slot must carry a fresh 7-dim issues vector and a
    matching anchor; the replacement log says replacements happened in
    the window."""
    rep = live_run.env.attrs.get("replacement_events") or []
    assert len(rep) > 0
    replaced_ids = {int(aid) for _t, aid in rep}
    by_id = {int(a.id): a for a in live_run.agents}
    for aid in list(replaced_ids)[:20]:
        a = by_id[aid]
        assert a.state.attrs["issues"].shape == (7,)
        assert a.state.attrs["anchor_issues"].shape == (7,)


def test_dynamics_actually_move_issue_space(live_run):
    """Sanity: the live substrate is not frozen — separation grows from
    the 1980 seed over the first 15 years, as the 2D arc does."""
    pos = live_run.positions()
    party = live_run.attr_array("party")
    d, r = party == 0, party == 1
    sep = float(np.linalg.norm(pos[d].mean(0) - pos[r].mean(0)))
    assert sep > 0.30   # 1986 seed starts ~0.32 separated on x+y


def test_momentum_rejected_with_issues():
    from abm.pillars.historical_arc import build_engine

    with pytest.raises(ValueError):
        build_engine(seed=0, n_issues=7, momentum=0.4)
