"""
Elite drift — party centers polarize over time.

Models the monotonic elite-polarization trend documented by McCarty,
Poole & Rosenthal (2006) via DW-NOMINATE: party leaders' positions
diverge from the political center over decades. Mass agents follow via
PartyPull, reproducing Hetherington (2001): mass partisanship rises when
elite cues become clearer.

Each tick, each party's center is pushed away from the centroid of all
party centers at a constant rate, until it hits the [-1, 1] bounds.
With 2 parties this just separates them along their initial axis; with
more parties they fan outward toward the corners.
"""
from __future__ import annotations

import numpy as np

from ..core.agent import Agent
from ..core.environment import Environment
from ..core.space import ContinuousSpace2D


class EliteDrift:
    def __init__(self, rate: float = 0.0005, asymmetric: dict[int, float] | None = None):
        """
        rate: per-tick drift magnitude
        asymmetric: optional {party_id: rate_multiplier} for asymmetric drift
                    (e.g., {0: 0.5, 1: 1.5} for one party drifting faster —
                    McCarty et al.'s "Republicans moved further right" pattern)
        """
        self.rate = rate
        self.asymmetric = asymmetric or {}

    def apply(
        self,
        env: Environment,
        agents: list[Agent],
        space: ContinuousSpace2D,
        rng: np.random.Generator,
        tick: int,
    ) -> None:
        if self.rate <= 0:
            return
        parties = env.attrs.get("parties")
        if not parties or len(parties) < 2:
            return
        positions = np.array(list(parties.values()), dtype=float)
        centroid = positions.mean(axis=0)
        for pid in list(parties.keys()):
            direction = parties[pid] - centroid
            d = float(np.linalg.norm(direction))
            if d < 1e-9:
                # Degenerate: nudge in a random direction so the rule can take hold
                direction = rng.normal(0, 1, size=2)
                d = float(np.linalg.norm(direction))
                if d < 1e-9:
                    continue
            mult = self.asymmetric.get(pid, 1.0)
            step = self.rate * mult * direction / d
            parties[pid] = np.clip(parties[pid] + step, -1.0, 1.0)

        # Update viz hint so the dashboard rerenders party stars at new positions
        viz = env.attrs.setdefault("viz", {})
        viz["party_centers"] = parties
