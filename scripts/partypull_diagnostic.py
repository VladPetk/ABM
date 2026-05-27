"""Diagnostic — within-party position dispersion at S4 end.

Question: does PartyPull's single-centroid mechanic compress agents
into tight blobs around the party centroids, with within-party SD
much smaller than empirical (DW-NOMINATE within-party SD ~0.15-0.20;
ANES self-placement equivalent ~0.20-0.25 on the [-1, 1] axis)?
"""
from __future__ import annotations

import numpy as np

from abm.pillars import PILLAR, apply_intervention
from abm.pillars.calm_to_camps import build_engine

N = 250
TICKS = 200
SEEDS = tuple(range(12))


def measure_stage(stage: int):
    sds_x_by_party = {0: [], 1: []}
    sds_y_by_party = {0: [], 1: []}
    centroids_x = {0: [], 1: []}
    iqrs_x_by_party = {0: [], 1: []}
    initial_sds_x = {0: [], 1: []}
    initial_sds_y = {0: [], 1: []}
    for seed in SEEDS:
        eng = build_engine(seed=seed, n_agents=N)
        # Snapshot initial within-party SD (t=0).
        parties = np.array([a.state.attrs["party"] for a in eng.agents])
        pos0 = eng.positions()
        for p in (0, 1):
            mask = parties == p
            initial_sds_x[p].append(float(pos0[mask, 0].std()))
            initial_sds_y[p].append(float(pos0[mask, 1].std()))
        apply_intervention(eng, PILLAR.interventions[stage])
        eng.run(TICKS)
        pos = eng.positions()
        for p in (0, 1):
            mask = parties == p
            sds_x_by_party[p].append(float(pos[mask, 0].std()))
            sds_y_by_party[p].append(float(pos[mask, 1].std()))
            centroids_x[p].append(float(pos[mask, 0].mean()))
            q1, q3 = np.percentile(pos[mask, 0], [25, 75])
            iqrs_x_by_party[p].append(float(q3 - q1))
    print(f"=== Stage S{stage} (after {TICKS} ticks, {len(SEEDS)} seeds) ===")
    print(f"t=0 within-party SD_x: party0={np.mean(initial_sds_x[0]):.3f}, "
          f"party1={np.mean(initial_sds_x[1]):.3f}  "
          f"(uniform-on-half baseline ~0.29)")
    print(f"t=0 within-party SD_y: party0={np.mean(initial_sds_y[0]):.3f}, "
          f"party1={np.mean(initial_sds_y[1]):.3f}  "
          f"(uniform [-1,1] baseline ~0.58)")
    print()
    print(f"end-state within-party SD_x: party0={np.mean(sds_x_by_party[0]):.3f}, "
          f"party1={np.mean(sds_x_by_party[1]):.3f}")
    print(f"end-state within-party SD_y: party0={np.mean(sds_y_by_party[0]):.3f}, "
          f"party1={np.mean(sds_y_by_party[1]):.3f}")
    print(f"end-state party-0 x-centroid: {np.mean(centroids_x[0]):+.3f} "
          f"(target {-0.5:+.3f})")
    print(f"end-state party-1 x-centroid: {np.mean(centroids_x[1]):+.3f} "
          f"(target {0.5:+.3f})")
    print(f"end-state within-party IQR_x (P75-P25): "
          f"party0={np.mean(iqrs_x_by_party[0]):.3f}, "
          f"party1={np.mean(iqrs_x_by_party[1]):.3f}")
    print()


def main():
    print("Empirical anchors:")
    print("  DW-NOMINATE within-party SD: ~0.15-0.20 (caucus first-dimension)")
    print("  ANES self-placement: SD ~1.2-1.5 on 7pt scale -> ~0.20-0.25 on [-1,1]")
    print("  Target band: within-party SD_x ~ 0.15-0.25 on the model's axis")
    print()
    for s in (0, 1, 2, 3, 4):
        measure_stage(s)


if __name__ == "__main__":
    main()
