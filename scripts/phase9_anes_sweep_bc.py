"""Phase 9 §11.7-C — BC strength × PartyPull strength sweep.

Tests whether reducing BoundedConfidenceInfluence.strength (currently
0.08) breaks the wp_sd ceiling. If wp_sd_2020 finally exceeds 0.25
when BC is softened, BC was the clamp. Otherwise something else.
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

DECADE_TICKS = [(1980, 0), (1990, 30), (2000, 60), (2010, 90), (2020, 120)]
SECTION11_TICKS = [(1990, 30), (2000, 60), (2010, 90), (2020, 120), (2025, 135)]


def _kwargs(bc, pp):
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
        tier_d_anes_drift_multiplier=3.0,
        tier_d_anes_sigma_pc_multiplier=1.6,
        tier_c_identity_pull_x=0.015,
        tier_c_identity_pull_y=0.040,
        tier_d_aniso_noise_sigma_x=0.025,
        tier_d_aniso_noise_sigma_y=0.025,
        tier_c_party_pull_strength=pp,
        tier_c_bc_strength=bc,
    )


def _worker(args):
    seed, bc, pp = args
    from abm.pillars.historical_arc import build_engine, build_schedule
    from abm.pillars.schedule import run_to
    from scripts.phase8f_lib import measure_all

    eng = build_engine(seed=seed, **_kwargs(bc, pp))
    sched = build_schedule(factional_seeding=False, faction_anchor_events=True)
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


def _score(results, seeds):
    from abm.calibration_phase9 import EMPIRICAL_DECADES, score_engine_run
    from scripts.phase8f_lib import (
        get_primary_targets, get_initial_targets_1980, aggregate, in_band,
    )
    import pandas as pd

    dfs = []
    for s, r in zip(seeds, results):
        df = score_engine_run(
            positions_by_decade=r["snapshots"],
            target_dir=Path("data/phase9_empirical"),
            seed_for_subsample=s,
        )
        df.insert(0, "seed", s)
        dfs.append(df)
    comb = pd.concat(dfs, ignore_index=True)
    w2 = 0.0
    pd_ = {}
    for d in EMPIRICAL_DECADES:
        sub = comb[comb["decade"] == d]
        pd_[str(d)] = {
            "w2_mean": float(sub["wasserstein"].mean()),
            "corr_xy": float(sub["corr_xy"].mean()),
            "var_x": float(sub["var_x"].mean()),
            "var_y": float(sub["var_y"].mean()),
        }
        w2 += pd_[str(d)]["w2_mean"]
    traj = [r["trajectory"] for r in results]
    means, ses = aggregate(traj)
    anes_pri = get_primary_targets(use_anes_bands=True)
    anes_init = get_initial_targets_1980(use_anes_bands=True)
    metrics_5 = ["constraint", "party_sep", "affect", "within_party_sd"]
    n_4x5 = 0
    for y in [1990, 2000, 2010, 2020, 2025]:
        for m in metrics_5:
            if in_band(means[y][m], anes_pri[y][m]):
                n_4x5 += 1
    n_init = sum(
        in_band(means[1980][m], anes_init[m])
        for m in ["variance", "constraint", "party_sep", "within_party_sd"]
    )
    return {
        "w2_total": float(w2),
        "per_decade": pd_,
        "anes_tally_24": int(n_4x5 + n_init),
        "anes_tally_4x5": int(n_4x5),
        "anes_tally_init": int(n_init),
        "means_2020": means[2020],
        "means_1980": means[1980],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=4)
    parser.add_argument("--bc-grid", default="0.08,0.05,0.03,0.015")
    parser.add_argument("--pp-grid", default="0.04,0.02")
    parser.add_argument("--out", default="docs/results/phase9_anes_sweep_bc.json")
    args = parser.parse_args()

    from abm.calibration_parallel import run_seeds_parallel
    from abm.calibration_phase9 import pot_available

    bcs = [float(x) for x in args.bc_grid.split(",")]
    pps = [float(x) for x in args.pp_grid.split(",")]
    seeds = list(range(args.seeds))

    print(f"BC × PartyPull sweep, {args.seeds} seeds/cell, POT={pot_available()}")
    print(f"  bc_grid: {bcs}")
    print(f"  pp_grid: {pps}")

    rows = []
    for bc, pp in itertools.product(bcs, pps):
        work = [(s, bc, pp) for s in seeds]
        results = run_seeds_parallel(_wrap, work)
        scored = _score(results, seeds)
        scored["bc"] = bc
        scored["pp"] = pp
        rows.append(scored)
        m20 = scored["means_2020"]
        m80 = scored["means_1980"]
        print(f"  bc={bc:.3f}  pp={pp:.3f}  "
              f"§11_ANES={scored['anes_tally_24']}/24  "
              f"w2={scored['w2_total']:.3f}  "
              f"1980 wp_sd={m80['within_party_sd']:.3f}  "
              f"2020 sep={m20['party_sep']:.3f} "
              f"wp_sd={m20['within_party_sd']:.3f} "
              f"corr={scored['per_decade']['2020']['corr_xy']:+.3f} "
              f"var_y={scored['per_decade']['2020']['var_y']:.3f}")

    rows.sort(key=lambda r: (-r["anes_tally_24"], r["w2_total"]))
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"seeds": seeds, "rows": rows}, f, indent=2)
    win = rows[0]
    print(f"\n[winner] bc={win['bc']}  pp={win['pp']}  "
          f"§11={win['anes_tally_24']}/24  w2={win['w2_total']:.3f}")


def _wrap(args):
    return _worker(args)


if __name__ == "__main__":
    main()
