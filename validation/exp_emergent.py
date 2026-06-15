"""Validate the COMMITTED gated feature (emergent common-mode culture) vs ANES.

Builds with cultural_common_mode=True at several turnover rates; m(t) emerges
from agent birth-years (no fed answer). Measures center, sorting, and the
Republican wrong-quadrant tail against ANES. Picks the turnover rate.
"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.anes_preset import ANES_FULL_KWARGS
from abm.pillars.historical_arc import build_engine, build_schedule
from abm.pillars.schedule import run_to

YEARS = [1986, 1992, 1996, 2000, 2004, 2008, 2012, 2016, 2020, 2024]
ANES_CULT = {1986: 0.103, 1992: 0.102, 1996: 0.216, 2000: 0.217, 2004: 0.128,
             2008: 0.089, 2012: 0.119, 2016: 0.043, 2020: -0.052, 2024: -0.057}
ANES_R_LL = {1986: 0.118, 1992: 0.091, 2000: 0.082, 2008: 0.109, 2016: 0.053, 2024: 0.084}


def run(common_mode, rate=None):
    kw = dict(ANES_FULL_KWARGS)
    if common_mode:
        kw["cultural_common_mode"] = True
        if rate is not None:
            kw["cohort_replacement_rate"] = rate
    eng = build_engine(seed=0, **kw)
    sched = build_schedule(
        factional_seeding=kw.get("factional_seeding", False),
        faction_anchor_events=kw.get("faction_anchor_events", True),
        evidence_regrade=kw.get("evidence_regrade", False),
        exogenous_shocks=kw.get("exogenous_shocks", False))
    rec = {}
    for t in range(1, 136):
        run_to(eng, sched, t)
        yr = int(round(1980 + t / 3))
        if yr in YEARS and yr not in rec:
            party = np.array([a.state.attrs.get("party") for a in eng.agents])
            pos = np.array([a.state.ideology for a in eng.agents])
            D, R = pos[party == 0], pos[party == 1]
            m = (party == 0) | (party == 1)
            rec[yr] = {
                "cult": float(pos[m, 1].mean()),
                "sep": float(np.hypot(*(R.mean(0) - D.mean(0)))),
                "cultgap": float(R[:, 1].mean() - D[:, 1].mean()),
                "corr": float(np.corrcoef(pos[m, 0], pos[m, 1])[0, 1]),
                "R_LL": float(np.mean((R[:, 0] <= 0) & (R[:, 1] <= 0))),
            }
    return rec


base = run(False)
variants = {f"cm_r={r}": run(True, r) for r in (0.005, 0.007, 0.010)}

print("=== cultural center: base vs emergent variants vs ANES ===")
print(f"{'yr':>5} {'ANES':>7} {'base':>7}" + "".join(f"{n.split('=')[1]:>8}" for n in variants))
for yr in YEARS:
    row = f"{yr:>5} {ANES_CULT[yr]:>7.3f} {base[yr]['cult']:>7.3f}"
    for n in variants:
        row += f"{variants[n][yr]['cult']:>8.3f}"
    print(row)

print("\n=== mid-period (1996-2004) mean |cult err| vs ANES (lower=better) ===")
for n, v in [("base", base)] + list(variants.items()):
    e = np.mean([abs(v[yr]['cult'] - ANES_CULT[yr]) for yr in (1996, 2000, 2004)])
    print(f"  {n:12} {e:.3f}")

print("\n=== sorting @ endpoints (party_sep / corr): base vs cm_r=0.007 ===")
cm = variants["cm_r=0.007"]
for yr in (2000, 2016, 2024):
    print(f"  {yr}: sep {base[yr]['sep']:.3f}->{cm[yr]['sep']:.3f}  "
          f"corr {base[yr]['corr']:.3f}->{cm[yr]['corr']:.3f}")

print("\n=== Republican wrong-quadrant (LL): base / cm_r=0.007 / ANES ===")
for yr in sorted(ANES_R_LL):
    print(f"  {yr}: {base[yr]['R_LL']:.3f} / {cm[yr]['R_LL']:.3f} / {ANES_R_LL[yr]:.3f}")
