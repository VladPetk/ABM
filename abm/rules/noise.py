"""
Gaussian noise — small random ideological drift each tick.

Keeps the system from freezing at brittle equilibria and models the fact
that real opinion shifts aren't purely driven by social pressure.
"""
from __future__ import annotations

import numpy as np

from ..core.agent import Agent
from ..core.environment import Environment
from ..core.space import ContinuousSpace2D
from ..core.state import StateDelta


class GaussianNoise:
    def __init__(self, sigma: float = 0.01):
        self.sigma = sigma

    def apply(
        self,
        agent: Agent,
        space: ContinuousSpace2D,
        env: Environment,
        rng: np.random.Generator,
    ) -> StateDelta:
        if self.sigma <= 0:
            return StateDelta()
        return StateDelta(d_ideology=rng.normal(0.0, self.sigma, size=2))
