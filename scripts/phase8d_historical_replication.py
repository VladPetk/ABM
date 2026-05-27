"""Phase 8d historical re-run on the augmented engine.

Same 1980→2025 decade-by-decade scenario as Phase 8b, but on the
engine that now carries:

- Phase 8c §2 — positive-going affect channel + agent-level
  cooperative mute (Pettigrew 2009 secondary-transfer).
- Phase 8c §3 — per-outlet media exposure.
- Phase 8c §4 — perception-gap construct (perceived_other_party
  with extreme_bias = 0.25; PerceptionUpdate at rate 0.01).
- Phase 8c §5 — identity-threat dynamics (2016 status-threat
  event for 60% of party=1 agents; ThreatDecay at 0.05/tick).
- Phase 8c §6 — asymmetric BacklashRepulsion (used by X1; the
  historical scenario's baseline `BacklashRepulsion.strength = 0`
  means asymmetric doesn't fire in baseline).
- Phase 8d — 12% pure Independents (party=2) per Klar & Krupnikov
  2016 + ANES "pure independents" share.

Uses the Phase 8c §1.5 parallel-seed runner — historical 15 seeds
run in parallel (the 8b serial baseline took ~8 hours; this runs
in ~10-15 minutes).

Outputs per-decade ensemble means against the Phase 8b pre-
registered targets, and prints a comparison summary.

Run: `python scripts/phase8d_historical_replication.py`.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np

# Force single-threaded BLAS in main; workers inherit via
# `_pool_initializer`.
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

from abm.calibration_parallel import run_seeds_parallel
from abm.metrics.affective import affective_polarization, ideological_constraint
from abm.metrics.network import cross_cutting_tie_fraction, party_modularity
from abm.metrics.polarization import variance
from abm.pillars.historical_arc import (
    DECADE_BOUNDARIES,
    build_engine,
    build_schedule,
)
from abm.pillars.schedule import run_to

SEEDS = tuple(range(20))   # Phase 8f §1: 15 → 20 seeds for combo_JJ verify
N = 250
INDEPENDENT_FRACTION = 0.12

# Pre-registered Phase 8b targets — frozen, do not adjust.
PRIMARY_TARGETS = {
    1990: {
        "constraint": (0.35, 0.50),
        "party_sep": (0.50, 0.65),
        "affect": (-0.45, -0.30),
        "within_party_sd": (0.18, 0.32),
    },
    2000: {
        "constraint": (0.45, 0.60),
        "party_sep": (0.55, 0.70),
        "affect": (-0.55, -0.40),
        "within_party_sd": (0.18, 0.30),
    },
    2010: {
        "constraint": (0.55, 0.70),
        "party_sep": (0.60, 0.75),
        "affect": (-0.65, -0.50),
        "within_party_sd": (0.17, 0.28),
    },
    2020: {
        "constraint": (0.60, 0.75),
        "party_sep": (0.65, 0.80),
        "affect": (-0.78, -0.60),
        "within_party_sd": (0.15, 0.25),
    },
    2025: {
        "constraint": (0.62, 0.78),
        "party_sep": (0.68, 0.82),
        "affect": (-0.85, -0.65),
        "within_party_sd": (0.15, 0.22),
    },
}
SECONDARY_TARGETS = {
    1990: {"variance": (0.40, 0.55), "xc_fraction": (0.25, 0.35),
           "modularity": (0.15, 0.25)},
    2000: {"variance": (0.30, 0.45), "xc_fraction": (0.20, 0.30),
           "modularity": (0.20, 0.30)},
    2010: {"variance": (0.20, 0.35), "xc_fraction": (0.18, 0.28),
           "modularity": (0.25, 0.38)},
    2020: {"variance": (0.15, 0.25), "xc_fraction": (0.15, 0.25),
           "modularity": (0.30, 0.42)},
    2025: {"variance": (0.13, 0.20), "xc_fraction": (0.15, 0.25),
           "modularity": (0.32, 0.45)},
}
INITIAL_TARGETS_1980 = {
    "variance": (0.45, 0.60),
    "constraint": (0.25, 0.40),
    "party_sep": (0.45, 0.60),
    "affect": (-0.35, -0.20),
    "within_party_sd": (0.20, 0.35),
    "xc_fraction": (0.30, 0.40),
}

# Phase 8b baseline measurements (from phase8b_results.md).
PHASE_8B_BASELINE = {
    1980: {"variance": 0.42, "constraint": 0.41, "party_sep": 0.72,
           "affect": -0.25, "within_party_sd": 0.31, "xc_fraction": 0.34,
           "modularity": None},
    1990: {"variance": 0.17, "constraint": 0.45, "party_sep": 0.58,
           "affect": -0.60, "within_party_sd": 0.18, "xc_fraction": 0.31,
           "modularity": 0.18},
    2000: {"variance": 0.10, "constraint": 0.49, "party_sep": 0.50,
           "affect": -0.76, "within_party_sd": 0.12, "xc_fraction": 0.29,
           "modularity": 0.21},
    2010: {"variance": 0.09, "constraint": 0.54, "party_sep": 0.51,
           "affect": -0.84, "within_party_sd": 0.11, "xc_fraction": 0.27,
           "modularity": 0.23},
    2020: {"variance": 0.11, "constraint": 0.58, "party_sep": 0.58,
           "affect": -0.89, "within_party_sd": 0.10, "xc_fraction": 0.25,
           "modularity": 0.25},
    2025: {"variance": 0.12, "constraint": 0.59, "party_sep": 0.61,
           "affect": -0.90, "within_party_sd": 0.10, "xc_fraction": 0.24,
           "modularity": 0.25},
}


# --- metric helpers ----------------------------------------------------


def constraint_avg(eng):
    ic = ideological_constraint(eng.agents)
    return (ic["x"] + ic["y"]) / 2.0


def party_sep(eng):
    parties = np.array([a.state.attrs["party"] for a in eng.agents])
    pos = eng.positions()
    if (parties == 0).sum() == 0 or (parties == 1).sum() == 0:
        return 0.0
    return float(np.linalg.norm(
        pos[parties == 0].mean(axis=0) - pos[parties == 1].mean(axis=0)
    ))


def within_party_sd_x(eng):
    parties = np.array([a.state.attrs["party"] for a in eng.agents])
    pos = eng.positions()
    sds = []
    for p in (0, 1):
        mask = parties == p
        if mask.sum() > 1:
            sds.append(float(pos[mask, 0].std()))
    return float(np.mean(sds)) if sds else 0.0


def measure_all(eng):
    return {
        "variance": float(variance(eng.positions())),
        "constraint": constraint_avg(eng),
        "party_sep": party_sep(eng),
        "affect": affective_polarization(eng.agents),
        "within_party_sd": within_party_sd_x(eng),
        "xc_fraction": cross_cutting_tie_fraction(
            eng.agents, eng.env.attrs["network"]),
        "modularity": party_modularity(
            eng.agents, eng.env.attrs["network"]),
    }


# --- parallel worker (top-level for multiprocessing.spawn) ------------


def _trajectory_worker(seed: int) -> dict:
    """Build a historical_arc engine at the given seed with 12%
    Independents; run the full 1980→2025 schedule, capturing
    metrics at each decade boundary (1980, 1990, 2000, 2010, 2020,
    2025). Returns {year: metrics_dict}."""
    eng = build_engine(
        seed=seed, n_agents=N, independent_fraction=INDEPENDENT_FRACTION,
    )
    sched = build_schedule()
    trajectory: dict = {1980: measure_all(eng)}
    decade_ticks = [(1990, 30), (2000, 60), (2010, 90), (2020, 120), (2025, 135)]
    for year, tick in decade_ticks:
        run_to(eng, sched, tick)
        trajectory[year] = measure_all(eng)
    return trajectory


# --- summary printing -------------------------------------------------


def in_band(value, band) -> bool:
    lo, hi = band
    return lo <= value <= hi


def fmt_row(name, target, measured, baseline):
    """Format one row: name, target band, measured (8d), baseline (8b)."""
    lo, hi = target
    target_str = f"[{lo:+.2f}, {hi:+.2f}]" if lo < 0 else f"[{lo:.2f}, {hi:.2f}]"
    in_band_now = "✓" if in_band(measured, target) else "✗"
    baseline_str = f"{baseline:+.3f}" if baseline is not None else "n/a"
    return (
        f"  {name:<22}  {target_str:<20}  "
        f"{measured:+.3f} {in_band_now}    "
        f"baseline 8b: {baseline_str}"
    )


def main():
    print("=" * 78)
    print("Phase 8d historical re-run — augmented engine (8c + 12% Independents)")
    print(f"  N={N}, 1980→2025 (135 ticks), {len(SEEDS)} seeds, "
          f"parallel-seed runner")
    print(f"  independent_fraction = {INDEPENDENT_FRACTION}")
    print("=" * 78)

    print("\n[run] launching 15-seed ensemble in parallel...")
    trajectories = run_seeds_parallel(_trajectory_worker, SEEDS)
    print(f"[run] complete — {len(trajectories)} seed trajectories collected")

    # Ensemble means per year.
    years = [1980, 1990, 2000, 2010, 2020, 2025]
    means: dict[int, dict] = {}
    ses: dict[int, dict] = {}
    for year in years:
        per_metric_values = {}
        for m in trajectories[0][year]:
            per_metric_values[m] = [traj[year][m] for traj in trajectories]
        means[year] = {
            m: float(np.mean(v)) for m, v in per_metric_values.items()
        }
        ses[year] = {
            m: float(np.std(v, ddof=1) / np.sqrt(len(v)))
            for m, v in per_metric_values.items()
        }

    # 1980 initial conditions.
    print("\n[1980] initial conditions vs pre-registered band")
    for name, band in INITIAL_TARGETS_1980.items():
        m = means[1980][name]
        b = PHASE_8B_BASELINE[1980].get(name)
        print(fmt_row(name, band, m, b))

    # Per-decade primary.
    for year in (1990, 2000, 2010, 2020, 2025):
        print(f"\n[{year}] primary metrics")
        for name, band in PRIMARY_TARGETS[year].items():
            m = means[year][name]
            b = PHASE_8B_BASELINE[year].get(name)
            print(fmt_row(name, band, m, b))
        print(f"\n[{year}] secondary metrics (reported only)")
        for name, band in SECONDARY_TARGETS[year].items():
            m = means[year][name]
            b = PHASE_8B_BASELINE[year].get(name)
            print(fmt_row(name, band, m, b))

    # SE summary.
    print("\n[SE] standard errors at 15 seeds")
    print(f"  year       constraint    party_sep    affect       w_party_sd")
    for year in years:
        c = ses[year]["constraint"]
        p = ses[year]["party_sep"]
        a = ses[year]["affect"]
        s = ses[year]["within_party_sd"]
        print(
            f"  {year}       {c:.4f}       {p:.4f}      {a:.4f}      {s:.4f}"
        )

    # Headline comparison.
    print("\n[headline] comparison to Phase 8b baseline (2025 endpoints)")
    for metric in ("constraint", "party_sep", "affect", "within_party_sd"):
        m_8d = means[2025][metric]
        m_8b = PHASE_8B_BASELINE[2025][metric]
        lo, hi = PRIMARY_TARGETS[2025][metric]
        center = (lo + hi) / 2.0
        delta_8d = m_8d - center
        delta_8b = m_8b - center
        # Closer to band when |delta_8d| < |delta_8b|.
        closer = "closer" if abs(delta_8d) < abs(delta_8b) else (
            "further" if abs(delta_8d) > abs(delta_8b) else "same"
        )
        print(
            f"  {metric:<20}  8b={m_8b:+.3f}  8d={m_8d:+.3f}  "
            f"target=[{lo:+.3f}, {hi:+.3f}]  ({closer} to band)"
        )

    # Dump JSON.
    out_path = Path("phase8d_historical_results.json")
    with open(out_path, "w", encoding="utf-8") as fp:
        json.dump({
            "metadata": {
                "n_agents": N,
                "independent_fraction": INDEPENDENT_FRACTION,
                "seeds": list(SEEDS),
                "years": years,
            },
            "means": {str(y): means[y] for y in years},
            "ses": {str(y): ses[y] for y in years},
            "phase_8b_baseline": {
                str(y): PHASE_8B_BASELINE[y] for y in years
            },
            "primary_targets": {
                str(y): PRIMARY_TARGETS[y]
                for y in PRIMARY_TARGETS
            },
            "secondary_targets": {
                str(y): SECONDARY_TARGETS[y]
                for y in SECONDARY_TARGETS
            },
            "initial_targets_1980": INITIAL_TARGETS_1980,
        }, fp, indent=2)
    print(f"\n[dump] {out_path.resolve()}")

    print("\n" + "=" * 78)


if __name__ == "__main__":
    main()
