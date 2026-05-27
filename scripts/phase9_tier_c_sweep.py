"""Phase 9 Tier C sweep — emergence-driven faction dynamics.

12-cell Cartesian product over Tier C's two tuning knobs:
  faction_anchor_strength ∈ {0.02, 0.04, 0.06, 0.08}
  event_stubbornness_bump_multiplier ∈ {0.5, 1.0, 1.5}

`factional_seeding` stays at its default False — Tier C uses broad-
Gaussian ICs (1980 §11 preserved by construction).

For each cell: build the historical_arc engine at the configured
kwargs, run the schedule with `faction_anchor_events=True`,
snapshot positions at the five empirical decades for Wasserstein
scoring, and capture the 6-metric trajectory for the Phase 8f §11
gate.

5 seeds per cell. The chosen winner gets re-run at 9 seeds via
`scripts/phase9_tier_c_blessed.py`.

Output: `phase9_tier_c_sweep.csv` and `.json`.
"""
from __future__ import annotations

import csv
import json
import os
import sys
from itertools import product
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
    PHASE9_TIERC_STRENGTH / _BUMP."""
    from abm.pillars.historical_arc import build_engine, build_schedule
    from abm.pillars.schedule import run_to
    from scripts.phase8f_lib import measure_all

    strength = float(os.environ["PHASE9_TIERC_STRENGTH"])
    bump = float(os.environ["PHASE9_TIERC_BUMP"])

    eng = build_engine(
        seed=seed, n_agents=N,
        independent_fraction=INDEPENDENT_FRACTION,
        factional_seeding=False,   # Tier C: broad-Gaussian ICs
        faction_anchor_strength=strength,
        faction_anchor_events=True,
        event_stubbornness_bump_multiplier=bump,
    )
    sched = build_schedule(
        factional_seeding=False,
        faction_anchor_events=True,
    )

    snapshots: dict[int, np.ndarray] = {}
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


def _evaluate_cell(strength: float, bump: float) -> dict:
    os.environ["PHASE9_TIERC_STRENGTH"] = f"{strength}"
    os.environ["PHASE9_TIERC_BUMP"] = f"{bump}"

    from abm.calibration_parallel import run_seeds_parallel
    from abm.calibration_phase9 import (
        EMPIRICAL_DECADES, score_engine_run,
    )
    from scripts.phase8f_lib import (
        PRIMARY_TARGETS, INITIAL_TARGETS_1980, aggregate, in_band,
    )

    print(f"  cell strength={strength} bump={bump} ...", flush=True)
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

    # 2020 shape descriptors
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
        "strength": strength, "bump_mult": bump,
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
    out_csv = Path("phase9_tier_c_sweep.csv")
    out_json = Path("phase9_tier_c_sweep.json")

    grid_strength = [0.02, 0.04, 0.06, 0.08]
    grid_bump = [0.5, 1.0, 1.5]

    print("=" * 78)
    print("Phase 9 Tier C sweep — 12 cells × 5 seeds")
    print(f"  strength × bump = {len(grid_strength)} × {len(grid_bump)}")
    print("=" * 78)

    rows = []
    for strength, bump in product(grid_strength, grid_bump):
        rec = _evaluate_cell(strength, bump)
        rows.append(rec)

    fieldnames = [
        "strength", "bump_mult",
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

    passing = [r for r in rows if r["gate_pass"]]
    print("\n" + "=" * 78)
    print(f"Cells passing §11 (≥18/24): {len(passing)}/{len(rows)}")
    if passing:
        passing.sort(key=lambda r: r["w2_total"])
        print("\nTop 3 §11-passing by w2_total:")
        for r in passing[:3]:
            print(f"  strength={r['strength']} bump={r['bump_mult']}  "
                  f"w2_total={r['w2_total']:.4f}  "
                  f"cells={r['cells_in_band']}/24")
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
                        "min §11-shortfall tiebreaker → tier_c_best_effort")
        any_pass = False
        print("\nNO cell passed §11 gate. Top 3 by w2_total (best-effort):")
        for r in rows_sorted[:3]:
            print(f"  strength={r['strength']} bump={r['bump_mult']}  "
                  f"w2_total={r['w2_total']:.4f}  "
                  f"cells={r['cells_in_band']}/24")

    print(f"\nWinner: strength={winner['strength']} bump={winner['bump_mult']}")
    print(f"  w2_total={winner['w2_total']:.4f}  "
          f"cells_in_band={winner['cells_in_band']}/24")
    print(f"  reason: {bless_reason}")
    print(f"\n[dump] {out_csv.resolve()}")
    print(f"[dump] {out_json.resolve()}")

    with open("phase9_tier_c_sweep_winner.json", "w", encoding="utf-8") as f:
        json.dump({
            "winner": winner,
            "bless_reason": bless_reason,
            "any_pass": any_pass,
        }, f, indent=2)


if __name__ == "__main__":
    main()
