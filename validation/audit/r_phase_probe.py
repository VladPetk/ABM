"""R-phase feasibility probe (NOT a bless) — does activating R1+R2:
  (a) perturb the canonical arc (the re-calibration burden), and
  (b) under a strong "Sweden-like" counterfactual, actually DEPOLARIZE
      (party_sep / affect peak then DECLINE) rather than just rise slower?

Single seed for the direction signal. Reuses the real measure_all. Engine
untouched — all via build_engine kwargs (R-phase knobs default off).
Run: .venv/Scripts/python.exe validation/audit/r_phase_probe.py
"""
import sys
sys.path.insert(0, ".")
import numpy as np
from abm.pillars.historical_arc import build_engine, build_schedule
from abm.pillars.schedule import run_to
from scripts.phase8f_lib import measure_all
from scripts.anes_preset import ANES_FULL_KWARGS

SNAPS = [(1990, 42), (2000, 72), (2010, 102), (2020, 126), (2025, 135)]

R_MOD = dict(contact_warming=True, contact_coop_frac=0.5, contact_warm_threshold=-0.6,
             contact_coop_share=0.3, xpressure_sorting_damp=0.4, xpressure_affect_damp=0.4)
R_STRONG = dict(contact_warming=True, contact_coop_frac=0.8, contact_warm_threshold=-1.0,
                contact_warm_magnitude=0.10, contact_coop_share=0.6,
                xpressure_sorting_damp=0.7, xpressure_affect_damp=0.7)
# "Sweden-like": strong restoring + weak polarizing drivers.
R_SWEDEN = dict(R_STRONG, mob_peak=0.8, elite_gain=1.0)

CONFIGS = [("baseline (R off)", {}),
           ("R-moderate", R_MOD),
           ("R-strong", R_STRONG),
           ("R-strong + low-forcing (Sweden-like)", R_SWEDEN)]


def run(extra):
    k = dict(ANES_FULL_KWARGS)
    k.update(extra)
    eng = build_engine(seed=0, **k)
    sched = build_schedule(
        factional_seeding=k.get("factional_seeding", False),
        faction_anchor_events=k.get("faction_anchor_events", True),
        evidence_regrade=k.get("evidence_regrade", False),
        exogenous_shocks=k.get("exogenous_shocks", False))
    traj = {}
    for yr, tick in SNAPS:
        run_to(eng, sched, tick)
        m = measure_all(eng)
        traj[yr] = (m["party_sep"], m["affect"], m["constraint"])
    return traj


def main():
    print("R-PHASE FEASIBILITY PROBE (seed 0)\n")
    rows = {}
    for name, extra in CONFIGS:
        rows[name] = run(extra)
        print("== " + name + " ==")
        for yr, _ in SNAPS:
            ps, af, co = rows[name][yr]
            print(f"   {yr}: party_sep {ps:+.3f}  affect {af:+.3f}  constraint {co:+.3f}")
        seps = [rows[name][yr][0] for yr, _ in SNAPS]
        peak = max(seps)
        end = seps[-1]
        reversed_ = end < peak - 0.03
        print(f"   -> sep peak {peak:.3f} @ { [y for y,_ in SNAPS][seps.index(peak)] }; "
              f"2025 {end:.3f}; {'DEPOLARIZES (peak->decline)' if reversed_ else 'monotone-ish'}\n")
    base = rows["baseline (R off)"]
    print("DELTA vs baseline @2025 (party_sep, affect):")
    for name, _ in CONFIGS[1:]:
        d_ps = rows[name][2025][0] - base[2025][0]
        d_af = rows[name][2025][1] - base[2025][1]
        print(f"   {name}: dsep {d_ps:+.3f}  daffect {d_af:+.3f}")


if __name__ == "__main__":
    main()
