"""
Backlash repulsion (Macy-Flache family — empirically contested).

Agents pushed away from neighbors in the ring [epsilon, max_range] — close
enough to perceive, too dissimilar to accept. Inverse-square magnitude so
the just-out-of-tolerance crowd dominates the push.

Note: the empirical record for negative influence is mixed (Bail et al. 2018
supports backfire; the Meta/2020 study and most other tests show null
cross-cutting effects). Mäs-Flache (2013) demonstrated bi-polarization can
emerge without it via argument-exchange (see rules/argument_exchange.py).
Default strength is 0 in newer scenarios; enable explicitly when comparing
mechanisms.
"""
from __future__ import annotations

import numpy as np

from ..core.agent import Agent
from ..core.environment import Environment
from ..core.space import ContinuousSpace2D
from ..core.state import StateDelta


class BacklashRepulsion:
    def __init__(self, epsilon: float = 0.3, max_range: float = 1.5, strength: float = 0.05):
        self.epsilon = epsilon
        self.max_range = max_range
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
        outer = space.neighbors_within(agent.state.ideology, self.max_range, exclude_id=agent.id)
        if not outer:
            return StateDelta()
        push = np.zeros(2)
        count = 0
        for neighbor in outer:
            diff = agent.state.ideology - neighbor.state.ideology
            d = float(np.linalg.norm(diff))
            if d <= self.epsilon or d < 1e-9:
                continue
            push += diff / (d * d)
            count += 1
        if count == 0:
            return StateDelta()
        return StateDelta(d_ideology=self.strength * push / count)
