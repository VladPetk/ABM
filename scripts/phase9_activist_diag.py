"""Phase 9 — diagnose whether emergence events are creating activist
sub-populations in the anes_full config."""
from __future__ import annotations

import os
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import numpy as np


def _worker(seed):
    from abm.pillars.historical_arc import build_engine, build_schedule
    from abm.pillars.schedule import run_to
    from scripts.phase9_anes_score import PRESETS

    eng = build_engine(seed=seed, **PRESETS["anes_full"])
    sched = build_schedule(
        factional_seeding=PRESETS["anes_full"].get("factional_seeding", False),
        faction_anchor_events=PRESETS["anes_full"].get("faction_anchor_events", True),
    )
    snapshots = {}
    for year, tick in [(2010, 102), (2020, 126)]:
        run_to(eng, sched, tick)
        snapshots[year] = []
        for a in eng.agents:
            snapshots[year].append({
                "pos": np.array(a.state.ideology, dtype=float),
                "party": a.state.attrs.get("party", -1),
                "faction": a.state.attrs.get("faction"),
                "faction_center": a.state.attrs.get("faction_center"),
                "stubbornness": float(a.state.attrs.get("stubbornness", 0.0)),
            })
    return snapshots


def main():
    from abm.calibration_parallel import run_seeds_parallel

    results = run_seeds_parallel(_worker, list(range(3)))

    for year in (2010, 2020):
        print(f"\n=== {year} (across 3 seeds, ~750 partisans/seed) ===")
        from collections import Counter
        all_factions = Counter()
        n_with_faction_center = 0
        n_total = 0
        positions_by_faction = {}
        for snap in results:
            for a in snap[year]:
                n_total += 1
                fac = a["faction"]
                all_factions[fac] += 1
                if a["faction_center"] is not None:
                    n_with_faction_center += 1
                positions_by_faction.setdefault(fac, []).append(a["pos"])

        for fac, count in sorted(all_factions.items(), key=lambda kv: -kv[1]):
            pct = 100.0 * count / n_total
            xy = np.array(positions_by_faction[fac])
            if len(xy) >= 5:
                mx, my = xy[:, 0].mean(), xy[:, 1].mean()
                print(f"  {str(fac):>20}  n={count:>4} ({pct:5.1f}%)  "
                      f"cent=({mx:+.3f}, {my:+.3f})")
            else:
                print(f"  {str(fac):>20}  n={count:>4} ({pct:5.1f}%)")
        print(f"  agents with faction_center attr: "
              f"{n_with_faction_center}/{n_total} "
              f"({100*n_with_faction_center/n_total:.1f}%)")


if __name__ == "__main__":
    main()
