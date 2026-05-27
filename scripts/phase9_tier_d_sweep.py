"""Phase 9 Tier D — 2-lever ±30% sweep.

After the central run (`phase9_tier_d_central.py`) revealed two
structural issues — 2020 corr(x, y) over-shooting (+0.78 vs empirical
~+0.45) and §11 dropping to 13/24 — the highest-leverage diagnostic
sweep is over the two levers that control y-axis sorting strength
and initial axis coupling:

  Lever 2 — `tier_d_party_center_y` ∈ {0.10, 0.15, 0.20, 0.25}
  Lever 3 — `tier_d_coupling_rho` ∈ {0.00, 0.10, 0.20, 0.30}

16 cells × 5 seeds. Levers 1, 4, 6 stay at central. Lever 5 (outlet
y-spread) is deferred — the 1D-only outlet literature gives no
principled prior, and the structural issue here is rule-level
y-compression, not outlet placement.

Multi-core strategy: the existing per-seed pool (`run_seeds_parallel`)
caps utilisation at min(N_seeds, N_cores). With 5 seeds and an 8+
core CPU, ~3 cores idle. This script instead parallelises *cells*
across cores via ProcessPoolExecutor — each cell-worker runs its 5
seeds sequentially. CPU saturation is independent of seed count.

Outputs:
  - `phase9_tier_d_sweep.csv`, `.json` — every cell's metrics
  - `phase9_tier_d_sweep_winner.json` — best §11-passing cell by
    w2_total, or best-effort if no cell passes
"""
from __future__ import annotations

import csv
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from itertools import product
from multiprocessing import cpu_count
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

GRID_Y = [0.10, 0.15, 0.20, 0.25]
GRID_RHO = [0.00, 0.10, 0.20, 0.30]


def _run_one_seed(seed: int, y_val: float, rho_val: float,
                  strength: float, bump: float) -> dict:
    """Build + run a single seed. Returns snapshots + trajectory.

    Imports happen inside the function so spawn-pool workers
    re-import cleanly (no shared module-level engine state).
    """
    import numpy as np
    from abm.pillars.historical_arc import build_engine, build_schedule
    from abm.pillars.schedule import run_to
    from scripts.phase8f_lib import measure_all

    eng = build_engine(
        seed=seed, n_agents=N,
        independent_fraction=INDEPENDENT_FRACTION,
        factional_seeding=False,
        faction_anchor_strength=strength,
        faction_anchor_events=True,
        event_stubbornness_bump_multiplier=bump,
        tier_d_axis_balance=True,
        tier_d_party_center_y=y_val,
        tier_d_coupling_rho=rho_val,
    )
    sched = build_schedule(
        factional_seeding=False,
        faction_anchor_events=True,
    )

    snapshots: dict[int, "np.ndarray"] = {}
    trajectory: dict[int, dict] = {1980: measure_all(eng)}
    snapshots[1980] = np.array(
        [a.state.ideology for a in eng.agents], dtype=float
    )
    year_at_tick: dict[int, list] = {}
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


def _evaluate_cell(y_val: float, rho_val: float,
                   strength: float, bump: float) -> dict:
    """Run all 5 seeds sequentially within this process, aggregate.

    Designed for outer ProcessPoolExecutor parallelism — each cell
    worker process is single-threaded across its seeds, so multiple
    cells saturate all cores.
    """
    import numpy as np
    from abm.calibration_phase9 import EMPIRICAL_DECADES, score_engine_run
    from scripts.phase8f_lib import (
        PRIMARY_TARGETS, INITIAL_TARGETS_1980, aggregate, in_band,
    )

    results = [_run_one_seed(s, y_val, rho_val, strength, bump)
               for s in SEEDS]

    # --- Wasserstein ---
    per_decade_w2: dict[int, list[float]] = {d: [] for d in EMPIRICAL_DECADES}
    for seed, res in zip(SEEDS, results):
        df = score_engine_run(
            positions_by_decade=res["snapshots"],
            target_dir=Path("data/phase9_empirical"),
            seed_for_subsample=seed,
        )
        for _, row in df.iterrows():
            per_decade_w2[int(row["decade"])].append(float(row["wasserstein"]))
    w2_means = {d: float(np.mean(v)) for d, v in per_decade_w2.items()}

    # --- §11 ---
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
    cells_in_band = cells_4x5 + cells_init

    # 2020 descriptors
    corr_2020 = float(np.mean([
        np.corrcoef(r["snapshots"][2020][:, 0],
                    r["snapshots"][2020][:, 1])[0, 1]
        for r in results
    ]))
    var_y_2020 = float(np.mean([
        np.var(r["snapshots"][2020][:, 1]) for r in results
    ]))
    var_x_2020 = float(np.mean([
        np.var(r["snapshots"][2020][:, 0]) for r in results
    ]))

    return {
        "party_center_y": y_val,
        "coupling_rho": rho_val,
        "w2_1980": w2_means[1980],
        "w2_1990": w2_means[1990],
        "w2_2000": w2_means[2000],
        "w2_2010": w2_means[2010],
        "w2_2020": w2_means[2020],
        "w2_total": float(sum(w2_means.values())),
        "cells_in_band": cells_in_band,
        "cells_total": 24,
        "gate_pass": bool(cells_in_band >= 18),
        "shape_2020_corr_xy": corr_2020,
        "shape_2020_var_y": var_y_2020,
        "shape_2020_var_x": var_x_2020,
    }


def _cell_task(args):
    """Top-level worker entry — picklable target for ProcessPoolExecutor."""
    y_val, rho_val, strength, bump = args
    return _evaluate_cell(y_val, rho_val, strength, bump)


def _load_tier_c_winner_strength_bump():
    p = Path("phase9_tier_c_sweep_winner.json")
    if not p.exists():
        p = Path("docs/results/phase9_tier_c_sweep_winner.json")
    if not p.exists():
        return 0.04, 1.0
    with open(p, "r", encoding="utf-8") as f:
        info = json.load(f)
    w = info["winner"]
    return float(w["strength"]), float(w["bump_mult"])


def main():
    strength, bump = _load_tier_c_winner_strength_bump()
    n_cores = cpu_count()
    cells = [(y, r, strength, bump) for y, r in product(GRID_Y, GRID_RHO)]
    n_cells = len(cells)
    # Don't over-subscribe — cap workers at min(cells, cores).
    max_workers = max(1, min(n_cells, n_cores))

    print("=" * 78)
    print(f"Phase 9 Tier D sweep — {n_cells} cells × {len(SEEDS)} seeds")
    print(f"  grid_y={GRID_Y}  grid_rho={GRID_RHO}")
    print(f"  layered on Tier C: strength={strength} bump={bump}")
    print(f"  CPU cores available: {n_cores}")
    print(f"  parallelising cells across {max_workers} worker processes")
    print(f"  (each worker runs its 5 seeds sequentially → full CPU saturation)")
    print("=" * 78)

    rows: list[dict] = []
    with ProcessPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(_cell_task, c): c for c in cells}
        done_count = 0
        for fut in as_completed(futures):
            c = futures[fut]
            rec = fut.result()
            rows.append(rec)
            done_count += 1
            print(f"  [{done_count:2d}/{n_cells}] "
                  f"y={c[0]:.2f} rho={c[1]:.2f}  "
                  f"w2_total={rec['w2_total']:.4f}  "
                  f"cells={rec['cells_in_band']}/24  "
                  f"corr_2020={rec['shape_2020_corr_xy']:+.3f}",
                  flush=True)

    # Re-sort rows by (y, rho) for stable CSV ordering.
    rows.sort(key=lambda r: (r["party_center_y"], r["coupling_rho"]))

    fieldnames = [
        "party_center_y", "coupling_rho",
        "w2_1980", "w2_1990", "w2_2000", "w2_2010", "w2_2020", "w2_total",
        "cells_in_band", "cells_total", "gate_pass",
        "shape_2020_corr_xy", "shape_2020_var_y", "shape_2020_var_x",
    ]
    with open("phase9_tier_d_sweep.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in fieldnames})
    with open("phase9_tier_d_sweep.json", "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)

    passing = [r for r in rows if r["gate_pass"]]
    print("\n" + "=" * 78)
    print(f"Cells passing §11 (≥18/24): {len(passing)}/{n_cells}")
    if passing:
        passing.sort(key=lambda r: r["w2_total"])
        print("\nTop 5 §11-passing by w2_total:")
        for r in passing[:5]:
            print(f"  y={r['party_center_y']:.2f} rho={r['coupling_rho']:.2f}  "
                  f"w2_total={r['w2_total']:.4f}  "
                  f"cells={r['cells_in_band']}/24  "
                  f"corr_2020={r['shape_2020_corr_xy']:+.3f}")
        winner = passing[0]
        bless_reason = "min w2_total among §11-passing"
        any_pass = True
    else:
        rows_sorted = sorted(
            rows,
            key=lambda r: (r["w2_total"], 24 - r["cells_in_band"]),
        )
        winner = rows_sorted[0]
        bless_reason = ("NO §11-passing cell; min w2_total + "
                        "min §11-shortfall tiebreaker → tier_d_best_effort")
        any_pass = False
        print("\nNO cell passed §11. Top 5 by w2_total (best-effort):")
        for r in rows_sorted[:5]:
            print(f"  y={r['party_center_y']:.2f} rho={r['coupling_rho']:.2f}  "
                  f"w2_total={r['w2_total']:.4f}  "
                  f"cells={r['cells_in_band']}/24  "
                  f"corr_2020={r['shape_2020_corr_xy']:+.3f}")

    print(f"\nWinner: y={winner['party_center_y']} rho={winner['coupling_rho']}")
    print(f"  w2_total={winner['w2_total']:.4f}  "
          f"cells={winner['cells_in_band']}/24  "
          f"corr_2020={winner['shape_2020_corr_xy']:+.3f}")
    print(f"  reason: {bless_reason}")
    print(f"\n[dump] {Path('phase9_tier_d_sweep.csv').resolve()}")
    print(f"[dump] {Path('phase9_tier_d_sweep.json').resolve()}")

    with open("phase9_tier_d_sweep_winner.json", "w", encoding="utf-8") as f:
        json.dump({
            "winner": winner,
            "bless_reason": bless_reason,
            "any_pass": any_pass,
            "grid_y": GRID_Y,
            "grid_rho": GRID_RHO,
            "tier_c_strength": strength,
            "tier_c_bump": bump,
        }, f, indent=2)


if __name__ == "__main__":
    main()
