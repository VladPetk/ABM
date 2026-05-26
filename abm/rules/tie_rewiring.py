"""
TieRewiring — slow homophilous co-evolution of the social network.

Each tick, each agent with probability ``rewire_rate`` drops its most
ideologically-distant **voluntary** current tie and forms a new tie to
the closest of ``n_candidates`` random non-neighbours. Combined distance
uses the same ``(ideology, social_coord)`` metric as the generator.
Involuntary ties (kin, workplace — Phase 4 F3) are exempt from rewiring.

Phase 5 (A5) adds ``affect_weight_rewire``: the drop ranking augments
the combined distance with the agent's affect toward each voluntary
tie's party. Cold out-party ties get a higher drop score; warm ones get
a lower score (and are preserved). ``affect_weight_rewire = 0.0`` is the
default and is an exact no-op — Phase 4 behaviour preserved.

``rewire_rate = 0`` is an exact no-op — the rule returns immediately —
so S0-S3 carry it in their bundles without effect.

This is an ``EnvRule`` because it mutates world state (the ``Network``
at ``env.attrs["network"]``), not a single agent.
"""
from __future__ import annotations

import numpy as np

from ..core.agent import Agent
from ..core.environment import Environment
from ..core.network import Network, combined_distance
from ..core.space import ContinuousSpace2D


class TieRewiring:
    def __init__(
        self,
        rewire_rate: float = 0.0,
        w_ideo: float = 1.0,
        w_soc: float = 1.0,
        n_candidates: int = 10,
        affect_weight_rewire: float = 0.0,
    ):
        self.rewire_rate = rewire_rate
        self.w_ideo = w_ideo
        self.w_soc = w_soc
        self.n_candidates = n_candidates
        # Phase 5 (A5): bias the drop ranking by affect. Default 0.0
        # preserves Phase 4 behaviour. The pillar opts in at S2+ via
        # TR_AFFECT_WEIGHT_REWIRE in calm_to_camps.py.
        self.affect_weight_rewire = affect_weight_rewire

    def _drop_score(self, agent, j, by_id):
        """Score a tie for dropping. Higher = more droppable."""
        nbr = by_id[j]
        base = combined_distance(agent, nbr, self.w_ideo, self.w_soc)
        if self.affect_weight_rewire == 0.0:
            return base
        other_party = nbr.state.attrs.get("party")
        own_party = agent.state.attrs.get("party")
        if other_party is None or other_party == own_party:
            return base
        # Cold ties (negative warmth) raise the drop score; warm ties
        # lower it. Same-party ties keep their pure combined-distance
        # score. The underlying affect can drift well past [-1, 1]
        # (AffectiveUpdate accumulates additively; only the metric
        # clips on read), so clip here too — otherwise the affect bias
        # eventually swamps `combined_distance` and the drop ranking
        # becomes "coldest tie wins, regardless of ideology/social
        # distance," which is *not* the documented "comparable bias"
        # behaviour.
        warmth = float((agent.state.attrs.get("affect") or {}).get(other_party, 0.0))
        warmth = float(np.clip(warmth, -1.0, 1.0))
        return base + self.affect_weight_rewire * (-warmth)

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
        network: Network | None = env.attrs.get("network")
        if network is None:
            return
        by_id = {a.id: a for a in agents}
        for a in agents:
            if rng.random() > self.rewire_rate:
                continue
            ties = network.neighbors(a.id)
            # Only voluntary ties are eligible to be dropped.
            voluntary = [
                j for j in ties if not network.is_involuntary(a.id, j)
            ]
            if not voluntary:
                continue

            # Drop the highest-scoring voluntary tie (most distant on
            # combined distance, plus the affect bias if affect_weight_rewire > 0).
            drop = max(voluntary, key=lambda j: self._drop_score(a, j, by_id))
            network.remove_edge(a.id, drop)

            # Add a tie to the closest of n_candidates random non-neighbours.
            current = network.neighbors(a.id)
            pool = [
                x for x in agents
                if x.id != a.id and x.id not in current
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
            network.add_edge(a.id, new.id)
