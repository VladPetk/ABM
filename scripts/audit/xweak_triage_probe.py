"""Triage probe (one-off): for X3 / X4 / X7, does the lever actually MUTATE
live engine state on apply (→ live-but-small null, faithful), or is there
nothing to change / is it shadowed (→ inert like X2, needs fix)?

Builds the canonical engine, runs to release (2010), snapshots the population
state each lever targets, applies the lever, snapshots again. One seed (the
state-change is deterministic given the seed).
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
from scripts.audit.audit_lib import build_engine, _make_schedule, _find_rule

BY_ID = {iv.id: iv for iv in INTERVENTIONS_PHASE6}
RELEASE = 90  # 2010 — media / social / perception channels all live
CABLE = {0, 4}  # MSNBC, Fox


def _build_to_release(seed=0):
    eng = build_engine(seed=seed, **ANES_FULL_KWARGS)
    sched = _make_schedule("full")
    for t in range(1, RELEASE + 1):
        run_to(eng, sched, t)
    return eng


def _x3_state(eng):
    agents = eng.agents
    cable_w = 0.0
    n_with_cable = 0
    n_with_diet = 0
    for a in agents:
        diet = a.state.attrs.get("media_diet")
        if diet:
            n_with_diet += 1
            w = sum(diet.get(c, 0.0) for c in CABLE)
            cable_w += w
            if w > 0:
                n_with_cable += 1
    mc = _find_rule(eng, "MediaConsumption")
    return {
        "agents_with_media_diet": n_with_diet,
        "agents_with_cable>0": n_with_cable,
        "total_cable_weight": round(cable_w, 4),
        "MediaConsumption.strength": getattr(mc, "strength", None) if mc else "ABSENT",
        "env.media_strength": round(float(eng.env.attrs.get("media_strength", 0.0)), 4),
    }


def _x4_state(eng):
    coop = [float(a.state.attrs.get("cooperative_share", 0.0)) for a in eng.agents]
    threat = [float(a.state.attrs.get("perceived_threat", 0.0)) for a in eng.agents]
    n_high = sum(1 for c in coop if c >= 0.49)
    return {
        "mean_cooperative_share": round(float(np.mean(coop)), 4),
        "agents_coop>=0.49": n_high,
        "mean_perceived_threat": round(float(np.mean(threat)), 4),
        "env.sandbox_contact_share(floor)": round(float(eng.env.attrs.get("sandbox_contact_share", 0.0)), 4),
    }


def _x7_state(eng):
    n_perc = sum(1 for a in eng.agents if a.state.attrs.get("perceived_other_party"))
    n_override = sum(1 for a in eng.agents if a.state.attrs.get("correction_rate_override") is not None)
    n_target = sum(1 for a in eng.agents if a.state.attrs.get("perception_target_override") is not None)
    pu = _find_rule(eng, "PerceptionUpdate")
    return {
        "agents_with_perceived_other_party": n_perc,
        "agents_with_correction_rate_override": n_override,
        "agents_with_perception_target_override": n_target,
        "PerceptionUpdate_rule": "present" if pu else "ABSENT",
    }


INSPECT = {
    "X3_quit_cable_news": _x3_state,
    "X4_bipartisan_dialogue": _x4_state,
    "X7_perception_correction": _x7_state,
}


def main():
    print(f"R-B triage — state change on apply at release 2010 (tick {RELEASE}), seed 0")
    print("=" * 78)
    for iv_id, inspect in INSPECT.items():
        eng = _build_to_release()
        before = inspect(eng)
        apply_intervention(eng, BY_ID[iv_id])
        after = inspect(eng)
        print(f"\n## {iv_id}")
        keys = list(before.keys())
        for k in keys:
            b, a = before[k], after[k]
            mark = "  <-- CHANGED" if b != a else ""
            print(f"  {k:<42} before={b!s:<10} after={a!s}{mark}")
    print("\n" + "=" * 78)
    print("CHANGED on the targeted state -> live lever (small null = faithful). "
          "No change / channel ABSENT -> inert like X2 (needs fix).")


if __name__ == "__main__":
    main()
