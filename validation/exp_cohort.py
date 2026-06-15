"""EXPERIMENT (not a committed change): does an empirically-calibrated cohort
cultural gradient correct the mid-period center-of-mass error (battery F0)?

We monkeypatch the cohort spec / replacement rate in-process and re-run the
canonical arc, comparing the partisan cultural center trajectory + Republican
wrong-quadrant tail to ANES. No engine file is modified.

NB the rule NEGATES y_mean when tier_d_cohort_y_signs_fix is on (canonical), so
COHORTS['y_mean'] = -(desired effective entering y). We set EFFECTIVE values via
that negation. Effective targets come from the measured ANES birth-cohort gradient:
  born ~1965 (boomer entrants 80s-90s) ~ +0.03 ; born ~1985 (genx/mil) ~ -0.08 ;
  born ~2002 (late-mil/genz)           ~ -0.25
"""
import sys, json
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from abm.rules import cohort_replacement as CR
from scripts.publish_web_data import run_trajectory

YEARS = [1986, 1992, 1996, 2000, 2004, 2008, 2012, 2016, 2020, 2024]
# ANES partisan cultural center of mass (computed earlier, compass units)
ANES_CULT = {1986: 0.103, 1992: 0.102, 1996: 0.216, 2000: 0.217, 2004: 0.128,
             2008: 0.089, 2012: 0.119, 2016: 0.043, 2020: -0.052, 2024: -0.057}
ANES_R_LL = {1986: 0.118, 1992: 0.091, 2000: 0.082, 2008: 0.109, 2016: 0.053, 2024: 0.084}


def traj_metrics(tr):
    out = {}
    for yr in YEARS:
        t = int(round((yr - 1980) * 3))
        if t >= len(tr["ticks"]):
            continue
        pos = np.array(tr["ticks"][t]["positions"]); party = np.array(tr["ticks"][t]["party"])
        m = (party == 0) | (party == 1)
        R = pos[party == 1]
        out[yr] = {"cult_com": float(pos[m, 1].mean()),
                   "R_LL": float(np.mean((R[:, 0] <= 0) & (R[:, 1] <= 0))) if len(R) else None}
    return out


def set_effective(boomer_y, genx_y, late_y, rate=None):
    """Set EFFECTIVE entering y (rule negates COHORTS['y_mean'])."""
    CR.COHORTS["boomer"]["y_mean"] = -boomer_y
    CR.COHORTS["genx_early_millennial"]["y_mean"] = -genx_y
    CR.COHORTS["late_millennial_genz"]["y_mean"] = -late_y
    if rate is not None:
        CR.COHORT_REPLACEMENT_RATE = rate  # note: rule instance already built w/ old rate


# snapshot originals
import copy
ORIG = copy.deepcopy(CR.COHORTS)

import time
configs = {
    "baseline":            None,   # effective entering y: 0.00 / -0.05 / -0.10 (current)
    "anes_gradient":       (0.03, -0.08, -0.25),
    "anes_gradient_steep": (0.05, -0.12, -0.32),
}
results = {}
for name, cfg in configs.items():
    # restore then apply
    for k in CR.COHORTS:
        CR.COHORTS[k].update(ORIG[k])
    if cfg is not None:
        set_effective(*cfg)
    t0 = time.time()
    tr = run_trajectory(seed=0, capture_agents=True)
    results[name] = traj_metrics(tr)
    print(f"[{name}] ran in {time.time()-t0:.0f}s")

# restore
for k in CR.COHORTS:
    CR.COHORTS[k].update(ORIG[k])

print("\n=== partisan CULTURAL center of mass: configs vs ANES ===")
hdr = f"{'year':>5} {'ANES':>7}" + "".join(f"{n[:10]:>12}" for n in configs)
print(hdr)
for yr in YEARS:
    row = f"{yr:>5} {ANES_CULT[yr]:>7.3f}"
    for n in configs:
        row += f"{results[n][yr]['cult_com']:>12.3f}"
    print(row)

print("\n=== Republican wrong-quadrant (LL) fraction vs ANES ===")
print(f"{'year':>5} {'ANES':>7}" + "".join(f"{n[:10]:>12}" for n in configs))
for yr in sorted(ANES_R_LL):
    row = f"{yr:>5} {ANES_R_LL[yr]:>7.3f}"
    for n in configs:
        row += f"{results[n][yr]['R_LL']:>12.3f}"
    print(row)

# F0 mid-period score (1994-2004 cult error vs ANES)
print("\n=== mid-period (1996-2004) mean cultural error vs ANES (closer to 0 = better) ===")
for n in configs:
    err = np.mean([results[n][yr]['cult_com'] - ANES_CULT[yr] for yr in (1996, 2000, 2004)])
    print(f"  {n:20} {err:+.3f}")

Path(__file__).resolve().parent.joinpath("exp_cohort_results.json").write_text(
    json.dumps(results, indent=2))
