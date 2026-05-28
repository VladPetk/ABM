"""Phase 9 §11.7-A — Score any config under BOTH old + ANES §11 bands.

Phase A entrypoint. Existing scripts (phase9_tier_d_central.py, etc.)
keep using the old `PRIMARY_TARGETS`; this one calls
`get_primary_targets(use_anes_bands=...)` and reports cells-in-band
under BOTH band sets side-by-side. That gives a clean diff per cell so
we can see exactly which cells flipped just from re-banding (no engine
change) and which are honest fails against ANES.

Presets:
  --config baseline        Phase 8f baseline (no Tier C/D)
  --config tier_c_blessed  Tier C FactionAnchor (strength=0.04)
  --config tier_d_central  Tier D 6-lever rebalance (central estimates)
  --config s11_6_winner    The §11.6 winner (cohort_fix + lever1_off +
                           y=0.15 + sigma_y=0.15) — morning report's pick
  --config s11_7_option_b  §11.7 Option B (lever1 ON + isotropic sigma=0.12)

Output:
  phase9_anes_score_<config>.json   — per-decade W2 + §11 cells under
                                       OLD and ANES bands side by side.
"""
from __future__ import annotations

import argparse
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
    (1980, 0),
    (1990, 30),
    (2000, 60),
    (2010, 90),
    (2020, 120),
]
SECTION11_TICKS = [(1990, 30), (2000, 60), (2010, 90),
                   (2020, 120), (2025, 135)]


# ---------------------------------------------------------------------
# Presets — each is a kwargs dict for build_engine. Names map to
# experiments referenced in PHASE9_HANDOFF.md / morning report.
# ---------------------------------------------------------------------

PRESETS = {
    "baseline": {
        "n_agents": N,
        "independent_fraction": INDEPENDENT_FRACTION,
        "factional_seeding": False,
        # No Tier C/D — Phase 8f head.
    },
    "tier_c_blessed": {
        "n_agents": N,
        "independent_fraction": INDEPENDENT_FRACTION,
        "factional_seeding": False,
        "faction_anchor_strength": 0.04,
        "faction_anchor_events": True,
        "event_stubbornness_bump_multiplier": 1.0,
    },
    "tier_d_central": {
        "n_agents": N,
        "independent_fraction": INDEPENDENT_FRACTION,
        "factional_seeding": False,
        "faction_anchor_strength": 0.04,
        "faction_anchor_events": True,
        "event_stubbornness_bump_multiplier": 1.0,
        "tier_d_axis_balance": True,
    },
    "s11_6_winner": {
        # The "safer" Option A from PHASE9_HANDOFF.md §5.
        "n_agents": N,
        "independent_fraction": INDEPENDENT_FRACTION,
        "factional_seeding": False,
        "faction_anchor_strength": 0.04,
        "faction_anchor_events": True,
        "event_stubbornness_bump_multiplier": 1.0,
        "tier_d_axis_balance": True,
        "tier_d_lever1_off": True,
        "tier_d_cohort_y_signs_fix": True,
        "tier_d_party_center_y": 0.15,
        "tier_d_aniso_noise_sigma_y": 0.15,
    },
    "s11_7_option_b": {
        # The "better shape" Option B — isotropic noise lift on both axes.
        "n_agents": N,
        "independent_fraction": INDEPENDENT_FRACTION,
        "factional_seeding": False,
        "faction_anchor_strength": 0.04,
        "faction_anchor_events": True,
        "event_stubbornness_bump_multiplier": 1.0,
        "tier_d_axis_balance": True,
        "tier_d_lever1_off": False,
        "tier_d_cohort_y_signs_fix": True,
        "tier_d_party_center_y": 0.20,
        "tier_d_aniso_noise_sigma_x": 0.12,
        "tier_d_aniso_noise_sigma_y": 0.12,
    },
    "anes_knobs": {
        # Phase 9 §11.7-B — ANES-derived knob set on top of Tier D
        # axis-balance. Replaces party centers, K-schedule, party_cue σ,
        # ElitDrift rates/asymmetric with empirical-ANES values.
        # No anisotropic noise (let σ_pc do the work) and no
        # tier_d_party_center_y override (ANES centers are asymmetric).
        "n_agents": N,
        "independent_fraction": INDEPENDENT_FRACTION,
        "factional_seeding": False,
        "faction_anchor_strength": 0.04,
        "faction_anchor_events": True,
        "event_stubbornness_bump_multiplier": 1.0,
        "tier_d_axis_balance": True,
        "tier_d_lever1_off": True,             # softer party sort
        "tier_d_cohort_y_signs_fix": True,     # §11.6 bug fix
        "tier_d_anes_knobs": True,             # the new Phase B switch
    },
    "anes_full": {
        # Phase 9 §11.7-D — full ANES pipeline:
        # B (ANES knobs) + C (identity pull + BC softening + noise) +
        # D-1 (cohort centroid anchor) + D-2 (widened outlets) +
        # D-3 (per-axis EliteDrift y/x ratio 1.3) + D-4 (narrower IC σ).
        "n_agents": N,
        "independent_fraction": INDEPENDENT_FRACTION,
        "factional_seeding": False,
        "faction_anchor_strength": 0.04,
        "faction_anchor_events": True,
        "event_stubbornness_bump_multiplier": 1.0,
        "tier_d_axis_balance": True,
        "tier_d_lever1_off": True,
        "tier_d_cohort_y_signs_fix": True,
        "tier_d_anes_knobs": True,
        "tier_d_anes_drift_multiplier": 3.0,
        "tier_d_anes_sigma_pc_multiplier": 1.6,
        "tier_c_identity_pull_x": 0.020,    # back near §11.7-D peak
        "tier_c_identity_pull_y": 0.040,
        "tier_d_aniso_noise_sigma_x": 0.08,
        "tier_d_aniso_noise_sigma_y": 0.08,
        "tier_c_party_pull_strength": 0.04,
        "tier_c_bc_strength": 0.015,
        "tier_d_coupling_rho": 0.30,        # IC x-y correlation (mild)
        "tier_d_cue_correlation": 0.60,     # D5: cue + per-tick noise ρ
    },
}


def _worker(args: tuple) -> dict:
    """Build, run, snapshot at decade ticks; measure §11 metrics.

    args = (seed, preset_name)
    """
    seed, preset_name = args
    from abm.pillars.historical_arc import build_engine, build_schedule
    from abm.pillars.schedule import run_to
    from scripts.phase8f_lib import measure_all

    kwargs = dict(PRESETS[preset_name])
    eng = build_engine(seed=seed, **kwargs)
    sched = build_schedule(
        factional_seeding=kwargs.get("factional_seeding", False),
        faction_anchor_events=kwargs.get("faction_anchor_events", True),
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


def _score_cells(means, ses, primary_targets, initial_targets):
    """Return (cells_4x5, cells_init, tally_4x5, tally_init, tally_24)."""
    from scripts.phase8f_lib import in_band

    metrics_5 = ["constraint", "party_sep", "affect", "within_party_sd"]
    years = [1990, 2000, 2010, 2020, 2025]
    cells_4x5 = []
    for year in years:
        for metric in metrics_5:
            band = primary_targets[year][metric]
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
        band = initial_targets[metric]
        v = means[1980][metric]
        cells_init.append({
            "year": 1980, "metric": metric,
            "value": v, "se": ses[1980][metric],
            "band_lo": band[0], "band_hi": band[1],
            "in_band": bool(in_band(v, band)),
        })
    n_4x5 = sum(c["in_band"] for c in cells_4x5)
    n_init = sum(c["in_band"] for c in cells_init)
    return cells_4x5, cells_init, n_4x5, n_init, n_4x5 + n_init


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, choices=list(PRESETS))
    parser.add_argument("--seeds", type=int, default=5,
                        help="Number of seeds (default 5).")
    parser.add_argument("--out-dir", default="docs/results",
                        help="Output dir for the JSON dump.")
    parser.add_argument("--processes", type=int, default=None,
                        help="Pool size; defaults to min(seeds, ncpu).")
    args = parser.parse_args()

    from abm.calibration_parallel import ci_95, run_seeds_parallel
    from abm.calibration_phase9 import (
        EMPIRICAL_DECADES, pot_available, score_engine_run,
    )
    from scripts.phase8f_lib import (
        get_primary_targets, get_initial_targets_1980, aggregate,
    )

    seeds = tuple(range(args.seeds))
    pname = args.config

    print("=" * 78)
    print(f"Phase 9 ANES-band scorer — preset={pname}  n_seeds={args.seeds}")
    print(f"  POT available: {pot_available()}")
    print(f"  build kwargs: {PRESETS[pname]}")
    print("=" * 78)

    # Run workers (each takes (seed, preset_name) tuple).
    work_args = [(s, pname) for s in seeds]
    results = run_seeds_parallel(
        _wrap_worker, work_args, processes=args.processes,
    )

    # --- Wasserstein scoring (vs current data/phase9_empirical, which is
    #     now ANES-derived per the 2026-05-28 rebuild) ---
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
    print("\n[w2] decade  W2_mean   ±CI95   corr   var_x   var_y")
    for decade in EMPIRICAL_DECADES:
        sub = combined[combined["decade"] == decade]
        w_vals = sub["wasserstein"].tolist()
        w_mean = float(np.mean(w_vals))
        lo, hi = ci_95(w_vals)
        hw = float((hi - lo) / 2.0)
        per_decade[str(decade)] = {
            "w2_mean": w_mean,
            "w2_ci95_halfwidth": hw,
            "corr_xy": float(sub["corr_xy"].mean()),
            "var_x": float(sub["var_x"].mean()),
            "var_y": float(sub["var_y"].mean()),
        }
        w2_total += w_mean
        print(f"  {decade}    {w_mean:.4f}   ±{hw:.4f}   "
              f"{per_decade[str(decade)]['corr_xy']:+.3f}   "
              f"{per_decade[str(decade)]['var_x']:.3f}   "
              f"{per_decade[str(decade)]['var_y']:.3f}")
    print(f"  ----  w2_total = {w2_total:.4f}")

    # --- §11 under BOTH band sets ---
    trajectories = [r["trajectory"] for r in results]
    means, ses = aggregate(trajectories)

    old_pri = get_primary_targets(use_anes_bands=False)
    old_init = get_initial_targets_1980(use_anes_bands=False)
    anes_pri = get_primary_targets(use_anes_bands=True)
    anes_init = get_initial_targets_1980(use_anes_bands=True)

    cells_old_4x5, cells_old_init, n_old_4x5, n_old_init, n_old_24 = \
        _score_cells(means, ses, old_pri, old_init)
    cells_anes_4x5, cells_anes_init, n_anes_4x5, n_anes_init, n_anes_24 = \
        _score_cells(means, ses, anes_pri, anes_init)

    print(f"\n[s11] OLD bands : {n_old_24}/24 cells "
          f"({n_old_4x5}/20 mainframe + {n_old_init}/4 IC)  "
          f"{'PASS' if n_old_24 >= 18 else 'FAIL'} (>=18)")
    print(f"[s11] ANES bands: {n_anes_24}/24 cells "
          f"({n_anes_4x5}/20 mainframe + {n_anes_init}/4 IC)  "
          f"{'PASS' if n_anes_24 >= 18 else 'FAIL'} (>=18)")

    # Per-cell diff (which cells flipped between band sets)
    flips = []
    for c_old, c_anes in zip(cells_old_4x5, cells_anes_4x5):
        if c_old["in_band"] != c_anes["in_band"]:
            flips.append({
                "year": c_old["year"], "metric": c_old["metric"],
                "value": c_old["value"],
                "old_band": [c_old["band_lo"], c_old["band_hi"]],
                "anes_band": [c_anes["band_lo"], c_anes["band_hi"]],
                "old_in_band": c_old["in_band"],
                "anes_in_band": c_anes["in_band"],
            })
    for c_old, c_anes in zip(cells_old_init, cells_anes_init):
        if c_old["in_band"] != c_anes["in_band"]:
            flips.append({
                "year": c_old["year"], "metric": c_old["metric"],
                "value": c_old["value"],
                "old_band": [c_old["band_lo"], c_old["band_hi"]],
                "anes_band": [c_anes["band_lo"], c_anes["band_hi"]],
                "old_in_band": c_old["in_band"],
                "anes_in_band": c_anes["in_band"],
            })
    if flips:
        print(f"\n[diff] {len(flips)} cells flipped between OLD and ANES bands:")
        for f in flips:
            arrow = "OLD->ANES: " + (
                "in->out" if f["old_in_band"] else "out->in"
            )
            print(f"  {f['year']} {f['metric']:<16}  v={f['value']:+.3f}  "
                  f"OLD{f['old_band']}  ANES{f['anes_band']}  {arrow}")

    out = {
        "preset": pname,
        "seeds": list(seeds),
        "build_kwargs": PRESETS[pname],
        "pot_available": pot_available(),
        "w2_total": w2_total,
        "per_decade": per_decade,
        "means": {str(y): means[y] for y in means},
        "ses": {str(y): ses[y] for y in ses},
        "s11_old_bands": {
            "tally_24": n_old_24, "tally_4x5": n_old_4x5,
            "tally_init": n_old_init,
            "cells_4x5": cells_old_4x5,
            "cells_init": cells_old_init,
            "pass_18_of_24": bool(n_old_24 >= 18),
        },
        "s11_anes_bands": {
            "tally_24": n_anes_24, "tally_4x5": n_anes_4x5,
            "tally_init": n_anes_init,
            "cells_4x5": cells_anes_4x5,
            "cells_init": cells_anes_init,
            "pass_18_of_24": bool(n_anes_24 >= 18),
        },
        "band_flips": flips,
    }
    out_path = Path(args.out_dir) / f"phase9_anes_score_{pname}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"\n[dump] {out_path.resolve()}")


def _wrap_worker(args):
    """Top-level wrapper so multiprocessing can pickle it."""
    return _worker(args)


if __name__ == "__main__":
    main()
