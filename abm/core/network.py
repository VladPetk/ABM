"""
Social tie network — adjacency, distance, and a homophilous generator.

Edges are undirected; stored as ``dict[int, set[int]]`` where
``j in net[i]  iff  i in net[j]``. We keep the structure flat (no Graph
object) so it can live in ``env.attrs["network"]`` and be picked apart
by rules and metrics without a wrapper API.

The network is built once in ``calm_to_camps.build_engine`` with a
dedicated RNG (phase3 spec E1) so the main-build stream stays
bit-identical to Phase 1/2 and the measured S0–S3 thresholds do not
shift. ``TieRewiring`` (Phase 3b) is the only thing allowed to mutate
the network at run time.
"""
from __future__ import annotations

import numpy as np


def combined_distance(a, b, w_ideo: float = 1.0, w_soc: float = 1.0) -> float:
    """Distance in the (ideology, social_coord) space used for homophily.

    Ideology contributes the Euclidean norm of the 2D ideology vector;
    ``social_coord`` is a scalar in [-1, 1] (set in ``build_engine``).
    Both terms are weighted so calibration can rebalance them without
    touching call sites.
    """
    d_ideo = float(np.linalg.norm(a.state.ideology - b.state.ideology))
    d_soc = abs(
        a.state.attrs["social_coord"] - b.state.attrs["social_coord"]
    )
    return w_ideo * d_ideo + w_soc * d_soc


def generate_homophilous_network(
    agents,
    rng: np.random.Generator,
    *,
    w_ideo: float = 1.0,
    w_soc: float = 1.0,
    tau: float = 0.40,
    p_local: float = 0.55,
    p_bridge: float = 0.002,
) -> dict[int, set[int]]:
    """Build a symmetric adjacency dict, edge prob falls with distance.

    Edge probability is ``p_local * exp(-d / tau) + p_bridge`` clipped
    to 1, where ``d`` is the combined ideology+social distance. The
    ``p_bridge`` term seeds a handful of distance-independent bridge
    ties (so the graph is never two perfectly isolated camps).

    ``tau`` / ``p_local`` are the knobs for mean degree (calibrated in
    phase3 spec §11 to land in ~6-10).
    """
    net: dict[int, set[int]] = {a.id: set() for a in agents}
    n = len(agents)
    for i in range(n):
        ai = agents[i]
        for j in range(i + 1, n):
            d = combined_distance(ai, agents[j], w_ideo, w_soc)
            p = min(1.0, p_local * float(np.exp(-d / tau)) + p_bridge)
            if rng.random() < p:
                net[ai.id].add(agents[j].id)
                net[agents[j].id].add(ai.id)
    return net
