"""Phase 9 Step 4 — score the Tier A historical_arc engine against
per-decade empirical Wasserstein targets.

Identical to `phase9_score_baseline.py` except `build_engine` is
called with `factional_seeding=True`.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

from abm.calibration_parallel import ci_95, run_seeds_parallel

SEEDS = tuple(range(9))
N = 250
INDEPENDENT_FRACTION = 0.12
FACTIONAL_SEEDING = True
FACTION_STUBBORNNESS_BOOST_VALUE = float(
    os.environ.get("PHASE9_BOOST", "0.5")
)
DATA_DIR = Path("phase9_data")

DECADE_TICKS = [
    (1980, 0),
    (1990, 30),
    (2000, 60),
    (2010, 90),
    (2020, 120),
]


def _tier_a_worker(seed: int) -> dict:
    from abm.pillars.historical_arc import build_engine, build_schedule
    from abm.pillars.schedule import run_to

    eng = build_engine(
        seed=seed, n_agents=N,
        independent_fraction=INDEPENDENT_FRACTION,
        factional_seeding=FACTIONAL_SEEDING,
        faction_stubbornness_boost=FACTION_STUBBORNNESS_BOOST_VALUE,
    )
    sched = build_schedule(factional_seeding=FACTIONAL_SEEDING)
    snapshots: dict = {}
    for decade, tick in DECADE_TICKS:
        if tick > 0:
            run_to(eng, sched, tick)
        positions = np.array(
            [a.state.ideology for a in eng.agents], dtype=float
        )
        snapshots[decade] = positions
    return snapshots


def main():
    from abm.calibration_phase9 import (
        EMPIRICAL_DECADES, pot_available, score_engine_run,
    )

    out_json = os.environ.get("PHASE9_OUT_JSON", "phase9_tier_a_score.json")
    out_csv = os.environ.get(
        "PHASE9_OUT_CSV", "phase9_tier_a_descriptors.csv"
    )

    print("=" * 78)
    print("Phase 9 Tier A — Wasserstein score (factional_seeding=True)")
    print(
        f"  N={N}, independent_fraction={INDEPENDENT_FRACTION}, "
        f"seeds={len(SEEDS)}, boost={FACTION_STUBBORNNESS_BOOST_VALUE}"
    )
    print(
        f"  POT available: {pot_available()} "
        f"({'primary metric' if pot_available() else 'DEGRADED fallback'})"
    )
    print(f"  data dir: {DATA_DIR.resolve()}")
    print("=" * 78)

    print("\n[run] launching Tier A ensemble in parallel...")
    all_snapshots = run_seeds_parallel(_tier_a_worker, SEEDS)
    print(f"[run] collected {len(all_snapshots)} seed snapshots")

    per_seed_dfs = []
    for seed, snaps in zip(SEEDS, all_snapshots):
        df = score_engine_run(
            positions_by_decade=snaps,
            target_dir=DATA_DIR,
            seed_for_subsample=seed,
        )
        df.insert(0, "seed", seed)
        per_seed_dfs.append(df)

    import pandas as pd
    combined = pd.concat(per_seed_dfs, ignore_index=True)
    csv_path = Path(out_csv)
    combined.to_csv(csv_path, index=False)
    print(f"[dump] {csv_path.resolve()}  ({len(combined)} rows)")

    summary: dict = {
        "metadata": {
            "n_agents": N,
            "independent_fraction": INDEPENDENT_FRACTION,
            "factional_seeding": FACTIONAL_SEEDING,
            "faction_stubbornness_boost": FACTION_STUBBORNNESS_BOOST_VALUE,
            "seeds": list(SEEDS),
            "pot_available": pot_available(),
            "degraded": not pot_available(),
            "decade_ticks": DECADE_TICKS,
            "population_includes": "all agents (party 0/1/2)",
        },
        "per_decade": {},
    }
    print("\n[summary] per-decade Wasserstein + descriptors")
    print(
        "  decade  W2_mean   95%CI_hw  corr_xy  var_x   var_y   "
        "mean|x|  mean|y|  n_lmax"
    )
    for decade in EMPIRICAL_DECADES:
        sub = combined[combined["decade"] == decade]
        w_vals = sub["wasserstein"].tolist()
        w_mean = float(np.mean(w_vals))
        lo, hi = ci_95(w_vals)
        hw = float((hi - lo) / 2.0)
        rec = {
            "wasserstein_mean": w_mean,
            "wasserstein_ci95_lo": lo,
            "wasserstein_ci95_hi": hi,
            "wasserstein_ci95_halfwidth": hw,
            "wasserstein_per_seed": w_vals,
            "corr_xy_mean": float(sub["corr_xy"].mean()),
            "var_x_mean": float(sub["var_x"].mean()),
            "var_y_mean": float(sub["var_y"].mean()),
            "mean_abs_x_mean": float(sub["mean_abs_x"].mean()),
            "mean_abs_y_mean": float(sub["mean_abs_y"].mean()),
            "n_local_max_mean": float(sub["n_local_max"].mean()),
            "q_ll_mean": float(sub["q_ll"].mean()),
            "q_lr_mean": float(sub["q_lr"].mean()),
            "q_ul_mean": float(sub["q_ul"].mean()),
            "q_ur_mean": float(sub["q_ur"].mean()),
        }
        summary["per_decade"][str(decade)] = rec
        print(
            f"  {decade}    {w_mean:.4f}   ±{hw:.4f}   "
            f"{rec['corr_xy_mean']:+.3f}   {rec['var_x_mean']:.3f}   "
            f"{rec['var_y_mean']:.3f}   {rec['mean_abs_x_mean']:.3f}    "
            f"{rec['mean_abs_y_mean']:.3f}    {rec['n_local_max_mean']:.1f}"
        )

    out_path = Path(out_json)
    with open(out_path, "w", encoding="utf-8") as fp:
        json.dump(summary, fp, indent=2)
    print(f"\n[dump] {out_path.resolve()}")
    print("\n" + "=" * 78)


if __name__ == "__main__":
    main()
