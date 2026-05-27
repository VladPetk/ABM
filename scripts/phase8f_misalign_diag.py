"""Diagnose: at 2025, what fraction of partisans are sign-misaligned."""
from __future__ import annotations

import os
import sys

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import numpy as np
from abm.calibration_parallel import run_seeds_parallel
from abm.pillars import historical_arc as ha
from abm.pillars.schedule import run_to
from abm.metrics.affective import ideological_constraint
from scripts.phase8f_lib import (
    apply_overrides, patch_schedules, restore_schedules, measure_all,
)
from scripts.phase8f_variants import VARIANTS

SEEDS = tuple(range(5))
N = 250
IF = 0.12


def _w(seed):
    variant = os.environ.get("PHASE8F_VARIANT", "baseline")
    overrides = VARIANTS.get(variant, [])
    saved = patch_schedules(overrides)
    try:
        ind_frac = IF
        for ov in overrides:
            if ov[0] == "build_kwarg" and ov[1] == "independent_fraction":
                ind_frac = ov[2]
        eng = ha.build_engine(seed=seed, n_agents=N, independent_fraction=ind_frac)
        apply_overrides(eng, overrides)
        sched = ha.build_schedule()
        snaps = {}
        for year, tick in [(1980, 0), (2010, 90), (2025, 135)]:
            if tick > 0:
                run_to(eng, sched, tick)
            pos = eng.positions()
            parties = np.array([a.state.attrs["party"] for a in eng.agents])
            stubbornness = np.array([a.state.attrs.get("stubbornness", 0.0)
                                      for a in eng.agents])
            mis = ((parties == 0) & (pos[:, 0] > 0)) | (
                (parties == 1) & (pos[:, 0] < 0))
            partisans = (parties == 0) | (parties == 1)
            cen = {p: pos[parties == p].mean(axis=0)
                   for p in (0, 1) if (parties == p).any()}
            wp_sd_y = []
            for p in (0, 1):
                m = parties == p
                if m.sum() > 1:
                    wp_sd_y.append(float(pos[m, 1].std()))
            ic = ideological_constraint(eng.agents)
            snaps[year] = {
                "mis_frac": float(mis.sum() / max(1, partisans.sum())),
                "cent0": cen.get(0).tolist() if 0 in cen else None,
                "cent1": cen.get(1).tolist() if 1 in cen else None,
                "wp_sd_y": float(np.mean(wp_sd_y)) if wp_sd_y else 0.0,
                "cx": ic["x"],
                "cy": ic["y"],
                "metrics": measure_all(eng),
            }
        return snaps
    finally:
        restore_schedules(saved)


def main():
    variant = sys.argv[1] if len(sys.argv) > 1 else "baseline"
    os.environ["PHASE8F_VARIANT"] = variant
    print("misalign diag variant=" + variant)
    snaps = run_seeds_parallel(_w, SEEDS)
    for year in [1980, 2010, 2025]:
        mf = np.mean([s[year]["mis_frac"] for s in snaps])
        c0x = np.mean([s[year]["cent0"][0] for s in snaps])
        c1x = np.mean([s[year]["cent1"][0] for s in snaps])
        c0y = np.mean([s[year]["cent0"][1] for s in snaps])
        c1y = np.mean([s[year]["cent1"][1] for s in snaps])
        cx = np.mean([s[year]["cx"] for s in snaps])
        cy = np.mean([s[year]["cy"] for s in snaps])
        wsdy = np.mean([s[year]["wp_sd_y"] for s in snaps])
        m = snaps[0][year]["metrics"]
        cma = np.mean([s[year]["metrics"]["constraint"] for s in snaps])
        psep = np.mean([s[year]["metrics"]["party_sep"] for s in snaps])
        wsd = np.mean([s[year]["metrics"]["within_party_sd"] for s in snaps])
        print(f" {year}: mis={mf:.3f} "
              f"c0=({c0x:+.3f},{c0y:+.3f}) c1=({c1x:+.3f},{c1y:+.3f}) "
              f"cx={cx:.3f} cy={cy:.3f} cavg={cma:.3f} "
              f"psep={psep:.3f} wp_sd_x={wsd:.3f} wp_sd_y={wsdy:.3f}")


if __name__ == "__main__":
    main()
