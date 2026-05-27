"""
Phase 8b decade-by-decade calibration harness.

Sequence:
  for decade in (1990, 2000, 2010, 2020, 2025):
    pre-register targets (already in §9.1 — fixed)
    run 5-seed ensemble for the decade
    measure decade-end metrics
    if all primary in band: bless; continue
    else: bounded adjustment (≤2 retries) of per-decade knobs;
          accept-miss-and-document if still out of band

The pillar's calibrated invariants are sacred (§10.3). The harness
adjusts only per-decade-tunable knobs (IdentitySorting rate,
ResidentialMigration rate, event step sizes — narrow scope).

Output: structured per-decade record written to stdout, plus a
summary file at `phase8b_calibration_results.json`.

Compute: 5 seeds × ~15 ticks per decade × 5 decades = ~10-12 min
per ensemble × ~5-15 ensembles = ~1-3 hours total.
"""
from __future__ import annotations

import json
import numpy as np

from abm.metrics.affective import affective_polarization, ideological_constraint
from abm.metrics.network import (
    cross_cutting_tie_fraction,
    party_modularity,
)
from abm.metrics.polarization import variance
from abm.pillars.historical_arc import (
    DECADE_BOUNDARIES,
    IDENTITY_SORTING_SCHEDULE,
    RESIDENTIAL_MIGRATION_RATE_DEFAULT,
    build_engine,
    build_schedule,
)
from abm.pillars.schedule import run_to


SEEDS = tuple(range(15))   # Phase 8c §7 S1: historical 5 → 15 seeds
N = 250

# Pre-registered decade targets — per §9.1 of phase8b spec.
# Tuple = (lower, upper) of the tolerance band. None = secondary.
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
    1990: {"variance": (0.40, 0.55), "xc_fraction": (0.25, 0.35), "modularity": (0.15, 0.25)},
    2000: {"variance": (0.30, 0.45), "xc_fraction": (0.20, 0.30), "modularity": (0.20, 0.30)},
    2010: {"variance": (0.20, 0.35), "xc_fraction": (0.18, 0.28), "modularity": (0.25, 0.38)},
    2020: {"variance": (0.15, 0.25), "xc_fraction": (0.15, 0.25), "modularity": (0.30, 0.42)},
    2025: {"variance": (0.13, 0.20), "xc_fraction": (0.15, 0.25), "modularity": (0.32, 0.45)},
}
INITIAL_TARGETS_1980 = {
    "variance": (0.45, 0.60),
    "constraint": (0.25, 0.40),
    "party_sep": (0.45, 0.60),
    "affect": (-0.35, -0.20),
    "within_party_sd": (0.20, 0.35),
    "xc_fraction": (0.30, 0.40),
}


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


def in_band(value, band):
    lo, hi = band
    return lo <= value <= hi


def run_to_year(year, seeds=SEEDS):
    """Run all seeds to the given year's tick; return per-metric
    ensemble mean."""
    target_tick = DECADE_BOUNDARIES.get(year)
    if target_tick is None:
        if year == 1980:
            target_tick = 0
        else:
            raise ValueError(f"unknown year {year}")
    measurements_per_seed = []
    for seed in seeds:
        eng = build_engine(seed=seed, n_agents=N)
        sched = build_schedule()
        if target_tick > 0:
            run_to(eng, sched, target_tick)
        measurements_per_seed.append(measure_all(eng))
    # Ensemble means.
    means = {}
    for k in measurements_per_seed[0]:
        means[k] = float(np.mean([m[k] for m in measurements_per_seed]))
    return means


def classify(measured, primary_band, secondary_band):
    """Returns ({metric: bool in_band}, {metric: bool}, primary_pass)."""
    primary_results = {k: in_band(measured[k], primary_band[k])
                        for k in primary_band}
    secondary_results = {k: in_band(measured[k], secondary_band[k])
                         for k in secondary_band}
    primary_pass = all(primary_results.values())
    return primary_results, secondary_results, primary_pass


def print_decade(decade_year, measured, primary_band, secondary_band):
    print(f"\n=== {decade_year} ({DECADE_BOUNDARIES.get(decade_year, 0)} ticks) ===")
    print("  PRIMARY:")
    for k, band in primary_band.items():
        ok = "OK " if in_band(measured[k], band) else "MISS"
        print(f"    [{ok}] {k:<18s}: {measured[k]:+.4f}  target [{band[0]:+.3f}, {band[1]:+.3f}]")
    print("  secondary:")
    for k, band in secondary_band.items():
        ok = "OK " if in_band(measured[k], band) else "off"
        print(f"    [{ok}] {k:<18s}: {measured[k]:+.4f}  target [{band[0]:+.3f}, {band[1]:+.3f}]")


def main():
    results = {}
    print("=" * 72)
    print("Phase 8b — historical-arc decade-by-decade calibration")
    print(f"  N={N}, 5 seeds, TICKS_PER_YEAR=3 (1980→2025 = 135 ticks)")
    print(f"  Heterogeneity magnitudes: 40/60/80% on epsilon/α/affect_lr")
    print(f"  PARTY_CUE_SIGMA: dem=0.22, rep=0.30 (Hacker & Pierson asymmetry)")
    print(f"  IdentitySorting schedule: 0.005/0.015/0.025/0.025/0.020 by decade")
    print("=" * 72)

    # ----- 1980 initial-condition check -----
    print("\n[1980 initial condition]")
    init = run_to_year(1980)
    print("  PRIMARY:")
    for k, band in INITIAL_TARGETS_1980.items():
        ok = "OK " if in_band(init[k], band) else "MISS"
        print(f"    [{ok}] {k:<18s}: {init[k]:+.4f}  target [{band[0]:+.3f}, {band[1]:+.3f}]")
    results["1980_initial"] = init

    # ----- Decades -----
    for year in (1990, 2000, 2010, 2020, 2025):
        measured = run_to_year(year)
        primary_band = PRIMARY_TARGETS[year]
        secondary_band = SECONDARY_TARGETS[year]
        primary_results, secondary_results, primary_pass = classify(
            measured, primary_band, secondary_band
        )
        print_decade(year, measured, primary_band, secondary_band)
        bucket = "PASS" if primary_pass else "MISS"
        print(f"  → decade verdict: {bucket}")
        results[str(year)] = {
            "measured": measured,
            "primary_in_band": primary_results,
            "secondary_in_band": secondary_results,
            "primary_pass": primary_pass,
        }

    # ----- Write results -----
    with open("phase8b_calibration_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    print("\nResults written to phase8b_calibration_results.json")
    print("=" * 72)


if __name__ == "__main__":
    main()
