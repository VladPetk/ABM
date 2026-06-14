"""E5.0 smoke — confirm ANES_FULL_ENDOGENOUS_KWARGS builds + traces ANES.

Builds the endogenous canonical preset directly (NOT via e4_fit._overrides) and
runs the arc with the standard schedule, printing sep/affect/wp_sd at the §11
decade ticks vs the ANES bands. Should reproduce the adopted E4 best trajectory.
"""
from __future__ import annotations

import sys

from abm.pillars.historical_arc import build_engine, build_schedule
from abm.pillars.schedule import run_to
from scripts.anes_preset import ANES_FULL_ENDOGENOUS_KWARGS
from scripts.phase8f_lib import measure_all
from scripts.phase9_anes_score import SECTION11_TICKS

SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 0
ANES = {1980: 0.40, 1990: 0.50, 2000: 0.67, 2010: 0.86, 2020: 1.11, 2025: 1.11}

ov = dict(ANES_FULL_ENDOGENOUS_KWARGS)
eng = build_engine(seed=SEED, **ov)
sched = build_schedule(
    factional_seeding=ov.get("factional_seeding", False),
    faction_anchor_events=ov.get("faction_anchor_events", True),
    evidence_regrade=ov.get("evidence_regrade", False),
    exogenous_shocks=ov.get("exogenous_shocks", False),
)
print(f"seed {SEED}  endogenous_elite={ov['endogenous_elite']} "
      f"data_fed_elite={ov['data_fed_elite']}")
print(f"  {'dec':>5} {'sep':>6} {'ANES':>6} {'affect':>7} {'wp_sd':>6} {'xcorr':>6}")
for year, tick in SECTION11_TICKS:
    if tick > 0:
        run_to(eng, sched, tick)
    m = measure_all(eng)
    xc = m.get("axis_correlation", float("nan"))
    print(f"  {year:>5} {m['party_sep']:>6.2f} {ANES[year]:>6.2f} "
          f"{m['affect']:>7.2f} {m['within_party_sd']:>6.2f} {xc:>6.2f}")
