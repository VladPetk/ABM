"""
Affective update — out-party warmth/coolness from interactions
(Banisch-Olbrich 2019 reinforcement route, extended with Mason 2018
mega-identity weighting).

For each neighbor of a *different* party within `radius`, the agent updates
its affect toward that party. The valence is a blend of:
- Ideological similarity: 1 at d=0, -1 at d=radius
- Identity similarity (when both agents carry an identities vector): mean
  per-dimension agreement, mapped to [-1, +1]

`identity_weight` ∈ [0, 1] mixes the two. With identity_weight=0 the rule
collapses to pure ideological proximity (Banisch-Olbrich). With it >0 and
identity sorting active, the Mason finding emerges: sorted partisans show
stronger out-party hostility even at equal *issue* distance because they
share fewer identities.

Reads:
  agent.state.attrs["party"]
  agent.state.attrs["affect"]       -- dict {other_party_id: warmth}
  agent.state.attrs["identities"]   -- ndarray (optional)
  neighbor.state.attrs["party"]
  neighbor.state.attrs["identities"] (optional)

Writes (delta):
  d_attrs["affect"] = {other_party_id: cumulative_warmth_change}
"""
from __future__ import annotations

import numpy as np

from ..core.agent import Agent
from ..core.environment import Environment
from ..core.space import ContinuousSpace2D
from ..core.state import StateDelta


class AffectiveUpdate:
    def __init__(
        self,
        radius: float = 0.5,
        learning_rate: float = 0.01,
        identity_weight: float = 0.0,
    ):
        self.radius = radius
        self.lr = learning_rate
        self.identity_weight = identity_weight

    def apply(
        self,
        agent: Agent,
        space: ContinuousSpace2D,
        env: Environment,
        rng: np.random.Generator,
    ) -> StateDelta:
        if self.lr == 0:
            return StateDelta()
        agent_party = agent.state.attrs.get("party")
        if agent_party is None:
            return StateDelta()
        neighbors = space.neighbors_within(agent.state.ideology, self.radius, exclude_id=agent.id)
        if not neighbors:
            return StateDelta()

        my_ids = agent.state.attrs.get("identities")
        use_ids = self.identity_weight > 0 and my_ids is not None and len(my_ids) > 0

        affect_delta: dict = {}
        for neighbor in neighbors:
            other_party = neighbor.state.attrs.get("party")
            if other_party is None or other_party == agent_party:
                continue
            d = float(np.linalg.norm(agent.state.ideology - neighbor.state.ideology))
            ideological_sim = 1.0 - 2.0 * d / self.radius

            if use_ids:
                their_ids = neighbor.state.attrs.get("identities")
                if their_ids is not None and len(their_ids) == len(my_ids):
                    # Mean per-dimension agreement: 1 - |Δ|/2 ∈ [0, 1], rescaled to [-1, +1]
                    diffs = np.abs(np.asarray(my_ids) - np.asarray(their_ids))
                    identity_sim = float(1.0 - np.mean(diffs))   # in [-1, 1] for ids in [-1, 1]
                    valence = (1.0 - self.identity_weight) * ideological_sim + self.identity_weight * identity_sim
                else:
                    valence = ideological_sim
            else:
                valence = ideological_sim

            affect_delta[other_party] = affect_delta.get(other_party, 0.0) + self.lr * valence

        if not affect_delta:
            return StateDelta()
        return StateDelta(d_attrs={"affect": affect_delta})
