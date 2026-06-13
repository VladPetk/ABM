"""E2 integration guard — the endogenous activist-elite loop on the shipped arc.

Builds the historical arc with `endogenous_elite=True` (the loop replaces the fed
`PartyCentroidSeries`) and checks that positional sorting EMERGES to a realistic,
stable magnitude with nothing positional fed. The 1980→2025 *trajectory shape*
(too fast without time-structured shocks) is an E3/E4 concern, not pinned here —
this guard pins that the loop reaches a realistic, stable endpoint.
"""
from __future__ import annotations

import numpy as np

from abm.pillars.historical_arc import build_engine
from scripts.anes_preset import ANES_FULL_KWARGS


def _sep_live(eng):
    pos = eng.positions()
    party = np.array([a.state.attrs.get("party") for a in eng.agents])
    m0, m1 = pos[party == 0].mean(0), pos[party == 1].mean(0)
    wp = float(np.mean([pos[party == p].std(0).mean() for p in (0, 1)]))
    corner = float(np.mean(np.any(np.abs(pos) > 0.9, axis=1)))
    return float(np.linalg.norm(m0 - m1)), wp, corner


def test_endogenous_arc_emerges_realistic_and_stable():
    kw = dict(ANES_FULL_KWARGS)
    kw.update(endogenous_elite=True, data_fed_elite=False)
    eng = build_engine(seed=0, **kw)
    traj = []
    sep0 = _sep_live(eng)[0]
    for t in range(136):
        traj.append(_sep_live(eng))
        if t < 135:
            eng.step()
    sep_final, wp_final, corner_final = traj[-1]
    stability = float(np.std([x[0] for x in traj[-20:]]))

    # emergent: starts at the small 1980 seed, amplifies to a realistic endpoint
    assert sep0 < 0.40, f"1980 seed should be small; got {sep0:.3f}"
    assert 0.85 <= sep_final <= 1.30, f"emergent endpoint out of ANES window: {sep_final:.3f}"
    assert sep_final > sep0 + 0.5, f"loop should amplify the seed; {sep0:.3f}->{sep_final:.3f}"
    # realistic + stable, nothing fed
    assert 0.25 <= wp_final <= 0.45, f"within-party SD out of band: {wp_final:.3f}"
    assert corner_final < 0.10, f"corner runaway: {corner_final:.2%}"
    assert stability < 0.05, f"endpoint not stable (SD last 20 = {stability:.3f})"
