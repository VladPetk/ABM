"""
Faction anchor — Phase 9 Tier C emergence-driven faction dynamics.

Pulls each agent toward a per-agent target ``attrs["faction_center"]``
(an `(x, y)` ndarray) at strength ``s * (1 - stubbornness)`` per tick.
Agents whose `faction_center` attr is missing (or `None`) are skipped
entirely — so the rule is **inert** at t=0 (no agent is tagged yet) and
**inert in the pillar** (which never tags factions).

This is the Tier C mechanism (see `phase9_spec.md §9`). The 4
faction-emergence event handlers in `historical_arc.py`
(`_event_2009_tea_party`, `_event_2015_maga`, `_event_2016_bernie`,
`_event_2018_dsa`) set `faction_center` on a sampled subset of
existing agents post-2009; this rule then progressively pulls those
agents toward their sub-centroid over subsequent ticks.

Pipeline placement: after ``PartyPull``, before
``BoundedConfidenceInfluence``. PartyPull pulls toward the original
party-centroid-noise ``party_cue`` (Tier C does **not** overwrite
party_cue); FactionAnchor adds a faction-specific tug for tagged
agents only; BC then homogenises locally.

Reads:
  agent.state.attrs["faction_center"]  -- (2,) ndarray; if None, no-op
  agent.state.attrs["stubbornness"]    -- [0, 1], default 0.0

Modeled on `PartyPull` (same per-agent ``apply(agent, space, env, rng)``
→ ``StateDelta`` signature; same Friedkin-Johnsen ``(1 - stubbornness)``
multiplier; same clip-to-unit-box discipline via the engine's
``space.clip`` after the agent phase).
"""
from __future__ import annotations

import numpy as np

from ..core.agent import Agent
from ..core.environment import Environment
from ..core.space import ContinuousSpace2D
from ..core.state import StateDelta


class FactionAnchor:
    """Phase 9 Tier C. Pulls each agent toward ``attrs['faction_center']``
    at strength ``s * (1 - stubbornness)``. Inert for agents lacking the
    attr — so it's a no-op at t=0 and a no-op in the pillar (which never
    tags factions)."""

    def __init__(self, strength: float = 0.04):
        self.strength = float(strength)

    def apply(
        self,
        agent: Agent,
        space: ContinuousSpace2D,
        env: Environment,
        rng: np.random.Generator,
    ) -> StateDelta:
        if self.strength == 0:
            return StateDelta()
        center = agent.state.attrs.get("faction_center")
        if center is None:
            return StateDelta()
        center_arr = np.asarray(center, dtype=float)
        stubbornness = float(agent.state.attrs.get("stubbornness", 0.0))
        d = self.strength * (1.0 - stubbornness) * (
            center_arr - agent.state.ideology
        )
        return StateDelta(d_ideology=d)
