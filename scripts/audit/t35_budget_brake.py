"""MHV S3 T3.5 — budget accounting (input-carried) + T0.3 brake re-check.

On the flipped substrate (data-fed elite + media inputs), decompose the
1980->2025 change per headline metric into:
  - emergent core  : survives all-schedules-frozen + inputs-frozen + no-events
  - input-carried  : the extra the data-fed series adds (inputs on vs frozen)
  - residual/events: the remainder (hand-drawn schedules + dated events)

and re-check T0.3 (events as a brake): does removing the dated events still let
separation run HIGHER than the full arc? (The brake must survive the media
re-expression.)

Run: PYTHONPATH=. .venv/Scripts/python.exe scripts/audit/t35_budget_brake.py
"""
from __future__ import annotations

import numpy as np

from abm.calibration_parallel import run_seeds_parallel
from scripts.audit.audit_lib import freeze_worker

SEEDS = tuple(range(6))
METRICS = ("party_sep", "affect", "identity_alignment")
SCHED_FREEZE = ("elite_drift", "identity_sorting", "coupling", "party_k",
                "social_media")
ALL_FREEZE = SCHED_FREEZE + ("data_fed_inputs",)


def main() -> None:
    # (freeze_tuple, schedule_mode) configs.
    cfgs = {
        "baseline":       ((), "full"),
        "sched_frozen":   (SCHED_FREEZE, "empty"),      # T2.6 emergent floor
        "all_frozen":     (ALL_FREEZE, "empty"),        # + inputs frozen
        "inputs_frozen":  (("data_fed_inputs",), "full"),  # only inputs off
        "no_events":      ((), "decade_only"),          # T0.3 brake
    }
    work = [(s, fr, mode) for (fr, mode) in cfgs.values() for s in SEEDS]
    flat = run_seeds_parallel(freeze_worker, work)
    # Regroup by config (run_seeds_parallel preserves order).
    runs = {}
    i = 0
    for name in cfgs:
        runs[name] = flat[i:i + len(SEEDS)]
        i += len(SEEDS)

    def fin(name, m):
        return float(np.mean([r["series"][-1][m] for r in runs[name]]))

    def start(m):
        return float(np.mean([r["series"][0][m] for r in runs["baseline"]]))

    print(f"{'metric':<20}{'b0':>8}{'base':>8}{'schedF':>8}{'allF':>8}"
          f"{'emerg%':>8}{'input%':>8}")
    for m in METRICS:
        b0, b1 = start(m), fin("baseline", m)
        rise = b1 - b0
        emerg = (fin("all_frozen", m) - b0) / rise if abs(rise) > 1e-9 else 0
        # input-carried = how much the inputs add on top of all-frozen
        inp = (fin("sched_frozen", m) - fin("all_frozen", m)) / rise if abs(rise) > 1e-9 else 0
        print(f"{m:<20}{b0:>8.3f}{b1:>8.3f}{fin('sched_frozen',m):>8.3f}"
              f"{fin('all_frozen',m):>8.3f}{emerg:>8.2f}{inp:>8.2f}")

    print("\n[T0.3 brake re-check] party_sep 2025:")
    base_sep = fin("baseline", "party_sep")
    noev_sep = fin("no_events", "party_sep")
    print(f"  full arc            = {base_sep:.3f}")
    print(f"  no dated events     = {noev_sep:.3f}")
    verdict = "SURVIVES (events still brake)" if noev_sep > base_sep else "BRAKE GONE"
    print(f"  {verdict}: removing events {'raises' if noev_sep>base_sep else 'lowers'} sep "
          f"by {noev_sep-base_sep:+.3f}")


if __name__ == "__main__":
    main()
