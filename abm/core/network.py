"""
Social tie network — the influence substrate (ADR-001).

The network is *the* substrate of influence: ``BoundedConfidenceInfluence``
and the other proximity rules iterate ``Network.neighbors(agent.id)``, not a
spatial radius query. Ideology space holds agent state and feeds homophily
on the build / rewire path; it no longer decides who hears whom.

Edges are undirected — ``j in net.neighbors(i)  iff  i in net.neighbors(j)``.
A subset of edges may be marked **involuntary** (kin, workplace); these are
exempt from homophilous rewiring. Build functions create zero involuntary
edges for now — the capability ships inert until Phase 4 activates it.

``Network.complete`` is the canonical-mode constructor: bounded-confidence on a
complete graph recovers classic Hegselmann-Krause exactly (ADR-001 §7).
``Network.homophilous`` wraps ``generate_homophilous_network`` for the pillar.
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


class Network:
    """The social graph over agent ids — the influence substrate (ADR-001).

    Undirected: ``j in adj[i] iff i in adj[j]``. Edges may carry two
    independent metadata flags:

    - ``involuntary`` (kin/workplace ties, Phase 4 F3) — exempt from
      homophilous ``TieRewiring`` rewiring.
    - ``cooperative`` (Allport-conditions contact, Phase 7 X6) — the
      affect channel (``AffectiveUpdate``) mutes negative valence on
      these edges by ``AffectiveUpdate.cooperative_mute``. Represents
      shared-institution contact under equal-status / cooperative-task /
      institutional-support conditions (Pettigrew & Tropp 2006). Mere
      involuntary contact (F3 baseline) does NOT carry cooperative
      conditions; the literature is explicit that contact alone is
      insufficient.

    The two flags are independent: X6's added edges are both involuntary
    and cooperative; F3's baseline involuntary edges are not cooperative.
    """

    def __init__(self, adjacency, involuntary=None, cooperative=None):
        self._adj: dict[int, set[int]] = {
            i: set(ns) for i, ns in adjacency.items()
        }
        # involuntary edges as canonical (min_id, max_id) pairs.
        self._involuntary: set[tuple[int, int]] = (
            set(involuntary) if involuntary else set()
        )
        # cooperative edges as canonical (min_id, max_id) pairs.
        self._cooperative: set[tuple[int, int]] = (
            set(cooperative) if cooperative else set()
        )

    # --- constructors ---
    @classmethod
    def complete(cls, node_ids):
        ids = list(node_ids)
        idset = set(ids)
        return cls({i: idset - {i} for i in ids})

    @classmethod
    def homophilous(cls, agents, rng, **kwargs):
        return cls(generate_homophilous_network(agents, rng, **kwargs))

    # --- queries ---
    def neighbors(self, i):
        return self._adj.get(i, set())

    def degree(self, i):
        return len(self._adj.get(i, ()))

    def has_edge(self, i, j):
        return j in self._adj.get(i, ())

    def edges(self):
        """Each undirected edge once, as (i, j) with i < j."""
        for i, ns in self._adj.items():
            for j in ns:
                if j > i:
                    yield (i, j)

    def is_involuntary(self, i, j):
        return (min(i, j), max(i, j)) in self._involuntary

    def is_cooperative(self, i, j):
        return (min(i, j), max(i, j)) in self._cooperative

    @property
    def node_ids(self):
        return self._adj.keys()

    @property
    def adjacency(self):
        return self._adj

    # --- mutation (TieRewiring + Phase 6 setup hooks) ---
    def add_edge(self, i, j, involuntary: bool = False, cooperative: bool = False):
        self._adj[i].add(j)
        self._adj[j].add(i)
        key = (min(i, j), max(i, j))
        if involuntary:
            self._involuntary.add(key)
        if cooperative:
            self._cooperative.add(key)

    def remove_edge(self, i, j):
        self._adj[i].discard(j)
        self._adj[j].discard(i)
        key = (min(i, j), max(i, j))
        self._involuntary.discard(key)
        self._cooperative.discard(key)


def generate_involuntary_edges(
    network: "Network",
    agents,
    rng: np.random.Generator,
    per_agent: int = 2,
) -> int:
    """Add cross-party involuntary edges to ``network`` (Mutz & Mondak 2006:
    kin and workplace ties cross party more often than voluntary discussion
    partners; the involuntary stratum is what keeps cross-cutting exposure
    above zero in a homophilous society).

    Targets ``per_agent * n / 2`` edges total, sampled uniformly across
    cross-party agent pairs that are not already connected. The actual
    count per agent varies (no per-agent rejection sampling — keeps
    generation O(target) and reproducible). Existing voluntary edges that
    happen to be cross-party are left alone; only newly-added edges are
    marked involuntary.

    Returns the number of involuntary edges placed. Caller is expected to
    use the same RNG stream as the homophilous-network build
    (``net_rng = seed + 9973``) so the involuntary stratum is reproducible
    without disturbing the main RNG.
    """
    target = (per_agent * len(agents)) // 2
    if target <= 0:
        return 0
    by_party: dict[object, list[int]] = {}
    for a in agents:
        by_party.setdefault(a.state.attrs["party"], []).append(a.id)
    parties = list(by_party)
    if len(parties) < 2:
        return 0
    placed = 0
    attempts = 0
    max_attempts = 20 * target
    while placed < target and attempts < max_attempts:
        attempts += 1
        # Two distinct parties; one agent from each.
        pair = rng.choice(len(parties), size=2, replace=False)
        p = parties[int(pair[0])]
        q = parties[int(pair[1])]
        i = int(rng.choice(by_party[p]))
        j = int(rng.choice(by_party[q]))
        if network.has_edge(i, j):
            continue
        network.add_edge(i, j, involuntary=True)
        placed += 1
    return placed


def neighbor_agents(agent, space, env):
    """An agent's network neighbours as ``Agent`` objects, ascending id order.

    Used by every network-mediated rule so the migration is uniform.
    Ascending id order keeps every run deterministic (ADR-001 impl-spec E8).
    Raises ``KeyError`` if no network has been placed in ``env`` — every
    ``build()`` must place one (E2).
    """
    network: Network = env.attrs["network"]
    roster = space.agents_by_id
    return [roster[j] for j in sorted(network.neighbors(agent.id))]
