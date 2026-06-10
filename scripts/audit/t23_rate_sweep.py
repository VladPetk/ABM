"""MHV S2 T2.3 — constraint_rate prior-centering sweep.

Finds the neighborhood of `constraint_rate` (x resid_sigma) where the
emergent ConstraintOp produces a BOUNDED, B&G/Kozlowski-plausible
constraint collapse on the live D=7 arc: pooled mean |inter-item r|
rising from the ~0.16 1986 seed by roughly +0.05..+0.15 over the arc
(Kozlowski & Murphy 2021 document the 2004-2016 rise; B&G 2008 the
modest pre-2004 trend), with the participation ratio staying clearly
above 1 (no runaway to rank-1). The chosen center becomes the kwarg
default / S4 prior center — N-tagged; S4 fits it properly.

Run: .venv/Scripts/python.exe scripts/audit/t23_rate_sweep.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import numpy as np

from abm.calibration_parallel import run_seeds_parallel

DECADES = {1986: 21, 2000: 72, 2016: 108, 2025: 135}


def worker(arg):
    rate, resid, seed = arg
    from abm.pillars.historical_arc import build_engine, build_schedule
    from abm.pillars.schedule import run_to
    eng = build_engine(seed=seed, n_issues=7, evidence_regrade=True,
                       exogenous_shocks=True, constraint_rate=rate,
                       constraint_resid_sigma=resid)
    sched = build_schedule(evidence_regrade=True, exogenous_shocks=True)
    out = {}
    for label, t in sorted(DECADES.items(), key=lambda kv: kv[1]):
        run_to(eng, sched, t)
        V = np.array([a.state.attrs["issues"] for a in eng.agents])
        party = np.array([a.state.attrs.get("party", 2) for a in eng.agents])
        def stats(M):
            C = np.nan_to_num(np.corrcoef(M, rowvar=False), nan=0.0)
            off = C[np.triu_indices(C.shape[0], 1)]
            w = np.clip(np.linalg.eigvalsh(C), 1e-9, None)
            return float(np.abs(off).mean()), float((w.sum() ** 2) / (w ** 2).sum())
        r_pool, pr_pool = stats(V)
        wp = [stats(V[party == p]) for p in (0, 1) if (party == p).sum() > 10]
        out[label] = {
            "r_pool": r_pool, "pr_pool": pr_pool,
            "r_wp": float(np.mean([x[0] for x in wp])),
            "pr_wp": float(np.mean([x[1] for x in wp])),
        }
    return (rate, resid, out)


def main():
    grid = [(0.0, 0.0), (0.005, 0.01), (0.01, 0.01), (0.02, 0.01),
            (0.04, 0.01), (0.02, 0.0), (0.02, 0.02)]
    work = [(r, rs, s) for (r, rs) in grid for s in range(4)]
    res = run_seeds_parallel(worker, work)
    agg = {}
    for rate, resid, out in res:
        agg.setdefault((rate, resid), []).append(out)
    print(f"{'rate':>6} {'resid':>6} | {'r86':>5} {'r2000':>6} {'r2016':>6} "
          f"{'r2025':>6} | {'wp86':>5} {'wp25':>5} | {'PR86':>5} {'PR25':>5} {'PRwp25':>6}")
    for (rate, resid), runs in sorted(agg.items()):
        def m(label, key):
            return float(np.mean([r[label][key] for r in runs]))
        print(f"{rate:>6} {resid:>6} | {m(1986,'r_pool'):>5.3f} "
              f"{m(2000,'r_pool'):>6.3f} {m(2016,'r_pool'):>6.3f} "
              f"{m(2025,'r_pool'):>6.3f} | {m(1986,'r_wp'):>5.3f} "
              f"{m(2025,'r_wp'):>5.3f} | {m(1986,'pr_pool'):>5.2f} "
              f"{m(2025,'pr_pool'):>5.2f} {m(2025,'pr_wp'):>6.2f}")


if __name__ == "__main__":
    main()
