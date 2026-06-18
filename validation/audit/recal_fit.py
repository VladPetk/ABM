"""R-phase joint re-calibration — light local fit around the A6 feasibility point.

Not a from-scratch ABC: the feasibility probe already localized a strong region
(A6: §11 21/24, affect 3/5, sep 5/5, 40% mob cut). This grids the two levers that
matter — the fed→earned mob cut (how far can we push it) and the affect cooling
rate — at 5 seeds on the REAL §11 ANES bands, and SELECTS the most-emergent
(largest mob cut) point that still passes all targets. Everything else fixed at
the A6 corrections (R5 media, R7 rest, P3a saturation, mild R1).

Selection rule (pre-registered): among configs with §11 ≥ 18 AND affect ≥ 3/5 AND
party_sep ≥ 4/5, pick the LARGEST mob cut (most forcing removed = most emergent);
tie-break by §11 then affect.

Run: PYTHONPATH=. .venv/Scripts/python.exe validation/audit/recal_fit.py
"""
import sys
sys.path.insert(0, ".")
import json
from pathlib import Path
import numpy as np
from abm.pillars.historical_arc import build_engine, build_schedule
from abm.pillars.schedule import run_to
from scripts.phase8f_lib import (
    measure_all, aggregate, get_primary_targets, get_initial_targets_1980,
)
from scripts.phase9_anes_score import _score_cells, SECTION11_TICKS
from scripts.anes_preset import ANES_FULL_KWARGS

SEEDS = (0, 1, 2, 3, 4)
MOB0 = float(ANES_FULL_KWARGS.get("mob_peak", 2.4838))

# Fixed A6 corrections (shipped-arc: corrections on, strong restoring OFF).
FIXED = dict(
    media_centrifugal=0.7,
    affect_rest_rate=0.02, affect_rest_anchor=-0.30, affect_saturation=1.0,
    contact_warming=True, contact_coop_frac=0.3, contact_warm_threshold=-0.6,
    contact_warm_magnitude=0.04, contact_coop_share=0.15,
)
MOB_CUTS = [0.60, 0.70, 0.80, 0.90, 1.00]  # fraction of canonical mob_peak (fed→earned frontier)
LR_SCALES = [0.30]                          # P3a affect cooling rate (fixed; affect ~flat in lr)


def _traj(seed, extra):
    k = dict(ANES_FULL_KWARGS); k.update(extra)
    eng = build_engine(seed=seed, **k)
    sched = build_schedule(
        factional_seeding=k.get("factional_seeding", False),
        faction_anchor_events=k.get("faction_anchor_events", True),
        evidence_regrade=k.get("evidence_regrade", False),
        exogenous_shocks=k.get("exogenous_shocks", False))
    traj = {}
    for yr, tick in SECTION11_TICKS:
        if tick > 0:
            run_to(eng, sched, tick)
        traj[yr] = measure_all(eng)
    return traj


def _score(extra):
    anes_pri = get_primary_targets(use_anes_bands=True)
    anes_init = get_initial_targets_1980(use_anes_bands=True)
    means, ses = aggregate([_traj(s, extra) for s in SEEDS])
    _, _, n45, ninit, n24 = _score_cells(means, ses, anes_pri, anes_init)
    yrs = (1990, 2000, 2010, 2020, 2025)
    aff = sum(int(anes_pri[y]["affect"][0] <= means[y]["affect"] <= anes_pri[y]["affect"][1]) for y in yrs)
    sep = sum(int(anes_pri[y]["party_sep"][0] <= means[y]["party_sep"] <= anes_pri[y]["party_sep"][1]) for y in yrs)
    return dict(n24=n24, n45=n45, ninit=ninit, affect=aff, sep=sep,
                sep2025=means[2025]["party_sep"], aff2025=means[2025]["affect"])


def main():
    print("R-PHASE RE-CAL LIGHT FIT —", len(SEEDS), "seeds\n")
    ref = _score({})   # current shipped canonical, same seeds, for reference
    print(f"  [ref] CURRENT SHIPPED       | §11 {ref['n24']:>2}/24  aff {ref['affect']}/5  "
          f"sep {ref['sep']}/5  | 2025 sep {ref['sep2025']:+.3f} aff {ref['aff2025']:+.3f}\n")
    rows = []
    for cut in MOB_CUTS:
        for lr in LR_SCALES:
            extra = dict(FIXED, mob_peak=MOB0 * cut, affect_lr_scale=lr)
            s = _score(extra)
            s.update(cut=cut, lr=lr)
            rows.append(s)
            print(f"  mobcut {int((1-cut)*100):>2}%  lr {lr:.2f} | §11 {s['n24']:>2}/24  "
                  f"aff {s['affect']}/5  sep {s['sep']}/5  | 2025 sep {s['sep2025']:+.3f} "
                  f"aff {s['aff2025']:+.3f}")
    # selection: pass all targets, then LARGEST mob cut (= smallest cut fraction)
    passing = [r for r in rows if r["n24"] >= 18 and r["affect"] >= 3 and r["sep"] >= 4]
    if passing:
        best = sorted(passing, key=lambda r: (r["cut"], -r["n24"], -r["affect"]))[0]
        print(f"\nSELECTED (most emergent passing): mobcut {int((1-best['cut'])*100)}% "
              f"lr {best['lr']:.2f} → §11 {best['n24']}/24, aff {best['affect']}/5, sep {best['sep']}/5")
    else:
        best = sorted(rows, key=lambda r: (-r["n24"], -r["affect"], -r["sep"]))[0]
        print(f"\nNO config passed all targets; best §11 = {best['n24']}/24 "
              f"(mobcut {int((1-best['cut'])*100)}% lr {best['lr']:.2f})")
    adopted = dict(FIXED, mob_peak=MOB0 * best["cut"], affect_lr_scale=best["lr"])
    out = Path("validation/audit/recal_fit_result.json")
    out.write_text(json.dumps({"seeds": list(SEEDS), "rows": rows,
                               "selected": best, "adopted_overrides": adopted},
                              indent=2) + "\n")
    print(f"\n[adopted overrides] {adopted}")
    print(f"[wrote] {out}")


if __name__ == "__main__":
    main()
