"""T2.4 instrument — measured-alignment trajectory, emergent vs legacy.

Traces mean partisan identity_alignment (and its two factors on the
emergent path) at decade ticks, plus affect/sep endpoints, so the report
can say honestly what the M3-light collapse did to the alignment spine.

Run:  .venv/Scripts/python.exe scripts/audit/t24_alignment_trace.py
Writes docs/internal/audit/t24_alignment_trace.json
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
from abm.rules.measured_alignment import measure_alignment

SEEDS = list(range(8))
TICKS = [0, 18, 30, 60, 90, 120, 135]


def _snapshot(eng):
    from scripts.phase8f_lib import measure_all
    rt = eng.env.attrs.get("issue_runtime")
    centers = eng.env.attrs.get("party_identity_centers")
    aligns, id_stacks, issue_stacks = [], [], []
    for a in eng.agents:
        party = a.state.attrs.get("party")
        if party not in (0, 1):
            continue
        aligns.append(float(a.state.attrs.get("identity_alignment", 0.0)))
        if rt is not None and rt.get("align_u") is not None:
            ids = np.asarray(a.state.attrs["identities"], float)
            c = (centers or {}).get(party)
            sign = (1.0 if party == 1 else -1.0) if c is None else (
                1.0 if float(np.mean(np.asarray(c))) >= 0.0 else -1.0)
            id_stacks.append(float(np.clip(sign * ids.mean(), 0.0, 1.0)))
            v = np.asarray(a.state.attrs["issues"], float)
            p = 1.0 if party == 1 else -1.0
            issue_stacks.append(float(np.clip(
                p * float((v - rt["align_m"]) @ rt["align_u"]), 0.0, 1.0)))
    m = measure_all(eng)
    return {
        "align": float(np.mean(aligns)),
        "id_stack": float(np.mean(id_stacks)) if id_stacks else None,
        "issue_stack": float(np.mean(issue_stacks)) if issue_stacks else None,
        "sep": float(m["party_sep"]),
        "affect": float(m["affect"]),
    }


def worker(args):
    seed, mode = args
    from abm.pillars.historical_arc import build_engine, build_schedule
    from abm.pillars.schedule import run_to
    kw = dict(seed=seed, evidence_regrade=True, exogenous_shocks=True)
    if mode == "emergent":
        kw.update(n_issues=7, constraint_rate=0.02, constraint_resid_sigma=0.01)
    eng = build_engine(**kw)
    sched = build_schedule(evidence_regrade=True, exogenous_shocks=True)
    out = {}
    for t in TICKS:
        run_to(eng, sched, t)
        out[t] = _snapshot(eng)
    return out


def main():
    work = [(s, m) for m in ("emergent", "legacy") for s in SEEDS]
    flat = run_seeds_parallel(worker, work)
    res = {"emergent": [], "legacy": []}
    for (s, m), r in zip(work, flat):
        res[m].append(r)

    summary = {}
    for mode, runs in res.items():
        summary[mode] = {}
        for t in TICKS:
            row = {}
            for k in ("align", "id_stack", "issue_stack", "sep", "affect"):
                vals = [r[t][k] for r in runs if r[t][k] is not None]
                row[k] = round(float(np.mean(vals)), 4) if vals else None
            summary[mode][t] = row

    outp = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "..",
        "docs", "internal", "audit", "t24_alignment_trace.json"))
    with open(outp, "w") as f:
        json.dump({"seeds": SEEDS, "ticks": TICKS, "summary": summary}, f, indent=2)

    hdr = f"{'tick':>5s} {'year':>5s} | " + "  ".join(
        f"{k:>11s}" for k in ("align", "id_stack", "issue_stack", "sep", "affect"))
    for mode in ("emergent", "legacy"):
        print(f"\n== {mode} ==\n{hdr}")
        for t in TICKS:
            row = summary[mode][t]
            cells = "  ".join(
                f"{(row[k] if row[k] is not None else float('nan')):>11.4f}"
                for k in ("align", "id_stack", "issue_stack", "sep", "affect"))
            print(f"{t:>5d} {1980 + t / 3:>5.0f} | {cells}")
    print(f"\nwrote {outp}")


if __name__ == "__main__":
    main()
