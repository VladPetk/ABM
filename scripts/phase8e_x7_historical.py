"""Phase 8e §4 — X7 historical-arc measurement (R1 round-2 request).

Fires X7 (`X7_PERCEPTION_CORRECTION`) in the historical scenario at
tick 90 (=2010) and tick 105 (=2015). Measures trajectory delta vs
the unfired 8e-augmented baseline at the 2025 endpoint.

The pillar-context X7 was null/null because pillar agents don't seed
`perceived_other_party`. The historical context DOES — agents are
seeded with extreme_bias = 0.25 at build and PerceptionUpdate
corrects slowly. X7 resets all agents' perceived positions to actual
centroids; the trajectory afterward shows whether perception
correction has measurable downstream effects on affect / sep /
constraint.

Run: `python scripts/phase8e_x7_historical.py`.
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
from abm.pillars import X7_PERCEPTION_CORRECTION, apply_intervention
from abm.pillars.historical_arc import build_engine, build_schedule
from abm.pillars.schedule import run_to

SEEDS = tuple(range(15))
N = 250
INDEP_FRACTION = 0.12


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


def _build():
    return None  # placeholder; workers build directly with their seed


def _worker_baseline(seed: int) -> dict:
    """8e-augmented engine, NO X7 fired. Reference trajectory."""
    eng = build_engine(seed=seed, n_agents=N, independent_fraction=INDEP_FRACTION)
    run_to(eng, build_schedule(), 135)
    return _measure(eng)


def _worker_x7_2010(seed: int) -> dict:
    """X7 fired at tick 90 (=2010); run to 2025."""
    eng = build_engine(seed=seed, n_agents=N, independent_fraction=INDEP_FRACTION)
    sched = build_schedule()
    run_to(eng, sched, 90)
    apply_intervention(eng, X7_PERCEPTION_CORRECTION)
    run_to(eng, sched, 135)
    return _measure(eng)


def _worker_x7_2015(seed: int) -> dict:
    """X7 fired at tick 105 (=2015); run to 2025."""
    eng = build_engine(seed=seed, n_agents=N, independent_fraction=INDEP_FRACTION)
    sched = build_schedule()
    run_to(eng, sched, 105)
    apply_intervention(eng, X7_PERCEPTION_CORRECTION)
    run_to(eng, sched, 135)
    return _measure(eng)


def main():
    print("=" * 78)
    print("Phase 8e §4 — X7 historical-arc measurement")
    print(f"  N={N}, indep_fraction={INDEP_FRACTION}, {len(SEEDS)} seeds × 3 cells")
    print("=" * 78)

    cells = [
        ("baseline (no X7)", _worker_baseline),
        ("X7 fired at 2010 (tick 90)", _worker_x7_2010),
        ("X7 fired at 2015 (tick 105)", _worker_x7_2015),
    ]
    results = {}
    for name, worker in cells:
        print(f"\n[run] {name}")
        per_seed = run_seeds_parallel(worker, SEEDS)
        per_metric = {m: [r[m] for r in per_seed] for m in per_seed[0]}
        means = {m: float(np.mean(v)) for m, v in per_metric.items()}
        ses = {
            m: float(np.std(v, ddof=1) / np.sqrt(len(v)))
            for m, v in per_metric.items()
        }
        results[name] = {"means": means, "ses": ses}
        for m in ("affect", "constraint", "party_sep"):
            print(f"  {m:<14} = {means[m]:+.4f} ± {ses[m]:.4f}")

    base = results["baseline (no X7)"]["means"]
    x7_10 = results["X7 fired at 2010 (tick 90)"]["means"]
    x7_15 = results["X7 fired at 2015 (tick 105)"]["means"]

    print("\n[delta] X7 effect on 2025 endpoint vs baseline")
    for m in ("affect", "constraint", "party_sep"):
        d_2010 = x7_10[m] - base[m]
        d_2015 = x7_15[m] - base[m]
        print(
            f"  Δ{m:<14}  X7@2010: {d_2010:+.4f}  X7@2015: {d_2015:+.4f}"
        )

    out_path = Path("phase8e_x7_historical.json")
    with open(out_path, "w", encoding="utf-8") as fp:
        json.dump(results, fp, indent=2)
    print(f"\n[dump] {out_path.resolve()}")
    print("\n" + "=" * 78)


if __name__ == "__main__":
    main()
