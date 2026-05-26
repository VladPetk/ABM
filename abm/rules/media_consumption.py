"""
Media consumption — each agent drifts toward the weighted mean of the
outlets they consume.

Replaces the old PartisanMediaExposure scalar with a proper per-agent diet
across N named outlets. The dynamic is the same in shape (you drift toward
your media) but the *story* is concrete: "this person reads Fox + WSJ, and
that's where they're being pulled."

Reads:
  agent.state.attrs["media_diet"]   -- dict {outlet_id: weight}
  env.attrs["outlets"]              -- dict {outlet_id: MediaOutlet}

Writes (delta):
  d_ideology = strength * (diet_target - current_ideology)
"""
from __future__ import annotations

import numpy as np

from ..core.agent import Agent
from ..core.environment import Environment
from ..core.outlets import diet_target
from ..core.space import ContinuousSpace2D
from ..core.state import StateDelta


class MediaConsumption:
    def __init__(self, strength: float = 0.04):
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
        diet = agent.state.attrs.get("media_diet")
        outlets = env.attrs.get("outlets")
        if not diet or not outlets:
            return StateDelta()
        target = diet_target(diet, outlets)
        d = self.strength * (target - agent.state.ideology)
        # F1: Friedkin-Johnsen scaling — stubborn agents move less.
        s = float(agent.state.attrs.get("stubbornness", 0.0))
        return StateDelta(d_ideology=(1.0 - s) * d)
