"""Diagnostic (one-off, analysis-only): decompose the long-run (2025) fate of
ALL SEVEN interventions X1-X7, and attribute any washout to forcings vs
endogenous self-regularization.

Generalizes scripts/audit/x6_reconvergence_decomp.py (the X6 pilot) to the
whole library. For each intervention, at its most-live release decade, run
control vs treated as same-seed full trajectories to 2025 and snapshot the
headline metrics at three ticks:
    immediate (release)  |  +10y (release+30, the phase10 bucket horizon)  |  2025
under four regimes:
    shipped     — canonical R-phase engine + full schedule (what the demo shows)
    frozen      — ALL forcings clamped at 1980 + empty schedule (no events/drift)
    rest-off    — affect_rest_rate = 0          (kills R7 affect mean-reversion)
    cohort-off  — cohort_replacement_rate = 0   (treated agents never turn over)

Read:
  • shipped vs frozen IDENTICAL  -> washout/effect is endogenous, NOT forcing-driven.
  • shipped vs frozen DIVERGE    -> forcings carry it (forcing-override / forcing-dilution).
  • rest-off / cohort-off lift    -> attribute the endogenous share (mean-reversion vs turnover).
  • effect ~0 at ALL horizons     -> inert/weak channel (nothing to wash out).

NOT committed. Run:
  .venv/Scripts/python.exe scripts/audit/intervention_durability_decomp.py
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
from scripts.audit.audit_lib import (
    build_engine, _apply_freeze, _capture_baseline, _make_schedule, END_TICK,
)

_BY_ID = {iv.id: iv for iv in INTERVENTIONS_PHASE6}

# headline axis per intervention (the one its bucket is declared on) + the
# release decade where it is most live (X5 is decade-gated: no factions before
# the emergence events, so it is measured at its only live decade, 2020).
IVS = [
    ("X1_show_other_side",       "sep", 60),   # 2000  — sorting backfire
    ("X2_fix_algorithm",         "aff", 60),
    ("X3_quit_cable_news",       "sep", 60),
    ("X4_bipartisan_dialogue",   "aff", 60),
    ("X5_deprogramming",         "sep", 120),  # 2020  — factions exist
    ("X6_shared_institutions",   "aff", 60),   # 2000  — matches the pilot
    ("X7_perception_correction", "aff", 60),
]

SEEDS = (0, 1, 2, 3, 4)
ALL_FREEZE = {"elite_drift", "identity_sorting", "coupling", "party_k",
              "social_media", "data_fed_inputs", "endogenous_loop"}
REGIMES = {
    "shipped":    dict(overrides={}, freeze=None, mode="full"),
    "frozen":     dict(overrides={}, freeze=ALL_FREEZE, mode="empty"),
    "rest-off":   dict(overrides={"affect_rest_rate": 0.0}, freeze=None, mode="full"),
    "cohort-off": dict(overrides={"cohort_replacement_rate": 0.0}, freeze=None, mode="full"),
}


def _snap(eng):
    return (float(affective_polarization(eng.agents)), float(party_sep_metric(eng)))


def _worker(arg):
    """arg = (iv_id, regime, cond, seed, release). cond in {'ctrl','tx'}.
    Returns the (aff, sep) snapshot at release / +10y / 2025."""
    iv_id, regime, cond, seed, release = arg
    cfg = REGIMES[regime]
    kwargs = dict(ANES_FULL_KWARGS)
    kwargs.update(cfg["overrides"] or {})
    eng = build_engine(seed=seed, **kwargs)
    sched = _make_schedule(cfg["mode"])
    freeze = cfg["freeze"]
    base = _capture_baseline(eng) if freeze else None
    if freeze:
        _apply_freeze(eng, freeze, base)

    h_tick = min(release + 30, END_TICK)
    snaps = {}
    for t in range(1, END_TICK + 1):
        run_to(eng, sched, t)
        if freeze:
            _apply_freeze(eng, freeze, base)
        if cond == "tx" and t == release:
            apply_intervention(eng, _BY_ID[iv_id])
        if t == release or t == h_tick or t == END_TICK:
            snaps[t] = _snap(eng)
    return {"iv": iv_id, "regime": regime, "cond": cond, "seed": seed,
            "release": release, "imm": snaps[release], "h": snaps[h_tick],
            "end": snaps[END_TICK]}


def main():
    from abm.calibration_parallel import run_seeds_parallel

    work = [(iv, reg, cond, s, rel)
            for (iv, _axis, rel) in IVS
            for reg in REGIMES
            for cond in ("ctrl", "tx")
            for s in SEEDS]
    print(f"running {len(work)} full-arc runs "
          f"({len(IVS)} ivs x {len(REGIMES)} regimes x 2 conds x {len(SEEDS)} seeds)...")
    res = run_seeds_parallel(_worker, work)

    # index by (iv, regime, cond, seed)
    by = {(r["iv"], r["regime"], r["cond"], r["seed"]): r for r in res}
    axis_of = {iv: ax for (iv, ax, _r) in IVS}
    rel_of = {iv: rel for (iv, _ax, rel) in IVS}

    def delta(iv, regime, which, axis):
        """mean over seeds of (tx - ctrl) on `axis` at horizon `which`.
        Helpful sign: affect positive = warmer; sep negative = closer. We
        report the RAW signed delta; the headline axis is noted per row."""
        idx = 0 if axis == "aff" else 1
        ds = []
        for s in SEEDS:
            c = by.get((iv, regime, "ctrl", s))
            t = by.get((iv, regime, "tx", s))
            if c and t:
                ds.append(t[which][idx] - c[which][idx])
        return float(np.mean(ds)) if ds else float("nan")

    print("\n" + "=" * 104)
    print("Intervention durability decomposition  —  headline-axis delta (tx - control), 5 seeds")
    print("  affect: + = warmer = helpful  |  sorting (sep): - = closer = helpful")
    print("=" * 104)
    hdr = (f"{'iv':<24} {'axis':<4} {'rel':>4} {'regime':<11} | "
           f"{'immediate':>10} {'+10y':>10} {'2025':>10} {'retained%':>9}")
    print(hdr)
    print("-" * len(hdr))
    for iv, axis, _r in IVS:
        rel = rel_of[iv]
        for regime in REGIMES:
            imm = delta(iv, regime, "imm", axis)
            h = delta(iv, regime, "h", axis)
            end = delta(iv, regime, "end", axis)
            ret = (end / imm * 100.0) if abs(imm) > 1e-6 else float("nan")
            print(f"{iv:<24} {axis:<4} {rel:>4} {regime:<11} | "
                  f"{imm:>+10.3f} {h:>+10.3f} {end:>+10.3f} {ret:>8.0f}%")
        print("-" * len(hdr))


if __name__ == "__main__":
    main()
