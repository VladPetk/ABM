"""
Bounded-confidence attraction (Hegselmann-Krause), exposure-aware.

Agents only listen to neighbors within ideological distance epsilon.
Within that confidence ball, they shift a fraction ``strength`` of the
way toward the **exposure-weighted mean** of those neighbours: tie
neighbours pull at full weight, non-tie neighbours pull at the residual
``cross_tie_weight``. Classic mechanism for echo-chamber formation;
``cross_tie_weight`` is the Phase 3 "soft gate" that lets the social
tie network filter who you actually hear.

S0-S3 keep ``cross_tie_weight = 1.0``, which takes a fast path that is
**bit-identical** to today's plain-mean rule (guarded by
``test_cross_tie_weight_1_is_inert``).
"""
from __future__ import annotations

import numpy as np

from ..core.agent import Agent
from ..core.environment import Environment
from ..core.space import ContinuousSpace2D
from ..core.state import StateDelta


class BoundedConfidenceInfluence:
    def __init__(
        self,
        epsilon: float = 0.3,
        strength: float = 0.1,
        cross_tie_weight: float = 1.0,
    ):
        self.epsilon = epsilon
        self.strength = strength
        # 1.0 = exposure is uniform (the Phase 1/2 behaviour).
        # 0.0 = only tie neighbours are heard. S4 sits well below 1.
        self.cross_tie_weight = cross_tie_weight

    def apply(
        self,
        agent: Agent,
        space: ContinuousSpace2D,
        env: Environment,
        rng: np.random.Generator,
    ) -> StateDelta:
        neighbors = space.neighbors_within(
            agent.state.ideology, self.epsilon, exclude_id=agent.id
        )
        if not neighbors:
            return StateDelta()

        network = env.attrs.get("network")
        if network is None or self.cross_tie_weight == 1.0:
            # FAST PATH — must stay bit-identical to the pre-Phase-3 rule.
            target = np.mean([n.state.ideology for n in neighbors], axis=0)
        else:
            ties = network.get(agent.id, ())
            weights = np.array(
                [1.0 if n.id in ties else self.cross_tie_weight for n in neighbors],
                dtype=float,
            )
            if weights.sum() == 0.0:
                # Gated agent with no in-range tie neighbours: silent this tick.
                return StateDelta()
            target = np.average(
                [n.state.ideology for n in neighbors], axis=0, weights=weights
            )
        return StateDelta(d_ideology=self.strength * (target - agent.state.ideology))
