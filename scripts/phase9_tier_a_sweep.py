"""Phase 9 Tier-A-rescue sweep.

27-cell Cartesian product over Tier A's three tuning knobs:
  scale ∈ {0.5, 0.7, 1.0}
  sigma ∈ {0.05, 0.10, 0.15}
  boost ∈ {0.0, 0.2, 0.5}

For each cell: build the historical_arc engine at the configured kwargs,
run the schedule with factional_seeding=True, snapshot positions at the
five empirical decades for Wasserstein scoring, and also capture the
6-metric trajectory used by the Phase 8f §11 gate.

5 seeds per cell to keep compute bounded — the chosen winner gets
re-run at 9 seeds via `scripts/phase9_tier_a_blessed.py`.

Output: `phase9_tier_a_sweep.csv` with columns
  scale, sigma, boost,
  w2_1980, w2_1990, w2_2000, w2_2010, w2_2020, w2_total,
  cells_in_band, cells_total, gate_pass.

Worker inputs are passed via environment variables so the parallel
spawn-pool workers can read them (multiprocessing 'spawn' inherits
os.environ from the parent at fork-time).
"""
from __future__ import annotations

import csv
import json
import os
import sys
from itertools import product
from pathlib import Path

# Project root on sys.path so `from scripts.phase8f_lib import ...` works
# both when the script is run directly (`python scripts/phase9_*.py` —
# sys.path[0] is the scripts/ dir, not cwd) and inside spawn-pool
# workers (they inherit sys.path from the parent at fork-time).
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

SEEDS = tuple(range(5))
N = 250
INDEPENDENT_FRACTION = 0.12

DECADE_TICKS = [
    (1980, 0),
    (1990, 30),
    (2000, 60),
    (2010, 90),
    (2020, 120),
]
SECTION11_TICKS = [(1990, 30), (2000, 60), (2010, 90),
                   (2020, 120), (2025, 135)]


def _sweep_worker(seed: int) -> dict:
    """Build + run one seed for the cell encoded in env vars
    PHASE9_SWEEP_SCALE / _SIGMA / _BOOST. Returns positions per decade
    and 6-metric trajectory for §11 evaluation."""
    from abm.pillars.historical_arc import build_engine, build_schedule
    from abm.pillars.schedule import run_to
    from scripts.phase8f_lib import measure_all

    scale = float(os.environ["PHASE9_SWEEP_SCALE"])
    sigma = float(os.environ["PHASE9_SWEEP_SIGMA"])
    boost = float(os.environ["PHASE9_SWEEP_BOOST"])

    eng = build_engine(
        seed=seed, n_agents=N,
        independent_fraction=INDEPENDENT_FRACTION,
        factional_seeding=True,
        faction_stubbornness_boost=boost,
        faction_center_scale=scale,
        faction_sigma_within=sigma,
    )
    sched = build_schedule(factional_seeding=True)

    snapshots: dict[int, np.ndarray] = {}
    trajectory: dict[int, dict] = {1980: measure_all(eng)}
    snapshots[1980] = np.array(
        [a.state.ideology for a in eng.agents], dtype=float
    )
    # Walk through ticks in order, capturing both W2 snapshots and §11
    # trajectory points.
    all_ticks = sorted(
        set(t for _, t in DECADE_TICKS) | set(t for _, t in SECTION11_TICKS)
    )
    year_at_tick = {}
    for y, t in DECADE_TICKS:
        year_at_tick.setdefault(t, []).append(("w2", y))
    for y, t in SECTION11_TICKS:
        year_at_tick.setdefault(t, []).append(("s11", y))
    for tick in all_ticks:
        if tick == 0:
            continue
        run_to(eng, sched, tick)
        for kind, year in year_at_tick.get(tick, []):
            if kind == "w2":
                snapshots[year] = np.array(
                    [a.state.ideology for a in eng.agents], dtype=float
                )
            else:
                trajectory[year] = measure_all(eng)
    return {"snapshots": snapshots, "trajectory": trajectory}


def _evaluate_cell(scale: float, sigma: float, boost: float) -> dict:
    """Run all seeds for one cell; return aggregated W2 and §11 tally."""
    os.environ["PHASE9_SWEEP_SCALE"] = f"{scale}"
    os.environ["PHASE9_SWEEP_SIGMA"] = f"{sigma}"
    os.environ["PHASE9_SWEEP_BOOST"] = f"{boost}"

    from abm.calibration_parallel import run_seeds_parallel
    from abm.calibration_phase9 import (
        EMPIRICAL_DECADES, score_engine_run,
    )
    from scripts.phase8f_lib import (
        PRIMARY_TARGETS, INITIAL_TARGETS_1980, aggregate, in_band,
    )

    print(f"  cell scale={scale} sigma={sigma} boost={boost} ...", flush=True)
    results = run_seeds_parallel(_sweep_worker, SEEDS)
    print(f"    collected {len(results)} seeds", flush=True)

    # --- Wasserstein ---
    per_decade_w2: dict[int, list[float]] = {d: [] for d in EMPIRICAL_DECADES}
    for seed, res in zip(SEEDS, results):
        df = score_engine_run(
            positions_by_decade=res["snapshots"],
            target_dir=Path("phase9_data"),
            seed_for_subsample=seed,
        )
        for _, row in df.iterrows():
            per_decade_w2[int(row["decade"])].append(float(row["wasserstein"]))
    w2_means = {d: float(np.mean(v)) for d, v in per_decade_w2.items()}

    # --- §11 cells ---
    trajectories = [r["trajectory"] for r in results]
    means, ses = aggregate(trajectories)

    metrics_5 = ["constraint", "party_sep", "affect", "within_party_sd"]
    years = [1990, 2000, 2010, 2020, 2025]
    cells_4x5 = 0
    for year in years:
        for metric in metrics_5:
            band = PRIMARY_TARGETS[year][metric]
            v = means[year][metric]
            if in_band(v, band):
                cells_4x5 += 1
    init_metrics = ["variance", "constraint", "party_sep", "within_party_sd"]
    cells_init = 0
    for metric in init_metrics:
        band = INITIAL_TARGETS_1980[metric]
        v = means[1980][metric]
        if in_band(v, band):
            cells_init += 1
    cells_total = 24
    cells_in_band = cells_4x5 + cells_init

    # Capture 2020 descriptors averaged across seeds for the winner-shape
    # write-up.
    var_y_2020 = float(np.mean([
        np.var(r["snapshots"][2020][:, 1]) for r in results
    ]))
    var_x_2020 = float(np.mean([
        np.var(r["snapshots"][2020][:, 0]) for r in results
    ]))
    corr_2020 = float(np.mean([
        np.corrcoef(r["snapshots"][2020][:, 0],
                    r["snapshots"][2020][:, 1])[0, 1]
        for r in results
    ]))

    w2_total = float(sum(w2_means.values()))
    return {
        "scale": scale, "sigma": sigma, "boost": boost,
        "w2_1980": w2_means[1980],
        "w2_1990": w2_means[1990],
        "w2_2000": w2_means[2000],
        "w2_2010": w2_means[2010],
        "w2_2020": w2_means[2020],
        "w2_total": w2_total,
        "cells_in_band": cells_in_band,
        "cells_total": cells_total,
        "gate_pass": bool(cells_in_band >= 18),
        "shape_2020_var_y": var_y_2020,
        "shape_2020_var_x": var_x_2020,
        "shape_2020_corr_xy": corr_2020,
    }


def main():
    out_csv = Path("phase9_tier_a_sweep.csv")
    out_json = Path("phase9_tier_a_sweep.json")

    grid_scale = [0.5, 0.7, 1.0]
    grid_sigma = [0.05, 0.10, 0.15]
    grid_boost = [0.0, 0.2, 0.5]

    print("=" * 78)
    print("Phase 9 Tier-A-rescue sweep — 27 cells × 5 seeds")
    print(f"  scale × sigma × boost = "
          f"{len(grid_scale)} × {len(grid_sigma)} × {len(grid_boost)}")
    print("=" * 78)

    rows = []
    for scale, sigma, boost in product(grid_scale, grid_sigma, grid_boost):
        rec = _evaluate_cell(scale, sigma, boost)
        rows.append(rec)

    # CSV
    fieldnames = [
        "scale", "sigma", "boost",
        "w2_1980", "w2_1990", "w2_2000", "w2_2010", "w2_2020", "w2_total",
        "cells_in_band", "cells_total", "gate_pass",
    ]
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in fieldnames})

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)

    # Summary + winner pick
    passing = [r for r in rows if r["gate_pass"]]
    print("\n" + "=" * 78)
    print(f"Cells passing §11 (≥18/24): {len(passing)}/27")
    if passing:
        passing.sort(key=lambda r: r["w2_total"])
        print("\nTop 3 §11-passing by w2_total:")
        for r in passing[:3]:
            print(f"  scale={r['scale']} sigma={r['sigma']} boost={r['boost']}  "
                  f"w2_total={r['w2_total']:.4f}  "
                  f"cells={r['cells_in_band']}/24")
        winner = passing[0]
        bless_reason = "min w2_total among §11-passing"
    else:
        # Best-effort: min w2_total, then min §11-shortfall as tiebreaker.
        rows_sorted = sorted(
            rows,
            key=lambda r: (r["w2_total"], 24 - r["cells_in_band"]),
        )
        winner = rows_sorted[0]
        bless_reason = ("NO §11-passing cell; min w2_total + "
                        "min §11-shortfall tiebreaker → tier_a_best_effort")
        print("\nNO cell passed §11 gate. Top 3 by w2_total (best-effort):")
        for r in rows_sorted[:3]:
            print(f"  scale={r['scale']} sigma={r['sigma']} boost={r['boost']}  "
                  f"w2_total={r['w2_total']:.4f}  "
                  f"cells={r['cells_in_band']}/24")

    print(f"\nWinner: scale={winner['scale']} sigma={winner['sigma']} "
          f"boost={winner['boost']}")
    print(f"  w2_total={winner['w2_total']:.4f}  "
          f"cells_in_band={winner['cells_in_band']}/24")
    print(f"  reason: {bless_reason}")
    print(f"\n[dump] {out_csv.resolve()}")
    print(f"[dump] {out_json.resolve()}")

    # Persist winner for the blessed re-run.
    with open("phase9_tier_a_sweep_winner.json", "w", encoding="utf-8") as f:
        json.dump({
            "winner": winner,
            "bless_reason": bless_reason,
            "any_pass": bool(passing),
        }, f, indent=2)


if __name__ == "__main__":
    main()
