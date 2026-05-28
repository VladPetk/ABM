"""Phase 9 §11.7-B — Sweep tier_d_anes_drift_multiplier ×
tier_d_anes_sigma_pc_multiplier to find the best Phase B operating
point against ANES bands. Parallel by seed.

Grid (default):
  drift_mult ∈ {1.0, 1.75, 2.5, 3.5}
  sigma_pc_mult ∈ {1.0, 1.3, 1.6}

Each cell runs N seeds in parallel and scores against ANES bands.
Best cell = max(§11_ANES tally) with w2_total as tiebreaker.

Output:
  docs/results/phase9_anes_sweep.json
  docs/results/phase9_anes_sweep_winner.json
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

import numpy as np

N = 250
INDEPENDENT_FRACTION = 0.12

DECADE_TICKS = [
    (1980, 0), (1990, 30), (2000, 60), (2010, 90), (2020, 120),
]
SECTION11_TICKS = [
    (1990, 30), (2000, 60), (2010, 90), (2020, 120), (2025, 135),
]


def _build_kwargs(drift_m, sigma_m):
    return dict(
        n_agents=N,
        independent_fraction=INDEPENDENT_FRACTION,
        factional_seeding=False,
        faction_anchor_strength=0.04,
        faction_anchor_events=True,
        event_stubbornness_bump_multiplier=1.0,
        tier_d_axis_balance=True,
        tier_d_lever1_off=True,
        tier_d_cohort_y_signs_fix=True,
        tier_d_anes_knobs=True,
        tier_d_anes_drift_multiplier=drift_m,
        tier_d_anes_sigma_pc_multiplier=sigma_m,
    )


def _worker(args):
    """args = (seed, drift_m, sigma_m)"""
    seed, drift_m, sigma_m = args
    from abm.pillars.historical_arc import build_engine, build_schedule
    from abm.pillars.schedule import run_to
    from scripts.phase8f_lib import measure_all

    eng = build_engine(seed=seed, **_build_kwargs(drift_m, sigma_m))
    sched = build_schedule(
        factional_seeding=False, faction_anchor_events=True,
    )

    snapshots = {}
    trajectory = {1980: measure_all(eng)}
    snapshots[1980] = np.array(
        [a.state.ideology for a in eng.agents], dtype=float
    )
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
    return {"snapshots": snapshots, "trajectory": trajectory}


def _score_cell(results, seeds):
    """Compute w2 + §11 tallies (ANES) for a list of per-seed results."""
    from abm.calibration_phase9 import (
        EMPIRICAL_DECADES, score_engine_run,
    )
    from scripts.phase8f_lib import (
        get_primary_targets, get_initial_targets_1980, aggregate, in_band,
    )
    import pandas as pd

    per_seed_dfs = []
    for seed, res in zip(seeds, results):
        df = score_engine_run(
            positions_by_decade=res["snapshots"],
            target_dir=Path("data/phase9_empirical"),
            seed_for_subsample=seed,
        )
        df.insert(0, "seed", seed)
        per_seed_dfs.append(df)
    combined = pd.concat(per_seed_dfs, ignore_index=True)
    w2_total = 0.0
    per_decade = {}
    for decade in EMPIRICAL_DECADES:
        sub = combined[combined["decade"] == decade]
        w_mean = float(sub["wasserstein"].mean())
        per_decade[str(decade)] = {
            "w2_mean": w_mean,
            "corr_xy": float(sub["corr_xy"].mean()),
            "var_x": float(sub["var_x"].mean()),
            "var_y": float(sub["var_y"].mean()),
        }
        w2_total += w_mean

    trajectories = [r["trajectory"] for r in results]
    means, ses = aggregate(trajectories)
    anes_pri = get_primary_targets(use_anes_bands=True)
    anes_init = get_initial_targets_1980(use_anes_bands=True)

    metrics_5 = ["constraint", "party_sep", "affect", "within_party_sd"]
    years = [1990, 2000, 2010, 2020, 2025]
    cells_4x5 = []
    for year in years:
        for metric in metrics_5:
            band = anes_pri[year][metric]
            v = means[year][metric]
            cells_4x5.append({
                "year": year, "metric": metric, "value": v,
                "band": list(band),
                "in_band": bool(in_band(v, band)),
            })
    init_metrics = ["variance", "constraint", "party_sep", "within_party_sd"]
    cells_init = []
    for metric in init_metrics:
        band = anes_init[metric]
        v = means[1980][metric]
        cells_init.append({
            "year": 1980, "metric": metric, "value": v,
            "band": list(band),
            "in_band": bool(in_band(v, band)),
        })
    n_4x5 = sum(c["in_band"] for c in cells_4x5)
    n_init = sum(c["in_band"] for c in cells_init)
    return {
        "w2_total": float(w2_total),
        "per_decade": per_decade,
        "anes_tally_24": int(n_4x5 + n_init),
        "anes_tally_4x5": int(n_4x5),
        "anes_tally_init": int(n_init),
        "cells_4x5": cells_4x5,
        "cells_init": cells_init,
        "means": {str(y): means[y] for y in means},
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=3,
                        help="Seeds per cell (default 3).")
    parser.add_argument("--drift-mults", type=str,
                        default="1.0,1.75,2.5,3.5")
    parser.add_argument("--sigma-mults", type=str,
                        default="1.0,1.3,1.6")
    parser.add_argument("--out-prefix", default="docs/results/phase9_anes_sweep")
    args = parser.parse_args()

    from abm.calibration_parallel import run_seeds_parallel
    from abm.calibration_phase9 import pot_available

    drift_mults = [float(x) for x in args.drift_mults.split(",")]
    sigma_mults = [float(x) for x in args.sigma_mults.split(",")]
    seeds = list(range(args.seeds))

    print("=" * 78)
    print(f"Phase 9 §11.7-B sweep — drift × sigma_pc grid, {args.seeds} seeds/cell")
    print(f"  drift_mults: {drift_mults}")
    print(f"  sigma_mults: {sigma_mults}")
    print(f"  cells total: {len(drift_mults) * len(sigma_mults)}")
    print(f"  POT available: {pot_available()}")
    print("=" * 78)

    rows = []
    for drift_m, sigma_m in itertools.product(drift_mults, sigma_mults):
        print(f"\n[cell] drift_m={drift_m}  sigma_m={sigma_m}")
        work = [(s, drift_m, sigma_m) for s in seeds]
        results = run_seeds_parallel(_wrap_worker, work)
        scored = _score_cell(results, seeds)
        scored["drift_mult"] = drift_m
        scored["sigma_pc_mult"] = sigma_m
        rows.append(scored)
        print(f"  w2_total={scored['w2_total']:.3f}  "
              f"§11_ANES={scored['anes_tally_24']}/24  "
              f"(2020: party_sep={scored['means']['2020']['party_sep']:.3f} "
              f"wp_sd={scored['means']['2020']['within_party_sd']:.3f})")

    rows.sort(key=lambda r: (-r["anes_tally_24"], r["w2_total"]))
    winner = rows[0]

    out_path = Path(f"{args.out_prefix}.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "config": "tier_d_anes_knobs",
            "seeds": seeds,
            "drift_mults": drift_mults,
            "sigma_mults": sigma_mults,
            "rows": rows,
        }, f, indent=2)
    print(f"\n[dump] {out_path}")

    win_path = Path(f"{args.out_prefix}_winner.json")
    with open(win_path, "w", encoding="utf-8") as f:
        json.dump(winner, f, indent=2)
    print(f"[dump] {win_path}")
    print(f"\n[winner] drift={winner['drift_mult']}  "
          f"sigma_pc={winner['sigma_pc_mult']}  "
          f"§11={winner['anes_tally_24']}/24  "
          f"w2={winner['w2_total']:.3f}")


def _wrap_worker(args):
    return _worker(args)


if __name__ == "__main__":
    main()
