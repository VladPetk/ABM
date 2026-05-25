"""
ContinuousSpace2D — bounded 2D continuous space with fast neighbor queries.

Rebuilt once per tick from the current agent positions; rules then issue
radius queries against the cached KDTree. O(N log N) rebuild, O(log N + k)
per query. neighbors_within() returns Agent objects so rules can read
arbitrary state (party, affect, identity) without separate lookups.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from scipy.spatial import cKDTree

if TYPE_CHECKING:
    from .agent import Agent


class ContinuousSpace2D:
    def __init__(self, bounds: tuple[tuple[float, float], tuple[float, float]] = ((-1.0, 1.0), (-1.0, 1.0))):
        self.bounds = bounds
        self._lo = np.array([bounds[0][0], bounds[1][0]])
        self._hi = np.array([bounds[0][1], bounds[1][1]])
        self._agents: list[Agent] = []
        self._positions: np.ndarray = np.zeros((0, 2))
        self._tree: cKDTree | None = None

    def rebuild(self, agents) -> None:
        self._agents = list(agents)
        if self._agents:
            self._positions = np.array([a.state.ideology for a in self._agents], dtype=float)
            self._tree = cKDTree(self._positions)
        else:
            self._positions = np.zeros((0, 2))
            self._tree = None

    def neighbors_within(
        self,
        center: np.ndarray,
        radius: float,
        exclude_id: int | None = None,
    ) -> list[Agent]:
        if self._tree is None or radius <= 0:
            return []
        idxs = self._tree.query_ball_point(center, r=radius)
        if exclude_id is None:
            return [self._agents[i] for i in idxs]
        return [self._agents[i] for i in idxs if self._agents[i].id != exclude_id]

    def clip(self, pos: np.ndarray) -> np.ndarray:
        return np.clip(pos, self._lo, self._hi)
