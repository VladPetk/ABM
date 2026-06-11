"""T2.6 instrument — arc viability re-pick on the emergent substrate.

Sweeps the four re-pick knobs the S2 spec names (constraint_rate,
party_pull, idpull, animus) on the CANDIDATE flipped canonical preset
(n_issues=7, BC wake eps 0.40 / strength 0.03 from T0.6, soft-cap kwargs
retired) and reports endpoint macro + decade waypoints. This is a
viability re-pick, NOT calibration (s2_spec §7): the scorecard is
informational; S4 owns the fit. Sanity neighborhoods used for ranking:
sep@2025 toward ~1.0, affect@2025 ~ -0.6..-0.8, alignment rising,
within-party SD ~0.30-0.40, |r| endpoint ~0.6-0.8.

Run:  .venv/Scripts/python.exe scripts/audit/t26_arc_repick.py
Writes docs/internal/audit/t26_arc_repick.json
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

from abm.calibration_parallel import run_seeds_parallel
from scripts.anes_preset import ANES_FULL_KWARGS

SEEDS = list(range(6))
DECADES = [0, 30, 60, 90, 120, 135]

# The fixed flip components (everything but the swept knobs).
FLIP_BASE = {
    "n_issues": 7,
    "constraint_resid_sigma": 0.01,
    "tier_c_bc_epsilon": 0.40,   # T0.6 BC wake
    "tier_c_bc_strength": 0.03,
}
RETIRED_KEYS = ("tier_d_ic_partisan_x_cap", "tier_d_ic_wrongside_tail_target")

GRID = [
    {"constraint_rate": cr, "tier_c_party_pull_strength": pp,
     "sandbox_animus_mult": am,
     "tier_c_identity_pull_x": ipx, "tier_c_identity_pull_y": ipy}
    for cr in (0.015, 0.02, 0.03)
    for pp in (0.04, 0.05)
    for am in (0.8, 1.0)
    for (ipx, ipy) in ((0.020, 0.040), (0.015, 0.030))
]


def cell_kwargs(cell: dict) -> dict:
    kw = dict(ANES_FULL_KWARGS)
    for k in RETIRED_KEYS:
        kw.pop(k, None)
    kw.update(FLIP_BASE)
    kw.update(cell)
    return kw


def worker(args):
    seed, cell = args
    from abm.pillars.historical_arc import build_engine, build_schedule
    from abm.pillars.schedule import run_to
    from scripts.phase8f_lib import measure_all

    eng = build_engine(seed=seed, **cell_kwargs(cell))
    sched = build_schedule(faction_anchor_events=True, evidence_regrade=True,
                           exogenous_shocks=True)
    out = {}
    for t in DECADES:
        run_to(eng, sched, t)
        m = measure_all(eng)
        parties = np.array([a.state.attrs.get("party", 2) for a in eng.agents])
        pos = eng.positions()
        aligns = [a.state.attrs.get("identity_alignment", 0.0)
                  for a in eng.agents if a.state.attrs.get("party") in (0, 1)]
        V = np.array([a.state.attrs["issues"] for a in eng.agents])
        C = np.nan_to_num(np.corrcoef(V, rowvar=False), nan=0.0)
        out[t] = {
            "sep": float(m["party_sep"]),
            "affect": float(m["affect"]),
            "align": float(np.mean(aligns)),
            "wp_sd_x": float(np.mean([pos[parties == p, 0].std()
                                      for p in (0, 1)])),
            "abs_r": float(np.abs(C[np.triu_indices(7, 1)]).mean()),
            "mod": float(m.get("modularity", 0.0)),
            "xc": float(m.get("xc_fraction", 0.0)),
        }
    return out


def main():
    work = [(s, cell) for cell in GRID for s in SEEDS]
    flat = run_seeds_parallel(worker, work)
    by_cell: dict[int, list] = {}
    for (s, cell), r in zip(work, flat):
        by_cell.setdefault(GRID.index(cell), []).append(r)

    rows = []
    for ci, runs in by_cell.items():
        cell = GRID[ci]
        m = {t: {k: float(np.mean([r[t][k] for r in runs]))
                 for k in runs[0][t]} for t in DECADES}
        rows.append((cell, m))

    print(f"{'rate':>5s} {'pp':>5s} {'anim':>5s} {'idpx':>5s} | "
          f"{'sep25':>6s} {'aff25':>7s} {'algn25':>6s} {'wp_sd':>6s} "
          f"{'|r|25':>6s} {'mod':>5s} {'xc':>5s} | {'aff90':>7s} {'sep80':>6s}")
    for cell, m in rows:
        e = m[135]
        print(f"{cell['constraint_rate']:>5.3f} "
              f"{cell['tier_c_party_pull_strength']:>5.2f} "
              f"{cell['sandbox_animus_mult']:>5.2f} "
              f"{cell['tier_c_identity_pull_x']:>5.3f} | "
              f"{e['sep']:>6.3f} {e['affect']:>+7.3f} {e['align']:>6.3f} "
              f"{e['wp_sd_x']:>6.3f} {e['abs_r']:>6.3f} {e['mod']:>5.2f} "
              f"{e['xc']:>5.2f} | {m[90]['affect']:>+7.3f} {m[0]['sep']:>6.3f}")

    outp = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "..",
        "docs", "internal", "audit", "t26_arc_repick.json"))
    with open(outp, "w") as f:
        json.dump({"seeds": SEEDS, "flip_base": FLIP_BASE,
                   "retired": list(RETIRED_KEYS),
                   "cells": [{"cell": c, "decades": {str(t): v for t, v in m.items()}}
                             for c, m in rows]}, f, indent=2)
    print(f"wrote {outp}")


if __name__ == "__main__":
    main()
