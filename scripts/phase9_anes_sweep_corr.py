"""Phase 9 — Sweep identity_pull_x × identity_pull_y × coupling_rho
to find the corr-vs-sep operating point. Phase D peak was 17/24 at
ipx=0.015, ipy=0.04, rho=0.20 with corr_2020=0.59. Boost to ipx=0.04
overshot mid-decade sep. The right point sits between.
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

DECADE_TICKS = [(1980, 0), (1990, 30), (2000, 60), (2010, 90), (2020, 120)]
SECTION11_TICKS = [(1990, 30), (2000, 60), (2010, 90), (2020, 120), (2025, 135)]


def _kwargs(ipx, ipy, rho):
    return dict(
        n_agents=250, independent_fraction=0.12,
        factional_seeding=False, faction_anchor_strength=0.04,
        faction_anchor_events=True, event_stubbornness_bump_multiplier=1.0,
        tier_d_axis_balance=True, tier_d_lever1_off=True,
        tier_d_cohort_y_signs_fix=True, tier_d_anes_knobs=True,
        tier_d_anes_drift_multiplier=3.0, tier_d_anes_sigma_pc_multiplier=1.6,
        tier_c_identity_pull_x=ipx, tier_c_identity_pull_y=ipy,
        tier_d_aniso_noise_sigma_x=0.08, tier_d_aniso_noise_sigma_y=0.08,
        tier_c_party_pull_strength=0.04, tier_c_bc_strength=0.015,
        tier_d_coupling_rho=rho,
    )


def _worker(args):
    seed, ipx, ipy, rho = args
    from abm.pillars.historical_arc import build_engine, build_schedule
    from abm.pillars.schedule import run_to
    from scripts.phase8f_lib import measure_all
    from abm.calibration_phase9 import score_engine_run

    eng = build_engine(seed=seed, **_kwargs(ipx, ipy, rho))
    sched = build_schedule(factional_seeding=False, faction_anchor_events=True)
    snapshots = {1980: np.array([a.state.ideology for a in eng.agents])}
    trajectory = {1980: measure_all(eng)}
    yat = {}
    for y, t in DECADE_TICKS:
        yat.setdefault(t, []).append(("w", y))
    for y, t in SECTION11_TICKS:
        yat.setdefault(t, []).append(("s", y))
    for t in sorted(yat):
        if t == 0:
            continue
        run_to(eng, sched, t)
        for kind, y in yat[t]:
            if kind == "w":
                snapshots[y] = np.array([a.state.ideology for a in eng.agents])
            else:
                trajectory[y] = measure_all(eng)
    df = score_engine_run(
        positions_by_decade=snapshots,
        target_dir=Path("data/phase9_empirical"),
        seed_for_subsample=seed,
    )
    return trajectory, df


def _score(results, seeds):
    from abm.calibration_phase9 import EMPIRICAL_DECADES
    from scripts.phase8f_lib import (
        get_primary_targets, get_initial_targets_1980, aggregate, in_band,
    )
    import pandas as pd

    trajectories = [t for t, _ in results]
    dfs = [df for _, df in results]
    for df, s in zip(dfs, seeds):
        df.insert(0, "seed", s)
    comb = pd.concat(dfs, ignore_index=True)
    w2_total = 0.0
    per_dec = {}
    for d in EMPIRICAL_DECADES:
        sub = comb[comb["decade"] == d]
        per_dec[d] = {
            "w2": float(sub["wasserstein"].mean()),
            "corr": float(sub["corr_xy"].mean()),
            "var_x": float(sub["var_x"].mean()),
            "var_y": float(sub["var_y"].mean()),
        }
        w2_total += per_dec[d]["w2"]
    means, _ = aggregate(trajectories)
    anes_pri = get_primary_targets(use_anes_bands=True)
    anes_init = get_initial_targets_1980(use_anes_bands=True)
    n4 = sum(
        in_band(means[y][m], anes_pri[y][m])
        for y in [1990, 2000, 2010, 2020, 2025]
        for m in ["constraint", "party_sep", "affect", "within_party_sd"]
    )
    ni = sum(
        in_band(means[1980][m], anes_init[m])
        for m in ["variance", "constraint", "party_sep", "within_party_sd"]
    )
    return {
        "tally": int(n4 + ni),
        "w2": float(w2_total),
        "per_decade": per_dec,
        "means_2020": means[2020],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument(
        "--grid",
        default="0.02,0.04,0.20;0.025,0.04,0.30;0.03,0.04,0.40;0.035,0.045,0.40;"
                "0.025,0.045,0.50;0.03,0.05,0.50;0.04,0.06,0.50",
        help="semicolon-separated ipx,ipy,rho triples",
    )
    args = parser.parse_args()

    from abm.calibration_parallel import run_seeds_parallel

    cells = []
    for triple in args.grid.split(";"):
        ipx, ipy, rho = [float(x) for x in triple.split(",")]
        cells.append((ipx, ipy, rho))
    seeds = list(range(args.seeds))

    print(f"Sweep {len(cells)} cells × {args.seeds} seeds")
    print(f"{'ipx':>7} {'ipy':>7} {'rho':>5}  §11  w2     2020:sep  wp_sd corr  var_y")
    rows = []
    for ipx, ipy, rho in cells:
        work = [(s, ipx, ipy, rho) for s in seeds]
        results = run_seeds_parallel(_worker, work)
        sc = _score(results, seeds)
        rows.append({"ipx": ipx, "ipy": ipy, "rho": rho, **sc})
        m20 = sc["means_2020"]
        print(f"{ipx:>7.3f} {ipy:>7.3f} {rho:>5.2f}  "
              f"{sc['tally']:>3d}/24 {sc['w2']:.3f}  "
              f"{m20['party_sep']:.3f}     "
              f"{m20['within_party_sd']:.3f} "
              f"{sc['per_decade'][2020]['corr']:+.3f} "
              f"{sc['per_decade'][2020]['var_y']:.3f}")

    rows.sort(key=lambda r: (-r["tally"], r["w2"]))
    with open("docs/results/phase9_anes_sweep_corr.json", "w") as f:
        json.dump(rows, f, indent=2, default=float)
    win = rows[0]
    print(f"\n[winner] ipx={win['ipx']} ipy={win['ipy']} rho={win['rho']}  "
          f"§11={win['tally']}/24  w2={win['w2']:.3f}")


if __name__ == "__main__":
    main()
