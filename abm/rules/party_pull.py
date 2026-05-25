"""
Party pull — elite-cue mechanism (Hetherington 2001; Levendusky 2009).

Agents' issue positions drift toward their affiliated party's centroid,
with magnitude modulated by their identity_strength. Strong identifiers
respond more to elite cues; weak identifiers drift more from interpersonal
influence alone.

Reads:
  agent.state.attrs["party"]              -- party id
  agent.state.attrs["identity_strength"]  -- [0, 1], default 0.5
  env.attrs["parties"]                    -- {party_id: ndarray ideology}
"""
from __future__ import annotations

import numpy as np

from ..core.agent import Agent
from ..core.environment import Environment
from ..core.space import ContinuousSpace2D
from ..core.state import StateDelta


class PartyPull:
    def __init__(self, strength: float = 0.05):
        self.strength = strength

    def apply(
        self,
        agent: Agent,
        space: ContinuousSpace2D,
        env: Environment,
        rng: np.random.Generator,
    ) -> StateDelta:
        if self.strength == 0:
            return StateDelta()
        party = agent.state.attrs.get("party")
        parties = env.attrs.get("parties", {})
        if party is None or party not in parties:
            return StateDelta()
        target = parties[party]
        s = float(agent.state.attrs.get("identity_strength", 0.5))
        return StateDelta(d_ideology=self.strength * s * (target - agent.state.ideology))
