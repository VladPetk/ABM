"""Phase 9 §11.7-C probe — test whether bigger σ_noise + softer BC
breaks the wp_sd ceiling. Quick 3-cell scan at n=4 seeds.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

import numpy as np

DECADE_TICKS = [(1980, 0), (1990, 30), (2000, 60), (2010, 90), (2020, 120)]
SECTION11_TICKS = [(1990, 30), (2000, 60), (2010, 90), (2020, 120), (2025, 135)]


def _worker(args):
    seed, sigma = args
    from abm.pillars.historical_arc import build_engine, build_schedule
    from abm.pillars.schedule import run_to
    from scripts.phase8f_lib import measure_all
    eng = build_engine(
        seed=seed, n_agents=250, independent_fraction=0.12,
        factional_seeding=False, faction_anchor_strength=0.04,
        faction_anchor_events=True, event_stubbornness_bump_multiplier=1.0,
        tier_d_axis_balance=True, tier_d_lever1_off=True,
        tier_d_cohort_y_signs_fix=True, tier_d_anes_knobs=True,
        tier_d_anes_drift_multiplier=3.0, tier_d_anes_sigma_pc_multiplier=1.6,
        tier_c_identity_pull_x=0.015, tier_c_identity_pull_y=0.040,
        tier_d_aniso_noise_sigma_x=sigma, tier_d_aniso_noise_sigma_y=sigma,
        tier_c_party_pull_strength=0.04, tier_c_bc_strength=0.015,
    )
    sched = build_schedule(factional_seeding=False, faction_anchor_events=True)
    trajectory = {1980: measure_all(eng)}
    yat = {}
    for y, t in SECTION11_TICKS:
        yat.setdefault(t, []).append(y)
    for t in sorted(yat):
        if t == 0:
            continue
        run_to(eng, sched, t)
        for y in yat[t]:
            trajectory[y] = measure_all(eng)
    return trajectory


def main():
    from abm.calibration_parallel import run_seeds_parallel
    from scripts.phase8f_lib import (
        get_primary_targets, get_initial_targets_1980, aggregate, in_band,
    )
    sigmas = [0.025, 0.05, 0.08, 0.12]
    print(f"noise probe — bc=0.015 pp=0.04, varying σ_noise (x=y), n=4 seeds/cell")
    for sigma in sigmas:
        work = [(s, sigma) for s in range(4)]
        results = run_seeds_parallel(_worker, work)
        means, _ = aggregate(results)
        anes_pri = get_primary_targets(use_anes_bands=True)
        anes_init = get_initial_targets_1980(use_anes_bands=True)
        n4 = sum(
            in_band(means[y][m], anes_pri[y][m])
            for y in [1990, 2000, 2010, 2020, 2025]
            for m in ["constraint", "party_sep", "affect", "within_party_sd"]
        )
        ni = sum(
            in_band(means[1980][m], anes_init[m])
            for m in ["variance", "constraint", "party_sep", "within_party_sd"]
        )
        print(f"  σ={sigma:.3f}:  §11_ANES={n4+ni}/24  "
              f"1980 wp_sd={means[1980]['within_party_sd']:.3f}  "
              f"2020 sep={means[2020]['party_sep']:.3f}  "
              f"2020 wp_sd={means[2020]['within_party_sd']:.3f}")


if __name__ == "__main__":
    main()
