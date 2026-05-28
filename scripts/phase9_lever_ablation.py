"""Phase 9 §11.4 — Lever 1/4/6 ablation diagnostic.

The §11 forensics (TC blessed vs TD central JSON diff) strongly point at
Lever 1 (party assignment sigmoid reading y) as the §11 killer: all five
decade-constraint cells go HIGH under Tier D, and that is mechanically
what lever 1 produces. This script runs the diagnostic empirically.

Four configs at 5 seeds each:
  - Tier D all on (= Tier D central reproduction, sanity-check baseline)
  - Tier D minus lever 1 (master on, lever1_off=True)
  - Tier D minus lever 4 (master on, lever4_off=True)
  - Tier D minus lever 6 (master on, lever6_off=True)

For each, score §11 cells + per-decade Wasserstein. Compare to Tier D
central (all 6 on) and Tier C blessed (all 0 on).

Output: docs/results/phase9_lever_ablation.json
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


SEEDS = tuple(range(3))  # 3 seeds for diagnostic — sandbox has 2 CPUs
N = 250
INDEPENDENT_FRACTION = 0.12
STRENGTH = 0.04        # Tier C blessed
BUMP = 1.0             # Tier C blessed

DECADE_TICKS = [(1980, 0), (1990, 30), (2000, 60), (2010, 90), (2020, 120)]
SECTION11_TICKS = [(1990, 30), (2000, 60), (2010, 90), (2020, 120), (2025, 135)]


def _config_worker(args):
    """Worker function: (config_label, seed) → result dict.

    Spawned via ProcessPoolExecutor; imports are inside to avoid
    cross-process import-state contamination (parallel spec).
    """
    config_label, seed = args
    from abm.pillars.historical_arc import build_engine, build_schedule
    from abm.pillars.schedule import run_to
    from scripts.phase8f_lib import measure_all

    # Configure the ablation
    extra_kwargs = {
        "tier_d_all_on": {},
        "tier_d_minus_lever1": {"tier_d_lever1_off": True},
        "tier_d_minus_lever4": {"tier_d_lever4_off": True},
        "tier_d_minus_lever6": {"tier_d_lever6_off": True},
    }[config_label]

    eng = build_engine(
        seed=seed, n_agents=N,
        independent_fraction=INDEPENDENT_FRACTION,
        factional_seeding=False,
        faction_anchor_strength=STRENGTH,
        faction_anchor_events=True,
        event_stubbornness_bump_multiplier=BUMP,
        tier_d_axis_balance=True,
        **extra_kwargs,
    )
    sched = build_schedule(
        factional_seeding=False, faction_anchor_events=True,
    )

    snapshots = {}
    trajectory = {1980: measure_all(eng)}
    snapshots[1980] = np.array([a.state.ideology for a in eng.agents], dtype=float)

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
        "config_label": config_label,
        "seed": seed,
        "snapshots": {k: v.tolist() for k, v in snapshots.items()},
        "trajectory": trajectory,
    }


def main():
    from concurrent.futures import ProcessPoolExecutor
    from abm.calibration_phase9 import (
        EMPIRICAL_DECADES, score_engine_run, pot_available,
    )
    from scripts.phase8f_lib import (
        PRIMARY_TARGETS, INITIAL_TARGETS_1980, aggregate, in_band,
    )

    configs = [
        "tier_d_all_on",
        "tier_d_minus_lever1",
        "tier_d_minus_lever4",
        "tier_d_minus_lever6",
    ]
    tasks = [(c, s) for c in configs for s in SEEDS]
    print(f"Lever ablation: {len(tasks)} tasks ({len(configs)} configs × {len(SEEDS)} seeds)")
    print(f"POT available: {pot_available()}")

    t0 = time.time()
    with ProcessPoolExecutor(max_workers=min(os.cpu_count() or 1, len(tasks))) as ex:
        results = list(ex.map(_config_worker, tasks))
    print(f"All workers done in {time.time() - t0:.1f}s")

    # Group by config
    by_config = {c: [] for c in configs}
    for r in results:
        by_config[r["config_label"]].append(r)

    all_summaries = []
    for config_label in configs:
        rs = by_config[config_label]
        rs.sort(key=lambda x: x["seed"])

        # §11 — aggregate per-config trajectories
        trajectories = [r["trajectory"] for r in rs]
        means, ses = aggregate(trajectories)
        years = [1990, 2000, 2010, 2020, 2025]
        metrics_5 = ["constraint", "party_sep", "affect", "within_party_sd"]
        cells_4x5 = []
        for year in years:
            for m in metrics_5:
                band = PRIMARY_TARGETS[year][m]
                v = means[year][m]
                cells_4x5.append({
                    "year": year, "metric": m, "value": v,
                    "band_lo": band[0], "band_hi": band[1],
                    "in_band": bool(in_band(v, band)),
                })
        init_metrics = ["variance", "constraint", "party_sep", "within_party_sd"]
        cells_init = []
        for m in init_metrics:
            band = INITIAL_TARGETS_1980[m]
            v = means[1980][m]
            cells_init.append({
                "year": 1980, "metric": m, "value": v,
                "band_lo": band[0], "band_hi": band[1],
                "in_band": bool(in_band(v, band)),
            })
        n_4x5 = sum(c["in_band"] for c in cells_4x5)
        n_init = sum(c["in_band"] for c in cells_init)
        n_24 = n_4x5 + n_init

        # Wasserstein per decade — use score_engine_run on each seed
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

        summary = {
            "config_label": config_label,
            "n_seeds": len(rs),
            "cells_in_band": n_24,
            "cells_total": 24,
            "gate_pass_18_of_24": n_24 >= 18,
            "cells_4x5": cells_4x5,
            "cells_1980_initial": cells_init,
            "per_decade": per_decade,
            "w2_total": w2_total,
            "means": {str(y): means[y] for y in means},
        }
        all_summaries.append(summary)
        print(f"  [{config_label:<25}] §11={n_24}/24  "
              f"w2_total={w2_total:.3f}  "
              f"2020 var(y)={per_decade['2020']['var_y_mean']:.3f}  "
              f"2020 corr={per_decade['2020']['corr_xy_mean']:+.3f}")

    out_path = Path("docs/results/phase9_lever_ablation.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(all_summaries, indent=2))
    print(f"\nWrote {out_path}")

    # Headline
    print("\nHeadline (compare to Tier C blessed: §11=21/24, w2_total=1.809; ")
    print("Tier D central per saved JSON: §11=13/24, w2_total=1.672)")
    print(f"{'config':<30} {'§11':>6} {'w2_total':>9} {'var_y_2020':>11} {'corr_2020':>10}")
    print("-" * 70)
    for s in all_summaries:
        print(f"{s['config_label']:<30} {s['cells_in_band']:>3}/24 "
              f"{s['w2_total']:>9.3f} "
              f"{s['per_decade']['2020']['var_y_mean']:>11.3f} "
              f"{s['per_decade']['2020']['corr_xy_mean']:>+10.3f}")


if __name__ == "__main__":
    main()
