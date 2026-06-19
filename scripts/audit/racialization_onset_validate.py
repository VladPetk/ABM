"""Validate + calibrate the racialization ONSET engine build (spec §10 re-scope).

(0) BIT-IDENTICAL when off: racialization_kick=True with rac_peak=0 & no mob-freeze
    must reproduce the canonical trajectory exactly (the plumbing is inert at zero).
(1) CALIBRATE rac_peak on the real ADD-based build (racialization adds on top of the
    baseline tier_c_identity_pull_y=0.04, unlike the probe which replaced it), with
    rac_freeze_mob=True and NO decay (the onset = ramp-and-hold). Find the peak that
    lands cultural-axis 2024 ≈ ANES (indexed to 2008). Report per axis.
"""
from __future__ import annotations

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
ANES_YEARS = [1986, 2000, 2008, 2016, 2020, 2024]
YEAR_TICKS = {y: (y - 1980) * 3 for y in ANES_YEARS}
SNAP = sorted(YEAR_TICKS.values())
ANES = {1986: (0.3209, 0.1216, 0.9572), 2000: (0.3879, 0.2840, 1.3917),
        2008: (0.5840, 0.4011, 1.8980), 2016: (0.7018, 0.6294, 2.6083),
        2020: (0.8382, 0.7832, 3.1986), 2024: (0.7599, 0.7335, 2.9308)}
PEAKS = [0.15, 0.18, 0.21]


def _axes(eng):
    parties = np.array([a.state.attrs["party"] for a in eng.agents])
    pos = eng.positions()
    if (parties == 0).sum() == 0 or (parties == 1).sum() == 0:
        return 0.0, 0.0, 0.0
    diff = pos[parties == 0].mean(0) - pos[parties == 1].mean(0)
    return abs(float(diff[0])), abs(float(diff[1])), float(np.linalg.norm(diff))


def _run(seed, **extra):
    eng = build_engine(seed=seed, **ANES_FULL_KWARGS, **extra)
    sched = _make_schedule("full")
    snaps = {}
    for t in range(1, END_TICK + 1):
        run_to(eng, sched, t)
        if t in SNAP:
            snaps[t] = _axes(eng)
    return snaps


def _worker(arg):
    label, seed = arg
    if label == "canonical":
        return {"label": label, "seed": seed, "snaps": _run(seed)}
    if label == "off_inert":
        return {"label": label, "seed": seed,
                "snaps": _run(seed, racialization_kick=True, rac_peak=0.0,
                              rac_freeze_mob=False)}
    peak = float(label.split("_p")[1])
    return {"label": label, "seed": seed,
            "snaps": _run(seed, racialization_kick=True, rac_peak=peak,
                          rac_freeze_mob=True, rac_decay_frac=None)}


def main():
    from abm.calibration_parallel import run_seeds_parallel
    labels = ["canonical", "off_inert"] + [f"onset_p{p}" for p in PEAKS]
    res = run_seeds_parallel(_worker, [(l, s) for l in labels for s in SEEDS])
    by = {}
    for r in res:
        by.setdefault(r["label"], {})[r["seed"]] = r["snaps"]

    # (0) bit-identical when off
    print("Racialization ONSET — validate + calibrate, 5 seeds")
    print("=" * 70)
    maxdiff = 0.0
    for s in SEEDS:
        for t in SNAP:
            for i in range(3):
                maxdiff = max(maxdiff, abs(by["canonical"][s][t][i] - by["off_inert"][s][t][i]))
    print(f"\n[0] BIT-IDENTICAL when off (rac_peak=0, no freeze): max |Δ| over all "
          f"seeds/ticks/axes = {maxdiff:.2e}")
    print("    -> must be ~0 (≈1e-12). Confirms the opt-in does not regress the "
          "shipped model.")

    # (1) calibration per axis, indexed to 2008
    def avg(label, tick, i):
        return float(np.mean([by[label][s][tick][i] for s in SEEDS]))
    axes = ["econ", "cult", "comb"]
    t08 = YEAR_TICKS[2008]
    anes_idx = {ax: {y: ANES[y][i] / ANES[2008][i] for y in ANES_YEARS}
                for i, ax in enumerate(axes)}
    for i, ax in enumerate(axes):
        print(f"\n[1-{ax}] indexed 2008=1.0 (ANES target in first row):")
        print(f"    {'cond':<14}" + "".join(f"{('y'+str(y)):>9}" for y in ANES_YEARS) + f"{'RMSE':>9}")
        print(f"    {'ANES':<14}" + "".join(f"{anes_idx[ax][y]:>9.3f}" for y in ANES_YEARS))
        for label in ["canonical"] + [f"onset_p{p}" for p in PEAKS]:
            base = avg(label, t08, i)
            row = [avg(label, YEAR_TICKS[y], i) / base for y in ANES_YEARS]
            rmse = float(np.sqrt(np.mean([(row[k] - anes_idx[ax][ANES_YEARS[k]]) ** 2
                                          for k in range(len(ANES_YEARS))])))
            print(f"    {label:<14}" + "".join(f"{v:>9.3f}" for v in row) + f"{rmse:>9.4f}")
    print("\nPick rac_peak whose cultural 2024 ≈ ANES 1.83 (indexed); set as the "
          "build default. econ under-fit is the disclosed Fork-A caveat.")


if __name__ == "__main__":
    main()
