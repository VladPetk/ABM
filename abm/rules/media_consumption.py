"""
Media consumption — each outlet pulls the agent toward its own position.

Phase 8c §3 (E1) rewrites the rule from a single weighted-mean `diet_target`
pull into a **per-outlet sum** of pulls. Mathematically identical when the
agent consumes a normalised diet (the sum of `weight_i * (outlet_i.position
- agent.ideology)` divided by the total weight equals
`diet_target - agent.ideology`); the behavioural change happens when an
intervention zeroes specific outlet weights without re-normalising the
remainder. The motivation is R1's "category error" critique of X3 in the
phase-7 reading: the engine bundled the *centripetal* pull of broadcast /
local news with the *centrifugal* pull of partisan cable. With per-outlet
contributions, X3 ("Quit cable news") can zero just the partisan-cable
outlets and leave broadcast/local in place, separating the two forces.

Reads:
  agent.state.attrs["media_diet"]   -- dict {outlet_id: weight}
  env.attrs["outlets"]              -- dict {outlet_id: MediaOutlet}

Writes (delta):
  d_ideology = strength * sum_i (weight_i * (outlet_i.position - ideology))

The weights are absolute (no re-normalisation by their current sum
— Fork 3-B default). When the diet's weights are normalised at
build (the usual case), this equals the Phase 7
`strength * (diet_target - ideology)` exactly.

This is identical to the Phase 5/6/7 `strength * (diet_target - ideology)`
when weights are normalised (i.e. every X-intervention that doesn't touch
media_diet's weights produces bit-identical pulls). Verified by
`test_per_outlet_pull_equals_diet_target_for_normalized_diet`.
"""
from __future__ import annotations

import numpy as np

from ..core.agent import Agent
from ..core.environment import Environment
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
        # Phase 8c §3 E1: per-outlet pull. The weights are treated as
        # *absolute* contributions: each outlet contributes
        # `weight * (outlet.position - ideology)`, summed across the
        # diet. **No re-normalisation by current sum.**
        #
        # When the diet weights are normalised at build (the usual
        # case — `diet_for_party` returns weights summing to 1), the
        # formula equals `diet_target - ideology` exactly (Phase 7
        # behaviour), so the pillar S0-S4 trajectory is bit-identical.
        # When X3 zeros some weights (Fork 3-B default: NO
        # re-normalisation), the sum drops and the pull magnitude
        # drops proportionally — the agent's total media intake goes
        # down. That's the lay reading of "quit cable news":
        # broadcast exposure stays where it was, partisan cable
        # exposure is removed, total intake shrinks.
        # Phase 8e §3: per-agent `media_cue` analog of Phase 8a's
        # `party_cue`. Each agent's media exposure is biased by a
        # personal vector — same outlet roster, but each agent
        # perceives them shifted by `media_cue`. Pillar agents don't
        # carry `media_cue` (fallback None → no bias → bit-identical
        # to Phase 8d). Historical_arc partisan agents seed
        # media_cue ~ N(0, MEDIA_CUE_SIGMA) at build; Independents
        # skip (they already have a centrist diet). The bias
        # addresses the post-2000 within-party SD collapse R1/R2
        # both flagged: a personal media cue introduces per-agent
        # heterogeneity in the diet's effective target, mirroring
        # Phase 8a's party_cue fix to PartyPull.
        media_cue = agent.state.attrs.get("media_cue")
        pull = np.zeros(2)
        for outlet_id, weight in diet.items():
            outlet = outlets.get(outlet_id)
            if outlet is None:
                continue
            effective_pos = outlet.position
            if media_cue is not None:
                effective_pos = effective_pos + np.asarray(media_cue)
            pull += weight * (effective_pos - agent.state.ideology)
        d = self.strength * pull
        # F1: Friedkin-Johnsen scaling — stubborn agents move less.
        s = float(agent.state.attrs.get("stubbornness", 0.0))
        return StateDelta(d_ideology=(1.0 - s) * d)
