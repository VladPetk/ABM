"""
Affect-gated backlash repulsion — the Bail 2018 backfire mechanism.

For each out-party network neighbour, the agent's affect toward that
party is checked: if warmth < ``affect_threshold`` (default ``-0.3``),
the encounter contributes a push **away** from the neighbour. Push
magnitude scales linearly with the absolute warmth (`(-warmth)`, clipped)
and with the existing inverse-square ring profile in
``[epsilon, max_range]``. Above the threshold (warm or neutral), no
backfire fires.

This is the **honest model of backfire**: it fires conditionally on
existing animus (Bail et al. 2018 *PNAS* 115:9216), not universally
on every cross-party encounter (the pre-Phase-6 Macy-Flache 1997 form,
which the empirical record does not support — Guess et al. 2023, Nyhan
et al. 2023 find null average effects of cross-cutting exposure;
Levendusky 2021 finds *positive* effects under warm framing). In-party
neighbours never contribute backlash — the mechanism is identity-threat-
driven and only fires across party.

Combines with Phase 4 F1 (Friedkin-Johnsen stubbornness scaling at the
apply site) and Phase 5 A1 (affect attribute being the agent's stored
warmth, capped only by the metric read).

``strength = 0`` is an exact no-op (the rule returns immediately) — the
pillar's baseline progression S0-S4 carries the rule at strength 0;
Phase 6 interventions turn it on.
"""
from __future__ import annotations

import numpy as np

from ..core.agent import Agent
from ..core.environment import Environment
from ..core.network import neighbor_agents
from ..core.space import ContinuousSpace2D
from ..core.state import StateDelta


class BacklashRepulsion:
    def __init__(
        self,
        epsilon: float = 0.3,
        max_range: float = 1.5,
        strength: float = 0.05,
        affect_threshold: float = -0.3,
    ):
        self.epsilon = epsilon
        self.max_range = max_range
        self.strength = strength
        # Phase 6 R1: out-party neighbours only contribute backlash when
        # the agent's warmth toward their party is below this threshold.
        # Default -0.3 means "noticeably cold but not extreme."
        # +inf disables the gate (every out-party encounter triggers
        # backlash — the pre-Phase-6 Macy-Flache form); -inf disables
        # backlash entirely.
        self.affect_threshold = affect_threshold

    def apply(
        self,
        agent: Agent,
        space: ContinuousSpace2D,
        env: Environment,
        rng: np.random.Generator,
    ) -> StateDelta:
        if self.strength == 0:
            return StateDelta()
        neighbours = neighbor_agents(agent, space, env)
        if not neighbours:
            return StateDelta()

        own_party = agent.state.attrs.get("party")
        own_affect = agent.state.attrs.get("affect") or {}
        push = np.zeros(2)
        count = 0
        for n in neighbours:
            other = n.state.attrs.get("party")
            # In-party neighbours and party-less agents never contribute
            # to backlash — Bail's mechanism is identity-threat driven.
            if other is None or other == own_party:
                continue
            warmth = float(np.clip(own_affect.get(other, 0.0), -1.0, 1.0))
            if warmth >= self.affect_threshold:
                # Not hot enough — no backfire from this encounter.
                continue
            diff = agent.state.ideology - n.state.ideology
            d = float(np.linalg.norm(diff))
            # Keep the [epsilon, max_range] ring semantics — too-close =
            # below ideological-distance threshold; too-far = no
            # meaningful exposure (Macy-Flache).
            if d <= self.epsilon or d > self.max_range or d < 1e-9:
                continue
            # Linear scaling in (-warmth): a -1 (clip floor) agent
            # pushes at full inverse-square strength; a -0.3 (just past
            # threshold) agent pushes at 30%.
            magnitude = (-warmth) / (d * d)
            push += magnitude * diff
            count += 1

        if count == 0:
            return StateDelta()
        d = self.strength * push / count
        # F1: Friedkin-Johnsen scaling — stubborn agents move less.
        s = float(agent.state.attrs.get("stubbornness", 0.0))
        return StateDelta(d_ideology=(1.0 - s) * d)
