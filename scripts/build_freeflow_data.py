"""build_freeflow_data.py — export the FREE-FLOWING engine run for the web prologue.

The prologue ("the engine with America switched off") animates the engine running
from the 1980 US seed with every empirical/external driver removed — the same
"all_frozen / empty schedule" floor the honesty budget measures
(scripts/audit/t35_budget_brake.py): mobilization frozen at 1980, no dated events,
no media ramp, no data-fed input series. It still cools (affect is ~83% the
engine's own dynamics) but the positional split stalls (~34% emergent) — the gap
the real US history fills.

Seed 0, full per-agent positions + the three macro series (sep / aff /
identity_alignment), same shape as runs.baseline so <Field> can render it directly.

Output: web_demo/cc-freeflow.js  ->  window.CC_FREEFLOW = {meta, run:{pos,party,macro}}

Run: PYTHONPATH=. .venv/Scripts/python.exe scripts/build_freeflow_data.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from abm.calibration_parallel import run_seeds_parallel
from abm.pillars.historical_arc import build_engine
from abm.pillars.schedule import run_to
from scripts.anes_preset import ANES_FULL_KWARGS
from scripts.audit.audit_lib import (
    END_TICK, _apply_freeze, _capture_baseline, _macro, _make_schedule,
    freeze_worker,
)

_ROOT = Path(__file__).resolve().parent.parent
OUT = _ROOT / "web_demo" / "cc-freeflow.js"

SEED = 0          # the animated cloud (one representative run)
MEAN_SEEDS = 6    # the chart LINES are the 6-seed mean (matches the honesty budget)
# the honesty-budget "all_frozen" floor (= free-flowing): freeze the scheduled
# drivers AND the data-fed input series, run on an empty (no-events) schedule.
FREEZE = {"elite_drift", "identity_sorting", "coupling", "party_k",
          "social_media", "data_fed_inputs"}


def _positions(eng):
    pos, party = [], []
    for a in eng.agents:
        ideo = a.state.ideology
        pos.append([round(float(ideo[0]), 3), round(float(ideo[1]), 3)])
        party.append(int(a.state.attrs.get("party", 2)))
    return pos, party


def main():
    eng = build_engine(seed=SEED, **dict(ANES_FULL_KWARGS))
    sched = _make_schedule("empty")
    base = _capture_baseline(eng)
    _apply_freeze(eng, FREEZE, base)

    pos_frames, party_frames, macro_frames = [], [], []

    def snap():
        p, pa = _positions(eng)
        pos_frames.append(p)
        party_frames.append(pa)
        m = _macro(eng)
        macro_frames.append({
            "sep": round(float(m["party_sep"]), 4),
            "aff": round(float(m["affect"]), 4),
            "identity_alignment": round(float(m["identity_alignment"]), 4),
        })

    snap()
    for t in range(1, END_TICK + 1):
        run_to(eng, sched, t)
        _apply_freeze(eng, FREEZE, base)
        snap()

    # 6-seed mean macro for the comparison chart lines (the cloud above is seed 0;
    # the lines are the ensemble, matching the blessed honesty-budget numbers).
    fr = tuple(sorted(FREEZE))
    flat = run_seeds_parallel(freeze_worker, [(s, fr, "empty") for s in range(MEAN_SEEDS)])
    mean_macro = []
    for t in range(END_TICK + 1):
        mean_macro.append({
            "sep": round(float(np.mean([r["series"][t]["party_sep"] for r in flat])), 4),
            "aff": round(float(np.mean([r["series"][t]["affect"] for r in flat])), 4),
            "identity_alignment": round(float(np.mean(
                [r["series"][t]["identity_alignment"] for r in flat])), 4),
        })

    payload = {
        "meta": {
            "kind": "freeflow",
            "n_agents": len(eng.agents),
            "n_ticks": END_TICK + 1,
            "tick_0_year": 1980.0,
            "ticks_per_year": 3.0,
            "seed": SEED,
            "note": ("FREE-FLOWING engine — every empirical/external driver removed "
                     "(mobilization frozen at 1980, no events, no media, no data-fed "
                     "inputs). Illustrative counterfactual, NOT the shipped US arc. "
                     "Built by scripts/build_freeflow_data.py."),
            "mean_seeds": MEAN_SEEDS,
        },
        # pos/party/macro = seed 0 (the animated cloud); macro_mean = 6-seed mean
        # (the chapter-B comparison lines, matching the honesty budget).
        "run": {"pos": pos_frames, "party": party_frames,
                "macro": macro_frames, "macro_mean": mean_macro},
    }
    text = "window.CC_FREEFLOW = " + json.dumps(payload, separators=(",", ":")) + ";\n"
    OUT.write_text(text, encoding="utf-8")
    s0, mn = macro_frames[-1], mean_macro[-1]
    deg = lambda a: (1 + a) * 50 + 12
    print(f"wrote {OUT}  ({len(text) / 1024:.0f} KB)")
    print(f"  seed-0 cloud 2025:  sep={s0['sep']:.3f}  aff={s0['aff']:.3f} "
          f"({deg(s0['aff']):.0f}deg)  identity={s0['identity_alignment']:.3f}")
    print(f"  6-seed mean 2025:   sep={mn['sep']:.3f}  aff={mn['aff']:.3f} "
          f"({deg(mn['aff']):.0f}deg)  identity={mn['identity_alignment']:.3f}")
    print(f"  (US arc 2025 ref:   sep~1.11  aff~-0.574 (~33deg)  identity~0.33)")


if __name__ == "__main__":
    main()
