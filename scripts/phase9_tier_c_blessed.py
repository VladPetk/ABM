"""Phase 9 Tier C — re-run sweep winner at 9 seeds.

Reads `phase9_tier_c_sweep_winner.json` (written by
`phase9_tier_c_sweep.py`) and re-runs the winning (strength,
bump_mult) cell at 9 seeds, producing:
  - `phase9_tier_c_blessed_score.json` — per-decade Wasserstein at 9 seeds.
  - `phase9_section11_under_tier_c_blessed.json` — §11 tally.
  - `phase9_tier_c_blessed_descriptors.csv` — per-decade shape descriptors.
"""
from __future__ import annotations

import csv
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

SEEDS = tuple(range(9))
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


def _blessed_worker(seed: int) -> dict:
    from abm.pillars.historical_arc import build_engine, build_schedule
    from abm.pillars.schedule import run_to
    from scripts.phase8f_lib import measure_all

    strength = float(os.environ["PHASE9_TIERC_BLESSED_STRENGTH"])
    bump = float(os.environ["PHASE9_TIERC_BLESSED_BUMP"])

    eng = build_engine(
        seed=seed, n_agents=N,
        independent_fraction=INDEPENDENT_FRACTION,
        factional_seeding=False,
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


def main():
    with open("phase9_tier_c_sweep_winner.json", "r", encoding="utf-8") as f:
        info = json.load(f)
    w = info["winner"]
    strength = float(w["strength"])
    bump = float(w["bump_mult"])
    label = "tier_c_blessed" if info.get("any_pass") else "tier_c_best_effort"

    os.environ["PHASE9_TIERC_BLESSED_STRENGTH"] = f"{strength}"
    os.environ["PHASE9_TIERC_BLESSED_BUMP"] = f"{bump}"

    from abm.calibration_parallel import ci_95, run_seeds_parallel
    from abm.calibration_phase9 import (
        EMPIRICAL_DECADES, pot_available, score_engine_run,
    )
    from scripts.phase8f_lib import (
        PRIMARY_TARGETS, INITIAL_TARGETS_1980, aggregate, in_band,
    )

    print("=" * 78)
    print(f"Phase 9 Tier C blessed re-run ({label}) — 9 seeds")
    print(f"  strength={strength}  bump_mult={bump}")
    print(f"  POT available: {pot_available()}")
    print("=" * 78)

    results = run_seeds_parallel(_blessed_worker, SEEDS)

    per_seed_dfs = []
    for seed, res in zip(SEEDS, results):
        df = score_engine_run(
            positions_by_decade=res["snapshots"],
            target_dir=Path("phase9_data"),
            seed_for_subsample=seed,
        )
        df.insert(0, "seed", seed)
        per_seed_dfs.append(df)

    import pandas as pd
    combined = pd.concat(per_seed_dfs, ignore_index=True)

    summary = {
        "metadata": {
            "label": label,
            "n_agents": N,
            "independent_fraction": INDEPENDENT_FRACTION,
            "factional_seeding": False,
            "faction_anchor_strength": strength,
            "event_stubbornness_bump_multiplier": bump,
            "seeds": list(SEEDS),
            "pot_available": pot_available(),
            "degraded": not pot_available(),
            "decade_ticks": DECADE_TICKS,
            "population_includes": "all agents (party 0/1/2)",
            "bless_reason": info.get("bless_reason"),
        },
        "per_decade": {},
    }
    print("\n[summary] per-decade Wasserstein (blessed)")
    print("  decade  W2_mean   95%CI_hw  corr_xy  var_x   var_y")
    desc_rows = []
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
        print(f"  {decade}    {w_mean:.4f}   ±{hw:.4f}   "
              f"{rec['corr_xy_mean']:+.3f}   {rec['var_x_mean']:.3f}   "
              f"{rec['var_y_mean']:.3f}")
        desc_rows.append({
            "decade": decade,
            "w2_mean": w_mean, "w2_ci95_hw": hw,
            "corr_xy": rec["corr_xy_mean"],
            "var_x": rec["var_x_mean"],
            "var_y": rec["var_y_mean"],
            "mean_abs_x": rec["mean_abs_x_mean"],
            "mean_abs_y": rec["mean_abs_y_mean"],
            "n_local_max": rec["n_local_max_mean"],
        })

    with open("phase9_tier_c_blessed_score.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"\n[dump] {Path('phase9_tier_c_blessed_score.json').resolve()}")

    with open("phase9_tier_c_blessed_descriptors.csv", "w",
              encoding="utf-8", newline="") as f:
        wcsv = csv.DictWriter(f, fieldnames=list(desc_rows[0].keys()))
        wcsv.writeheader()
        for r in desc_rows:
            wcsv.writerow(r)
    print(f"[dump] {Path('phase9_tier_c_blessed_descriptors.csv').resolve()}")

    # §11
    trajectories = [r["trajectory"] for r in results]
    means, ses = aggregate(trajectories)
    metrics_5 = ["constraint", "party_sep", "affect", "within_party_sd"]
    years = [1990, 2000, 2010, 2020, 2025]
    cells_4x5 = []
    for year in years:
        for metric in metrics_5:
            band = PRIMARY_TARGETS[year][metric]
            v = means[year][metric]
            cells_4x5.append({
                "year": year, "metric": metric,
                "value": v, "se": ses[year][metric],
                "band_lo": band[0], "band_hi": band[1],
                "in_band": bool(in_band(v, band)),
            })
    init_metrics = ["variance", "constraint", "party_sep", "within_party_sd"]
    cells_init = []
    for metric in init_metrics:
        band = INITIAL_TARGETS_1980[metric]
        v = means[1980][metric]
        cells_init.append({
            "year": 1980, "metric": metric,
            "value": v, "se": ses[1980][metric],
            "band_lo": band[0], "band_hi": band[1],
            "in_band": bool(in_band(v, band)),
        })
    n_4x5 = sum(c["in_band"] for c in cells_4x5)
    n_init = sum(c["in_band"] for c in cells_init)
    n_24 = n_4x5 + n_init
    print(f"\n[gate] §11 cells in band: {n_24}/24  "
          f"(>= 18 required) — {'PASS' if n_24 >= 18 else 'FAIL'}")

    out = {
        "variant": label,
        "n_agents": N,
        "independent_fraction": INDEPENDENT_FRACTION,
        "faction_anchor_strength": strength,
        "event_stubbornness_bump_multiplier": bump,
        "factional_seeding": False,
        "seeds": list(SEEDS),
        "means": {str(y): means[y] for y in means},
        "ses": {str(y): ses[y] for y in ses},
        "cells_4x5": cells_4x5,
        "cells_1980_initial": cells_init,
        "tally_4x5": n_4x5,
        "tally_4x5_total": 20,
        "tally_24": n_24,
        "tally_24_total": 24,
        "gate_pass_18_of_24": bool(n_24 >= 18),
    }
    with open("phase9_section11_under_tier_c_blessed.json", "w",
              encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"[dump] {Path('phase9_section11_under_tier_c_blessed.json').resolve()}")


if __name__ == "__main__":
    main()
