"""
Affect-recalibration FEASIBILITY scope (audit follow-up, NOT a committed fix).

Question: can re-tuning the pure affect knobs bring out-party affect back into the
grounded ANES thermometer bands (currently 0/5 on the shipped config) WITHOUT
knocking the 4 currently-in-band position metrics (party_sep, constraint,
within_party_sd, variance) out of band?

Method: monkeypatch the module-level affect constants + mutate the AffectiveUpdate
rule's saturation post-build (engine files untouched), then reuse the REAL scorer
(_score_cells, same path that produced realism_measurement.json). For each knob
cell, report affect-cells-in-band /5, the full n24/24, and any NON-affect cell that
flips OUT (the cross-coupling cost).

Knobs swept:
  lr_scale   -> multiplies AFFECT_LR_BASE_REGRADE (contact cooling, dominant early)
  sat        -> AffectiveUpdate.saturation (retired under evidence_regrade; >0 damps
                cooling near the floor, helps late decades)
  mani_scale -> multiplies MEDIATED_ANIMUS_LR (parasocial cooling, 2008+ only)

Run: .venv/Scripts/python.exe validation/audit/affect_recal_scope.py --seeds 1
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import abm.pillars.historical_arc as ha  # noqa: E402
from abm.pillars.historical_arc import build_engine, build_schedule  # noqa: E402
from abm.pillars.schedule import run_to  # noqa: E402
from scripts.phase8f_lib import (  # noqa: E402
    measure_all, aggregate, get_primary_targets, get_initial_targets_1980,
)
from scripts.phase9_anes_score import _score_cells  # noqa: E402
from scripts.anes_preset import ANES_FULL_KWARGS  # noqa: E402

SNAPS = [(1980, 21), (1990, 42), (2000, 72), (2010, 102), (2020, 126), (2025, 135)]
AFFECT_DECADES = [1990, 2000, 2010, 2020, 2025]

# (lr_scale, baseline, saturation, mani_scale)
# baseline = AffectiveUpdate per-encounter coolness floor (default 0.10). Lowering
# it warms the EARLY decades specifically (when parties overlap and the floor, not
# ideological distance, dominates cooling) without flattening the late acceleration.
GRID = [
    (1.0, 0.0, 0.0, 1.0),   # canonical reference (reproduce realism_measurement A4)
    (0.3, 0.0, 1.0, 0.4),   # ~4/5 candidate
    (0.25, 0.0, 1.0, 0.35),
    (0.2, 0.0, 1.0, 0.3),   # 5/5 candidate
]


def _find_rules(eng, classname):
    # engine.rules is the RulePipeline; engine.rules.rules is the list of rules.
    pipe = getattr(eng, "rules", None) or getattr(eng, "pipeline", None)
    rules = getattr(pipe, "rules", pipe)  # RulePipeline.rules -> list; or already a list
    out = [r for r in (rules or []) if type(r).__name__ == classname]
    for attr in ("env_rules", "envrules", "_env_rules"):
        out += [r for r in (getattr(pipe, attr, None) or []) if type(r).__name__ == classname]
    return out


def run_seed(seed, lr_scale, baseline, sat, mani_scale):
    # All knobs applied POST-build by mutating rule attrs + per-agent affect_lr,
    # so we bypass the build-time affect_lr clip [0.001,0.03] and test the cooling
    # mechanism cleanly. baseline is forced explicitly (canonical = 0.0).
    k = dict(ANES_FULL_KWARGS)
    eng = build_engine(seed=seed, **k)
    affrules = _find_rules(eng, "AffectiveUpdate")
    manirules = _find_rules(eng, "MediatedAnimus")
    if not affrules:
        raise RuntimeError("AffectiveUpdate rule not found in pipeline")
    for r in affrules:
        r.saturation = float(sat)
        r.baseline = float(baseline)
    for r in manirules:
        r.lr = float(r.lr) * float(mani_scale)
    # scale per-agent contact learning rate (the lever that drives AffectiveUpdate)
    for a in eng.agents:
        cur = a.state.attrs.get("affect_lr")
        if cur is not None:
            a.state.attrs["affect_lr"] = float(cur) * float(lr_scale)
    sched = build_schedule(
        factional_seeding=k.get("factional_seeding", False),
        faction_anchor_events=k.get("faction_anchor_events", True),
        evidence_regrade=k.get("evidence_regrade", False),
        exogenous_shocks=k.get("exogenous_shocks", False))
    traj = {}
    for lab, tick in SNAPS:
        if tick > 0:
            run_to(eng, sched, tick)
        traj[lab] = measure_all(eng)
    return traj


def score_cell(seeds, lr_scale, baseline, sat, mani_scale):
    trajs = [run_seed(s, lr_scale, baseline, sat, mani_scale) for s in seeds]
    means, ses = aggregate(trajs)
    pri = get_primary_targets(use_anes_bands=True)
    init = get_initial_targets_1980(use_anes_bands=True)
    cells_4x5, cells_init, n45, ninit, n24 = _score_cells(means, ses, pri, init)
    allcells = cells_4x5 + cells_init
    affect = {}
    aff_in = 0
    for c in allcells:
        if c["metric"] == "affect":
            affect[c["year"]] = (round(c["value"], 3), c["in_band"])
            if c["in_band"]:
                aff_in += 1
    non_aff_out = [
        f"{c['year']}/{c['metric']}={c['value']:+.2f}[{c['band_lo']:+.2f},{c['band_hi']:+.2f}]"
        for c in allcells if c["metric"] != "affect" and not c["in_band"]
    ]
    return {
        "knobs": {"lr_scale": lr_scale, "baseline": baseline, "sat": sat,
                  "mani_scale": mani_scale},
        "affect": affect, "affect_in_band": aff_in, "n24": n24,
        "non_affect_out": non_aff_out,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=1)
    args = ap.parse_args()
    seeds = list(range(args.seeds))
    print(f"affect-recal scope: {len(GRID)} cells x {len(seeds)} seed(s) on ANES_FULL_KWARGS")
    print(f"baseline constants: AFFECT_LR_BASE_REGRADE={ha.AFFECT_LR_BASE_REGRADE} "
          f"MEDIATED_ANIMUS_LR={ha.MEDIATED_ANIMUS_LR}\n")
    rows = []
    for (lr, base, sat, mani) in GRID:
        r = score_cell(seeds, lr, base, sat, mani)
        rows.append(r)
        affstr = " ".join(
            f"{y}:{r['affect'].get(y, ('?', False))[0]}"
            f"{'*' if r['affect'].get(y, ('', False))[1] else ' '}"
            for y in AFFECT_DECADES)
        print(f"lr={lr:<4} base={base:<5} sat={sat:<4} mani={mani:<4} | aff {affstr} | "
              f"aff_in={r['affect_in_band']}/5 | n24={r['n24']}/24 | "
              f"nonaff_out={len(r['non_affect_out'])}", flush=True)
    out = os.path.join(os.path.dirname(__file__), "affect_recal_scope.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)
    print(f"\nwrote {out}")
    print("(* = affect cell in band; baseline row should reproduce realism_measurement A4)")


if __name__ == "__main__":
    main()
