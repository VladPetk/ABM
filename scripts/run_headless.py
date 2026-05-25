"""
Headless smoke test — runs a chosen scenario for N ticks and prints metrics.

    python scripts/run_headless.py --scenario compass_basic --steps 200
    python scripts/run_headless.py --scenario actb --steps 200
    python scripts/run_headless.py --scenario two_party_sorting --steps 200
"""
from __future__ import annotations

import argparse

import numpy as np

from abm.metrics import (
    affective_polarization,
    bimodality,
    ideological_constraint,
    mean_pairwise_distance,
    quadrant_counts,
    sorting_index,
    variance,
)
from abm.scenarios import REGISTRY


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--scenario", default="compass_basic", choices=list(REGISTRY.keys()))
    p.add_argument("--agents", type=int, default=300)
    p.add_argument("--steps", type=int, default=200)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--every", type=int, default=25)
    args = p.parse_args()

    build = REGISTRY[args.scenario]
    engine = build(n_agents=args.agents, seed=args.seed)
    print(f"Scenario: {args.scenario}   (agents={args.agents}, steps={args.steps}, seed={args.seed})\n")

    has_parties = any(a.state.attrs.get("party") is not None for a in engine.agents)
    has_identities = any(a.state.attrs.get("identities") is not None for a in engine.agents)
    header = f"{'tick':>5}  {'var':>6}  {'mpd':>6}  {'bx':>6}  {'by':>6}"
    if has_parties:
        header += f"  {'affect':>7}  {'ic_x':>5}  {'ic_y':>5}"
    if has_identities:
        header += f"  {'sort':>5}"
    header += "  quadrants"
    print(header)

    for t in range(0, args.steps + 1):
        if t % args.every == 0 or t == args.steps:
            pos = engine.positions()
            row = (
                f"{t:>5d}  {variance(pos):>6.3f}  {mean_pairwise_distance(pos):>6.3f}  "
                f"{bimodality(pos[:, 0]):>6.3f}  {bimodality(pos[:, 1]):>6.3f}"
            )
            if has_parties:
                aff = affective_polarization(engine.agents)
                ic = ideological_constraint(engine.agents)
                row += f"  {aff:>+7.3f}  {ic['x']:>5.2f}  {ic['y']:>5.2f}"
            if has_identities:
                si = sorting_index(engine.agents)
                row += f"  {si:>5.2f}"
            q = quadrant_counts(pos)
            row += (
                f"  LL={q['lib_left']:3d} LR={q['lib_right']:3d}"
                f" AL={q['auth_left']:3d} AR={q['auth_right']:3d}"
            )
            print(row)
        if t < args.steps:
            engine.step()


if __name__ == "__main__":
    main()
