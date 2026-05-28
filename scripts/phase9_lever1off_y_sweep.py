"""Phase 9 §11.4 — Lever 1 OFF + Lever 2 y-magnitude sweep.

The single-lever ablation showed:
  - Tier D all-on: §11=13/24, var_y_2020=0.096
  - Tier D minus lever 1: §11=15/24 (+2), var_y_2020=0.079
  - Tier D minus lever 4: §11=13/24 (no change — lever 4 inert)
  - Tier D minus lever 6: §11=13/24 (no change — lever 6 inert)

So Lever 1 is partially responsible, but most of the §11 break is from
Lever 2 (the expanded y-centroid). This script runs Lever 1 OFF + Lever 2
swept over y ∈ {0.08, 0.10, 0.12, 0.15, 0.20} to find a sweet spot that
trades a small §11 cost for the largest var_y gain.

Anchor points: y=0.08 is the pre-Tier-D Phase 8f value; y=0.20 is Tier D
central. So we're effectively bracketing.

Output: docs/results/phase9_lever1off_y_sweep.json
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import numpy as np

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

SEEDS = tuple(range(3))
N = 250
INDEPENDENT_FRACTION = 0.12
STRENGTH = 0.04
BUMP = 1.0

DECADE_TICKS = [(1980, 0), (1990, 30), (2000, 60), (2010, 90), (2020, 120)]
SECTION11_TICKS = [(1990, 30), (2000, 60), (2010, 90),
                   (2020, 120), (2025, 135)]

Y_MAGNITUDES = [0.08, 0.10, 0.12, 0.15, 0.20]


def _worker(args):
    y_mag, seed = args
    from abm.pillars.historical_arc import build_engine, build_schedule
    from abm.pillars.schedule import run_to
    from scripts.phase8f_lib import measure_all

    eng = build_engine(
        seed=seed, n_agents=N,
        independent_fraction=INDEPENDENT_FRACTION,
        factional_seeding=False,
        faction_anchor_strength=STRENGTH,
        faction_anchor_events=True,
        event_stubbornness_bump_multiplier=BUMP,
        tier_d_axis_balance=True,
        tier_d_lever1_off=True,           # ← Lever 1 disabled
        tier_d_party_center_y=y_mag,      # ← Lever 2 swept
        tier_d_coupling_rho=0.0,          # use independent draws
    )
    sched = build_schedule(factional_seeding=False, faction_anchor_events=True)

    snapshots = {1980: np.array([a.state.ideology for a in eng.agents], dtype=float)}
    trajectory = {1980: measure_all(eng)}
    year_at_tick = {}
    for y, t in DECADE_TICKS:
        year_at_tick.setdefault(t, []).append(("w2", y))
    for y, t in SECTION11_TICKS:
        year_at_tick.setdefault(t, []).append(("s11", y))
    for tick in sorted(year_at_tick):
        if tick == 0:
            continue
        run_to(eng, sched, tick)
        for kind, year in year_at_tick[tick]:
            if kind == "w2":
                snapshots[year] = np.array(
                    [a.state.ideology for a in eng.agents], dtype=float
                )
            else:
                trajectory[year] = measure_all(eng)
    return {
        "y_mag": y_mag, "seed": seed,
        "snapshots": {k: v.tolist() for k, v in snapshots.items()},
        "trajectory": trajectory,
    }


def main():
    from concurrent.futures import ProcessPoolExecutor
    from abm.calibration_phase9 import (
        EMPIRICAL_DECADES, score_engine_run,
    )
    from scripts.phase8f_lib import (
        PRIMARY_TARGETS, INITIAL_TARGETS_1980, aggregate, in_band,
    )

    tasks = [(y, s) for y in Y_MAGNITUDES for s in SEEDS]
    print(f"Running {len(tasks)} tasks ({len(Y_MAGNITUDES)} y × {len(SEEDS)} seeds)")
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=min(os.cpu_count() or 1, len(tasks))) as ex:
        results = list(ex.map(_worker, tasks))
    print(f"All workers done in {time.time() - t0:.1f}s")

    by_y = {y: [] for y in Y_MAGNITUDES}
    for r in results:
        by_y[r["y_mag"]].append(r)

    all_rows = []
    for y in Y_MAGNITUDES:
        rs = sorted(by_y[y], key=lambda x: x["seed"])
        trajectories = [r["trajectory"] for r in rs]
        means, ses = aggregate(trajectories)

        cells_4x5 = 0
        for year in [1990, 2000, 2010, 2020, 2025]:
            for m in ["constraint", "party_sep", "affect", "within_party_sd"]:
                band = PRIMARY_TARGETS[year][m]
                if in_band(means[year][m], band):
                    cells_4x5 += 1
        cells_init = 0
        cells_init_detail = {}
        for m in ["variance", "constraint", "party_sep", "within_party_sd"]:
            band = INITIAL_TARGETS_1980[m]
            ok = in_band(means[1980][m], band)
            cells_init_detail[m] = {"value": means[1980][m], "band": band, "in_band": ok}
            if ok:
                cells_init += 1
        n_24 = cells_4x5 + cells_init

        # Wasserstein
        per_seed_dfs = []
        for r in rs:
            snaps = {int(k): np.array(v) for k, v in r["snapshots"].items()}
            df = score_engine_run(
                positions_by_decade=snaps,
                target_dir=Path("data/phase9_empirical"),
                seed_for_subsample=r["seed"],
            )
            df.insert(0, "seed", r["seed"])
            per_seed_dfs.append(df)
        import pandas as pd
        combined = pd.concat(per_seed_dfs, ignore_index=True)

        per_decade = {}
        w2_total = 0.0
        for decade in EMPIRICAL_DECADES:
            sub = combined[combined["decade"] == decade]
            w_mean = float(sub["wasserstein"].mean())
            per_decade[str(decade)] = {
                "wasserstein_mean": w_mean,
                "corr_xy_mean": float(sub["corr_xy"].mean()),
                "var_x_mean": float(sub["var_x"].mean()),
                "var_y_mean": float(sub["var_y"].mean()),
            }
            w2_total += w_mean

        row = {
            "y_mag": y,
            "cells_in_band": n_24,
            "cells_4x5": cells_4x5,
            "cells_init": cells_init,
            "cells_init_detail": cells_init_detail,
            "w2_total": w2_total,
            "per_decade": per_decade,
            "trajectory_means": {str(yr): means[yr] for yr in means},
        }
        all_rows.append(row)
        print(f"  [y={y:.2f}] §11={n_24}/24 (4x5={cells_4x5}, init={cells_init})  "
              f"w2={w2_total:.3f}  var_y_2020={per_decade['2020']['var_y_mean']:.3f}  "
              f"corr_2020={per_decade['2020']['corr_xy_mean']:+.3f}")

    out_path = Path("docs/results/phase9_lever1off_y_sweep.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(all_rows, indent=2))
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
