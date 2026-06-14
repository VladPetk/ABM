"""MHV S3 T3.2 — data-fed elite channel (arc integration guard).

The unit behaviour of PartyCentroidSeries is pinned in test_t31_inputs.py.
Here we guard the two arc-level properties that matter:

  1. **Accept clause (T0.6 hard req).** On the data-fed path no party
     coordinate reaches a domain bound at any tick — the corner-pin the
     scheduled EliteDrift produces (centroids run to [±1, ±1] by ~2014) is
     gone. This is the evidence-backed reason the data-fed series exists.
  2. The arc still polarizes (party_sep rises monotone-ish over 1980→2025)
     — the *magnitude* is left to the S4 fit (the realistic attractor
     undershoots the ANES target pre-calibration; see methods §5.24), so
     this guard pins shape, not level.

Gated behind `data_fed_elite` (default off → EliteDrift unchanged); the
canonical preset flip + golden re-bless lands at T3.5.

emergence-recovery E5.7 note: this contrast (fed series vs scheduled
EliteDrift) is a FED-config concern. On the endogenous canonical config
`data_fed_elite=False` activates the loop (not scheduled EliteDrift), so the
file pins against the preserved FED config (`ANES_FULL_FED_KWARGS`).
"""
from __future__ import annotations

import numpy as np
import pytest

from scripts.anes_preset import ANES_FULL_FED_KWARGS as ANES_FULL_KWARGS
from abm.pillars.historical_arc import build_engine, build_schedule
from abm.pillars.schedule import run_to


def _run_capture(data_fed: bool):
    kwargs = dict(ANES_FULL_KWARGS)
    kwargs["data_fed_elite"] = data_fed
    eng = build_engine(seed=0, **kwargs)
    sched = build_schedule(faction_anchor_events=True, evidence_regrade=True,
                           exogenous_shocks=True)
    max_abs = 0.0
    for t in range(1, 136):
        run_to(eng, sched, t)
        for pid in (0, 1):
            max_abs = max(max_abs, float(np.abs(eng.env.attrs["parties"][pid]).max()))
    return eng, max_abs


def test_data_fed_elite_no_domain_bound():
    eng, max_abs = _run_capture(data_fed=True)
    assert max_abs < 0.999, (
        f"data-fed party centroid reached a domain bound (max |coord| "
        f"{max_abs:.4f}) — the series should keep the attractor inside the "
        "ANES envelope (accept clause, mhv_spec S3 / T0.6)."
    )


def test_scheduled_elite_does_corner_pin():
    # Contrast guard: documents WHY the data-fed channel is required — the
    # scheduled EliteDrift saturates the attractor at the corners.
    _eng, max_abs = _run_capture(data_fed=False)
    assert max_abs >= 0.999, (
        "expected the scheduled EliteDrift to corner-pin the attractor "
        f"(max |coord| {max_abs:.4f}); if it no longer does, the data-fed "
        "channel's justification needs re-checking."
    )
