"""Phase 8f diagnostic runner.
PYTHONPATH=. python scripts/phase8f_diagnostic_runner.py <variant>
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

import numpy as np

from abm.calibration_parallel import run_seeds_parallel
from abm.pillars import historical_arc as ha

from scripts.phase8f_lib import (
    apply_overrides, patch_schedules, restore_schedules,
    measure_all, aggregate, print_trajectory,
)
from scripts.phase8f_variants import VARIANTS


SEEDS = tuple(range(int(os.environ.get("PHASE8F_NSEEDS", "5"))))
N = 250
INDEPENDENT_FRACTION = 0.12


def _trajectory_worker(seed: int) -> dict:
    variant = os.environ.get("PHASE8F_VARIANT", "baseline")
    overrides = VARIANTS.get(variant, [])
    saved = patch_schedules(overrides)
    try:
        ind_frac = INDEPENDENT_FRACTION
        for ov in overrides:
            if ov[0] == "build_kwarg" and ov[1] == "independent_fraction":
                ind_frac = ov[2]
        eng = ha.build_engine(
            seed=seed, n_agents=N, independent_fraction=ind_frac,
        )
        apply_overrides(eng, overrides)
        sched = ha.build_schedule()
        trajectory = {1980: measure_all(eng)}
        from abm.pillars.schedule import run_to
        for year, tick in [(1990, 30), (2000, 60), (2010, 90),
                            (2020, 120), (2025, 135)]:
            run_to(eng, sched, tick)
            trajectory[year] = measure_all(eng)
    finally:
        restore_schedules(saved)
    return trajectory


def main():
    variant = sys.argv[1] if len(sys.argv) > 1 else "baseline"
    if variant not in VARIANTS:
        print(f"Unknown variant '{variant}'.")
        print(f"Available: {sorted(VARIANTS.keys())}")
        sys.exit(1)
    os.environ["PHASE8F_VARIANT"] = variant
    print(f"Phase 8f: variant={variant} seeds={len(SEEDS)} N={N}")
    trajectories = run_seeds_parallel(_trajectory_worker, SEEDS)
    means, ses = aggregate(trajectories)
    print_trajectory(variant, means)
    out = Path(f"phase8f_diag_{variant}.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump({
            "variant": variant, "seeds": list(SEEDS),
            "means": {str(y): means[y] for y in means},
            "ses": {str(y): ses[y] for y in ses},
        }, f, indent=2)
    print(f"[dump] {out.resolve()}")


if __name__ == "__main__":
    main()
