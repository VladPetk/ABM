"""
Argument exchange — simplified Mäs-Flache ACTB (2013).

Each tick, the agent picks one homophilous neighbor (within `homophily_radius`)
and adopts one "argument" on one randomly chosen issue axis. The argument's
direction matches the neighbor's attitude on that axis, with magnitude
proportional to how strong that attitude is.

This is the canonical mechanism for bi-polarization *without* negative
influence. Homophily filters who you listen to (only people near you on
the compass), and they're all on the same side as you, so successive
adoptions drive you outward. Pair with BoundedConfidenceInfluence off
(or low) to see the pure ACTB effect.
"""
from __future__ import annotations

import numpy as np

from ..core.agent import Agent
from ..core.environment import Environment
from ..core.space import ContinuousSpace2D
from ..core.state import StateDelta


class ArgumentExchange:
    def __init__(self, homophily_radius: float = 0.3, step: float = 0.02):
        self.homophily_radius = homophily_radius
        self.step = step

    def apply(
        self,
        agent: Agent,
        space: ContinuousSpace2D,
        env: Environment,
        rng: np.random.Generator,
    ) -> StateDelta:
        if self.step == 0:
            return StateDelta()
        neighbors = space.neighbors_within(
            agent.state.ideology, self.homophily_radius, exclude_id=agent.id
        )
        if not neighbors:
            return StateDelta()
        neighbor = neighbors[int(rng.integers(len(neighbors)))]
        axis = int(rng.integers(2))
        delta = np.zeros(2)
        delta[axis] = self.step * float(neighbor.state.ideology[axis])
        return StateDelta(d_ideology=delta)
