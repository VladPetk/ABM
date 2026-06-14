"""Honesty budget accounting + T0.3 brake re-check.

Emergence-recovery E5.2 REFRAME. The canonical config is now the ENDOGENOUS
activist->elite->mass loop (ANES_FULL_KWARGS, endogenous_elite=True,
data_fed_elite=False), so the budget question changes from "how much of the
rise is the fed answer" to "how much is produced by the endogenous mechanism."
Per headline metric, the 1980->2025 change is decomposed into:
  - emergent      : LOOP-ATTRIBUTABLE -- the share that COLLAPSES when the
                    endogenous loop is frozen (loop-off counterfactual,
                    `endogenous_loop` freeze). This is the emergence WIN for
                    party_sep (was ~0 input-carried on the FED config).
  - input_carried : the data-fed-input instrument (inputs-on vs inputs-frozen).
                    On the endogenous config NO positions are fed, so this is
                    ~0 by construction (the fed-answer channel is gone).
  - residual      : the remainder (BC / identity / noise drift + how the
                    exogenous event-timed mobilization forcing is accounted).

Diagnostics also reported: `spontaneous_floor` (the OLD all-frozen definition of
emergent -- the loop's floor at 1980 mobilization with no event forcing) and
`forcing` (the share the dated-event mobilization ramp adds, baseline vs
no-events). The mobilization forcing is exogenous TIMING, not positions
(legitimate per the workstream principle).

T0.3 brake re-check: does removing the dated events still let separation run
HIGHER than the full arc? (The brake must survive on the endogenous config too.)

Run: PYTHONPATH=. .venv/Scripts/python.exe scripts/audit/t35_budget_brake.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from abm.calibration_parallel import run_seeds_parallel
from scripts.audit.audit_lib import freeze_worker

OUT_JSON = Path(__file__).resolve().parents[2] / "docs" / "results" / "honesty_budget.json"

SEEDS = tuple(range(6))
METRICS = ("party_sep", "affect", "identity_alignment")
SCHED_FREEZE = ("elite_drift", "identity_sorting", "coupling", "party_k",
                "social_media")
ALL_FREEZE = SCHED_FREEZE + ("data_fed_inputs",)


def main() -> None:
    # (freeze_tuple, schedule_mode) configs.
    cfgs = {
        "baseline":       ((), "full"),
        "loop_frozen":    (("endogenous_loop",), "full"),  # E5.2 loop-off counterfactual
        "sched_frozen":   (SCHED_FREEZE, "empty"),      # loop-on, no forcing (spontaneous floor)
        "all_frozen":     (ALL_FREEZE, "empty"),        # + inputs frozen
        "inputs_frozen":  (("data_fed_inputs",), "full"),  # only inputs off (~baseline now)
        "no_events":      ((), "decade_only"),          # T0.3 brake / forcing
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

    print(f"{'metric':<20}{'b0':>7}{'base':>7}{'loopF':>7}{'schedF':>7}"
          f"{'allF':>7}{'noEv':>7}{'emerg%':>8}{'input%':>8}{'resid%':>8}{'spont%':>8}")
    # Headline "emergent" is the metric's PRIMARY generative-mechanism share.
    # For party_sep / identity_alignment that mechanism is the endogenous loop
    # (loop-off counterfactual). For affect it is its own AffectiveUpdate rule,
    # which is loop-independent, so its emergent basis is the all-frozen
    # spontaneous floor (the loop-off number would understate it). Both bases
    # are reported per metric so the choice is fully auditable.
    LOOP_BASIS = {"party_sep", "identity_alignment"}
    metrics_out = {}
    for m in METRICS:
        b0, b1 = start(m), fin("baseline", m)
        rise = b1 - b0
        safe = abs(rise) > 1e-9
        # candidate bases:
        loop_attr = (b1 - fin("loop_frozen", m)) / rise if safe else 0  # loop-off
        spont = (fin("all_frozen", m) - b0) / rise if safe else 0       # all-frozen floor
        basis = "loop" if m in LOOP_BASIS else "spontaneous"
        emerg = loop_attr if basis == "loop" else spont
        # input_carried = the data-fed-input instrument (now ~0; no fed positions).
        inp = (fin("sched_frozen", m) - fin("all_frozen", m)) / rise if safe else 0
        resid = 1.0 - emerg - inp
        forcing = (b1 - fin("no_events", m)) / rise if safe else 0  # event-timed mobilization
        print(f"{m:<20}{b0:>7.3f}{b1:>7.3f}{fin('loop_frozen',m):>7.3f}"
              f"{fin('sched_frozen',m):>7.3f}{fin('all_frozen',m):>7.3f}"
              f"{fin('no_events',m):>7.3f}{emerg:>8.2f}{inp:>8.2f}{resid:>8.2f}{spont:>8.2f}")
        metrics_out[m] = {
            "b0": round(b0, 4), "b1": round(b1, 4),
            "emergent": round(emerg, 4),
            "input_carried": round(inp, 4),
            "residual": round(resid, 4),
            "grounded": round(emerg + inp, 4),
            "emergent_basis": basis,
            "loop_attributable": round(loop_attr, 4),
            "spontaneous_floor": round(spont, 4),
            "loop_frozen": round(fin("loop_frozen", m), 4),
            "forcing": round(forcing, 4),
        }

    print("\n[T0.3 brake re-check] party_sep 2025:")
    base_sep = fin("baseline", "party_sep")
    noev_sep = fin("no_events", "party_sep")
    print(f"  full arc            = {base_sep:.3f}")
    print(f"  no dated events     = {noev_sep:.3f}")
    survives = noev_sep > base_sep
    verdict = "SURVIVES (events still brake)" if survives else "BRAKE GONE"
    print(f"  {verdict}: removing events {'raises' if survives else 'lowers'} sep "
          f"by {noev_sep-base_sep:+.3f}")

    OUT_JSON.write_text(json.dumps({
        "_provenance": "Emergence-recovery E5.2 honesty budget — measure-then-bless on "
                       "the ENDOGENOUS canonical config (ANES_FULL_KWARGS, "
                       "endogenous_elite, the adopted E4 ABC point), 6 seeds. "
                       "'emergent' = loop-attributable (endogenous_loop freeze, loop-off "
                       "counterfactual); 'input_carried' = data-fed-input instrument "
                       "(~0: no positions fed). 'spontaneous_floor'/'forcing' are "
                       "diagnostics. Reproduce: PYTHONPATH=. python "
                       "scripts/audit/t35_budget_brake.py",
        "seeds": len(SEEDS),
        "metrics": metrics_out,
        "events_brake": {"full_arc": round(base_sep, 4), "no_events": round(noev_sep, 4),
                         "survives": survives},
    }, indent=2) + "\n")
    print(f"\nwrote {OUT_JSON}")


if __name__ == "__main__":
    main()
