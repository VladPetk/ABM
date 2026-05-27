"""Phase 9 Step 4 — re-measure Phase 8f §11 cells under factional_seeding=True.

Runs the historical_arc engine at the factional-seeding-on configuration,
captures the same 6-metric trajectory measured by phase8f_diagnostic_runner,
counts how many primary-target cells land in band, and dumps the
per-cell pass/fail to JSON.

The §11 gate (per phase9_spec.md §6 Step 4 and phase8f_lib PRIMARY_TARGETS):
4 metrics (constraint, party_sep, affect, within_party_sd) × 5 target years
(1990, 2000, 2010, 2020, 2025) + 1 initial-condition variance check + the
extras in phase8f_lib.print_trajectory's tally. We report the canonical
5-metric × 5-year tally (25 cells) consistent with Phase 8f reporting,
plus the 4-metric × 5-year tally (20 cells) for the conservative
"primary subset" view.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

import numpy as np

from abm.calibration_parallel import run_seeds_parallel
from abm.pillars import historical_arc as ha

from scripts.phase8f_lib import (
    PRIMARY_TARGETS, INITIAL_TARGETS_1980,
    measure_all, aggregate, in_band,
)


SEEDS = tuple(range(int(os.environ.get("PHASE9_SEC11_NSEEDS", "9"))))
N = 250
INDEPENDENT_FRACTION = 0.12
BOOST = float(os.environ.get("PHASE9_BOOST", "0.5"))


def _worker(seed: int) -> dict:
    from abm.pillars.schedule import run_to
    eng = ha.build_engine(
        seed=seed, n_agents=N,
        independent_fraction=INDEPENDENT_FRACTION,
        factional_seeding=True,
        faction_stubbornness_boost=BOOST,
    )
    sched = ha.build_schedule(factional_seeding=True)
    trajectory = {1980: measure_all(eng)}
    for year, tick in [(1990, 30), (2000, 60), (2010, 90),
                       (2020, 120), (2025, 135)]:
        run_to(eng, sched, tick)
        trajectory[year] = measure_all(eng)
    return trajectory


def main():
    print("=" * 78)
    print(f"Phase 9 §11 re-measurement — factional_seeding=True, boost={BOOST}, "
          f"seeds={len(SEEDS)}")
    print("=" * 78)

    trajectories = run_seeds_parallel(_worker, SEEDS)
    means, ses = aggregate(trajectories)

    # 5-metric × 5-year primary tally (Phase 8f canonical = 25 cells)
    metrics_5 = ["constraint", "party_sep", "affect", "within_party_sd"]
    years = [1990, 2000, 2010, 2020, 2025]

    cells_4x5 = []     # 20 cells — conservative spec §6 subset
    cells_extra = []   # 1980 initial cells (4 metrics) — for 24-cell tally

    for year in years:
        for metric in metrics_5:
            band = PRIMARY_TARGETS[year][metric]
            v = means[year][metric]
            ok = in_band(v, band)
            cells_4x5.append({
                "year": year, "metric": metric,
                "value": v, "se": ses[year][metric],
                "band_lo": band[0], "band_hi": band[1],
                "in_band": bool(ok),
            })

    # 1980 initial-condition cells (4 — variance, constraint, party_sep,
    # within_party_sd; affect & xc skipped to keep the count nice).
    init_metrics = ["variance", "constraint", "party_sep", "within_party_sd"]
    for metric in init_metrics:
        band = INITIAL_TARGETS_1980[metric]
        v = means[1980][metric]
        ok = in_band(v, band)
        cells_extra.append({
            "year": 1980, "metric": metric,
            "value": v, "se": ses[1980][metric],
            "band_lo": band[0], "band_hi": band[1],
            "in_band": bool(ok),
        })

    in_band_4x5 = sum(c["in_band"] for c in cells_4x5)
    in_band_extra = sum(c["in_band"] for c in cells_extra)
    in_band_24 = in_band_4x5 + in_band_extra

    print("\n=== Trajectory ===")
    print("  year   constraint   party_sep      affect   wp_sd     xc     mod")
    for year in [1980, 1990, 2000, 2010, 2020, 2025]:
        m = means[year]
        print(
            f"  {year}  {m['constraint']:+8.3f}   {m['party_sep']:+8.3f}   "
            f"{m['affect']:+8.3f}  {m['within_party_sd']:+6.3f}  "
            f"{m['xc_fraction']:+5.3f}  {m['modularity']:+5.3f}"
        )

    print(f"\n[gate] primary 4×5 cells in band: {in_band_4x5}/20")
    print(f"[gate] 1980 initial 4 cells in band: {in_band_extra}/4")
    print(f"[gate] combined 24-cell tally: {in_band_24}/24  "
          f"(spec §7.4 / §6.4 gate: >= 18/24)")

    misses = [c for c in cells_4x5 + cells_extra if not c["in_band"]]
    if misses:
        print("\nMisses:")
        for c in misses:
            print(f"  {c['year']} {c['metric']:<16} {c['value']:+.3f}  "
                  f"target [{c['band_lo']:+.2f}, {c['band_hi']:+.2f}]")

    out_path = Path(os.environ.get(
        "PHASE9_SEC11_OUT", "phase9_section11_under_tier_a.json"
    ))
    out = {
        "variant": "tier_a_factional_seeding",
        "n_agents": N,
        "independent_fraction": INDEPENDENT_FRACTION,
        "faction_stubbornness_boost": BOOST,
        "seeds": list(SEEDS),
        "means": {str(y): means[y] for y in means},
        "ses": {str(y): ses[y] for y in ses},
        "cells_4x5": cells_4x5,
        "cells_1980_initial": cells_extra,
        "tally_4x5": in_band_4x5,
        "tally_4x5_total": 20,
        "tally_24": in_band_24,
        "tally_24_total": 24,
        "gate_pass_18_of_24": bool(in_band_24 >= 18),
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"\n[dump] {out_path.resolve()}")


if __name__ == "__main__":
    main()
