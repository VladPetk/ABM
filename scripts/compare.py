"""
Side-by-side validation runs for Chunk B.

  python scripts/compare.py sorting    # Mason: identity sorting amplifies affective polarization
  python scripts/compare.py parties    # Gidron: multi-party has lower affective polarization than 2-party
"""
from __future__ import annotations

import sys

import numpy as np

from abm.metrics import affective_polarization, ideological_constraint, sorting_index, variance
from abm.scenarios.elite_dynamics import build as build_elite
from abm.scenarios.multi_party_4 import build as build_multi
from abm.scenarios.two_party_sorting import build as build_two


def _summary(eng, label: str):
    pos = eng.positions()
    aff = affective_polarization(eng.agents)
    ic = ideological_constraint(eng.agents)
    si = sorting_index(eng.agents)
    si_str = f"{si:.3f}" if si == si else "  n/a"
    print(
        f"  {label:>26}: "
        f"variance={variance(pos):.3f}  "
        f"affect={aff:+.3f}  "
        f"constraint={(ic['x']+ic['y'])/2:.3f}  "
        f"sorting={si_str}"
    )


def run_sorting_comparison(steps: int = 500, seed: int = 0, n: int = 200):
    print(f"\n=== Mason: identity sorting amplifies affective polarization "
          f"(two_party_sorting, n={n}, {steps} ticks) ===", flush=True)
    ids_no_sort = build_two(n_agents=n, n_identities=3, sort_rate=0.0, identity_weight=0.5, seed=seed)
    ids_no_sort.run(steps)
    _summary(ids_no_sort, "ids, no sorting")

    ids_sort = build_two(n_agents=n, n_identities=3, sort_rate=0.1, sort_step=0.1, identity_weight=0.5, seed=seed)
    ids_sort.run(steps)
    _summary(ids_sort, "ids + sorting")

    print("\nExpected: 'ids + sorting' should show MORE NEGATIVE affect "
          "AND higher sorting index than 'ids, no sorting' (Mason 2018).", flush=True)


def run_party_comparison(steps: int = 500, seed: int = 0, n: int = 200):
    print(f"\n=== Gidron: multi-party has lower affective polarization than "
          f"two-party (n={n}, {steps} ticks, identity sorting on) ===", flush=True)
    two = build_two(n_agents=n, n_identities=3, sort_rate=0.1, sort_step=0.1, identity_weight=0.5, seed=seed)
    two.run(steps)
    _summary(two, "two_party_sorting")

    multi = build_multi(n_agents=n, n_identities=3, sort_rate=0.1, sort_step=0.1, identity_weight=0.5, seed=seed)
    multi.run(steps)
    _summary(multi, "multi_party_4")

    print("\nExpected: 'multi_party_4' should show LESS NEGATIVE affect than "
          "'two_party_sorting' (Gidron et al. 2020).", flush=True)


def run_elite_comparison(steps: int = 600, seed: int = 0, n: int = 200):
    print(f"\n=== Hetherington: elite drift drives mass polarization "
          f"(elite_dynamics, n={n}, {steps} ticks) ===", flush=True)
    no_elite = build_elite(
        n_agents=n, elite_drift_rate=0.0, media_period=0,
        media_consumption_strength=0.0, seed=seed,
    )
    no_elite.run(steps)
    party_sep = float(np.linalg.norm(no_elite.env.attrs["parties"][1] - no_elite.env.attrs["parties"][0]))
    print(f"  {'no elite drift / media':>26}: party_sep={party_sep:.3f}  ", end="")
    _summary(no_elite, "")

    with_elite = build_elite(
        n_agents=n, elite_drift_rate=0.0012, media_period=80,
        media_strength=0.06, media_consumption_strength=0.04, seed=seed,
    )
    with_elite.run(steps)
    party_sep2 = float(np.linalg.norm(with_elite.env.attrs["parties"][1] - with_elite.env.attrs["parties"][0]))
    print(f"  {'elite drift + media':>26}: party_sep={party_sep2:.3f}  ", end="")
    _summary(with_elite, "")

    print("\nExpected: 'elite drift + media' should show wider party separation, "
          "MORE negative affect, and higher ideological constraint (Hetherington 2001).", flush=True)


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which in ("sorting", "all"):
        run_sorting_comparison()
    if which in ("parties", "all"):
        run_party_comparison()
    if which in ("elite", "all"):
        run_elite_comparison()
