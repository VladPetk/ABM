"""
Media shock — periodic external events push the population.

Every `period` ticks, all agents (or a party subset, for partisan media
spillover) are pulled toward a target position by `strength`. Models
elections, scandals, salient crises — moments when an external signal
dominates day-to-day social influence.

If `target` is None the rule picks a random direction each firing,
modeling unpredictable news cycles. Otherwise the same target fires
every period (e.g., a sustained campaign at a fixed position).

The event record is written to env.attrs["last_event"] so the dashboard
can flash a marker.
"""
from __future__ import annotations

import numpy as np

from ..core.agent import Agent
from ..core.environment import Environment
from ..core.space import ContinuousSpace2D


class MediaShock:
    def __init__(
        self,
        period: int = 100,
        strength: float = 0.08,
        target: np.ndarray | None = None,
        party_targeted: int | None = None,
    ):
        self.period = period
        self.strength = strength
        self.target = target
        self.party_targeted = party_targeted

    def apply(
        self,
        env: Environment,
        agents: list[Agent],
        space: ContinuousSpace2D,
        rng: np.random.Generator,
        tick: int,
    ) -> None:
        if self.period <= 0 or tick == 0 or tick % self.period != 0:
            return
        target = self.target if self.target is not None else rng.uniform(-1.0, 1.0, size=2)
        lo = np.array([-1.0, -1.0])
        hi = np.array([1.0, 1.0])
        affected = 0
        for agent in agents:
            if self.party_targeted is not None and agent.state.attrs.get("party") != self.party_targeted:
                continue
            agent.state.ideology = np.clip(
                agent.state.ideology + self.strength * (target - agent.state.ideology),
                lo, hi,
            )
            affected += 1
        env.attrs["last_event"] = {
            "tick": tick,
            "target": np.asarray(target, dtype=float).tolist(),
            "strength": self.strength,
            "party_targeted": self.party_targeted,
            "affected": affected,
        }
