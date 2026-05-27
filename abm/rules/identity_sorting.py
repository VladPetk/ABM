"""
Identity sorting — Mason 2018 "mega-identity" mechanism.

Each agent carries a vector of cross-cutting identity dimensions (think:
secular/religious, urban/rural, college/non-college). With low probability
per tick, an agent updates one identity dimension toward a contrastive
target:

    target = in_mean + differentiation * (in_mean − out_mean)

- With differentiation=0 this collapses to "drift toward in-party mean" —
  variance shrinks within each party but cross-party means don't move.
- With differentiation>0 the rule also pushes *away* from the out-party
  mean: any initial party-identity correlation grows over time, producing
  the empirical mega-identity stacking. Bounded by the [-1, 1] clip on the
  agent state, so divergence is finite.

Default sort_rate of 0.02 ≈ one identity update per 50 ticks per agent,
matching the slow timescale of real-world sorting.

Reads:
  agent.state.attrs["party"]
  agent.state.attrs["identities"]   -- 1D ndarray, values in [-1, 1]
  (and all other agents' party + identities via the space)

Writes (delta):
  d_attrs["identities"] = ndarray (mostly zeros, one element nonzero)
"""
from __future__ import annotations

import numpy as np

from ..core.agent import Agent
from ..core.environment import Environment
from ..core.space import ContinuousSpace2D
from ..core.state import StateDelta


class IdentitySorting:
    def __init__(self, sort_rate: float = 0.02, step: float = 0.05, differentiation: float = 0.5):
        self.sort_rate = sort_rate
        self.step = step
        self.differentiation = differentiation

    def apply(
        self,
        agent: Agent,
        space: ContinuousSpace2D,
        env: Environment,
        rng: np.random.Generator,
    ) -> StateDelta:
        if self.sort_rate <= 0 or rng.random() > self.sort_rate:
            return StateDelta()
        identities = agent.state.attrs.get("identities")
        if identities is None or len(identities) == 0:
            return StateDelta()
        party = agent.state.attrs.get("party")
        if party is None:
            return StateDelta()

        dim = int(rng.integers(len(identities)))

        in_vals: list[float] = []
        out_vals: list[float] = []
        for other in space._agents:
            if other.id == agent.id:
                continue
            other_ids = other.state.attrs.get("identities")
            if other_ids is None or len(other_ids) <= dim:
                continue
            other_party = other.state.attrs.get("party")
            if other_party == party:
                in_vals.append(float(other_ids[dim]))
            elif (
                # Phase 8d: only the other PARTISAN party counts as
                # "out" for Mason's mega-identity mechanism. Independents
                # (party=2) and party-less agents (party=None) are not
                # the identity-differentiation target. At
                # independent_fraction=0.0 no party=2 agents exist and
                # this filter is a no-op (bit-identity preserved).
                other_party is not None
                and other_party != 2
            ):
                out_vals.append(float(other_ids[dim]))
        if not in_vals:
            return StateDelta()

        in_mean = float(np.mean(in_vals))
        out_mean = float(np.mean(out_vals)) if out_vals else 0.0
        target = in_mean + self.differentiation * (in_mean - out_mean)
        target = max(-1.0, min(1.0, target))
        diff = target - float(identities[dim])

        delta_vec = np.zeros(len(identities), dtype=float)
        delta_vec[dim] = self.step * diff
        return StateDelta(d_attrs={"identities": delta_vec})
