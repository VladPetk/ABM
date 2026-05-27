"""
Tie-network metrics — how cross-cutting the social graph is.

All three take ``agents`` and a ``Network`` (the ADR-001 substrate at
``env.attrs["network"]``) and aggregate party affiliation across the
edges. They are the headline measures that pillar stage S4 is supposed
to move.

- ``cross_cutting_tie_fraction`` — share of edges that join
  different-party agents. Falls as the network sorts.
- ``party_modularity`` — Newman modularity Q under the party
  partition. Rises as the network sorts.
- ``mean_ego_diversity`` — per-agent share of cross-party ties,
  averaged over agents with at least one tie.
"""
from __future__ import annotations

import numpy as np


def cross_cutting_tie_fraction(agents, network) -> float:
    """Share of edges joining agents of different party.

    Phase 8d note: when Independents (party=2) are present, Independent-
    to-partisan ties count as cross-cutting under this metric (they
    are, from a partisan perspective). For apples-to-apples comparison
    with Phase 8b binary-party measurements, use
    `partisan_cross_cutting_fraction` instead.
    """
    party = {a.id: a.state.attrs.get("party") for a in agents}
    cross = total = 0
    for (i, j) in network.edges():
        total += 1
        if party[i] != party[j]:
            cross += 1
    return cross / total if total else 0.0


def partisan_cross_cutting_fraction(agents, network) -> float:
    """Phase 8e §1: cross-cutting fraction restricted to partisan-
    partisan edges only (party 0 vs party 1). Independent ties
    (involving party=2 or any non-partisan) are excluded entirely
    — both from the numerator and the denominator.

    At `independent_fraction = 0.0` (no party=2 agents), this metric
    is bit-identical to `cross_cutting_tie_fraction`. With Independents
    present, this metric measures the *partisan-only* cross-cutting
    structure — apples-to-apples with the Phase 8b binary band.
    """
    party = {a.id: a.state.attrs.get("party") for a in agents}
    partisan_edges = 0
    cross = 0
    for (i, j) in network.edges():
        p_i = party.get(i)
        p_j = party.get(j)
        if p_i not in (0, 1) or p_j not in (0, 1):
            continue
        partisan_edges += 1
        if p_i != p_j:
            cross += 1
    return cross / partisan_edges if partisan_edges else 0.0


def party_modularity(agents, network) -> float:
    """Newman modularity Q under the party partition.

    Q = sum_c [ L_c/m - (D_c/2m)^2 ], with L_c the edges inside party
    c, D_c the total degree of party c, and m the edge count.
    """
    party = {a.id: a.state.attrs.get("party") for a in agents}
    deg = {i: network.degree(i) for i in network.node_ids}
    m = sum(deg.values()) / 2.0
    if m == 0:
        return 0.0
    L: dict[object, int] = {}
    D: dict[object, int] = {}
    for i in network.node_ids:
        c = party[i]
        D[c] = D.get(c, 0) + deg[i]
    for (i, j) in network.edges():
        if party[i] == party[j]:
            L[party[i]] = L.get(party[i], 0) + 1
    return sum(L.get(c, 0) / m - (D[c] / (2 * m)) ** 2 for c in D)


def mean_ego_diversity(agents, network) -> float:
    """Per-agent share of cross-party ties, averaged over agents with >=1 tie."""
    party = {a.id: a.state.attrs.get("party") for a in agents}
    vals = []
    for i in network.node_ids:
        nbrs = network.neighbors(i)
        if nbrs:
            vals.append(sum(party[j] != party[i] for j in nbrs) / len(nbrs))
    return float(np.mean(vals)) if vals else 0.0
