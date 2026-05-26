"""
ContinuousSpace2D — bounded 2D coordinate store, demoted by ADR-001.

Holds agent positions, the agent roster, and an id->Agent index used by
the network-mediated influence rules. It no longer answers proximity
queries: the social network at ``env.attrs["network"]`` is the substrate
for "who hears whom" (ADR-001 §6.1). The KDTree and ``neighbors_within``
are gone.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from .agent import Agent


class ContinuousSpace2D:
    def __init__(self, bounds: tuple[tuple[float, float], tuple[float, float]] = ((-1.0, 1.0), (-1.0, 1.0))):
        self.bounds = bounds
        self._lo = np.array([bounds[0][0], bounds[1][0]])
        self._hi = np.array([bounds[0][1], bounds[1][1]])
        self._agents: list[Agent] = []
        self._positions: np.ndarray = np.zeros((0, 2))
        self.agents_by_id: dict[int, Agent] = {}

    def rebuild(self, agents) -> None:
        self._agents = list(agents)
        if self._agents:
            self._positions = np.array(
                [a.state.ideology for a in self._agents], dtype=float
            )
        else:
            self._positions = np.zeros((0, 2))
        self.agents_by_id = {a.id: a for a in self._agents}

    def clip(self, pos: np.ndarray) -> np.ndarray:
        return np.clip(pos, self._lo, self._hi)
