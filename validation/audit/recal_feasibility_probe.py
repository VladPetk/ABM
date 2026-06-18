"""Joint re-calibration FEASIBILITY probe (NOT a fit, NOT a bless).

Before the expensive full ABC fit + re-bless cascade, confirm the two key targets
are JOINTLY reachable with the R-phase corrections on:

  Q1 (affect): can R7 (rest state) + P3a (affect_lr_scale) + mild R1 (contact)
     land out-party affect IN the ANES bands WITHOUT breaking §11 (party_sep /
     constraint / within_party_sd)?  [the audit said affect is ~orthogonal to
     position metrics — verify with the mechanisms actually on the arc]
  Q2 (fed→earned): with R5 media now CENTRIFUGAL (carrying real positional
     sorting), can we CUT the mob_* forcing and keep party_sep in band? Each
     mob-cut level that still scores §11 is forcing the arc LESS = more emergent.

Design note: the SHIPPED US arc keeps the CORRECTIONS on (R5 media-direction, R7
rest, P3a) + MILD R1 contact, but the strong position-restoring forces (R2/R3/R4/
R6) stay near-off — those are the depolarization CAPACITY (proven generically in
the G1 battery), not active brakes in a society that did polarize. So the probe
candidates are NOT the G1 "strong restoring" configs.

Scored on the REAL §11 ANES bands (scripts/phase9_anes_score._score_cells). Cheap:
few seeds, measure only at the §11 ticks. Engine untouched; canonical bit-identical.

Run: PYTHONPATH=. .venv/Scripts/python.exe validation/audit/recal_feasibility_probe.py
"""
import sys
sys.path.insert(0, ".")
import numpy as np
from abm.pillars.historical_arc import build_engine, build_schedule
from abm.pillars.schedule import run_to
from scripts.phase8f_lib import (
    measure_all, aggregate, get_primary_targets, get_initial_targets_1980,
)
from scripts.phase9_anes_score import _score_cells, SECTION11_TICKS
from scripts.anes_preset import ANES_FULL_KWARGS

SEEDS = (0, 1, 2)
MOB_PEAK_CANON = float(ANES_FULL_KWARGS.get("mob_peak", 2.4838))

# --- affect corrections (always-on in the shipped re-cal): R7 + P3a + mild R1 ---
AFFECT_FIX = dict(
    affect_rest_rate=0.02, affect_rest_anchor=-0.30,   # R7 — affect equilibrium
    affect_lr_scale=0.5,                               # P3a — less over-cooling
    contact_warming=True, contact_coop_frac=0.3,       # R1 — mild contact warming
    contact_warm_threshold=-0.6, contact_warm_magnitude=0.04, contact_coop_share=0.15,
)
MEDIA_FIX = dict(media_centrifugal=0.7)                # R5 part A — media polarizes position

CANDS = {
    "A0_canonical": {},
    "A1_affectfix": dict(AFFECT_FIX),
    "A2_media+affect": dict(AFFECT_FIX, **MEDIA_FIX),
    "A3_media+affect+mobcut20": dict(AFFECT_FIX, **MEDIA_FIX, mob_peak=MOB_PEAK_CANON * 0.80),
    "A4_media+affect+mobcut40": dict(AFFECT_FIX, **MEDIA_FIX, mob_peak=MOB_PEAK_CANON * 0.60),
    # A5 — A4 with the affect knobs pushed harder, to gauge the affect-cells ceiling.
    "A5_strongaffect+mobcut40": dict(
        affect_rest_rate=0.035, affect_rest_anchor=-0.38, affect_lr_scale=0.30,
        contact_warming=True, contact_coop_frac=0.5, contact_warm_threshold=-0.6,
        contact_warm_magnitude=0.06, contact_coop_share=0.25,
        media_centrifugal=0.7, mob_peak=MOB_PEAK_CANON * 0.60),
}


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


def main():
    print("RE-CAL FEASIBILITY PROBE — seeds", SEEDS, "(NOT a fit)\n")
    anes_pri = get_primary_targets(use_anes_bands=True)
    anes_init = get_initial_targets_1980(use_anes_bands=True)
    aff_band = {y: anes_pri[y]["affect"] for y in (1990, 2000, 2010, 2020, 2025)}
    sep_band = {y: anes_pri[y]["party_sep"] for y in (1990, 2000, 2010, 2020, 2025)}

    for name, extra in CANDS.items():
        trajs = [_traj(s, extra) for s in SEEDS]
        means, ses = aggregate(trajs)
        _, _, n45, ninit, n24 = _score_cells(means, ses, anes_pri, anes_init)
        # affect cells in band (of 5)
        aff_in = sum(int(aff_band[y][0] <= means[y]["affect"] <= aff_band[y][1])
                     for y in aff_band)
        sep_in = sum(int(sep_band[y][0] <= means[y]["party_sep"] <= sep_band[y][1])
                     for y in sep_band)
        aff25 = means[2025]["affect"]; sep25 = means[2025]["party_sep"]
        print(f"== {name} ==")
        print(f"   §11 ANES: {n24}/24  ({n45}/20 main + {ninit}/4 IC)  "
              f"{'PASS' if n24 >= 18 else 'FAIL'}(>=18)")
        print(f"   affect cells in band: {aff_in}/5   (2025 affect {aff25:+.3f}, "
              f"band {aff_band[2025]})")
        print(f"   party_sep cells in band: {sep_in}/5  (2025 sep {sep25:+.3f}, "
              f"band {sep_band[2025]})\n")


if __name__ == "__main__":
    main()
