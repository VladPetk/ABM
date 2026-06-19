"""Final fit data for graphing: the adopted racialization ONSET build
(racialization_kick=True, rac_peak=0.18) vs canonical vs ANES, per axis +
combined, sampled at the 14 ANES survey-year ticks, indexed to 2008=1.0.

Writes docs/internal/racialization_final_fit_data.json.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

import numpy as np

from abm.pillars.historical_arc import build_engine
from abm.pillars.schedule import run_to
from scripts.anes_preset import ANES_FULL_KWARGS
from scripts.audit.audit_lib import _make_schedule, END_TICK

SEEDS = (0, 1, 2, 3, 4)
ANES_YEARS = [1986, 1988, 1990, 1992, 1994, 1996, 1998, 2000,
              2004, 2008, 2012, 2016, 2020, 2024]
YEAR_TICKS = {y: (y - 1980) * 3 for y in ANES_YEARS}
SNAP = sorted(YEAR_TICKS.values())
ANES = {
    1986: (0.3209, 0.1216, 0.9572), 1988: (0.3756, 0.2037, 1.2086),
    1990: (0.3256, 0.1734, 1.0223), 1992: (0.4075, 0.2950, 1.4155),
    1994: (0.4037, 0.3152, 1.4363), 1996: (0.4449, 0.3069, 1.5857),
    1998: (0.3743, 0.3202, 1.3581), 2000: (0.3879, 0.2840, 1.3917),
    2004: (0.5241, 0.4416, 1.8978), 2008: (0.5840, 0.4011, 1.8980),
    2012: (0.6206, 0.5186, 2.3419), 2016: (0.7018, 0.6294, 2.6083),
    2020: (0.8382, 0.7832, 3.1986), 2024: (0.7599, 0.7335, 2.9308),
}
CONDS = ["canonical", "onset"]


def _axes(eng):
    parties = np.array([a.state.attrs["party"] for a in eng.agents])
    pos = eng.positions()
    if (parties == 0).sum() == 0 or (parties == 1).sum() == 0:
        return 0.0, 0.0, 0.0
    diff = pos[parties == 0].mean(0) - pos[parties == 1].mean(0)
    return abs(float(diff[0])), abs(float(diff[1])), float(np.linalg.norm(diff))


def _worker(arg):
    cond, seed = arg
    extra = {} if cond == "canonical" else dict(
        racialization_kick=True, rac_peak=0.18, rac_freeze_mob=True, rac_decay_frac=None)
    eng = build_engine(seed=seed, **ANES_FULL_KWARGS, **extra)
    sched = _make_schedule("full")
    snaps = {}
    for t in range(1, END_TICK + 1):
        run_to(eng, sched, t)
        if t in SNAP:
            snaps[t] = _axes(eng)
    return {"cond": cond, "seed": seed, "snaps": snaps}


def main():
    from abm.calibration_parallel import run_seeds_parallel
    res = run_seeds_parallel(_worker, [(c, s) for c in CONDS for s in SEEDS])
    by = {}
    for r in res:
        by.setdefault(r["cond"], {})[r["seed"]] = r["snaps"]

    def avg(cond, tick, i):
        return float(np.mean([by[cond][s][tick][i] for s in SEEDS]))

    axes = ["econ", "cult", "comb"]
    t08 = YEAR_TICKS[2008]
    series = {}
    for i, ax in enumerate(axes):
        series[ax] = {}
        for cond in CONDS:
            base = avg(cond, t08, i)
            series[ax][cond] = [round(avg(cond, YEAR_TICKS[y], i) / base, 3) for y in ANES_YEARS]
        a08 = ANES[2008][i]
        series[ax]["ANES"] = [round(ANES[y][i] / a08, 3) for y in ANES_YEARS]

    out = {"years": ANES_YEARS, "series": series}
    (_ROOT / "docs" / "internal" / "racialization_final_fit_data.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8")
    for ax in axes:
        print(f"\n[{ax}] indexed 2008=1.0")
        print("    year :", "  ".join(str(y) for y in ANES_YEARS))
        for cond in ["ANES", "canonical", "onset"]:
            print(f"    {cond:<10}", series[ax][cond])
    print("\nwrote docs/internal/racialization_final_fit_data.json")


if __name__ == "__main__":
    main()
