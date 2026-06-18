"""Honesty budget accounting + T0.3 brake re-check.

Emergence-recovery E5.8 REFRAME (per user). The canonical config is the
ENDOGENOUS activist->elite->mass loop (ANES_FULL_KWARGS, endogenous_elite=True,
data_fed_elite=False). The earlier E5.2 panel claimed "wholly emergent / 0
empirical input" -- an overclaim: positions are not fed, but the loop's pace is
set by an ANES-CALIBRATED mobilization forcing, so empirical data still adjusts
the result. The honest split (the panel reads `free_flowing` + `empirical_input`):
  - free_flowing     : the mechanism with every EMPIRICAL/external driver removed
                       (mobilization frozen at 1980, no events, no media) -- the
                       all-frozen-no-events floor. The loop's own free dynamics.
  - empirical_input  : (rise_with - rise_sans)/rise_with -- how much the
                       ANES-calibrated forcing (mobilization timing + dated events
                       + media) ADJUSTS the free-flowing mechanism (= 1 -
                       free_flowing). This is FORCING/timing, NOT fed positions.
  - fed_positions    : the retired data-fed-POSITION instrument (~0) -- the
                       "feeding the answer" channel, gone on the endogenous config.

Diagnostics also reported: `loop_attributable` (share that collapses if the whole
loop is frozen -- shows the loop is necessary) and `forcing` (baseline vs
no-events). The empirical input here is exogenous TIMING/calibration, not the
answer (legitimate per the workstream principle) -- but it is NOT zero, and the
panel now shows it.

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

    print(f"{'metric':<20}{'b0':>7}{'base':>7}{'loopF':>7}{'allF':>7}{'noEv':>7}"
          f"{'free%':>8}{'emp.in%':>8}{'emp.val%':>9}{'loopAtt%':>9}{'fedPos%':>8}")
    # The honest decomposition the panel reads (user's formula, E5.8):
    #   free_flowing   = the mechanism running with every EMPIRICAL/external driver
    #                    removed (mobilization frozen at 1980, no events, no media)
    #                    -- the all-frozen-no-events floor. The loop's own dynamics.
    #   empirical_input = (rise_with - rise_sans) / rise_with -- how much the
    #                    ANES-calibrated forcing (mobilization timing + dated events
    #                    + media) ADJUSTS the free-flowing mechanism. = 1 - free_flowing.
    #   fed_positions  = the retired data-fed-POSITION instrument (~0): the
    #                    "feeding the answer" channel, gone on the endogenous config.
    #   loop_attributable = diagnostic: share that collapses if the whole loop is
    #                    frozen (shows the loop is necessary, not the empirical split).
    metrics_out = {}
    for m in METRICS:
        b0, b1 = start(m), fin("baseline", m)
        rise = b1 - b0
        safe = abs(rise) > 1e-9
        free_flowing = (fin("all_frozen", m) - b0) / rise if safe else 0
        empirical_input = 1.0 - free_flowing                  # (rise_w - rise_sans)/rise_w
        empirical_input_value = ((b1 - fin("all_frozen", m)) / b1
                                 if abs(b1) > 1e-9 else 0)     # value-based cross-check
        loop_attr = (b1 - fin("loop_frozen", m)) / rise if safe else 0
        fed_positions = (fin("sched_frozen", m) - fin("all_frozen", m)) / rise if safe else 0
        forcing = (b1 - fin("no_events", m)) / rise if safe else 0
        print(f"{m:<20}{b0:>7.3f}{b1:>7.3f}{fin('loop_frozen',m):>7.3f}"
              f"{fin('all_frozen',m):>7.3f}{fin('no_events',m):>7.3f}"
              f"{free_flowing:>8.2f}{empirical_input:>8.2f}{empirical_input_value:>9.2f}"
              f"{loop_attr:>9.2f}{fed_positions:>8.2f}")
        metrics_out[m] = {
            "b0": round(b0, 4), "b1": round(b1, 4),
            "free_flowing": round(free_flowing, 4),
            "empirical_input": round(empirical_input, 4),
            "empirical_input_value": round(empirical_input_value, 4),
            "fed_positions": round(fed_positions, 4),
            "loop_attributable": round(loop_attr, 4),
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
        "_provenance": "R-phase re-bless (2026-06-18, branch audit-surface-fixes) — "
                       "measure-then-bless on the R-PHASE canonical (ANES_FULL_KWARGS = "
                       "ANES_FULL_RPHASE_KWARGS: the common-mode-econ build + R5 media-direction "
                       "+ R7 affect rest state + P3a affect recal + mild R1 contact + R8 "
                       "endogenous mobilization endo_mob_gain=0.15), 6 seeds, methods §5.32. "
                       "vs the pre-R-phase numbers, party_sep free_flowing rose 0.28->0.34 "
                       "(empirical_input 0.72->0.66), driven by R8 (a party's own sorting feeds "
                       "its mobilization — the genuine fed->earned lever; R5 media is itself fed "
                       "so it does NOT raise emergence). The measured CAP on fit-compatible "
                       "emergence is ~0.39 (recal_fit.py / recal_budget_check.py): a stronger "
                       "spiral front-loads polarization and breaks the per-decade fit, because "
                       "US polarization TIMING is event-paced (blindspot #7, methods §5.32). "
                       "affect free_flowing ~0.83 (its own rest-state mechanism). The common-mode "
                       "channels remain rigid sorting-INVARIANT level shifts (not tracked here). "
                       "'free_flowing' = the "
                       "mechanism with every empirical/external driver removed "
                       "(all-frozen-no-events floor); 'empirical_input' = (rise_with - "
                       "rise_sans)/rise_with (= 1 - free_flowing). 'fed_positions' = the "
                       "retired data-fed-POSITION instrument (~0). 'loop_attributable'/"
                       "'forcing' are diagnostics. Reproduce: PYTHONPATH=. python "
                       "scripts/audit/t35_budget_brake.py",
        "seeds": len(SEEDS),
        "metrics": metrics_out,
        "events_brake": {"full_arc": round(base_sep, 4), "no_events": round(noev_sep, 4),
                         "survives": survives},
    }, indent=2) + "\n")
    print(f"\nwrote {OUT_JSON}")


if __name__ == "__main__":
    main()
