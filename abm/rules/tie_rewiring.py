"""
TieRewiring — slow homophilous co-evolution of the social network.

Each tick, each agent with probability ``rewire_rate`` drops its most
ideologically-distant current tie and forms a new tie to the closest
of ``n_candidates`` random non-neighbours. Combined distance uses the
same ``(ideology, social_coord)`` metric as the generator, so
homophily is consistent. Degree is preserved (one out, one in).

``rewire_rate = 0`` is an exact no-op — the rule returns immediately —
so S0-S3 can carry it in their bundles without effect.

This is an ``EnvRule`` because it mutates world state (the adjacency
dict at ``env.attrs["network"]``), not a single agent.
"""
from __future__ import annotations

import numpy as np

from ..core.agent import Agent
from ..core.environment import Environment
from ..core.network import combined_distance
from ..core.space import ContinuousSpace2D


class TieRewiring:
    def __init__(
        self,
        rewire_rate: float = 0.0,
        w_ideo: float = 1.0,
        w_soc: float = 1.0,
        n_candidates: int = 10,
    ):
        self.rewire_rate = rewire_rate
        self.w_ideo = w_ideo
        self.w_soc = w_soc
        self.n_candidates = n_candidates

    def apply(
        self,
        env: Environment,
        agents: list[Agent],
        space: ContinuousSpace2D,
        rng: np.random.Generator,
        tick: int,
    ) -> None:
        if self.rewire_rate <= 0:
            return
        net = env.attrs.get("network")
        if net is None:
            return
        by_id = {a.id: a for a in agents}
        for a in agents:
            if rng.random() > self.rewire_rate:
                continue
            ties = net[a.id]
            if not ties:
                continue

            # Drop the most ideologically-distant current tie.
            drop = max(
                ties,
                key=lambda j: combined_distance(
                    a, by_id[j], self.w_ideo, self.w_soc
                ),
            )
            net[a.id].discard(drop)
            net[drop].discard(a.id)

            # Add a tie to the closest of n_candidates random non-neighbours.
            pool = [
                x for x in agents
                if x.id != a.id and x.id not in net[a.id]
            ]
            if not pool:
                continue
            k = min(self.n_candidates, len(pool))
            idxs = rng.integers(0, len(pool), size=k)
            cand = [pool[int(i)] for i in idxs]
            new = min(
                cand,
                key=lambda x: combined_distance(a, x, self.w_ideo, self.w_soc),
            )
            net[a.id].add(new.id)
            net[new.id].add(a.id)
