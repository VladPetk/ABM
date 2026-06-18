"""Probe (one-off): does a SUSTAINED population-wide contact floor give X6 a
DURABLE warming (persists to 2025), and what floor value lands it in the
Pettigrew-Tropp envelope (partial: +0.05..+0.15 helpful)?

Candidate faithful X6 ("sustained shared institutions"): set the cohort-proof
env floor env.attrs['sandbox_contact_share'] = C at release (permanent — a
structural feature), muting out-party cooling population-wide and continuously
(Pettigrew 2009 secondary-transfer). Compare to the shipped one-shot X6.

Δ vs same-seed control at +10y (tick 90) and 2025 (tick 135), release 2000, 5 seeds.
Baseline floor is 0.15 (R1 contact); the candidates raise it to C.
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
from scripts.phase8f_lib import affective_polarization, party_sep_metric
from scripts.audit.audit_lib import build_engine, _make_schedule, END_TICK

X6 = next(iv for iv in INTERVENTIONS_PHASE6 if iv.id == "X6_shared_institutions")
RELEASE = 60
SEEDS = (0, 1, 2, 3, 4)
# Round 2: pure-sustained-max (floor only) vs current one-shot + sustained floor.
# "cur+susC" = apply the shipped X6 (initial contact warming + ties) AND set the
# cohort-proof floor to C (durability). Looking for a DURABLE partial.
CONDS = ["control", "current", "sus1.0", "cur+sus0.5", "cur+sus1.0"]


def _worker(arg):
    cond, seed = arg
    eng = build_engine(seed=seed, **ANES_FULL_KWARGS)
    sched = _make_schedule("full")
    snaps = {}
    for t in range(1, END_TICK + 1):
        run_to(eng, sched, t)
        if t == RELEASE:
            if cond == "current":
                apply_intervention(eng, X6)
            elif cond.startswith("sus"):
                eng.env.attrs["sandbox_contact_share"] = float(cond[3:])
            elif cond.startswith("cur+sus"):
                apply_intervention(eng, X6)
                eng.env.attrs["sandbox_contact_share"] = float(cond.split("sus")[1])
        if t in (90, END_TICK):
            snaps[t] = (float(affective_polarization(eng.agents)),
                        float(party_sep_metric(eng)))
    return {"cond": cond, "seed": seed, "snaps": snaps}


def main():
    from abm.calibration_parallel import run_seeds_parallel
    work = [(c, s) for c in CONDS for s in SEEDS]
    res = run_seeds_parallel(_worker, work)
    by = {(r["cond"], r["seed"]): r["snaps"] for r in res}

    print(f"X6 sustained-institutions probe — release 2000, {len(SEEDS)} seeds")
    print("Δ vs control: aff (+ = warmer = helpful). Pettigrew-Tropp envelope: "
          "partial +0.05..+0.15, real >=+0.15, cap +0.30.")
    print("baseline contact floor = 0.15; sustained candidates raise it to C.")
    print("=" * 74)
    print(f"{'condition':<14} | {'Δaff +10y':>10} | {'Δaff 2025':>10} | "
          f"{'durable?':>9} | {'Δsep 2025':>10}")
    print("-" * 74)
    for cond in CONDS:
        if cond == "control":
            continue
        da10 = np.mean([by[(cond, s)][90][0] - by[("control", s)][90][0] for s in SEEDS])
        da25 = np.mean([by[(cond, s)][END_TICK][0] - by[("control", s)][END_TICK][0] for s in SEEDS])
        ds25 = np.mean([by[(cond, s)][END_TICK][1] - by[("control", s)][END_TICK][1] for s in SEEDS])
        durable = "partial!" if 0.05 <= da25 <= 0.15 else ("real" if da25 > 0.15 else "sub")
        print(f"{cond:<14} | {da10:>+10.3f} | {da25:>+10.3f} | {durable:>9} | {ds25:>+10.3f}")
    print("-" * 74)
    print("current fades to ~+0.017 (9% retained). A sustained floor that lands "
          "Δaff 2025 in +0.05..+0.15 = durable partial within the envelope.")


if __name__ == "__main__":
    main()
