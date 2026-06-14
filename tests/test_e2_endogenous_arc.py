"""E2/E3 integration guard — the endogenous activist-elite loop on the shipped arc.

E2 wired `ActivistEliteCue` into the historical arc (replacing the fed
`PartyCentroidSeries`); E3 added the time-structure — the dated elite events ramp
a per-party `activist_mobilization` that scales the elite leapfrog, and newcomers
sort via the loop instead of teleporting to the centroid.

This guard runs the arc **with the schedule firing** (events ON) and checks that
positional sorting (a) EMERGES from the 1980 seed with nothing positional fed,
(b) is no longer an instant jump — the rise is SPREAD across the arc by the
mobilization ramp (the E2-without-time-structure loop completed >100% of its rise
by 1990; here it must be much less), and (c) lands at a realistic, stable
magnitude. The PRECISE ANES shape match (frac-by-1990 ≈ 25%, the late
acceleration, the exact endpoint) is the E4 joint calibration of the mobilization
schedule + uptake + gain — NOT asserted here.
"""
from __future__ import annotations

import numpy as np

from abm.pillars.historical_arc import build_engine, build_schedule
from abm.pillars.schedule import run_to
from scripts.anes_preset import ANES_FULL_KWARGS

DECADES = [(1980, 0), (1990, 30), (2000, 60), (2010, 90), (2020, 120), (2025, 135)]


def _sep_live(eng):
    pos = eng.positions()
    party = np.array([a.state.attrs.get("party") for a in eng.agents])
    m0, m1 = pos[party == 0].mean(0), pos[party == 1].mean(0)
    wp = float(np.mean([pos[party == p].std(0).mean() for p in (0, 1)]))
    corner = float(np.mean(np.any(np.abs(pos) > 0.9, axis=1)))
    return float(np.linalg.norm(m0 - m1)), wp, corner


def _run_endogenous_with_events(seed=0):
    kw = dict(ANES_FULL_KWARGS)
    kw.update(endogenous_elite=True, data_fed_elite=False)
    eng = build_engine(seed=seed, **kw)
    sched = build_schedule(
        factional_seeding=kw.get("factional_seeding", False),
        faction_anchor_events=kw.get("faction_anchor_events", False),
        evidence_regrade=kw.get("evidence_regrade", False),
        exogenous_shocks=kw.get("exogenous_shocks", False),
    )
    traj = []
    decade_sep = {}
    want = {t: yr for yr, t in DECADES}
    for t in range(136):
        traj.append(_sep_live(eng))
        if t in want:
            decade_sep[want[t]] = traj[-1][0]
        if t < 135:
            run_to(eng, sched, t + 1)
    return traj, decade_sep


def test_endogenous_arc_emergent_and_time_structured():
    traj, dec = _run_endogenous_with_events()
    sep0 = traj[0][0]
    sep_final, wp_final, corner_final = traj[-1]
    stability = float(np.std([x[0] for x in traj[-20:]]))
    rise = dec[2025] - dec[1980]
    frac90 = (dec[1990] - dec[1980]) / rise
    frac_late = (dec[2025] - dec[2010]) / rise

    # (a) emergent: small 1980 seed amplified, nothing positional fed
    assert sep0 < 0.40, f"1980 seed should be small; got {sep0:.3f}"
    assert sep_final > sep0 + 0.4, f"loop should amplify the seed; {sep0:.3f}->{sep_final:.3f}"
    # (b) time-structured: the rise is SPREAD, not the >100%-by-1990 instant jump
    #     of the no-time-structure loop (E2). Generous bar — E4 tightens toward ~25%.
    assert frac90 < 0.90, f"rise still front-loads like the no-time-structure jump: frac90={frac90:.0%}"
    assert frac_late > 0.05, f"no late rise — mobilization ramp not biting: frac_late={frac_late:.0%}"
    # (c) realistic + stable magnitude (uncalibrated range; E4 fits to ANES)
    assert 0.70 <= sep_final <= 1.25, f"endpoint out of plausible range: {sep_final:.3f}"
    assert 0.22 <= wp_final <= 0.45, f"within-party SD out of band: {wp_final:.3f}"
    assert corner_final < 0.10, f"corner runaway: {corner_final:.2%}"
    assert stability < 0.05, f"endpoint not stable (SD last 20 = {stability:.3f})"
