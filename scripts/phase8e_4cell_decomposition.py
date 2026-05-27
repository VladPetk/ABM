"""Phase 8e §4 — 4-cell decomposition of the 2025 affect-in-band finding.

Disambiguates whether the Phase 8d 2025-affect-in-band result is
*compositional* (12% null-affect Independents pulling mean affect
less-negative) or *mechanism-driven* (8c §2/§4/§5 + 8e.2/§3
improvements). Per round-2 R2 review.

Four cells:

  Cell A: 8b baseline engine, 0.0 Independents  → expected ~-0.90
  Cell B: 8b baseline engine, 0.12 Independents → ? (composition only)
  Cell C: augmented engine, 0.0 Independents    → ? (mechanism only)
  Cell D: augmented engine, 0.12 Independents   → ~-0.79 (full Phase 8e)

Honest reading:
  (D - A) = (B - A) + (C - A)  → additive (both contribute)
  (D - A) ≈ (B - A), (C - A) ≈ 0 → compositional only (Independents alone explain it)
  (D - A) ≈ (C - A), (B - A) ≈ 0 → mechanism only

Run: `python scripts/phase8e_4cell_decomposition.py`.
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

from abm.calibration_parallel import run_seeds_parallel
from abm.metrics.affective import affective_polarization, ideological_constraint
from abm.metrics.network import (
    cross_cutting_tie_fraction,
    party_modularity,
)
from abm.metrics.polarization import variance
from abm.pillars.historical_arc import build_engine, build_schedule
from abm.pillars.schedule import run_to

SEEDS = tuple(range(15))
N = 250


def _measure(eng) -> dict:
    parties = np.array([a.state.attrs.get("party") for a in eng.agents])
    pos = eng.positions()
    if (parties == 0).sum() > 0 and (parties == 1).sum() > 0:
        sep = float(np.linalg.norm(
            pos[parties == 0].mean(axis=0) - pos[parties == 1].mean(axis=0)
        ))
    else:
        sep = 0.0
    ic = ideological_constraint(eng.agents)
    return {
        "affect": affective_polarization(eng.agents),
        "constraint": (ic["x"] + ic["y"]) / 2.0,
        "party_sep": sep,
    }


def _worker_A(seed: int) -> dict:
    """Cell A: 8b baseline engine (no 8c/8e mechanisms), 0% Independents."""
    eng = build_engine(
        seed=seed, n_agents=N, independent_fraction=0.0,
        phase8e_baseline=True,
    )
    run_to(eng, build_schedule(), 135)
    return _measure(eng)


def _worker_B(seed: int) -> dict:
    """Cell B: 8b baseline engine, 12% Independents."""
    eng = build_engine(
        seed=seed, n_agents=N, independent_fraction=0.12,
        phase8e_baseline=True,
    )
    run_to(eng, build_schedule(), 135)
    return _measure(eng)


def _worker_C(seed: int) -> dict:
    """Cell C: augmented engine (8c/8e on), 0% Independents."""
    eng = build_engine(
        seed=seed, n_agents=N, independent_fraction=0.0,
        phase8e_baseline=False,
    )
    run_to(eng, build_schedule(), 135)
    return _measure(eng)


def _worker_D(seed: int) -> dict:
    """Cell D: augmented engine, 12% Independents (= Phase 8d)."""
    eng = build_engine(
        seed=seed, n_agents=N, independent_fraction=0.12,
        phase8e_baseline=False,
    )
    run_to(eng, build_schedule(), 135)
    return _measure(eng)


def main():
    print("=" * 78)
    print("Phase 8e §4 — 4-cell decomposition of 2025 affect-in-band")
    print(f"  N={N}, 1980→2025 (135 ticks), {len(SEEDS)} seeds × 4 cells")
    print("=" * 78)

    cells = [
        ("A: baseline / 0% indep", _worker_A),
        ("B: baseline / 12% indep", _worker_B),
        ("C: augmented / 0% indep", _worker_C),
        ("D: augmented / 12% indep", _worker_D),
    ]
    results: dict[str, dict[str, dict]] = {}
    for name, worker in cells:
        print(f"\n[run] {name}")
        per_seed = run_seeds_parallel(worker, SEEDS)
        per_metric = {
            m: [r[m] for r in per_seed]
            for m in per_seed[0]
        }
        means = {m: float(np.mean(v)) for m, v in per_metric.items()}
        ses = {
            m: float(np.std(v, ddof=1) / np.sqrt(len(v)))
            for m, v in per_metric.items()
        }
        results[name] = {"means": means, "ses": ses}
        for m in ("affect", "constraint", "party_sep"):
            print(f"  {m:<14} = {means[m]:+.4f} ± {ses[m]:.4f}")

    # Decomposition table.
    a = results["A: baseline / 0% indep"]["means"]
    b = results["B: baseline / 12% indep"]["means"]
    c = results["C: augmented / 0% indep"]["means"]
    d = results["D: augmented / 12% indep"]["means"]

    print("\n[decomposition] 2025 affect attribution")
    print(f"  Cell A (baseline/0%):    {a['affect']:+.4f}")
    print(f"  Cell B (baseline/12%):   {b['affect']:+.4f}")
    print(f"  Cell C (augmented/0%):   {c['affect']:+.4f}")
    print(f"  Cell D (augmented/12%):  {d['affect']:+.4f}")
    print()
    print(f"  Compositional shift (B - A):  {b['affect'] - a['affect']:+.4f}")
    print(f"  Mechanism shift (C - A):      {c['affect'] - a['affect']:+.4f}")
    print(f"  Combined shift (D - A):       {d['affect'] - a['affect']:+.4f}")
    print(f"  Sum (B - A) + (C - A):        {(b['affect'] - a['affect']) + (c['affect'] - a['affect']):+.4f}")
    print()
    print(f"  Interaction (D - A - (B - A) - (C - A)):  {d['affect'] - a['affect'] - (b['affect'] - a['affect']) - (c['affect'] - a['affect']):+.4f}")

    # Attribution share.
    comp_share = (b["affect"] - a["affect"]) / (d["affect"] - a["affect"]) if (d["affect"] - a["affect"]) != 0 else float("nan")
    mech_share = (c["affect"] - a["affect"]) / (d["affect"] - a["affect"]) if (d["affect"] - a["affect"]) != 0 else float("nan")
    print(f"\n  Compositional share of full improvement: {comp_share:.1%}")
    print(f"  Mechanism share of full improvement:     {mech_share:.1%}")

    out_path = Path("phase8e_4cell_decomposition.json")
    with open(out_path, "w", encoding="utf-8") as fp:
        json.dump(results, fp, indent=2)
    print(f"\n[dump] {out_path.resolve()}")
    print("\n" + "=" * 78)


if __name__ == "__main__":
    main()
