"""
Perception update — slow correction of perceived out-party positions
toward observed neighbour positions (Phase 8c §4 E4.4).

Each agent that carries `perceived_other_party: dict[int, np.ndarray]`
holds a *belief* about each out-party's centroid position. The
belief is initially seeded biased outward (Levendusky & Malhotra
2016; Ahler & Sood 2018; Druckman et al. 2022 — Americans
systematically over-estimate the out-party's extremity).
`PerceptionUpdate` corrects the belief slowly each tick by averaging
toward the agent's actually-observed out-party neighbours' positions.

Mechanism per tick:

  For each out-party `p`:
    observed_p = mean(neighbor.ideology for neighbor in out-party-p neighbours)
    perceived_other_party[p] += correction_rate * (observed_p - perceived_other_party[p])

The rate is small (default 0.01) — agents update their beliefs
slowly because (a) cross-cutting contact is rare, (b) people
typecast / discount disconfirming evidence (Taber & Lodge 2006;
Levendusky & Malhotra 2016 finds correction is possible but slow
even with concerted prime).

**Pillar-fallback discipline.** When an agent doesn't carry
`perceived_other_party`, the rule no-ops (returns empty StateDelta).
The pillar's S0-S4 builds do NOT seed the attribute — pillar
bit-identical to Phase 8b. Historical-arc agents DO carry it; the
rule fires there. `strength = 0` also no-ops (a defensive zero
short-circuit, mirroring other rules' convention).

Reads:
  agent.state.attrs["party"]
  agent.state.attrs["perceived_other_party"]    -- dict[int, np.ndarray]
  neighbour.state.attrs["party"]
  neighbour.state.ideology

Writes (delta):
  d_attrs["perceived_other_party"] = {other_party: delta_ndarray}
"""
from __future__ import annotations

import numpy as np

from ..core.agent import Agent
from ..core.environment import Environment
from ..core.network import neighbor_agents
from ..core.space import ContinuousSpace2D
from ..core.state import StateDelta


class PerceptionUpdate:
    def __init__(self, correction_rate: float = 0.01):
        # `correction_rate = 0` is an exact no-op (defensive guard:
        # the pillar's S0-S4 bundles carry strength=0 so the rule is
        # inert in pillar contexts).
        self.correction_rate = correction_rate

    def apply(
        self,
        agent: Agent,
        space: ContinuousSpace2D,
        env: Environment,
        rng: np.random.Generator,
    ) -> StateDelta:
        if self.correction_rate == 0:
            return StateDelta()
        agent_party = agent.state.attrs.get("party")
        if agent_party is None:
            return StateDelta()
        perceived = agent.state.attrs.get("perceived_other_party")
        if perceived is None or not perceived:
            # Pillar-fallback: agent doesn't carry the perception attr.
            return StateDelta()
        neighbors = neighbor_agents(agent, space, env)
        if not neighbors:
            return StateDelta()
        # Group out-party neighbours by their actual party.
        by_party: dict = {}
        for n in neighbors:
            n_party = n.state.attrs.get("party")
            if n_party is None or n_party == agent_party:
                continue
            by_party.setdefault(n_party, []).append(n.state.ideology)
        if not by_party:
            return StateDelta()
        deltas: dict[int, np.ndarray] = {}
        for other_party, positions in by_party.items():
            current = perceived.get(other_party)
            if current is None:
                continue
            mean_obs = np.mean(positions, axis=0)
            delta = self.correction_rate * (mean_obs - current)
            deltas[other_party] = delta
        if not deltas:
            return StateDelta()
        return StateDelta(d_attrs={"perceived_other_party": deltas})
