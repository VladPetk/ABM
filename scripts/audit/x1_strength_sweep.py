"""Probe (one-off): re-anchor threat-gated X1's strength so the threat-era
releases (2010/2020) land a PARTIAL backfire (+0.05..+0.15), without runaway.

X1 now opts into threat-gating (fires only for the post-2016 threatened subset).
Its strength (0.055) was tuned for the OLD unconditional gate, so it's free to
re-anchor. Sweep strength at releases 2010 (tick 90) and 2020 (tick 120),
Δsep vs same-seed control at +30t, 5 seeds. Pre-2016 releases stay ~0 (threat=0)
by construction, so they're not swept.
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

from abm.pillars.intervention import apply_intervention
from abm.pillars.interventions_phase6 import INTERVENTIONS_PHASE6
from abm.pillars.schedule import run_to
from scripts.anes_preset import ANES_FULL_KWARGS
from scripts.phase8f_lib import party_sep_metric
from scripts.audit.audit_lib import build_engine, _make_schedule, _find_rule

X1 = next(iv for iv in INTERVENTIONS_PHASE6 if iv.id == "X1_show_other_side")
SEEDS = (0, 1, 2, 3, 4)
STRENGTHS = (0.10, 0.15, 0.20, 0.30)
RELEASES = {2010: 90, 2020: 120}


def _worker(arg):
    cond, seed, release = arg
    eng = build_engine(seed=seed, **ANES_FULL_KWARGS)
    sched = _make_schedule("full")
    h = min(release + 30, 150)
    for t in range(1, h + 1):
        run_to(eng, sched, t)
        if t == release and cond != "control":
            apply_intervention(eng, X1)  # sets threat_gated=True, strength 0.055
            bl = _find_rule(eng, "BacklashRepulsion")
            if bl is not None:
                bl.strength = float(cond)  # re-anchor strength
    return {"cond": cond, "seed": seed, "release": release,
            "sep": float(party_sep_metric(eng))}


def main():
    from abm.calibration_parallel import run_seeds_parallel
    conds = ["control"] + [f"{s}" for s in STRENGTHS]
    work = [(c, s, rel) for rel in RELEASES.values() for c in conds for s in SEEDS]
    res = run_seeds_parallel(_worker, work)
    by = {(r["cond"], r["seed"], r["release"]): r["sep"] for r in res}

    print(f"Threat-gated X1 strength sweep — Δsep vs control at +30t, {len(SEEDS)} seeds")
    print("backfire bucket: Δsep > +0.05 (partial 0.05-0.15, real >=0.15). "
          "current strength was 0.055.")
    print("=" * 60)
    print(f"{'strength':>9} | {'2010 Δsep':>10} {'bkt':>8} | {'2020 Δsep':>10} {'bkt':>8}")
    print("-" * 60)
    def bkt(d):
        if d > 0.15: return "real-bf"
        if d > 0.05: return "partial-bf"
        if d < -0.05: return "HELP?!"
        return "null"
    for s in STRENGTHS:
        row = []
        for rel in (90, 120):
            d = np.mean([by[(f"{s}", sd, rel)] - by[("control", sd, rel)] for sd in SEEDS])
            row.append((d, bkt(d)))
        print(f"{s:>9} | {row[0][0]:>+10.3f} {row[0][1]:>8} | {row[1][0]:>+10.3f} {row[1][1]:>8}")
    print("-" * 60)
    print("Pick the smallest strength whose 2010/2020 land partial (0.05-0.15), "
          "no runaway. (1990/2000 stay null — threat=0.)")


if __name__ == "__main__":
    main()
